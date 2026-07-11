<template>
  <div>
    <!-- Enhanced button-based sorting controls -->
    <div class="sort-container mb-6 mt-4">
      <div class="flex flex-wrap justify-center sm:justify-start gap-4 px-6 max-w-[1200px] mx-auto">
        <button v-for="sort in sortOptions" :key="sort.value" @click="changeSort(sort.value)" :class="[
          'magnetic-button px-5 py-2.5 rounded-full transition-all duration-300 font-sans text-sm font-semibold border',
          currentSort === sort.value
            ? 'bg-[#2A2A35] text-[#C9A84C] border-[#C9A84C]/30 shadow-[0_0_15px_rgba(201,168,76,0.1)]'
            : 'bg-[#14141A] text-[#FAF8F5]/60 border-[#2A2A35]/50 hover:bg-[#1A1A24] hover:text-[#FAF8F5] hover:border-[#2A2A35]'
        ]">
          <span class="relative z-10">{{ sort.label }}</span>
        </button>
      </div>
    </div>

    <div class="px-6  mx-auto">
      <ImageMasonry :pins="pins" />
    </div>

    <!--Error message display-->
    <div v-if="errorMessage" class="text-red-500 text-center my-8 font-mono tracking-wide">

      {{ errorMessage }}
    </div>

    <!-- Loading indicator -->
    <div v-if="isLoading" class="flex flex-col items-center justify-center my-12" aria-live="polite"
      aria-label="Loading">
      <div class="relative w-12 h-12 mb-4">
        <div class="absolute inset-0 rounded-full border-t-2 border-[#C9A84C] border-opacity-20"></div>
        <div class="absolute inset-0 rounded-full border-t-2 border-[#C9A84C] animate-spin"></div>
      </div>
      <ClearArt />
      <span class="text-[#FAF8F5]/60 font-mono text-sm tracking-widest uppercase">
        Loading Sequence
      </span>
    </div>

    <!-- Page indicator -->
    <div class="text-center text-[#FAF8F5]/40 font-mono text-xs mt-8 mb-12">
      [ Page {{ String(page).padStart(3, '0') }} ]
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { GetFromApi, apiUrl } from '../api'
import Image from '../components/Image.vue'
import ImageMasonry from '@/components/ImageMasonry.vue'
import ClearArt from '@/components/ClearArt.vue'

const route = useRoute()
const router = useRouter()
const pins = ref([])
const isLoading = ref(false)
const isDarkMode = inject('isDarkMode', ref(false))

// Initialize from URL parameters or defaults
const currentSort = ref(route.query.sort || 'relevance')
let page = parseInt(route.query.page) || 1

function randomErrorImage() {

  const base = apiUrl + "/files/comfyui/"

  const errorImages = [
    'cafe_sprite_00048_.png',
    'cafe_sprite_00005_.png',
    'cafe_sprite_00020_.png',
    'cafe_sprite_00029_.png',
    'cafe_sprite_00074_.png',
    'cafe_sprite_00071_.png',
    'cafe_sprite_00025_.png',
    'chat_image_00018_.png',
    'chat_image_00007_.png',
    'chat_image_00025_.png',
    'chat_image_00029_.png',
    'Cafe/sprite_00014_.png',
    'Chat/image_00104_.png',
    'Chat/image_00111_.png',
    'Chat/image_00007_.png',
    'Chat/image_00084_.png',
    'Chat/image_00114_.png',
    'rembg/image_00016_.png',
    'VN/ComfyUI_00037_.png',
    'VN/ComfyUI_00021_.png',
    'VN/ComfyUI_00022_.png',
    'VN/ComfyUI_00036_.png',
    'VN/ComfyUI_00051_.png',
    'VN/ComfyUI_00082_.png',
  ]
  return base + errorImages[Math.floor(Math.random() * errorImages.length)]
}

const sortOptions = [
  { label: 'New', value: 'new' },
  { label: 'Old', value: 'old' },
  { label: 'Random', value: 'random' },
  { label: 'Top', value: 'top' },
  { label: 'Relevance ', value: 'relevance' },
  { label: 'AI Search', value: 'ai' }
]

// Update URL parameters
const updateUrlParams = () => {
  router.push({
    query: {
      ...route.query,
      sort: currentSort.value,
      page: page
    }
  })
}

const changeSort = (sortValue) => {
  currentSort.value = sortValue
  page = 1
  updateUrlParams()
  fetchSearchResults()
}

const loadMore = async () => {
  if (isLoading.value) return
  isLoading.value = true
  try {
    page++
    updateUrlParams()
    const newData = await GetFromApi(`search?query=${route.query.q}&sort=${currentSort.value}&per_page=20&page=${page}`)
    const uniqueNewData = newData.filter(newPin =>
      !pins.value.some(existingPin => existingPin.Id === newPin.Id)
    )
    pins.value = [...pins.value, ...uniqueNewData]
  } finally {
    isLoading.value = false
  }
}

const handleScroll = () => {
  if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 10) {
    loadMore()
  }
}

const errorMessage = ref('')

const fetchSearchResults = async () => {
  isLoading.value = true
  try {
    const data = await GetFromApi(`search?query=${route.query.q}&sort=${currentSort.value}&per_page=50&page=${page}`)


    //handle {"detail":"No images match date filter"} 404 error
    if (data.detail) {
      errorMessage.value = data.detail
      pins.value = []
      return
    } else {
      errorMessage.value = ''
    }


    pins.value = data
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchSearchResults()
  window.addEventListener('scroll', handleScroll)
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
})

// Watch for changes in the search query
watch(() => route.query.q, () => {
  page = 1
  fetchSearchResults()
})

// Watch for external URL changes (browser back/forward)
watch(() => route.query, (newQuery) => {
  let shouldFetch = false

  if (newQuery.sort && newQuery.sort !== currentSort.value) {
    currentSort.value = newQuery.sort
    shouldFetch = true
  }

  const newPage = parseInt(newQuery.page) || 1
  if (newPage !== page) {
    page = newPage
    shouldFetch = true
  }

  if (shouldFetch) {
    fetchSearchResults()
  }
}, { deep: true })

// Watch for sort changes
watch(currentSort, () => {
  page = 1
  fetchSearchResults()
})
</script>

<style scoped></style>