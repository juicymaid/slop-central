<template>
  <div class="hentai-viewer min-h-screen bg-[#0d0d12] text-white pb-20">
    <!-- Navbar / Header -->
    <header class="bg-[#0d0d12]/85 backdrop-blur-md border-b border-white/5 py-4 px-6 md:px-12 flex items-center justify-between">
      <router-link to="/hentai" class="flex items-center gap-2 text-white/60 hover:text-red-400 font-semibold transition-colors text-sm">
        <ArrowLeft class="w-4 h-4" /> Back to Browse
      </router-link>
      <div class="flex items-center gap-2">
        <Tv class="w-5 h-5 text-red-500" />
        <span class="text-sm font-bold tracking-wider text-red-400">CINEMA PLAY</span>
      </div>
    </header>

    <!-- Main Content Container -->
    <div class="max-w-7xl mx-auto px-6 md:px-12 mt-8">
      <!-- Loading Screen -->
      <div v-if="isLoading" class="flex flex-col items-center justify-center py-32">
        <div class="relative w-12 h-12 mb-4">
          <div class="absolute inset-0 rounded-full border-2 border-red-500/15"></div>
          <div class="absolute inset-0 rounded-full border-t-2 border-red-500 animate-spin"></div>
        </div>
        <span class="text-white/40 font-mono text-[10px] tracking-widest uppercase">Initializing Cinema Stream...</span>
      </div>

      <!-- Error Screen -->
      <div v-else-if="errorMsg" class="bg-red-950/20 border border-red-500/20 rounded-2xl p-10 text-center max-w-lg mx-auto">
        <Info class="w-12 h-12 mx-auto text-red-400 mb-4 animate-bounce" />
        <h3 class="text-lg font-bold text-red-200">Failed to Load Stream</h3>
        <p class="text-red-300/60 text-xs mt-2 font-mono">{{ errorMsg }}</p>
        <button 
          @click="fetchDetails"
          class="mt-6 px-6 py-2.5 rounded-xl bg-red-500 text-black text-xs font-bold hover:bg-red-600 transition-colors"
        >
          Try Again
        </button>
      </div>

      <!-- Content Details -->
      <div v-else-if="details" class="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <!-- Cinema Screen Column -->
        <div class="lg:col-span-8 flex flex-col gap-6">
          <!-- Video Player Container -->
          <div class="aspect-video w-full rounded-2xl overflow-hidden border border-white/5 bg-black shadow-2xl relative">
            <video 
              ref="videoPlayer"
              controls 
              autoplay
              class="w-full h-full object-contain"
              :poster="details.poster || details.image"
            ></video>
            <div v-if="!activeStreamUrl" class="absolute inset-0 flex flex-col items-center justify-center p-6 text-center bg-black/90">
              <Tv class="w-16 h-16 text-white/20 mb-3" />
              <h4 class="font-bold text-white/80">No Playable Link Found</h4>
              <p class="text-white/40 text-xs mt-1">This video stream is currently unavailable.</p>
            </div>
          </div>

          <!-- Video Quality Selector -->
          <div v-if="availableStreams.length > 1" class="flex flex-wrap gap-2 items-center bg-[#161622] p-4 rounded-xl border border-white/5">
            <span class="text-xs font-bold text-white/40 uppercase tracking-wider mr-2">Quality:</span>
            <button 
              v-for="stream in availableStreams" 
              :key="stream.url"
              @click="changeQuality(stream)"
              :class="[
                'px-3 py-1.5 rounded-lg text-xs font-bold border transition-all duration-300',
                activeStreamUrl === stream.url 
                  ? 'bg-red-500 border-transparent text-black shadow-lg shadow-red-500/10'
                  : 'bg-white/5 border-white/5 text-white/60 hover:text-white hover:bg-white/10'
              ]"
            >
              {{ stream.name || 'Default' }}
            </button>
          </div>

          <!-- Title & Actions Details Card -->
          <div class="bg-[#161622] border border-white/5 rounded-2xl p-6 shadow-xl">
            <div class="flex flex-col sm:flex-row justify-between items-start gap-4 mb-4">
              <h1 class="text-xl md:text-2xl font-extrabold text-white leading-tight">
                {{ details.name || details.title }}
              </h1>
              
              <!-- Likes / Dislikes Action Controls -->
              <div class="flex items-center gap-2 flex-shrink-0">
                <button 
                  @click="toggleLike"
                  :class="[
                    'flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all duration-300 border',
                    isLiked 
                      ? 'bg-red-500/10 border-red-500/30 text-red-400' 
                      : 'bg-white/5 border-white/5 text-white/60 hover:text-white hover:bg-white/10'
                  ]"
                >
                  <ThumbsUp class="w-4 h-4" :class="{ 'fill-current': isLiked }" />
                  <span>Like</span>
                </button>
                
                <button 
                  @click="toggleDislike"
                  :class="[
                    'flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all duration-300 border',
                    isDisliked 
                      ? 'bg-blue-500/10 border-blue-500/30 text-blue-400' 
                      : 'bg-white/5 border-white/5 text-white/60 hover:text-white hover:bg-white/10'
                  ]"
                >
                  <ThumbsDown class="w-4 h-4" :class="{ 'fill-current': isDisliked }" />
                  <span>Dislike</span>
                </button>
              </div>
            </div>

            <div class="flex flex-wrap items-center gap-3.5 text-xs text-white/50 border-b border-white/5 pb-4 mb-4">
              <span class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 text-red-400 font-bold border border-white/5 uppercase">
                {{ activeMode === 'hentai' ? 'Hentai' : 'Porn' }}
              </span>
              <span v-if="details.runtime" class="flex items-center gap-1 text-red-400 font-semibold">
                {{ details.runtime }}
              </span>
              <span v-if="details.releaseInfo" class="flex items-center gap-1">
                Release: {{ details.releaseInfo }}
              </span>
            </div>

            <p class="text-white/70 text-sm leading-relaxed whitespace-pre-wrap">
              {{ details.description || 'Enjoy seamless premium streaming. Access multiple episodes, categories, and high-definition direct stream links.' }}
            </p>
          </div>
        </div>

        <!-- Episodes & Metadata Column -->
        <div class="lg:col-span-4 flex flex-col gap-6">
          <!-- Episodes List -->
          <div v-if="details.videos && details.videos.length > 0" class="bg-[#161622] border border-white/5 rounded-2xl p-6 shadow-xl">
            <h3 class="text-xs font-bold text-white/40 uppercase tracking-widest mb-4">Episode Selection</h3>
            <div class="flex flex-col gap-2.5 max-h-[300px] overflow-y-auto pr-1 scrollbar-thin">
              <div 
                v-for="ep in details.videos" 
                :key="ep.id"
                @click="activeEpisodeId === ep.id ? null : playEpisode(ep)"
                :class="[
                  'flex items-center gap-3 p-2.5 rounded-xl border cursor-pointer transition-all duration-300',
                  activeEpisodeId === ep.id
                    ? 'bg-red-500/10 border-red-500/30 text-red-400 pointer-events-none'
                    : 'bg-black/30 border-white/5 hover:border-red-500/30 text-white/80 hover:text-white'
                ]"
              >
                <div v-if="ep.thumbnail" class="w-20 aspect-[16/10] rounded-lg overflow-hidden bg-black flex-shrink-0">
                  <img :src="ep.thumbnail" class="w-full h-full object-cover" />
                </div>
                <div class="flex-grow min-w-0">
                  <h4 class="text-xs font-bold truncate">
                    {{ ep.title }}
                  </h4>
                  <div class="flex items-center gap-1.5 mt-0.5">
                    <span v-if="activeEpisodeId === ep.id" class="text-[9px] font-bold text-red-400 uppercase tracking-wider block">
                      Now Playing
                    </span>
                    <span v-if="isEpisodeWatched(ep.id)" class="flex items-center gap-0.5 text-[9px] font-bold text-emerald-400 uppercase tracking-wider block">
                      <CheckCircle class="w-2.5 h-2.5" /> Watched
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Tags List / Genres -->
          <div v-if="genresList && genresList.length > 0" class="bg-[#161622] border border-white/5 rounded-2xl p-6 shadow-xl">
            <h3 class="text-xs font-bold text-white/40 uppercase tracking-widest mb-4">Genre Index</h3>
            <div class="flex flex-wrap gap-2">
              <button 
                v-for="tag in genresList" 
                :key="tag"
                @click="searchTag(tag)"
                class="bg-black/40 hover:bg-red-500 hover:text-black border border-white/5 text-white/70 px-3 py-1.5 rounded-lg text-xs transition-colors duration-200"
              >
                #{{ tag }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { GetFromApi, PostToApi } from '@/api'
