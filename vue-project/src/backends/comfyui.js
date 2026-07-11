/**
 * ComfyUI Service Module
 * Handles workflow parsing, WebSocket progress, image fetching, and workflow persistence.
 */
import { reactive, ref } from 'vue'
import { saveToFile, loadFromFile } from '@/storage'

const COMFY_WORKFLOWS_FILE = 'comfyWorkflows.json'

// ── Reactive State ────────────────────────────────────────────────────────

export const comfyState = reactive({
  workflows: [],          // Array of { id, name, workflow, exposedInputs }
  activeWorkflowId: null, // Currently selected workflow ID
  clientId: generateClientId(),
  wsConnection: null,     // Active WebSocket instance
  objectInfoCache: {},    // Cache of /object_info responses keyed by class_type
})

function generateClientId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `comfy_${Date.now()}_${Math.floor(Math.random() * 1000000)}`
}

// ── Workflow Parsing ──────────────────────────────────────────────────────

/**
 * Fetch /object_info for a specific node class from ComfyUI
 */
async function fetchObjectInfo(baseUrl, classType) {
  if (comfyState.objectInfoCache[classType]) {
    return comfyState.objectInfoCache[classType]
  }
  try {
    const response = await fetch(`${baseUrl}object_info/${encodeURIComponent(classType)}`)
    if (!response.ok) return null
    const data = await response.json()
    const info = data[classType] || null
    if (info) {
      comfyState.objectInfoCache[classType] = info
    }
    return info
  } catch (e) {
    console.warn(`Failed to fetch object_info for ${classType}:`, e)
    return null
  }
}

/**
 * Determine if an input type is user-editable (not a link to another node).
 * ComfyUI links are arrays like ["nodeId", outputIndex].
 */
function isEditableValue(value) {
  if (Array.isArray(value) && value.length === 2 && typeof value[1] === 'number') {
    // This is a node link [nodeId, outputSlot]
    return false
  }
  return true
}

/**
 * Determine the UI control type for a given input spec from object_info.
 * Returns { type, default, min, max, step, options, tooltip }
 */
function resolveInputSpec(inputSpec) {
  if (!inputSpec || !Array.isArray(inputSpec) || inputSpec.length === 0) {
    return { type: 'text', tooltip: '' }
  }

  const typeOrOptions = inputSpec[0]
  const meta = inputSpec[1] || {}

  // If it's an array of strings → dropdown/select
  if (Array.isArray(typeOrOptions)) {
    return {
      type: 'select',
      options: typeOrOptions,
      default: meta.default ?? typeOrOptions[0],
      tooltip: meta.tooltip || '',
    }
  }

  // Primitive types
  switch (typeOrOptions) {
    case 'INT':
      return {
        type: 'int',
        default: meta.default ?? 0,
        min: meta.min ?? 0,
        max: meta.max ?? 1000000,
        step: meta.step ?? 1,
        tooltip: meta.tooltip || '',
        controlAfterGenerate: meta.control_after_generate || false,
      }
    case 'FLOAT':
      return {
        type: 'float',
        default: meta.default ?? 0.0,
        min: meta.min ?? 0.0,
        max: meta.max ?? 100.0,
        step: meta.step ?? 0.1,
        round: meta.round ?? null,
        tooltip: meta.tooltip || '',
      }
    case 'STRING':
      return {
        type: meta.multiline ? 'textarea' : 'text',
        default: meta.default ?? '',
        tooltip: meta.tooltip || '',
        multiline: meta.multiline || false,
        dynamicPrompts: meta.dynamicPrompts || false,
      }
    case 'BOOLEAN':
      return {
        type: 'boolean',
        default: meta.default ?? false,
        tooltip: meta.tooltip || '',
      }
    // Connection types (MODEL, CLIP, VAE, CONDITIONING, LATENT, IMAGE, etc.)
    // These are typically node links and shouldn't be exposed as UI inputs
    default:
      return {
        type: 'connection',
        connectionType: typeOrOptions,
        tooltip: meta.tooltip || '',
      }
  }
}

/**
 * Parse all inputs from a workflow JSON, enriched with /object_info metadata.
 * Returns an array of discovered inputs.
 */
