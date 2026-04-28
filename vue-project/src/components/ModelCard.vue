<template>
    <RouterLink :to="`/models/${model?.hash}`">        
        <div class="relative rounded-[2rem] overflow-hidden border border-[#2A2A35] bg-[#0D0D12] group shadow-md hover:shadow-[0_4px_20px_rgba(0,0,0,0.5)] transition-shadow duration-300">
            <div class="relative w-full" style="aspect-ratio: 2/3" @mouseenter="startSlideshow" @mouseleave="stopSlideshow">
                <img
                    v-if="currentImage"
                    :src="ImageSrc(currentImage)"
                    :alt="model?.name || 'model cover'"
                    class="w-full h-full object-cover"
                    loading="lazy"
                />
                <div v-else class="w-full h-full flex items-center justify-center text-neutral-400 bg-neutral-100 dark:bg-neutral-800">
                    No preview
                </div>
    
                <!-- Top gradient for legibility -->
                <div class="pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-black/70 to-transparent"></div>
                <!-- Bottom gradient for legibility -->
                <div class="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-black/70 to-transparent"></div>
    
                <!-- Top overlay: type -->
                <div class="absolute top-0 left-0 right-0 p-3">
                    <span class="inline-block text-[11px] px-2 py-0.5 rounded-full bg-white/20 text-white uppercase tracking-wide">
                        {{ model?.type }}
                    </span>
                </div>
    
                <!-- Bottom overlay: name + image count -->
                <div class="absolute bottom-0 left-0 right-0 p-3">
                    <h3 class="text-white font-semibold leading-tight truncate text-2xl" :title="model?.name">
                        {{ model?.name }}
                    </h3>
                    <div class="mt-1">
                        <span class="text-xs text-white/80">
                            {{ imageCount }} images
                        </span>
                    </div>
                </div>
            </div>
        </div>
    </RouterLink>
</template>

<script setup>
import { defineProps, computed, ref, onBeforeUnmount } from 'vue'
import { ImageSrc } from '@/api'

const props = defineProps({
    model: Object
})

const model = props.model

// Slideshow sources
const images = computed(() => model?.cover_images ?? [])
const currentIndex = ref(0)
const currentImage = computed(() => images.value[currentIndex.value] ?? null)

let intervalId = null
function startSlideshow() {
    if (images.value.length <= 1 || intervalId) return
    intervalId = setInterval(() => {
        currentIndex.value = (currentIndex.value + 1) % images.value.length
    }, 1000) // slide interval (ms)
}
function stopSlideshow() {
    if (intervalId) {
        clearInterval(intervalId)
        intervalId = null
    }
    currentIndex.value = 0
}
onBeforeUnmount(() => stopSlideshow())

// Count
const imageCount = computed(() => model?.image_count ?? images.value.length)
</script>