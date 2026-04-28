<template>
    <RouterLink v-if="!hide" :to="`/image/${pin.Id}`" class="block relative group/link"
        @click.capture="handleLinkClick">
        <div :key="pin.Id" class="break-inside-avoid cursor-pointer p-0.5">
            <div class="relative group rounded-xl overflow-hidden" :style="`aspect-ratio: ${pin.Width}/${pin.Height}`"
                :class="{ 'ring-2 ring-[#C9A84C] ring-offset-4 ring-offset-[#0D0D12]': isSelected }">
                <!-- Placeholder shown while image is loading -->
                <div v-if="!imageLoaded"
                    class="w-full h-full absolute top-0 left-0 bg-[#14141A] animate-pulse rounded-[2rem]"></div>

                <img :src="ImageSrc(pin.Path)" :alt="pin.Prompt"
                    class="w-full h-full object-cover  absolute top-0 left-0 transition-opacity duration-300"
                    :class="{ 'opacity-0': !imageLoaded, 'opacity-100': imageLoaded }" @error="handleImageError"
                    @load="imageLoaded = true" loading="lazy" />
                <div
                    class="absolute inset-0 bg-[#0D0D12]/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 ">
                    <div class="absolute bottom-0 left-0 right-0 p-6">
                        <!-- Add a subtle text shadow for readability -->
                        <h3 class="text-[#FAF8F5] font-sans font-medium drop-shadow-md">{{ }}</h3>
                    </div>
                    <div class="absolute bottom-0 right-0 p-4 flex gap-3">
                        <div
                            class="p-2.5 bg-[#FAF8F5]/10 rounded-full hover:bg-[#FAF8F5]/20  cursor-pointer flex items-center gap-1.5 transition-colors border border-[#FAF8F5]/10">
                            <div class="flex" @click.prevent.stop="">
                                <Star v-for="star in 5" :key="star"
                                    class="w-4 h-4 text-white cursor-pointer transition-colors duration-150" :class="{
                                        'fill-yellow-400 text-yellow-400': star <= (pin.Rating || 0),
                                        'hover:fill-yellow-200 hover:text-yellow-200': star <= hoverRating
                                    }" @click.prevent.stop="rateImage(star)" @mouseenter="hoverRating = star"
                                    @mouseleave="hoverRating = 0" />
                            </div>
                            <p v-if="pin.Rating > 0" class="text-[#FAF8F5] font-mono text-sm ml-1">{{
                                pin.Rating.toFixed(0) }}</p>
                        </div>
                        <button
                            class="p-2.5 bg-red-500/20 text-red-400 rounded-full hover:bg-red-500/40 hover:text-red-300  flex transition-colors border border-red-500/20"
                            @click.prevent.stop="deletePin(pin.Id)">
                            <Trash class="w-4 h-4" />
                        </button>
                    </div>
                    <div
                        class="absolute bottom-0 left-0 p-4 bg-[#0D0D12]/40 backdrop-blur-md rounded-tr-[2rem] flex items-center border-t border-r border-[#FAF8F5]/10">
                        <Eye class="w-4 h-4 text-[#C9A84C]" />
                        <p class="ml-2 text-[#FAF8F5] font-mono text-sm">{{ pin.Clicks }}</p>
                    </div>
                    <div v-if="pin.recommended_boards && !board"
                        class="absolute top-0 left-0 right-0 p-4 flex items-center justify-between cursor-pointer">
                        <div v-if="pin.in_boards.length == 0" ref="dropdownTrigger"
                            class="rounded-full px-4 py-2 cursor-pointer font-sans font-medium text-sm text-[#FAF8F5] flex items-center bg-[#1A1A24]/60 backdrop-blur-md hover:bg-[#2A2A35]/80 transition-colors border border-[#FAF8F5]/10"
                            @click.prevent.stop="toggleDropdown($event)">
                            {{ pin.recommended_boards[selectedBoard].name || '' }}
                            <ChevronDown class="w-4 h-4 text-[#FAF8F5]/60 ml-2" />
                        </div>
                        <RouterLink :to="'/board/' + pin.in_boards[0].id" v-else
                            class="rounded-full px-4 py-2 cursor-pointer font-sans font-medium text-sm text-[#FAF8F5] flex items-center bg-[#C9A84C]/20 text-[#C9A84C] backdrop-blur-md hover:bg-[#C9A84C]/30 transition-colors border border-[#C9A84C]/20">
                            {{ pin.in_boards[0].name || '' }}
                        </RouterLink>

                        <button v-if="pin.in_boards.length == 0"
                            class="px-5 py-2 bg-[#C9A84C] text-[#0D0D12] font-sans font-semibold text-sm rounded-full hover:bg-[#C9A84C]/90 shadow-[0_0_15px_rgba(201,168,76,0.2)] transition-colors magnetic-button inline-flex items-center"
                            @click.prevent.stop="saveToBoard(pin.recommended_boards[selectedBoard].id)">
                            <span class="relative z-10">Save</span>
                        </button>
                        <button v-else
                            class="px-5 py-2 bg-[#1A1A24] text-[#FAF8F5]/60 font-sans font-semibold text-sm rounded-full border border-[#2A2A35]"
                            @click.prevent.stop="removeFromBoard(pin.recommended_boards[selectedBoard].id)">
                            Saved
                        </button>
                    </div>

                </div>

                <div v-if="board">
                    <div class="absolute top-0 right-0 p-4 flex gap-2">
                        <button
                            class="p-2.5 bg-[#C9A84C] rounded-full hover:bg-[#C9A84C]/90 cursor-pointer flex transition-colors shadow-[0_0_15px_rgba(201,168,76,0.2)]"
                            @click.prevent.stop="PostToApi('board/' + board + '/pin?image_id=' + pin.Id); showPin = false">
                            <Pin class="w-4 h-4 text-[#0D0D12]" />
                        </button>
                    </div>
                </div>

            </div>
        </div>
        <div v-if="showBoardDropdown" ref="dropdownContainer" class="z-50 absolute top-16" @click.prevent.stop="">
            <BoardDropDown :pin="pin" @save-to="(id) => saveToBoard(id)" />
        </div>
    </RouterLink>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import { ImageSrc, PostToApi } from '../api'
