<template>
    <div
        class="flex h-screen w-full flex-col bg-zinc-950 text-zinc-200 overflow-hidden font-sans selection:bg-indigo-500/30 fixed inset-0 pt-16">

        <div class="flex flex-1 min-h-0 relative">

            <main ref="viewportRef" class="relative flex-1 overflow-hidden bg-zinc-950" @wheel.prevent="onWheel">
                <div class="absolute inset-0 pointer-events-none opacity-20"
                    style="background-image: radial-gradient(#404040 1px, transparent 1px); background-size: 20px 20px;">
                </div>

                <div v-if="!hasImage"
                    class="absolute inset-0 flex flex-col items-center justify-center text-zinc-500 pointer-events-none">
                    <p class="text-sm">Upload an image to start</p>
                </div>

                <div class="absolute inset-0 overflow-auto flex items-center justify-center p-12 outline-none mb-12"
                    ref="scrollContainerRef">
                    <div v-if="hasImage"
                        class="relative transition-transform duration-75 ease-out origin-center shadow-2xl shadow-black"
                        :style="{
                            width: canvasWidth + 'px',
                            height: canvasHeight + 'px',
                            transform: `scale(${zoom})`
                        }" @pointerleave="onPointerUp">
                        <canvas ref="baseCanvasRef" class="block bg-zinc-800 pointer-events-none" />

                        <img v-if="hasGeneratedPreview" :src="currentGeneratedImage"
                            class="absolute left-0 top-0 h-full w-full pointer-events-none object-contain" />

                        <canvas ref="maskCanvasRef" class="absolute left-0 top-0 touch-none"
                            :class="[cursorClass, hasGeneratedPreview ? 'opacity-0 pointer-events-none' : 'opacity-100']"
                            @pointerdown="onPointerDown" @pointermove="onPointerMove" @pointerup="onPointerUp"
                            @pointercancel="onPointerUp" @contextmenu.prevent />

                        <div class="pointer-events-none absolute -inset-[1px] border border-zinc-500/50 z-50">
                            <div class="absolute inset-0 border border-white/20"></div>

                            <div class="pointer-events-auto absolute left-0 top-0 h-full w-6 -translate-x-3 cursor-ew-resize group flex items-center justify-center"
                                @pointerdown="(e) => onResizeHandleDown(e, 'l')">
                                <div
                                    class="h-8 w-1 rounded-full bg-indigo-500/0 transition-colors group-hover:bg-indigo-500">
                                </div>
                            </div>

                            <div class="pointer-events-auto absolute right-0 top-0 h-full w-6 translate-x-3 cursor-ew-resize group flex items-center justify-center"
                                @pointerdown="(e) => onResizeHandleDown(e, 'r')">
                                <div
                                    class="h-8 w-1 rounded-full bg-indigo-500/0 transition-colors group-hover:bg-indigo-500">
                                </div>
                            </div>

                            <div class="pointer-events-auto absolute left-0 top-0 w-full h-6 -translate-y-3 cursor-ns-resize group flex items-center justify-center"
                                @pointerdown="(e) => onResizeHandleDown(e, 't')">
                                <div
                                    class="w-8 h-1 rounded-full bg-indigo-500/0 transition-colors group-hover:bg-indigo-500">
                                </div>
                            </div>

                            <div class="pointer-events-auto absolute left-0 bottom-0 w-full h-6 translate-y-3 cursor-ns-resize group flex items-center justify-center"
                                @pointerdown="(e) => onResizeHandleDown(e, 'b')">
                                <div
                                    class="w-8 h-1 rounded-full bg-indigo-500/0 transition-colors group-hover:bg-indigo-500">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            <aside
                class="w-[320px] shrink-0 border-l border-zinc-800 bg-zinc-900 flex flex-col overflow-y-auto z-10 shadow-xl">
                <div class="p-4 border-b border-zinc-800 space-y-4">
                    <div class="flex items-center justify-between gap-3">
                        <div class="flex items-center gap-2">
                            <div class="h-6 w-6 rounded bg-gradient-to-br from-indigo-500 to-purple-600"></div>
                            <span class="font-bold tracking-tight text-zinc-100">Inpaint Studio</span>
                        </div>
                        <div class="text-[11px] text-zinc-400" v-if="hasImage">
                            {{ canvasWidth }} × {{ canvasHeight }}px
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-2">
                        <button
                            class="rounded px-3 py-1.5 text-xs font-medium transition-colors hover:bg-zinc-800 disabled:opacity-50 text-zinc-300 hover:text-white"
                            :disabled="!hasImage || isGenerating" @click="fitView">
                            Fit Screen
                        </button>

                        <div class="space-y-2">
                            <button
                                class="w-full rounded bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-indigo-500 disabled:bg-zinc-800 disabled:text-zinc-500"
                                :disabled="!hasImage || isGenerating" @click="generatePreview">
                                {{ isGenerating ? 'Generating…' : 'Generate' }}
                            </button>

                            <div class="space-y-1">
                                <div class="flex justify-between text-[11px] text-zinc-400">
                                    <span>Image Count</span>
                                    <span>{{ imageCount }}</span>
                                </div>
                                <input v-model.number="imageCount" type="range" min="1" max="8" step="1"
                                    class="h-1 w-full appearance-none rounded bg-zinc-700 accent-indigo-500"
                                    :disabled="isGenerating" />
                            </div>


                        </div>
                    </div>

                    <div class="flex items-center justify-between rounded bg-zinc-950 px-2 py-1 border border-zinc-800"
                        v-if="hasImage">
                        <button @click="setZoom(zoom - 0.1)"
                            class="hover:text-white text-zinc-400 text-lg leading-none px-1">-</button>
                        <span class="w-12 text-center tabular-nums text-xs">{{ Math.round(zoom * 100) }}%</span>
                        <button @click="setZoom(zoom + 0.1)"
                            class="hover:text-white text-zinc-400 text-lg leading-none px-1">+</button>
                    </div>
                    <div v-if="isGenerating" class="space-y-1">
                        <div class="flex justify-between text-[11px] text-zinc-500">
                            <span>{{ progressLabel }}</span>
                            <span>{{ Math.round(progressPct * 100) }}%</span>
                        </div>
                        <div class="h-1 w-full rounded bg-zinc-800 overflow-hidden">
                            <div class="h-full bg-indigo-600" :style="{ width: `${Math.round(progressPct * 100)}%` }">
                            </div>
                        </div>
                    </div>
                </div>

                <div class="p-4 border-b border-zinc-800">
                    <h3 class="mb-3 text-xs font-bold uppercase tracking-wider text-zinc-500">Source</h3>
                    <label
                        class="flex w-full cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-zinc-700 bg-zinc-800/50 hover:bg-zinc-800 hover:border-zinc-500 transition h-20 group">
                        <div class="flex items-center gap-2">
                            <svg class="h-5 w-5 text-zinc-400 group-hover:text-zinc-200" fill="none"
                                stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
                            </svg>
                            <span class="text-xs text-zinc-400 group-hover:text-zinc-200">Open Image</span>
                        </div>
                        <input type="file" class="hidden" accept="image/*" @change="onPickFile" />
                    </label>
                    <div v-if="imageError" class="mt-2 text-xs text-red-400">{{ imageError }}</div>
                </div>

                <div class="p-4 border-b border-zinc-800 space-y-5">
                    <div>
                        <h3 class="mb-2 text-xs font-bold uppercase tracking-wider text-zinc-500">Tools</h3>
                        <div class="grid grid-cols-2 gap-1 rounded bg-zinc-950 p-1">
                            <button @click="mode = 'paint'"
                                class="flex items-center justify-center gap-2 rounded px-2 py-1.5 text-xs font-medium transition-all"
                                :class="mode === 'paint' ? 'bg-zinc-700 text-white shadow-sm' : 'text-zinc-400 hover:text-zinc-200'">Paint</button>
                            <button @click="mode = 'erase'"
                                class="flex items-center justify-center gap-2 rounded px-2 py-1.5 text-xs font-medium transition-all"
                                :class="mode === 'erase' ? 'bg-zinc-700 text-white shadow-sm' : 'text-zinc-400 hover:text-zinc-200'">Erase</button>
                        </div>
                    </div>

                    <div class="space-y-2">
                        <div class="flex justify-between text-xs text-zinc-400">
                            <span>Brush Size</span>
                            <span>{{ brushSize }}px</span>
                        </div>
                        <input v-model.number="brushSize" type="range" min="1" max="300"
                            class="h-1 w-full appearance-none rounded bg-zinc-700 accent-zinc-200" />
                    </div>

                    <div>
                        <h3 class="mb-2 text-xs font-bold uppercase tracking-wider text-zinc-500">Transform</h3>
                        <div class="grid grid-cols-2 gap-2 text-xs">
                            <div>
                                <label class="text-zinc-500 block mb-1">Canvas W</label>
                                <input v-model.number="canvasWidth" type="number"
                                    class="w-full bg-zinc-950 border border-zinc-800 rounded px-2 py-1 text-zinc-300">
                            </div>
                            <div>
                                <label class="text-zinc-500 block mb-1">Canvas H</label>
                                <input v-model.number="canvasHeight" type="number"
                                    class="w-full bg-zinc-950 border border-zinc-800 rounded px-2 py-1 text-zinc-300">
                            </div>
                            <div>
                                <label class="text-zinc-500 block mb-1">Offset X</label>
                                <input v-model.number="imageOffsetX" type="number"
                                    class="w-full bg-zinc-950 border border-zinc-800 rounded px-2 py-1 text-zinc-300">
                            </div>
                            <div>
                                <label class="text-zinc-500 block mb-1">Offset Y</label>
                                <input v-model.number="imageOffsetY" type="number"
                                    class="w-full bg-zinc-950 border border-zinc-800 rounded px-2 py-1 text-zinc-300">
                            </div>
                        </div>
                    </div>

                    <button @click="clearMask"
                        class="w-full rounded border border-zinc-700 bg-transparent py-1.5 text-xs text-zinc-300 hover:bg-zinc-800 disabled:opacity-50"
                        :disabled="!hasImage">Clear Mask</button>
                </div>

                <div class="p-4 border-b border-zinc-800 space-y-4 flex-1">
                    <h3 class="text-xs font-bold uppercase tracking-wider text-zinc-500">Generation</h3>
                    <div class="space-y-2">
                        <label class="text-xs text-zinc-300">Prompt</label>
                        <textarea id="positive_prompt" v-model="prompt"
                            class="positive_prompt w-full resize-none rounded bg-zinc-950 p-3 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500 border border-zinc-800"
                            rows="3" placeholder="Describe the change..."></textarea>
                    </div>
                    <div class="space-y-2">
                        <div class="flex justify-between text-xs text-zinc-400">
                            <span>Denoising Strength</span>
                            <span>{{ denoise.toFixed(2) }}</span>
                        </div>
                        <input v-model.number="denoise" type="range" min="0" max="1" step="0.01"
                            class="h-1 w-full appearance-none rounded bg-zinc-700 accent-indigo-500" />
                    </div>
                    <div class="space-y-2">
                        <span class="text-xs text-zinc-300">Loras ({{ selectedLoras.length }}/{{ maxLoras }})</span>
                        <button
                            class="w-full rounded border border-zinc-700 bg-transparent py-1.5 text-xs text-zinc-300 hover:bg-zinc-800 disabled:opacity-50"
                            :disabled="isGenerating || selectedLoras.length >= maxLoras || !loras?.length"
                            @click="selectedLoras.push({ name: loras[0].name, path: loras[0].path, weight: 1 })">
                            Add Lora
                        </button>

                        <div
                            v-for="(lora, idx) in selectedLoras"
                            :key="`${lora?.path || 'lora'}-${idx}`"
                            class="rounded bg-zinc-800 px-3 py-2 text-xs border border-zinc-700">
                            <div class="flex items-center gap-2">
                                <select
                                    class="flex-1 bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-zinc-300"
                                    :disabled="isGenerating"
                                    :value="lora?.path"
                                    @change="(e) => {
                                        const path = e.target.value
                                        const opt = loras.find(o => o.path === path)
                                        if (opt) {
                                            lora.name = opt.name
                                            lora.path = opt.path
                                        } else {
                                            lora.path = path
                                        }
                                    }">
                                    <option v-for="option in loras" :key="option.path" :value="option.path">
                                        {{ option.name }}
                                    </option>
                                </select>

                                <button
                                    type="button"
                                    class="text-zinc-400 hover:text-red-500 text-lg leading-none px-1"
                                    :disabled="isGenerating"
                                    @click="selectedLoras.splice(idx, 1)"
                                    aria-label="Remove lora"
                                    title="Remove">
                                    &times;
                                </button>
                            </div>

                            <div class="mt-2 space-y-1">
                                <div class="flex justify-between text-[11px] text-zinc-400">
                                    <span>Strength</span>
                                    <span class="tabular-nums">
                                        {{ (typeof lora.weight === 'number' ? lora.weight : 1).toFixed(2) }}
                                    </span>
                                </div>

                                <input
                                    type="range"
                                    min="0"
                                    max="5"
                                    step="0.01"
                                    class="h-1 w-full appearance-none rounded bg-zinc-700 accent-indigo-500"
                                    :disabled="isGenerating"
                                    :value="typeof lora.weight === 'number' ? lora.weight : 1"
                                    @input="(e) => { lora.weight = e.target.valueAsNumber }" />
                            </div>
                        </div>
                    </div>
                </div>

                <div v-if="previewUrl" class="p-4 border-t border-zinc-800 bg-zinc-950">
                    <div class="mb-2 text-xs font-semibold text-zinc-400">Mask</div>
                    <img :src="previewUrl"
                        class="w-full rounded border border-zinc-800 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4IiBoZWlnaHQ9IjgiPjxwYXRoIGQ9Ik0wIDBoNHY0SDB6TTQgNGg0djhINFoiIGZpbGw9IiMzMzMiIGZpbGwtb3BhY2l0eT0iMC40Ii8+PC9zdmc+')] object-contain" />
                </div>
            </aside>
        </div>
        <div v-if="isGenerating || generatedImages.length > 0"
            class="absolute bottom-16 left-0  z-30 border-t border-zinc-800 bg-zinc-900/95 backdrop-blur ">
            <div class="mx-auto flex max-w-5xl items-center justify-between gap-3 px-4 py-2">
                <div class="flex items-center gap-2 text-xs text-zinc-400">
                    <span v-if="isGenerating">Generating…</span>
                    <span v-else>Done</span>
                    <span v-if="generatedImages.length">({{ currentGeneratedIndex + 1 }}/{{ generatedImages.length
                        }})</span>
                </div>

                <div class="flex items-center gap-2">
                    <button
                        class="rounded border border-zinc-700 bg-transparent px-2 py-1 text-xs text-zinc-200 hover:bg-zinc-800 disabled:opacity-50"
                        :disabled="generatedImages.length <= 1" @click="prevGenerated">
                        Prev
                    </button>
                    <button
                        class="rounded border border-zinc-700 bg-transparent px-2 py-1 text-xs text-zinc-200 hover:bg-zinc-800 disabled:opacity-50"
                        :disabled="generatedImages.length <= 1" @click="nextGenerated">
                        Next
                    </button>
                    <button
                        class="rounded border border-zinc-700 bg-transparent px-2 py-1 text-xs text-zinc-200 hover:bg-zinc-800 disabled:opacity-50"
                        :disabled="!generatedImages.length" @click="toggleGeneratedPreview">
                        {{ showGeneratedPreview ? 'Hide Preview' : 'Show Preview' }}
                    </button>
                </div>

                <div class="flex items-center gap-2">
                    <button
                        class="rounded border border-zinc-700 bg-transparent px-2 py-1 text-xs text-zinc-200 hover:bg-zinc-800 disabled:opacity-50"
                        :disabled="isGenerating" @click="retryGeneration">
                        Retry
                    </button>
                    <button
                        class="rounded border border-zinc-700 bg-transparent px-2 py-1 text-xs text-zinc-200 hover:bg-zinc-800"
                        @click="denyOrCancel">
                        {{ isGenerating ? 'Cancel' : 'Deny' }}
                    </button>
                    <button
                        class="rounded bg-indigo-600 px-2 py-1 text-xs font-semibold text-white hover:bg-indigo-500 disabled:bg-zinc-800 disabled:text-zinc-500"
                        :disabled="!generatedImages.length" @click="acceptGenerated">
                        Accept
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch, nextTick } from 'vue'
import { onUiUpdate } from '@/scripts/autoComplete'
import { useRoute } from 'vue-router'
import { GetFromApi, ImageSrc } from '../api'

