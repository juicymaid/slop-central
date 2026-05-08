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

const isLoaded = ref(false)
const saveState = ref('idle')
const lastSavedAt = ref(null)
let saveTimer = null

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

const scheduleSave = () => {
  if (!isLoaded.value) return
  if (saveTimer) clearTimeout(saveTimer)
  saveState.value = 'saving'
  saveTimer = setTimeout(async () => {
    await saveBackendSettings()
    saveState.value = 'saved'
    lastSavedAt.value = Date.now()
  }, 300)
}

onMounted(async () => {
  await loadBackendSettings()
  isLoaded.value = true
  ensureActiveConfig()
})

watch(activeBackendId, ensureActiveConfig)
watch(backendState, scheduleSave, { deep: true })
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
            <!-- Active dot -->
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

      <!-- Card Header -->
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

      <!-- Fields -->
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

      <!-- Missing Fields Warning -->
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


    <div class="space-y-1.5">
      <div class="text-[10px] uppercase tracking-[0.25em] text-gray-600 px-0.5">AutoComplete</div>
      <div class="flex flex-col gap-2">
      </div>
    </div>


  </div>
</template>
