<template>
    <section
        class="min-h-screen py-8 md:py-10 bg-gradient-to-b from-slate-50 to-white dark:from-slate-900 dark:to-slate-950">
        <header class="text-center mb-4">
            <h2 class="m-0 text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">Pick the better
                image</h2>
            <p class="mt-1 text-slate-600 dark:text-slate-400">Click on the one you prefer</p>
        </header>

        <div class="relative grid items-center gap-4 max-w-5xl mx-auto grid-cols-1 md:grid-cols-[1fr_auto_1fr]">
            <div class="flex flex-col">
                <!-- Rank chip above image (left) -->
                <div class="mb-2 flex justify-center">
                    <span
                        class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ring-1 ring-slate-200 dark:ring-slate-700 bg-white/80 dark:bg-slate-800/80 text-slate-700 dark:text-slate-200 shadow-sm">
                        <img :src="rankBadgeSrcFromItem(left)" :alt="(left.rank_label || 'Unranked') + ' badge'"
                            class="h-6 w-6 object-contain" />
                        <span>{{ left.rank_label || 'Unranked' }}</span>
                    </span>
                </div>


                <div class="flex justify-between mb-">
                    <span class="text-base font-medium text-blue-700 dark:text-white">top</span>
                    <span class="text-sm font-medium text-blue-700 dark:text-white">{{ 100-left.top_percentile }}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700 mb-2">
                    <div class="bg-blue-600 h-2.5 rounded-full" :style="`width: ${left.top_percentile}%`"></div>
                </div>



                <button
                    class="group relative block rounded-2xl overflow-hidden bg-slate-100 dark:bg-slate-800 shadow-lg ring-1 ring-slate-200 dark:ring-slate-700 transition will-change-transform duration-200 ease-out hover:-translate-y-1 hover:scale-[1.02] hover:shadow-2xl focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 dark:focus-visible:ring-violet-400"
                    :class="[(hover === 'left' || picked === 'left') && 'ring-2 ring-indigo-300 dark:ring-violet-400', picked === 'left' && 'is-picked', (isLoadingPair || isSubmittingChoice) && 'pointer-events-none opacity-75']"
                    @click="choose('left')" @mouseenter="hover = 'left'" @mouseleave="hover = ''">

                    <!-- Loading spinner for left image -->
                    <div v-if="isLoadingPair || !leftImageLoaded"
                        class="absolute inset-0 flex items-center justify-center bg-slate-100 dark:bg-slate-800">
                        <div
                            class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 dark:border-violet-400">
                        </div>
                    </div>

                    <img v-if="left.Path" :src="ImageSrc(left.Path)" :alt="left.alt" @load="onImageLoad('left')"
                        :class="['w-full h-auto transition duration-300 ease-out saturate-[.9] group-hover:scale-[1.04] group-hover:saturate-110 group-hover:contrast-105', !leftImageLoaded && 'opacity-0']" />

                    <div v-if="leftImageLoaded && !isLoadingPair"
                        class="absolute inset-x-0 bottom-0 h-14 grid place-items-center text-white font-bold uppercase text-xs tracking-widest bg-gradient-to-t from-black/60 to-transparent opacity-0 translate-y-1 transition group-hover:opacity-100 group-hover:translate-y-0">
                        <span v-if="!isSubmittingChoice">Pick</span>
                        <span v-else class="flex items-center gap-2">
                            <div class="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                            Submitting...
                        </span>
                    </div>
                </button>

                <!-- Conservative rating under image (left) -->
                <div class="mt-2 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
                    CR: {{ fmt(left.conservative_rating) }}
                </div>

                <!-- remove button-->
                <div class="mt-2 flex">
                    <router-link :to="'/image/' + left.id"
                        class="mr-4 text-xs text-blue-600 dark:text-blue-400 hover:underline">view</router-link>
                    <button
                        class="text-xs text-red-600 dark:text-red-400 hover:underline disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                        :disabled="isRemovingImage" @click="remove(left.id)">
                        <div v-if="isRemovingImage"
                            class="animate-spin rounded-full h-2 w-2 border-b border-red-600 dark:border-red-400"></div>
                        {{ isRemovingImage ? 'Removing...' : 'Remove' }}
                    </button>
                </div>
            </div>

            <!-- Center VS and average rank -->
            <div class="mx-auto flex flex-col items-center">
                <div
                    class="h-12 w-12 rounded-full grid place-items-center font-bold text-slate-700 dark:text-slate-200 bg-white/80 dark:bg-slate-800/80 ring-1 ring-slate-200 dark:ring-slate-700 shadow">
                    vs
                </div>
                <div class="mt-2 inline-flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400">
                    <img :src="averageRankBadgeSrc()" :alt="(averageRank.label || 'Unranked') + ' badge'"
                        class="h-5 w-5 object-contain" />
                    <span>{{ averageRank.label ?? 'Unranked' }}</span>
                </div>
            </div>

            <div class="flex flex-col">
                <!-- Rank chip above image (right) -->
                <div class="mb-2 flex justify-center">
                    <span
                        class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ring-1 ring-slate-200 dark:ring-slate-700 bg-white/80 dark:bg-slate-800/80 text-slate-700 dark:text-slate-200 shadow-sm">
                        <img :src="rankBadgeSrcFromItem(right)" :alt="(right.rank_label || 'Unranked') + ' badge'"
                            class="h-6 w-6 object-contain" />
                        <span>{{ right.rank_label || 'Unranked' }}</span>
                    </span>
                </div>

                
                <div class="flex justify-between mb-">
                    <span class="text-base font-medium text-blue-700 dark:text-white">top</span>
                    <span class="text-sm font-medium text-blue-700 dark:text-white">{{ 100-right.top_percentile }}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700 mb-2">
                    <div class="bg-blue-600 h-2.5 rounded-full" :style="`width: ${right.top_percentile}%`"></div>
                </div>

                <button
                    class="group relative block rounded-2xl overflow-hidden bg-slate-100 dark:bg-slate-800 shadow-lg ring-1 ring-slate-200 dark:ring-slate-700 transition will-change-transform duration-200 ease-out hover:-translate-y-1 hover:scale-[1.02] hover:shadow-2xl focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 dark:focus-visible:ring-violet-400"
                    :class="[(hover === 'right' || picked === 'right') && 'ring-2 ring-indigo-300 dark:ring-violet-400', picked === 'right' && 'is-picked', (isLoadingPair || isSubmittingChoice) && 'pointer-events-none opacity-75']"
                    @click="choose('right')" @mouseenter="hover = 'right'" @mouseleave="hover = ''">

                    <!-- Loading spinner for right image -->
                    <div v-if="isLoadingPair || !rightImageLoaded"
                        class="absolute inset-0 flex items-center justify-center bg-slate-100 dark:bg-slate-800">
                        <div
                            class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 dark:border-violet-400">
                        </div>
                    </div>

                    <img v-if="right.Path" :src="ImageSrc(right.Path)" :alt="right.alt" @load="onImageLoad('right')"
                        :class="['w-full h-auto transition duration-300 ease-out saturate-[.9] group-hover:scale-[1.04] group-hover:saturate-110 group-hover:contrast-105', !rightImageLoaded && 'opacity-0']" />

                    <div v-if="rightImageLoaded && !isLoadingPair"
                        class="absolute inset-x-0 bottom-0 h-14 grid place-items-center text-white font-bold uppercase text-xs tracking-widest bg-gradient-to-t from-black/60 to-transparent opacity-0 translate-y-1 transition group-hover:opacity-100 group-hover:translate-y-0">
                        <span v-if="!isSubmittingChoice">Pick</span>
                        <span v-else class="flex items-center gap-2">
                            <div class="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                            Submitting...
                        </span>
                    </div>
                </button>

                <!-- Conservative rating under image (right) -->
                <div class="mt-2 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
                    CR: {{ fmt(right.conservative_rating) }}
                </div>

                <!-- remove button-->
                <div class="mt-2 flex">
                    <router-link :to="'/image/' + right.id"
                        class="mr-4 text-xs text-blue-600 dark:text-blue-400 hover:underline">view</router-link>
                    <button
                        class="text-xs text-red-600 dark:text-red-400 hover:underline disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                        :disabled="isRemovingImage" @click="remove(right.id)">
                        <div v-if="isRemovingImage"
                            class="animate-spin rounded-full h-2 w-2 border-b border-red-600 dark:border-red-400"></div>
                        {{ isRemovingImage ? 'Removing...' : 'Remove' }}
                    </button>
                </div>
            </div>
        </div>
        <footer class="flex justify-center mt-4">
            <button
                class="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-800/80 text-slate-700 dark:text-slate-200 font-semibold tracking-wide shadow-sm hover:border-slate-300 dark:hover:border-slate-600 hover:shadow transition active:scale-[.98] disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="isLoadingPair || isSubmittingChoice" @click="nextPair">
                <div v-if="isLoadingPair"
                    class="animate-spin rounded-full h-4 w-4 border-b-2 border-slate-700 dark:border-slate-200"></div>
                {{ isLoadingPair ? 'Loading...' : 'Skip' }}
            </button>
        </footer>
        <!-- Leaderboard -->
        <section class="max-w-5xl mx-auto mt-8">
            <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
                Leaderboard
                <div v-if="isLoadingLeaderboard"
                    class="animate-spin rounded-full h-4 w-4 border-b-2 border-slate-700 dark:border-slate-200"></div>
            </h3>

            <!-- Loading skeleton for leaderboard -->
            <div v-if="isLoadingLeaderboard && leaderboard.length === 0"
                class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                <div v-for="n in 6" :key="n"
                    class="flex items-center gap-4 p-4 rounded-xl ring-1 ring-slate-200 dark:ring-slate-700 bg-white/70 dark:bg-slate-800/60 animate-pulse">
                    <div class="w-24 h-24 md:w-28 md:h-28 rounded-xl bg-slate-300 dark:bg-slate-600"></div>
                    <div class="min-w-0 flex-1">
                        <div class="h-4 bg-slate-300 dark:bg-slate-600 rounded mb-2"></div>
                        <div class="h-3 bg-slate-300 dark:bg-slate-600 rounded w-3/4"></div>
                    </div>
                </div>
            </div>

            <ul v-else class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                <li v-for="(item, idx) in leaderboard" :key="item.id"
                    class="flex items-center gap-4 p-4 rounded-xl ring-1 ring-slate-200 dark:ring-slate-700 bg-white/70 dark:bg-slate-800/60">
                    <div class="relative">
                        <img :src="ImageSrc(item.Path)" alt=""
                            class="w-24 h-24 md:w-28 md:h-28 rounded-xl object-cover shadow ring-1 ring-slate-200 dark:ring-slate-700" />
                        <!-- Rank chip overlay -->
                        <div class="absolute top-1 left-1">
                            <span
                                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ring-1 ring-slate-200 dark:ring-slate-700 bg-white/90 dark:bg-slate-800/90 text-slate-700 dark:text-slate-200 shadow-sm">
                                <img :src="rankBadgeSrcFromItem(item)" :alt="(item.rank_label || 'Unranked') + ' badge'"
                                    class="h-4 w-4 object-contain" />
                                <span v-if="item.rank_subrank != null">{{ item.rank_subrank }}</span>
                            </span>
                        </div>
                        <!-- Optional: Add loading indicator for leaderboard images -->
                        <div class="absolute inset-0 bg-slate-300 dark:bg-slate-600 rounded-xl animate-pulse opacity-0">
                        </div>
                    </div>
                    <div class="min-w-0">
                        <div class="text-sm font-semibold text-slate-800 dark:text-slate-200">
                            #{{ idx + 1 }}
                        </div>
                        <div class="text-xs text-slate-600 dark:text-slate-400">
                            μ {{ fmt(item.mu) }} • σ {{ fmt(item.sigma) }} • CR {{ fmt(item.conservative_rating) }}
                        </div>
                    </div>
                </li>
            </ul>
        </section>


    </section>
