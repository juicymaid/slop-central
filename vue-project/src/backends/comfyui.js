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
/**
 * Map standard sampler names (e.g. "DPM++ 2M", "Euler a") to ComfyUI sampler identifiers (e.g. "dpmpp_2m", "euler_ancestral").
 */
export function mapSamplerToComfy(name, validOptions = null) {
  if (!name) return 'dpmpp_2m'
  if (Array.isArray(validOptions) && validOptions.includes(name)) {
    return name
  }

  const normalized = String(name).trim()
  const map = {
    'Euler a': 'euler_ancestral',
    'Euler': 'euler',
    'LMS': 'lms',
    'Heun': 'heun',
    'DPM2': 'dpm_2',
    'DPM2 a': 'dpm_2_ancestral',
    'DPM fast': 'dpm_fast',
    'DPM adaptive': 'dpm_adaptive',
    'DPM++ 2S a': 'dpmpp_2s_ancestral',
    'DPM++ SDE': 'dpmpp_sde',
    'DPM++ 2M': 'dpmpp_2m',
    'DPM++ 2M SDE': 'dpmpp_2m_sde',
    'DPM++ 2M SDE Heun': 'dpmpp_2m_sde',
    'DPM++ 3M SDE': 'dpmpp_3m_sde',
    'DDIM': 'ddim',
    'UniPC': 'uni_pc',
    'LCM': 'lcm',
  }

  let mapped = map[normalized]
  if (!mapped) {
    mapped = normalized
      .toLowerCase()
      .replace(/\+\+/g, 'pp')
      .replace(/\s+/g, '_')
  }

  if (Array.isArray(validOptions) && validOptions.length > 0) {
    if (validOptions.includes(mapped)) return mapped
    const match = validOptions.find(opt => opt.toLowerCase() === mapped.toLowerCase())
    if (match) return match
    return validOptions[0]
  }

  return mapped
}

/**
 * Unmap ComfyUI sampler identifier back to standard UI name (e.g. "dpmpp_2m" -> "DPM++ 2M").
 */
export function unmapSamplerFromComfy(name) {
  if (!name) return 'DPM++ 2M'
  const map = {
    'euler_ancestral': 'Euler a',
    'euler': 'Euler',
    'lms': 'LMS',
    'heun': 'Heun',
    'dpm_2': 'DPM2',
    'dpm_2_ancestral': 'DPM2 a',
    'dpm_fast': 'DPM fast',
    'dpm_adaptive': 'DPM adaptive',
    'dpmpp_2s_ancestral': 'DPM++ 2S a',
    'dpmpp_sde': 'DPM++ SDE',
    'dpmpp_2m': 'DPM++ 2M',
    'dpmpp_2m_sde': 'DPM++ 2M SDE',
    'dpmpp_3m_sde': 'DPM++ 3M SDE',
    'ddim': 'DDIM',
    'uni_pc': 'UniPC',
    'lcm': 'LCM',
  }
  return map[String(name).toLowerCase()] || name
}

/**
 * Trace positive and negative prompt nodes in a ComfyUI workflow template by examining
 * KSampler links and node metadata titles.
 */
