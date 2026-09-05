<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { importWorkflow, addWorkflow, saveComfyWorkflows, findPositiveAndNegativeNodes } from '@/backends/comfyui'

const props = defineProps({
  baseUrl: { type: String, required: true },
  workflowToEdit: { type: Object, default: null },
})

const emit = defineEmits(['close', 'imported'])

// ── Wizard Steps ───────────────────────────────────────────────────────
const WIZARD_STEPS = [
  { id: 'upload', stepNum: 1, title: 'Import JSON', desc: 'Select or drag-and-drop a workflow JSON file' },
  { id: 'checkpoint', stepNum: 2, title: 'Select Checkpoint Input', desc: 'Choose the model loader input (ckpt_name)' },
  { id: 'loras', stepNum: 3, title: 'Add LoRAs', desc: 'Select LoRA model and strength inputs' },
  { id: 'positive_prompt', stepNum: 4, title: 'Select Positive Prompt', desc: 'Choose which text input is the Positive Prompt' },
  { id: 'negative_prompt', stepNum: 5, title: 'Select Negative Prompt', desc: 'Choose which text input is the Negative Prompt' },
  { id: 'resolution', stepNum: 6, title: 'Select Resolution', desc: 'Select width and height inputs for aspect ratio' },
  { id: 'image_input', stepNum: 7, title: 'Select Image Input (Img2Img)', desc: 'Select input image node for img2img / image processing' },
  { id: 'advanced', stepNum: 8, title: 'Advanced Settings', desc: 'Select sampler, steps, cfg, seed inputs' },
  { id: 'other', stepNum: 9, title: 'Other Workflow Inputs', desc: 'Select any other custom workflow inputs to expose' },
  { id: 'review', stepNum: 10, title: 'Review & Save', desc: 'Confirm exposed inputs and save workflow' }
]

const currentStepId = ref('upload')
const workflowName = ref('')
const workflowData = ref(null)
const allInputs = ref([])
const errorMessage = ref('')
const isDragging = ref(false)
const isLoading = ref(false)
const fileInputRef = ref(null)

const currentStepObj = computed(() => WIZARD_STEPS.find(s => s.id === currentStepId.value) || WIZARD_STEPS[0])

const tracedPromptNodes = computed(() => {
  if (!workflowData.value?.workflow) return { posNodeId: null, negNodeId: null }
  return findPositiveAndNegativeNodes(workflowData.value.workflow)
})

// Candidates per step
function getCandidatesForStep(stepId) {
  if (!allInputs.value || allInputs.value.length === 0) return []

  switch (stepId) {
    case 'checkpoint':
      return allInputs.value.filter(input => {
        const k = (input.inputKey || '').toLowerCase()
        const c = (input.classType || '').toLowerCase()
        return k === 'ckpt_name' || k === 'unet_name' || k === 'model_name' || c.includes('checkpoint') || c.includes('unet')
      })

    case 'loras':
      return allInputs.value.filter(input => {
        const k = (input.inputKey || '').toLowerCase()
        const c = (input.classType || '').toLowerCase()
        return c.includes('lora') || k === 'lora_name' || k === 'strength_model' || k === 'strength_clip'
      })

    case 'positive_prompt':
      const ckptLoras = [...getCandidatesForStep('checkpoint'), ...getCandidatesForStep('loras')]
      return allInputs.value.filter(input => {
        const k = (input.inputKey || '').toLowerCase()
        const c = (input.classType || '').toLowerCase()
        const isText = input.spec?.type === 'textarea' || input.spec?.type === 'text' || k === 'text' || c.includes('cliptextencode') || c.includes('prompt')
        return isText && !ckptLoras.includes(input)
      })

    case 'negative_prompt':
      const selectedPos = allInputs.value.find(i => i.role === 'positive')
      const posCandidates = getCandidatesForStep('positive_prompt')
      return posCandidates.filter(input => input !== selectedPos)

    case 'resolution':
      return allInputs.value.filter(input => {
        const k = (input.inputKey || '').toLowerCase()
        const c = (input.classType || '').toLowerCase()
        return k === 'width' || k === 'height' || k === 'resolution' || k === 'size' || c.includes('emptylatent')
      })

    case 'image_input':
      return allInputs.value.filter(input => {
        const k = (input.inputKey || '').toLowerCase()
        const c = (input.classType || '').toLowerCase()
        return k === 'image' || k.includes('image_input') || c.includes('loadimage')
      })

    case 'advanced':
      return allInputs.value.filter(input => {
        const k = (input.inputKey || '').toLowerCase()
        const c = (input.classType || '').toLowerCase()
        return k === 'cfg' || k === 'cfg_scale' || k === 'sampler_name' || k === 'steps' || k === 'seed' || k === 'scheduler' || k === 'denoise' || k === 'stop_at_clip_layer' || k === 'clip_skip' || c.includes('ksampler')
      })

    case 'other':
      const categorized = [
        ...getCandidatesForStep('checkpoint'),
        ...getCandidatesForStep('loras'),
        ...getCandidatesForStep('positive_prompt'),
        ...getCandidatesForStep('resolution'),
        ...getCandidatesForStep('image_input'),
        ...getCandidatesForStep('advanced'),
      ]
      return allInputs.value.filter(input => !categorized.includes(input))

    default:
      return []
  }
}

