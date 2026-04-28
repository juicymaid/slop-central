<script setup>
import { ref, onMounted } from 'vue'
import { GetFromApi, PostToApi, ImageSrc } from '../api'
import { RouterLink } from 'vue-router'

const items = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 60
const isLoading = ref(false)
const isEmptying = ref(false)

async function fetchTrash() {
  if (isLoading.value) return
  isLoading.value = true
  try {
    const data = await GetFromApi(`trash?page=${page.value}&per_page=${perPage}`)
    items.value = data.items || []
    total.value = data.total || 0
  } finally {
    isLoading.value = false
  }
}

async function restoreImage(imageId) {
  await PostToApi(`trash/restore/${imageId}`)
  items.value = items.value.filter(img => img.Id !== imageId)
  total.value = Math.max(0, total.value - 1)
}

async function emptyTrash() {
  if (!confirm(`Permanently delete all ${total.value} image(s) from trash? This cannot be undone.`)) return
  isEmptying.value = true
  try {
    await PostToApi('trash/empty')
    items.value = []
    total.value = 0
  } finally {
    isEmptying.value = false
  }
}

async function emptyTrashWithFiles() {
  if (!confirm(`Permanently delete all ${total.value} image(s) AND their files from disk? This cannot be undone.`)) return
  isEmptying.value = true
  try {
    await PostToApi('trash/empty?delete_files=true')
    items.value = []
    total.value = 0
  } finally {
    isEmptying.value = false
  }
}

function formatDate(ts) {
  if (!ts) return ''
  return new Date(ts * 1000).toLocaleString()
}

onMounted(fetchTrash)
</script>

<template>
  <div class="max-w-[1200px] mx-auto px-6 mb-12">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8 mt-12">
      <div class="flex items-center gap-4">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 text-[#C9A84C]" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="3 6 5 6 21 6"></polyline>
          <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"></path>
          <path d="M10 11v6M14 11v6"></path>
          <path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"></path>
        </svg>
        <h1 class="text-3xl font-serif font-bold italic text-[#FAF8F5] drop-shadow-md">Trash</h1>
        <span class="text-sm font-mono tracking-widest uppercase text-[#FAF8F5]/40 mt-1">[{{ total }} item{{ total !== 1 ? 's' : '' }}]</span>
      </div>

      <div v-if="total > 0" class="flex gap-2">

        <button
          class="magnetic-button px-6 py-2.5 text-sm rounded-full bg-red-500/20 hover:bg-red-500/40 border border-red-500/30 text-red-400 hover:text-red-300 font-sans font-semibold transition-colors"
          :disabled="isEmptying"
          @click="emptyTrashWithFiles"
        >
          <span class="relative z-10">Empty Trash</span>
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="flex justify-center py-20">
      <div class="relative w-12 h-12">
        <div class="absolute inset-0 rounded-full border-t-2 border-[#C9A84C] border-opacity-20"></div>
        <div class="absolute inset-0 rounded-full border-t-2 border-[#C9A84C] animate-spin"></div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="items.length === 0" class="flex flex-col items-center justify-center py-32 text-[#FAF8F5]/40">
      <svg xmlns="http://www.w3.org/2000/svg" class="w-16 h-16 mb-6 opacity-40 text-[#FAF8F5]/20" viewBox="0 0 24 24"
        fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="3 6 5 6 21 6"></polyline>
        <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"></path>
        <path d="M10 11v6M14 11v6"></path>
        <path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"></path>
      </svg>
      <p class="text-sm font-mono tracking-widest uppercase">[ Trash is empty ]</p>
    </div>

    <!-- Grid -->
    <div v-else class="columns-2 sm:columns-3 md:columns-4 lg:columns-5 gap-4">
      <div
        v-for="img in items"
        :key="img.Id"
        class="break-inside-avoid mb-4 relative group rounded-[2rem] overflow-hidden border border-[#2A2A35]"
      >
        <RouterLink :to="`/image/${img.Id}`">
          <img
            :src="ImageSrc(img.Path)"
            :alt="img.Prompt"
            class="w-full object-cover rounded-[2rem]"
            loading="lazy"
          />
        </RouterLink>

        <!-- Overlay actions -->
        <div class="absolute inset-0 bg-[#0D0D12]/60 opacity-0 group-hover:opacity-100 transition-opacity rounded-[2rem] flex flex-col justify-between p-4 backdrop-blur-[2px]">
          <div class="flex justify-end relative z-10">
            <button
              class="magnetic-button p-2.5 bg-[#FAF8F5]/10 hover:bg-[#FAF8F5]/20 backdrop-blur-md border border-[#FAF8F5]/10 text-[#FAF8F5] rounded-full font-medium flex items-center gap-2 shadow-lg transition-colors"
              @click.prevent.stop="restoreImage(img.Id)"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 relative z-10" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="1 4 1 10 7 10"></polyline>
                <path d="M3.51 15a9 9 0 1 0 .49-3.87"></path>
              </svg>
              <span class="font-sans text-sm relative z-10">Restore</span>
            </button>
          </div>
          <p v-if="img.TrashedAt" class="text-[#FAF8F5]/80 font-mono text-xs uppercase tracking-widest truncate relative z-10">
            {{ formatDate(img.TrashedAt) }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
