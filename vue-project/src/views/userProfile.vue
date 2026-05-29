<template>
  <div class="min-h-screen bg-[#0D0D12] text-[#FAF8F5] font-sans selection:bg-[#C9A84C]/30 relative overflow-hidden">
    <!-- Noise overlay -->
    <svg class="pointer-events-none fixed inset-0 z-50 h-full w-full opacity-5" xmlns="http://www.w3.org/2000/svg">
      <filter id="noise">
        <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch" />
      </filter>
      <rect width="100%" height="100%" filter="url(#noise)" />
    </svg>

    <!-- Loading State -->
    <div v-if="!character"
      class="min-h-screen flex items-center justify-center font-mono text-[#C9A84C] text-sm tracking-widest uppercase animate-pulse">
      Retrieving dossier…
    </div>

    <div v-else class="max-w-4xl mx-auto pt-16 pb-16 px-6 relative z-10">

      <!-- Profile Header -->
      <div class="bg-[#14141A] rounded-2xl border border-[#2A2A35] p-8 relative shadow-xl overflow-hidden">
        <div
          class="absolute top-0 right-0 w-80 h-80 bg-gradient-to-br from-[#C9A84C]/10 to-transparent rounded-full blur-3xl -mr-40 -mt-40">
        </div>

        <div class="flex flex-col gap-6 relative z-10">
          <div class="flex justify-between items-start">
            <div class="flex gap-6 items-center">
              <div class="relative group">
                <div
                  class="absolute inset-0 bg-[#C9A84C] rounded-full blur-xl opacity-20 group-hover:opacity-40 transition-opacity duration-700">
                </div>
                <img
                  :src="character.avatar || 'https://images.unsplash.com/photo-1511275539165-cc46b1ee89bf?w=150&h=150&fit=crop'"
                  class="w-32 h-32 rounded-full object-cover shadow-[0_0_20px_rgba(0,0,0,0.5)] border-2 border-[#2A2A35] relative z-10 transition-transform duration-500 hover:scale-[1.03]" />
              </div>
              <div>
                <h1 class="text-4xl font-bold font-sans tracking-tight text-[#FAF8F5]">{{ character.name }}</h1>
                <p class="text-[#C9A84C] font-mono text-sm mt-1">@{{ character.id }}</p>
                <div class="flex gap-4 mt-3">
                  <div class="text-center">
                    <span class="text-lg font-bold text-[#FAF8F5]">{{ character.posts?.length || 0 }}</span>
                    <span class="text-[#FAF8F5]/40 text-xs block font-mono uppercase tracking-widest">posts</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="flex gap-3">
              <router-link :to="'/chat/' + character.id"
                class="px-5 py-2.5 bg-[#C9A84C] text-[#0D0D12] rounded-full font-bold font-sans text-sm shadow-[0_0_15px_rgba(201,168,76,0.3)] hover:shadow-[0_0_25px_rgba(201,168,76,0.4)] transition-all">
                Message
              </router-link>
            </div>
          </div>

          <div class="bg-[#0D0D12]/50 rounded-xl border border-[#2A2A35]/50 overflow-hidden">
            <button @click="descExpanded = !descExpanded"
              class="w-full flex items-center justify-between px-6 py-4 hover:bg-[#FAF8F5]/[0.02] transition-colors group">
              <h3 class="text-xs font-mono text-[#FAF8F5]/40 uppercase tracking-widest">Description</h3>
              <svg class="w-4 h-4 text-[#FAF8F5]/30 group-hover:text-[#C9A84C] transition-all duration-300"
                :class="descExpanded ? 'rotate-180' : 'rotate-0'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            <div class="overflow-hidden transition-all duration-500 ease-in-out"
              :style="descExpanded ? 'max-height: 2000px; opacity: 1' : 'max-height: 5rem; opacity: 0.7'">
              <div class="px-6 pb-6 prose prose-invert prose-sm max-w-none text-[#FAF8F5]/80 leading-relaxed"
                v-html="parsedDescription" />
            </div>
            <div v-if="!descExpanded && parsedDescription.length > 300" class="px-6 pb-3 pointer-events-none">
            </div>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="flex mt-8 border-b border-[#2A2A35]">
        <button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id"
          class="px-6 py-3 text-sm font-sans font-semibold transition-all duration-300 relative" :class="activeTab === tab.id
            ? 'text-[#C9A84C]'
            : 'text-[#FAF8F5]/40 hover:text-[#FAF8F5]/70'">
          {{ tab.label }}
          <span v-if="tab.count !== undefined" class="ml-2 text-xs font-mono px-1.5 py-0.5 rounded-full"
            :class="activeTab === tab.id ? 'bg-[#C9A84C]/20 text-[#C9A84C]' : 'bg-[#2A2A35] text-[#FAF8F5]/30'">
            {{ tab.count }}
          </span>
          <div v-if="activeTab === tab.id" class="absolute bottom-0 left-0 right-0 h-[2px] bg-[#C9A84C] rounded-full">
          </div>
        </button>
      </div>

      <!-- Posts Tab -->
      <div v-if="activeTab === 'posts'" class="space-y-6 mt-6">
        <div v-for="(post, index) in character.posts" :key="post.created_at || index"
          class="bg-[#14141A] rounded-2xl border border-[#2A2A35] overflow-hidden shadow-lg transition-transform duration-300 hover:-translate-y-1 hover:shadow-xl hover:border-[#2A2A35]/80">
          <div class="p-6 flex gap-4">
            <img
              :src="character.avatar || 'https://images.unsplash.com/photo-1511275539165-cc46b1ee89bf?w=100&h=100&fit=crop'"
              class="w-12 h-12 rounded-full object-cover shadow-sm border border-[#2A2A35]" />
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-2">
                <span class="font-bold font-sans text-[#FAF8F5]">{{ character.name }}</span>
                <span class="text-[#FAF8F5]/40 font-mono text-sm">@{{ character.id }}</span>
                <span v-if="post.created_at" class="text-[#FAF8F5]/30 font-mono text-xs ml-auto">
                  {{ formatTime(post.created_at) }}
                </span>
              </div>
              <p class="text-[#FAF8F5]/90 font-sans leading-relaxed text-[15px] mb-4 whitespace-pre-wrap">
                {{ post.title }}
              </p>

              <div v-if="post.image_url" class="rounded-xl border border-[#2A2A35] overflow-hidden bg-[#0D0D12]">
                <img :src="apiUrl + post.image_url" class="w-full h-auto object-cover" />
              </div>
              <div v-else class="rounded-xl border border-[#2A2A35] bg-[#0D0D12] p-6 text-center">
                <span class="text-[#FAF8F5]/30 font-mono text-xs uppercase tracking-widest">No image generated</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="!character.posts?.length" class="py-24 text-center">
          <p class="text-[#FAF8F5]/30 font-mono text-sm">No posts yet.</p>
        </div>
      </div>

      <!-- Comments Tab -->
      <div v-if="activeTab === 'comments'" class="space-y-4 mt-6">
        <div v-for="(entry, idx) in characterComments" :key="idx"
          class="bg-[#14141A] rounded-2xl border border-[#2A2A35] p-5 flex gap-5 items-start group hover:border-[#C9A84C]/30 transition-all duration-500 relative overflow-hidden">
          <div
            class="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-[#C9A84C]/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700">
          </div>

          <!-- Image Thumbnail -->
          <router-link :to="'/image/' + entry.image_id" class="shrink-0" v-if="entry.image_id">
            <img :src="apiUrl + '/image-file/' + entry.image_id" alt="Image thumbnail"
              class="w-40 h-40 rounded-2xl object-cover border border-[#2A2A35] group-hover:border-[#C9A84C]/20 transition-all duration-500 opacity-80 group-hover:opacity-100" />
          </router-link>

          <!-- Comment Body -->
          <div class="flex-1 min-w-0">
            <span class="inline-block font-mono text-[10px] uppercase tracking-widest px-2 py-0.5 rounded-md mb-2"
              :class="entry.comment
                ? 'bg-[#C9A84C]/10 text-[#C9A84C]'
                : 'bg-[#FAF8F5]/5 text-[#FAF8F5]/40'">
              {{ entry.comment ? 'Comment' : 'Reply' }}
            </span>
            <p class="font-sans text-sm text-[#FAF8F5]/75 leading-relaxed font-light">
              {{ (entry.comment || entry.reply)?.content || '' }}
            </p>
          </div>
        </div>

        <div v-if="!characterComments.length" class="py-24 text-center">
          <p class="text-[#FAF8F5]/30 font-mono text-sm">No comments yet.</p>
        </div>
      </div>

      <!-- Media Tab -->
      <div v-if="activeTab === 'media'" class="mt-6">
        <div class="py-24 text-center">
          <svg class="mx-auto w-16 h-16 text-[#2A2A35] mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1"
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p class="text-[#FAF8F5]/30 font-mono text-sm uppercase tracking-widest">Media gallery coming soon</p>
          <p class="text-[#FAF8F5]/20 font-sans text-xs mt-2">This tab is reserved for future media content.</p>
        </div>
      </div>

    </div>
  </div>
