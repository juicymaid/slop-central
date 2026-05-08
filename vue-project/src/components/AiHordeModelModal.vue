<template>
  <div v-if="isVisible" class="fixed inset-0 bg-black/60 flex justify-center items-center z-50" @click="closeModal">
    <div class="bg-[#1A1A24] rounded-[2rem] w-[95%] max-w-6xl h-[90vh] flex flex-col shadow-2xl border border-[#2A2A35]"
      @click.stop>

      <!-- Header -->
      <div class="p-4 border-b border-[#2A2A35] flex justify-between items-center">
        <h2 class="uppercase text-sm text-[#FAF8F5]/60 tracking-wider">Select AI Horde Model</h2>
        <!-- Search -->
        <div class=" w-full mr-2 ml-4">
          <input v-model="searchQuery" type="text" placeholder="Search AI Horde models..."
            class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-lg text-[#FAF8F5] placeholder-gray-500 p-3 focus:ring-1 focus:ring-[#C9A84C] focus:outline-none" />
        </div>
        <div class="flex gap-2">
          <button class="text-[#FAF8F5]/40 hover:text-[#FAF8F5] text-xl w-8 h-8 flex items-center justify-center"
            @click="fetchModels" title="Refresh">
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

      <!-- Models Grid -->
      <div class="flex-1 overflow-y-auto p-4">
        <div class="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          <div v-for="model in filteredModels" :key="model.name"
            class="relative bg-[#0D0D12] border border-[#2A2A35] rounded-2xl shadow-xl hover:shadow-2xl hover:border-[#C9A84C]/50 transition-all flex flex-col h-full cursor-pointer overflow-hidden group"
            @click="selectModel(model)">
            
            <div class="p-6 flex-1 flex flex-col">
              <div class="flex justify-between items-start mb-4">
                <h3 class="text-xl font-bold text-[#FAF8F5] break-words line-clamp-2" :title="model.name">
                  {{ model.name }}
                </h3>
                <span class="bg-[#1A1A24] border border-[#2A2A35] text-xs font-mono px-2 py-1 rounded text-blue-400 shrink-0">
                  {{ model.type }}
                </span>
              </div>
              
              <div class="grid grid-cols-2 gap-3 text-sm mt-auto border-t border-[#2A2A35] pt-4">
                <div class="flex flex-col">
                  <span class="text-[#FAF8F5]/40 text-[10px] uppercase tracking-wider mb-1">Workers</span>
                  <span class="font-mono text-[#FAF8F5] flex items-center gap-1 text-sm">
                    <svg class="w-3 h-3 text-green-400" fill="currentColor" viewBox="0 0 20 20"><path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z"></path></svg>
                    {{ model.count }}
                  </span>
                </div>
                
                <div class="flex flex-col">
                  <span class="text-[#FAF8F5]/40 text-[10px] uppercase tracking-wider mb-1">Queued Jobs</span>
                  <span class="font-mono text-yellow-400 text-sm">{{ model.queued }} / {{ model.jobs }}</span>
                </div>
                
                <div class="flex flex-col">
                  <span class="text-[#FAF8F5]/40 text-[10px] uppercase tracking-wider mb-1">Performance</span>
                  <span class="font-mono text-blue-400 text-sm">{{ model.performance.toFixed(2) }} it/s</span>
                </div>
                
                <div class="flex flex-col">
                  <span class="text-[#FAF8F5]/40 text-[10px] uppercase tracking-wider mb-1">ETA</span>
                  <span class="font-mono text-purple-400 text-sm">{{ model.eta }}s</span>
                </div>
              </div>
            </div>

            <!-- Hover overlay -->
            <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center pointer-events-none">
              <span class="bg-[#C9A84C] text-[#0D0D12] px-6 py-2 rounded-lg font-bold">Select Model</span>
            </div>

          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

const props = defineProps({
  isVisible: { type: Boolean, default: true },
  url: { type: String, default: 'https://aihorde.net/api/v2/' }
});

const emit = defineEmits(['close', 'select']);

const searchQuery = ref('');
const models = ref([]);

async function fetchModels() {
  let full_url = props.url;
  if (!full_url.endsWith('/')) {
    full_url += '/';
  }
  full_url += 'status/models?type=image';

  try {
    const response = await fetch(full_url);
    if (response.ok) {
      models.value = await response.json();
      models.value.sort((a, b) => b.count - a.count);
    } else {
      console.error('Failed to fetch AI Horde models:', response.statusText);
    }
  } catch (err) {
    console.error('Error fetching AI Horde models:', err);
  }
}

onMounted(() => {
  fetchModels();
});

const filteredModels = computed(() => {
  let filtered = models.value;

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    filtered = filtered.filter(m => {
      const name = (m.name || '').toLowerCase();
      return name.includes(q);
    });
  }
  return filtered;
});

function closeModal() {
  emit('close');
}

function selectModel(model) {
  emit('select', {
    ...model,
    model_name: model.name,
    title: model.name,
    filename: model.name
  });
  closeModal();
}
</script>
