<template>
    <div class="max-w-[1200px] mx-auto px-6 mb-12 transition-colors duration-200">
        <div class="flex">
            <div>
                <h1 class="text-4xl font-serif font-bold italic mb-4 mt-16 text-[#FAF8F5] drop-shadow-md">{{
                    model?.name ?? model?.hash }}</h1>
                <h2 class="text-[#FAF8F5]/60 font-mono text-sm uppercase tracking-wider">{{ totalImages }} images</h2>
                <div class="sort-container mb-6 mt-8">
                    <div class="flex flex-wrap justify-start gap-4">
                        <button v-for="option in sortOptions" :key="option.value" @click="updateSort(option.value)"
                            :class="[
                                'magnetic-button px-5 py-2.5 rounded-full transition-all duration-300 font-sans text-sm font-semibold border',
                                currentSort === option.value
                                    ? 'bg-[#2A2A35] text-[#C9A84C] border-[#C9A84C]/30 shadow-[0_0_15px_rgba(201,168,76,0.1)]'
                                    : 'bg-[#14141A] text-[#FAF8F5]/60 border-[#2A2A35]/50 hover:bg-[#1A1A24] hover:text-[#FAF8F5] hover:border-[#2A2A35]'
                            ]">
                            <span class="relative z-10">{{ option.label }}</span>
                        </button>
                    </div>
                </div>
            </div>
            <div class="flex items-end ml-auto">
                <ClearArt class="max-h-32 sm:max-h-62 select-none pointer-events-none" />
            </div>
        </div>


        <!-- Sort controls -->
    </div>

    <div class="px-6  mx-auto w-full">
        <ImageMasonry :pins="modelImages" />
    </div>

    <!-- Loading indicator -->
    <div v-if="isLoading" class="flex flex-col items-center justify-center my-12" aria-live="polite"
        aria-label="Loading">
        <div class="relative w-12 h-12 mb-4">
            <div class="absolute inset-0 rounded-full border-t-2 border-[#C9A84C] border-opacity-20"></div>
            <div class="absolute inset-0 rounded-full border-t-2 border-[#C9A84C] animate-spin"></div>
        </div>
        <ClearArt class="max-w-xs max-h-60 rounded-lg mb-4 " />
        <span class="text-[#FAF8F5]/60 font-mono text-sm tracking-widest uppercase">
            Loading Sequence
        </span>
    </div>

    <!-- Enhanced Page indicator -->
    <div class="text-center text-[#FAF8F5]/40 font-mono text-xs mt-8 mb-12 tracking-wide">
        [ Page {{ String(page).padStart(3, '0') }} / {{ String(totalPages || 0).padStart(3, '0') }} ]
        <div class="text-[10px] mt-2 text-[#C9A84C]/60 tracking-widest uppercase">
            Showing {{ String(modelImages.length).padStart(4, '0') }} of {{ String(totalImages).padStart(4, '0') }}
            images
        </div>
    </div>
</template>

<script setup>
import { GetFromApi } from '@/api';
import Image from '@/components/Image.vue';
import ImageMasonry from '@/components/ImageMasonry.vue';
import ClearArt from '@/components/ClearArt.vue';
import { onMounted, ref, onBeforeUnmount, computed, watch, inject } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();
const isDarkMode = inject('isDarkMode', ref(false));

const model = ref(null);
const modelImages = ref([]);
const isLoading = ref(false);
const isUpdatingFromWatcher = ref(false);

// Pagination metadata
const totalImages = ref(0);
const totalPages = ref(0);
const perPage = ref(50);

// Sorting and pagination
const sortOptions = [
    { label: 'Default', value: 'default' },
    { label: 'New', value: 'new' },
    { label: 'Old', value: 'old' },
    { label: 'Random', value: 'random' }
];

// Initialize sort and page from URL or default values
const currentSort = ref(route.query.sort || 'default');
let page = parseInt(route.query.page) || 1;