import {
  ArrowLeft,
  Tv,
  ThumbsUp,
  ThumbsDown,
  CheckCircle,
  Info
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

// Base Constants
const HENTAI_BASE = 'https://hentaistream-addon.keypop3750.workers.dev/bg=futa,futanari,furry'
const PORN_BASE = 'https://07b88951aaab-jaxxx-v2.baby-beamup.club'

// Refs
const videoPlayer = ref(null)
const details = ref(null)
const isLoading = ref(true)
const errorMsg = ref(null)

const activeStreamUrl = ref('')
const availableStreams = ref([])
const activeEpisodeId = ref(null)

// Mode detection
const activeMode = computed(() => {
  const itemId = route.params.id
  if (itemId.startsWith('http') || itemId.includes('eporner') || itemId.includes('xhamster') || itemId.includes('spankbang') || itemId.includes('porntrex') || itemId.includes('missav')) {
    return 'porn'
  }
  return 'hentai'
})

// Status / Likes / Continue watching
const userStatus = ref(null)
let lastSavedTime = 0

const fetchStatus = async () => {
  try {
    const res = await GetFromApi('hhaven/status')
    if (res) {
      userStatus.value = res
    }
  } catch (err) {
    console.error("Failed to load user status:", err)
  }
}

const isLiked = computed(() => {
  return userStatus.value?.likes?.includes(route.params.id) || false
})

const isDisliked = computed(() => {
  return userStatus.value?.dislikes?.includes(route.params.id) || false
})

const genresList = computed(() => {
  return details.value?.genres || details.value?.tags || []
})

const toggleLike = async () => {
  try {
    const res = await PostToApi(`hhaven/like?id=${encodeURIComponent(route.params.id)}`, {})
    if (res) {
      userStatus.value = res
    }
  } catch (err) {
    console.error(err)
  }
}

const toggleDislike = async () => {
  try {
    const res = await PostToApi(`hhaven/dislike?id=${encodeURIComponent(route.params.id)}`, {})
    if (res) {
      userStatus.value = res
    }
  } catch (err) {
    console.error(err)
  }
}

const isEpisodeWatched = (link) => {
  return userStatus.value?.progress?.[link]?.watched || false
}

// Video progress saving
const onMetadataLoaded = () => {
  const video = videoPlayer.value
  if (!video) return
  
  const videoId = activeEpisodeId.value || route.params.id
  const savedProgress = userStatus.value?.progress?.[videoId]
  
  if (savedProgress && !savedProgress.watched && savedProgress.currentTime > 5) {
    console.log(`Resuming playback from: ${savedProgress.currentTime}s`)
    video.currentTime = savedProgress.currentTime
  }
}

const onTimeUpdate = () => {
  const video = videoPlayer.value
  if (!video || !video.duration) return
  
  const videoId = activeEpisodeId.value || route.params.id
  const currentTime = video.currentTime
  const duration = video.duration
  
  if (Math.abs(currentTime - lastSavedTime) > 5) {
    lastSavedTime = currentTime
    const isWatched = currentTime > duration * 0.9
    saveProgress(videoId, currentTime, duration, isWatched)
  }
}

const onEnded = () => {
  const video = videoPlayer.value
  if (!video || !video.duration) return
  
  const videoId = activeEpisodeId.value || route.params.id
  saveProgress(videoId, video.duration, video.duration, true)
}

const saveProgress = async (id, currentTime, duration, watched) => {
  if (!details.value) return
  try {
    const res = await PostToApi('hhaven/progress', {
      id: id,
      title: details.value.name || details.value.title,
      image: details.value.poster || details.value.image,
      currentTime: currentTime,
      duration: duration,
      watched: watched
    })
    if (res) {
      userStatus.value = res
    }
  } catch (err) {
    console.error("Failed to save watch progress:", err)
  }
}

const setupVideoListeners = () => {
  const video = videoPlayer.value
  if (!video) return
  
  video.removeEventListener('loadedmetadata', onMetadataLoaded)
  video.removeEventListener('timeupdate', onTimeUpdate)
  video.removeEventListener('ended', onEnded)
  
  video.addEventListener('loadedmetadata', onMetadataLoaded)
  video.addEventListener('timeupdate', onTimeUpdate)
  video.addEventListener('ended', onEnded)
}

// Load Hls.js dynamically from CDN
const loadHlsScript = () => {
  return new Promise((resolve) => {
    if (window.Hls) {
      resolve()
      return
    }
    const script = document.createElement('script')
    script.src = 'https://cdn.jsdelivr.net/npm/hls.js@latest'
    script.onload = () => resolve()
    document.head.appendChild(script)
  })
}

// Fetch details and streams
const fetchDetails = async () => {
  isLoading.value = true
  errorMsg.value = null
  details.value = null
  activeStreamUrl.value = ''
  availableStreams.value = []
  activeEpisodeId.value = null

  const itemId = route.params.id
  const base = activeMode.value === 'hentai' ? HENTAI_BASE : PORN_BASE

  try {
    let metadata = null
    
    if (activeMode.value === 'hentai') {
      // Try series first
      try {
        const res = await fetch(`${base}/meta/series/${encodeURIComponent(itemId)}.json`)
        const data = await res.json()
        metadata = data.meta
      } catch {}

      // Fallback to hentai type
      if (!metadata) {
        try {
          const res = await fetch(`${base}/meta/hentai/${encodeURIComponent(itemId)}.json`)
          const data = await res.json()
          metadata = data.meta
        } catch {}
      }
    } else {
      // Porn mode meta
      const res = await fetch(`${PORN_BASE}/meta/movie/${encodeURIComponent(itemId)}.json`)
      const data = await res.json()
      metadata = data.meta
    }

    if (metadata) {
      details.value = metadata

      // If Hentai mode has episodes, default to episode 1
      if (activeMode.value === 'hentai' && metadata.videos && metadata.videos.length > 0) {
        const firstEp = metadata.videos[0]
        activeEpisodeId.value = firstEp.id
        await fetchEpisodeStream(firstEp.id)
      } else {
        // Direct stream for movie type
        await fetchMovieStream(itemId)
      }
    } else {
      errorMsg.value = 'Item details could not be found.'
    }
  } catch (err) {
    console.error(err)
    errorMsg.value = 'Failed to connect to stream controller.'
  } finally {
    isLoading.value = false
    if (details.value) {
      nextTick(() => {
        initPlayer()
      })
    }
  }
}

// Fetch Hentai episode stream links
const fetchEpisodeStream = async (videoId) => {
  try {
    const base = HENTAI_BASE
    let res = await fetch(`${base}/stream/series/${encodeURIComponent(videoId)}.json`)
    let data = await res.json()
    
    if (!data.streams || data.streams.length === 0) {
      res = await fetch(`${base}/stream/hentai/${encodeURIComponent(videoId)}.json`)
      data = await res.json()
    }

    if (data.streams && data.streams.length > 0) {
      availableStreams.value = data.streams
      activeStreamUrl.value = data.streams[0].url
    }
  } catch (err) {
    console.error("Failed fetching episode stream:", err)
  }
}

// Fetch Porn movie stream links
const fetchMovieStream = async (movieId) => {
  try {
    const res = await fetch(`${PORN_BASE}/stream/movie/${encodeURIComponent(movieId)}.json`)
    const data = await res.json()
    if (data.streams && data.streams.length > 0) {
      availableStreams.value = data.streams
      activeStreamUrl.value = data.streams[0].url
    }
  } catch (err) {
    console.error("Failed fetching movie stream:", err)
  }
}

// Switch episode
const playEpisode = async (ep) => {
  isLoading.value = true
  activeEpisodeId.value = ep.id
  await fetchEpisodeStream(ep.id)
  isLoading.value = false
  nextTick(() => {
    initPlayer()
  })
}

// Change quality (OnlyPorn streams)
const changeQuality = (stream) => {
  const video = videoPlayer.value
  if (!video) return
  
  const savedTime = video.currentTime
  activeStreamUrl.value = stream.url
  
  nextTick(() => {
    initPlayer()
    video.currentTime = savedTime
  })
}

// Click tag to search
const searchTag = (tag) => {
  router.push({
    path: '/hentai',
    query: { q: tag }
  })
}

// Initialize video player with Hls support
const initPlayer = async () => {
  const video = videoPlayer.value
  if (!video || !activeStreamUrl.value) {
    console.error("Video element or stream URL missing", { video, url: activeStreamUrl.value })
    return
  }

  try {
    await loadHlsScript()
  } catch (e) {
    console.error("Failed to load Hls script", e)
  }

  const streamUrl = activeStreamUrl.value
  console.log("Playing stream URL:", streamUrl)

  if (streamUrl.includes('.m3u8')) {
    if (window.Hls && window.Hls.isSupported()) {
      console.log("Hls.js is supported. Initializing Hls instance.")
      // Destroy existing hls instance if any
      if (video._hls) {
        try { video._hls.destroy() } catch {}
      }
      const hls = new window.Hls()
      hls.loadSource(streamUrl)
      hls.attachMedia(video)
      video._hls = hls
      
      hls.on(window.Hls.Events.ERROR, function (event, data) {
        console.error("HLS.js error event:", data)
        if (data.fatal) {
          switch (data.type) {
            case window.Hls.ErrorTypes.NETWORK_ERROR:
              console.log("fatal network error encountered, try to recover")
              hls.startLoad()
              break
            case window.Hls.ErrorTypes.MEDIA_ERROR:
              console.log("fatal media error encountered, try to recover")
              hls.recoverMediaError()
              break
            default:
              console.log("fatal error cannot be recovered")
              hls.destroy()
              break
          }
        }
      })
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      console.log("Native HLS support detected (Safari).")
      video.src = streamUrl
    } else {
      console.error("Browser does not support HLS playback.")
    }
  } else {
    video.src = streamUrl
  }
  setupVideoListeners()
}

// Reload when route ID updates
watch(() => route.params.id, async () => {
  await fetchStatus()
  fetchDetails()
})

onMounted(async () => {
  await fetchStatus()
  fetchDetails()
})
</script>

<style scoped>
.scrollbar-thin::-webkit-scrollbar {
  width: 5px;
}
.scrollbar-thin::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 99px;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 99px;
}
.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background: #ef4444;
}
</style>