export async function parseWorkflowInputs(workflowJson, baseUrl) {
  const inputs = []

  for (const [nodeId, node] of Object.entries(workflowJson)) {
    const classType = node.class_type
    if (!classType) continue

    const nodeTitle = node._meta?.title || classType
    const nodeInputs = node.inputs || {}

    // Fetch object_info for this node class
    let objectInfo = null
    if (baseUrl) {
      objectInfo = await fetchObjectInfo(baseUrl, classType)
    }

    for (const [inputKey, inputValue] of Object.entries(nodeInputs)) {
      // Skip node links (connections to other nodes)
      if (!isEditableValue(inputValue)) continue

      // Get input spec from object_info
      let spec = { type: 'text', tooltip: '' }
      if (objectInfo?.input?.required?.[inputKey]) {
        spec = resolveInputSpec(objectInfo.input.required[inputKey])
      } else if (objectInfo?.input?.optional?.[inputKey]) {
        spec = resolveInputSpec(objectInfo.input.optional[inputKey])
      }

      // Skip connection-type inputs (they are node links even if currently hardcoded)
      if (spec.type === 'connection') continue

      inputs.push({
        nodeId,
        nodeTitle,
        classType,
        inputKey,
        label: `${nodeTitle} → ${inputKey}`,
        value: inputValue,
        spec,
        // Will be set by user during import
        exposed: false,
        order: inputs.length,
      })
    }
  }

  return inputs
}

/**
 * Import a workflow: parse JSON, discover inputs, return for user selection.
 */
export async function importWorkflow(jsonData, name, baseUrl) {
  const workflow = typeof jsonData === 'string' ? JSON.parse(jsonData) : jsonData
  const allInputs = await parseWorkflowInputs(workflow, baseUrl)

  return {
    id: generateClientId(),
    name: name || 'Untitled Workflow',
    workflow,
    allInputs,
    exposedInputs: [], // User will select these
  }
}

/**
 * Save a finalized workflow (after user selects inputs) to the workflow library.
 */
export function addWorkflow(workflowData) {
  const existing = comfyState.workflows.findIndex(w => w.id === workflowData.id)
  if (existing >= 0) {
    comfyState.workflows.splice(existing, 1, workflowData)
  } else {
    comfyState.workflows.push(workflowData)
  }
  if (!comfyState.activeWorkflowId) {
    comfyState.activeWorkflowId = workflowData.id
  }
}

/**
 * Remove a workflow from the library.
 */
export function removeWorkflow(workflowId) {
  comfyState.workflows = comfyState.workflows.filter(w => w.id !== workflowId)
  if (comfyState.activeWorkflowId === workflowId) {
    comfyState.activeWorkflowId = comfyState.workflows[0]?.id || null
  }
}

/**
 * Get the currently active workflow.
 */
export function getActiveWorkflow() {
  return comfyState.workflows.find(w => w.id === comfyState.activeWorkflowId) || null
}

// ── Prompt Building ───────────────────────────────────────────────────────

/**
 * Build the final ComfyUI prompt from a workflow template + user input overrides.
 * inputOverrides is an object keyed by `${nodeId}.${inputKey}` → value
 */
export function buildComfyPrompt(workflow, inputOverrides = {}) {
  // Deep clone the workflow
  const prompt = JSON.parse(JSON.stringify(workflow))

  for (const [key, value] of Object.entries(inputOverrides)) {
    const [nodeId, inputKey] = key.split('.')
    if (prompt[nodeId]?.inputs && inputKey in prompt[nodeId].inputs) {
      // Convert types appropriately
      const currentValue = prompt[nodeId].inputs[inputKey]
      if (typeof currentValue === 'number' && typeof value === 'string') {
        const parsed = Number(value)
        prompt[nodeId].inputs[inputKey] = Number.isNaN(parsed) ? value : parsed
      } else if (typeof currentValue === 'boolean' && typeof value === 'string') {
        prompt[nodeId].inputs[inputKey] = value === 'true'
      } else {
        prompt[nodeId].inputs[inputKey] = value
      }
    }
  }

  return prompt
}

// ── WebSocket Communication ───────────────────────────────────────────────

/**
 * Connect to ComfyUI WebSocket for real-time progress tracking.
 * Returns an object with { ws, close } for management.
 *
 * callbacks: {
 *   onProgress(data)      - { value, max, prompt_id, node }
 *   onExecuting(data)     - { node, prompt_id } (node=null means done)
 *   onExecuted(data)      - { node, output, prompt_id }
 *   onError(data)         - { exception_message, ... }
 *   onStatus(data)        - { status: { exec_info: { queue_remaining } } }
 * }
 */