</template>


<script setup>
import { apiUrl, GetFromApi } from '@/api';
import { onMounted, ref, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { marked } from 'marked';

// Configure marked for safe, clean rendering
marked.setOptions({ breaks: true, gfm: true });

const route = useRoute();

const character = ref(null);
const characterComments = ref([]);
const descExpanded = ref(false);

const parsedDescription = computed(() => {
  const raw = character.value?.description || 'A figure shrouded in mystery.'
  return marked.parse(raw)
})


const activeTab = ref('posts');

const tabs = computed(() => [
  { id: 'posts', label: 'Posts', count: character.value?.posts?.length || 0 },
  { id: 'comments', label: 'Comments', count: characterComments.value.length },
  { id: 'media', label: 'Media' },
]);

function formatTime(timestamp) {
  if (!timestamp) return '';
  const d = new Date(timestamp * 1000);
  const now = new Date();
  const diff = (now - d) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
  if (diff < 604800) return Math.floor(diff / 86400) + 'd ago';
  return d.toLocaleDateString();
}

async function loadCharacter() {
  try {
    const charId = route.params.username;
    const data = await GetFromApi(`characters/${charId}`);
    if (data) {
      character.value = data;
    }
  } catch (e) {
    console.error("Failed to fetch character:", e);
  }
}

async function loadCharacterComments() {
  try {
    const charId = route.params.username;
    // Try to load comments where this character is involved
    const data = await GetFromApi(`users/${charId}/comments`);
    if (data && Array.isArray(data)) {
      characterComments.value = data;
    }
  } catch (e) {
    // Character may not have old-style comments - that's ok
    characterComments.value = [];
  }
}

onMounted(() => {
  loadCharacter();
  loadCharacterComments();
});

watch(() => route.params.username, () => {
  loadCharacter();
  loadCharacterComments();
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400&family=Playfair+Display:ital,wght@1,400;1,600&display=swap');

.font-sans {
  font-family: 'Inter', sans-serif;
}

.font-serif {
  font-family: 'Playfair Display', serif;
}

.font-mono {
  font-family: 'JetBrains Mono', monospace;
}

/* Markdown prose styles */
.prose :deep(h1),
.prose :deep(h2),
.prose :deep(h3),
.prose :deep(h4) {
  color: #FAF8F5;
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  margin-top: 1.2em;
  margin-bottom: 0.4em;
}

.prose :deep(h1) {
  font-size: 1.25rem;
}

.prose :deep(h2) {
  font-size: 1.1rem;
  color: #C9A84C;
}

.prose :deep(h3) {
  font-size: 0.95rem;
  color: #FAF8F5cc;
}

.prose :deep(p) {
  margin-bottom: 0.75em;
  line-height: 1.7;
  color: rgba(250, 248, 245, 0.8);
}

.prose :deep(strong) {
  color: #FAF8F5;
  font-weight: 600;
}

.prose :deep(em) {
  color: #C9A84C;
  font-style: italic;
}

.prose :deep(ul),
.prose :deep(ol) {
  margin: 0.5em 0 0.75em 1.25em;
  color: rgba(250, 248, 245, 0.75);
}

.prose :deep(li) {
  margin-bottom: 0.25em;
  line-height: 1.6;
}

.prose :deep(ul li::marker) {
  color: #C9A84C;
}

.prose :deep(code) {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.82em;
  background: rgba(201, 168, 76, 0.1);
  color: #C9A84C;
  padding: 0.1em 0.4em;
  border-radius: 4px;
}

.prose :deep(pre) {
  background: #0A0A10;
  border: 1px solid #2A2A35;
  border-radius: 0.75rem;
  padding: 1em;
  overflow-x: auto;
  margin: 0.75em 0;
}

.prose :deep(pre code) {
  background: none;
  color: #FAF8F5cc;
  padding: 0;
}

.prose :deep(blockquote) {
  border-left: 2px solid #C9A84C;
  padding-left: 1em;
  color: rgba(250, 248, 245, 0.5);
  font-style: italic;
  margin: 0.75em 0;
}

.prose :deep(hr) {
  border-color: #2A2A35;
  margin: 1em 0;
}

.prose :deep(a) {
  color: #C9A84C;
  text-decoration: underline;
  text-underline-offset: 3px;
}
</style>