// --- Refs ---
const baseCanvasRef = ref(null)
const maskCanvasRef = ref(null)
const scrollContainerRef = ref(null)
const viewportRef = ref(null)
const imageEl = ref(null)

const route = useRoute()

// --- State ---
const prompt = ref('')
const denoise = ref(1)
const imageCount = ref(1)
const imageError = ref('')
const mode = ref('paint')
const brushSize = ref(50)
const previewUrl = ref('')

// --- ComfyUI Generation State ---
const isGenerating = ref(false)
const progressPct = ref(0)
const progressLabel = ref('')
const generatedImages = ref([])
const currentGeneratedIndex = ref(0)
const showGeneratedPreview = ref(true)

// --- Document State ---
const canvasWidth = ref(1024)
const canvasHeight = ref(1024)

// --- Transform State ---
const imageOffsetX = ref(0)
const imageOffsetY = ref(0)
const imageScale = ref(1)


const loras = ref([
    {
        name: "Breast Size Slider",
        path: "Pony\\Slider\\Breast Size Slider.safetensors",
    },
    {
        name: "Ass Size Slider",
        path: "Pony\\Slider\\Ass slider _last.safetensors",
    },
    {
        name: "Cum slider",
        path: "Pony\\Slider\\cum slider 2 _last.safetensors"
    },
    {
        name: "Thicc Slider",
        path: "Pony\\Slider\\ThiccPonyXL_V1.safetensors"
    },
    {
        name: "Skindentation",
        path: "Pony\\Slider\\skindentation_v1.safetensors"
    }
])
const maxLoras = 4;
const selectedLoras = ref([])

