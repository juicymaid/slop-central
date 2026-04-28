<template>
    <div class="bg-white rounded-lg shadow-lg border border-gray-100 py-2 w-80 overflow-y-auto z-40 text-black">
        <p class="px-4 py-2 text-center">Save</p>

        <div class="px-4 py-2">
            <input ref="searchInput" v-model="search" type="text" placeholder="Search boards…"
                class="w-full px-3 py-2 border border-gray-300 rounded-xl focus:outline-none" />
        </div>

        <div v-for="(board, index) in filteredBoards" :key="board.id"
            class="px-4 py-3 cursor-pointer flex items-center gap-3 transition-colors rounded-lg hover:bg-gray-100 group"
            @click="emit('save-to', board.id)">
            <img v-if="board.cover_image" :src="ImageSrc(board.cover_image)" alt="Board cover"
                class="w-12 h-12 rounded-lg object-cover" />
            <div>
                <div class="flex">
                    <div class="text-gray-700">{{ board.name }}</div>
                    <div class="text-gray-400 text-sm mt-0.5 ml-0.5">{{ Math.round(board.pin_count) }}</div>
                </div>
                <div class="flex items-center">
                    <Star class="w-3 h-3 text-yellow-500" />
                    <div class="text-gray-500 text-xs">{{ board.recommendation_score.toFixed(1) }}</div>
                    <Tag class="w-3 h-3 text-gray-500 ml-2" />
                    <div class="text-gray-500 text-xs">{{ board.tag_count }}</div>
                </div>
            </div>
            <button
                class="bg-red-600 text-white px-2 py-1 rounded-full hover:bg-red-700 hidden group-hover:block ml-auto">
                Save
            </button>
        </div>
    </div>
</template>

<script setup>
import { ImageSrc } from '@/api';
import { Star, Tag } from 'lucide-vue-next';
import { ref, onMounted, computed } from 'vue';

const searchInput = ref(null);
const emit = defineEmits(['change-board'])
const props = defineProps({
    pin: Object
})
const search = ref('');

// Computed property to filter boards based on search
const filteredBoards = computed(() => {
    return props.pin.recommended_boards.filter(board =>
        board.name.toLowerCase().includes(search.value.toLowerCase())
    );
});

onMounted(() => {
    if (searchInput.value) {
        searchInput.value.focus();
    }
});
</script>