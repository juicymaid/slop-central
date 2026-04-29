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
  <div class="space-y-4">
    <div class="flex items-start justify-between gap-3">
      <div>
        <h3 class="text-lg font-semibold text-[#FAF8F5]">Backend Settings</h3>
        <p class="text-xs text-gray-400">Switch adapters and update connection details.</p>
      </div>
      <span class="text-[10px] uppercase tracking-[0.2em] text-gray-500 border border-[#2A2A35] px-2 py-1 rounded-full">
        Auto-saved
      </span>
    </div>

    <div class="space-y-2">
      <div class="text-[10px] uppercase tracking-[0.3em] text-gray-500">Backends</div>
      <button
        v-for="backend in backendOptions"
        :key="backend.id"
        type="button"
        class="w-full rounded-xl border border-[#2A2A35] bg-[#111118]/70 px-3 py-2 text-left transition hover:border-[#3A3A48]"
        :class="backend.id === activeBackendId ? 'ring-1 ring-blue-500/40' : ''"
        @click="activeBackendId = backend.id"
      >
        <div class="flex items-start justify-between gap-3">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-sm font-semibold text-[#FAF8F5]">{{ backend.label }}</span>
              <span class="text-[10px] uppercase tracking-[0.2em] text-gray-500">{{ backend.type }}</span>
            </div>
            <p class="mt-1 text-xs text-gray-400">{{ backend.description }}</p>
          </div>
          <span
            class="shrink-0 rounded-full px-2 py-1 text-[10px] font-mono border"
            :class="getBackendBadge(backend.id).className"
          >
            {{ getBackendBadge(backend.id).label }}
          </span>
        </div>
      </button>
    </div>

    <div class="rounded-xl border border-[#2A2A35] bg-[#0F0F16]/80 p-4 space-y-4">
      <div>
        <div class="text-sm font-semibold text-[#FAF8F5]">Active: {{ activeBackend.label }}</div>
        <div class="text-xs text-gray-400">Edit the fields below to update the adapter.</div>
      </div>

      <div v-for="field in (activeBackend.fields || [])" :key="field.key" class="space-y-2">
        <label class="text-[10px] uppercase tracking-[0.2em] text-gray-400">{{ field.label }}</label>
        <input
          v-model="backendState.configs[activeBackendId][field.key]"
          :type="field.type || 'text'"
          :placeholder="field.placeholder"
          class="w-full rounded-lg border border-[#2A2A35] bg-[#0D0D12] px-3 py-2 text-sm text-[#FAF8F5] focus:border-blue-500 focus:outline-none"
        />
        <p v-if="field.hint" class="text-xs text-gray-500">{{ field.hint }}</p>
      </div>

      <div class="text-xs" :class="saveState === 'saving' ? 'text-blue-400' : 'text-gray-400'">
        <span v-if="saveState === 'saving'">Saving changes...</span>
        <span v-else-if="lastSavedAt">Saved at {{ formatTimestamp(lastSavedAt) }}</span>
        <span v-else>Changes auto-saved as you type.</span>
      </div>
      <div v-if="!activeStatus.ok" class="text-xs text-orange-300">
        Missing: {{ activeStatus.missingFields.join(', ') }}
      </div>
    </div>

    <div class="grid gap-3">
      <div class="rounded-xl border border-[#2A2A35] bg-[#111118]/60 p-3">
        <h4 class="text-xs font-semibold text-[#FAF8F5]">Adapter Notes</h4>
        <p class="mt-1 text-xs text-gray-400">
          Forge is wired today. ComfyUI and AI Horde remain placeholders until their adapters are implemented.
        </p>
      </div>
      <div class="rounded-xl border border-[#2A2A35] bg-[#111118]/60 p-3">
        <h4 class="text-xs font-semibold text-[#FAF8F5]">Prompt Portability</h4>
        <p class="mt-1 text-xs text-gray-400">
          Core settings stay backend-neutral. Adapters will translate models and schedulers on demand.
        </p>
      </div>
    </div>
  </div>
</template>