// --- Viewport State ---
const zoom = ref(1)

const hasImage = computed(() => !!imageEl.value)
const currentGeneratedImage = computed(() => generatedImages.value[currentGeneratedIndex.value] || '')
const hasGeneratedPreview = computed(() => showGeneratedPreview.value && !!currentGeneratedImage.value)
const cursorClass = computed(() => {
    if (resizeState.value.active) return 'cursor-none' // Hide default cursor while dragging handles
    return mode.value === 'erase' ? 'cursor-cell' : 'cursor-crosshair'
})

// --- Helpers ---
function clampNumber(value, min, max) {
    const n = Number(value)
    if (Number.isNaN(n)) return min
    return Math.min(max, Math.max(min, n))
}

function clampInt(value, min, max) {
    return Math.floor(clampNumber(value, min, max))
}

watch(denoise, (v) => { denoise.value = clampNumber(v, 0, 1) })
watch(imageCount, (v) => { imageCount.value = clampInt(v, 1, 8) })

// --- Canvas Context Helpers ---
function getBaseCtx() { return baseCanvasRef.value?.getContext('2d') }
function getMaskCtx() { return maskCanvasRef.value?.getContext('2d', { willReadFrequently: true }) }

// --- Core Resizing Logic ---
function resizeCanvases() {
    const base = baseCanvasRef.value
    const mask = maskCanvasRef.value
    if (!base || !mask) return

    const w = Math.max(1, Math.floor(Number(canvasWidth.value) || 1))
    const h = Math.max(1, Math.floor(Number(canvasHeight.value) || 1))

    if (base.width !== w) base.width = w
    if (base.height !== h) base.height = h
    if (mask.width !== w) mask.width = w
    if (mask.height !== h) mask.height = h
}

