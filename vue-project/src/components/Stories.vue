<template>
  <div class="p-4 space-y-4 text-gray-200 hidden"> <!-- added text-gray-200 -->
    <div class="flex items-center gap-3">
      <h1 class="text-xl font-semibold">Highlights</h1>
      <button @click="onGenerate" :disabled="generating"
        class="px-3 py-1.5 rounded bg-indigo-600 text-white text-sm disabled:opacity-50">
        <span v-if="!generating">Generate Story</span>
        <span v-else>Generating...</span>
      </button>
      <div class="ml-auto text-xs text-gray-400" v-if="stories.length">{{ stories.length }} stories</div> <!-- gray-500 -> gray-400 -->
    </div>

    <!-- Story Bubbles -->
    <div class="story-strip flex gap-3 overflow-x-auto pb-2 hidden">
      <button v-for="s in stories.slice(0,10)" :key="s.id" @click="openStory(s.id)"
      class="flex flex-col items-center min-w-[70px] group">
      <div class="w-24 h-32 rounded-xl border-2 border-blue-800 ring-2 ring-transparent group-hover:ring-indigo-400 overflow-hidden bg-gray-700 relative">
        <img v-if="s.cover?.Path" :src="imageSrc(s.cover.Path)" :alt="s.title" class="w-full h-full object-cover" loading="lazy" />
        <div v-else class="w-full h-full flex items-center justify-center text-[10px] text-gray-400">No cover</div>
        <div class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent p-1">
        <span class="block text-white text-[16px] truncate px-1">{{ s.title }}</span>
        </div>
      </div>
      </button>
    </div>

    <!-- Empty State -->
    <div v-if="!stories.length && !loading" class="text-sm text-gray-400">
      No stories yet. Click Generate Story.
    </div>
    <div v-if="loading" class="text-sm text-gray-400">Loading...</div>
  </div>

  <!-- Fullscreen Viewer -->
  <div
    v-if="viewerOpen"
    class="fixed inset-0 bg-black/95 z-50 flex flex-col"
    @keyup.esc="closeViewer"
    @keydown="onKeydown"
    tabindex="0"
    ref="viewerEl"
  >
    <!-- Progress bars -->
    <div class="px-3 pt-4 space-y-2 select-none">
      <div class="flex gap-1">
        <div v-for="(sl,i) in selectedStory.slides" :key="sl.image_id" class="h-1 flex-1 bg-white/25 rounded overflow-hidden"> <!-- white/20 -> white/25 -->
          <div class="h-full bg-white" :style="{width: progressWidth(i)}"></div>
        </div>
      </div>
      <div class="flex items-center justify-between text-white text-sm px-1">
        <span class="font-medium truncate max-w-[60%]">{{ selectedStory.title }}</span>
        <div class="flex items-center gap-3">
          <button @click="togglePlay" class="text-xs px-2 py-1 rounded bg-white/10 hover:bg-white/20">
            {{ playing ? 'Pause' : 'Play' }}
          </button>
          <button @click="closeViewer" class="text-xs px-2 py-1 rounded bg-white/10 hover:bg-white/20">Close</button>
        </div>
      </div>
    </div>

    <!-- Slide area -->
    <div class="flex-1 relative" @click="onViewerTap">
        <RouterLink :to="'image/'+currentSlide?.image_id">
            <div :key="currentSlide?.image_id" class="absolute inset-0 flex items-center justify-center">
              <img v-if="currentSlide?.image?.Path" :src="imageSrc(currentSlide.image.Path)"
                   class="max-h-full max-w-full object-contain" :alt="currentSlide.caption || ''" />
              <div v-else class="text-gray-400 text-sm">Loading...</div>
              <div class="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/70 to-transparent">
                <p class="text-white text-sm">{{ currentSlide?.caption }}</p>
              </div>
            </div>
        </RouterLink>
      <!-- Tap zones -->
      <div class="absolute inset-y-0 left-0 w-1/3"></div>
      <div class="absolute inset-y-0 right-0 w-1/3"></div>

      <!-- Arrow buttons -->
      <button
        @click.stop="prevSlide"
        aria-label="Previous"
        class="absolute left-3 top-1/2 -translate-y-1/2 p-2 sm:p-3 rounded-full bg-white/10 hover:bg-white/20 text-white"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 sm:h-6 sm:w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <button
        @click.stop="nextSlide"
        aria-label="Next"
        class="absolute right-3 top-1/2 -translate-y-1/2 p-2 sm:p-3 rounded-full bg-white/10 hover:bg-white/20 text-white"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 sm:h-6 sm:w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { listStories, getStory, generateStory, ImageSrc } from '@/api'

