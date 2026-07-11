<template>
    <div class="flex">
        <div class="max-w-[1200px] mx-auto px-6 mb-12 transition-colors duration-200">
            <h1 class="text-4xl font-serif font-bold italic mb-4 mt-16 text-[#FAF8F5] drop-shadow-md">{{ board?.name }}
            </h1>
            <h1 class="text-lg font-sans font-medium mb-4 text-[#C9A84C]">{{ board?.tags }}</h1>
            <h2 class="text-[#FAF8F5]/60 font-mono text-sm uppercase tracking-wider">{{ board?.images.length }} pins
            </h2>
        </div>
        <ClearArt :animated="true" class="max-h-96" />
    </div>
    <div class="px-6  mx-auto">
        <ImageMasonry :pins="board?.images" />
    </div>
    <h1 class="text-3xl font-serif font-bold italic mb-8 mt-24 text-center text-[#FAF8F5] drop-shadow-md">More Ideas
    </h1>
    <div class="px-6  mx-auto">
        <ImageMasonry :pins="suggestions" :inBoard="board?.id" />
    </div>

</template>



<script setup>
import { GetFromApi } from '@/api';
import ClearArt from '@/components/ClearArt.vue';
import Image from '@/components/Image.vue';
import ImageMasonry from '@/components/ImageMasonry.vue';
import { onMounted, ref, onBeforeUnmount, inject } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const isDarkMode = inject('isDarkMode', ref(false));

const boardId = route.params.id;

const board = ref(null);
const suggestions = ref([]);

const suggestionPage = ref(1);
const isSuggestionsLoading = ref(false);

const loadMoreSuggestions = async () => {
    if (isSuggestionsLoading.value) return;
    isSuggestionsLoading.value = true;
    try {
        suggestionPage.value++;
        const moreSuggestions = await GetFromApi(`board-suggestions?board_id=${boardId}&per_page=50&page=${suggestionPage.value}`);
        suggestions.value = [...suggestions.value, ...moreSuggestions];
    } finally {
        isSuggestionsLoading.value = false;
    }
}

const handleScroll = () => {
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 10) {
        loadMoreSuggestions();
    }
}

onMounted(async () => {
    const data = await GetFromApi(`board/${boardId}`);
    board.value = data;

    const suggestionsData = await GetFromApi(`board-suggestions?board_id=${boardId}`);
    suggestions.value = suggestionsData;

    window.addEventListener('scroll', handleScroll);
});

onBeforeUnmount(() => {
    window.removeEventListener('scroll', handleScroll);
});

</script>