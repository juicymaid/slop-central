<template>
    <div class="max-w-[1200px] mx-auto px-6 mb-12">
        <h1 class="text-3xl font-serif font-bold italic mb-8 mt-12 text-[#FAF8F5] drop-shadow-md">Image Scanner</h1>

        <!-- Scan Button -->
        <div class="flex flex-wrap justify-start gap-4 mb-12">
            <button @click="startScan"
                class="magnetic-button bg-[#2A2A35] hover:bg-[#1A1A24] text-[#C9A84C] py-3 px-8 rounded-full text-sm font-sans font-semibold border border-[#C9A84C]/30 flex items-center gap-2 transition-all shadow-[0_0_15px_rgba(201,168,76,0.1)]"
                :disabled="isScanning">
                <svg v-if="!isScanning" class="w-5 h-5 relative z-10" fill="none" stroke="currentColor"
                    viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z">
                    </path>
                </svg>
                <svg v-else class="w-5 h-5 animate-spin relative z-10" viewBox="0 0 24 24" fill="none">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
                    </path>
                </svg>
                <span class="relative z-10">{{ isScanning ? 'Scanning...' : 'Start Scan' }}</span>
            </button>
            <button @click="startphash"
                class="magnetic-button bg-[#1A1A24] hover:bg-[#2A2A35] text-[#FAF8F5]/80 py-3 px-8 rounded-full text-sm font-sans font-semibold border border-[#2A2A35] flex items-center gap-2 transition-all"
                :disabled="phasInProgress">
                <svg v-if="!phasInProgress" class="w-5 h-5 relative z-10" fill="none" stroke="currentColor"
                    viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z">
                    </path>
                </svg>
                <svg v-else class="w-5 h-5 animate-spin relative z-10" viewBox="0 0 24 24" fill="none">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
                    </path>
                </svg>
                <span class="relative z-10">{{ phasInProgress ? 'Calculating...' : 'Calculate pHashes' }}</span>
            </button>
            <!-- Prune Images Button -->
            <button @click="pruneImages"
                class="magnetic-button bg-[#1A1A24] hover:bg-red-500/20 hover:text-red-400 hover:border-red-500/30 text-[#FAF8F5]/80 py-3 px-8 rounded-full text-sm font-sans font-semibold border border-[#2A2A35] flex items-center gap-2 transition-all"
                :disabled="isPruning">
                <svg v-if="!isPruning" class="w-5 h-5 relative z-10" fill="none" stroke="currentColor"
                    viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16">
                    </path>
                </svg>
                <svg v-else class="w-5 h-5 animate-spin relative z-10" viewBox="0 0 24 24" fill="none">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
                    </path>
                </svg>
                <span class="relative z-10">{{ isPruning ? 'Pruning...' : 'Prune Images' }}</span>
            </button>
            <RouterLink to="/trash"
                class="magnetic-button bg-[#1A1A24] hover:bg-[#2A2A35] text-[#FAF8F5]/80 py-3 px-8 rounded-full text-sm font-sans font-semibold border border-[#2A2A35] flex items-center gap-2 transition-all">
                <svg class="w-5 h-5 relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16">
                    </path>
                </svg>
                <span class="relative z-10">Trash</span>
            </RouterLink>
        </div>

        <!-- SigLIP 2 Embeddings Panel -->
        <div class="mb-12 p-6 rounded-[2rem] bg-[#14141A] border border-[#2A2A35]">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                <div>
                    <h2 class="text-xl font-sans font-semibold text-[#FAF8F5]">Neural Search & Recommendations (SigLIP 2)</h2>
                    <p class="text-sm text-[#FAF8F5]/60 mt-1">Generates 768-dimensional deep visual embeddings to power similarity search and recommendations.</p>
                </div>
                <div class="flex gap-3">
                    <button @click="startSiglipIndexing(false)"
                        class="magnetic-button bg-[#2A2A35] hover:bg-[#1A1A24] text-[#FAF8F5] py-2 px-6 rounded-full text-xs font-sans font-semibold border border-[#2A2A35] flex items-center gap-2 transition-all cursor-pointer"
                        :disabled="siglipStatus.status === 'running'">
                        {{ siglipStatus.status === 'running' ? 'Indexing...' : 'Update Embeddings' }}
                    </button>
                    <button @click="startSiglipIndexing(true)"
                        class="magnetic-button bg-[#1A1A24] hover:bg-red-500/20 hover:text-red-400 hover:border-red-500/30 text-[#FAF8F5]/60 py-2 px-6 rounded-full text-xs font-sans font-semibold border border-[#2A2A35] flex items-center gap-2 transition-all cursor-pointer"
                        :disabled="siglipStatus.status === 'running'">
                        Force Rebuild All
                    </button>
                </div>
            </div>

            <!-- Status info -->
            <div class="flex flex-col gap-2 font-mono text-xs uppercase tracking-widest text-[#FAF8F5]/60">
                <div class="flex justify-between">
                    <span>Status:</span>
                    <span :class="siglipStatus.status === 'running' ? 'text-[#C9A84C]' : 'text-green-500'">{{ siglipStatus.status }}</span>
                </div>
                <div v-if="siglipStatus.status === 'running'" class="w-full mt-2">
                    <div class="h-1 w-full bg-[#0D0D12] overflow-hidden mb-2">
                        <div class="h-full bg-[#C9A84C] transition-all duration-300 ease-out"
                            :style="{ width: `${siglipProgress}%` }"></div>
                    </div>
                    <div class="flex justify-between">
                        <span>Progress:</span>
                        <span>{{ siglipStatus.processed }} / {{ siglipStatus.total }} ({{ siglipProgress }}%)</span>
                    </div>
                </div>
                <div class="flex justify-between mt-1">
                    <span>Message:</span>
                    <span class="normal-case text-right text-gray-400 max-w-[70%] truncate">{{ siglipStatus.message || 'No active task.' }}</span>
                </div>
            </div>
        </div>
        <p v-if="error" class="text-red-500 font-mono tracking-wide text-sm mt-4">{{ errorMessage }}</p>

        <!-- Loading Progress Bar -->
        <div v-if="isScanning" class="mb-12 p-6 rounded-[2rem] bg-[#14141A] border border-[#2A2A35]">
            <!-- Progress bar for retrieving files -->
            <div v-if="scanStatus === 'retrieving_files'" class="mb-4">
                <div class="h-1 w-full bg-[#0D0D12] overflow-hidden">
                    <div class="h-full bg-[#C9A84C] transition-all duration-300 ease-out indeterminate-progress"></div>
                </div>
                <p class="text-center mt-4 text-[#FAF8F5]/60 font-mono text-sm tracking-widest uppercase">{{
                    scanStatusMessage }}</p>
            </div>

            <!-- Progress bar for scanning files -->
            <div v-else-if="scanStatus === 'files_found' || scanStatus === 'scanning'">
                <div class="h-1 w-full bg-[#0D0D12] overflow-hidden">
                    <div class="h-full bg-[#C9A84C] transition-all duration-300 ease-out"
                        :style="{ width: `${scanProgress}%` }"></div>
                </div>
                <div
                    class="mt-4 flex justify-between items-center text-[#FAF8F5]/60 font-mono text-sm uppercase tracking-widest">
                    <p>{{ scanStatusMessage }}</p>
                    <p v-if="scanTotal > 0">{{ scanProcessed }} / {{ scanTotal }} ({{ scanProgress }}%)</p>
                </div>
            </div>

            <!-- Saving status -->
            <div v-else-if="scanStatus === 'saving'" class="mb-4">
                <div class="h-1 w-full bg-[#0D0D12] overflow-hidden">
                    <div class="h-full bg-green-500 transition-all duration-300 ease-out indeterminate-progress"></div>
                </div>
                <p class="text-center mt-4 text-[#FAF8F5]/60 font-mono text-sm tracking-widest uppercase">{{
                    scanStatusMessage }}</p>
            </div>
        </div>

        <!-- Scan Complete Summary -->
        <div v-if="scanStatus === 'completed' && !isScanning"
            class="mb-10 p-6 bg-green-900/10 border border-green-500/20 rounded-[2rem] transition-colors">
            <h3 class="text-green-500 text-xl font-serif italic mb-2">Scan Completed</h3>
            <p class="text-green-400 font-sans text-sm">{{ scanStatusMessage }}</p>
            <p class="text-green-400/80 font-mono text-xs uppercase tracking-widest mt-2">Processed {{
                completedStats.totalProcessed }} images, added {{ completedStats.totalAdded }} new images.</p>
        </div>

        <!-- New Images Grid -->
        <div v-if="newImages.length > 0" class="mb-10">
            <h2 class="text-xl font-sans font-semibold mb-6 text-[#FAF8F5]">
                Discovered Images <span class="text-[#FAF8F5]/40 font-mono text-sm">({{ newImages.length }})</span>
            </h2>
            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                <div v-for="(image, index) in newImages" :key="image.Path || index" class="relative group">
                    <RouterLink v-if="image.Id" :to="'/image/' + image.Id">
                        <img :src="apiUrl + image.Path" alt="Image"
                            class="w-full h-64 object-cover rounded-[2rem] shadow-md transition-transform duration-500 transform group-hover:scale-105" />
                    </RouterLink>
                    <div v-else class="relative">
                        <img :src="apiUrl + image.Path" alt="Image"
                            class="w-full h-64 object-cover rounded-[2rem] shadow-md" />
                        <div
                            class="absolute inset-0 bg-[#0D0D12]/60 backdrop-blur-sm rounded-[2rem] flex items-center justify-center text-[#C9A84C] font-mono tracking-widest uppercase text-xs">
                            Processing...
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="!isScanning && scanStatus !== 'completed'" class="text-center py-24">
            <ClearArt class="max-h-[50vh] mx-auto" />
            <p class="mt-4 text-[#FAF8F5]/40 font-mono text-sm tracking-widest uppercase">[ System Ready for Scan ]
            </p>
        </div>
    </div>
