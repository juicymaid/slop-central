<script setup>




import { ref, onMounted, onBeforeUnmount, watch, computed, inject } from 'vue'
import { GetFromApi, ImageSrc } from '../api'
import Image from '../components/Image.vue'
import { useRoute, useRouter } from 'vue-router'
import ImageMasonry from '@/components/ImageMasonry.vue'
import Stories from '@/components/Stories.vue'
import ClearArt from '@/components/ClearArt.vue'
import { ChevronDown, SlidersHorizontal } from 'lucide-vue-next'
const windowWidth = ref(window.innerWidth)


const pins = ref([])
const isLoading = ref(false)
const hasMore = ref(true)
const route = useRoute()
const router = useRouter()
// Flag to prevent duplicate fetch calls
const isUpdatingFromWatcher = ref(false)
// Get dark mode state
const isDarkMode = inject('isDarkMode', ref(false))

let currentAbortController = null

const cancelOngoingFetch = () => {
  if (currentAbortController) {
    currentAbortController.abort()
    currentAbortController = null
  }
}

const sortOptions = [
  { label: 'Recommended', value: 'home' },
  { label: 'New', value: 'new' },
  { label: 'Old', value: 'old' },
  { label: 'Random', value: 'random' },
  { label: 'Top', value: 'top' },
  { label: 'Hot', value: 'predict' },
  { label: 'Most Viewed', value: 'most_viewed' },
  { label: 'Least Viewed', value: 'least_viewed' },
  { label: 'Lewd', value: 'nsfw' },
  { label: 'Safe', value: 'sfw' }
]

const isSortOpen = ref(false)
const sortDropdownRef = ref(null)

const activeSortOption = computed(() => {
  return sortOptions.find(opt => opt.value === currentSort.value) || sortOptions[0]
})

const selectSort = (value) => {
  updateSort(value)
  isSortOpen.value = false
}

const handleClickOutside = (event) => {
  if (sortDropdownRef.value && !sortDropdownRef.value.contains(event.target)) {
    isSortOpen.value = false
  }
}

// Initialize sort and page from URL or default values
const currentSort = ref(route.query.sort || 'home')
const page = ref(parseInt(route.query.page) || 1)

// Utility function to ensure unique pins by Id
const getUniquePinsById = (pinsArray) => {
  const uniqueMap = new Map();
  pinsArray.forEach(pin => {
    if (pin && pin.Id != null && !uniqueMap.has(pin.Id)) {
      uniqueMap.set(pin.Id, pin);
    }
  });
  return Array.from(uniqueMap.values());
}

// Update URL when sort changes
const updateSort = (sortValue) => {
  if (currentSort.value === sortValue && page.value === 1) return
  currentSort.value = sortValue
  page.value = 1
  hasMore.value = true
  pins.value = [] // Reset pins for new sort
  updateUrlParams()
  fetchCurrentPage()
}

// Update URL parameters
const updateUrlParams = () => {
  isUpdatingFromWatcher.value = true
  router.push({
    query: {
      ...route.query,
      sort: currentSort.value,
      page: page.value
    }
  }).finally(() => {
    setTimeout(() => {
      isUpdatingFromWatcher.value = false
    }, 100)
  })
}

let scrollRaf = null
const handleScroll = () => {
  if (scrollRaf) return
  scrollRaf = requestAnimationFrame(() => {
    scrollRaf = null
    if (isLoading.value || !hasMore.value || pins.value.length === 0) return
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 600) {
      loadMore()
    }
  })
}

const loadMore = async () => {
  if (isLoading.value || !hasMore.value) return

  isLoading.value = true
  const nextPage = page.value + 1
  try {
    const newData = await GetFromApi(`all-images?sort=${currentSort.value}&per_page=60&page=${nextPage}`)
    if (Array.isArray(newData) && newData.length > 0) {
      page.value = nextPage
      updateUrlParams()
      pins.value = getUniquePinsById([...pins.value, ...newData])
      if (newData.length < 60) {
        hasMore.value = false
      }
    } else {
      hasMore.value = false
    }
  } catch (err) {
    if (err.name !== 'AbortError') {
      console.error('Error loading more images:', err)
    }
  } finally {
    isLoading.value = false
  }
}