function getMaskSnapshotCanvas() {
    const mask = maskCanvasRef.value
    if (!mask) return null
    const tmp = document.createElement('canvas')
    tmp.width = mask.width
    tmp.height = mask.height
    const tmpCtx = tmp.getContext('2d')
    if (!tmpCtx) return null
    tmpCtx.drawImage(mask, 0, 0)
    return tmp
}

function applyCanvasResizeWithMaskPreserved({ newW, newH, shiftX = 0, shiftY = 0 }) {
    // 1. Snapshot the current mask
    const prevMask = getMaskSnapshotCanvas()

    // 2. Update Dimensions
    canvasWidth.value = Math.max(1, Math.floor(Number(newW) || 1))
    canvasHeight.value = Math.max(1, Math.floor(Number(newH) || 1))

    // 3. Resize DOM Elements
    resizeCanvases()
    drawBase()

    // 4. Restore Mask at new position
    const ctx = getMaskCtx()
    if (!ctx) return
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height)
    if (prevMask) {
        ctx.drawImage(prevMask, shiftX, shiftY)
    }
}

function drawBase() {
    const ctx = getBaseCtx()
    const img = imageEl.value
    if (!ctx) return

    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height)
    if (!img) return

    ctx.imageSmoothingEnabled = true
    ctx.imageSmoothingQuality = 'high'

    ctx.drawImage(
        img,
        imageOffsetX.value,
        imageOffsetY.value,
        img.naturalWidth * imageScale.value,
        img.naturalHeight * imageScale.value
    )
}

