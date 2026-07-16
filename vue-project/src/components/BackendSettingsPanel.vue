<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
  backendState,
  backendOptions,
  getBackendConfigStatus,
  loadBackendSettings,
  saveBackendSettings,
  setActiveBackend,
} from '@/backends'
import { apiUrl } from '@/api'
import { themes, applyTheme } from '@/theme'

const isLoaded = ref(false)
const saveState = ref('idle')
const lastSavedAt = ref(null)
let saveTimer = null

// AI Settings
const aiSettings = ref({
  default_model: '',
  default_vision_model: '',
  default_assistant_model: '',
  model_is_vision: false,
  use_thinking: false,
  manage_vram: false,
  override_temperature: false,
  temperature: 0.7,
})
const aiSaveState = ref('idle')
let lastSavedAiSettings = {}
async function loadAiSettings() {
  try {
    const res = await fetch(`${apiUrl}/ai-settings`)
    if (res.ok) {
      const data = await res.json()
      aiSettings.value = data
      lastSavedAiSettings = { ...data }
    }
  } catch (e) {
    console.error('Failed to load AI settings:', e)
  }
}

let aiSaveTimer = null
function scheduleAiSave() {
  if (!isLoaded.value) return
  if (aiSaveTimer) clearTimeout(aiSaveTimer)
  aiSaveState.value = 'saving'
  aiSaveTimer = setTimeout(async () => {
    try {
      const diff = {}
      for (const key in aiSettings.value) {
        if (aiSettings.value[key] !== lastSavedAiSettings[key]) {
          diff[key] = aiSettings.value[key]
        }
      }

      if (Object.keys(diff).length > 0) {
        await fetch(`${apiUrl}/ai-settings`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(diff),
        })
        lastSavedAiSettings = { ...aiSettings.value }
      }
      aiSaveState.value = 'saved'
    } catch (e) {
      console.error('Failed to save AI settings:', e)
      aiSaveState.value = 'error'
    }
  }, 400)
}

watch(aiSettings, scheduleAiSave, { deep: true })

const activeBackendId = computed({
  get: () => backendState.activeId,
  set: (value) => setActiveBackend(value),
})

const activeBackend = computed(() => {
  return backendOptions.find((backend) => backend.id === activeBackendId.value) || backendOptions[0]
})

const activeStatus = computed(() => getBackendConfigStatus(activeBackendId.value))

const formatTimestamp = (value) => {
  if (!value) return ''
  return new Date(value).toLocaleTimeString()
}

const getBackendBadge = (backendId) => {
  const status = getBackendConfigStatus(backendId)
  if (!status.ok) {
    return {
      label: 'Needs setup',
      className: 'bg-orange-500/20 text-orange-200 border border-orange-500/30',
    }
  }
  if (backendId === activeBackendId.value) {
    return {
      label: 'Active',
      className: 'bg-blue-500/20 text-blue-100 border border-blue-500/30',
    }
  }
  return {
    label: 'Configured',
    className: 'bg-emerald-500/20 text-emerald-100 border border-emerald-500/30',
  }
}

const ensureActiveConfig = () => {
  const backend = activeBackend.value
  if (!backend) return
  if (!backendState.configs[backend.id]) {
    backendState.configs[backend.id] = { ...backend.defaultConfig }
  }
}


const availableModels = ref([])
const showCustomDefaultModel = ref(false)
const showCustomVisionModel = ref(false)
const showCustomAssistantModel = ref(false)
const showCustomAutocompleteModel = ref(false)

const currentThemeKey = ref('classic')
const customColors = ref({
  background: '#0D0D12',
  accent: '#C9A84C',
  text: '#FAF8F5',
  border: '#2A2A35',
  panel: '#1A1A24',
  input: '#14141A'
})

function selectTheme(key) {
  currentThemeKey.value = key
  localStorage.setItem('selectedThemeKey', key)
  if (key === 'custom') {
    applyTheme(customColors.value)
    localStorage.setItem('customTheme', JSON.stringify(customColors.value))
  } else {
    const themeColors = themes[key]
    customColors.value = { ...themeColors }
    applyTheme(themeColors)
    localStorage.setItem('customTheme', JSON.stringify(themeColors))
  }
}

