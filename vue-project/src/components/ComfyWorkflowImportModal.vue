<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { importWorkflow, addWorkflow, saveComfyWorkflows } from '@/backends/comfyui'

const props = defineProps({
  baseUrl: { type: String, required: true },
})

const emit = defineEmits(['close', 'imported'])

// ── State ─────────────────────────────────────────────────────────────
const step = ref('upload')  // 'upload' | 'select' | 'saving'
const workflowName = ref('')
const workflowData = ref(null)
const allInputs = ref([])
const errorMessage = ref('')
const isDragging = ref(false)
const isLoading = ref(false)

// ── File Handling ─────────────────────────────────────────────────────
const fileInputRef = ref(null)

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
    step.value = 'select'
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

// ── Input Selection ───────────────────────────────────────────────────
function toggleInput(input) {
  input.exposed = !input.exposed
}

function toggleAll() {
  const allExposed = allInputs.value.every(i => i.exposed)
  allInputs.value.forEach(i => { i.exposed = !allExposed })
}

const selectedInputs = computed(() =>
  allInputs.value
    .filter(i => i.exposed)
    .sort((a, b) => a.order - b.order)
)

const selectedCount = computed(() => selectedInputs.value.length)

// ── Drag & Drop Reordering ────────────────────────────────────────────
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

  // Swap orders
  const tempOrder = draggedItem.order
  draggedItem.order = targetItem.order
  targetItem.order = tempOrder

  dragIndex.value = index
}

function endDrag() {
  dragIndex.value = null
}

// ── Grouped Inputs ────────────────────────────────────────────────────
const groupedInputs = computed(() => {
  const groups = {}
  allInputs.value.forEach(input => {
    const key = `${input.nodeId}_${input.nodeTitle}`
    if (!groups[key]) {
      groups[key] = {
        nodeId: input.nodeId,
        nodeTitle: input.nodeTitle,
        classType: input.classType,
        inputs: [],
      }
    }
    groups[key].inputs.push(input)
  })
  return Object.values(groups)
})

// ── Input Type Display ────────────────────────────────────────────────
function getTypeLabel(spec) {
  switch (spec.type) {
    case 'int': return 'Integer'
    case 'float': return 'Float'
    case 'text': return 'Text'
    case 'textarea': return 'Text (Multi-line)'
    case 'select': return 'Dropdown'
    case 'boolean': return 'Toggle'
    default: return spec.type
  }
}

function getTypeColor(spec) {
  switch (spec.type) {
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
    return val.length > 60 ? val.substring(0, 60) + '…' : val
  }
  if (typeof val === 'boolean') return val ? 'true' : 'false'
  return String(val)
}