// --- Zoom & Fit Logic ---
function setZoom(val) {
    zoom.value = clampNumber(val, 0.1, 5)
}

function fitView() {
    if (!hasImage.value || !scrollContainerRef.value) return
    const containerW = scrollContainerRef.value.clientWidth - 80
    const containerH = scrollContainerRef.value.clientHeight - 80
    const ratioW = containerW / canvasWidth.value
    const ratioH = containerH / canvasHeight.value
    setZoom(Math.min(1, Math.min(ratioW, ratioH)))
}

function onWheel(e) {
    if (e.ctrlKey || e.metaKey) {
        const delta = e.deltaY > 0 ? -0.1 : 0.1
        setZoom(zoom.value + delta)
    }
}

// --- File Handling ---
function onPickFile(e) {
    imageError.value = ''
    previewUrl.value = ''
    const file = e?.target?.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = () => {
        const img = new Image()
        img.onload = () => {
            imageEl.value = img
            canvasWidth.value = img.naturalWidth
            canvasHeight.value = img.naturalHeight
            imageOffsetX.value = 0
            imageOffsetY.value = 0
            imageScale.value = 1

            // Wait for the canvases to actually render (v-if="hasImage")
            // before trying to resize/draw, otherwise they stay at 300x150.
            nextTick(() => {
                resizeCanvases()
                drawBase()
                clearMask()
                fitView()
            })
        }
        img.src = String(reader.result)
    }
    reader.readAsDataURL(file)
}

async function loadImageFromUrl(src) {
    imageError.value = ''
    previewUrl.value = ''

    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
        imageEl.value = img
        canvasWidth.value = img.naturalWidth
        canvasHeight.value = img.naturalHeight
        imageOffsetX.value = 0
        imageOffsetY.value = 0
        imageScale.value = 1

        nextTick(() => {
            resizeCanvases()
            drawBase()
            clearMask()
            fitView()
        })
    }
    img.onerror = () => {
        imageError.value = 'Failed to load image'
    }
    img.src = src
}

// --- Canvas Coordinates & Painting ---
function getCanvasPointFromEvent(evt) {
    const canvas = maskCanvasRef.value
    if (!canvas) return null
    const rect = canvas.getBoundingClientRect()

    // Calculate raw pixel offset relative to the element
    const clientX = evt.clientX - rect.left
    const clientY = evt.clientY - rect.top

    // Scale by the inverse of the CSS zoom to get actual canvas pixels
    const x = clientX / zoom.value
    const y = clientY / zoom.value
    return { x, y }
}

function strokeLine(ctx, from, to) {
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.lineWidth = brushSize.value

    if (mode.value === 'erase') {
        ctx.globalCompositeOperation = 'destination-out'
        ctx.strokeStyle = 'rgba(0,0,0,1)'
    } else {
        ctx.globalCompositeOperation = 'source-over'
        ctx.strokeStyle = 'rgba(239, 68, 68, 0.5)'
    }

    ctx.beginPath()
    ctx.moveTo(from.x, from.y)
    ctx.lineTo(to.x, to.y)
    ctx.stroke()
}

// --- Resize Handles Logic (Fixed) ---
const resizeState = ref({
    active: false,
    edge: null,
    pointerId: null,
    startClientX: 0,
    startClientY: 0,
    startW: 0,
    startH: 0,
    startOffsetX: 0,
    startOffsetY: 0,
})

function onResizeHandleDown(evt, edge) {
    if (!hasImage.value) return

    // Lock pointer to handle
    try { evt.currentTarget?.setPointerCapture?.(evt.pointerId) } catch { }

    resizeState.value = {
        active: true,
        edge,
        pointerId: evt.pointerId,
        startClientX: evt.clientX,
        startClientY: evt.clientY,
        startW: Number(canvasWidth.value) || 1,
        startH: Number(canvasHeight.value) || 1,
        startOffsetX: Number(imageOffsetX.value) || 0,
        startOffsetY: Number(imageOffsetY.value) || 0,
    }

    // Attach to window so dragging continues if mouse leaves the handle/div
    window.addEventListener('pointermove', onResizeHandleMove, { passive: false })
    window.addEventListener('pointerup', onResizeHandleUp, { passive: true })
    window.addEventListener('pointercancel', onResizeHandleUp, { passive: true })
}

function onResizeHandleMove(evt) {
    const s = resizeState.value
    if (!s.active) return
    if (s.pointerId !== evt.pointerId) return

    // 1. Calculate raw screen movement
    const rawDx = evt.clientX - s.startClientX
    const rawDy = evt.clientY - s.startClientY

    // 2. Adjust for ZOOM level to get canvas pixels
    // If zoom is 0.5, moving mouse 100px means we moved 200 canvas pixels.
    const dx = Math.round(rawDx / zoom.value)
    const dy = Math.round(rawDy / zoom.value)

    let newW = s.startW
    let newH = s.startH
    let newOffsetX = s.startOffsetX
    let newOffsetY = s.startOffsetY
    let shiftX = 0
    let shiftY = 0

    // 3. Apply math based on handle
    if (s.edge === 'l') {
        newW = Math.max(1, s.startW - dx)
        const appliedDx = s.startW - newW
        newOffsetX = s.startOffsetX - appliedDx
        shiftX = -appliedDx // Move mask to stay relative to image content
    } else if (s.edge === 'r') {
        newW = Math.max(1, s.startW + dx)
    } else if (s.edge === 't') {
        newH = Math.max(1, s.startH - dy)
        const appliedDy = s.startH - newH
        newOffsetY = s.startOffsetY - appliedDy
        shiftY = -appliedDy
    } else if (s.edge === 'b') {
        newH = Math.max(1, s.startH + dy)
    }

    // 4. Update state (this triggers the canvas redraw via watchers/apply)
    imageOffsetX.value = newOffsetX
    imageOffsetY.value = newOffsetY
    applyCanvasResizeWithMaskPreserved({ newW, newH, shiftX, shiftY })
}

