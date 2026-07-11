<template>
  <div class="max-w-[1400px] mx-auto px-6 mb-12">

    <div class="mb-16 relative flex justify-between">
      <ClearArt class="max-h-96" />
      <div
        class="text-3xl font-serif font-bold italic absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10 text-[#FAF8F5] drop-shadow-md">
        Profile
      </div>
      <ClearArt class="max-h-96" />

    </div>


    <h2 class="text-3xl font-serif font-bold italic mb-8 mt-12 flex items-center text-[#FAF8F5] drop-shadow-md">
      Boards
      <button @click="showModal = !showModal"
        class="magnetic-button ml-4 p-2 rounded-full hover:bg-[#2A2A35] transition-colors border border-[#2A2A35] bg-[#1A1A24]">
        <Plus class="w-5 h-5 text-[#C9A84C]" />
      </button>
    </h2>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 group cursor-pointer mb-16">
      <div v-for="board in boards" :key="board.id"
        class="bg-[#1A1A24] rounded-[2rem] shadow-lg hover:shadow-[0_4px_25px_rgba(0,0,0,0.5)] transition-all duration-300 overflow-hidden border border-[#2A2A35] group/board">
        <RouterLink :to="'/board/' + board.id">
          <div class="flex">
            <img v-if="board.cover_images.length >= 1" :src="ImageSrc(board.cover_images[0])" alt="Board cover"
              class="w-48 rounded-tl-[2rem] h-48 object-cover group-hover/board:scale-105 transition-transform duration-500" />
            <div v-else class="w-48 h-48 bg-[#0D0D12] rounded-tl-[2rem]"></div>
            <div class="h-48 flex flex-col w-full overflow-hidden">
              <img v-if="board.cover_images.length >= 2" :src="ImageSrc(board.cover_images[1])" alt="Board cover"
                class="w-full h-full object-cover group-hover/board:scale-105 transition-transform duration-500" />
              <img v-if="board.cover_images.length >= 3" :src="ImageSrc(board.cover_images[2])" alt="Board cover"
                class="w-full rounded-tr-[2rem] h-full object-cover group-hover/board:scale-105 transition-transform duration-500" />
            </div>
          </div>

          <div class="p-5 border-t border-[#2A2A35]/50 bg-[#14141A]">
            <h3 class="text-xl font-sans font-semibold text-[#FAF8F5]">{{ board.name }}</h3>
            <p class="text-sm font-mono tracking-widest uppercase mt-1 text-[#C9A84C]">{{ board.pin_count }} Pins</p>
          </div>
        </RouterLink>
      </div>
    </div>

    <h2 class="text-3xl font-serif font-bold italic mb-8 mt-16 flex items-center text-[#FAF8F5] drop-shadow-md">
      Liked Images
    </h2>
    <ImageMasonry :pins="likedImages" />

    <CreateBoardModal v-if="showModal" @close="showModal = false" @create-board="createBoard" />
  </div>
</template>

<script setup>
import { GetFromApi, ImageSrc } from '@/api';
import Image from '@/components/Image.vue';
import { onMounted, onBeforeUnmount, ref, computed, inject } from 'vue';
import { Plus, ChevronDown } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import CreateBoardModal from '@/components/CreateBoardModal.vue';
import ImageMasonry from '@/components/ImageMasonry.vue';
import ClearArt from '@/components/ClearArt.vue';

const boards = ref([])
const models = ref([])
const router = useRouter()
const isDarkMode = inject('isDarkMode', ref(false))

const showModal = ref(false)

// Model sorting and display options
const modelSortOptions = [
  { label: 'Most Images', value: 'most_images' },
  { label: 'Name', value: 'name' },
  { label: 'Last Used', value: 'last_used' }
]
const currentModelSort = ref('most_images')
const showAllModels = ref(false)
const modelsPerRow = 6 // Assuming 4 models per row based on grid layout
const defaultRows = 2

// Computed property to filter displayed models
const displayedModels = computed(() => {
  if (showAllModels.value) {
    return models.value
  } else {
    return models.value.slice(0, defaultRows * modelsPerRow)
  }
})

// Function to change model sort
const changeModelSort = async (sortValue) => {
  if (currentModelSort.value === sortValue) return
  currentModelSort.value = sortValue
  models.value = await GetFromApi(`models?sort=${currentModelSort.value}`)
}