function updateCustomColor(colorKey, value) {
  customColors.value[colorKey] = value
  if (currentThemeKey.value !== 'custom') {
    currentThemeKey.value = 'custom'
    localStorage.setItem('selectedThemeKey', 'custom')
  }
  applyTheme(customColors.value)
  localStorage.setItem('customTheme', JSON.stringify(customColors.value))
}

async function loadAvailableModels() {
  try {
    const res = await fetch(`${apiUrl}/lmstudio/models`)
    if (res.ok) {
      availableModels.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to load available LM Studio models:', e)
  }
}

onMounted(async () => {
  await loadBackendSettings()
  await loadAiSettings()
  await loadAvailableModels()
  isLoaded.value = true
  ensureActiveConfig()

  const saved = localStorage.getItem('customTheme')
  const savedKey = localStorage.getItem('selectedThemeKey') || 'classic'
  currentThemeKey.value = savedKey
  if (savedKey === 'custom' && saved) {
    try {
      customColors.value = { ...customColors.value, ...JSON.parse(saved) }
    } catch(e) {}
  } else if (themes[savedKey]) {
    customColors.value = { ...themes[savedKey] }
  }
})

watch(activeBackendId, async (newVal, oldVal) => {
  ensureActiveConfig()
  if (newVal === oldVal || !isLoaded.value) return

  saveState.value = 'saving'
  try {
    await fetch(`${apiUrl}/backend-settings`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ activeId: newVal })
    })
    saveState.value = 'saved'
    lastSavedAt.value = Date.now()
  } catch (e) {
    console.error('Failed to save active backend:', e)
    saveState.value = 'error'
  }
})

let configSaveTimer = null
watch(
  () => backendState.configs[activeBackendId.value],
  (newConfig) => {
    if (!isLoaded.value) return
    if (configSaveTimer) clearTimeout(configSaveTimer)

    saveState.value = 'saving'
    const backendId = activeBackendId.value

    configSaveTimer = setTimeout(async () => {
      try {
        await fetch(`${apiUrl}/backend-settings`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            configs: {
              [backendId]: newConfig
            }
          })
        })
        saveState.value = 'saved'
        lastSavedAt.value = Date.now()
      } catch (e) {
        console.error('Failed to save backend config:', e)
        saveState.value = 'error'
      }
    }, 300)
  },
  { deep: true }
)
</script>