function onResizeHandleUp() {
    if (!resizeState.value.active) return
    resizeState.value = { ...resizeState.value, active: false }
    window.removeEventListener('pointermove', onResizeHandleMove)
    window.removeEventListener('pointerup', onResizeHandleUp)
    window.removeEventListener('pointercancel', onResizeHandleUp)
}

// --- Painting Pointer Events ---
let isPointerDown = false
let lastPos = null

function onPointerDown(evt) {
    if (!hasImage.value) return
    if (resizeState.value.active) return // Don't paint if resizing
    if (evt.button === 1) return // Middle click ignore

    try { evt.currentTarget?.setPointerCapture?.(evt.pointerId) } catch { }

    isPointerDown = true
    const ctx = getMaskCtx()
    const p = getCanvasPointFromEvent(evt)

    if (ctx && p) {
        lastPos = p
        strokeLine(ctx, p, { x: p.x + 0.1, y: p.y + 0.1 })
    }
}

function onPointerMove(evt) {
    if (!isPointerDown) return
    const ctx = getMaskCtx()
    const p = getCanvasPointFromEvent(evt)

    if (ctx && p && lastPos) {
        strokeLine(ctx, lastPos, p)
        lastPos = p
    }
}

function onPointerUp() {
    isPointerDown = false
    lastPos = null
}

function clearMask() {
    const ctx = getMaskCtx()
    if (ctx) ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height)
    previewUrl.value = ''
}

// --- ComfyUI Client ---
const comfyServerAddress = '127.0.0.1:8888'
const comfyClientId = (globalThis.crypto?.randomUUID?.() ?? String(Math.random()).slice(2))

let comfyWs = null
let activePromptId = null
let activeGenerationToken = 0

function resetGenerationState() {
    progressPct.value = 0
    progressLabel.value = ''
    generatedImages.value = []
    currentGeneratedIndex.value = 0
    showGeneratedPreview.value = true
}

function closeComfyWs() {
    try { comfyWs?.close?.() } catch { }
    comfyWs = null
}

async function interruptComfyUi() {
    try {
        await fetch(`http://${comfyServerAddress}/interrupt`, { method: 'POST' })
    } catch {
        // best-effort
    }
}

async function uploadImageToComfyUi(dataUrl) {
    const blob = await (await fetch(dataUrl)).blob()
    const file = new File([blob], `inpaint-${Date.now()}.png`, { type: blob.type || 'image/png' })
    const form = new FormData()
    form.append('image', file)

    const res = await fetch(`http://${comfyServerAddress}/upload/image`, {
        method: 'POST',
        body: form,
    })
    if (!res.ok) throw new Error(`ComfyUI upload failed: ${res.status}`)
    const json = await res.json()
    const name = json?.name
    const subfolder = json?.subfolder || ''
    if (!name) throw new Error('ComfyUI upload response missing filename')
    return subfolder ? `${subfolder}/${name}` : name
}

async function queueComfyPrompt(workflow) {
    const payload = { prompt: workflow, client_id: comfyClientId }
    const res = await fetch(`http://${comfyServerAddress}/prompt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error(`ComfyUI queue failed: ${res.status}`)
    return await res.json()
}

function connectComfyWs() {
    return new Promise((resolve, reject) => {
        const ws = new WebSocket(`ws://${comfyServerAddress}/ws?clientId=${encodeURIComponent(comfyClientId)}`)
        ws.binaryType = 'arraybuffer'
        ws.onopen = () => resolve(ws)
        ws.onerror = (e) => reject(e)
    })
}

function prevGenerated() {
    if (generatedImages.value.length <= 1) return
    currentGeneratedIndex.value = Math.max(0, currentGeneratedIndex.value - 1)
}

function nextGenerated() {
    if (generatedImages.value.length <= 1) return
    currentGeneratedIndex.value = Math.min(generatedImages.value.length - 1, currentGeneratedIndex.value + 1)
}

function toggleGeneratedPreview() {
    showGeneratedPreview.value = !showGeneratedPreview.value
}

async function acceptGenerated() {
    const src = currentGeneratedImage.value
    if (!src) return

    const img = new Image()
    img.onload = () => {
        imageEl.value = img
        canvasWidth.value = img.naturalWidth
        canvasHeight.value = img.naturalHeight
        imageOffsetX.value = 0
        imageOffsetY.value = 0
        imageScale.value = 1
        resizeCanvases()
        drawBase()
        clearMask()
        nextTick(() => fitView())
    }
    img.src = src

    resetGenerationState()
}

async function retryGeneration() {
    if (isGenerating.value) return
    await generatePreview()
}

async function denyOrCancel() {
    if (isGenerating.value) {
        activeGenerationToken++
        await interruptComfyUi()
        closeComfyWs()
        isGenerating.value = false
        progressLabel.value = 'Canceled'
        return
    }
    resetGenerationState()
}