// New refs for liked images infinite scroll
const likedImages = ref([]);
const likedImagesPage = ref(1);
const likedIsLoading = ref(false);

// Function to load more liked images
const loadMoreLikedImages = async () => {
  if (likedIsLoading.value) return;
  likedIsLoading.value = true;
  try {
    likedImagesPage.value++;
    const newData = await GetFromApi('liked-images?per_page=20&page=' + likedImagesPage.value);
    const uniqueNewData = newData.filter(newImage =>
      !likedImages.value.some(existingImage => existingImage.Id === newImage.Id)
    );
    likedImages.value = [...likedImages.value, ...uniqueNewData];
  } finally {
    likedIsLoading.value = false;
  }
};

// Scroll handler for liked images
const handleLikedScroll = () => {
  if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 10) {
    loadMoreLikedImages();
  }
};

// Track current and next image indexes for each model
const modelCurrentImageIndex = ref({});
const modelNextImageIndex = ref({});
const isFading = ref({});

// Track model rotation intervals by hash
const modelRotationIntervals = ref({});

// Track hover state
const hoveredModel = ref(null);

// Function to get current cover image
const getModelCurrentImage = (model) => {
  if (!model.cover_images || model.cover_images.length === 0) {
    return ''; // Return empty if no images
  }

  // Initialize if this model doesn't have an index yet
  if (modelCurrentImageIndex.value[model.hash] === undefined) {
    modelCurrentImageIndex.value[model.hash] = 0;
  }

  return model.cover_images[modelCurrentImageIndex.value[model.hash]];
};

// Function to get next cover image
const getModelNextImage = (model) => {
  if (!model.cover_images || model.cover_images.length <= 1) {
    return getModelCurrentImage(model); // Return same image if only one exists
  }

  // Initialize if this model doesn't have a next index yet
  if (modelNextImageIndex.value[model.hash] === undefined) {
    const nextIdx = (modelCurrentImageIndex.value[model.hash] + 1) % model.cover_images.length;
    modelNextImageIndex.value[model.hash] = nextIdx;
  }

  return model.cover_images[modelNextImageIndex.value[model.hash]];
};

// Function to start model image rotation on hover
const startModelImageRotation = (modelHash) => {
  // Don't start a new interval if one already exists
  if (modelRotationIntervals.value[modelHash]) return;

  // Set this model as hovered
  hoveredModel.value = modelHash;

  // Start rotation interval for this specific model
  modelRotationIntervals.value[modelHash] = setInterval(() => {
    // Only rotate the specific hovered model
    const model = models.value.find(m => m.hash === modelHash);

    if (model && model.cover_images && model.cover_images.length > 1) {
      // Start fade transition
      isFading.value[model.hash] = true;

      // After fade completes, update indices
      setTimeout(() => {
        // Update current to next
        modelCurrentImageIndex.value[model.hash] = modelNextImageIndex.value[model.hash];

        // Calculate new next
        modelNextImageIndex.value[model.hash] =
          (modelNextImageIndex.value[model.hash] + 1) % model.cover_images.length;

        // Reset fade state
        isFading.value[model.hash] = false;
      }, 1000); // Match to CSS transition duration
    }
  }, 3000);
};

// Function to stop model image rotation when not hovering
const stopModelImageRotation = (modelHash) => {
  if (modelRotationIntervals.value[modelHash]) {
    clearInterval(modelRotationIntervals.value[modelHash]);
    modelRotationIntervals.value[modelHash] = null;
  }

  // Clear hover state
  if (hoveredModel.value === modelHash) {
    hoveredModel.value = null;
  }
};

onMounted(async () => {
  // Fetch boards from API
  const data = await GetFromApi('all-boards')
  boards.value = data
  console.log(data)

  // Fetch models from API with current sort
  models.value = await GetFromApi(`models?sort=${currentModelSort.value}`)

  // Load initial liked images
  const likedData = await GetFromApi('liked-images?per_page=20&page=' + likedImagesPage.value);
  likedImages.value = likedData;

  // Register scroll event for liked images
  window.addEventListener('scroll', handleLikedScroll);
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleLikedScroll);

  // Clear all model rotation intervals
  Object.keys(modelRotationIntervals.value).forEach(hash => {
    if (modelRotationIntervals.value[hash]) {
      clearInterval(modelRotationIntervals.value[hash]);
    }
  });
});

</script>