const stories = ref([])
const loading = ref(false)
const generating = ref(false)
const selectedStory = ref(null)
const viewerOpen = ref(false)
const slideIndex = ref(0)
const playing = ref(true)
let timer = null
let slideStart = ref(0)
let rafId = null
const viewerEl = ref(null)

function imageSrc(path){ return ImageSrc(path) }
function formatDate(ts){ if(!ts) return ''; return new Date(ts * 1000).toLocaleDateString() }

async function loadStories(){
  loading.value = true
  try { stories.value = await listStories() } finally { loading.value = false }
}

async function openStory(id){
  selectedStory.value = null
  const data = await getStory(id)
  selectedStory.value = data
  slideIndex.value = 0
  playing.value = true
  viewerOpen.value = true
  startSlide()
  await nextTick()
  viewerEl.value && viewerEl.value.focus()
}

function closeViewer(){
  viewerOpen.value = false
  clearTimer()
  cancelRaf()
}

async function onGenerate(){
  if(generating.value) return
  generating.value = true
  try {
    const s = await generateStory()
    stories.value.unshift({
      id: s.id, title: s.title, cover_image_id: s.cover_image_id, cover: null,
      created_at: s.created_at, slides_count: s.slides?.length || 0
    })
    await openStory(s.id)
  } finally { generating.value = false }
}

const currentSlide = computed(()=> selectedStory.value?.slides?.[slideIndex.value])

function nextSlide(){
  if(!selectedStory.value) return
  slideIndex.value = (slideIndex.value + 1) % selectedStory.value.slides.length
  startSlide()
}
function prevSlide(){
  if(!selectedStory.value) return
  slideIndex.value = (slideIndex.value - 1 + selectedStory.value.slides.length) % selectedStory.value.slides.length
  startSlide()
}
function setSlide(i){ slideIndex.value = i; startSlide() }

function startSlide(){
  clearTimer()
  cancelRaf()
  slideStart.value = performance.now()
  if(playing.value){
    scheduleNext()
    tickProgress()
  }
  // prefetch next
  const next = selectedStory.value?.slides[(slideIndex.value + 1) % selectedStory.value.slides.length]
  if(next?.image?.Path){
    const img = new Image()
    img.src = imageSrc(next.image.Path)
  }
}

function scheduleNext(){
  const dur = currentSlide.value?.duration || 4
  timer = setTimeout(()=>{ nextSlide() }, dur * 1000)
}
function clearTimer(){ if(timer){ clearTimeout(timer); timer=null } }

function tickProgress(){
  rafId = requestAnimationFrame(()=>{
    if(playing.value) tickProgress()
  })
}
function cancelRaf(){ if(rafId){ cancelAnimationFrame(rafId); rafId=null } }

function togglePlay(){
  playing.value = !playing.value
  if(playing.value){ startSlide() } else { clearTimer(); cancelRaf() }
}

function progressWidth(i){
  if(!selectedStory.value) return '0%'
  const slides = selectedStory.value.slides
  if(i < slideIndex.value) return '100%'
  if(i > slideIndex.value) return '0%'
  const dur = slides[i].duration || 4
  const elapsed = playing.value ? (performance.now() - slideStart.value)/1000 : (performance.now() - slideStart.value)/1000
  const pct = Math.min(100, (elapsed / dur) * 100)
  return pct + '%'
}

function onViewerTap(e){
  const x = e.clientX
  const w = window.innerWidth
  if(x < w * 0.33) { prevSlide() } else if (x > w * 0.66) { nextSlide() } else { togglePlay() }
}

function onKeydown(e){
  if(!viewerOpen.value) return
  if(e.key === 'ArrowLeft'){ e.preventDefault(); prevSlide() }
  if(e.key === 'ArrowRight'){ e.preventDefault(); nextSlide() }
}

watch(()=>playing.value, (v)=>{
  if(!v){ clearTimer(); cancelRaf() }
})

onMounted(loadStories)
</script>

<style scoped>
/* hide scrollbar for story strip */
.story-strip::-webkit-scrollbar { display: none; }
.story-strip { -ms-overflow-style: none; scrollbar-width: none; }
/* ...existing code... */
.fade-enter-active, .fade-leave-active { transition: opacity .4s }
.fade-enter-from, .fade-leave-to { opacity: 0 }
</style>