<template>
  <div class="space-y-5">

    <!-- Header -->
    <div class="flex items-center justify-between gap-3">
      <div>
        <h3 class="text-base font-semibold text-[#FAF8F5] tracking-tight">Backend Settings</h3>
        <p class="text-xs text-gray-500 mt-0.5">Switch adapters and configure connection details.</p>
      </div>
      <div class="flex items-center gap-1.5 text-[10px] font-mono px-2 py-1 rounded-full border" :class="saveState === 'saving'
        ? 'border-blue-500/40 text-blue-400 bg-blue-500/10'
        : 'border-[#2A2A35] text-gray-500 bg-transparent'">
        <span class="w-1.5 h-1.5 rounded-full"
          :class="saveState === 'saving' ? 'bg-blue-400 animate-pulse' : 'bg-emerald-400'"></span>
        <span v-if="saveState === 'saving'">Saving…</span>
        <span v-else-if="lastSavedAt">Saved {{ formatTimestamp(lastSavedAt) }}</span>
        <span v-else>Auto-save on</span>
      </div>
    </div>

    <!-- Backend Selector Strip -->
    <div class="space-y-1.5">
      <div class="text-[10px] uppercase tracking-[0.25em] text-gray-600 px-0.5">Adapter</div>
      <div class="flex flex-col gap-2">
        <button v-for="backend in backendOptions" :key="backend.id" type="button"
          class="group w-full rounded-2xl border px-4 py-3 text-left transition-all duration-200" :class="backend.id === activeBackendId
            ? 'border-blue-500/50 bg-blue-500/8 ring-1 ring-blue-500/30'
            : 'border-[#232836] bg-[#111118]/60 hover:border-[#3A3A48] hover:bg-[#151820]/80'"
          @click="activeBackendId = backend.id">
          <div class="flex items-center gap-3">
            <div class="flex-shrink-0 w-2 h-2 rounded-full transition-colors duration-200"
              :class="backend.id === activeBackendId ? 'bg-blue-400' : 'bg-[#2A2A35] group-hover:bg-[#3A3A48]'">
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium"
                  :class="backend.id === activeBackendId ? 'text-[#FAF8F5]' : 'text-gray-300'">
                  {{ backend.label }}
                </span>
                <span class="text-[10px] uppercase tracking-widest text-gray-600">{{ backend.type }}</span>
              </div>
              <p class="text-xs text-gray-500 mt-0.5 truncate">{{ backend.description }}</p>
            </div>
            <span class="flex-shrink-0 rounded-full px-2.5 py-0.5 text-[10px] font-mono border"
              :class="getBackendBadge(backend.id).className">
              {{ getBackendBadge(backend.id).label }}
            </span>
          </div>
        </button>
      </div>
    </div>

    <!-- Config Card -->
    <div class="rounded-2xl border border-[#232836] bg-[#0F0F16] overflow-hidden">
      <div class="flex items-center justify-between px-4 py-3 border-b border-[#1E1E28]">
        <div class="flex items-center gap-2">
          <svg class="w-3.5 h-3.5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
          </svg>
          <span class="text-xs font-semibold text-[#FAF8F5]">{{ activeBackend.label }}</span>
        </div>
        <span class="text-[10px] text-gray-600 font-mono">config</span>
      </div>
      <div class="p-4 space-y-4">
        <div v-if="!(activeBackend.fields || []).length" class="text-xs text-gray-500 text-center py-4">
          No configuration fields for this adapter.
        </div>
        <div v-for="field in (activeBackend.fields || [])" :key="field.key" class="space-y-1.5">
          <label class="text-[10px] uppercase tracking-[0.2em] text-gray-500 block">{{ field.label }}</label>
          <input v-model="backendState.configs[activeBackendId][field.key]" :type="field.type || 'text'"
            :placeholder="field.placeholder"
            class="w-full rounded-xl border border-[#2A2A35] bg-[#0A0A10] px-3 py-2.5 text-sm text-[#FAF8F5] placeholder-gray-600 focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/20 focus:outline-none transition-all" />
          <p v-if="field.hint" class="text-[11px] text-gray-600 leading-relaxed">{{ field.hint }}</p>
        </div>
      </div>
      <div v-if="!activeStatus.ok"
        class="mx-4 mb-4 flex items-start gap-2.5 rounded-xl border border-orange-500/20 bg-orange-500/8 px-3 py-2.5">
        <svg class="w-3.5 h-3.5 text-orange-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor"
          viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div>
          <p class="text-[11px] font-medium text-orange-300">Missing required fields</p>
          <p class="text-[11px] text-orange-400/70 mt-0.5 font-mono">{{ activeStatus.missingFields.join(' · ') }}</p>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════ -->
    <!-- AI Generation Settings                         -->
    <!-- ═══════════════════════════════════════════════ -->
    <div class="rounded-2xl border border-[#232836] bg-[#0F0F16] overflow-hidden">
      <div class="flex items-center justify-between px-4 py-3 border-b border-[#1E1E28]">
        <div class="flex items-center gap-2">
          <svg class="w-3.5 h-3.5 text-[#C9A84C]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <span class="text-xs font-semibold text-[#FAF8F5]">AI Generation</span>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="w-1.5 h-1.5 rounded-full"
            :class="aiSaveState === 'saving' ? 'bg-[#C9A84C] animate-pulse' : aiSaveState === 'error' ? 'bg-red-400' : 'bg-emerald-400'"></span>
          <span class="text-[10px] text-gray-600 font-mono">
            {{ aiSaveState === 'saving' ? 'saving…' : aiSaveState === 'error' ? 'error' : 'synced' }}
          </span>
        </div>
      </div>

      <div class="p-4 space-y-5">
        <!-- Default Model -->
        <div class="space-y-1.5">
          <div class="flex justify-between items-center">
            <label class="text-[10px] uppercase tracking-[0.2em] text-gray-500 block">Default Model</label>
            <button v-if="availableModels.length > 0" type="button"
              @click="showCustomDefaultModel = !showCustomDefaultModel"
              class="text-[10px] text-[#C9A84C] hover:underline bg-none border-none cursor-pointer">
              {{ showCustomDefaultModel ? 'Use Dropdown' : 'Type Manually' }}
            </button>
          </div>
          <div class="space-y-2">
            <select v-if="availableModels.length > 0 && !showCustomDefaultModel" v-model="aiSettings.default_model"
              class="w-full rounded-xl border border-[#2A2A35] bg-[#0A0A10] px-3 py-2.5 text-sm text-[#FAF8F5] focus:border-[#C9A84C]/60 focus:ring-1 focus:ring-[#C9A84C]/20 focus:outline-none transition-all font-mono">
              <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
              <option v-if="!availableModels.includes(aiSettings.default_model) && aiSettings.default_model"
                :value="aiSettings.default_model">{{ aiSettings.default_model }} (custom)</option>
            </select>
            <input v-if="availableModels.length === 0 || showCustomDefaultModel" v-model="aiSettings.default_model"
              type="text" placeholder="hf.co/org/model-name:Q8_0"
              class="w-full rounded-xl border border-[#2A2A35] bg-[#0A0A10] px-3 py-2.5 text-sm text-[#FAF8F5] placeholder-gray-600 focus:border-[#C9A84C]/60 focus:ring-1 focus:ring-[#C9A84C]/20 focus:outline-none transition-all font-mono" />
          </div>
          <p class="text-[11px] text-gray-600 leading-relaxed">LM Studio model for comments, posts, and chat.</p>
        </div>

        <!-- Default Vision Model -->
        <div class="space-y-1.5">
          <div class="flex justify-between items-center">
            <label class="text-[10px] uppercase tracking-[0.2em] text-gray-500 block">Default Vision Model</label>
            <button v-if="availableModels.length > 0" type="button"
              @click="showCustomVisionModel = !showCustomVisionModel"
              class="text-[10px] text-[#C9A84C] hover:underline bg-none border-none cursor-pointer">
              {{ showCustomVisionModel ? 'Use Dropdown' : 'Type Manually' }}
            </button>
          </div>
          <div class="space-y-2">
            <select v-if="availableModels.length > 0 && !showCustomVisionModel"
              v-model="aiSettings.default_vision_model"
              class="w-full rounded-xl border border-[#2A2A35] bg-[#0A0A10] px-3 py-2.5 text-sm text-[#FAF8F5] focus:border-[#C9A84C]/60 focus:ring-1 focus:ring-[#C9A84C]/20 focus:outline-none transition-all font-mono">
              <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
              <option
                v-if="!availableModels.includes(aiSettings.default_vision_model) && aiSettings.default_vision_model"
                :value="aiSettings.default_vision_model">{{ aiSettings.default_vision_model }} (custom)</option>
            </select>
            <input v-if="availableModels.length === 0 || showCustomVisionModel"
              v-model="aiSettings.default_vision_model" type="text" placeholder="model-name:tag"
              class="w-full rounded-xl border border-[#2A2A35] bg-[#0A0A10] px-3 py-2.5 text-sm text-[#FAF8F5] placeholder-gray-600 focus:border-[#C9A84C]/60 focus:ring-1 focus:ring-[#C9A84C]/20 focus:outline-none transition-all font-mono" />
          </div>
          <p class="text-[11px] text-gray-600 leading-relaxed">Model used for image descriptions and vision tasks.</p>
        </div>

        <!-- Default Assistant Model -->
        <div class="space-y-1.5">
          <div class="flex justify-between items-center">
            <label class="text-[10px] uppercase tracking-[0.2em] text-gray-500 block">Default Assistant Model</label>
            <button v-if="availableModels.length > 0" type="button"
              @click="showCustomAssistantModel = !showCustomAssistantModel"
              class="text-[10px] text-[#C9A84C] hover:underline bg-none border-none cursor-pointer">
              {{ showCustomAssistantModel ? 'Use Dropdown' : 'Type Manually' }}
            </button>
          </div>
          <div class="space-y-2">
            <select v-if="availableModels.length > 0 && !showCustomAssistantModel"
              v-model="aiSettings.default_assistant_model"
              class="w-full rounded-xl border border-[#2A2A35] bg-[#0A0A10] px-3 py-2.5 text-sm text-[#FAF8F5] focus:border-[#C9A84C]/60 focus:ring-1 focus:ring-[#C9A84C]/20 focus:outline-none transition-all font-mono">
              <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
              <option
                v-if="!availableModels.includes(aiSettings.default_assistant_model) && aiSettings.default_assistant_model"
                :value="aiSettings.default_assistant_model">{{ aiSettings.default_assistant_model }} (custom)</option>
            </select>
            <input v-if="availableModels.length === 0 || showCustomAssistantModel"
              v-model="aiSettings.default_assistant_model" type="text" placeholder="model-name:tag"
              class="w-full rounded-xl border border-[#2A2A35] bg-[#0A0A10] px-3 py-2.5 text-sm text-[#FAF8F5] placeholder-gray-600 focus:border-[#C9A84C]/60 focus:ring-1 focus:ring-[#C9A84C]/20 focus:outline-none transition-all font-mono" />
          </div>
          <p class="text-[11px] text-gray-600 leading-relaxed">Model used for the AI assistant chat.</p>
        </div>

        <!-- Toggles Row -->
        <div class="grid grid-cols-3 gap-3">
          <button type="button" @click="aiSettings.manage_vram = !aiSettings.manage_vram"
            class="rounded-xl border px-3 py-3 text-center transition-all duration-200 cursor-pointer" :class="aiSettings.manage_vram
              ? 'border-[#C9A84C]/50 bg-[#C9A84C]/8 ring-1 ring-[#C9A84C]/30'
              : 'border-[#232836] bg-[#111118]/60 hover:border-[#3A3A48]'">
            <div class="text-[10px] uppercase tracking-widest mb-1"
              :class="aiSettings.manage_vram ? 'text-[#C9A84C]' : 'text-gray-600'">Manage VRAM</div>
            <div class="text-xs font-semibold" :class="aiSettings.manage_vram ? 'text-[#FAF8F5]' : 'text-gray-500'">
              {{ aiSettings.manage_vram ? 'ON' : 'OFF' }}
            </div>
          </button>
          <button type="button" @click="aiSettings.use_thinking = !aiSettings.use_thinking"
            class="rounded-xl border px-3 py-3 text-center transition-all duration-200 cursor-pointer" :class="aiSettings.use_thinking
              ? 'border-[#C9A84C]/50 bg-[#C9A84C]/8 ring-1 ring-[#C9A84C]/30'
              : 'border-[#232836] bg-[#111118]/60 hover:border-[#3A3A48]'">
            <div class="text-[10px] uppercase tracking-widest mb-1"
              :class="aiSettings.use_thinking ? 'text-[#C9A84C]' : 'text-gray-600'">Thinking</div>
            <div class="text-xs font-semibold" :class="aiSettings.use_thinking ? 'text-[#FAF8F5]' : 'text-gray-500'">
              {{ aiSettings.use_thinking ? 'ON' : 'OFF' }}
            </div>
          </button>
          <button type="button" @click="aiSettings.model_is_vision = !aiSettings.model_is_vision"
            class="rounded-xl border px-3 py-3 text-center transition-all duration-200 cursor-pointer" :class="aiSettings.model_is_vision
              ? 'border-[#C9A84C]/50 bg-[#C9A84C]/8 ring-1 ring-[#C9A84C]/30'
              : 'border-[#232836] bg-[#111118]/60 hover:border-[#3A3A48]'">
            <div class="text-[10px] uppercase tracking-widest mb-1"
              :class="aiSettings.model_is_vision ? 'text-[#C9A84C]' : 'text-gray-600'">Vision</div>
            <div class="text-xs font-semibold" :class="aiSettings.model_is_vision ? 'text-[#FAF8F5]' : 'text-gray-500'">
              {{ aiSettings.model_is_vision ? 'ON' : 'OFF' }}
            </div>
          </button>
          <button type="button" @click="aiSettings.override_temperature = !aiSettings.override_temperature"
            class="rounded-xl border px-3 py-3 text-center transition-all duration-200 cursor-pointer" :class="aiSettings.override_temperature
              ? 'border-[#C9A84C]/50 bg-[#C9A84C]/8 ring-1 ring-[#C9A84C]/30'
              : 'border-[#232836] bg-[#111118]/60 hover:border-[#3A3A48]'">
            <div class="text-[10px] uppercase tracking-widest mb-1"
              :class="aiSettings.override_temperature ? 'text-[#C9A84C]' : 'text-gray-600'">Override Temp</div>
            <div class="text-xs font-semibold"
              :class="aiSettings.override_temperature ? 'text-[#FAF8F5]' : 'text-gray-500'">
              {{ aiSettings.override_temperature ? 'ON' : 'OFF' }}
            </div>
          </button>
        </div>

        <div v-if="aiSettings.override_temperature" class="space-y-3 pt-2">
          <div class="flex justify-between items-center">
            <label class="text-[10px] uppercase tracking-[0.2em] text-gray-500 block">Temperature</label>
            <span class="text-xs text-[#C9A84C] font-mono">{{ aiSettings.temperature.toFixed(2) }}</span>
          </div>
          <input v-model.number="aiSettings.temperature" type="range" min="0.0" max="2.0" step="0.05"
            class="w-full accent-[#C9A84C] bg-[#2A2A35] rounded-lg appearance-none h-1.5 focus:outline-none focus:ring-1 focus:ring-[#C9A84C]/50" />
          <div class="flex justify-between text-[10px] text-gray-600 font-mono">
            <span>0.0</span>
            <span>1.0</span>
            <span>2.0</span>
          </div>
        </div>
      </div>
    </div>

    <div class="space-y-1.5">
      <div class="text-[10px] uppercase tracking-[0.25em] text-gray-600 px-0.5">AutoComplete</div>
      <div class="rounded-2xl border border-[#232836] bg-[#0F0F16] overflow-hidden p-4 space-y-4">
        <!-- Toggle -->
        <div class="flex items-center justify-between">
          <div>
            <label class="text-sm font-medium text-gray-300 block">Autocomplete</label>
            <p class="text-xs text-gray-500 mt-0.5">Use DanTagGen models to suggest tags as you type.</p>
          </div>
          <button type="button" @click="aiSettings.autocomplete_enabled = !aiSettings.autocomplete_enabled"
            :class="aiSettings.autocomplete_enabled ? 'bg-[#C9A84C] border-[#C9A84C]/50 bg-[#C9A84C]/8 ring-1 ring-[#C9A84C]/30' : 'bg-gray-700'"
            class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none cursor-pointer">
            <span :class="aiSettings.autocomplete_enabled ? 'translate-x-6' : 'translate-x-1'"
              class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform" />
          </button>
        </div>

        <!-- Model Selection -->
        <div v-if="aiSettings.autocomplete_enabled" class="space-y-2 border-t border-[#232836] pt-3">
          <div class="flex justify-between items-center">
            <label class="text-[10px] uppercase tracking-[0.2em] text-gray-500 block">Autocomplete Model</label>
            <button v-if="availableModels.length > 0" type="button"
              @click="showCustomAutocompleteModel = !showCustomAutocompleteModel"
              class="text-[10px] text-[#C9A84C] hover:underline bg-none border-none cursor-pointer">
              {{ showCustomAutocompleteModel ? 'Use Dropdown' : 'Type Manually' }}
            </button>
          </div>
          <div class="space-y-2">
            <select v-if="availableModels.length > 0 && !showCustomAutocompleteModel"
              v-model="aiSettings.autocomplete_model"
              class="w-full rounded-xl border border-[#2A2A35] bg-[#0A0A10] px-3 py-2.5 text-sm text-[#FAF8F5] focus:border-[#C9A84C]/60 focus:ring-1 focus:ring-[#C9A84C]/20 focus:outline-none transition-all font-mono">
              <option value="">Select a model...</option>
              <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
              <option v-if="!availableModels.includes(aiSettings.autocomplete_model) && aiSettings.autocomplete_model"
                :value="aiSettings.autocomplete_model">{{ aiSettings.autocomplete_model }} (custom)</option>
            </select>
            <input v-if="availableModels.length === 0 || showCustomAutocompleteModel"
              v-model="aiSettings.autocomplete_model" type="text" placeholder="e.g. KBlueLeaf/DanTagGen-delta-rev2"
              class="w-full rounded-xl border border-[#2A2A35] bg-[#0A0A10] px-3 py-2.5 text-sm text-[#FAF8F5] placeholder-gray-600 focus:border-[#C9A84C]/60 focus:ring-1 focus:ring-[#C9A84C]/20 focus:outline-none transition-all font-mono" />
          </div>
          <p class="text-[11px] text-gray-600 leading-relaxed">LM Studio model for tag completions.</p>
        </div>
      </div>
    </div>

    <!-- Color Scheme Settings -->
    <div class="space-y-1.5">
      <div class="text-[10px] uppercase tracking-[0.25em] text-gray-600 px-0.5">Color Scheme Customizer</div>
      <div class="rounded-2xl border border-slate bg-panel overflow-hidden p-4 space-y-4">
        <!-- Preset Theme Selector -->
        <div class="space-y-2">
          <label class="text-sm font-medium text-gray-300 block">Active Theme</label>
          <select :value="currentThemeKey" @change="selectTheme($event.target.value)"
            class="w-full rounded-xl border border-slate bg-dark-input px-3 py-2.5 text-sm text-ivory focus:border-champagne focus:ring-1 focus:ring-champagne/20 focus:outline-none transition-all font-sans">
            <option v-for="(theme, key) in themes" :key="key" :value="key">
              {{ theme.name }}
            </option>
            <option value="custom">Custom Palette</option>
          </select>
        </div>

        <!-- Color Customizer Matrix -->
        <div class="grid grid-cols-2 gap-3 pt-2 border-t border-slate">
          <div class="space-y-1">
            <div class="text-[10px] uppercase tracking-wider text-gray-500 flex justify-between items-center">
              <span>Main Background</span>
              <span class="font-mono text-[9px]">{{ customColors.background }}</span>
            </div>
            <div class="flex gap-2 items-center">
              <input type="color" :value="customColors.background" @input="updateCustomColor('background', $event.target.value)" class="w-8 h-8 rounded border-none bg-transparent cursor-pointer" />
              <span class="text-xs text-gray-300">Background</span>
            </div>
          </div>
          
          <div class="space-y-1">
            <div class="text-[10px] uppercase tracking-wider text-gray-500 flex justify-between items-center">
              <span>Accent Color</span>
              <span class="font-mono text-[9px]">{{ customColors.accent }}</span>
            </div>
            <div class="flex gap-2 items-center">
              <input type="color" :value="customColors.accent" @input="updateCustomColor('accent', $event.target.value)" class="w-8 h-8 rounded border-none bg-transparent cursor-pointer" />
              <span class="text-xs text-gray-300">Accent</span>
            </div>
          </div>

          <div class="space-y-1">
            <div class="text-[10px] uppercase tracking-wider text-gray-500 flex justify-between items-center">
              <span>Foreground Text</span>
              <span class="font-mono text-[9px]">{{ customColors.text }}</span>
            </div>
            <div class="flex gap-2 items-center">
              <input type="color" :value="customColors.text" @input="updateCustomColor('text', $event.target.value)" class="w-8 h-8 rounded border-none bg-transparent cursor-pointer" />
              <span class="text-xs text-gray-300">Text</span>
            </div>
          </div>

          <div class="space-y-1">
            <div class="text-[10px] uppercase tracking-wider text-gray-500 flex justify-between items-center">
              <span>Borders & Cards</span>
              <span class="font-mono text-[9px]">{{ customColors.border }}</span>
            </div>
            <div class="flex gap-2 items-center">
              <input type="color" :value="customColors.border" @input="updateCustomColor('border', $event.target.value)" class="w-8 h-8 rounded border-none bg-transparent cursor-pointer" />
              <span class="text-xs text-gray-300">Border</span>
            </div>
          </div>

          <div class="space-y-1">
            <div class="text-[10px] uppercase tracking-wider text-gray-500 flex justify-between items-center">
              <span>Inner Panels</span>
              <span class="font-mono text-[9px]">{{ customColors.panel }}</span>
            </div>
            <div class="flex gap-2 items-center">
              <input type="color" :value="customColors.panel" @input="updateCustomColor('panel', $event.target.value)" class="w-8 h-8 rounded border-none bg-transparent cursor-pointer" />
              <span class="text-xs text-gray-300">Panel Background</span>
            </div>
          </div>

          <div class="space-y-1">
            <div class="text-[10px] uppercase tracking-wider text-gray-500 flex justify-between items-center">
              <span>Inputs & Forms</span>
              <span class="font-mono text-[9px]">{{ customColors.input }}</span>
            </div>
            <div class="flex gap-2 items-center">
              <input type="color" :value="customColors.input" @input="updateCustomColor('input', $event.target.value)" class="w-8 h-8 rounded border-none bg-transparent cursor-pointer" />
              <span class="text-xs text-gray-300">Input Background</span>
            </div>
          </div>
        </div>
      </div>
    </div>


  </div>
</template>