const currentStepCandidates = computed(() => getCandidatesForStep(currentStepId.value))

const groupedStepCandidates = computed(() => {
  const groups = {}
  currentStepCandidates.value.forEach(input => {
    const key = `${input.nodeId}_${input.nodeTitle}`
    if (!groups[key]) {
      groups[key] = {
        nodeId: input.nodeId,
        nodeTitle: input.nodeTitle,
        classType: input.classType,
        inputs: []
      }
    }
    groups[key].inputs.push(input)
  })
  return Object.values(groups)
})
function applyAutoRecommendations() {
  if (!allInputs.value || !workflowData.value?.workflow) return
  const { posNodeId, negNodeId } = tracedPromptNodes.value

  allInputs.value.forEach(input => {
    const k = (input.inputKey || '').toLowerCase()
    const nodeId = String(input.nodeId)

    if (nodeId === String(posNodeId) && (input.spec?.type === 'textarea' || k === 'text')) {
      input.recommendedRole = 'positive'
      if (!input.role) input.role = 'positive'
      input.exposed = true
    } else if (nodeId === String(negNodeId) && (input.spec?.type === 'textarea' || k === 'text')) {
      input.recommendedRole = 'negative'
      if (!input.role) input.role = 'negative'
      input.exposed = true
    } else if (k === 'ckpt_name' || k === 'unet_name') {
      input.recommendedRole = 'checkpoint'
      if (!input.role) input.role = 'checkpoint'
      input.exposed = true
    } else if (k === 'width') {
      input.recommendedRole = 'width'
      if (!input.role) input.role = 'width'
      input.exposed = true
    } else if (k === 'height') {
      input.recommendedRole = 'height'
      if (!input.role) input.role = 'height'
      input.exposed = true
    } else if (k === 'image' || k.includes('image_input')) {
      input.recommendedRole = 'image'
      if (!input.role) input.role = 'image'
      input.exposed = true
    } else if (k === 'seed' || k === 'steps' || k === 'cfg' || k === 'sampler_name') {
      input.recommendedRole = k
      if (!input.role) input.role = k
      input.exposed = true
    }
  })
}

function findNextValidStepId(fromId) {
  const currentIndex = WIZARD_STEPS.findIndex(s => s.id === fromId)
  for (let i = currentIndex + 1; i < WIZARD_STEPS.length; i++) {
    const s = WIZARD_STEPS[i]
    if (s.id === 'review' || s.id === 'upload') return s.id
    if (getCandidatesForStep(s.id).length > 0) return s.id
  }
  return 'review'
}

function findPrevValidStepId(fromId) {
  const currentIndex = WIZARD_STEPS.findIndex(s => s.id === fromId)
  for (let i = currentIndex - 1; i >= 0; i--) {
    const s = WIZARD_STEPS[i]
    if (s.id === 'upload') return s.id
    if (getCandidatesForStep(s.id).length > 0) return s.id
  }
  return 'upload'
}

function goToNextStep() {
  currentStepId.value = findNextValidStepId(currentStepId.value)
}

function goToPrevStep() {
  currentStepId.value = findPrevValidStepId(currentStepId.value)
}

function selectPositivePrompt(input) {
  allInputs.value.forEach(i => {
    if (i.role === 'positive') i.role = null
  })
  input.exposed = true
  input.role = 'positive'
}

function selectNegativePrompt(input) {
  allInputs.value.forEach(i => {
    if (i.role === 'negative') i.role = null
  })
  input.exposed = true
  input.role = 'negative'
}

function toggleCandidateExposed(input, defaultRole = null) {
  input.exposed = !input.exposed
  if (input.exposed && defaultRole && !input.role) {
    input.role = defaultRole
  }
}