const inpaintWorkflow = {
    "9": {
        "inputs": {
            "text": "score_9, score_8_up, score_7_up, prompt",
            "clip": [
                "53",
                1
            ]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {
            "title": "CLIP Text Encode (Prompt)"
        }
    },
    "10": {
        "inputs": {
            "text": "score_6, score_5, score_4, (worst quality:1.2), (low quality:1.2), (normal quality:1.2), lowres, bad anatomy, bad hands, signature, watermarks, ugly, imperfect eyes, skewed eyes, unnatural face, unnatural body, error, extra limb, missing limbs",
            "clip": [
                "53",
                1
            ]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {
            "title": "CLIP Text Encode (Prompt)"
        }
    },
    "14": {
        "inputs": {
            "samples": [
                "40",
                0
            ],
            "vae": [
                "19",
                2
            ]
        },
        "class_type": "VAEDecode",
        "_meta": {
            "title": "VAE Decode"
        }
    },
    "19": {
        "inputs": {
            "ckpt_name": "Pony\\cyberrealisticPony_v150.safetensors"
        },
        "class_type": "CheckpointLoaderSimple",
        "_meta": {
            "title": "Load Checkpoint"
        }
    },
    "28": {
        "inputs": {
            "filename_prefix": "inpaint/Comfyui",
            "images": [
                "14",
                0
            ]
        },
        "class_type": "SaveImage",
        "_meta": {
            "title": "Save Image"
        }
    },
    "33": {
        "inputs": {
            "image": "clipspace/clipspace-painted-masked-1767546399345.png [input]"
        },
        "class_type": "LoadImage",
        "_meta": {
            "title": "Load Image"
        }
    },
    "35": {
        "inputs": {
            "head": "fooocus_inpaint_head.pth",
            "patch": "inpaint_v26.fooocus.patch"
        },
        "class_type": "INPAINT_LoadFooocusInpaint",
        "_meta": {
            "title": "Load Fooocus Inpaint"
        }
    },
    "36": {
        "inputs": {
            "model": [
                "53",
                0
            ],
            "patch": [
                "35",
                0
            ],
            "latent": [
                "38",
                0
            ]
        },
        "class_type": "INPAINT_ApplyFooocusInpaint",
        "_meta": {
            "title": "Apply Fooocus Inpaint"
        }
    },
    "38": {
        "inputs": {
            "grow_mask_by": 8,
            "pixels": [
                "43",
                0
            ],
            "vae": [
                "19",
                2
            ],
            "mask": [
                "45",
                0
            ]
        },
        "class_type": "VAEEncodeForInpaint",
        "_meta": {
            "title": "VAE Encode (for Inpainting)"
        }
    },
    "40": {
        "inputs": {
            "seed": 397275539528203,
            "steps": 20,
            "cfg": 7,
            "sampler_name": "euler_ancestral",
            "scheduler": "karras",
            "denoise": 0.8,
            "model": [
                "36",
                0
            ],
            "positive": [
                "9",
                0
            ],
            "negative": [
                "10",
                0
            ],
            "latent_image": [
                "38",
                0
            ]
        },
        "class_type": "KSampler",
        "_meta": {
            "title": "KSampler"
        }
    },
    "43": {
        "inputs": {
            "upscale_method": "lanczos",
            "megapixels": 1,
            "resolution_steps": 1,
            "image": [
                "33",
                0
            ]
        },
        "class_type": "ImageScaleToTotalPixels",
        "_meta": {
            "title": "ImageScaleToTotalPixels"
        }
    },
    "44": {
        "inputs": {
            "image": [
                "43",
                0
            ]
        },
        "class_type": "Get resolution [Crystools]",
        "_meta": {
            "title": "🪛 Get resolution"
        }
    },
    "45": {
        "inputs": {
            "width": [
                "44",
                0
            ],
            "height": [
                "44",
                1
            ],
            "keep_proportions": false,
            "upscale_method": "nearest-exact",
            "crop": "disabled",
            "mask": [
                "33",
                1
            ]
        },
        "class_type": "ResizeMask",
        "_meta": {
            "title": "Resize Mask"
        }
    },
    "53": {
        "inputs": {
            "lora_01": "None",
            "strength_01": 1,
            "lora_02": "None",
            "strength_02": 1,
            "lora_03": "None",
            "strength_03": 1,
            "lora_04": "None",
            "strength_04": 1,
            "model": [
                "19",
                0
            ],
            "clip": [
                "19",
                1
            ]
        },
        "class_type": "Lora Loader Stack (rgthree)",
        "_meta": {
            "title": "Lora Loader Stack (rgthree)"
        }
    },
    "54": {
        "inputs": {
            "amount": 1
        },
        "class_type": "RepeatLatentBatch",
        "_meta": {
            "title": "Repeat Latent Batch"
        }
    }
}

// --- Generator ---
function generatePreview() {
    const img = imageEl.value
    const base = baseCanvasRef.value
    const mask = maskCanvasRef.value
    if (!img || !base || !mask) return

    if (isGenerating.value) return

    const w = base.width
    const h = base.height

    const out = document.createElement('canvas')
    out.width = w
    out.height = h
    const outCtx = out.getContext('2d')
    if (!outCtx) return

    outCtx.drawImage(img, imageOffsetX.value, imageOffsetY.value, img.naturalWidth * imageScale.value, img.naturalHeight * imageScale.value)

    const outData = outCtx.getImageData(0, 0, w, h)
    const maskData = mask.getContext('2d').getImageData(0, 0, w, h).data

    for (let i = 0; i < outData.data.length; i += 4) {
        const alpha = maskData[i + 3]
        if (alpha > 0) {
            outData.data[i + 3] = Math.max(0, outData.data[i + 3] - alpha)
        }
    }

    outCtx.putImageData(outData, 0, 0)
    previewUrl.value = out.toDataURL('image/png')

    const thisToken = ++activeGenerationToken
    isGenerating.value = true
    imageError.value = ''
    progressPct.value = 0
    progressLabel.value = 'Uploading'
    generatedImages.value = []
    currentGeneratedIndex.value = 0
    showGeneratedPreview.value = true

        ; (async () => {
            try {
                const uploadedPath = await uploadImageToComfyUi(previewUrl.value)
                if (thisToken !== activeGenerationToken) return

                const workflow = { ...inpaintWorkflow }
                workflow["9"].inputs.text = workflow["9"].inputs.text.replace('prompt', prompt.value)
                workflow["40"].inputs.denoise = denoise.value
                workflow["54"].inputs.amount = imageCount.value
                workflow["40"].inputs.seed = Math.floor(Math.random() * 9007199254740991)
                workflow["33"].inputs.image = uploadedPath

                workflow["53"].inputs.lora_01 = selectedLoras.value[0]?.path || 'None'
                workflow["53"].inputs.strength_01 = selectedLoras.value[0]?.weight ||0

                workflow["53"].inputs.lora_02 = selectedLoras.value[1]?.path || 'None'
                workflow["53"].inputs.strength_02 = selectedLoras.value[1]?.weight ||0

                workflow["53"].inputs.lora_03 = selectedLoras.value[2]?.path || 'None'
                workflow["53"].inputs.strength_03 = selectedLoras.value[2]?.weight ||0
                
                workflow["53"].inputs.lora_04 = selectedLoras.value[3]?.path || 'None'
                workflow["53"].inputs.strength_04 = selectedLoras.value[3]?.weight ||0



                workflow["save_image_websocket_node"] = {
                    class_type: 'SaveImageWebsocket',
                    inputs: {
                        images: ["14", 0],
                    },
                }

                progressLabel.value = 'Queueing'
                comfyWs = await connectComfyWs()
                if (thisToken !== activeGenerationToken) return

                const queued = await queueComfyPrompt(workflow)
                const promptId = queued?.prompt_id
                if (!promptId) throw new Error('ComfyUI did not return a prompt_id')
                activePromptId = promptId
                progressLabel.value = 'Running'

                let currentNode = ''
                await new Promise((resolve, reject) => {
                    if (!comfyWs) return reject(new Error('WebSocket not connected'))

                    comfyWs.onmessage = async (evt) => {
                        if (thisToken !== activeGenerationToken) return

                        if (typeof evt.data === 'string') {
                            let message
                            try { message = JSON.parse(evt.data) } catch { return }

                            if (message?.type === 'progress') {
                                const v = Number(message?.data?.value)
                                const m = Number(message?.data?.max)
                                if (m > 0) progressPct.value = Math.max(0, Math.min(1, v / m))
                                return
                            }

                            if (message?.type === 'executing') {
                                const data = message?.data
                                if (data?.prompt_id !== activePromptId) return
                                if (data?.node == null) return resolve()
                                currentNode = String(data?.node)
                                return
                            }

                            return
                        }

                        if (currentNode !== 'save_image_websocket_node') return

                        try {
                            const buf = evt.data instanceof ArrayBuffer ? evt.data : await evt.data.arrayBuffer()
                            const imageBytes = buf.slice(8)
                            const blob = new Blob([imageBytes])
                            const url = await new Promise((r) => {
                                const reader = new FileReader()
                                reader.onload = () => r(String(reader.result))
                                reader.readAsDataURL(blob)
                            })

                            generatedImages.value = [...generatedImages.value, url]
                            currentGeneratedIndex.value = generatedImages.value.length - 1
                        } catch {
                            // ignore
                        }
                    }
                    comfyWs.onclose = () => resolve()
                    comfyWs.onerror = (e) => reject(e)
                })

                if (thisToken !== activeGenerationToken) return
                progressPct.value = 1
                progressLabel.value = generatedImages.value.length ? 'Done' : 'Done (no images)'
            } catch (err) {
                if (thisToken !== activeGenerationToken) return
                imageError.value = String(err?.message || err || 'Generation failed')
                progressLabel.value = 'Error'
            } finally {
                if (thisToken !== activeGenerationToken) return
                isGenerating.value = false
                closeComfyWs()
                activePromptId = null
            }
        })()
}

onMounted(async () => {
    resizeCanvases()
    window.addEventListener('resize', fitView)
    onUiUpdate()

    const imageId = route.query?.image
    if (imageId != null && String(imageId).trim() !== '') {
        try {
            const pin = await GetFromApi(`image/${encodeURIComponent(String(imageId))}`)
            if (pin?.Path) {
                await loadImageFromUrl(ImageSrc(pin.Path))
            }
        } catch (e) {
            imageError.value = String(e?.message || e || 'Failed to load image')
        }
    }
})
onBeforeUnmount(() => {
    window.removeEventListener('resize', fitView)
})

watch([canvasWidth, canvasHeight], resizeCanvases)
watch([imageOffsetX, imageOffsetY, imageScale], drawBase)
</script>