</template>

<script setup>
import { GetFromApi, PostToApi, apiUrl, wsUrl } from '@/api';
import ClearArt from '@/components/ClearArt.vue';
import { ref, computed, onMounted, onBeforeUnmount, inject } from 'vue';

// State for scan
const isScanning = ref(false);
const scanStatus = ref('');
const scanStatusMessage = ref('');
const scanProcessed = ref(0);
const scanSuccessful = ref(0);
const scanTotal = ref(0);
const scanProgress = ref(0);
const latestFile = ref('');
const error = ref(false);
const errorMessage = ref('');
const newImages = ref([]);
const websocket = ref(null);
const completedStats = ref({
    totalProcessed: 0,
    totalAdded: 0
});

// State for other operations
const phasInProgress = ref(false);
const isPruning = ref(false);
const isDarkMode = inject('isDarkMode', ref(false));

// State for SigLIP embeddings builder
const siglipStatus = ref({ status: 'idle', processed: 0, total: 0, message: '' });
const siglipInterval = ref(null);
const siglipProgress = computed(() => {
    if (siglipStatus.value.total > 0) {
        return Math.round((siglipStatus.value.processed / siglipStatus.value.total) * 100);
    }
    return 0;
});

const fetchSiglipStatus = async () => {
    try {
        const res = await GetFromApi("ai-search/siglip-status");
        if (res) {
            siglipStatus.value = res;
        }
    } catch (e) {
        console.error("Error fetching SigLIP status:", e);
    }
};