// File handling
function openFilePicker() {
  fileInputRef.value?.click()
}

async function handleFile(file) {
  if (!file) return
  errorMessage.value = ''
  isLoading.value = true

  try {
    const text = await file.text()
    const json = JSON.parse(text)
    const name = file.name.replace(/\.json$/i, '')
    workflowName.value = name

    const result = await importWorkflow(json, name, props.baseUrl)
    workflowData.value = result
    allInputs.value = result.allInputs.map((input, i) => ({
      ...input,
      exposed: false,
      order: i,
    }))

    applyAutoRecommendations()
    currentStepId.value = findNextValidStepId('upload')
  } catch (e) {
    console.error('Failed to import workflow:', e)
    errorMessage.value = `Failed to parse workflow: ${e.message}`
  } finally {
    isLoading.value = false
  }
}

function handleFileInputChange(event) {
  const file = event.target.files?.[0]
  if (file) handleFile(file)
  event.target.value = ''
}

function handleDrop(event) {
  event.preventDefault()
  isDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) handleFile(file)
}

onMounted(async () => {
  if (props.workflowToEdit) {
    isLoading.value = true
    try {
      workflowName.value = props.workflowToEdit.name || ''
      const result = await importWorkflow(props.workflowToEdit.workflow, props.workflowToEdit.name, props.baseUrl)
      workflowData.value = {
        id: props.workflowToEdit.id,
        workflow: props.workflowToEdit.workflow
      }

      const exposedMap = new Map()
      ;(props.workflowToEdit.exposedInputs || []).forEach((exp, idx) => {
        exposedMap.set(`${exp.nodeId}.${exp.inputKey}`, { order: exp.order ?? idx, label: exp.label, value: exp.value, role: exp.role })
      })

      allInputs.value = result.allInputs.map((input, i) => {
        const key = `${input.nodeId}.${input.inputKey}`
        const matched = exposedMap.get(key)
        if (matched) {
          return {
            ...input,
            value: matched.value !== undefined ? matched.value : input.value,
            label: matched.label || input.label,
            exposed: true,
            order: matched.order,
            role: matched.role || null,
          }
        }
        return {
          ...input,
          exposed: false,
          order: 999 + i,
        }
      })

      applyAutoRecommendations()
      currentStepId.value = findNextValidStepId('upload')
    } catch (e) {
      console.error('Failed to load workflow for editing:', e)
      errorMessage.value = `Failed to parse workflow: ${e.message}`
    } finally {
      isLoading.value = false
    }
  }
})

const selectedInputs = computed(() =>
  allInputs.value
    .filter(i => i.exposed)
    .sort((a, b) => a.order - b.order)
)
const selectedCount = computed(() => selectedInputs.value.length)

// Drag and drop reordering
const dragIndex = ref(null)
function startDrag(index, event) {
  dragIndex.value = index
  event.dataTransfer.effectAllowed = 'move'
}
function onDragOver(index, event) {
  event.preventDefault()
  if (dragIndex.value === null || dragIndex.value === index) return
  const selected = selectedInputs.value
  const draggedItem = selected[dragIndex.value]
  const targetItem = selected[index]
  const tempOrder = draggedItem.order
  draggedItem.order = targetItem.order
  targetItem.order = tempOrder
  dragIndex.value = index
}
function endDrag() {
  dragIndex.value = null
}

function getTypeLabel(spec) {
  switch (spec?.type) {
    case 'int': return 'Integer'
    case 'float': return 'Float'
    case 'text': return 'Text'
    case 'textarea': return 'Text (Multi-line)'
    case 'select': return 'Dropdown'
    case 'boolean': return 'Toggle'
    default: return spec?.type || 'Input'
  }
}

function getTypeColor(spec) {
  switch (spec?.type) {
    case 'int':
    case 'float':
      return 'bg-blue-500/20 text-blue-300 border-blue-500/30'
    case 'text':
    case 'textarea':
      return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
    case 'select':
      return 'bg-purple-500/20 text-purple-300 border-purple-500/30'
    case 'boolean':
      return 'bg-amber-500/20 text-amber-300 border-amber-500/30'
    default:
      return 'bg-gray-500/20 text-gray-300 border-gray-500/30'
  }
}

function formatValue(input) {
  const val = input.value
  if (typeof val === 'string') {
    return val.length > 80 ? val.substring(0, 80) + '…' : val
  }
  if (typeof val === 'boolean') return val ? 'true' : 'false'
  return String(val ?? '')
}

