<template>
  <div v-if="isVisible" class="fixed inset-0 bg-black/60 flex justify-center items-center z-50" @click="closeModal">
    <div class="bg-[#1A1A24] rounded-[2rem] w-[95%] max-w-6xl h-[90vh] flex flex-col shadow-2xl border border-[#2A2A35]"
      @click.stop>

      <!-- Header -->
      <div class="p-4 border-b border-[#2A2A35] flex justify-between items-center">
        <h2 class="uppercase text-sm text-[#FAF8F5]/60 tracking-wider">Select Model</h2>
        <!-- Search -->
        <div class=" w-full mr-2">
          <input v-model="searchQuery" type="text" placeholder="Search models..."
            class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-lg text-[#FAF8F5] placeholder-gray-500 p-3 focus:ring-1 focus:ring-[#C9A84C] focus:outline-none" />
        </div>
        <div class="flex gap-2">
          <button class="text-[#FAF8F5]/40 hover:text-[#FAF8F5] text-xl w-8 h-8 flex items-center justify-center"
            @click="refreshModels" title="Refresh">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5"
              stroke="currentColor" class="w-5 h-5 mt-2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
            </svg>
          </button>
          <button class="text-[#FAF8F5]/40 hover:text-[#FAF8F5] text-2xl w-8 h-8 flex items-center justify-center"
            @click="$emit('close')">&times;</button>
        </div>
      </div>



      <!-- Breadcrumb Navigation -->
      <div class="p-4 border-b border-[#2A2A35]">
        <div class="flex items-center gap-2 flex-wrap">
          <button
            class="px-3 py-1 rounded text-sm  text-[#FAF8F5] hover:bg-[#B89A45] hover:text-[#0D0D12] transition-colors magnetic-button"
            @click="navigateToPath('')">
            Root
          </button>
          <span v-if="currentPath" class="text-[#FAF8F5]/40">/</span>
          <template v-for="(segment, index) in pathSegments" :key="index">
            <button
              class="px-3 py-1 rounded text-sm  text-[#FAF8F5]/80 hover:bg-[#2A2A35] transition-colors magnetic-button"
              @click="navigateToPath(pathSegments.slice(0, index + 1).join('/'))">
              {{ segment }}
            </button>
            <span v-if="index < pathSegments.length - 1" class="text-[#FAF8F5]/40">/</span>
          </template>
          <!-- Available Subfolders -->
          <div v-if="availableSubfolders.length > 0" class="flex gap-2 flex-wrap ">
            <span class="text-[#FAF8F5]/40">/</span>

            <button v-for="folder in availableSubfolders" :key="folder"
              class="px-3 py-1 rounded text-sm bg-[#0D0D12] text-[#FAF8F5]/60 hover:bg-[#2A2A35] border border-[#2A2A35] transition-colors magnetic-button"
              @click="navigateToPath(currentPath ? `${currentPath}/${folder}` : folder)">
              📁 {{ folder }}
            </button>
          </div>
        </div>

      </div>

      <!-- Models Grid -->
      <div class="flex-1 overflow-y-auto p-4">
        <div class="grid grid-cols-1 sm:grid-cols-4 lg:grid-cols-4 gap-3">
          <div v-for="model in filteredModels" :key="model.id"
            class="relative bg-[#0D0D12] border border-[#2A2A35] rounded-2xl shadow-xl hover:shadow-2xl hover:scale-[1.02] transition-transform overflow-hidden ">
            <div class="w-full h-72 rounded-t-2xl relative overflow-hidden">
              <img v-if="!model._imgError" :src="getModelImage(model, 0)" :alt="model.name"
                class="w-full h-72 object-cover rounded-t-2xl" @error="handleImageError($event, model)" />
              <div v-else
                class="w-full h-72 flex items-center justify-center text-[#FAF8F5] text-lg font-semibold relative"
                :style="{ backgroundImage: `url(${apiUrl + '/random-image-file?model=' + (model.filename || model.name)})`, backgroundSize: 'cover', backgroundPosition: 'center' }">
                <div class="absolute inset-0 bg-black/95  flex items-center justify-center">
                  No Image
                </div>
              </div>
            </div>
            <div class="p-6">
              <h3 class="text-lg font-semibold text-[#FAF8F5]"
                :title="getModelName(model.filename) ?? model.name ?? model.filename">
                {{ getModelName(model.filename ?? model.name) }}
              </h3>
              <p class="text-[#FAF8F5]/60 text-sm mt-2 truncate" :title="model.title || model.filename">
                {{ GetPath(model.path || model.filename) }}
              </p>
            </div>

            <!-- Details on Hover -->
            <div
              class="absolute inset-0 bg-black/90 bg-opacity-90 text-[#FAF8F5] opacity-0 hover:opacity-100 transition-opacity duration-300 p-6 flex flex-col justify-between rounded-2xl">
              <div>
                <h3 class="text-xl font-bold mb-4 break-all">
                  {{ model?.civitai?.model?.name || getModelName(model.filename ?? model.name) }}
                </h3>
                <a v-if="model?.civitai?.modelId" class="cursor-pointer flex items-center gap-2 text-blue-400"
                  :href="'https://civitai.com/models/' + model?.civitai?.modelId + '?modelVersionId=' + model?.civitai?.id"
                  target="_blank">
                  <svg class="w-4 h-4 " fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14">
                    </path>
                  </svg>Open on Civitai</a>
                <!--Desc-->
                <p class="text-sm whitespace-pre-wrap break-words  overflow-y-hidden h-42"
                  v-html="model?.civitai?.description">
                </p>

              </div>
              <button
                class="mt-4 bg-[#C9A84C] text-[#0D0D12] hover:bg-[#C9A84C] text-[#0D0D12] text-[#FAF8F5] py-2 rounded-lg font-semibold transition magnetic-button"
                @click="selectModel(model)">
                {{ !loraSelected(model) ? 'Add' : 'Remove' }}
              </button>


            </div>
          </div>
        </div>
      </div>


    </div>
  </div>
</template>

<script setup>
import { apiUrl } from '@/api';
import { ref, computed, onMounted } from 'vue';

function GetPath(path) {
  // Remove everything up to and including "models" and the next category folder
  if (!path) return '';
  const parts = path.split('\\');
  const modelsIndex = parts.findIndex(part => part.toLowerCase() === 'models');
  if (modelsIndex === -1 || modelsIndex + 2 >= parts.length) return '/' + parts.slice(modelsIndex + 1).join('/');
  // Skip "models" and the next folder (category)
  return '/' + parts.slice(modelsIndex + 2).join('/');
}

function loraSelected(model) {
  // Check if the model is already selected in the current_loras array
  return props.current_loras.some(lora => lora.name === model.name);
}

const props = defineProps({
  isVisible: { type: Boolean, default: true },
  modelType: { type: String, default: 'checkpoint' },
  current_loras: { type: Array, default: () => [] },
  url: { type: String, default: 'http://127.0.0.1:8000/' }
});

const emit = defineEmits(['close', 'select']);

const searchQuery = ref('');
const selectedTag = ref('All');
const tags = [];
const placeholderImage = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDUwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMzMzIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk5vIEltYWdlPC90ZXh0Pjwvc3ZnPg==';
const models = ref([]);

const currentPath = ref('');
const folderStructure = ref({});

const pathSegments = computed(() => {
  return currentPath.value ? currentPath.value.split('/').filter(Boolean) : [];
});

function getModelName(file) {

  if (!file) return '';

  const path = file.replaceAll(/\\/g, '/');
  const parts = path.split('/');
  if (parts.length === 0) return '';
  const filename = parts[parts.length - 1];
  return filename.replace(/\.(safetensors|ckpt|pt|bin|pth)$/i, '');
}

const availableSubfolders = computed(() => {
  let current = folderStructure.value;

  // Navigate to current path
  for (const segment of pathSegments.value) {
    current = current[segment] || {};
  }

  // Return available subfolders
  return Object.keys(current).sort();
});

function buildFolderStructure() {
  const structure = {};

  for (const model of models.value) {
    if (model.path || model.filename) {
      const path = GetPath(model.path || model.filename);
      const parts = path.split('/').filter(Boolean);

      // Skip the first part if it's empty and start from index 1
      const folders = parts.slice(0, -1); // Remove filename

      let current = structure;
      for (const folder of folders) {
        if (!current[folder]) {
          current[folder] = {};
        }
        current = current[folder];
      }
    }
  }

  folderStructure.value = structure;
}

function navigateToPath(path) {
  currentPath.value = path;
}

function GetFolders() {
  // This function is now used to build the folder structure
  buildFolderStructure();
  return [];
}

const getModelImage = (model, attempt = 0) => {
  let modelPath = model.path || model.filename;
  let baseUrl = props.url + 'sd_extra_networks/thumb?filename=';

  if (attempt === 0) {
    return apiUrl + '/webui/model-image?model_path=' + encodeURIComponent(model.path || model.filename)
  } else {
    return null;
  }
};

const handleImageError = (event, model) => {
  const img = event.target;
  // mark model as having failed to load its image so template shows fallback
  try {
    model._imgError = true;
  } catch (e) {
    // fallback: assign property immutably
    Object.assign(model, { _imgError: true });
  }
  // set a lightweight placeholder in case image element remains visible briefly
  if (img && !img.dataset._placeholderSet) {
    img.src = placeholderImage;
    img.dataset._placeholderSet = '1';
  }
};

async function refreshModels() {
  let full_url = props.url;
  const isAiHorde = props.url.includes('aihorde');

  if (isAiHorde) {
    await fetchModels();
    buildFolderStructure();
    return;
  }

  if (props.modelType === 'checkpoint') {
    full_url += 'sdapi/v1/refresh-checkpoints';
  } else if (props.modelType === 'lora') {
    full_url += 'sdapi/v1/refresh-loras';
  }
  const response = await fetch(full_url, { method: 'POST' });
  if (response.ok) {
    await fetchModels();
  } else {
    console.error('Failed to refresh models:', response.statusText);
  }
  buildFolderStructure();
}

onMounted(async () => {
  await fetchModels();
  buildFolderStructure();
});

async function fetchModels() {
  let full_url = props.url;
  const isAiHorde = props.url.includes('aihorde');

  if (isAiHorde) {
    if (props.modelType === 'checkpoint') {
      full_url += 'status/models?type=image';
    } else if (props.modelType === 'lora') {
      // AI horde does not have an endpoint to list all loras. 
      // We will rely on Civitai or local loras later, but for now return empty or use the local backend loras.
      // Actually we will fetch local loras since we can use them to get CivitAI IDs.
      full_url = apiUrl + '/webui/loras';
    }
  } else {
    if (props.modelType === 'checkpoint') {
      full_url += 'sdapi/v1/sd-models';
    } else if (props.modelType === 'lora') {
      full_url = apiUrl + '/webui/loras';
    }
  }

  const response = await fetch(full_url);
  if (response.ok) {
    models.value = await response.json();
  } else {
    console.error('Failed to fetch models:', response.statusText);
  }
}

const filteredModels = computed(() => {
  let filtered = models.value;

  // Filter by current path
  if (currentPath.value) {
    filtered = filtered.filter(m => {
      const path = GetPath(m.path || m.filename);
      const modelFolder = path.split('/').slice(1, -1).join('/'); // Remove leading slash and filename
      return modelFolder.startsWith(currentPath.value);
    });
  }

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    filtered = filtered.filter(m => {
      const name = (m.model_name || m.name || '').toLowerCase();
      const title = (m.title || '').toLowerCase();
      const filename = (m.filename || '').toLowerCase();
      const path = GetPath(m.path || m.filename).toLowerCase()

      return name.includes(q) ||
        title.includes(q) ||
        filename.includes(q) ||
        path.includes(q);
    });
  }
  return filtered;
});

function closeModal() {
  emit('close');
}

function selectTag(tag) {
  selectedTag.value = tag;
}

function selectModel(model) {
  emit('select', model);

  if (props.modelType === 'checkpoint') {
    closeModal();
  }
}
</script>