</template>

<script setup>
import { apiUrl, GetFromApi, ImageSrc } from '@/api';
import { ref, onMounted } from 'vue';

const hover = ref('');
const picked = ref('');

// Loading states
const isLoadingPair = ref(false);
const isSubmittingChoice = ref(false);
const isLoadingLeaderboard = ref(false);
const isRemovingImage = ref(false);
const leftImageLoaded = ref(false);
const rightImageLoaded = ref(false);

const left = ref({});
const right = ref({});

// New: average rank for current matchup
const averageRank = ref({ tier: null, subrank: null, label: null });

// Error handling
const error = ref(null);

async function nextPair() {
    picked.value = '';
    isLoadingPair.value = true;
    leftImageLoaded.value = false;
    rightImageLoaded.value = false;

    try {

        //get id url param
        const urlParams = new URLSearchParams(window.location.search);
        const id = urlParams.get('id');

        let url = 'matchup';
        if (id) {
            url += '?image1_id=' + encodeURIComponent(id);
        }

        const response = await GetFromApi(url);
        left.value = response.image1;
        right.value = response.image2;

        // Capture average rank fields if present
        averageRank.value = {
            tier: response.average_rank_tier ?? null,
            subrank: response.average_rank_subrank ?? null,
            label: response.average_rank_label ?? null,
        };
    } catch (error) {
        console.error('Error fetching next pair:', error);
    } finally {
        isLoadingPair.value = false;
    }
}

