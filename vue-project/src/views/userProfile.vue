<template>
  <div class="min-h-screen  text-[#FAF8F5] font-sans selection:bg-[#C9A84C]/30 relative overflow-hidden">
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

              <div v-if="post.image_url" class="rounded-xl border border-[#2A2A35] overflow-hidden bg-[#0D0D12] relative group/postimg">
                <router-link v-if="post.image_id" :to="'/image/' + post.image_id" class="block relative group/link">
                  <img :src="apiUrl + post.image_url" class="w-full h-auto object-cover transition-transform duration-500 group-hover/postimg:scale-[1.01]" />
                  <div class="absolute inset-0 bg-[#0D0D12]/40 opacity-0 group-hover/postimg:opacity-100 transition-opacity flex items-center justify-center">
                    <span class="px-4 py-2 bg-[#C9A84C] text-[#0D0D12] rounded-full font-bold text-xs font-sans shadow-lg flex items-center gap-1.5 transform translate-y-2 group-hover/postimg:translate-y-0 transition-transform">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                      View Image #{{ post.image_id }}
                    </span>
                  </div>
                </router-link>
                <img v-else :src="apiUrl + post.image_url" class="w-full h-auto object-cover" />
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
      <div v-if="activeTab === 'media'" class="mt-6 space-y-6">
        <!-- Media Tags Bar & Settings -->
        <div class="bg-[#14141A] rounded-2xl border border-[#2A2A35] p-5 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1.5">
              <span class="text-xs font-mono uppercase tracking-widest text-[#C9A84C] font-semibold">Media Query Tags</span>
              <span class="text-xs font-mono text-[#FAF8F5]/40">({{ characterMedia.length }} matched images)</span>
            </div>
            
            <div v-if="!editingTags" class="flex items-center gap-2 flex-wrap">
              <span v-for="tag in currentTagsList" :key="tag"
                class="px-2.5 py-1 bg-[#0D0D12] text-[#FAF8F5]/80 border border-[#2A2A35] rounded-lg text-xs font-mono">
                {{ tag }}
              </span>
              <span v-if="!currentTagsList.length" class="text-xs text-[#FAF8F5]/30 font-mono italic">
                No tags configured (defaulting to prompt prefix / name)
              </span>
            </div>
            
            <div v-else class="flex gap-2 mt-2">
              <input v-model="tagsInput" type="text" placeholder="e.g. tohru, maid, dragon maid, blonde hair"
                class="flex-1 bg-[#0D0D12] text-[#FAF8F5] text-xs font-mono border border-[#2A2A35] rounded-xl px-3.5 py-2 focus:outline-none focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C]"
                @keydown.enter="saveTags" />
              <button @click="saveTags" :disabled="savingTags"
                class="px-4 py-2 bg-[#C9A84C] text-[#0D0D12] font-sans font-bold text-xs rounded-xl hover:brightness-110 transition-all disabled:opacity-50">
                {{ savingTags ? 'Saving…' : 'Save' }}
              </button>
              <button @click="cancelEditTags"
                class="px-3 py-2 bg-[#2A2A35] text-[#FAF8F5]/70 font-sans text-xs rounded-xl hover:bg-[#353545] transition-all">
                Cancel
              </button>
            </div>
          </div>

          <div v-if="!editingTags" class="shrink-0 flex items-center gap-2">
            <button @click="startEditTags"
              class="px-4 py-2 bg-[#2A2A35]/80 hover:bg-[#2A2A35] text-[#FAF8F5] border border-[#2A2A35] rounded-xl text-xs font-sans font-semibold transition-all flex items-center gap-1.5">
              <svg class="w-3.5 h-3.5 text-[#C9A84C]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Edit Tags
            </button>
            <button @click="loadCharacterMedia"
              class="p-2 bg-[#2A2A35]/60 hover:bg-[#2A2A35] text-[#FAF8F5]/60 hover:text-[#FAF8F5] rounded-xl transition-all" title="Refresh media">
              <svg class="w-4 h-4" :class="{ 'animate-spin': mediaLoading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="mediaLoading" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          <div v-for="n in 8" :key="n" class="aspect-[3/4] rounded-2xl bg-[#14141A] border border-[#2A2A35] animate-pulse"></div>
        </div>

        <!-- Media Grid -->
        <div v-else-if="characterMedia.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          <div v-for="img in characterMedia" :key="img.Id"
            class="group/card relative rounded-2xl overflow-hidden bg-[#14141A] border border-[#2A2A35] hover:border-[#C9A84C]/40 transition-all duration-300 shadow-md hover:shadow-xl aspect-[3/4]">
            <router-link :to="'/image/' + img.Id" class="block w-full h-full">
              <img :src="ImageSrc(img.Path)"
                class="w-full h-full object-cover transition-transform duration-500 group-hover/card:scale-105"
                loading="lazy" />
              
              <!-- Card Hover Overlay -->
              <div class="absolute inset-0 bg-gradient-to-t from-[#0D0D12]/90 via-[#0D0D12]/20 to-transparent opacity-0 group-hover/card:opacity-100 transition-opacity p-3 flex flex-col justify-between">
                <!-- Top Badge if linked to post -->
                <div class="flex justify-between items-center">
                  <span v-if="img.post_info"
                    class="px-2 py-0.5 bg-[#C9A84C] text-[#0D0D12] text-[10px] font-mono uppercase tracking-wider font-bold rounded-full shadow">
                    Post
                  </span>
                  <span v-else></span>

                  <span v-if="img.Rating" class="px-2 py-0.5 bg-[#0D0D12]/80 backdrop-blur-sm text-yellow-400 text-xs font-mono rounded-full border border-[#2A2A35]">
                    ★ {{ img.Rating.toFixed(0) }}
                  </span>
                </div>

                <!-- Bottom info -->
                <div class="min-w-0">
                  <p class="text-xs font-sans text-[#FAF8F5] line-clamp-2 leading-tight drop-shadow">
                    {{ img.Prompt || img.taggerPrompt || 'No prompt' }}
                  </p>
                  <p class="text-[10px] font-mono text-[#FAF8F5]/40 mt-1">#{{ img.Id }}</p>
                </div>
              </div>
            </router-link>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="py-24 text-center bg-[#14141A]/50 rounded-2xl border border-[#2A2A35]">
          <svg class="mx-auto w-16 h-16 text-[#2A2A35] mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1"
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p class="text-[#FAF8F5]/40 font-mono text-sm uppercase tracking-widest">No matching media found</p>
          <p class="text-[#FAF8F5]/20 font-sans text-xs mt-2">Try editing the media query tags above to match images of this character.</p>
        </div>
      </div>

    </div>
  </div>
</template>


<script setup>
import { apiUrl, GetFromApi, ImageSrc } from '@/api';
import { onMounted, ref, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { marked } from 'marked';

// Configure marked for safe, clean rendering
marked.setOptions({ breaks: true, gfm: true });

const route = useRoute();

const character = ref(null);
const characterComments = ref([]);
const characterMedia = ref([]);
const mediaLoading = ref(false);
const editingTags = ref(false);
const tagsInput = ref('');
const savingTags = ref(false);
const descExpanded = ref(false);

const parsedDescription = computed(() => {
  const raw = character.value?.description || 'A figure shrouded in mystery.'
  return marked.parse(raw)
})

const activeTab = ref('posts');

const tabs = computed(() => [
  { id: 'posts', label: 'Posts', count: character.value?.posts?.length || 0 },
  { id: 'comments', label: 'Comments', count: characterComments.value.length },
  { id: 'media', label: 'Media', count: characterMedia.value.length },
]);

const currentTagsList = computed(() => {
  const raw = (character.value?.tags || '').trim();
  if (raw) {
    return raw.split(',').map(t => t.trim()).filter(Boolean);
  }
  const fallback = (character.value?.prompt_prefix || character.value?.name || '').trim();
  return fallback ? fallback.split(',').map(t => t.trim()).filter(Boolean) : [];
});

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

function startEditTags() {
  tagsInput.value = character.value?.tags || character.value?.prompt_prefix || '';
  editingTags.value = true;
}

function cancelEditTags() {
  editingTags.value = false;
  tagsInput.value = '';
}

async function saveTags() {
  if (!character.value?.id) return;
  savingTags.value = true;
  try {
    const res = await fetch(`${apiUrl}/characters/${character.value.id}/tags`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tags: tagsInput.value.trim() })
    });
    if (res.ok) {
      const updated = await res.json();
      character.value.tags = updated.tags;
      editingTags.value = false;
      await loadCharacterMedia();
    }
  } catch (e) {
    console.error("Failed to update character tags:", e);
  } finally {
    savingTags.value = false;
  }
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
    const data = await GetFromApi(`users/${charId}/comments`);
    if (data && Array.isArray(data)) {
      characterComments.value = data;
    }
  } catch (e) {
    characterComments.value = [];
  }
}

async function loadCharacterMedia() {
  const charId = route.params.username;
  if (!charId) return;
  mediaLoading.value = true;
  try {
    const data = await GetFromApi(`characters/${charId}/media?per_page=60`);
    if (data && Array.isArray(data.images)) {
      characterMedia.value = data.images;
    } else if (Array.isArray(data)) {
      characterMedia.value = data;
    } else {
      characterMedia.value = [];
    }
  } catch (e) {
    console.error("Failed to fetch character media:", e);
    characterMedia.value = [];
  } finally {
    mediaLoading.value = false;
  }
}

onMounted(() => {
  loadCharacter();
  loadCharacterComments();
  loadCharacterMedia();
});

watch(() => route.params.username, () => {
  loadCharacter();
  loadCharacterComments();
  loadCharacterMedia();
});

watch(activeTab, (newTab) => {
  if (newTab === 'media' && characterMedia.value.length === 0) {
    loadCharacterMedia();
  }
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