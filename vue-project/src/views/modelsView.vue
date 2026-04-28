<template>
  <div class="mb-6 mt-4 rounded-[2rem] border border-[#2A2A35] bg-[#0D0D12]/60 backdrop-blur-xl shadow-md mx-6">
    <div class="p-4 sm:p-5 flex flex-wrap items-center gap-4 sm:gap-6">
      <div class="flex items-center gap-3">
        <span class="text-xs font-mono uppercase tracking-widest text-[#FAF8F5]/50">Sort</span>
        <div class="inline-flex rounded-full overflow-hidden border border-[#2A2A35]">
          <button
            v-for="opt in sortOptions"
            :key="'s-' + opt"
            @click="sort = opt"
            :aria-pressed="sort === opt"
            class="px-4 py-1.5 text-xs font-sans font-medium transition-colors focus:outline-none"
            :class="sort === opt
              ? 'bg-[#2A2A35] text-[#C9A84C]'
              : 'bg-transparent text-[#FAF8F5]/60 hover:bg-[#1A1A24] hover:text-[#FAF8F5]'"
          >
            {{ formatLabel(opt) }}
          </button>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <span class="text-xs font-mono uppercase tracking-widest text-[#FAF8F5]/50">Type</span>
        <div class="inline-flex rounded-full overflow-hidden border border-[#2A2A35]">
          <button
            v-for="opt in typeOptions"
            :key="'t-' + opt"
            @click="type = opt"
            :aria-pressed="type === opt"
            class="px-4 py-1.5 text-xs font-sans font-medium transition-colors focus:outline-none"
            :class="type === opt
              ? 'bg-[#2A2A35] text-[#C9A84C]'
              : 'bg-transparent text-[#FAF8F5]/60 hover:bg-[#1A1A24] hover:text-[#FAF8F5]'"
          >
            {{ formatLabel(opt) }}
          </button>
        </div>
      </div>

      <div class="relative ml-auto w-full sm:w-64">
        <span class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#FAF8F5]/40">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M12.9 14.32a8 8 0 1 1 1.414-1.414l3.387 3.387a1 1 0 0 1-1.414 1.414l-3.387-3.387ZM14 8a6 6 0 1 1-12 0 6 6 0 0 1 12 0Z" clip-rule="evenodd" />
          </svg>
        </span>
        <input
          id="model-search"
          v-model="search"
          type="text"
          placeholder="Search models..."
          class="w-full pl-10 pr-8 py-2.5 rounded-full border text-sm font-sans bg-[#1A1A24] text-[#FAF8F5] border-[#2A2A35] focus:border-[#C9A84C] focus:outline-none transition-colors placeholder:text-[#FAF8F5]/30"
        />
        <button
          v-if="search"
          @click="search = ''"
          class="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-[#2A2A35] text-[#FAF8F5]/60 transition-colors"
          aria-label="Clear search"
          title="Clear"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 8.586 5.757 4.343 4.343 5.757 8.586 10l-4.243 4.243 1.414 1.414L10 11.414l4.243 4.243 1.414-1.414L11.414 10l4.243-4.243-1.414-1.414L10 8.586Z" clip-rule="evenodd"/>
          </svg>
        </button>
      </div>
    </div>
  </div>

  <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-6 px-6 max-w-[1400px] mx-auto">
    <div v-if="isLoading" class="col-span-full flex items-center justify-center py-20 text-[#FAF8F5]/60">
      <div class="relative w-8 h-8">
        <div class="absolute inset-0 rounded-full border-t-2 border-[#C9A84C] border-opacity-20"></div>
        <div class="absolute inset-0 rounded-full border-t-2 border-[#C9A84C] animate-spin"></div>
      </div>
    </div>
    <div v-else-if="filteredModels.length === 0" class="col-span-full text-center py-20 font-mono text-[#FAF8F5]/60 text-sm tracking-widest">
      [ NO MODELS FOUND ]
    </div>
    <ModelCard
      v-else
      v-for="model in filteredModels"
      :key="model.hash || model.id"
      :model="model"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { GetFromApi } from '@/api';
import ModelCard from '@/components/ModelCard.vue';

const models = ref([]);
const search = ref('');
const sortOptions = ['name', 'most_images', 'last_used'];
const typeOptions = ['all', 'checkpoint', 'lora'];
const sort = ref('last_used');
const type = ref('all');

// New: prettier labels for buttons
function formatLabel(s) {
  return String(s).replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// New: loading state
const isLoading = ref(false);

const filteredModels = computed(() => {
  const q = search.value.trim().toLowerCase();
  if (!q) return models.value;
  return models.value.filter(m => (m?.name || '').toLowerCase().includes(q));
});

async function fetchModels() {
  try {
    isLoading.value = true;
    models.value = await GetFromApi(`models?sort=${sort.value}&type=${type.value}`);
  } finally {
    isLoading.value = false;
  }
}

onMounted(fetchModels);

watch([sort, type], fetchModels);
</script>