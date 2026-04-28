<template>
  <div class="fixed inset-0 bg-black/80 flex justify-center items-center z-50" @click="closeModal">
    <div class="bg-[#0d1117] rounded-xl w-[95%] max-w-7xl h-[90vh] flex flex-col shadow-2xl border border-gray-800"
      @click.stop>

      <!-- Header -->
      <div class="p-4 border-b border-gray-800 flex justify-between items-center bg-[#161b22]">
        <div>
          <h2 class="text-xl font-bold text-white mb-1">{{ model.name }}</h2>
          <p class="text-sm text-gray-400">Download LoRA Model</p>
        </div>

        <div class="flex items-center gap-4">
          <a :href="`https://civitai.com/models/${model.id}`" target="_blank"
            class="text-blue-400 hover:text-blue-300 text-sm font-medium flex items-center gap-2 px-3 py-1.5 border border-blue-500/30 rounded-lg hover:bg-blue-500/10 transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
            </svg>
            Open CivitAI
          </a>
          <button
            class="text-gray-400 hover:text-white text-2xl w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-700 transition-colors"
            @click="$emit('close')">&times;</button>
        </div>
      </div>

      <!-- Main Content -->
      <div class="flex-1 overflow-hidden">
        <div v-if="model.id" class="h-full flex">
          <!-- Left Side - Image Gallery -->
          <div class="w-1/2 bg-[#0d1117] p-6 flex flex-col">
            <!-- Main Image Display -->
            <div class="flex-1 mb-4 bg-gray-900 rounded-lg overflow-hidden relative">
              <div v-if="selectedVersion?.images?.length" class="h-full flex items-center justify-center">
                <img v-if="selectedImageUrl" :src="selectedImageUrl" alt="Selected preview"
                  class="max-w-full max-h-full object-contain rounded-lg">
                <div v-else class="text-gray-500 text-center">
                  <svg class="w-16 h-16 mx-auto mb-2 opacity-50" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd"
                      d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"
                      clip-rule="evenodd" />
                  </svg>
                  <p>Select an image to preview</p>
                </div>
              </div>
              <div v-else class="h-full flex items-center justify-center text-gray-500">
                <div class="text-center">
                  <svg class="w-16 h-16 mx-auto mb-2 opacity-50" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd"
                      d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"
                      clip-rule="evenodd" />
                  </svg>
                  <p>No preview images available</p>
                </div>
              </div>

              <!-- Navigation arrows -->
              <button v-if="selectedVersion?.images?.length > 1" @click="navigateImage(-1)"
                class="absolute left-2 top-1/2 transform -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-2 rounded-full transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <button v-if="selectedVersion?.images?.length > 1" @click="navigateImage(1)"
                class="absolute right-2 top-1/2 transform -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-2 rounded-full transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>

            <!-- Thumbnail Strip -->
            <div v-if="selectedVersion?.images?.length" class="flex gap-2 overflow-x-auto pb-2">
              <div v-for="(image, index) in selectedVersion.images" :key="index" :class="[
                'flex-shrink-0 w-16 h-16 rounded-lg overflow-hidden cursor-pointer transition-all duration-200 border-2',
                selectedImageUrl === image.url
                  ? 'border-blue-500 shadow-lg shadow-blue-500/25'
                  : 'border-gray-700 hover:border-gray-500'
              ]" @click="selectImage(image.url)">
                <img :src="image.url" :alt="`Thumbnail ${index + 1}`" class="w-full h-full object-cover">
              </div>
            </div>
          </div>

          <!-- Right Side - Details and Downloads -->
          <div class="w-1/2 bg-[#161b22] p-6 overflow-y-auto">
            <!-- Model Info -->
            <div class="space-y-6">
              <!-- Creator and Stats -->
              <div class="flex items-center gap-4 text-sm text-gray-400 flex-wrap">
                <span class="flex items-center gap-1">
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                      clip-rule="evenodd"></path>
                  </svg>
                  {{ model.creator?.username }}
                </span>
                <span class="px-2 py-1 bg-gray-700 rounded-full text-xs">{{ model.type }}</span>
                <span class="flex items-center gap-1">
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd"
                      d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                      clip-rule="evenodd"></path>
                  </svg>
                  {{ model.stats?.downloadCount?.toLocaleString() }}
                </span>
                <span class="flex items-center gap-1">
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z">
                    </path>
                  </svg>
                  {{ model.stats?.thumbsUpCount?.toLocaleString() }}
                </span>
              </div>

              <!-- Version Tabs -->
              <div class="space-y-3">
                <h4 class="text-lg font-semibold text-white">Versions</h4>
                <div class="flex flex-wrap gap-1 bg-gray-800 p-1 rounded-lg">
                  <button v-for="version in model.modelVersions" :key="version.id"
                    @click="selectedVersionId = version.id; selectedImageUrl = version.images[0].url" :class="[
                      'px-2 py-1.5 rounded-md text-sm font-medium transition-all duration-200 flex',
                      selectedVersionId === version.id
                        ? 'bg-blue-600 text-white shadow-lg'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    ]">
                    {{ version.name }}
                    <!--checkmark-->
                    <span v-if="model_isInstalled[version?.id]" class="ml-1 my-auto text-green-400">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2"
                        stroke="currentColor" class="w-4 h-4">
                        <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                      </svg>
                    </span>
                  </button>
                </div>
              </div>

              <!-- Version Details -->
              <div v-if="selectedVersion" class="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                <div class="flex justify-between items-start mb-3">
                  <div>
                    <h5 class="text-lg font-semibold text-white">{{ selectedVersion.name }}</h5>
                    <p class="text-sm text-gray-400">{{ selectedVersion.baseModel }} • {{
                      formatDate(selectedVersion.publishedAt) }} • {{ selectedVersion.id }}</p>
                  </div>
                  <div class="text-right space-y-1">
                    <div class="text-sm text-gray-400 flex items-center gap-1">
                      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd"
                          d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                          clip-rule="evenodd"></path>
                      </svg>
                      {{ selectedVersion.stats?.downloadCount?.toLocaleString() }}
                    </div>
                    <div class="text-sm text-green-400 flex items-center gap-1">
                      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z">
                        </path>
                      </svg>
                      {{ selectedVersion.stats?.thumbsUpCount?.toLocaleString() }}
                    </div>
                  </div>
                </div>

                <div v-if="selectedVersion?.description" class="text-gray-300 text-sm leading-relaxed mb-4"
                  v-html="selectedVersion.description"></div>

                <!-- Trigger Words -->
                <div v-if="selectedVersion?.trainedWords?.length"
                  class="mb-4 bg-blue-900/10 border border-blue-500/20 rounded-lg p-3">
                  <h6 class="text-sm font-medium text-blue-300 mb-2">Trigger Words</h6>
                  <div class="flex flex-wrap gap-1">
                    <span v-for="word in selectedVersion.trainedWords" :key="word"
                      class="px-2 py-1 bg-blue-800/30 text-blue-200 text-xs rounded border border-blue-600/30">
                      {{ word }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Subfolder Selector -->
              <div v-if="selectedVersion" class="space-y-2">
                <label class="block text-sm font-medium text-gray-300">Save to subfolder:</label>
                <select v-model="selectedSubfolder"
                  class="w-full bg-gray-800 text-white rounded-lg px-3 py-2 text-sm border border-gray-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors">
                  <option v-for="folder in subFolders['LORA']" :key="folder" :value="folder">
                    {{ folder }}
                  </option>
                </select>
              </div>

              <!-- Files Section -->
              <div v-if="selectedVersion?.files?.length" class="space-y-4">
                <h6 class="text-lg font-semibold text-white">Files ({{ selectedVersion.files.length }})</h6>
                <div class="space-y-2">
                  <div v-for="file in selectedVersion.files" :key="file.id"
                    class="bg-gray-800/30 border border-gray-700 rounded-lg p-3 hover:bg-gray-800/50 transition-colors">
                    <div class="flex justify-between items-center">
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 mb-1">
                          <div class="text-sm font-medium text-white truncate">{{ file.name }}</div>
                          <span v-if="file.primary"
                            class="px-1.5 py-0.5 bg-green-600/20 text-green-300 text-xs rounded border border-green-600/30">Primary</span>
                        </div>
                        <div class="flex items-center gap-3 text-xs text-gray-400">
                          <span class="flex items-center gap-1">
                            <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                              <path fill-rule="evenodd"
                                d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z"
                                clip-rule="evenodd"></path>
                            </svg>
                            {{ formatFileSize(file.sizeKB) }}
                          </span>
                          <span>{{ file.type }}</span>
                          <span v-if="file.virusScanResult"
                            :class="file.virusScanResult === 'Success' ? 'text-green-400' : 'text-red-400'">
                            Scan: {{ file.virusScanResult }}
                          </span>
                        </div>
                      </div>
                      <button v-if="model_isInstalled[selectedVersionId] != true || !file.primary" @click="downloadFile(file)"
                        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 hover:shadow-lg flex items-center gap-2 ml-3">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z">
                          </path>
                        </svg>
                        Download
                      </button>
                      <button v-else
                        class="bg-green-600  text-white px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 hover:shadow-lg flex items-center gap-2 ml-3 cursor-default">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7">
                          </path>
                        </svg>
                        Downloaded
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Model Description -->
              <div v-if="model.description" class="bg-gray-800/30 rounded-lg p-4 border border-gray-700">
                <h6 class="text-sm font-semibold text-white mb-2">About this model</h6>
                <div class="text-gray-300 text-sm leading-relaxed" v-html="model.description"></div>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="!model.id" class="flex items-center justify-center h-full">
          <div class="text-center space-y-4">
            <div class="animate-spin rounded-full h-12 w-12 border-2 border-blue-500 border-t-transparent mx-auto">
            </div>
            <div>
              <p class="text-white text-lg font-medium">Loading model details...</p>
              <p class="text-gray-400 text-sm">Please wait while we fetch the information</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>

import { ref, onMounted, computed } from 'vue';


const model = ref({});
const selectedVersionId = ref(null);
const selectedSubfolder = ref('/');
const selectedImageUrl = ref(null);
const subFolders = ref([])

const props = defineProps({
  modelId: {
    type: String,
    required: true
  },
  url: {
    type: String,
    default: ''
  }
});

const selectedVersion = computed(() => {
  if (!selectedVersionId.value || !model.value.modelVersions) return null;
  return model.value.modelVersions.find(v => v.id === selectedVersionId.value);
});

onMounted(() => {
  // Fetch model details when the component is mounted
  fetchModelDetails();
  fetchSubFolders();
});

async function fetchModelDetails() {
  let apiUrl = 'https://civitai.com/api/v1/models/' + props.modelId;
  let response = await fetch(apiUrl);
  if (response.ok) {
    model.value = await response.json();
    // Auto-select first version
    if (model.value.modelVersions && model.value.modelVersions.length > 0) {
      selectedVersionId.value = model.value.modelVersions[0].id;
      // Auto-select first image if available
      if (model.value.modelVersions[0].images && model.value.modelVersions[0].images.length > 0) {
        selectedImageUrl.value = model.value.modelVersions[0].images[0].url;
      }
    }
    GetInstalledModels();
  } else {
    console.error('Failed to fetch model details:', response.statusText);
  }
}

async function fetchSubFolders() {
  // Fetch subfolders from the API
  let apiUrl = props.url + 'civitai_api/subfolders';
  let response = await fetch(apiUrl);
  if (response.ok) {
    subFolders.value = await response.json()
  } else {
    console.error('Failed to fetch subfolders:', response.statusText);
  }
}

function closeModal() {
  $emit('close');
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString();
}

function formatFileSize(sizeKB) {
  if (sizeKB < 1024) {
    return `${sizeKB.toFixed(1)} KB`;
  } else if (sizeKB < 1024 * 1024) {
    return `${(sizeKB / 1024).toFixed(1)} MB`;
  } else {
    return `${(sizeKB / (1024 * 1024)).toFixed(1)} GB`;
  }
}

async function downloadFile(file) {
  // Check if it's a .safetensors file
  if (file.name.endsWith('.safetensors')) {
    console.log('Download Info:');
    console.log('Version ID:', selectedVersionId.value);
    console.log('Selected Image URL:', selectedImageUrl.value);
    console.log('Selected Subfolder:', selectedSubfolder.value);
    console.log('File:', file.name);

    const body = {
      "imageUrl": selectedImageUrl.value,
      "subfolder": selectedSubfolder.value,
      "modelId": parseInt(selectedVersionId.value),
      "token": "28f7a30c25bebcda5378345857393ef3",
    }
    //post to url +civitai_api/download

    const response = await fetch(props.url + 'civitai_api/download', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    })

    if (!response.ok) {
      console.error('Download failed:', response.statusText);
      return;
    }

    const fileData = await response.json();
    console.log('Download successful:', fileData);
    RefreshInstalledModels();

    return;
  }

  const link = document.createElement('a');
  link.href = file.downloadUrl;
  link.download = file.name;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function selectImage(imageUrl) {
  selectedImageUrl.value = imageUrl;
}

function navigateImage(direction) {
  if (!selectedVersion.value?.images?.length) return;

  const currentIndex = selectedVersion.value.images.findIndex(img => img.url === selectedImageUrl.value);
  let newIndex = currentIndex + direction;

  if (newIndex < 0) {
    newIndex = selectedVersion.value.images.length - 1;
  } else if (newIndex >= selectedVersion.value.images.length) {
    newIndex = 0;
  }

  selectedImageUrl.value = selectedVersion.value.images[newIndex].url;
}

function getImageIndex(imageUrl) {
  if (!selectedVersion.value?.images) return 0;
  return selectedVersion.value.images.findIndex(img => img.url === imageUrl);
}

function openImageModal(imageUrl) {
  window.open(imageUrl, '_blank');
}
const model_isInstalled = ref({});

async function GetInstalledModels() {

  let list_of_ids = [];
  for (const version of model.value.modelVersions) {
    if (!model_isInstalled.value[version.id]) {
      list_of_ids.push(version.id);
    }
  }
  let url = props.url + 'civitai_api/installed?id_type=id&ids=' + list_of_ids.join(',');
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
      for (const version of model.value.modelVersions) {
        if (!model_isInstalled.value[version.id]) {
          model_isInstalled.value[version.id] = data.is_installed[version.id] || false;
        }
      }

    } else {
      console.error('Failed to fetch installed models:', response.statusText);
    }
  } catch (error) {
    console.error('Error fetching installed models:', error);
  }
}

async function RefreshInstalledModels() {
  //post to /civitai_api/refresh-installed
  const response = await fetch(props.url + 'civitai_api/refresh-installed', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  });
  if (response.ok) {
    await GetInstalledModels();
  } else {
    console.error('Failed to refresh installed models:', response.statusText);
  }
}

</script>