// ── Save ──────────────────────────────────────────────────────────────
async function saveWorkflow() {
  if (!workflowData.value || selectedCount.value === 0) return

  step.value = 'saving'

  // Renumber order for selected inputs
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
    <div class="w-full max-w-2xl max-h-[85vh] bg-[#0F0F16] border border-[#2A2A35] rounded-2xl shadow-2xl flex flex-col overflow-hidden">

      <!-- Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-[#2A2A35] flex-shrink-0">
        <div>
          <h3 class="text-lg font-semibold text-[#FAF8F5]">Import ComfyUI Workflow</h3>
          <p class="text-xs text-gray-500 mt-0.5">
            {{ step === 'upload' ? 'Select a workflow JSON file' : step === 'select' ? 'Choose which inputs to expose in the UI' : 'Saving...' }}
          </p>
        </div>
        <div class="flex items-center gap-3">
          <!-- Step indicator -->
          <div class="flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full transition-colors"
              :class="step === 'upload' ? 'bg-blue-400' : 'bg-emerald-400'"></span>
            <span class="w-2 h-2 rounded-full transition-colors"
              :class="step === 'select' ? 'bg-blue-400' : step === 'saving' ? 'bg-emerald-400' : 'bg-[#2A2A35]'"></span>
            <span class="w-2 h-2 rounded-full transition-colors"
              :class="step === 'saving' ? 'bg-blue-400 animate-pulse' : 'bg-[#2A2A35]'"></span>
          </div>
          <button @click="$emit('close')" class="text-gray-400 hover:text-[#FAF8F5] p-1 rounded transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Step 1: Upload -->
      <div v-if="step === 'upload'" class="flex-1 p-5">
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

      <!-- Step 2: Select Inputs -->
      <template v-if="step === 'select'">
        <div class="flex-1 overflow-y-auto p-5 space-y-4 min-h-0">
          <!-- Workflow Name -->
          <div class="space-y-1.5">
            <label class="text-[10px] uppercase tracking-[0.2em] text-gray-500">Workflow Name</label>
            <input v-model="workflowName" type="text" placeholder="My Workflow"
              class="w-full rounded-xl border border-[#2A2A35] bg-[#0A0A10] px-3 py-2.5 text-sm text-[#FAF8F5] placeholder-gray-600 focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/20 focus:outline-none transition-all" />
          </div>

          <!-- Select All Toggle -->
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-gray-300">Select Inputs to Expose</span>
              <span class="text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full border border-blue-500/30">
                {{ selectedCount }} / {{ allInputs.length }}
              </span>
            </div>
            <button @click="toggleAll" class="text-xs text-blue-400 hover:text-blue-300 transition-colors">
              {{ allInputs.every(i => i.exposed) ? 'Deselect All' : 'Select All' }}
            </button>
          </div>

          <!-- Grouped Input List -->
          <div v-for="group in groupedInputs" :key="group.nodeId" class="space-y-2">
            <div class="flex items-center gap-2">
              <span class="text-xs font-semibold text-[#FAF8F5]">{{ group.nodeTitle }}</span>
              <span class="text-[10px] text-gray-600 font-mono">{{ group.classType }}</span>
              <span class="text-[10px] text-gray-700 font-mono">#{{ group.nodeId }}</span>
            </div>

            <div v-for="input in group.inputs" :key="`${input.nodeId}-${input.inputKey}`"
              class="flex items-center gap-3 rounded-xl border px-3 py-2.5 cursor-pointer transition-all group/item"
              :class="input.exposed
                ? 'border-blue-500/40 bg-blue-500/8 ring-1 ring-blue-500/20'
                : 'border-[#232836] bg-[#111118]/60 hover:border-[#3A3A48]'"
              @click="toggleInput(input)">

              <!-- Checkbox -->
              <div class="flex-shrink-0 w-5 h-5 rounded border flex items-center justify-center transition-colors"
                :class="input.exposed
                  ? 'bg-blue-500 border-blue-500'
                  : 'border-[#3A3A48] bg-[#0A0A10]'">
                <svg v-if="input.exposed" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </div>

              <!-- Input Info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="text-sm font-medium" :class="input.exposed ? 'text-[#FAF8F5]' : 'text-gray-300'">
                    {{ input.inputKey }}
                  </span>
                  <span class="text-[10px] font-mono px-1.5 py-0.5 rounded-full border"
                    :class="getTypeColor(input.spec)">
                    {{ getTypeLabel(input.spec) }}
                  </span>
                </div>
                <p v-if="input.spec.tooltip" class="text-[11px] text-gray-500 mt-0.5 line-clamp-1">
                  {{ input.spec.tooltip }}
                </p>
              </div>

              <!-- Current Value -->
              <div class="flex-shrink-0 max-w-[180px]">
                <span class="text-xs text-gray-400 font-mono truncate block">{{ formatValue(input) }}</span>
              </div>
            </div>
          </div>

          <!-- Selected Order Preview -->
          <div v-if="selectedCount > 0" class="space-y-2 pt-2 border-t border-[#232836]">
            <div class="flex items-center gap-2">
              <span class="text-xs font-semibold text-[#FAF8F5]">Input Order</span>
              <span class="text-[10px] text-gray-600">Drag to reorder</span>
            </div>
            <div class="space-y-1">
              <div v-for="(input, index) in selectedInputs" :key="`order-${input.nodeId}-${input.inputKey}`"
                class="flex items-center gap-2 rounded-lg bg-[#151820] border border-[#232836] px-3 py-2 cursor-grab active:cursor-grabbing"
                draggable="true"
                @dragstart="startDrag(index, $event)"
                @dragover="onDragOver(index, $event)"
                @dragend="endDrag">
                <svg class="w-4 h-4 text-gray-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8h16M4 16h16" />
                </svg>
                <span class="text-xs font-mono text-gray-500 w-5">{{ index + 1 }}</span>
                <span class="text-sm text-gray-200 truncate">{{ input.nodeTitle }} → {{ input.inputKey }}</span>
                <span class="text-[10px] font-mono px-1.5 py-0.5 rounded-full border ml-auto"
                  :class="getTypeColor(input.spec)">
                  {{ getTypeLabel(input.spec) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-between px-5 py-4 border-t border-[#2A2A35] flex-shrink-0 bg-[#0D0D12]">
          <button @click="step = 'upload'"
            class="text-sm text-gray-300 hover:text-[#FAF8F5] px-4 py-2 rounded-lg transition-colors">
            ← Back
          </button>
          <div class="flex items-center gap-3">
            <button @click="$emit('close')"
              class="text-sm text-gray-400 hover:text-[#FAF8F5] px-4 py-2 rounded-lg transition-colors">
              Cancel
            </button>
            <button @click="saveWorkflow"
              :disabled="selectedCount === 0 || !workflowName.trim()"
              :class="selectedCount === 0 || !workflowName.trim()
                ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20'"
              class="text-sm font-medium px-5 py-2.5 rounded-xl transition-colors flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              Import ({{ selectedCount }} inputs)
            </button>
          </div>
        </div>
      </template>

      <!-- Step 3: Saving -->
      <div v-if="step === 'saving'" class="flex-1 flex items-center justify-center p-12">
        <div class="text-center">
          <svg class="animate-spin w-10 h-10 text-blue-400 mx-auto mb-4" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
          <p class="text-sm text-gray-300">Saving workflow...</p>
        </div>
      </div>

    </div>
  </div>
</template>
