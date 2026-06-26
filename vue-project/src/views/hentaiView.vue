<template>
  <div class="hentai-browse min-h-screen bg-[#0d0d12] text-white pb-20">
    <!-- Navbar Overlay / Glassmorphism -->
    <header class="sticky top-0 z-50 bg-[#0d0d12]/85 backdrop-blur-md border-b border-white/5 py-4 px-6 md:px-12 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2">
          <Tv class="w-6 h-6 text-red-500 animate-pulse" />
          <span class="text-xl font-bold tracking-wider bg-gradient-to-r from-red-500 to-rose-400 bg-clip-text text-transparent">CINEMA STREAM</span>
        </div>
        
        <!-- Mode Switcher -->
        <div class="bg-white/5 border border-white/5 rounded-xl p-1 flex items-center">
          <button 
            @click="switchMode('hentai')" 
            :class="[
              'px-3 py-1.5 rounded-lg text-xs font-bold transition-all duration-300',
              activeMode === 'hentai' ? 'bg-red-500 text-black shadow-lg' : 'text-white/60 hover:text-white'
            ]"
          >
            Hentai
          </button>
          <button 
            @click="switchMode('porn')" 
            :class="[
              'px-3 py-1.5 rounded-lg text-xs font-bold transition-all duration-300',
              activeMode === 'porn' ? 'bg-rose-600 text-white shadow-lg' : 'text-white/60 hover:text-white'
            ]"
          >
            Porn
          </button>
        </div>
      </div>
      
      <div class="flex items-center gap-6">
        <router-link to="/hentai" class="text-sm font-semibold text-white/90 hover:text-red-400 transition-colors">Home</router-link>
        <button @click="triggerRandom" class="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-red-500/10 border border-red-500/20 hover:bg-red-500 hover:text-black hover:border-transparent text-red-400 text-xs font-bold transition-all duration-300">
          <Sparkles class="w-3.5 h-3.5" />
          Surprise Me
        </button>
      </div>
    </header>

    <!-- Hero Spotlight Banner -->
    <section v-if="heroItem && !searchQuery" class="relative w-full aspect-[21/9] md:aspect-[25/9] min-h-[350px] overflow-hidden flex items-end">
      <!-- Background Image with Dark Vignette/Gradients -->
      <div class="absolute inset-0 bg-black">
        <img 
          :src="heroItem.poster" 
          alt="Spotlight"
          class="w-full h-full object-cover opacity-60"
        />
        <div class="absolute inset-0 bg-gradient-to-t from-[#0d0d12] via-[#0d0d12]/40 to-transparent"></div>
        <div class="absolute inset-0 bg-gradient-to-r from-[#0d0d12] via-transparent to-transparent"></div>
      </div>

      <!-- Hero Details -->
      <div class="relative z-10 p-6 md:p-16 max-w-3xl">
        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-500/20 border border-red-500/30 text-[10px] font-bold tracking-widest text-red-400 uppercase mb-4">
          <Flame class="w-3.5 h-3.5" /> Featured Spotlight
        </span>
        <h1 class="text-3xl md:text-5xl font-extrabold tracking-tight mb-4 leading-tight">
          {{ heroItem.name }}
        </h1>
        <p class="text-white/60 text-sm md:text-base mb-6 line-clamp-2 max-w-xl">
          {{ heroItem.description || 'Dive into premium streaming now. Experience rich storylines, detailed animation, and seamless ad-free playback.' }}
        </p>
        <div class="flex items-center gap-3">
          <router-link 
            :to="`/hentai/${encodeURIComponent(heroItem.id)}`"
            class="flex items-center gap-2 px-6 py-3 bg-red-500 hover:bg-red-600 text-black font-bold rounded-xl transition-all duration-200 shadow-lg shadow-red-500/20 hover:shadow-red-500/35"
          >
            <Play class="w-4.5 h-4.5 fill-current" />
            Watch Now
          </router-link>
        </div>
      </div>
      <!-- Spotlight Mascot/Feature Art -->
      <ClearArt class="absolute right-12 bottom-0 max-h-[85%] z-20 select-none pointer-events-none hidden md:block" />
    </section>

    <!-- Search & Catalog Section -->
    <section class="max-w-7xl mx-auto px-6 md:px-12 mt-8">
      <div class="bg-white/5 border border-white/10 rounded-2xl p-4 md:p-6 flex flex-col gap-4 backdrop-blur-xl">
        <!-- Catalog Selectors for Search/Genre Filter Context -->
        <div class="flex gap-2.5 overflow-x-auto pb-2 scrollbar-thin">
          <button 
            @click="selectCatalog(null)"
            :class="[
              'px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-300 border',
              selectedCatalogId === null 
                ? (activeMode === 'hentai' ? 'bg-red-500 border-transparent text-black shadow-lg' : 'bg-rose-600 border-transparent text-white shadow-lg')
                : 'bg-white/5 border-white/5 text-white/70 hover:text-white hover:bg-white/10'
            ]"
          >
            All Catalogs
          </button>
          <button 
            v-for="cat in activeManifest?.catalogs?.filter(c => c.id !== 'hentai-search')" 
            :key="cat.id"
            @click="selectCatalog(cat.id)"
            :class="[
              'px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-300 border',
              selectedCatalogId === cat.id 
                ? (activeMode === 'hentai' ? 'bg-red-500 border-transparent text-black shadow-lg' : 'bg-rose-600 border-transparent text-white shadow-lg')
                : 'bg-white/5 border-white/5 text-white/70 hover:text-white hover:bg-white/10'
            ]"
          >
            {{ activeMode === 'hentai' ? cat.name : cat.name.replace('OnlyPorn: ', '') }}
          </button>
        </div>

        <div class="flex flex-col md:flex-row gap-4 items-center">
          <form @submit.prevent="handleSearch" class="relative w-full flex-grow">
            <input 
              type="text" 
              v-model="searchQuery"
              placeholder="Search anime titles, tags, studios..."
              class="w-full bg-[#161622] text-white text-sm rounded-xl border border-white/10 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 pl-12 pr-28 py-3.5 transition-all duration-300"
            />
            <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-white/45" />
            <button 
              type="submit"
              class="absolute right-2 top-1/2 -translate-y-1/2 bg-red-500 hover:bg-red-600 text-black text-xs font-bold px-4 py-2 rounded-lg transition-colors duration-200"
            >
              Search
            </button>
          </form>
          <button 
            v-if="searchQuery" 
            @click="clearSearch"
            class="text-xs font-semibold text-red-400 hover:underline px-2"
          >
            Clear
          </button>
        </div>
      </div>
    </section>

    <!-- Genres / Category Chips -->
    <section class="max-w-7xl mx-auto px-6 md:px-12 mt-6">
      <div class="flex gap-2.5 overflow-x-auto pb-2 scrollbar-thin">
        <button 
          @click="selectGenre(null)"
          :class="[
            'px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-300 border',
            selectedGenreId === null 
              ? 'bg-red-500 border-transparent text-black shadow-lg'
              : 'bg-white/5 border-white/5 text-white/70 hover:text-white hover:bg-white/10'
          ]"
        >
          All Genres
        </button>
        <button 
          v-for="genre in genres" 
          :key="genre.id"
          @click="selectGenre(genre)"
          :class="[
            'px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-300 border',
            selectedGenreId === genre.id 
              ? 'bg-red-500 border-transparent text-black shadow-lg'
              : 'bg-white/5 border-white/5 text-white/70 hover:text-white hover:bg-white/10'
          ]"
        >
          {{ genre.name }} <span v-if="genre.count" class="text-white/40 text-[10px]">({{ genre.count }})</span>
        </button>
      </div>
    </section>

    <!-- Main Results Grid (Search Active, Genre Selected, or Specific Catalog Chosen) -->
    <main class="max-w-7xl mx-auto px-6 md:px-12 mt-12">
      <!-- Loading indicator -->
      <div v-if="isLoading" class="flex flex-col items-center justify-center py-20">
        <div class="relative w-12 h-12 mb-4">
          <div class="absolute inset-0 rounded-full border-2 border-red-500/15"></div>
          <div class="absolute inset-0 rounded-full border-t-2 border-red-500 animate-spin"></div>
        </div>
        <ClearArt :animated="true" class="max-w-xs max-h-60 rounded-lg mb-4 shadow-lg" />
        <span class="text-white/40 font-mono text-[10px] tracking-widest uppercase">Fetching Stream Library...</span>
      </div>

      <div v-else-if="selectedCatalogId !== null || searchQuery || selectedGenreId !== null">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg md:text-xl font-bold tracking-tight">
            {{ searchQuery ? `Search Results for "${searchQuery}"` : (selectedGenreId !== null ? `${selectedGenreName} Category` : `${activeCatalogName} Catalog`) }}
          </h2>
          <span class="text-xs text-white/45">Page {{ currentPage }}</span>
        </div>

        <div v-if="results.length === 0" class="text-center py-20 bg-white/5 rounded-2xl border border-white/5">
          <Film class="w-12 h-12 mx-auto text-white/20 mb-4" />
          <h3 class="text-base font-bold text-white/80">No Results Found</h3>
          <p class="text-white/40 text-xs mt-1">Try another keyword or genre selection.</p>
        </div>

        <div v-else>
          <div :class="activeMode === 'porn' ? 'grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6' : 'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6'">
            <div 
              v-for="item in results" 
              :key="item.id"
              @click="$router.push(`/hentai/${encodeURIComponent(item.id)}`)"
              class="group bg-[#161622] rounded-xl overflow-hidden cursor-pointer border border-white/5 hover:border-red-500/40 transition-all duration-300 hover:-translate-y-1 shadow-lg"
            >
              <div class="relative overflow-hidden bg-black/50" :class="activeMode === 'porn' ? 'aspect-video' : 'aspect-[2/3]'">
                <img 
                  :src="item.poster" 
                  alt="Cover"
                  loading="lazy"
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <!-- Hover Play Icon -->
                <div class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <div class="w-10 h-10 bg-red-500 rounded-full flex items-center justify-center text-black shadow-lg">
                    <Play class="w-5 h-5 fill-current ml-0.5" />
                  </div>
                </div>
              </div>
              <div class="p-4">
                <h3 class="text-sm font-semibold line-clamp-2 text-white/90 group-hover:text-red-400 transition-colors duration-200">
                  {{ item.name }}
                </h3>
              </div>
            </div>
          </div>

          <!-- Pagination -->
          <div class="flex items-center justify-center gap-6 mt-12 pt-6 border-t border-white/5">
            <button 
              @click="changePage(currentPage - 1)"
              :disabled="currentPage <= 1"
              class="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white/5 border border-white/5 hover:border-red-500/35 text-xs font-semibold disabled:opacity-20 disabled:hover:border-white/5 transition-all"
            >
              <ChevronLeft class="w-4 h-4" /> Prev
            </button>
            <span class="text-xs text-white/60">Page {{ currentPage }}</span>
            <button 
              @click="changePage(currentPage + 1)"
              :disabled="results.length < 20"
              class="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white/5 border border-white/5 hover:border-red-500/35 text-xs font-semibold disabled:opacity-20 disabled:hover:border-white/5 transition-all"
            >
              Next <ChevronRight class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <!-- Dashboard Mode (Netflix Carousel Rows displaying all catalogs) -->
      <div v-else class="flex flex-col gap-14">
        <!-- Row 0: Continue Watching -->
        <div v-if="continueWatching.length > 0">
          <h2 class="text-lg md:text-xl font-bold tracking-tight mb-4 flex items-center gap-2">
            <PlayCircle class="w-5 h-5 text-red-500 animate-pulse" /> Continue Watching
          </h2>
          <div class="flex gap-5 overflow-x-auto pb-4 scrollbar-thin">
            <div 
              v-for="item in continueWatching" 
              :key="item.id"
              @click="$router.push(`/hentai/${encodeURIComponent(item.id)}`)"
              :class="[
                'bg-[#161622] rounded-xl overflow-hidden cursor-pointer border border-white/5 hover:border-red-500/30 transition-all duration-300 hover:scale-[1.02] flex-shrink-0 flex flex-col justify-between group',
                isPornId(item.id) ? 'w-52' : 'w-40'
              ]"
            >
              <div class="overflow-hidden bg-black/50 relative" :class="isPornId(item.id) ? 'aspect-video' : 'aspect-[2/3]'">
                <img :src="item.image" class="w-full h-full object-cover" />
                
                <!-- Progress Bar Overlay -->
                <div class="absolute bottom-0 left-0 right-0 h-1.5 bg-white/20">
                  <div 
                    class="h-full bg-red-500" 
                    :style="{ width: `${(item.currentTime / item.duration) * 100}%` }"
                  ></div>
                </div>
                
                <!-- Play Icon Hover -->
                <div class="absolute inset-0 bg-black/45 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <Play class="w-8 h-8 text-white fill-current" />
                </div>
              </div>
              <div class="p-3">
                <h3 class="text-xs font-semibold text-white/80 line-clamp-1 group-hover:text-red-400 transition-colors">
                  {{ item.title }}
                </h3>
                <span class="text-[9px] text-white/40 block mt-1 font-mono">
                  {{ formatTime(item.currentTime) }} / {{ formatTime(item.duration) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Dynamic Catalogs Rows -->
        <div v-for="catalog in catalogsData" :key="catalog.id">
          <h2 class="text-lg md:text-xl font-bold tracking-tight mb-4 flex items-center gap-2">
            <Flame class="w-5 h-5 text-red-500" /> {{ catalog.name }}
          </h2>
          <div class="flex gap-5 overflow-x-auto pb-4 scrollbar-thin">
            <div 
              v-for="item in catalog.metas" 
              :key="item.id"
              @click="$router.push(`/hentai/${encodeURIComponent(item.id)}`)"
              :class="[
                'bg-[#161622] rounded-xl overflow-hidden cursor-pointer border border-white/5 hover:border-red-500/30 transition-all duration-300 hover:scale-[1.02] flex-shrink-0 flex flex-col justify-between',
                activeMode === 'porn' ? 'w-52' : 'w-40'
              ]"
            >
              <div class="overflow-hidden bg-black/50 relative" :class="activeMode === 'porn' ? 'aspect-video' : 'aspect-[2/3]'">
                <img :src="item.poster" class="w-full h-full object-cover" loading="lazy" />
              </div>
              <div class="p-3">
                <h3 class="text-xs font-semibold text-white/80 line-clamp-2 hover:text-red-400 transition-colors">
                  {{ item.name }}
                </h3>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { GetFromApi } from '@/api'
import ClearArt from '@/components/ClearArt.vue'
import {
  Search,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Play,
  PlayCircle,
  Flame,
  Film,
  Tv
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()

// Base Constants
const HENTAI_BASE = 'https://hentaistream-addon.keypop3750.workers.dev/bg=futa,futanari,furry'
const PORN_BASE = 'https://07b88951aaab-jaxxx-v2.baby-beamup.club'

// UI & Data States
const activeMode = ref('hentai') // 'hentai' or 'porn'
const hentaiManifest = ref(null)
const pornManifest = ref(null)
const selectedCatalogId = ref(null) // null means "All Catalogs" (Dashboard view)

const catalogsData = ref([])
const heroItem = ref(null)

const searchQuery = ref('')
const selectedGenreId = ref(null)
const selectedGenreName = ref('')

const results = ref([])
const currentPage = ref(1)
const isLoading = ref(false)

// Status / Continue watching states
const userStatus = ref(null)

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

const continueWatching = computed(() => {
  if (!userStatus.value || !userStatus.value.progress) return []
  return Object.values(userStatus.value.progress)
    .filter(item => !item.watched && item.currentTime > 5)
    .sort((a, b) => b.updatedAt - a.updatedAt)
})

const formatTime = (seconds) => {
  if (isNaN(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

// Fetch helper targeting Stremio addon APIs directly
const queryAddon = async (path) => {
  const base = activeMode.value === 'hentai' ? HENTAI_BASE : PORN_BASE
  const res = await fetch(`${base}/${path}`)
  return await res.json()
}

// Active Manifest helper
const activeManifest = computed(() => {
  return activeMode.value === 'hentai' ? hentaiManifest.value : pornManifest.value
})

const activeCatalogName = computed(() => {
  if (!activeManifest.value) return ''
  const cat = activeManifest.value.catalogs?.find(c => c.id === selectedCatalogId.value)
  return cat ? cat.name.replace('OnlyPorn: ', '') : ''
})

const isPornId = (id) => {
  if (!id) return false
  return id.startsWith('http') || id.includes('eporner') || id.includes('xhamster') || id.includes('spankbang') || id.includes('porntrex') || id.includes('missav')
}

// Extract genres dynamically from current active manifest
const genres = computed(() => {
  const manifest = activeManifest.value
  if (!manifest || !manifest.catalogs) return []

  // Find dynamic catalog or fallback to first option offering genres
  let catalog = manifest.catalogs.find(c => c.id === selectedCatalogId.value)
  let genreExtra = catalog?.extra?.find(e => e.name === 'genre')

  if (!genreExtra) {
    for (const cat of manifest.catalogs) {
      genreExtra = cat.extra?.find(e => e.name === 'genre')
      if (genreExtra) break
    }
  }

  if (!genreExtra?.options) return []

  return genreExtra.options.map(opt => {
    const match = opt.match(/^(.+?)\s*\((\d+)\)$/)
    if (match) {
      return { id: match[1].trim(), name: match[1].trim(), count: parseInt(match[2]), raw: opt }
    }
    return { id: opt, name: opt, count: null, raw: opt }
  })
})

// Load manifests
const loadManifests = async () => {
  try {
    const hRes = await fetch(`${HENTAI_BASE}/manifest.json`)
    hentaiManifest.value = await hRes.json()
  } catch (err) {
    console.error("Failed loading Hentai manifest:", err)
  }

  try {
    const pRes = await fetch(`${PORN_BASE}/manifest.json`)
    pornManifest.value = await pRes.json()
  } catch (err) {
    console.error("Failed loading Porn manifest:", err)
  }
}

// Load Home Page Dashboard rows dynamically for all manifest catalogs
const loadDashboard = async () => {
  isLoading.value = true
  catalogsData.value = []
  heroItem.value = null

  try {
    await fetchStatus()
    const manifest = activeManifest.value
    if (manifest && manifest.catalogs) {
      for (const cat of manifest.catalogs) {
        if (cat.id.includes('search')) continue
        try {
          const data = await queryAddon(`catalog/${cat.type}/${cat.id}.json`)
          if (data.metas && data.metas.length > 0) {
            catalogsData.value.push({
              id: cat.id,
              name: activeMode.value === 'hentai' ? cat.name : cat.name.replace('OnlyPorn: ', ''),
              metas: data.metas
            })
          }
        } catch (err) {
          console.error(`Failed to load catalog ${cat.id}:`, err)
        }
      }
    }

    // Set Hero Spotlight Banner from the first loaded catalog items
    if (catalogsData.value.length > 0 && catalogsData.value[0].metas.length > 0) {
      const items = catalogsData.value[0].metas
      heroItem.value = items[Math.floor(Math.random() * items.length)]
    }
  } catch (err) {
    console.error('Failed to load dashboard:', err)
  } finally {
    isLoading.value = false
  }
}

// Fetch search or genre-specific results
const fetchResults = async () => {
  isLoading.value = true
  results.value = []

  const skip = (currentPage.value - 1) * 20
  const skipParam = skip > 0 ? `skip=${skip}` : ''

  const manifest = activeManifest.value
  if (!manifest) {
    isLoading.value = false
    return
  }

  let catId = selectedCatalogId.value
  if (!catId) {
    catId = activeMode.value === 'hentai' ? 'hentai-all' : 'eporner'
  }

  const catalog = manifest.catalogs?.find(c => c.id === catId) || manifest.catalogs?.[0]
  if (!catalog) {
    isLoading.value = false
    return
  }

  const type = catalog.type

  try {
    let path = ''
    if (searchQuery.value) {
      const searchCat = manifest.catalogs?.find(c => c.id.includes('search')) || catalog
      const queryPart = `search=${encodeURIComponent(searchQuery.value)}`
      const extra = skipParam ? `${queryPart}&${skipParam}` : queryPart
      path = `catalog/${searchCat.type}/${searchCat.id}/${extra}.json`
    } else {
      let extraParts = []
      if (selectedGenreId.value !== null) {
        extraParts.push(`genre=${encodeURIComponent(selectedGenreId.value)}`)
      }
      if (skipParam) {
        extraParts.push(skipParam)
      }
      if (extraParts.length > 0) {
        path = `catalog/${type}/${catalog.id}/${extraParts.join('&')}.json`
      } else {
        path = `catalog/${type}/${catalog.id}.json`
      }
    }

    const data = await queryAddon(path)
    results.value = data.metas || []
  } catch (err) {
    console.error("Failed fetching catalog results:", err)
  } finally {
    isLoading.value = false
  }
}

// Switch Mode handler
const switchMode = (mode) => {
  activeMode.value = mode
  selectedCatalogId.value = null
  searchQuery.value = ''
  selectedGenreId.value = null
  selectedGenreName.value = ''
  currentPage.value = 1
  results.value = []
  loadDashboard()
}

// Select Catalog Provider
const selectCatalog = (catId) => {
  selectedCatalogId.value = catId
  searchQuery.value = ''
  selectedGenreId.value = null
  selectedGenreName.value = ''
  currentPage.value = 1
  results.value = []
  if (catId === null) {
    loadDashboard()
  } else {
    fetchResults()
  }
}

// Search form handler
const handleSearch = () => {
  selectedGenreId.value = null
  currentPage.value = 1
  fetchResults()
}

// Clear search
const clearSearch = () => {
  searchQuery.value = ''
  currentPage.value = 1
  results.value = []
}

// Select Genre Filter
const selectGenre = (genre) => {
  searchQuery.value = ''
  if (genre === null) {
    selectedGenreId.value = null
    selectedGenreName.value = ''
    results.value = []
  } else {
    selectedGenreId.value = genre.id
    selectedGenreName.value = genre.name
    currentPage.value = 1
    fetchResults()
  }
}

// Surprise Me / Randomizer
const triggerRandom = async () => {
  try {
    let metas = []
    const manifest = activeManifest.value
    const catId = selectedCatalogId.value || manifest?.catalogs?.[0]?.id
    if (catId) {
      const type = manifest.catalogs.find(c => c.id === catId)?.type || 'movie'
      const res = await queryAddon(`catalog/${type}/${catId}.json`)
      metas = res.metas || []
    }
    if (metas.length > 0) {
      const randomItem = metas[Math.floor(Math.random() * metas.length)]
      router.push(`/hentai/${encodeURIComponent(randomItem.id)}`)
    }
  } catch (err) {
    console.error(err)
  }
}

// Page change handler
const changePage = (page) => {
  currentPage.value = page
  fetchResults()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const syncRouteQuery = () => {
  if (route.query.q) {
    searchQuery.value = route.query.q
    selectedGenreId.value = null
    currentPage.value = 1
    fetchResults()
  } else {
    searchQuery.value = ''
  }
}

watch(() => route.query.q, () => {
  syncRouteQuery()
})

onMounted(async () => {
  await loadManifests()
  await loadDashboard()
  syncRouteQuery()
})
</script>

<style scoped>
.scrollbar-thin::-webkit-scrollbar {
  height: 6px;
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