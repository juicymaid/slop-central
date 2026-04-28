<template>
  <div class="min-h-screen bg-gray-950 text-gray-100">
    <div class="mx-auto max-w-7xl p-4 sm:p-6 lg:p-8">
      <div class="mb-8 flex items-center justify-between">
        <div>
          <h1 class="text-4xl font-bold bg-gradient-to-r from-purple-400 via-pink-500 to-red-500 bg-clip-text text-transparent">
            Comics Library
          </h1>
          <p class="mt-2 text-gray-400">Explore our collection of comics</p>
        </div>
        <button
          @click="showModal = true"
          class="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 rounded-lg font-semibold shadow-lg hover:shadow-purple-500/50 transition-all duration-300 flex items-center gap-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Generate New
        </button>
      </div>

      <div v-if="loading" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
        <div v-for="i in 10" :key="'s'+i" class="animate-pulse">
          <div class="bg-gray-800/60 rounded-xl h-80 mb-3"></div>
          <div class="bg-gray-800/40 h-4 rounded mb-2"></div>
          <div class="bg-gray-800/30 h-3 rounded w-3/4"></div>
        </div>
      </div>

      <div v-else-if="error" class="rounded-lg bg-red-900/20 border border-red-500/50 p-4 text-red-400">
        {{ error }}
      </div>

      <div v-else-if="comics.length === 0" class="text-center py-16 text-gray-500">
        <svg class="mx-auto h-16 w-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
        <p>No comics available yet</p>
      </div>

      <div v-else class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
        <div
          v-for="(c, idx) in comics"
          :key="idx"
          class="group cursor-pointer"
        >
          <div class="rounded-xl overflow-hidden bg-gradient-to-br from-gray-800 to-gray-900 shadow-lg hover:shadow-2xl hover:shadow-purple-500/20 transition-all duration-300 transform hover:-translate-y-2">
            <div class="relative aspect-[3/4] bg-gray-900 overflow-hidden" @click="$router.push(`/comics/${idx}/read`)">
              <img
                v-if="c.cover_image"
                :src="c.cover_image"
                :alt="c.title || 'Comic cover'"
                class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                loading="lazy"
              />
              <div v-else class="h-full w-full bg-gradient-to-br from-gray-700 via-gray-800 to-black flex items-center justify-center text-gray-500">
                <svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-60 group-hover:opacity-40 transition-opacity"></div>
              <div class="absolute top-2 right-2 bg-purple-600 text-xs font-bold px-2 py-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                #{{ idx }}
              </div>
            </div>
            <div class="p-4">
              <h2 class="text-base font-bold truncate group-hover:text-purple-400 transition-colors">
                {{ c.title || 'Untitled' }}
              </h2>
              <p class="mt-2 text-xs text-gray-400 line-clamp-2 leading-relaxed mb-3">
                {{ c.topic || 'No description available' }}
              </p>
              <div class="flex gap-2">
                <button
                  @click.stop="$router.push(`/comics/${idx}/read`)"
                  class="flex-1 px-3 py-1.5 bg-purple-600 hover:bg-purple-500 rounded-lg text-xs font-semibold transition-colors flex items-center justify-center gap-1"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  Read
                </button>
                <button
                  @click.stop="$router.push(`/comics/${idx}`)"
                  class="flex-1 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded-lg text-xs font-semibold transition-colors flex items-center justify-center gap-1"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Edit
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Generate Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
          @click.self="showModal = false"
        >
          <div class="bg-gray-900 rounded-2xl shadow-2xl max-w-lg w-full border border-gray-800 overflow-hidden">
            <div class="p-6 border-b border-gray-800">
              <div class="flex items-center justify-between">
                <h2 class="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
                  Generate New Comic
                </h2>
                <button
                  @click="showModal = false"
                  class="text-gray-400 hover:text-gray-200 transition-colors"
                >
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <div class="p-6">
              <label class="block text-sm font-medium text-gray-300 mb-2">
                Comic Prompt
              </label>
              <textarea
                v-model="prompt"
                placeholder="Describe your comic story... (e.g., 'A superhero saves a cat from a tree')"
                class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none resize-none text-gray-100 placeholder-gray-500"
                rows="5"
                :disabled="generating"
              ></textarea>

              <div v-if="generateError" class="mt-4 p-3 bg-red-900/20 border border-red-500/50 rounded-lg text-red-400 text-sm">
                {{ generateError }}
              </div>

              <div class="mt-6 flex gap-3">
                <button
                  @click="showModal = false"
                  :disabled="generating"
                  class="flex-1 px-4 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  @click="generateComic"
                  :disabled="!prompt.trim() || generating"
                  class="flex-1 px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 rounded-lg font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center justify-center gap-2"
                >
                  <svg v-if="generating" class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span>{{ generating ? 'Generating...' : 'Generate' }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { GetFromApi } from '@/api';
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const comics = ref([]);
const loading = ref(true);
const error = ref('');
const showModal = ref(false);
const prompt = ref('');
const generating = ref(false);
const generateError = ref('');

onMounted(async () => {
  try {
    const response = await GetFromApi('comics');
    comics.value = Array.isArray(response) ? response : [];
  } catch (e) {
    error.value = 'Failed to load comics.';
  } finally {
    loading.value = false;
  }
});

async function generateComic() {
  if (!prompt.value.trim()) return;
  
  generating.value = true;
  generateError.value = '';
  
  try {
    const comicIndex = await GetFromApi(`generate-comic?prompt=${encodeURIComponent(prompt.value)}`);
    showModal.value = false;
    prompt.value = '';
    router.push(`/comics/${comicIndex}`);
  } catch (e) {
    generateError.value = 'Failed to generate comic. Please try again.';
  } finally {
    generating.value = false;
  }
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active > div,
.modal-leave-active > div {
  transition: transform 0.3s ease;
}

.modal-enter-from > div,
.modal-leave-to > div {
  transform: scale(0.9);
}
</style>