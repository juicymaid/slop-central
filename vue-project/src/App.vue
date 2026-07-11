<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount, provide, computed } from 'vue'
import { RouterLink, useRouter, useRoute } from 'vue-router'
import { Search, Moon, Sun } from 'lucide-vue-next'
import { GetFromApi, ImageSrc } from './api'
import CreateSidebar from './components/CreateSidebar.vue'
import { webState } from './api'
import SelectModelModal from './components/SelectModelModal.vue'
import Masonry from 'masonry-layout'
import ClearArt from './components/ClearArt.vue'

const isMobile = ref(false)
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

const searchQuery = ref('')
const showSuggestions = ref(false)
const tags = ref([])
const suggestions = ref([])
const selectedIndex = ref(-1)
const isDarkMode = ref(false)

const handleKeyDown = (e) => {
  if (e.key === 'Control') {
    document.body.classList.add('ctrl-pressed')
  }
}

const handleKeyUp = (e) => {
  if (e.key === 'Control') {
    document.body.classList.remove('ctrl-pressed')
  }
}

const handleDevBlurFocusLoss = () => {
  document.body.classList.remove('ctrl-pressed')
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)

  if (import.meta.env.VITE_DEV_BLUR === 'true') {
    document.body.classList.add('dev-blur-enabled')
    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)
    window.addEventListener('blur', handleDevBlurFocusLoss)
    window.addEventListener('focusout', handleDevBlurFocusLoss)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
  if (import.meta.env.VITE_DEV_BLUR === 'true') {
    window.removeEventListener('keydown', handleKeyDown)
    window.removeEventListener('keyup', handleKeyUp)
    window.removeEventListener('blur', handleDevBlurFocusLoss)
    window.removeEventListener('focusout', handleDevBlurFocusLoss)
  }
})

// Provide theme context to child components
provide('isDarkMode', isDarkMode)

const router = useRouter()
const route = useRoute()
const hideNav = computed(() => route.query.hidenav === '1')

// Theme toggle function
const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
  localStorage.setItem('darkMode', isDarkMode.value ? 'dark' : 'light')
  updateTheme()
}

// Update theme based on current state
const updateTheme = () => {
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

// Initialize theme from localStorage
onMounted(async () => {
  const savedTheme = localStorage.getItem('darkMode')
  if (savedTheme) {
    isDarkMode.value = savedTheme === 'dark'
  } else {
    // Check system preference if no saved preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    isDarkMode.value = prefersDark
  }
  updateTheme()
  tags.value = await GetFromApi('tags')
})

// Watch for system theme changes
onMounted(() => {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  const handleChange = () => {
    // Only update if there's no user preference saved
    if (!localStorage.getItem('darkMode')) {
      isDarkMode.value = mediaQuery.matches
      updateTheme()
    }
  }
  mediaQuery.addEventListener('change', handleChange)
})

const selectSuggestion = (suggestion) => {
  searchQuery.value = suggestion
  showSuggestions.value = false
  selectedIndex.value = -1
  router.push(`/search?q=${encodeURIComponent(suggestion)}`)
}

const handleSearch = (e) => {
  e.preventDefault()
  if (searchQuery.value.trim()) {
    router.push(`/search?q=${encodeURIComponent(searchQuery.value.trim())}`)
  }
}

const handleKeydown = (e) => {
  if (!showSuggestions.value || !suggestions.value.length) return

  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault()
      selectedIndex.value = (selectedIndex.value + 1) % suggestions.value.length
      scrollSelectedIntoView()
      break
    case 'ArrowUp':
      e.preventDefault()
      selectedIndex.value = selectedIndex.value <= 0 ? suggestions.value.length - 1 : selectedIndex.value - 1
      scrollSelectedIntoView()
      break
    case 'Enter':
      if (selectedIndex.value >= 0) {
        selectSuggestion(suggestions.value[selectedIndex.value].tag)
      }
      break
    case 'Escape':
      showSuggestions.value = false
      selectedIndex.value = -1
      break
  }
}

const scrollSelectedIntoView = () => {
  nextTick(() => {
    const selectedElement = document.querySelector('.suggestion-selected')
    if (selectedElement) {
      selectedElement.scrollIntoView({ block: 'nearest' })
    }
  })
}

const onInputFocus = () => {
  showSuggestions.value = true
  selectedIndex.value = -1
}