import { Star, Pin, ChevronDown, Eye, Trash } from 'lucide-vue-next'
import { ref, defineProps, defineEmits, onMounted, onBeforeUnmount } from 'vue'
import BoardDropDown from './BoardDropDown.vue'

const hide = ref(false)
const showPin = ref(true)
const imageLoaded = ref(false)
const hoverRating = ref(0)

const selectedBoard = ref(0)

const emit = defineEmits(['toggle-select'])

const props = defineProps({
    pin: Object,
    board: Number,
    isSelected: {
        type: Boolean,
        default: false
    }
})

function handleLinkClick(event) {
    if (event.ctrlKey || event.metaKey) {
        event.preventDefault()
        emit('toggle-select', props.pin.Id)
    }
}

// Handle image loading error
function handleImageError() {
    hide.value = true
    imageLoaded.value = false
}

// Reset image loaded state when pin changes
onMounted(() => {
    document.addEventListener('click', handleClickOutside)
    imageLoaded.value = false // Reset on mount
})

onBeforeUnmount(() => {
    document.removeEventListener('click', handleClickOutside)
})

async function saveToBoard(boardId) {
    showBoardDropdown.value = false
    await PostToApi('board/' + boardId + '/pin?image_id=' + props.pin.Id)
    let board = props.pin.recommended_boards.find(board => board.id === boardId)
    props.pin.in_boards.push(board)
}
async function removeFromBoard(boardId) {
    showBoardDropdown.value = false
    await PostToApi('board/' + boardId + '/unpin?image_id=' + props.pin.Id)
    props.pin.in_boards = []
}

// Function to handle pin deletion (moves to trash)
async function deletePin(pinId) {
    //if (confirm('Move this image to trash?')) {
        try {
            await PostToApi('delete/' + pinId)
            hide.value = true
        } catch (error) {
            console.error('Error trashing image:', error)
        }
    //}
}

// Function to handle star rating
async function rateImage(rating) {
    try {
        await PostToApi(`rate/${props.pin.Id}?rating=${rating}`)
        props.pin.Rating = rating
    } catch (error) {
        console.error('Error rating image:', error)
    }
}

const showBoardDropdown = ref(false)

// New ref for dropdown container
const dropdownContainer = ref(null)

// Add click-outside handler to close dropdown
function handleClickOutside(event) {
    if (dropdownContainer.value && !dropdownContainer.value.contains(event.target)) {
        showBoardDropdown.value = false
    }
}

// New reactive variable for dropdown style
const dropdownStyle = ref({ top: '0px', left: '0px' })

// New function to toggle dropdown and calculate position
function toggleDropdown(event) {
    showBoardDropdown.value = !showBoardDropdown.value
    if (showBoardDropdown.value) {
        const triggerRect = event.target.getBoundingClientRect()
        dropdownStyle.value = {
            top: `${triggerRect.bottom + window.scrollY}px`,
            left: `${triggerRect.left + window.scrollX}px`
        }
    }
}
</script>

<style scoped>
/* Add smooth fade-in animation for images */
.transition-opacity {
    transition: opacity 0.3s ease-in-out;
}

@keyframes pulse {

    0%,
    100% {
        opacity: 0.6;
    }

    50% {
        opacity: 0.8;
    }
}

.animate-pulse {
    animation: pulse 1.5s ease-in-out infinite;
}
</style>