export function connectComfyWebSocket(baseUrl, callbacks = {}) {
  const wsUrl = baseUrl.replace(/^http/, 'ws') + `ws?clientId=${comfyState.clientId}`

  // Close existing connection
  if (comfyState.wsConnection && comfyState.wsConnection.readyState !== WebSocket.CLOSED) {
    comfyState.wsConnection.close()
  }

  const ws = new WebSocket(wsUrl)
  comfyState.wsConnection = ws

  ws.onopen = () => {
    console.log('ComfyUI WebSocket connected')
  }

  ws.onmessage = (event) => {
    if (typeof event.data !== 'string') {
      // Binary data (e.g., preview images from SaveImageWebsocket)
      return
    }

    try {
      const message = JSON.parse(event.data)
      const { type, data } = message

      switch (type) {
        case 'progress':
          callbacks.onProgress?.(data)
          break
        case 'executing':
          callbacks.onExecuting?.(data)
          break
        case 'executed':
          callbacks.onExecuted?.(data)
          break
        case 'execution_error':
          callbacks.onError?.(data)
          break
        case 'status':
          callbacks.onStatus?.(data)
          break
        case 'execution_start':
        case 'execution_cached':
          // Informational, can be logged
          break
        default:
          break
      }
    } catch (e) {
      console.warn('Failed to parse ComfyUI WS message:', e)
    }
  }

  ws.onerror = (event) => {
    console.error('ComfyUI WebSocket error:', event)
  }

  ws.onclose = () => {
    console.log('ComfyUI WebSocket closed')
    if (comfyState.wsConnection === ws) {
      comfyState.wsConnection = null
    }
  }

  return ws
}

/**
 * Close the active ComfyUI WebSocket connection.
 */
export function closeComfyWebSocket() {
  if (comfyState.wsConnection && comfyState.wsConnection.readyState !== WebSocket.CLOSED) {
    comfyState.wsConnection.close()
  }
  comfyState.wsConnection = null
}

// ── API Calls ─────────────────────────────────────────────────────────────

/**
 * Queue a prompt on ComfyUI.
 */
export async function queueComfyPrompt(baseUrl, promptData) {
  const payload = {
    prompt: promptData,
    client_id: comfyState.clientId,
  }

  const response = await fetch(`${baseUrl}prompt`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`ComfyUI prompt failed (${response.status}): ${errorText}`)
  }

  return await response.json()
}

/**
 * Fetch generation history for a specific prompt_id.
 */
export async function getComfyHistory(baseUrl, promptId) {
  const response = await fetch(`${baseUrl}history/${promptId}`)
  if (!response.ok) return null
  return await response.json()
}

/**
 * Fetch an image from ComfyUI's /view endpoint.
 * Returns the image as a Blob.
 */
export async function fetchComfyImage(baseUrl, filename, subfolder = '', folderType = 'output') {
  const params = new URLSearchParams({
    filename,
    subfolder,
    type: folderType,
  })

  const response = await fetch(`${baseUrl}view?${params}`)
  if (!response.ok) throw new Error(`Failed to fetch image: ${response.statusText}`)
  return await response.blob()
}

/**
 * Convert a Blob to a base64 data URL.
 */
export function blobToDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}

/**
 * Interrupt the current ComfyUI execution.
 */
export async function interruptComfyExecution(baseUrl) {
  const response = await fetch(`${baseUrl}interrupt`, { method: 'POST' })
  return response.ok
}

/**
 * Check ComfyUI system stats (health check).
 */
export async function getComfySystemStats(baseUrl) {
  try {
    const response = await fetch(`${baseUrl}system_stats`)
    if (!response.ok) return null
    return await response.json()
  } catch {
    return null
  }
}

/**
 * Fetch all available object_info from ComfyUI (full node registry).
 */
export async function fetchAllObjectInfo(baseUrl) {
  try {
    const response = await fetch(`${baseUrl}object_info`)
    if (!response.ok) return null
    const data = await response.json()
    // Merge into cache
    Object.assign(comfyState.objectInfoCache, data)
    return data
  } catch {
    return null
  }
}

// ── Persistence ───────────────────────────────────────────────────────────

/**
 * Save workflows to persistent storage.
 */
export async function saveComfyWorkflows() {
  await saveToFile(
    {
      workflows: comfyState.workflows,
      activeWorkflowId: comfyState.activeWorkflowId,
    },
    COMFY_WORKFLOWS_FILE
  )
}

/**
 * Load workflows from persistent storage.
 */
export async function loadComfyWorkflows() {
  const stored = await loadFromFile(COMFY_WORKFLOWS_FILE)
  if (!stored) return

  if (Array.isArray(stored.workflows)) {
    comfyState.workflows = stored.workflows
  }
  if (stored.activeWorkflowId) {
    comfyState.activeWorkflowId = stored.activeWorkflowId
  }
}
