<template>
    <div class="bg-panel/95 backdrop-blur-2xl rounded-2xl shadow-[0_8px_30px_rgba(0,0,0,0.5)] border border-slate py-3 w-80 max-h-96 overflow-y-auto z-50 text-ivory">
        <p class="px-4 pb-2 text-center text-xs font-semibold uppercase tracking-wider text-ivory/60 font-sans">Save to Board</p>

        <div class="px-3 pb-2">
            <input ref="searchInput" v-model="search" type="text" placeholder="Search boards…"
                class="w-full px-3.5 py-2 bg-dark-input text-ivory placeholder-ivory/40 border border-slate rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-champagne focus:border-champagne transition-colors font-sans" />
        </div>

        <div v-for="(board, index) in filteredBoards" :key="board.id"
            class="px-3 py-2.5 mx-1 cursor-pointer flex items-center gap-3 transition-colors rounded-xl hover:bg-slate/60 group"
            @click="emit('save-to', board.id)">
            <img v-if="board.cover_image" :src="ImageSrc(board.cover_image)" alt="Board cover"
                class="w-11 h-11 rounded-lg object-cover bg-obsidian border border-slate/40 flex-shrink-0" />
            <div class="min-w-0 flex-1">
                <div class="flex items-center gap-1.5">
                    <div class="text-ivory font-medium text-sm truncate group-hover:text-champagne transition-colors">{{ board.name }}</div>
                    <div class="text-ivory/40 text-xs font-mono">({{ Math.round(board.pin_count) }})</div>
                </div>
                <div class="flex items-center gap-2 mt-0.5">
                    <div class="flex items-center gap-1">
                        <Star class="w-3 h-3 text-champagne fill-champagne/30" />
                        <span class="text-ivory/50 text-xs font-mono">{{ board.recommendation_score ? board.recommendation_score.toFixed(1) : '0.0' }}</span>
                    </div>
                    <div class="flex items-center gap-1">
                        <Tag class="w-3 h-3 text-ivory/40" />
                        <span class="text-ivory/50 text-xs font-mono">{{ board.tag_count ?? 0 }}</span>
                    </div>
                </div>
            </div>
            <button
                class="magnetic-button bg-champagne text-obsidian px-3 py-1 rounded-full hover:brightness-110 font-sans font-semibold text-xs hidden group-hover:flex items-center ml-auto transition-all shadow-md flex-shrink-0"
                @click.stop="emit('save-to', board.id)">
                Save
            </button>
        </div>

        <div v-if="filteredBoards.length === 0" class="px-4 py-4 text-center text-xs text-ivory/40 font-sans">
            No boards found
        </div>
    </div>
</template>

<script setup>
import { ImageSrc } from '@/api';
import { Star, Tag } from 'lucide-vue-next';
import { ref, onMounted, computed } from 'vue';

const searchInput = ref(null);
const emit = defineEmits(['save-to', 'change-board']);
const props = defineProps({
    pin: Object
})
const search = ref('');

// Computed property to filter boards based on search
const filteredBoards = computed(() => {
    return (props.pin?.recommended_boards || []).filter(board =>
        board.name.toLowerCase().includes(search.value.toLowerCase())
    );
});

onMounted(() => {
    if (searchInput.value) {
        searchInput.value.focus();
    }
});
</script>