const handleBlur = () => {
  setTimeout(() => {
    showSuggestions.value = false
    selectedIndex.value = -1
  }, 200)
}
var loadingSuggestions = false;
async function GetSuggestions() {
  if (!searchQuery.value) {
    suggestions.value = []
    return
  }
  if (loadingSuggestions) return;

  loadingSuggestions = true;
  let data = await GetFromApi('autocomplete-tags?query=' + searchQuery.value)
  loadingSuggestions = false;
  suggestions.value = data
  console.log(data)
}
</script>

<template>
  <CreateSidebar />
  <div class="min-h-screen transition-colors duration-300 bg-[#0D0D12]">
    <!-- Navigation Header - Floating Island -->
    <nav v-if="!hideNav" id="app-header"
      class="app-header fixed top-4 left-1/2 -translate-x-1/2 transition-colors duration-200 bg-[#0D0D12]/60 backdrop-blur-xl border border-[#2A2A35] rounded-full shadow-lg z-40 px-6 py-3"
      :style="isMobile ? { width: 'calc(100% - 2rem)', maxWidth: '1200px' } : { marginLeft: webState.sidebarWidth > 0 ? (webState.sidebarWidth / 2) + 'px' : '0px', width: `calc(100% - ${webState.sidebarWidth}px - 2rem)`, maxWidth: '1200px' }">
      <div class="flex items-center justify-between w-full mx-auto">
        <!-- Logo -->
        <RouterLink to="/" class="flex items-center group">
          <svg class="w-8 h-8 text-[#C9A84C] transition-transform duration-300 group-hover:scale-105"
            fill="currentColor" viewBox="0 0 24 24">
            <path
              d="M12 0a12 12 0 0 0-4.5 23.1c-.1-.9-.2-2.4 0-3.4.2-.9 1.4-5.7 1.4-5.7s-.4-.7-.4-1.8c0-1.7 1-3 2.2-3 1 0 1.5.8 1.5 1.7 0 1-.7 2.5-1 3.9-.3 1.2.6 2.2 1.8 2.2 2.2 0 3.8-2.3 3.8-5.6 0-2.9-2.1-5-5.2-5-3.5 0-5.6 2.6-5.6 5.3 0 1 .4 2.1.9 2.7.1.1.1.2 0 .3l-.3 1.3c-.1.2-.2.3-.4.2-1.5-.7-2.4-2.9-2.4-4.6 0-3.8 2.8-7.3 7.9-7.3 4.2 0 7.4 3 7.4 7 0 4.2-2.7 7.5-6.4 7.5-1.3 0-2.5-.7-2.9-1.5 0 0-.6 2.3-.8 2.9-.3 1-1 2.3-1.5 3.1a12 12 0 1 0 4.5-23.1z" />
          </svg>
          <span class="hidden md:inline-block ml-3 font-semibold font-sans text-lg tracking-tight text-[#FAF8F5]">Slop
            Central</span>
        </RouterLink>

        <!-- Search Bar -->
        <div class="flex-1 mx-2 md:mx-6 max-w-2xl">
          <div class="relative group">
            <form @submit="handleSearch">
              <input type="text" v-model="searchQuery" @focus="onInputFocus" @blur="handleBlur" @keydown="handleKeydown"
                @input="GetSuggestions()"
                class="w-full pl-12 pr-4 py-2.5 bg-[#14141A] text-[#FAF8F5] font-mono text-sm rounded-full border border-[#2A2A35] hover:border-[#C9A84C]/50 focus:border-[#C9A84C] focus:outline-none focus:ring-1 focus:ring-[#C9A84C] shadow-sm transition-all duration-300"
                placeholder="Search database...">
            </form>
            <Search
              class="w-4 h-4 absolute left-4 top-1/2 transform -translate-y-1/2 text-[#FAF8F5]/50 group-focus-within:text-[#C9A84C] transition-colors duration-300" />

            <!-- Suggestions Dropdown -->
            <div v-if="showSuggestions && suggestions.length && searchQuery"
              class="absolute w-full mt-2 bg-[#1A1A24]/95 backdrop-blur-xl rounded-2xl shadow-[0_8px_30px_rgba(0,0,0,0.5)] border border-[#2A2A35] py-2 max-h-[400px] overflow-y-auto z-50 overflow-hidden">
              <div v-for="(suggestion, index) in suggestions" :key="suggestion" :class="[
                'px-4 py-3 cursor-pointer flex items-center gap-3 transition-colors',
                index === selectedIndex
                  ? 'bg-[#2A2A35] suggestion-selected'
                  : 'hover:bg-[#2A2A35]/50'
              ]" @mouseenter="selectedIndex = index" @click="selectSuggestion(suggestion.tag)">
                <Search class="w-4 h-4 text-[#FAF8F5]/40" />
                <div>
                  <span class="text-[#FAF8F5] font-sans">{{ suggestion.tag }}</span>
                  <span class="text-xs font-mono text-[#FAF8F5]/40 ml-2">{{ suggestion.count }}</span>
                </div>
              </div>
            </div>
            <div v-else-if="showSuggestions"
              class="absolute w-full mt-2 bg-[#1A1A24]/95 backdrop-blur-xl rounded-2xl shadow-[0_8px_30px_rgba(0,0,0,0.5)] border border-[#2A2A35] py-4 max-h-[400px] overflow-y-auto z-50">
              <div class="px-4 py-2">
                <h3 class="text-xs uppercase tracking-wider font-semibold text-[#FAF8F5]/50 font-sans mb-3">Popular Tags
                </h3>

                <div class="grid gap-3" style="grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));">

                  <div v-for="tag in tags.top_tags.slice(0, 8)" :key="tag.tag"
                    class="group flex items-center gap-3 cursor-pointer hover:bg-[#2A2A35]/50 transition-colors p-2 rounded-xl"
                    @click="selectSuggestion(tag.tag)">

                    <div class="w-12 h-12 flex-shrink-0 overflow-hidden rounded-lg relative">
                      <div class="absolute inset-0 bg-[#0D0D12]/20 group-hover:bg-transparent transition-colors z-10">
                      </div>
                      <img :src="ImageSrc(tag.cover_image)"
                        class="w-full h-full object-cover grayscale opacity-80 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-300">
                    </div>

                    <div class="overflow-hidden">
                      <p
                        class="text-sm font-semibold text-[#FAF8F5] font-sans truncate group-hover:text-[#C9A84C] transition-colors">
                        {{ tag.tag }}
                      </p>
                      <p class="text-xs font-mono text-[#FAF8F5]/40 truncate mt-0.5">
                        {{ tag.count }} pins
                      </p>
                    </div>

                  </div>
                </div>

                <h3 class="text-xs uppercase tracking-wider font-semibold text-[#FAF8F5]/50 font-sans mt-6 mb-3">Ideas
                  for you</h3>
                <div class="grid gap-3" style="grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));">

                  <div v-for="tag in tags.recommended_tags.slice(0, 8)" :key="tag.tag"
                    class="group flex items-center gap-3 cursor-pointer hover:bg-[#2A2A35]/50 transition-colors p-2 rounded-xl"
                    @click="selectSuggestion(tag.tag)">

                    <div class="w-12 h-12 flex-shrink-0 overflow-hidden rounded-lg relative">
                      <div class="absolute inset-0 bg-[#0D0D12]/20 group-hover:bg-transparent transition-colors z-10">
                      </div>
                      <img :src="ImageSrc(tag.cover_image)"
                        class="w-full h-full object-cover grayscale opacity-80 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-300">
                    </div>

                    <div class="overflow-hidden">
                      <p
                        class="text-sm font-semibold text-[#FAF8F5] font-sans truncate group-hover:text-[#C9A84C] transition-colors">
                        {{ tag.tag }}
                      </p>
                      <p class="text-xs font-mono text-[#FAF8F5]/40 truncate mt-0.5">
                        {{ tag.count }} pins
                      </p>
                    </div>

                  </div>
                </div>
              </div>
            </div>




          </div>
        </div>

        <!-- Theme Toggle on Mobile -->
        <button @click="toggleDarkMode"
          class="md:hidden p-2 text-[#FAF8F5]/80 hover:text-[#FAF8F5] transition-colors cursor-pointer mr-1"
          aria-label="Toggle Theme">
          <component :is="isDarkMode ? Sun : Moon" class="w-5 h-5 text-[#FAF8F5]/80" />
        </button>

        <!-- Navigation Items - Hidden on Mobile -->
        <div class="hidden md:flex items-center space-x-1 sm:space-x-2">
          <!-- Generate -->
          <button @click="webState.sidebarWidth = webState.sidebarWidth === 0 ? 500 : 0;"
            class="magnetic-button text-[#0D0D12] bg-[#C9A84C] rounded-full flex items-center space-x-2 px-5 py-2.5 font-sans font-medium text-sm transition-colors cursor-pointer shadow-[0_0_15px_rgba(201,168,76,0.15)]">
            <svg class="w-4 h-4 relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
            <span class="relative z-10">Generate</span>
          </button>

          <!-- New: Models link -->
          <RouterLink to="/models">
            <button
              class="magnetic-button px-4 py-2.5 rounded-full text-sm font-sans font-medium text-[#FAF8F5]/80 hover:text-[#FAF8F5] transition-colors"
              aria-label="Models">
              <span class="relative z-10">Models</span>
            </button>
          </RouterLink>


          <!-- New: Extras link -->
          <RouterLink to="/extras">
            <button
              class="magnetic-button px-4 py-2.5 rounded-full text-sm font-sans font-medium text-[#FAF8F5]/80 hover:text-[#FAF8F5] transition-colors"
              aria-label="Extras">
              <span class="relative z-10">Extras</span>
            </button>
          </RouterLink>

          <!-- Posts link -->
          <RouterLink to="/posts">
            <button
              class="magnetic-button px-4 py-2.5 rounded-full text-sm font-sans font-medium text-[#FAF8F5]/80 hover:text-[#FAF8F5] transition-colors"
              aria-label="Posts">
              <span class="relative z-10">Posts</span>
            </button>
          </RouterLink>



          <!-- Scan -->
          <RouterLink to="/scan">
            <button
              class="magnetic-button p-2.5 text-[#FAF8F5]/80 hover:text-[#FAF8F5] rounded-full transition-colors flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5"
                stroke="currentColor" class="w-5 h-5 relative z-10">
                <path stroke-linecap="round" stroke-linejoin="round"
                  d="M12 10.5v6m3-3H9m4.06-7.19-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z" />
              </svg>

            </button>
          </RouterLink>
          <!-- Profile -->
          <RouterLink to="/profile" class="cursor-pointer">
            <button
              class="magnetic-button p-2.5 text-[#FAF8F5]/80 hover:text-[#FAF8F5] rounded-full transition-colors flex items-center justify-center">
              <svg class="w-5 h-5 relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
              </svg>
            </button>
          </RouterLink>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <div :class="['flex pb-20 md:pb-0', hideNav ? '' : 'pt-20']">
      <main class="flex-grow px-6" :style="{ marginLeft: isMobile ? '0px' : webState.sidebarWidth + 'px' }">
        <RouterView />
      </main>
    </div>

    <!-- Bottom Navigation Bar for Mobile -->
    <nav v-if="!hideNav && isMobile"
      class="fixed bottom-0 left-0 right-0 bg-[#0D0D12]/90 backdrop-blur-xl border-t border-[#2A2A35] py-2 px-6 flex items-center justify-between z-40 shadow-lg">
      <RouterLink to="/"
        class="flex flex-col items-center gap-1 text-[#FAF8F5]/70 hover:text-[#FAF8F5] transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
        <span class="text-[10px] font-sans">Home</span>
      </RouterLink>

      <button @click="webState.sidebarWidth = webState.sidebarWidth === 0 ? 500 : 0;"
        class="flex flex-col items-center gap-1 text-[#C9A84C] hover:text-[#FAF8F5] transition-colors cursor-pointer bg-transparent border-none">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        <span class="text-[10px] font-sans">Generate</span>
      </button>

      <RouterLink to="/posts"
        class="flex flex-col items-center gap-1 text-[#FAF8F5]/70 hover:text-[#FAF8F5] transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012-2h10a2 2 0 012 2v1m2 4a2 2 0 00-2-2v3m2-3V9m0 0l-9 9m9-9h-4m4 0v4" />
        </svg>
        <span class="text-[10px] font-sans">Posts</span>
      </RouterLink>

      <RouterLink to="/scan"
        class="flex flex-col items-center gap-1 text-[#FAF8F5]/70 hover:text-[#FAF8F5] transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 13h6m-3-3v6m-9 1V4a2 2 0 012-2h6l2 2h6a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
        </svg>
        <span class="text-[10px] font-sans">Scan</span>
      </RouterLink>

      <RouterLink to="/profile"
        class="flex flex-col items-center gap-1 text-[#FAF8F5]/70 hover:text-[#FAF8F5] transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        <span class="text-[10px] font-sans">Profile</span>
      </RouterLink>
    </nav>
  </div>
</template>
