<script setup>
import { webState } from '@/api'
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

const api_access = "&api_key=1eee46ec7bc85a93e10cd74310ebab08db0ac7a45baba8f1173286902286676889c783342bc3a0a467d18e24a74e6f56e9d078225c717e1055c2ee3192f44ddf&user_id=1696472"
const blacklist_tags = ' -furry -furry_focus -futa_only -futanari -gay -male/male -male_only -male_penetrating_male -penis_focus -penis_size_difference -tentacle_on_male -1futa -femboy -bara_tits -bara -anthro -canine_genitalia -male_masturbation -reptile -ai_generated'

const pins = ref([])
const columns = ref([])
const columnCount = ref(4)
const isLoading = ref(false)
const page = ref(0)
const searchQuery = ref('')
const autocompleteResults = ref([])

const getUniquePinsById = (pinsArray) => {
  const uniqueMap = new Map();
  pinsArray.forEach(pin => {
    if (!uniqueMap.has(pin.id)) {
      uniqueMap.set(pin.id, pin);
    }
  });
  return Array.from(uniqueMap.values());
}

const updateColumns = () => {
    let count = 4;
    if (window.innerWidth < 640) count = 2;
    else if (window.innerWidth < 1024) count = 3;
    else if (window.innerWidth > 1536) count = 5;
    
    columnCount.value = count;
    
    const cols = Array.from({length: count}, () => []);
    pins.value.forEach((pin, index) => {
        cols[index % count].push(pin);
    });
    columns.value = cols;
}

const remix = (prompt) => {
    webState.remixImage = {
        Prompt: prompt,
    }
}

function format_tags(_tags) {
    if (!_tags) return '';
    var tags = _tags.replace(/ /g, ", ")
    tags = tags.replace(/_/g, " ")
    return tags
}

watch(() => pins.value, updateColumns, {deep: true});

const fetchCurrentPage = async () => {
  if (isLoading.value) return
  isLoading.value = true
  try {
    const term = (searchQuery.value || '') + blacklist_tags;
    const url = `https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1&limit=60&pid=${page.value}&tags=${encodeURIComponent(term)}${api_access}`;
    const res = await fetch(url);
    const data = await res.json();
    if (data && data.length) {
      if (page.value === 0) {
        pins.value = getUniquePinsById(data);
      } else {
        const combinedPins = [...pins.value, ...data];
        pins.value = getUniquePinsById(combinedPins);
      }
    }
  } catch (e) {
    console.error(e)
  } finally {
    isLoading.value = false
  }
}

const loadMore = () => {
  if (isLoading.value) return
  page.value++
  fetchCurrentPage()
}

const handleScroll = () => {
  if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 512) {
    loadMore()
  }
}

const onSearch = () => {
  page.value = 0
  pins.value = []
  fetchCurrentPage()
}

const fetchAutocomplete = async (e) => {
  const query = e.target.value;
  searchQuery.value = query;
  
  if (!query || query.length < 2) {
      autocompleteResults.value = [];
      return;
  }
  const tags = query.split(' ').pop();
  if(!tags) return;
  try {
      const res = await fetch(`https://api.rule34.xxx/autocomplete.php?q=${tags}`);
      const data = await res.json();
      autocompleteResults.value = data;
  } catch(e) {
      console.error(e);
  }
}

const selectTag = (tag) => {
  const words = searchQuery.value.split(' ');
  words.pop();
  words.push(tag);
  searchQuery.value = words.join(' ') + ' ';
  autocompleteResults.value = [];
  onSearch();
}

onMounted(() => {
  fetchCurrentPage()
  window.addEventListener('scroll', handleScroll)
  window.addEventListener('resize', updateColumns)
  updateColumns()
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('resize', updateColumns)
})

</script>

