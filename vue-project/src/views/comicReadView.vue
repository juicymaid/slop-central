<template>
  <div class="min-h-screen bg-gray-950 text-gray-100">
    <!-- Header -->
    <div class="sticky top-0 z-10 bg-gray-900/95 backdrop-blur-sm border-b border-gray-800">
      <div class="mx-auto max-w-4xl px-4 py-4">
        <div class="flex items-center justify-between">
          <button
            @click="$router.push('/comics')"
            class="flex items-center gap-2 text-gray-400 hover:text-gray-200 transition-colors"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
            <span>Back to Comics</span>
          </button>
          <button
            @click="$router.push(`/comics/${$route.params.id}`)"
            class="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            <span>Edit</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-24">
      <div class="flex items-center gap-3 text-gray-400">
        <svg class="h-6 w-6 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
        </svg>
        <span>Loading comic...</span>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="mx-auto max-w-4xl px-4 py-12">
      <div class="rounded-lg bg-red-900/20 border border-red-500/50 p-6 text-red-400">
        {{ error }}
      </div>
    </div>

    <!-- Comic Content -->
    <div v-else class="mx-auto max-w-4xl px-4 py-8">
      <!-- Comic Title & Topic -->
      <div class="mb-8 text-center">
        <h1 class="text-4xl font-bold bg-gradient-to-r from-purple-400 via-pink-500 to-red-500 bg-clip-text text-transparent mb-3">
          {{ comic.title || 'Untitled Comic' }}
        </h1>
        <p v-if="comic.topic" class="text-gray-400 text-lg">{{ comic.topic }}</p>
      </div>

      <!-- Panels -->
      <div class="space-y-8">
        <div
          v-for="(panel, idx) in comic.panels"
          :key="idx"
          class="relative bg-gray-900 rounded-xl overflow-hidden shadow-2xl border border-gray-800 hover:border-gray-700 transition-colors"
        >
          <!-- Panel Number Badge -->
          <div class="absolute top-4 left-4 z-10 bg-purple-600 text-white text-xs font-bold px-3 py-1 rounded-full shadow-lg">
            Panel {{ idx + 1 }}
          </div>

          <!-- Panel Image with Text Overlays -->
          <div class="relative">
            <template v-if="panel.image">
              <img
                :src="panel.image"
                :alt="`Panel ${idx + 1}`"
                class="w-full h-auto object-contain bg-gray-950"
                loading="lazy"
              />
            </template>
            <template v-else>
              <div class="w-full aspect-video bg-gradient-to-br from-gray-800 via-gray-900 to-black flex items-center justify-center">
                <div class="text-center text-gray-600">
                  <svg class="w-16 h-16 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <p>No image available</p>
                </div>
              </div>
            </template>

            <!-- Text Overlays -->
            <div
              v-for="(txt, tIdx) in panel.texts"
              :key="'text-' + tIdx"
              :class="[
                'absolute select-none font-comic pointer-events-none',
                txt.style === 'speech' ? 'bubble-speech rounded-2xl border-2 border-black bg-white/95 px-3 py-2 text-black shadow-lg' :
                txt.style === 'label'  ? 'bubble-label rounded-full border-2 border-white bg-transparent px-3 py-1 text-white' :
                txt.style === 'box'    ? 'bubble-box rounded-sm border-2 border-black bg-white px-3 py-2 text-black shadow' :
                'bubble-outline text-white'
              ]"
              :style="{
                left: (txt.x ?? 10) + '%',
                top: (txt.y ?? 10) + '%',
                fontSize: ((txt.size ?? 18)) + 'px',
                transform: 'translate(-50%, -50%)'
              }"
            >
              {{ txt.value || 'Text' }}
            </div>
          </div>
        </div>

        <!-- End Message -->
        <div class="text-center py-12">
          <div class="inline-block bg-gradient-to-r from-purple-600/20 via-pink-600/20 to-red-600/20 border border-purple-500/30 rounded-xl px-8 py-4">
            <p class="text-gray-400 text-lg font-semibold">— End of Comic —</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { GetFromApi } from '@/api';

const route = useRoute();
const comic = ref({});
const loading = ref(true);
const error = ref('');

onMounted(async () => {
  const comicId = route.params.id;
  
  try {
    const response = await GetFromApi(`comics/${comicId}`);
    comic.value = response;
  } catch (e) {
    error.value = 'Failed to load comic.';
    console.error('Error loading comic:', e);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
/* Comic font styling */
.font-comic {
  font-family: 'Comic Sans MS', 'Marker Felt', 'Comic Neue', cursive;
  font-weight: bold;
  line-height: 1.2;
  text-align: center;
}

/* Speech bubble */
.bubble-speech {
  text-shadow: none;
}

.bubble-speech::before {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 20%;
  width: 0;
  height: 0;
  border-left: 10px solid transparent;
  border-right: 10px solid transparent;
  border-top: 10px solid black;
  transform: translateX(-50%);
}

.bubble-speech::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 20%;
  width: 0;
  height: 0;
  border-left: 9px solid transparent;
  border-right: 9px solid transparent;
  border-top: 9px solid white;
  transform: translateX(-50%);
}

/* Label (transparent with outline) */
.bubble-label {
  text-shadow: 
    -1px -1px 0 rgba(0, 0, 0, 0.8),
    1px -1px 0 rgba(0, 0, 0, 0.8),
    -1px 1px 0 rgba(0, 0, 0, 0.8),
    1px 1px 0 rgba(0, 0, 0, 0.8);
}

/* Box (simple white box) */
.bubble-box {
  text-shadow: none;
}

/* Outline text */
.bubble-outline {
  text-shadow:
    -2px -2px 0 #000,
    2px -2px 0 #000,
    -2px 2px 0 #000,
    2px 2px 0 #000,
    -2px 0 0 #000,
    2px 0 0 #000,
    0 -2px 0 #000,
    0 2px 0 #000;
}
</style>