async function choose(side) {

    if (picked.value != '' || isSubmittingChoice.value) return; // Prevent double picks

    picked.value = side;
    isSubmittingChoice.value = true;

    const result = {
        winner_id: side === 'left' ? left.value.id : right.value.id,
        loser_id: side === 'left' ? right.value.id : left.value.id,
    }
    // Send the result to the server (fire and forget)
    const url = apiUrl + "/match";

    try {
        await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(result)
        });
        console.log('Result sent:', result);
    } catch (error) {
        console.error('Error sending match result:', error);
    } finally {
        isSubmittingChoice.value = false;
    }

    nextPair();
}

async function remove(id) {
    if (isRemovingImage.value) return;

    isRemovingImage.value = true;
    const url = apiUrl + "/score/remove/" + id;

    try {
        await fetch(url, {
            method: 'POST',
        });
        await nextPair();
        await updateLeaderboard();
    } catch (error) {
        console.error('Error removing score:', error);
    } finally {
        isRemovingImage.value = false;
    }
}

const leaderboard = ref([]);

async function updateLeaderboard() {
    isLoadingLeaderboard.value = true;

    try {
        const response = await GetFromApi('leaderboard?limit=12');
        leaderboard.value = response.leaderboard || [];
    } catch (error) {
        console.error('Error updating leaderboard:', error);
    } finally {
        isLoadingLeaderboard.value = false;
    }
}
onMounted(() => {
    nextPair();
    updateLeaderboard();
});

