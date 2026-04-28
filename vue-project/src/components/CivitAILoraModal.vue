<template>
  <div class="fixed inset-0 bg-[#0D0D12]/80 backdrop-blur-md flex justify-center items-center z-50 p-4 sm:p-8" @click="closeModal">
    <div class="bg-[#1A1A24] rounded-[2rem] md:rounded-[3rem] w-full max-w-[1400px] h-full max-h-[90vh] flex flex-col shadow-[0_0_50px_rgba(0,0,0,0.5)] border border-[#2A2A35] overflow-hidden"
      @click.stop>

      <div class="absolute inset-0 bg-noise opacity-5 pointer-events-none"></div>

      <!-- Header -->
      <div class="p-6 md:p-8 border-b border-[#2A2A35] flex flex-col sm:flex-row justify-between items-center gap-4 relative z-10 bg-[#1A1A24]/90 backdrop-blur-sm">
        <h2 class="uppercase text-sm font-mono tracking-widest text-[#FAF8F5]/60 mr-2 flex-shrink-0">CivitAI </h2>
        <!-- Search and Filters -->
        <div class="flex-1 flex flex-wrap sm:flex-nowrap gap-4 w-full sm:w-auto">
          <div class="relative flex-1 min-w-[200px]">
            <input v-model="searchQuery" type="text" placeholder="Search models..."
              class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-full font-sans text-[#FAF8F5] placeholder-[#FAF8F5]/40 px-5 py-3 focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] focus:outline-none transition-colors"
              @input="debouncedFetchModels" />
          </div>

          <select v-model="selectedSort" @change="resetAndFetch"
            class="bg-[#0D0D12] border border-[#2A2A35] rounded-full font-sans text-[#FAF8F5] px-5 py-3 focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] focus:outline-none transition-colors max-w-[170px] appearance-none cursor-pointer">
            <option v-for="sort in sortOptions" :key="sort.value" :value="sort.value">
              {{ sort.label }}
            </option>
          </select>

          <select v-model="selectedPeriod" @change="resetAndFetch"
            class="bg-[#0D0D12] border border-[#2A2A35] rounded-full font-sans text-[#FAF8F5] px-5 py-3 focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] focus:outline-none transition-colors max-w-[140px] appearance-none cursor-pointer">
            <option v-for="period in periodOptions" :key="period.value" :value="period.value">
              {{ period.label }}
            </option>
          </select>
        </div>
        <div class="flex gap-3 flex-shrink-0">
          <button class="magnetic-button bg-[#2A2A35] hover:bg-[#0D0D12] text-[#FAF8F5] border border-[#2A2A35] hover:border-[#C9A84C]/50 w-12 h-12 rounded-full flex items-center justify-center transition-all shadow-sm"
            @click="resetAndFetch" title="Refresh">
            <span class="relative z-10 flex">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2"
                stroke="currentColor" class="w-5 h-5">
                <path stroke-linecap="round" stroke-linejoin="round"
                  d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
              </svg>
            </span>
          </button>
          <button class="magnetic-button bg-[#2A2A35] hover:bg-red-500/20 text-[#FAF8F5] hover:text-red-400 border border-[#2A2A35] hover:border-red-500/50 w-12 h-12 rounded-full flex items-center justify-center transition-all shadow-sm"
            @click="$emit('close')"><span class="relative z-10 text-xl font-bold">&times;</span></button>
        </div>
      </div>


      <!--Tags-->
      <div class="p-4 md:px-8 border-b border-[#2A2A35] flex gap-3 overflow-x-auto relative z-10 no-scrollbar">
        <span v-for="tag in tags" :key="tag" @click="selectTag(tag)"
          class="cursor-pointer bg-[#2A2A35]/50 border border-[#2A2A35] text-[#FAF8F5] text-[11px] font-mono tracking-widest uppercase px-4 py-2 rounded-full hover:bg-[#C9A84C] hover:text-[#0D0D12] hover:border-[#C9A84C] transition-all whitespace-nowrap shadow-sm">
          {{ tag }}
        </span>
        <span v-if="tags?.length === 0" class="text-[#FAF8F5]/40 text-xs font-mono uppercase tracking-widest py-2">No tags available</span>
      </div>

      <!-- Models Grid -->
      <div class="flex-1 overflow-y-auto p-6 md:p-8 relative z-10" @scroll="onScroll" ref="scrollContainer">
        <!-- Loading Indicator -->
        <div v-if="isLoading && models.items?.length === 0" class="flex justify-center flex-col items-center h-full min-h-[300px] gap-6">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-[#C9A84C]"></div>
          <span class="text-[#FAF8F5]/60 font-mono tracking-widest uppercase text-sm">Initializing Catalog...</span>
        </div>

        <div v-if="models.items?.length > 0" class="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6 lg:gap-8">
          <div v-for="model in models.items" @click="emit('select', model.id)"
            class="cursor-pointer relative bg-[#0D0D12] border border-[#2A2A35] rounded-[2rem] shadow-lg hover:shadow-[0_10px_30px_rgba(0,0,0,0.8)] hover:-translate-y-1 hover:border-[#C9A84C]/50 transition-all duration-300 overflow-hidden group flex flex-col">
            <div class="relative w-full aspect-[3/4] overflow-hidden bg-[#1A1A24]">
              <img :src="model.modelVersions[0]?.images[0]?.url" alt=""
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out" />
              <div class="absolute inset-0 bg-gradient-to-t from-[#0D0D12] via-transparent to-transparent opacity-80 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              <div class="absolute top-4 left-4 bg-[#1A1A24]/80 backdrop-blur-md border border-[#2A2A35] text-[#FAF8F5] font-mono text-[10px] uppercase tracking-wider px-3 py-1.5 rounded-lg shadow-lg">
                {{ model.modelVersions[0]?.baseModel || 'Unknown' }}
              </div>
              
              <div v-if="model_isInstalled[model.id]" class="absolute top-4 right-4 bg-[#C9A84C] text-[#0D0D12] shadow-lg w-8 h-8 flex items-center justify-center rounded-full border-2 border-[#1A1A24]" title="Installed">
                <!--Checkmark-->
                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 font-bold" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
            
            <div class="p-5 flex-1 flex flex-col justify-between">
              <div>
                <h3 class="text-lg font-serif italic font-bold text-[#FAF8F5] leading-tight line-clamp-2 mb-3 group-hover:text-[#C9A84C] transition-colors">{{ model.name }}</h3>
              </div>
              
              <div class="flex items-center justify-between border-t border-[#2A2A35] pt-4 mt-auto">
                <div class="flex items-center gap-2 text-[11px] font-mono text-[#FAF8F5]/60 uppercase tracking-widest">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3.5 h-3.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
                  </svg>
                  <span>{{ (model.stats?.downloadCount || 0).toLocaleString() }}</span>
                </div>
                
                <div class="flex items-center gap-2" :title="model.creator?.username || 'Unknown'">
                  <img v-if="model.creator?.image" :src="model.creator.image" alt="Creator"
                    class="w-6 h-6 rounded-full object-cover border border-[#2A2A35]" />
                  <div v-else class="w-6 h-6 rounded-full bg-[#2A2A35] flex items-center justify-center font-bold text-[10px] text-[#FAF8F5]/50">
                    {{ (model.creator?.username || '?').charAt(0).toUpperCase() }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Loading More Indicator -->
        <div v-if="isLoading && models.items?.length > 0" class="flex justify-center items-center py-12 gap-4">
          <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#C9A84C]"></div>
          <span class="text-[#FAF8F5]/60 font-mono text-xs uppercase tracking-widest">Extracting Database...</span>
        </div>

        <!-- End of Results -->
        <div v-if="!isLoading && !hasNextPage && models.items?.length > 0"
          class="flex justify-center items-center py-12">
          <span class="text-[#FAF8F5]/40 font-mono text-xs uppercase tracking-widest flex items-center gap-4 before:h-px before:w-12 before:bg-[#2A2A35] after:h-px after:w-12 after:bg-[#2A2A35]">End of Archive</span>
        </div>
      </div>


    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import DownloadLoraModal from './downloadLoraModal.vue';

const baseApiUrl = 'https://civitai.com/api/v1/models?types=LORA&nsfw=true'


onMounted(() => {
  // Fetch models when the component is mounted
  fetchModels();
  fetchTags();
});

async function fetchTags() {
  const response = await fetch('https://civitai.com/api/v1/tags');
  if (response.ok) {
    tags.value = await response.json().items;
  } else {
    console.error('Failed to fetch tags:', response.statusText);
  }
}







const props = defineProps({
  isVisible: { type: Boolean, default: true },
  modelType: { type: String, default: 'checkpoint' },
  baseModel: { type: String, default: null },
  webuiUrl: { type: String, default: null },
});

const emit = defineEmits(['close', 'select']);

const searchQuery = ref('');
const selectedSort = ref('Highest Rated');
const selectedPeriod = ref('AllTime');
const selectedTag = ref('All');
const tags = ref([]);

const sortOptions = [
  { value: 'Highest Rated', label: 'Highest Rated' },
  { value: 'Most Downloaded', label: 'Most Downloaded' },
  { value: 'Most Liked', label: 'Most Liked' },
  { value: 'Most Discussed', label: 'Most Discussed' },
  { value: 'Most Collected', label: 'Most Collected' },
  { value: 'Most Images', label: 'Most Images' },
  { value: 'Newest', label: 'Newest' },
  { value: 'Oldest', label: 'Oldest' }
];

const periodOptions = [
  { value: 'AllTime', label: 'All Time' },
  { value: 'Year', label: 'Year' },
  { value: 'Month', label: 'Month' },
  { value: 'Week', label: 'Week' },
  { value: 'Day', label: 'Day' }
];

const placeholderImage = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDUwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMzMzIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk5vIEltYWdlPC90ZXh0Pjwvc3ZnPg==';
const models = ref({ items: [] });
const isLoading = ref(false);
// Remove currentPage, add currentCursor
// const currentPage = ref(1);
const currentCursor = ref(null);
const hasNextPage = ref(true);
const scrollContainer = ref(null);

// Debounce function for search
let debounceTimeout;
const debouncedFetchModels = () => {
  clearTimeout(debounceTimeout);
  debounceTimeout = setTimeout(() => {
    resetAndFetch();
  }, 500);
};

function resetAndFetch() {
  // Reset cursor and models
  currentCursor.value = null;
  hasNextPage.value = true;
  models.value = { items: [] };
  fetchModels(null, false);
}


const model_isInstalled = ref({});


async function fetchModels(cursor = null, append = false) {
  if (isLoading.value) return;

  isLoading.value = true;

  if (!append) {
    models.value = { items: [] };
  }

  let apiUrl = baseApiUrl;

  if (props.baseModel) {
    apiUrl += `&baseModels=${props.baseModel}`;

    if (props.baseModel === 'NoobAI') {
      apiUrl += '&baseModels=Illustrious';
    }
  }

  if (searchQuery.value.trim()) {
    apiUrl += `&query=${encodeURIComponent(searchQuery.value.trim())}`;
  }

  if (selectedSort.value) {
    apiUrl += `&sort=${encodeURIComponent(selectedSort.value)}`;
  }

  if (selectedPeriod.value) {
    apiUrl += `&period=${selectedPeriod.value}`;
  }

  // Use cursor for pagination
  if (cursor) {
    apiUrl += `&cursor=${encodeURIComponent(cursor)}`;
  }

  try {
    const response = await fetch(apiUrl);
    if (response.ok) {
      const newData = await response.json();

      if (append && models.value.items) {
        models.value.items.push(...newData.items);
        models.value.metadata = newData.metadata;
      } else {
        models.value = newData;
      }

      // Update cursor and hasNextPage
      currentCursor.value = newData.metadata?.nextCursor || null;
      hasNextPage.value = !!newData.metadata?.nextCursor;

      

    } else {
      console.error('Failed to fetch models:', response.statusText);
    }
  } catch (error) {
    console.error('Error fetching models:', error);
  } finally {
    isLoading.value = false;
    GetInstalledModels();
  }
}
async function GetInstalledModels() {
  let list_of_ids = [];
  for (const model of models.value.items) {
    if (!model_isInstalled.value[model.id]) {
      list_of_ids.push(model.id);
    }
  }
  let url = props.webuiUrl + 'civitai_api/installed?id_type=modelId&ids=' + list_of_ids.join(',');
  try {
    const response = await fetch(url);
    if (response.ok) {

      //response format
      // {
      //   "is_installed": {
      //     "341353": true
      //   }
      // }
      const data = await response.json();
      for (const model of models.value.items) {
        if (!model_isInstalled.value[model.id]) {
          model_isInstalled.value[model.id] = data.is_installed[model.id] || false;
        }
      }

    } else {
      console.error('Failed to fetch installed models:', response.statusText);
    }
  } catch (error) {
    console.error('Error fetching installed models:', error);
  }
}

function onScroll(event) {
  const { scrollTop, scrollHeight, clientHeight } = event.target;
  const threshold = 200; // Load more when 200px from bottom

  if (scrollHeight - scrollTop - clientHeight < threshold && hasNextPage.value && !isLoading.value) {
    // Use currentCursor for next page
    fetchModels(currentCursor.value, true);
  }
}

function closeModal() {
  emit('close');
}

function selectTag(tag) {
  selectedTag.value = tag;
}
</script>