export function findPositiveAndNegativeNodes(workflowJson) {
  let posNodeId = null
  let negNodeId = null

  if (!workflowJson || typeof workflowJson !== 'object') {
    return { posNodeId, negNodeId }
  }

  const traceToTextNode = (link) => {
    if (!Array.isArray(link) || link.length < 1) return null
    let targetId = String(link[0])
    let visited = new Set()

    while (targetId && workflowJson[targetId] && !visited.has(targetId)) {
      visited.add(targetId)
      const targetNode = workflowJson[targetId]
      const targetClass = (targetNode.class_type || '').toLowerCase()

      if (targetClass.includes('cliptextencode') || targetClass.includes('prompt') || targetClass.includes('text')) {
        return targetId
      }
      const targetInputs = targetNode.inputs || {}
      let prevLink = targetInputs.conditioning || targetInputs.clip || targetInputs.positive || targetInputs.negative
      if (Array.isArray(prevLink) && prevLink.length >= 1) {
        targetId = String(prevLink[0])
      } else {
        break
      }
    }
    return null
  }

  // 1. Trace directly from KSampler / Sampler inputs
  for (const [nodeId, node] of Object.entries(workflowJson)) {
    const classType = (node.class_type || '').toLowerCase()
    if (classType.includes('ksampler') || classType.includes('sampler')) {
      const inputs = node.inputs || {}
      if (inputs.positive) {
        posNodeId = traceToTextNode(inputs.positive)
      }
      if (inputs.negative) {
        negNodeId = traceToTextNode(inputs.negative)
      }
      if (posNodeId || negNodeId) break
    }
  }

  // 2. Fallback: Search by title keywords
  const clipNodes = []
  for (const [nodeId, node] of Object.entries(workflowJson)) {
    const classType = (node.class_type || '').toLowerCase()
    if (classType.includes('cliptextencode') || classType.includes('prompt')) {
      clipNodes.push({ nodeId: String(nodeId), title: (node._meta?.title || '').toLowerCase() })
    }
  }

  if (!posNodeId) {
    const posMatch = clipNodes.find(n => n.title.includes('positive') || n.title.includes('pos'))
    posNodeId = posMatch ? posMatch.nodeId : (clipNodes[0]?.nodeId || null)
  }

  if (!negNodeId) {
    const negMatch = clipNodes.find(n => n.nodeId !== posNodeId && (n.title.includes('negative') || n.title.includes('neg')))
    negNodeId = negMatch ? negMatch.nodeId : (clipNodes.find(n => n.nodeId !== posNodeId)?.nodeId || null)
  }

  return { posNodeId, negNodeId }
}

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

  // If already open or connecting to same URL, update callbacks and reuse
  if (
    comfyState.wsConnection &&
    comfyState.wsConnection.url === wsUrl &&
    (comfyState.wsConnection.readyState === WebSocket.OPEN ||
      comfyState.wsConnection.readyState === WebSocket.CONNECTING)
  ) {
    comfyState.activeCallbacks = callbacks
    return comfyState.wsConnection
  }

  // Close existing connection
  if (comfyState.wsConnection && comfyState.wsConnection.readyState !== WebSocket.CLOSED) {
    comfyState.wsConnection.close()
  }

  comfyState.activeCallbacks = callbacks
  const ws = new WebSocket(wsUrl)
  comfyState.wsConnection = ws

  ws.onopen = () => {
    console.log('ComfyUI WebSocket connected')
  }

  ws.onmessage = (event) => {
    if (typeof event.data !== 'string') {
      // Binary data: preview images from ComfyUI
      // ComfyUI binary preview format:
      // Byte 0-3: event type (1 = PREVIEW_IMAGE)
      // Byte 4-7: image type (1 = JPEG, 2 = PNG)
      // Byte 8+: image binary data
      if (event.data instanceof Blob && event.data.size > 8) {
        try {
          const imageBlob = event.data.slice(8)
          const previewUrl = URL.createObjectURL(imageBlob)
          comfyState.activeCallbacks?.onPreview?.(previewUrl)
        } catch (e) {
          console.warn('Failed to parse ComfyUI preview blob:', e)
        }
      }
      return
    }

    try {
      const message = JSON.parse(event.data)
      const { type, data } = message

      switch (type) {
        case 'progress':
          comfyState.activeCallbacks?.onProgress?.(data)
          break
        case 'executing':
          comfyState.activeCallbacks?.onExecuting?.(data)
          break
        case 'executed':
          comfyState.activeCallbacks?.onExecuted?.(data)
          break
        case 'execution_error':
          comfyState.activeCallbacks?.onError?.(data)
          break
        case 'status':
          comfyState.activeCallbacks?.onStatus?.(data)
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
      comfyState.activeCallbacks = null
    }
  }

  return ws
}

/**
 * Ensure ComfyUI WebSocket is connected before proceeding.
 */
export async function ensureComfyWebSocket(baseUrl, callbacks = {}) {
  const ws = connectComfyWebSocket(baseUrl, callbacks)
  if (ws.readyState === WebSocket.OPEN) {
    return ws
  }
  if (ws.readyState === WebSocket.CONNECTING) {
    await new Promise((resolve) => {
      const onOpen = () => {
        ws.removeEventListener('open', onOpen)
        ws.removeEventListener('error', onError)
        resolve()
      }
      const onError = () => {
        ws.removeEventListener('open', onOpen)
        ws.removeEventListener('error', onError)
        resolve()
      }
      ws.addEventListener('open', onOpen)
      ws.addEventListener('error', onError)
      setTimeout(resolve, 2000)
    })
  }
  return ws
}

/**
 * Extract all generated image descriptors from ComfyUI history output object.
 */
export function extractComfyOutputs(historyData, promptId) {
  const promptData = (historyData && promptId && historyData[promptId]) ? historyData[promptId] : historyData
  if (!promptData) return []
  const outputs = promptData.outputs || {}
  const images = []
  for (const nodeOutput of Object.values(outputs)) {
    if (Array.isArray(nodeOutput?.images)) {
      for (const img of nodeOutput.images) {
        images.push(img)
      }
    }
  }
  return images
}