function fmt(n, d = 2) {
    return typeof n === 'number' && isFinite(n) ? n.toFixed(d) : '—';
}

function onImageLoad(side) {
    if (side === 'left') {
        leftImageLoaded.value = true;
    } else {
        rightImageLoaded.value = true;
    }
}

// Helper: get tier string from item (fallback to Unranked)
function getTierFromItem(item) {
    const tier = item?.rank_tier || (item?.rank_label ? String(item.rank_label).split(' ')[0] : '') || 'Unranked';
    // Normalize to Title Case to match filenames like Gold.png, Bronze.png, Unranked.png
    return tier.split(' ')
        .map(w => w ? w[0].toUpperCase() + w.slice(1).toLowerCase() : w)
        .join(' ');
}

// Helper: build badge src from tier using API base
function rankBadgeSrc(tier) {
    const safe = encodeURIComponent(tier || 'Unranked');
    return (`/ranks/${safe}.png`);
}



// Convenience helpers
function rankBadgeSrcFromItem(item) {
    return rankBadgeSrc(getTierFromItem(item));
}
function averageRankBadgeSrc() {
    const tier = averageRank.value?.tier || (averageRank.value?.label ? String(averageRank.value.label).split(' ')[0] : 'Unranked');
    return rankBadgeSrc(tier);
}
</script>

<style scoped>
/* Tailwind handles styling; keep only the click pulse animation */
@keyframes pick {
    0% {
        transform: scale(1);
    }

    50% {
        transform: scale(1.03);
    }

    100% {
        transform: scale(1);
    }
}

.is-picked {
    animation: pick 0.4s ease;
}
</style>