const startSiglipIndexing = async (force = false) => {
    try {
        await PostToApi(`ai-search/rebuild-siglip?force=${force}`);
        await fetchSiglipStatus();
        startSiglipPolling();
    } catch (e) {
        console.error("Error starting SigLIP indexing:", e);
    }
};

const startSiglipPolling = () => {
    if (siglipInterval.value) return;
    siglipInterval.value = setInterval(async () => {
        await fetchSiglipStatus();
        if (siglipStatus.value.status !== 'running') {
            stopSiglipPolling();
        }
    }, 1000);
};

const stopSiglipPolling = () => {
    if (siglipInterval.value) {
        clearInterval(siglipInterval.value);
        siglipInterval.value = null;
    }
};

// WebSocket connection for scan
const connectWebSocket = () => {
    // Close any existing connection
    if (websocket.value && websocket.value.readyState !== WebSocket.CLOSED) {
        websocket.value.close();
    }

    // Determine WebSocket URL from current location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const _wsUrl = `${wsUrl}/ws/scan`;

    websocket.value = new WebSocket(_wsUrl);

    websocket.value.onopen = () => {
        console.log('WebSocket connection established');
        isScanning.value = true;
        error.value = false;
        errorMessage.value = '';
    };

    websocket.value.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (e) {
            console.error('Error parsing WebSocket message:', e);
        }
    };

    websocket.value.onerror = (event) => {
        console.error('WebSocket error:', event);
        error.value = true;
        errorMessage.value = 'WebSocket connection error';
        isScanning.value = false;
    };

    websocket.value.onclose = () => {
        console.log('WebSocket connection closed');
        isScanning.value = false;
    };
};