async function saveWorkflow() {
  if (!workflowData.value || selectedCount.value === 0) return

  currentStepId.value = 'saving'

  const exposed = selectedInputs.value.map((input, i) => ({
    ...input,
    order: i,
    exposed: true,
  }))

  const finalWorkflow = {
    id: workflowData.value.id,
    name: workflowName.value || 'Untitled Workflow',
    workflow: workflowData.value.workflow,
    exposedInputs: exposed,
  }

  addWorkflow(finalWorkflow)
  await saveComfyWorkflows()

  emit('imported', finalWorkflow)
  emit('close')
}
</script>

<template>
  <div class="fixed inset-0 z-[60] flex items-center justify-center bg-black/75 backdrop-blur-sm"
    @click.self="$emit('close')">
    <div class="w-full max-w-3xl max-h-[85vh] bg-[#0F0F16] border border-[#2A2A35] rounded-2xl shadow-2xl flex flex-col overflow-hidden">

      <!-- Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-[#2A2A35] flex-shrink-0">
        <div>
          <div class="flex items-center gap-2">
            <h3 class="text-lg font-semibold text-[#FAF8F5]">
              {{ props.workflowToEdit ? 'Edit ComfyUI Workflow' : 'Import ComfyUI Workflow' }}
            </h3>
            <span v-if="currentStepId !== 'upload' && currentStepId !== 'saving' && currentStepId !== 'review'"
              class="text-xs bg-blue-500/20 text-blue-300 px-2.5 py-0.5 rounded-full border border-blue-500/30 font-medium">
              Step {{ currentStepObj.stepNum - 1 }} of 8: {{ currentStepObj.title }}
            </span>
          </div>
          <p class="text-xs text-gray-500 mt-0.5">{{ currentStepObj.desc }}</p>
        </div>
        <div class="flex items-center gap-3">
          <button @click="$emit('close')" class="text-gray-400 hover:text-[#FAF8F5] p-1 rounded transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Step 1: Upload -->
      <div v-if="currentStepId === 'upload'" class="flex-1 p-5">
        <input ref="fileInputRef" type="file" accept=".json" class="hidden" @change="handleFileInputChange" />

        <div class="border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer"
          :class="isDragging ? 'border-blue-400 bg-blue-500/10' : 'border-[#2A2A35] hover:border-blue-500/50 hover:bg-[#151820]'"
          @click="openFilePicker"
          @dragenter.prevent="isDragging = true"
          @dragover.prevent
          @dragleave="isDragging = false"
          @drop="handleDrop">

          <div v-if="isLoading" class="flex flex-col items-center gap-3">
            <svg class="animate-spin w-10 h-10 text-blue-400" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
            </svg>
            <p class="text-sm text-gray-300">Parsing workflow & fetching node info...</p>
          </div>

          <template v-else>
            <svg class="w-12 h-12 mx-auto mb-3 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p class="text-base font-medium text-[#FAF8F5] mb-1">Drop workflow JSON here</p>
            <p class="text-sm text-gray-400">or click to browse</p>
            <p class="text-xs text-gray-600 mt-3">Supports ComfyUI API format (.json)</p>
          </template>
        </div>

        <div v-if="errorMessage"
          class="mt-4 flex items-start gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3">
          <svg class="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p class="text-sm text-red-300">{{ errorMessage }}</p>
        </div>
      </div>

      <!-- Step 4 & 5: Text Prompt Selection Steps Grouped by Node -->
      <template v-else-if="currentStepId === 'positive_prompt' || currentStepId === 'negative_prompt'">
        <div class="flex-1 overflow-y-auto p-5 space-y-4 min-h-0">
          <div class="flex items-center justify-between">
            <h4 class="text-sm font-semibold text-[#FAF8F5]">
              {{ currentStepId === 'positive_prompt' ? 'Choose Positive Prompt Node' : 'Choose Negative Prompt Node' }}
            </h4>
            <span class="text-xs text-gray-500">{{ currentStepCandidates.length }} candidate text input(s)</span>
          </div>

          <div class="space-y-4">
            <div v-for="group in groupedStepCandidates" :key="group.nodeId" class="space-y-2">
              <div class="flex items-center gap-2 px-1">
                <span class="text-xs font-bold text-[#FAF8F5]">{{ group.nodeTitle }}</span>
                <span class="text-[11px] font-mono text-gray-400">{{ group.classType }}#{{ group.nodeId }}</span>
              </div>

              <div v-for="input in group.inputs" :key="`${input.nodeId}-${input.inputKey}`"
                class="rounded-xl border p-4 cursor-pointer transition-all space-y-2"
                :class="((currentStepId === 'positive_prompt' && input.role === 'positive') || (currentStepId === 'negative_prompt' && input.role === 'negative'))
                  ? 'border-blue-500 bg-blue-500/10 ring-1 ring-blue-500/30'
                  : 'border-[#232836] bg-[#111118]/60 hover:border-[#3A3A48]'"
                @click="currentStepId === 'positive_prompt' ? selectPositivePrompt(input) : selectNegativePrompt(input)">

                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-semibold text-[#FAF8F5]">{{ input.inputKey }}</span>
                    <span class="text-[10px] font-mono px-2 py-0.5 rounded-full border" :class="getTypeColor(input.spec)">
                      {{ getTypeLabel(input.spec) }}
                    </span>
                  </div>

                  <div class="flex items-center gap-2">
                    <span v-if="(currentStepId === 'positive_prompt' && String(input.nodeId) === String(tracedPromptNodes.posNodeId)) || (currentStepId === 'negative_prompt' && String(input.nodeId) === String(tracedPromptNodes.negNodeId))"
                      class="text-[10px] bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full border border-amber-500/30 font-medium">
                      ★ Recommended (Traced from KSampler)
                    </span>
                    <div class="w-5 h-5 rounded-full border flex items-center justify-center"
                      :class="((currentStepId === 'positive_prompt' && input.role === 'positive') || (currentStepId === 'negative_prompt' && input.role === 'negative'))
                        ? 'border-blue-500 bg-blue-500'
                        : 'border-gray-600 bg-[#0A0A10]'">
                      <div v-if="(currentStepId === 'positive_prompt' && input.role === 'positive') || (currentStepId === 'negative_prompt' && input.role === 'negative')"
                        class="w-2 h-2 rounded-full bg-white"></div>
                    </div>
                  </div>
                </div>

                <p v-if="input.spec?.tooltip" class="text-xs text-gray-500 italic">{{ input.spec.tooltip }}</p>

                <!-- Text Content Preview -->
                <div class="bg-[#0A0A10] border border-[#232836] rounded-lg p-3 text-xs text-gray-300 font-mono line-clamp-3 break-words">
                  {{ input.value || '(Empty prompt)' }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Steps 2, 3, 6, 7, 8, 9: Input Selection Cards Grouped by Node -->
      <template v-else-if="currentStepId !== 'review' && currentStepId !== 'saving'">
        <div class="flex-1 overflow-y-auto p-5 space-y-4 min-h-0">
          <div class="flex items-center justify-between">
            <h4 class="text-sm font-semibold text-[#FAF8F5]">{{ currentStepObj.title }}</h4>
            <span class="text-xs text-gray-500">{{ currentStepCandidates.length }} candidate input(s)</span>
          </div>

          <div class="space-y-4">
            <div v-for="group in groupedStepCandidates" :key="group.nodeId" class="space-y-2">
              <div class="flex items-center gap-2 px-1">
                <span class="text-xs font-bold text-[#FAF8F5]">{{ group.nodeTitle }}</span>
                <span class="text-[11px] font-mono text-gray-400">{{ group.classType }}#{{ group.nodeId }}</span>
              </div>

              <div v-for="input in group.inputs" :key="`${input.nodeId}-${input.inputKey}`"
                class="flex items-center gap-3 rounded-xl border px-4 py-3 cursor-pointer transition-all"
                :class="input.exposed
                  ? 'border-blue-500/50 bg-blue-500/10 ring-1 ring-blue-500/20'
                  : 'border-[#232836] bg-[#111118]/60 hover:border-[#3A3A48]'"
                @click="toggleCandidateExposed(input, currentStepId)">

                <div class="flex-shrink-0 w-5 h-5 rounded border flex items-center justify-center transition-colors"
                  :class="input.exposed ? 'bg-blue-500 border-blue-500' : 'border-[#3A3A48] bg-[#0A0A10]'">
                  <svg v-if="input.exposed" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                  </svg>
                </div>

                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span class="text-xs font-semibold text-blue-300">{{ input.inputKey }}</span>
                    <span class="text-[10px] font-mono px-1.5 py-0.5 rounded-full border" :class="getTypeColor(input.spec)">
                      {{ getTypeLabel(input.spec) }}
                    </span>
                    <span v-if="input.recommendedRole"
                      class="text-[10px] bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full border border-amber-500/30">
                      Recommended: {{ input.recommendedRole }}
                    </span>
                  </div>
                  <p v-if="input.spec?.tooltip" class="text-xs text-gray-500 mt-1 line-clamp-1">{{ input.spec.tooltip }}</p>
                </div>

                <div class="flex-shrink-0 max-w-[180px]">
                  <span class="text-xs text-gray-400 font-mono truncate block">{{ formatValue(input) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Step 10: Review & Save -->
      <template v-else-if="currentStepId === 'review'">
        <div class="flex-1 overflow-y-auto p-5 space-y-4 min-h-0">
          <div class="space-y-1.5">
            <label class="text-[10px] uppercase tracking-[0.2em] text-gray-500">Workflow Name</label>
            <input v-model="workflowName" type="text" placeholder="My Workflow"
              class="w-full rounded-xl border border-[#2A2A35] bg-[#0A0A10] px-3 py-2.5 text-sm text-[#FAF8F5] placeholder-gray-600 focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/20 focus:outline-none transition-all" />
          </div>

          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-sm font-semibold text-[#FAF8F5]">Summary of Exposed Inputs</span>
              <span class="text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full border border-blue-500/30">
                {{ selectedCount }} input(s) selected
              </span>
            </div>

            <div v-if="selectedCount === 0" class="text-xs text-gray-500 italic py-4 text-center">
              No inputs selected. Click Back to select inputs to expose in the UI.
            </div>

            <div v-else class="space-y-1.5">
              <div v-for="(input, index) in selectedInputs" :key="`review-${input.nodeId}-${input.inputKey}`"
                class="flex items-center gap-3 rounded-lg bg-[#151820] border border-[#232836] px-3 py-2.5 cursor-grab active:cursor-grabbing"
                draggable="true"
                @dragstart="startDrag(index, $event)"
                @dragover="onDragOver(index, $event)"
                @dragend="endDrag">
                <svg class="w-4 h-4 text-gray-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8h16M4 16h16" />
                </svg>
                <span class="text-xs font-mono text-gray-500 w-5">{{ index + 1 }}</span>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="text-sm text-gray-200 truncate">{{ input.nodeTitle }} → {{ input.inputKey }}</span>
                    <span v-if="input.role" class="text-[10px] bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded-full border border-purple-500/30 font-medium">
                      {{ input.role }}
                    </span>
                  </div>
                </div>
                <span class="text-[10px] font-mono px-1.5 py-0.5 rounded-full border" :class="getTypeColor(input.spec)">
                  {{ getTypeLabel(input.spec) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Step 11: Saving -->
      <div v-if="currentStepId === 'saving'" class="flex-1 flex items-center justify-center p-12">
        <div class="text-center">
          <svg class="animate-spin w-10 h-10 text-blue-400 mx-auto mb-4" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
          <p class="text-sm text-gray-300">Saving workflow...</p>
        </div>
      </div>

      <!-- Navigation Footer -->
      <div v-if="currentStepId !== 'saving'" class="flex items-center justify-between px-5 py-4 border-t border-[#2A2A35] flex-shrink-0 bg-[#0D0D12]">
        <button v-if="currentStepId !== 'upload'" @click="goToPrevStep"
          class="text-sm text-gray-300 hover:text-[#FAF8F5] px-4 py-2 rounded-lg transition-colors flex items-center gap-1">
          ← Back
        </button>
        <div v-else></div>

        <div class="flex items-center gap-3">
          <button v-if="currentStepId !== 'upload' && currentStepId !== 'review'" @click="skipStep"
            class="text-xs text-gray-400 hover:text-gray-200 px-3 py-2 rounded-lg transition-colors">
            Skip Step →
          </button>

          <button v-if="currentStepId === 'upload'" @click="openFilePicker"
            class="bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium px-5 py-2.5 rounded-xl transition-colors">
            Choose JSON File
          </button>

          <button v-else-if="currentStepId !== 'review'" @click="goToNextStep"
            class="bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium px-5 py-2.5 rounded-xl transition-colors">
            Next Step →
          </button>

          <button v-else @click="saveWorkflow"
            :disabled="selectedCount === 0 || !workflowName.trim()"
            :class="selectedCount === 0 || !workflowName.trim()
              ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
              : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-900/20'"
            class="text-sm font-medium px-5 py-2.5 rounded-xl transition-colors flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            Save Workflow ({{ selectedCount }} inputs)
          </button>
        </div>
      </div>

    </div>
  </div>
</template>