<template>
  <div class="booru-container">
    <div class="search-container mb-6 mt-8 max-w-[800px] mx-auto px-6 relative">
      <div class="relative w-full text-white">
        <input 
          type="text" 
          :value="searchQuery"
          @input="fetchAutocomplete"
          @keydown.enter="onSearch"
          placeholder="Search tags..."
          class="w-full bg-[#14141A] border border-[#2A2A35]/50 text-[#FAF8F5] rounded-full px-6 py-3 outline-none focus:border-[#C9A84C]/50 transition-colors"
        />
        <button 
          @click="onSearch"
          class="absolute right-2 top-1/2 -translate-y-1/2 bg-[#2A2A35] hover:bg-[#C9A84C] hover:text-[#1A1A24] text-[#FAF8F5] px-4 py-1.5 rounded-full transition-colors"
        >
          Search
        </button>
      </div>
      
      <div v-if="autocompleteResults.length" class="absolute z-50 mt-2 w-[calc(100%-3rem)] bg-[#14141A] border border-[#2A2A35] rounded-xl shadow-xl overflow-hidden">
        <div 
          v-for="res in autocompleteResults" 
          :key="res.value"
          @click="selectTag(res.value)"
          class="px-4 py-2 hover:bg-[#2A2A35] cursor-pointer text-[#FAF8F5]/80 hover:text-[#C9A84C] transition-colors flex justify-between items-center"
        >
          <span class="font-medium">{{ res.value }}</span>
          <span class="text-xs text-[#FAF8F5]/40">{{ res.label.match(/\((\d+)\)/)?.[1] || '' }}</span>
        </div>
      </div>
    </div>
    
    <div class="px-6 mx-auto w-full">
      <div class="flex gap-4">
        <div v-for="(col, colIndex) in columns" :key="colIndex" class="flex flex-col gap-4 flex-1">
          <div v-for="pin in col" :key="pin.id" class="relative group rounded-xl overflow-hidden bg-[#1A1A24] border border-[#2A2A35]/30 shadow-lg break-inside-avoid">
            <template v-if="pin.file_url.endsWith('.mp4')">
              <video 
                :src="pin.file_url" 
                loop
                class="w-full h-auto object-cover"
                :poster="pin.preview_url"
                @mouseenter="$event.target.play()"
                @mouseleave="$event.target.pause(); $event.target.currentTime = 0;"
              ></video>
              <div class="absolute top-2 right-2 bg-black/60 px-2 py-1 rounded text-xs text-white font-mono z-10 pointer-events-none">MP4</div>
            </template>
            <template v-else>
              <img 
                :src="pin.sample_url" 
                loading="lazy"
                class="w-full h-auto object-cover transition-transform duration-500 group-hover:scale-[1.02]"
                :alt="pin.tags"
              />
            </template>
            
            <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
              <div class="absolute bottom-4 left-4 right-4 pointer-events-auto">
                <p class="text-white text-xs line-clamp-3 font-mono opacity-80 mb-2">{{ format_tags(pin.tags) }}</p>
                <div class="flex justify-between items-center text-[#C9A84C] text-xs font-semibold">
                  <span>Score: {{ pin.score }}</span>
                  <div class="flex gap-2">
                    <button @click="remix(format_tags(pin.tags))" class="hover:text-white transition-colors border border-[#C9A84C]/50 px-2 py-1 rounded bg-black/50">Use Prompt</button>
                    <a :href="'https://rule34.xxx/index.php?page=post&s=view&id=' + pin.id" target="_blank" class="hover:text-white transition-colors border border-[#C9A84C]/50 px-2 py-1 rounded bg-black/50">View Original</a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="isLoading" class="flex flex-col items-center justify-center my-12" aria-live="polite">
      <div class="relative w-12 h-12 mb-4">
        <div class="absolute inset-0 rounded-full border-t-2 border-[#C9A84C] border-opacity-20"></div>
        <div class="absolute inset-0 rounded-full border-t-2 border-[#C9A84C] animate-spin"></div>
      </div>
      <span class="text-[#FAF8F5]/60 font-mono text-sm tracking-widest uppercase">
        Loading Sequence
      </span>
    </div>
    
    <div class="text-center text-[#FAF8F5]/40 font-mono text-xs mt-8 mb-12">
      [ Page {{ String(page).padStart(3, '0') }} ]
    </div>
  </div>
</template>

<style scoped>
.booru-container {
  min-height: 100vh;
}
</style>
