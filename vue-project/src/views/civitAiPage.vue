<template>

  
<div
    v-if="showImage && showImage.meta"
    class="fixed top-16 right-0 z-10 h-full w-96 bg-gray-900 border-l border-gray-800 shadow-2xl flex flex-col"
  >
    <!-- Close Button -->
    <div class="absolute top-3 right-3">
      <button
        class="text-gray-400 hover:text-white hover:bg-gray-700 p-1 rounded-full transition"
        @click="showImage = null"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
          viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round"
            stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Content -->
    <div class="p-5 pt-10 text-sm text-gray-200 space-y-4 overflow-y-auto">
      <InfoItem label="By" :value="'@' + showImage.username" />
      <InfoItem label="Size" :value="showImage.meta?.Size || (showImage.width + 'x' + showImage.height)" />
      <InfoItem label="Seed" :value="showImage.meta?.seed" />
      <InfoItem label="Steps" :value="showImage.meta?.steps" />
      <InfoItem label="Sampler" :value="showImage.meta?.sampler" />
      <InfoItem label="CFG Scale" :value="showImage.meta?.cfgScale" />
      <InfoItem label="Clip Skip" :value="showImage.meta?.clipSkip" />

      <!-- Prompt -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <span class="font-semibold text-gray-300">Prompt</span>
          <button
            class="text-xs text-gray-400 hover:text-white transition"
            @click="copyToClipboard(showImage.meta?.prompt)"
          >Copy</button>
        </div>
        <div class="bg-gray-800 rounded-lg p-3 text-xs whitespace-pre-line break-words">
          {{ showImage.meta?.prompt }}
        </div>
      </div>

      <!-- Negative Prompt -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <span class="font-semibold text-gray-300">Negative Prompt</span>
          <button
            class="text-xs text-gray-400 hover:text-white transition"
            @click="copyToClipboard(showImage.meta?.negativePrompt)"
          >Copy</button>
        </div>
        <div class="bg-gray-800 rounded-lg p-3 text-xs whitespace-pre-line break-words">
          {{ showImage.meta?.negativePrompt }}
        </div>
      </div>

      <!-- Resources -->
      <div v-if="showImage.meta?.civitaiResources?.length">
        <span class="font-semibold text-gray-300">Resources</span>
        <ul class="mt-2 ml-3 space-y-1 text-xs">
          <li
            v-for="(res, idx) in showImage.meta.civitaiResources"
            :key="idx"
            class="text-gray-400"
          >
            <span class="capitalize text-gray-200">{{ res.type }}</span>
            <span v-if="res.weight"> (weight: {{ res.weight }})</span>
            <span class="ml-1 text-gray-500">ID: {{ res.modelVersionId }}</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- Remix Button -->
    <div class="p-4 border-t border-gray-800">
      <button
        class="w-full py-2 bg-blue-600 hover:bg-blue-500 transition rounded-xl text-sm font-semibold text-white"
        @click="remixImage(showImage)"
      >
        Remix Prompt
      </button>
    </div>
  </div>
       
    

  <div class="mx-auto p-5">


    <!-- Header -->
    <div class="mb-8 text-center">
      <h1 class="mb-6 text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
        CivitAI Gallery
      </h1>

      <!-- Filters Container -->
      <div class=" rounded-2xl p-6 max-w-4xl mx-auto ">
        <!-- Sort and Period Filters -->
        <div class="flex gap-4 justify-center items-center flex-wrap mb-6">
          <div class="flex flex-col gap-2">
            <label class="text-sm font-medium text-gray-300">Sort By</label>
            <select v-model="filters.sort" @change="resetAndFetch"
              class="px-4 py-2.5 bg-gray-700 border border-gray-600 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 hover:bg-gray-600">
              <option value="Most Reactions">Most Reactions</option>
              <option value="Most Comments">Most Comments</option>
              <option value="Newest">Newest</option>
            </select>
          </div>

          <div class="flex flex-col gap-2">
            <label class="text-sm font-medium text-gray-300">Time Period</label>
            <select v-model="filters.period" @change="resetAndFetch"
              class="px-4 py-2.5 bg-gray-700 border border-gray-600 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 hover:bg-gray-600">
              <option value="AllTime">All Time</option>
              <option value="Week">Week</option>
              <option value="Month">Month</option>
              <option value="Year">Year</option>
            </select>
          </div>
        </div>

        <!-- NSFW Filter Bubbles -->
        <div class="flex flex-col gap-3">
          <label class="text-sm font-medium text-gray-300">Content Filter</label>
          <div class="flex gap-3 justify-center flex-wrap">
            <button v-for="option in nsfwOptions" :key="option.value" @click="toggleNsfwFilter(option.value)" :class="[
              'px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 border-2',
              selectedNsfw.has(option.value)
                ? 'bg-blue-500 border-blue-500 text-white shadow-lg shadow-blue-500/25'
                : 'bg-gray-700/50 border-gray-600 text-gray-300 hover:bg-gray-600/70 hover:border-gray-500'
            ]" type="button">
              <span class="mr-1">
                <svg v-if="selectedNsfw.has(option.value)" xmlns="http://www.w3.org/2000/svg" class="inline w-4 h-4"
                  fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </span>
              {{ option.label }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Masonry Gallery Grid -->
    <div class="w-full flex gap-2 mb-10" ref="galleryGrid">
      <div class="w-full" v-for="ci in columnCount" :key="ci">
        <!-- Image Card -->
        <div v-for="image in getImagesForColumn(ci - 1)" :key="image.id"
          class="mb-2 relative  rounded-xl overflow-hidden shadow-lg transition-all duration-200 hover:-translate-y-1 hover:shadow-xl cursor-pointer break-inside-avoid"
          :style="{ aspectRatio: image.width / image.height }" @click="openImagePage(image)">

          <!-- Video or Image -->
          <video v-if="isVideo(image.url)" :src="image.url" @loadeddata="onImageLoad" @error="onImageError" muted loop
            playsinline @mouseenter="playVideo" @mouseleave="pauseVideo"
            class="w-full h-full object-cover opacity-0 transition-opacity duration-300" />
          <img v-else :src="image.url" :alt="`Image by ${image.username}`" @load="onImageLoad" @error="onImageError"
            loading="lazy" class="w-full h-full object-cover opacity-0 transition-opacity duration-300" />

          <!-- Overlay -->
          <div
            class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent text-white p-4 pb-3 opacity-0 hover:opacity-100 transition-opacity duration-200">
            <div class="flex gap-3 mb-2 text-sm">
              <span v-if="image.stats.heartCount > 0" class="inline-block">❤️ {{ image.stats.heartCount }}</span>
              <span v-if="image.stats.likeCount > 0" class="inline-block">👍 {{ image.stats.likeCount }}</span>
              <span v-if="image.stats.laughCount > 0" class="inline-block">😂 {{ image.stats.laughCount }}</span>
              <span v-if="image.stats.cryCount > 0" class="inline-block">😭 {{ image.stats.cryCount }}</span>
              <span v-if="image.stats.commentCount > 0" class="inline-block">💬 {{ image.stats.commentCount }}</span>
            </div>
            <div>
              <p class="font-semibold text-sm mb-1">@{{ image.username }}</p>
              <p class="text-xs opacity-80">{{ image.width }}×{{ image.height }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-10">
      <div class="w-10 h-10 border-3 border-gray-300 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
      <p class="text-gray-600">Loading more images...</p>
    </div>

    <!-- End -->
    <div v-if="!hasMore && images.length > 0" class="text-center ">
      <hr class=" border-gray-400 opacity-50" />
      <p class="text-gray-600">No more images to load.</p>
    </div>


    <!-- Error -->
    <div v-if="error" class="text-center py-10 text-red-600">
      <p class="mb-3">{{ error }}</p>
      <button @click="fetchImages"
        class="px-5 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors">
        Retry
      </button>
    </div>

    <div ref="sentinel" class="h-px w-full"></div>
  </div>
</template>

<script setup>
import { webState } from '@/api'
import { ref, reactive, onMounted, onUnmounted, computed, watch, getCurrentInstance } from 'vue'

const images = ref([])
const loading = ref(false)
const error = ref(null)
const hasMore = ref(true)
const nextCursor = ref(null)
const nextPageUrl = ref(null)
const galleryGrid = ref(null)
const sentinel = ref(null)
const windowWidth = ref(window.innerWidth)
const copyToClipboard = (text) => {
  if (!text) return
  navigator.clipboard.writeText(text).then(() => {
    console.log("Copied to clipboard")
  })
}
function remixImage(image) {
  
  webState.remixImage = {
    Prompt: image.meta.prompt || '',
    NegativePrompt: image.meta.negativePrompt || '',
    Steps: image.meta.steps || 20,
    Sampler: image.meta.sampler || 'DPM++ 2M',
    CFGScale: image.meta.cfgScale || 7.0,
  }

  image.showImage = false
}
const showImage = ref(null)

const openImagePage = (image) => {
  showImage.value = image == showImage.value ? null : { ...image }
}

const filters = reactive({
  sort: 'Most Reactions',
  period: 'Week',
  nsfw: '',
  limit: 50
})

let observer = null

// NSFW filter options in increasing order of explicitness
const nsfwOptions = [
  { value: 'None', label: 'Safe' },
  { value: 'Soft', label: 'Soft' },
  { value: 'Mature', label: 'Mature' },
  { value: 'X', label: 'X (Explicit)' }
]

// Track selected NSFW levels as a Set
const selectedNsfw = ref(new Set(['']))

// Compute the highest selected NSFW level for the API param
const highestSelectedNsfw = computed(() => {
  // Find the highest index in nsfwOptions whose value is in selectedNsfw
  let maxIdx = -1
  nsfwOptions.forEach((opt, idx) => {
    if (selectedNsfw.value.has(opt.value)) maxIdx = idx
  })
  // If none selected, default to Safe
  return maxIdx === -1 ? '' : nsfwOptions[maxIdx].value
})

// Keep filters.nsfw in sync for fetchImages
watch(highestSelectedNsfw, (val) => {
  filters.nsfw = val
})

const fetchImages = async (reset = false) => {
  if (loading.value || (!hasMore.value && !reset)) return

  try {
    loading.value = true
    error.value = null

    if (reset) {
      images.value = []
      nextCursor.value = null
      nextPageUrl.value = null
      hasMore.value = true
    }

    let url
    if (nextPageUrl.value && !reset) {
      url = nextPageUrl.value
    } else {
      const params = new URLSearchParams({
        limit: filters.limit,
        sort: filters.sort,
        period: filters.period
      })

      if (nextCursor.value && !reset) {
        params.append('cursor', nextCursor.value)
      }

      // Only set the highest selected NSFW level
      if (filters.nsfw) {
        params.append('nsfw', filters.nsfw)
      } else {
        params.append('nsfw', 'None')
      }

      url = `https://civitai.com/api/v1/images?${params}`
    }

    const response = await fetch(url)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()

    if (reset) {
      images.value = data.items
    } else {
      images.value.push(...data.items)
    }

    // Update cursor and next page URL from response
    nextCursor.value = data.metadata?.nextCursor || null
    nextPageUrl.value = data.metadata?.nextPage || null
    hasMore.value = !!(nextCursor.value || nextPageUrl.value)

    console.log(`Fetched ${data.items.length} images, total: ${images.value.length} filtered: ${filteredImages.value.length}`)

    if (filteredImages.value.length === 0 && images.value.length > 0 && hasMore.value) {
      console.log('No images match the current filters, fetching more...')
      await fetchImages(false)
    }

  } catch (err) {
    error.value = `Failed to load images: ${err.message}`
    console.error('Error fetching images:', err)
  } finally {
    loading.value = false
  }
}

const resetAndFetch = () => {
  fetchImages(true)
}

const onImageLoad = (event) => {
  event.target.style.opacity = '1'
}

const onImageError = (event) => {
  event.target.style.display = 'none'
}

const isVideo = (url) => {
  return url && url.toLowerCase().includes('.mp4')
}

const playVideo = (event) => {
  if (event.target.tagName === 'VIDEO') {
    event.target.play()
  }
}

const pauseVideo = (event) => {
  if (event.target.tagName === 'VIDEO') {
    event.target.pause()
  }
}



const setupIntersectionObserver = () => {
  if (!sentinel.value) return

  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && hasMore.value && !loading.value) {
          fetchImages()
        }
      })
    },
    {
      rootMargin: '100px'
    }
  )

  observer.observe(sentinel.value)
}