// Utility function to ensure unique images by id
const getUniqueImagesById = (imagesArray) => {
    const uniqueMap = new Map();
    imagesArray.forEach(image => {
        if (!uniqueMap.has(image.id)) {
            uniqueMap.set(image.id, image);
        }
    });
    return Array.from(uniqueMap.values());
}

// Update URL when sort changes
const updateSort = (sortValue) => {
    if (currentSort.value === sortValue) return;
    currentSort.value = sortValue;
    page = 1;
    modelImages.value = []; // Reset images for new sort
    updateUrlParams();
    fetchCurrentPage();
}

// Update URL parameters
const updateUrlParams = () => {
    isUpdatingFromWatcher.value = true;
    router.push({
        query: {
            ...route.query,
            sort: currentSort.value,
            page: page
        }
    }).finally(() => {
        setTimeout(() => {
            isUpdatingFromWatcher.value = false;
        }, 50);
    });
}

const loadMore = async () => {
    if (isLoading.value) return;
    // Don't try to load more if we're on the last page
    if (page >= totalPages.value) return;

    isLoading.value = true;
    try {
        page++;
        updateUrlParams();
        const newData = await GetFromApi(`models/${route.params.hash}?sort=${currentSort.value}&per_page=${perPage.value}&page=${page}`);

        // Update pagination metadata
        if (newData.total) totalImages.value = newData.total;
        if (newData.total_pages) totalPages.value = newData.total_pages;
        if (newData.per_page) perPage.value = newData.per_page;

        // Only use images array from the response
        const newImages = newData.images || [];
        if (!newImages.length) return; // Don't proceed if no new images

        // Append new images, don't replace the array
        modelImages.value = [...modelImages.value, ...newImages];
    } finally {
        isLoading.value = false;
    }
}

// Debounce scroll handler to prevent multiple rapid firing
let scrollTimeout = null;
const handleScroll = () => {
    if (scrollTimeout) clearTimeout(scrollTimeout);

    scrollTimeout = setTimeout(() => {
        const scrollPosition = window.innerHeight + window.scrollY;
        const threshold = document.documentElement.scrollHeight - 1000;

        if (scrollPosition > threshold && !isLoading.value && page < totalPages.value) {
            loadMore();
        }
    }, 100);
}

// Function to fetch current page data
const fetchCurrentPage = async () => {
    if (isLoading.value) return;

    isLoading.value = true;
    try {
        const data = await GetFromApi(`models/${route.params.hash}?sort=${currentSort.value}&per_page=${perPage.value}&page=${page}`);
        model.value = data;

        // Update pagination metadata
        if (data.total) totalImages.value = data.total;
        if (data.total_pages) totalPages.value = data.total_pages;
        if (data.per_page) perPage.value = data.per_page;

        // Initialize modelImages with the images from the response
        // Use a non-destructive assignment to ensure reactivity
        modelImages.value = [...(data.images || [])];

        // Log for debugging
        console.log(`Loaded page ${page} with ${modelImages.value.length} images`);
    } finally {
        isLoading.value = false;
    }
}

onMounted(async () => {
    // Initial data fetch on mount
    await fetchCurrentPage();
    window.addEventListener('scroll', handleScroll);
});

onBeforeUnmount(() => {
    window.removeEventListener('scroll', handleScroll);
});

// Watch for route changes
watch(() => route.query, (newQuery) => {
    if (isUpdatingFromWatcher.value) return;

    const newSort = newQuery.sort;
    const newPage = parseInt(newQuery.page) || 1;
    let shouldFetch = false;

    if (newSort && newSort !== currentSort.value) {
        currentSort.value = newSort;
        shouldFetch = true;
    }

    if (newPage !== page) {
        page = newPage;
        shouldFetch = true;
    }

    if (shouldFetch) {
        fetchCurrentPage();
    }
}, { deep: true });
</script>

<style scoped></style>