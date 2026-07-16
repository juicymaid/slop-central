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
const route = useRoute()
const router = useRouter()
// Flag to prevent duplicate fetch calls
const isUpdatingFromWatcher = ref(false)
// Get dark mode state
const isDarkMode = inject('isDarkMode', ref(false))


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
let page = parseInt(route.query.page) || 1

// Computed property to ensure reactivity
const displayPins = computed(() => pins.value)

// Utility function to ensure unique pins by Id
const getUniquePinsById = (pinsArray) => {
  const uniqueMap = new Map();
  pinsArray.forEach(pin => {
    if (!uniqueMap.has(pin.Id)) {
      uniqueMap.set(pin.Id, pin);
    }
  });
  return Array.from(uniqueMap.values());
}

// Update URL when sort changes
const updateSort = (sortValue) => {
  currentSort.value = sortValue
  page = 1
  pins.value = [] // Reset pins for new sort
  updateUrlParams()
  fetchCurrentPage()
}

// Update URL parameters
const updateUrlParams = () => {
  // Set the flag to prevent double fetching
  isUpdatingFromWatcher.value = true
  router.push({
    query: {
      ...route.query,
      sort: currentSort.value,
      page: page
    }
  }).finally(() => {
    // Reset the flag after navigation completes
    setTimeout(() => {
      isUpdatingFromWatcher.value = false
    }, 50)
  })
}

const loadMore = async () => {
  if (isLoading.value) return
  isLoading.value = true
  try {
    page++
    updateUrlParams()
    const newData = await GetFromApi('all-images?sort=' + currentSort.value + '&per_page=60&page=' + page)
    // Filter out duplicates using both methods for redundancy
    const uniqueNewData = newData.filter(newPin =>
      !pins.value.some(existingPin => existingPin.Id === newPin.Id)
    )
    const combinedPins = [...pins.value, ...uniqueNewData]
    // Apply final deduplication before assignment
    pins.value = getUniquePinsById(combinedPins)
  } finally {
    isLoading.value = false
  }
}

const handleScroll = () => {
  if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 512) {
    loadMore()
  }
}

// Function to fetch current page data
const fetchCurrentPage = async () => {
  if (isLoading.value) return

  isLoading.value = true
  try {
    const data = await GetFromApi(`all-images?sort=${currentSort.value}&per_page=60&page=${page}`)
    // Ensure no duplicates in initial data load
    pins.value = getUniquePinsById(data)
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  // Initial data fetch on mount
  await fetchCurrentPage()
  window.addEventListener('scroll', handleScroll)
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
  document.removeEventListener('click', handleClickOutside)
})

// Single watcher for route changes
watch(() => route.query, (newQuery) => {
  if (isUpdatingFromWatcher.value) return

  const newSort = newQuery.sort
  const newPage = parseInt(newQuery.page) || 1
  let shouldFetch = false

  if (newSort && newSort !== currentSort.value) {
    currentSort.value = newSort
    shouldFetch = true
  }

  if (newPage !== page) {
    page = newPage
    shouldFetch = true
  }

  if (shouldFetch) {
    fetchCurrentPage()
  }
}, { deep: true })

// Remove the separate watch on currentSort as it's now handled in updateSort
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