const updateWindowWidth = () => {
  windowWidth.value = window.innerWidth
}

// Calculate column count based on window width
const columnCount = computed(() => {
  const availableWidth = windowWidth.value - 0 // padding
  return Math.max(1, Math.floor((availableWidth - 1) / 300))
})

// Filter images based on selected NSFW levels
const filteredImages = computed(() => {
  return images.value.filter((image) =>
    selectedNsfw.value.has(image.nsfwLevel)
  )
})



// Get images for specific column (masonry layout)
const getImagesForColumn = (columnIndex) => {



  return filteredImages.value.filter((_, index) =>
    (index - columnIndex) % columnCount.value === 0
  )
}

onMounted(() => {
  fetchImages(true)
  setupIntersectionObserver()
  window.addEventListener('resize', updateWindowWidth)
})

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
  }
  window.removeEventListener('resize', updateWindowWidth)
})

function toggleNsfwFilter(value) {
  if (selectedNsfw.value.has(value)) {
    selectedNsfw.value.delete(value)
    // Always keep at least one selected (default to Safe if none)
    if (selectedNsfw.value.size === 0) selectedNsfw.value.add('')
  } else {
    selectedNsfw.value.add(value)
  }
  // Update filters.nsfw and fetch
  filters.nsfw = highestSelectedNsfw.value
  resetAndFetch()
}
</script>