/**
 * Execute a ComfyUI prompt request and await completion.
 * Handles WebSocket connection, event tracking, live previews,
 * history extraction, and polling fallback.
 *
 * @param {Object} backendRequest - Object returned by buildBackendRequest for ComfyUI
 * @param {Object} callbacks - { onProgress(data), onPreview(url), onExecuting(data), onStatus(data) }
 * @returns {Promise<{ promptId: string, images: Array<{ filename: string, subfolder: string, type: string }> }>}
 */
export async function executeComfyPrompt(backendRequest, callbacks = {}) {
  const baseUrl = backendRequest.baseUrl
  const outputImages = []
  let executionFinished = false
  let targetPromptId = null
  let resolveExecution
  let rejectExecution

  const executionPromise = new Promise((resolve, reject) => {
    resolveExecution = resolve
    rejectExecution = reject
  })

  const handleCompletion = async () => {
    if (executionFinished) return
    executionFinished = true

    // Inspect ComfyUI history to ensure no output images were missed
    if (targetPromptId) {
      try {
        const hist = await getComfyHistory(baseUrl, targetPromptId)
        if (hist) {
          const histImages = extractComfyOutputs(hist, targetPromptId)
          for (const img of histImages) {
            if (!outputImages.some(existing => existing.filename === img.filename)) {
              outputImages.push(img)
            }
          }
        }
      } catch (e) {
        console.warn('Could not fetch ComfyUI history for prompt:', e)
      }
    }

    callbacks.onProgress?.({ value: 1, max: 1, prompt_id: targetPromptId })
    resolveExecution(outputImages)
  }

  const wsCallbacks = {
    onProgress: (data) => {
      if (targetPromptId && data.prompt_id === targetPromptId) {
        callbacks.onProgress?.(data)
      }
    },
    onExecuting: (data) => {
      if (targetPromptId && data.prompt_id === targetPromptId) {
        if (data.node === null) {
          handleCompletion()
        } else {
          callbacks.onExecuting?.(data)
        }
      }
    },
    onExecuted: (data) => {
      if (targetPromptId && data.prompt_id === targetPromptId && data.output?.images) {
        for (const img of data.output.images) {
          if (!outputImages.some(existing => existing.filename === img.filename)) {
            outputImages.push(img)
          }
        }
      }
    },
    onPreview: (previewUrl) => {
      callbacks.onPreview?.(previewUrl)
    },
    onError: (data) => {
      if (!targetPromptId || data.prompt_id === targetPromptId) {
        console.error('ComfyUI execution error:', data)
        rejectExecution(new Error(data.exception_message || 'ComfyUI execution error'))
      }
    },
    onStatus: (data) => {
      callbacks.onStatus?.(data)
    }
  }

  // 1. Ensure WebSocket is connected BEFORE sending the prompt so no messages are lost
  await ensureComfyWebSocket(baseUrl, wsCallbacks)

  // 2. Submit prompt to ComfyUI
  const response = await fetch(backendRequest.requestUrl, {
    method: 'POST',
    headers: backendRequest.headers,
    body: JSON.stringify(backendRequest.payload),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`ComfyUI prompt failed (${response.status}): ${errorText}`)
  }

  const result = await response.json()
  targetPromptId = result.prompt_id
  if (!targetPromptId) {
    throw new Error('ComfyUI did not return a prompt_id')
  }

  // 3. Fallback polling on /history/{targetPromptId} in case WS message is missed or drops
  const pollInterval = setInterval(async () => {
    if (executionFinished) {
      clearInterval(pollInterval)
      return
    }
    try {
      const hist = await getComfyHistory(baseUrl, targetPromptId)
      if (hist) {
        const entry = hist[targetPromptId] || hist
        if (entry?.status?.completed || (entry?.outputs && Object.keys(entry.outputs).length > 0)) {
          clearInterval(pollInterval)
          await handleCompletion()
        }
      }
    } catch (_) {
      // Poll retry
    }
  }, 1000)

  try {
    const images = await executionPromise
    return { promptId: targetPromptId, images }
  } finally {
    clearInterval(pollInterval)
  }
}

/**
 * Close the active ComfyUI WebSocket connection.
 */
export function closeComfyWebSocket() {
  if (comfyState.wsConnection && comfyState.wsConnection.readyState !== WebSocket.CLOSED) {
    comfyState.wsConnection.close()
  }
  comfyState.wsConnection = null
  comfyState.activeCallbacks = null
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
  } else if (!comfyState.activeWorkflowId && comfyState.workflows.length > 0) {
    comfyState.activeWorkflowId = comfyState.workflows[0].id
  }
}
