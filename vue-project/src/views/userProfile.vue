<template>
  <div class="min-h-screen bg-[#0D0D12] text-[#FAF8F5] font-sans selection:bg-[#C9A84C]/30 relative overflow-hidden">
    <!-- Noise overlay -->
    <svg class="pointer-events-none fixed inset-0 z-50 h-full w-full opacity-5" xmlns="http://www.w3.org/2000/svg">
      <filter id="noise">
        <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch" />
      </filter>
      <rect width="100%" height="100%" filter="url(#noise)" />
    </svg>

    <div v-if="userInfo" class="max-w-4xl mx-auto pt-32 pb-16 px-6 relative z-10">

      <!-- Profile Header -->
      <div class="flex flex-col md:flex-row items-center md:items-start gap-10">
        <!-- Profile Icon -->
        <div class="relative group cursor-pointer">
          <div
            class="absolute inset-0 bg-[#C9A84C] rounded-[2rem] blur-xl opacity-20 group-hover:opacity-40 transition-opacity duration-700">
          </div>
          <div
            class="w-40 h-40 rounded-[2rem] border border-[#2A2A35] bg-[#0D0D12] flex items-center justify-center text-5xl overflow-hidden relative z-10 transition-transform duration-500 hover:scale-[1.03]"
            style="transition-timing-function: cubic-bezier(0.25, 0.46, 0.45, 0.94);">
            <template v-if="true">
              <img :src="apiUrl + '/random-image-file?user=' + userInfo.username" alt="Profile Icon"
                class="w-full h-full object-cover  opacity-80 " />
            </template>
            <template v-else>
              <span class="font-serif italic text-[#C9A84C]">{{ userInfo.username?.charAt(0) || '?' }}</span>
            </template>
          </div>
        </div>

        <!-- Info -->
        <div class="flex flex-col flex-1 text-center md:text-left mt-4 md:mt-0">
          <h1 class="text-4xl md:text-5xl font-serif italic text-[#FAF8F5] mb-4 font-light tracking-tight">
            {{ userInfo.username }}
          </h1>
          <div class="flex items-center justify-center md:justify-start gap-4 mb-10">

          </div>

          <!-- Personality / Bio -->
          <div
            class="bg-[#0D0D12] rounded-[2rem] p-8 border border-[#2A2A35] relative overflow-hidden shadow-2xl group hover:border-[#C9A84C]/30 transition-colors duration-500">
            <div
              class="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-[#C9A84C]/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700">
            </div>
            <h3 class="font-sans text-[10px] uppercase tracking-[0.3em] text-[#FAF8F5]/40 mb-4">Bio
            </h3>
            <p class="font-sans text-lg text-[#FAF8F5]/80 leading-relaxed font-light">
              {{ userInfo.bio || 'No data provided.' }}
            </p>
            <h3 class="font-sans text-[10px] uppercase tracking-[0.3em] text-[#FAF8F5]/40 mb-4 mt-6">Personality

            </h3>
            <p class="font-sans text-lg text-[#FAF8F5]/80 leading-relaxed font-light">
              {{ userInfo.personality || 'No data provided.' }}
            </p>
          </div>
        </div>
      </div>
      <!-- Recent Activity / Comments -->
      <div v-if="userInfo.comments && userInfo.comments.length > 0" class="mt-16">
        <h2 class="font-sans text-[10px] uppercase tracking-[0.3em] text-[#FAF8F5]/40 mb-8">
          Recent Activity
        </h2>

        <div class="space-y-4">
          <div
            v-for="(entry, idx) in userInfo.comments"
            :key="idx"
            class="comment-card bg-[#0D0D12] rounded-2xl border border-[#2A2A35] p-5 flex gap-5 items-start group hover:border-[#C9A84C]/30 transition-all duration-500 relative overflow-hidden"
          >
            <!-- Top gold line on hover -->
            <div
              class="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-[#C9A84C]/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700"
            ></div>

            <!-- Image Thumbnail -->
            <router-link
              :to="'/image/' + entry.image_id"
              class="shrink-0"
            >
              <img
                :src="apiUrl + '/image-file/' + entry.image_id"
                alt="Image thumbnail"
                class="w-40 h-40 rounded-2xl object-cover border border-[#2A2A35] group-hover:border-[#C9A84C]/20 transition-all duration-500 opacity-80 group-hover:opacity-100"
              />
            </router-link>

            <!-- Comment Body -->
            <div class="flex-1 min-w-0">
              <!-- Badge: Comment vs Reply -->
              <span
                class="inline-block font-mono text-[10px] uppercase tracking-widest px-2 py-0.5 rounded-md mb-2"
                :class="entry.comment
                  ? 'bg-[#C9A84C]/10 text-[#C9A84C]'
                  : 'bg-[#FAF8F5]/5 text-[#FAF8F5]/40'"
              >
                {{ entry.comment ? 'Comment' : 'Reply' }}
              </span>

              <!-- Content -->
              <p class="font-sans text-sm text-[#FAF8F5]/75 leading-relaxed font-light truncate-multiline">
                {{ (entry.comment || entry.reply)?.content || '' }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else-if="userInfo.comments && userInfo.comments.length === 0" class="mt-16 text-center">
        <p class="font-mono text-xs uppercase tracking-widest text-[#FAF8F5]/20">
          No activity yet.
        </p>
      </div>
    </div>

    <div v-else
      class="min-h-screen flex items-center justify-center font-mono text-[#C9A84C] text-sm tracking-widest uppercase animate-pulse">
      Retrieving dossier...
    </div>
  </div>
</template>


<script setup>
import { apiUrl, GetFromApi } from '@/api';
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

const userInfo = ref({
  username: "",
  personality: "...."
});

onMounted(() => {
  getUserInfo();
});

async function getUserInfo() {
  try {
    const data = await GetFromApi(`users/${route.params.username}`);
    if (data) {
      userInfo.value = data;
    }
  } catch (e) {
    console.error("Failed to fetch user, using fallback data.");
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&family=JetBrains+Mono:wght@400&family=Playfair+Display:ital,wght@1,400;1,600&display=swap');

.font-sans {
  font-family: 'Inter', sans-serif;
}

.font-serif {
  font-family: 'Playfair Display', serif;
}

.font-mono {
  font-family: 'JetBrains Mono', monospace;
}
</style>