// Handle incoming WebSocket messages
const handleWebSocketMessage = (data) => {
    console.log('WebSocket message:', data);

    switch (data.type) {
        case 'status':
            scanStatus.value = data.status;
            scanStatusMessage.value = data.message;

            if (data.status === 'files_found' && data.total_files) {
                scanTotal.value = data.total_files;
            }

            if (data.status === 'completed') {
                isScanning.value = false;
                completedStats.value = {
                    totalProcessed: data.total_processed || 0,
                    totalAdded: data.total_added || 0
                };
            }
            break;

        case 'progress':
            scanStatus.value = 'scanning';
            scanProcessed.value = data.processed;
            scanSuccessful.value = data.successful;
            scanTotal.value = data.total;
            scanProgress.value = data.percent;
            latestFile.value = data.latest_file;
            break;

        case 'image_discovered':
            // Add newly discovered image to the list
            if (data.image_path) {
                // Check if we already have this image to avoid duplicates
                const exists = newImages.value.some(img => img.Path === data.image_path);
                if (!exists) {
                    newImages.value.push({
                        Path: data.image_path,
                        // Other metadata will be updated when ID is assigned
                    });
                }
            }

            // Update scan progress
            scanProcessed.value = data.processed;
            scanSuccessful.value = data.successful;
            scanTotal.value = data.total;
            scanProgress.value = data.percent;
            break;

        case 'image_failed':
            // Update scan progress for failed images
            scanProcessed.value = data.processed;
            scanSuccessful.value = data.successful;
            scanTotal.value = data.total;
            scanProgress.value = data.percent;
            break;

        case 'error':
            error.value = true;
            errorMessage.value = data.message || 'An error occurred';
            isScanning.value = false;
            break;

        case 'complete':
            scanStatus.value = 'completed';
            scanStatusMessage.value = data.message;
            isScanning.value = false;

            // Update statistics
            completedStats.value = {
                totalProcessed: data.total_processed || 0,
                totalAdded: data.total_added || 0
            };

            // No need to fetch from API - we already have the images
            // Just update their IDs if needed
            const startId = (data.start_id || 0) + 1;

            newImages.value.forEach((img, index) => {
                if (!img.Id) {
                    img.Id = startId + index;
                }
            });
            break;

        default:
            console.warn('Unknown WebSocket message type:', data.type);
    }
};

// Methods
const startScan = () => {
    // Reset state
    scanStatus.value = 'starting';
    scanStatusMessage.value = 'Connecting...';
    scanProcessed.value = 0;
    scanSuccessful.value = 0;
    scanTotal.value = 0;
    scanProgress.value = 0;
    latestFile.value = '';
    error.value = false;
    errorMessage.value = '';
    newImages.value = []; // Clear any existing images before starting

    // Connect to WebSocket
    connectWebSocket();
};

const startphash = async () => {
    phasInProgress.value = true;
    try {
        const response = await PostToApi("calculate-phashes");
        // Wait for a short time to allow backend to start processing
        await new Promise(resolve => setTimeout(resolve, 500));
    } catch (e) {
        console.error('Error starting phash calculation:', e);
    } finally {
        phasInProgress.value = false;
    }
};

const pruneImages = async () => {
    isPruning.value = true;
    try {
        const response = await PostToApi("prune-images");
        // Wait for a short time to allow backend to complete processing
        await new Promise(resolve => setTimeout(resolve, 500));
    } catch (e) {
        console.error('Error pruning images:', e);
    } finally {
        isPruning.value = false;
    }
};

onMounted(async () => {
    // Load current SigLIP status
    await fetchSiglipStatus();
    if (siglipStatus.value.status === 'running') {
        startSiglipPolling();
    }
});

onBeforeUnmount(() => {
    stopSiglipPolling();
    // Close WebSocket connection when component is unmounted
    if (websocket.value && websocket.value.readyState !== WebSocket.CLOSED) {
        websocket.value.close();
    }
});
</script>

<style scoped>
/* Add indeterminate progress bar animation */
@keyframes indeterminate {
    0% {
        left: -35%;
        right: 100%;
    }

    60% {
        left: 100%;
        right: -90%;
    }

    100% {
        left: 100%;
        right: -90%;
    }
}

.indeterminate-progress {
    position: relative;
    width: 100%;
}

.indeterminate-progress::before {
    content: '';
    position: absolute;
    background-color: inherit;
    top: 0;
    left: 0;
    bottom: 0;
    will-change: left, right;
    animation: indeterminate 2.1s cubic-bezier(0.65, 0.815, 0.735, 0.395) infinite;
}
</style>