// Function to fetch current page data
const fetchCurrentPage = async () => {
  cancelOngoingFetch()
  const controller = new AbortController()
  currentAbortController = controller

  isLoading.value = true
  try {
    const data = await GetFromApi(`all-images?sort=${currentSort.value}&per_page=60&page=${page.value}`, { signal: controller.signal })
    if (currentAbortController === controller) {
      if (Array.isArray(data)) {
        pins.value = getUniquePinsById(data)
        hasMore.value = data.length >= 60
      } else {
        pins.value = []
        hasMore.value = false
      }
    }
  } catch (err) {
    if (err.name !== 'AbortError') {
      console.error('Error fetching images:', err)
    }
  } finally {
    if (currentAbortController === controller) {
      isLoading.value = false
      currentAbortController = null
    }
  }
}

onMounted(async () => {
  await fetchCurrentPage()
  window.addEventListener('scroll', handleScroll, { passive: true })
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  cancelOngoingFetch()
  if (scrollRaf) cancelAnimationFrame(scrollRaf)
  window.removeEventListener('scroll', handleScroll)
  document.removeEventListener('click', handleClickOutside)
})

// Single watcher for route changes
watch(() => route.query, (newQuery) => {
  if (isUpdatingFromWatcher.value) return

  const newSort = newQuery.sort || 'home'
  const newPage = parseInt(newQuery.page) || 1
  let shouldFetch = false

  if (newSort !== currentSort.value) {
    currentSort.value = newSort
    pins.value = []
    hasMore.value = true
    shouldFetch = true
  }
  if (newPage !== page.value) {
    page.value = newPage
    shouldFetch = true
  }

  if (shouldFetch) {
    fetchCurrentPage()
  }
}, { deep: true })
</script>

<template>

  <Stories />

  <div>
    <!-- Enhanced sorting controls -->
    <div class="sort-container mb-6 mt-8" ref="sortDropdownRef">
      <div class="flex items-center justify-center sm:justify-start px-2 md:px-6 max-w-[1200px] mx-auto">
        <div class="relative inline-block text-left">
          <button @click.stop="isSortOpen = !isSortOpen" class="flex items-center gap-2.5 px-5 py-2.5 rounded-full transition-all duration-300 font-sans text-sm font-semibold border bg-[#14141A] text-[#FAF8F5]/90 border-[#2A2A35]/50 hover:bg-[#1A1A24] hover:text-[#FAF8F5] hover:border-[#2A2A35]">
            <SlidersHorizontal class="w-4 h-4 text-[#C9A84C]" />
            <span>Sort: {{ activeSortOption.label }}</span>
            <ChevronDown class="w-4 h-4 text-[#FAF8F5]/60 transition-transform duration-300" :class="{ 'rotate-180': isSortOpen }" />
          </button>
          
          <div v-if="isSortOpen" class="absolute left-1/2 -translate-x-1/2 sm:left-0 sm:translate-x-0 mt-2 w-56 rounded-2xl bg-background/95 backdrop-blur-md border border-[#2A2A35]/80 shadow-[0_10px_30px_rgba(0,0,0,0.5)] z-50 py-2 overflow-hidden">
            <button v-for="option in sortOptions" :key="option.value" @click="selectSort(option.value)" :class="[
              'w-full text-left px-4 py-2.5 text-sm font-sans font-medium transition-colors duration-200 block',
              currentSort === option.value
                ? 'text-[#C9A84C] bg-[#2A2A35]/30'
                : 'text-[#FAF8F5]/70 hover:text-[#FAF8F5] hover:bg-[#1A1A24]'
            ]">
              {{ option.label }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="px-2 md:px-6 mx-auto">
      <ImageMasonry :pins="pins" />
    </div>

    <!-- Enhanced Loading Indicator -->
    <div v-if="isLoading" class="flex flex-col items-center justify-center my-12" aria-live="polite"
      aria-label="Loading">
      <ClearArt class="max-h-[50vh] object-contain select-none pointer-events-none" />
      <span class="text-[#FAF8F5]/60 font-mono text-sm tracking-widest uppercase">
        Loading
      </span>
    </div>

    <!-- Page indicator -->
    <div class="text-center text-[#FAF8F5]/40 font-mono text-xs mt-8 mb-12">
      [ Page {{ String(page).padStart(3, '0') }} ]
    </div>
  </div>
</template>

<style scoped>
button {
  position: relative;
  overflow: hidden;
}

button::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 5px;
  height: 5px;
  background: rgba(255, 255, 255, 0.5);
  opacity: 0;
  border-radius: 100%;
  transform: scale(1, 1) translate(-50%, -50%);
  transform-origin: 50% 50%;
}

button:focus:not(:active)::after {
  animation: ripple 0.6s ease-out;
}

@keyframes ripple {
  0% {
    transform: scale(0, 0);
    opacity: 0.7;
  }

  100% {
    transform: scale(20, 20);
    opacity: 0;
  }
}
</style>
