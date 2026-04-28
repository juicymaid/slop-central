<template>
  <div class="relative flex flex-col overflow-hidden bg-gradient-to-b from-slate-900 to-slate-800 text-slate-200"
    :style="{ height: availableHeight + 'px' }">
    <div class="flex flex-1 items-end justify-center px-[2vw] pt-[2vh]">
      <img class="max-h-[65vh] w-auto object-contain drop-shadow-xl select-none pointer-events-none" :src="charSrc"
        alt="Character portrait" draggable="false" />
    </div>

    <div class="mt-auto px-4 pb-4 pt-0" @click="next" title="Click to continue">
      <div class="mx-auto max-w-3xl rounded-xl border border-slate-400/20 bg-slate-900/60 p-4 backdrop-blur shadow-xl">
        <div class="mb-1 font-bold text-sky-300">{{ speaker }}</div>
        <div class="min-h-[3.2em] leading-relaxed text-slate-200" aria-live="polite">{{ line }}</div>
        <div class="mt-2 flex justify-end">
          <button class="rounded-md bg-blue-500 px-3 py-2 font-semibold text-white hover:bg-blue-600"
            @click.stop="next">
            Next ▶
          </button>
        </div>
      </div>
      <div
        class="mx-auto max-w-3xl rounded-xl border border-slate-400/20 bg-slate-900/60 p-4 backdrop-blur shadow-xl"
        @click.stop
      >
        <input
          id="vn-input"
          type="text"
          placeholder="Type here..."
          class="w-full rounded-md border border-slate-500/40 bg-slate-800/70 px-3 py-2 text-slate-100 placeholder-slate-400 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/40"
          @keydown.stop
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';

const charSrc = '/char.png';
const speaker = ref('Aiko');
const lines = [
  'Welcome to the visual novel layout.',
  'This shows a character portrait and a dialogue box.',
  'Click or press Space/Enter to advance.'
];
const index = ref(0);
const line = computed(() => lines[index.value]);

function next() {
  index.value = (index.value + 1) % lines.length;
}

function onKey(e) {
  if (e.key === ' ' || e.key === 'Enter') {
    e.preventDefault();
    next();
  }
}

// Dynamically fit height to viewport minus app header
const availableHeight = ref(0);
function computeAvailableHeight() {
  const headerEl = document.querySelector('header, [role="banner"], [data-app-header], .app-header');
  const headerH = headerEl ? headerEl.getBoundingClientRect().height : 0;
  availableHeight.value = Math.max(320, window.innerHeight - headerH);
}

onMounted(() => {
  computeAvailableHeight();
  window.addEventListener('resize', computeAvailableHeight);
  window.addEventListener('orientationchange', computeAvailableHeight);
  window.addEventListener('keydown', onKey);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', computeAvailableHeight);
  window.removeEventListener('orientationchange', computeAvailableHeight);
  window.removeEventListener('keydown', onKey);
});
</script>
