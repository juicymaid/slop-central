<script setup>
const windowWidth = ref(window.innerWidth)
const scale = ref(0.7)
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { GetFromApi, webState, PostToApi } from '../api'
import Image from '../components/Image.vue'

// Define emits
const emit = defineEmits(['load-more'])

// Sidebar resize functionality
const isResizing = ref(false)
const startX = ref(0)
const startWidth = ref(0)

// Multi-select state
const selectedIds = ref(new Set())

function toggleSelect(imageId) {
    const next = new Set(selectedIds.value)
    if (next.has(imageId)) {
        next.delete(imageId)
    } else {
        next.add(imageId)
    }
    selectedIds.value = next
}

function clearSelection() {
    selectedIds.value = new Set()
}

async function deleteSelected() {
    if (selectedIds.value.size === 0) return
    if (!confirm(`Move ${selectedIds.value.size} image(s) to trash?`)) return
    const ids = Array.from(selectedIds.value)
    try {
        await PostToApi('trash/bulk', { image_ids: ids })
        // Hide the trashed images from the local pins array by removing them
        ids.forEach(id => {
            const idx = props.pins.findIndex(p => p.Id === id)
            if (idx !== -1) props.pins.splice(idx, 1)
        })
    } catch (error) {
        console.error('Error bulk trashing images:', error)
    }
    clearSelection()
}

function handleKeydown(e) {
    if ((e.key === 'Delete' || e.key === 'Backspace') && selectedIds.value.size > 0) {
        // Only if not focused on an input/textarea
        if (
            document.activeElement.tagName !== 'INPUT' &&
            document.activeElement.tagName !== 'TEXTAREA'
        ) {
            deleteSelected()
        }
    }
    if (e.key === 'Escape') {
        clearSelection()
    }
}

function startResize(e) {
  e.preventDefault()
  isResizing.value = true
  startX.value = e.clientX
  startWidth.value = webState.sidebarWidth
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'col-resize'
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
}

function handleResize(e) {
  if (!isResizing.value) return
  e.preventDefault()
  const deltaX = e.clientX - startX.value
  const newWidth = Math.max(300, Math.min(600, startWidth.value + deltaX))
  webState.sidebarWidth = newWidth
}

function stopResize() {
  isResizing.value = false
  document.body.style.userSelect = ''
  document.body.style.cursor = ''
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
}

// reactive window width
onMounted(() => {
  window.addEventListener('resize', updateWindowWidth)
  window.addEventListener('scroll', handleScroll)
  window.addEventListener('keydown', handleKeydown)
  updateWindowWidth()
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', updateWindowWidth)
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
})
function updateWindowWidth() {
  windowWidth.value = window.innerWidth
}

function handleScroll() {
  const { scrollTop, scrollHeight, clientHeight } = document.documentElement
  if (scrollTop + clientHeight >= scrollHeight - 100) {
    emit('load-more')
  }
}

//pins from props
const props = defineProps({
  pins: {
    type: Array,
    default: () => []
  },
  inBoard: {
    type: Number,
    default: null,
    required: false
  }
})

</script>

<template>
  <!-- Responsive grid layout for images -->
  <div class="w-full flex gap-2">
    <!-- Resize handle for sidebar -->
    <div 
      class="fixed left-0 top-0 w-1 h-full bg-transparent hover:bg-blue-500 cursor-col-resize z-50 transition-colors"
      :style="{ left: webState.sidebarWidth + 'px' }"
      @mousedown="startResize"
    ></div>
    
    <!-- Multi-select action bar -->
    <Teleport to="body">
      <div
        v-if="selectedIds.size > 0"
        class="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 bg-gray-900 text-white px-5 py-3 rounded-full shadow-xl"
      >
        <span class="text-sm font-medium">{{ selectedIds.size }} selected</span>
        <button
          class="flex items-center gap-1.5 bg-red-600 hover:bg-red-700 text-white text-sm font-medium px-4 py-1.5 rounded-full transition-colors"
          @click="deleteSelected"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"></path>
            <path d="M10 11v6M14 11v6"></path>
            <path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"></path>
          </svg>
          Move to Trash
        </button>
        <button
          class="text-sm text-gray-300 hover:text-white px-3 py-1.5 rounded-full hover:bg-white/10 transition-colors"
          @click="clearSelection"
        >
          Cancel
        </button>
      </div>
    </Teleport>

    <div class="w-full" v-for="ci in Math.ceil((((windowWidth-webState.sidebarWidth)/scale * 0.9) - 320) / 400)" :key="ci">
      <Image v-for="pin in pins.filter((p, pi) => ((pi + 1 - ci) % Math.ceil((((windowWidth-webState.sidebarWidth)/scale * 0.9) - 320) / 400)) === 0)"
        :key="pin.Id" :pin="pin" class="mb-2"
        :isSelected="selectedIds.has(pin.Id)"
        :board="inBoard"
        @toggle-select="toggleSelect" />
    </div>
  </div>
</template>