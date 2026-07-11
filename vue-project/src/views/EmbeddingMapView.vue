<template>
    <div class="flex h-[calc(100vh-5rem)] overflow-hidden text-[#FAF8F5] font-sans -mx-6">
        <!-- Main Map Area (Left) -->
        <div class="flex-grow relative h-full bg-[#07070a] overflow-hidden select-none">
            <!-- Canvas -->
            <canvas ref="canvasRef" class="w-full h-full block cursor-grab active:cursor-grabbing" @mousedown="onMouseDown"
                @mousemove="onMouseMove" @mouseup="onMouseUp" @wheel="onWheel" @touchstart="onTouchStart"
                @touchmove="onTouchMove" @touchend="onTouchEnd" />

            <!-- Floating Overlay Controls -->
            <div class="absolute top-6 left-6 flex flex-col gap-4 max-w-sm pointer-events-none">
                <!-- Search & Highlight -->
                <div class="bg-[#14141A]/90 backdrop-blur-xl border border-[#2A2A35]/80 p-4 rounded-3xl shadow-2xl pointer-events-auto flex flex-col gap-3">
                    <div class="flex items-center gap-2">
                        <div class="text-[#C9A84C] font-serif italic text-lg font-bold">SigLIP 2 Map</div>
                        <div class="text-[9px] font-mono tracking-widest text-[#FAF8F5]/40 uppercase bg-[#2A2A35]/30 px-2 py-0.5 rounded">Visual Clusters</div>
                    </div>
                    <div class="relative">
                        <input v-model="searchQuery" type="text" placeholder="Highlight tags or filenames..."
                            @input="onSearchInput"
                            class="w-full bg-[#0D0D12] border border-[#2A2A35] focus:border-[#C9A84C]/50 rounded-2xl py-2 pl-4 pr-10 text-xs text-[#FAF8F5] placeholder-[#FAF8F5]/30 focus:outline-none transition-all" />
                        <svg class="absolute right-3.5 top-2.5 w-4 h-4 text-[#FAF8F5]/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </div>
                    <div v-if="searchQuery" class="text-[10px] font-mono text-[#FAF8F5]/50 flex justify-between px-1">
                        <span>Matched Points:</span>
                        <span class="text-[#C9A84C]">{{ matchedCount }} / {{ points.length }}</span>
                    </div>
                </div>

                <!-- Navigation Guide / Map Stats -->
                <div class="bg-[#14141A]/70 backdrop-blur-md border border-[#2A2A35]/40 p-3.5 rounded-2xl shadow-lg text-[10px] font-mono text-[#FAF8F5]/40 flex flex-col gap-1.5">
                    <div class="flex justify-between">
                        <span>Zoom Level:</span>
                        <span class="text-[#FAF8F5]/70">{{ Math.round(zoom * 100) }}%</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Total Points:</span>
                        <span class="text-[#FAF8F5]/70">{{ points.length }}</span>
                    </div>
                    <div class="border-t border-[#2A2A35]/40 my-1"></div>
                    <div class="flex gap-1.5 items-center">
                        <span class="w-1.5 h-1.5 rounded-full bg-[#C9A84C] animate-pulse"></span>
                        <span class="normal-case">Drag to Pan • Scroll to Zoom</span>
                    </div>
                </div>
            </div>

            <!-- Floating Controls (Bottom Left) -->
            <div class="absolute bottom-6 left-6 flex gap-2 pointer-events-auto">
                <button @click="zoomIn" class="w-10 h-10 rounded-full bg-[#14141A]/95 border border-[#2A2A35] flex items-center justify-center text-[#FAF8F5]/80 hover:text-white hover:border-[#C9A84C]/50 transition-all cursor-pointer shadow-lg active:scale-95" title="Zoom In">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
                </button>
                <button @click="zoomOut" class="w-10 h-10 rounded-full bg-[#14141A]/95 border border-[#2A2A35] flex items-center justify-center text-[#FAF8F5]/80 hover:text-white hover:border-[#C9A84C]/50 transition-all cursor-pointer shadow-lg active:scale-95" title="Zoom Out">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4" /></svg>
                </button>
                <button @click="resetView" class="w-10 h-10 rounded-full bg-[#14141A]/95 border border-[#2A2A35] flex items-center justify-center text-[#FAF8F5]/80 hover:text-white hover:border-[#C9A84C]/50 transition-all cursor-pointer shadow-lg active:scale-95" title="Reset View">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H18" /></svg>
                </button>
                <button @click="triggerRebuild" class="h-10 px-4 rounded-full bg-[#14141A]/95 border border-[#2A2A35] flex items-center justify-center text-xs font-mono tracking-wider uppercase text-[#C9A84C]/90 hover:text-[#FAF8F5] hover:border-[#C9A84C]/50 transition-all cursor-pointer shadow-lg active:scale-95 gap-2" :disabled="rebuilding" title="Run UMAP Projection">
                    <svg class="w-3.5 h-3.5 animate-spin" v-if="rebuilding" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>
                    <span>{{ rebuilding ? 'Calculating Map...' : 'Recalculate Map' }}</span>
                </button>
            </div>

            <!-- Tooltip Overlay -->
            <div v-if="hoveredPoint && !panning" :style="{ left: tooltipX + 'px', top: tooltipY + 'px' }"
                class="absolute z-30 -translate-x-1/2 -translate-y-[calc(100%+12px)] pointer-events-none bg-[#14141A] border border-[#2A2A35] p-3 rounded-2xl shadow-2xl flex flex-col items-center gap-2 max-w-[180px]">
                <img :src="apiUrl + hoveredPoint.path" class="w-24 h-24 object-cover rounded-lg shadow" />
                <div class="text-[10px] font-mono text-[#FAF8F5]/80 text-center truncate w-full">{{ hoveredPoint.name }}</div>
                <div class="flex gap-2 text-[9px] font-mono text-[#C9A84C]">
                    <span v-if="hoveredPoint.rating">★ {{ hoveredPoint.rating }}</span>
                    <span v-if="hoveredPoint.likes">♥ {{ hoveredPoint.likes }}</span>
                </div>
            </div>

            <!-- Loading overlay -->
            <div v-if="loading" class="absolute inset-0 bg-[#07070a]/90 backdrop-blur-sm flex flex-col items-center justify-center z-40">
                <div class="relative w-16 h-16 mb-4">
                    <div class="absolute inset-0 rounded-full border-t-2 border-[#C9A84C] border-opacity-20"></div>
                    <div class="absolute inset-0 rounded-full border-t-2 border-[#C9A84C] animate-spin"></div>
                </div>
                <h2 class="text-xl font-serif italic mb-1 text-[#FAF8F5]">Mapping Visual Space</h2>
                <p class="text-xs font-mono text-[#FAF8F5]/40 uppercase tracking-widest">{{ loadingStatus }}</p>
            </div>
        </div>

        <!-- Sidebar Panel (Right) -->
        <div class="w-[340px] border-l border-[#2A2A35]/60 bg-[#0A0A0E] flex flex-col h-full z-20">
            <!-- Header -->
            <div class="p-6 border-b border-[#2A2A35]/40 flex justify-between items-center">
                <div class="text-xs font-mono uppercase tracking-widest text-[#FAF8F5]/50">Image Inspector</div>
                <button v-if="selectedPoint" @click="selectedPoint = null" class="text-xs text-[#FAF8F5]/30 hover:text-[#FAF8F5] cursor-pointer">Clear</button>
            </div>

            <!-- Details -->
            <div class="flex-grow overflow-y-auto p-6 flex flex-col gap-6 custom-scrollbar">
                <div v-if="selectedPoint" class="flex flex-col gap-6">
                    <!-- Image Card -->
                    <div class="relative group rounded-3xl overflow-hidden border border-[#2A2A35] bg-[#14141A]">
                        <img :src="apiUrl + selectedPoint.path" class="w-full aspect-square object-cover" />
                        <div class="absolute bottom-4 right-4 flex gap-2">
                            <RouterLink :to="'/image/' + selectedPoint.id"
                                class="bg-[#14141A]/90 hover:bg-[#FAF8F5] text-[#FAF8F5] hover:text-[#0D0D12] px-4 py-2 rounded-full text-xs font-sans font-semibold tracking-wide border border-[#2A2A35] transition-all flex items-center gap-1.5 shadow-lg">
                                <span>Inspect Details</span>
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                            </RouterLink>
                        </div>
                    </div>

                    <!-- Metadata -->
                    <div class="flex flex-col gap-4 font-mono text-xs">
                        <div class="flex justify-between border-b border-[#2A2A35]/30 pb-2">
                            <span class="text-[#FAF8F5]/40">ID:</span>
                            <span class="text-[#FAF8F5]">{{ selectedPoint.id }}</span>
                        </div>
                        <div class="flex justify-between border-b border-[#2A2A35]/30 pb-2">
                            <span class="text-[#FAF8F5]/40">File:</span>
                            <span class="text-[#FAF8F5] truncate max-w-[200px]" :title="selectedPoint.name">{{ selectedPoint.name }}</span>
                        </div>
                        <div class="flex justify-between border-b border-[#2A2A35]/30 pb-2">
                            <span class="text-[#FAF8F5]/40">Rating:</span>
                            <span class="text-[#FAF8F5]">{{ selectedPoint.rating ? '★ ' + selectedPoint.rating : 'Unrated' }}</span>
                        </div>
                        <div class="flex justify-between border-b border-[#2A2A35]/30 pb-2">
                            <span class="text-[#FAF8F5]/40">Likes:</span>
                            <span class="text-[#FAF8F5]">♥ {{ selectedPoint.likes }}</span>
                        </div>
                    </div>

                    <!-- Action controls -->
                    <div class="flex gap-3">
                        <button @click="likeImage"
                            class="flex-grow py-3 px-4 rounded-2xl border transition-all text-xs font-sans font-semibold cursor-pointer shadow flex items-center justify-center gap-2"
                            :class="isLiked ? 'bg-red-500/10 border-red-500/30 text-red-400' : 'bg-[#14141A] border-[#2A2A35] text-[#FAF8F5]/80 hover:text-white hover:border-[#FAF8F5]/30'">
                            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
                            <span>{{ isLiked ? 'Liked' : 'Like' }}</span>
                        </button>
                    </div>
                </div>

                <!-- Empty State -->
                <div v-else class="flex-grow flex flex-col items-center justify-center text-center p-4">
                    <svg class="w-12 h-12 text-[#FAF8F5]/20 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                    </svg>
                    <h3 class="text-sm font-medium text-[#FAF8F5]/70 mb-1">No Selection</h3>
                    <p class="text-[11px] text-[#FAF8F5]/40 leading-relaxed font-sans max-w-[200px]">Click a node on the map to inspect image parameters and details.</p>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue';
import { GetFromApi, PostToApi, apiUrl } from '../api';

const canvasRef = ref(null);
const loading = ref(true);
const loadingStatus = ref('Fetching layout data...');
const rebuilding = ref(false);

const points = ref([]);
const drawPoints = ref([]);
const matchedIndices = ref(new Set());
const searchQuery = ref('');
const matchedCount = ref(0);

// Selection / Hover
const selectedPoint = ref(null);
const hoveredPoint = ref(null);
const tooltipX = ref(0);
const tooltipY = ref(0);
const isLiked = ref(false);

// Debounce state for camera movements (zero HDD reads during pan/zoom)
const isMoving = ref(false);
let movementTimeout = null;

const startMovement = () => {
    isMoving.value = true;
    if (movementTimeout) {
        clearTimeout(movementTimeout);
    }
    movementTimeout = setTimeout(() => {
        isMoving.value = false;
        requestAnimationFrame(draw);
    }, 250);
};

// View Transformation
const zoom = ref(1.0);
const panX = ref(0);
const panY = ref(0);
const mapSize = 4000; // Virtual width/height of coordinate space

// Interactive Dragging
let panning = false;
let startX = 0;
let startY = 0;

// Thumbnail Images Cache
const thumbnailCache = new Map(); // path -> Image

// Watch selection to check likes
watch(selectedPoint, (newVal) => {
    if (newVal) {
        isLiked.value = newVal.likes > 0;
    }
});

// Canvas Context
let ctx = null;
let animationFrameId = null;

// Sizing
const resizeCanvas = () => {
    const canvas = canvasRef.value;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    draw();
};

// Check if a point is within visible screen bounds
const isPointInViewport = (sx, sy, canvasW, canvasH) => {
    return sx >= -50 && sx <= canvasW + 50 && sy >= -50 && sy <= canvasH + 50;
};

// Main Rendering Logic
const draw = () => {
    const canvas = canvasRef.value;
    if (!canvas) return;
    
    ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    
    ctx.clearRect(0, 0, w, h);
    ctx.save();
    
    // Scale coordinate points based on DPI
    const ratio = window.devicePixelRatio;
    ctx.scale(ratio, ratio);
    
    const viewportW = w / ratio;
    const viewportH = h / ratio;
    
    // Draw background grid lines (subtle dark cyberpunk aesthetic)
    ctx.strokeStyle = '#2A2A35/10';
    ctx.lineWidth = 0.5;
    const gridSpacing = 200 * zoom.value;
    const startGridX = panX.value % gridSpacing;
    const startGridY = panY.value % gridSpacing;
    
    ctx.beginPath();
    for (let x = startGridX; x < viewportW; x += gridSpacing) {
        ctx.moveTo(x, 0);
        ctx.lineTo(x, viewportH);
    }
    for (let y = startGridY; y < viewportH; y += gridSpacing) {
        ctx.moveTo(0, y);
        ctx.lineTo(viewportW, y);
    }
    ctx.stroke();

    // Determine zoom thresholds for detail levels
    // When zoom is high, we can render tiny images!
    const showThumbnails = zoom.value > 1.2 && !isMoving.value;
    const thumbSize = Math.max(16, Math.min(128, 48 * zoom.value));

    // drawPoints is pre-sorted on load/search to prevent frame stutters
    const sortedPoints = drawPoints.value;

    // Viewport culling and centering metric calculations
    const visiblePoints = [];
    for (let i = 0; i < sortedPoints.length; i++) {
        const pt = sortedPoints[i];
        const sx = pt.x * mapSize * zoom.value + panX.value;
        const sy = pt.y * mapSize * zoom.value + panY.value;
        
        if (isPointInViewport(sx, sy, viewportW, viewportH)) {
            visiblePoints.push({
                pt,
                sx,
                sy,
                distToCenter: Math.hypot(sx - viewportW / 2, sy - viewportH / 2)
            });
        }
    }

    // Limit thumbnails drawn concurrently to preserve HDD performance
    const maxThumbnails = 80;
    const thumbnailIdsToDraw = new Set();
    if (showThumbnails && visiblePoints.length > 0) {
        // Sort visible points by distance to viewport center
        const sortedVisible = [...visiblePoints].sort((a, b) => a.distToCenter - b.distToCenter);
        const closestVisible = sortedVisible.slice(0, maxThumbnails);
        closestVisible.forEach(item => {
            thumbnailIdsToDraw.add(item.pt.id);
        });
    }

    // Render visible points
    for (let i = 0; i < visiblePoints.length; i++) {
        const { pt, sx, sy } = visiblePoints[i];

        const isMatch = searchQuery.value ? matchedIndices.value.has(pt.id) : true;
        const isSelected = selectedPoint.value && selectedPoint.value.id === pt.id;
        const isHovered = hoveredPoint.value && hoveredPoint.value.id === pt.id;
        
        let alpha = 1.0;
        if (searchQuery.value && !isMatch) {
            alpha = 0.12; // Dim non-matched points
        }
        
        ctx.globalAlpha = alpha;

        const drawAsThumbnail = showThumbnails && thumbnailIdsToDraw.has(pt.id);

        if (drawAsThumbnail) {
            // Load tiny 128px cached JPEGs instead of original full-resolution files
            const thumbPath = `/image-thumbnail/${pt.id}?size=128`;
            const cachedImage = thumbnailCache.get(thumbPath);
            
            if (cachedImage) {
                if (cachedImage.complete) {
                    ctx.save();
                    ctx.strokeStyle = isSelected ? '#C9A84C' : isHovered ? '#FAF8F5' : '#2A2A35';
                    ctx.lineWidth = isSelected ? 3 : isHovered ? 2 : 1;
                    
                    ctx.beginPath();
                    ctx.arc(sx, sy, thumbSize / 2, 0, Math.PI * 2);
                    ctx.stroke();
                    ctx.clip();
                    
                    ctx.drawImage(cachedImage, sx - thumbSize / 2, sy - thumbSize / 2, thumbSize, thumbSize);
                    ctx.restore();
                } else {
                    drawPointDot(ctx, sx, sy, pt, isSelected, isHovered, alpha);
                }
            } else {
                const imgEl = new Image();
                imgEl.src = apiUrl + thumbPath;
                imgEl.onload = () => requestAnimationFrame(draw);
                thumbnailCache.set(thumbPath, imgEl);
                
                drawPointDot(ctx, sx, sy, pt, isSelected, isHovered, alpha);
            }
        } else {
            drawPointDot(ctx, sx, sy, pt, isSelected, isHovered, alpha);
        }
    }
    
    ctx.globalAlpha = 1.0;
    ctx.restore();
};

const drawPointDot = (ctx, sx, sy, pt, isSelected, isHovered, alpha) => {
    const size = isSelected ? 8 : isHovered ? 6 : 4;
    
    // Choose color: Likes = gold, Unliked = cyan/blue
    let color = '#3b82f6'; // default blue
    if (pt.likes > 0) {
        color = '#C9A84C'; // gold for liked
    } else if (pt.rating > 4) {
        color = '#10b981'; // green for high rating
    }
    
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(sx, sy, size, 0, Math.PI * 2);
    ctx.fill();
    
    if (isSelected || isHovered) {
        ctx.strokeStyle = '#FAF8F5';
        ctx.lineWidth = 1.5;
        ctx.stroke();
    }
};

// Pointer Events (Zoom & Pan)
const onMouseDown = (evt) => {
    // Left click only
    if (evt.button !== 0) return;
    
    const canvas = canvasRef.value;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const ratio = window.devicePixelRatio;
    const mx = (evt.clientX - rect.left);
    const my = (evt.clientY - rect.top);
    
    // Check if clicked a point
    const clickedPt = findPointAt(mx, my);
    
    if (clickedPt) {
        selectedPoint.value = clickedPt;
    } else {
        panning = true;
        startX = evt.clientX - panX.value;
        startY = evt.clientY - panY.value;
    }
};

const onMouseMove = (evt) => {
    const canvas = canvasRef.value;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const mx = (evt.clientX - rect.left);
    const my = (evt.clientY - rect.top);
    
    if (panning) {
        panX.value = evt.clientX - startX;
        panY.value = evt.clientY - startY;
        startMovement();
        requestAnimationFrame(draw);
    } else {
        // Update hovered point
        const pt = findPointAt(mx, my);
        if (pt) {
            hoveredPoint.value = pt;
            tooltipX.value = evt.clientX - rect.left;
            tooltipY.value = evt.clientY - rect.top;
        } else {
            hoveredPoint.value = null;
        }
        requestAnimationFrame(draw);
    }
};

const onMouseUp = () => {
    panning = false;
};

// Touch Gestures
let touchStartDist = 0;
let lastTouchX = 0;
let lastTouchY = 0;

const getTouchDist = (touch1, touch2) => {
    return Math.hypot(touch2.clientX - touch1.clientX, touch2.clientY - touch1.clientY);
};

const onTouchStart = (evt) => {
    if (evt.touches.length === 1) {
        const touch = evt.touches[0];
        panning = true;
        startX = touch.clientX - panX.value;
        startY = touch.clientY - panY.value;
    } else if (evt.touches.length === 2) {
        panning = false;
        touchStartDist = getTouchDist(evt.touches[0], evt.touches[1]);
        lastTouchX = (evt.touches[0].clientX + evt.touches[1].clientX) / 2;
        lastTouchY = (evt.touches[0].clientY + evt.touches[1].clientY) / 2;
    }
};

const onTouchMove = (evt) => {
    if (panning && evt.touches.length === 1) {
        const touch = evt.touches[0];
        panX.value = touch.clientX - startX;
        panY.value = touch.clientY - startY;
        startMovement();
        requestAnimationFrame(draw);
    } else if (evt.touches.length === 2) {
        const dist = getTouchDist(evt.touches[0], evt.touches[1]);
        const scaleFactor = dist / touchStartDist;
        
        const midX = (evt.touches[0].clientX + evt.touches[1].clientX) / 2;
        const midY = (evt.touches[0].clientY + evt.touches[1].clientY) / 2;
        
        zoomTo(scaleFactor, midX, midY);
        
        panX.value += midX - lastTouchX;
        panY.value += midY - lastTouchY;
        
        lastTouchX = midX;
        lastTouchY = midY;
        touchStartDist = dist;
        startMovement();
        requestAnimationFrame(draw);
    }
};

const onTouchEnd = () => {
    panning = false;
    touchStartDist = 0;
};

const onWheel = (evt) => {
    evt.preventDefault();
    
    const canvas = canvasRef.value;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const mouseX = evt.clientX - rect.left;
    const mouseY = evt.clientY - rect.top;
    
    const zoomFactor = evt.deltaY < 0 ? 1.1 : 0.9;
    zoomTo(zoomFactor, mouseX, mouseY);
    startMovement();
    requestAnimationFrame(draw);
};

const zoomTo = (factor, centerX, centerY) => {
    const newZoom = Math.max(0.15, Math.min(15.0, zoom.value * factor));
    
    // Zoom centered on pointer location
    panX.value = centerX - (centerX - panX.value) * (newZoom / zoom.value);
    panY.value = centerY - (centerY - panY.value) * (newZoom / zoom.value);
    
    zoom.value = newZoom;
};

const zoomIn = () => {
    const canvas = canvasRef.value;
    if (!canvas) return;
    zoomTo(1.25, canvas.width / 2 / window.devicePixelRatio, canvas.height / 2 / window.devicePixelRatio);
    startMovement();
    requestAnimationFrame(draw);
};

const zoomOut = () => {
    const canvas = canvasRef.value;
    if (!canvas) return;
    zoomTo(0.8, canvas.width / 2 / window.devicePixelRatio, canvas.height / 2 / window.devicePixelRatio);
    startMovement();
    requestAnimationFrame(draw);
};

const resetView = () => {
    const canvas = canvasRef.value;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    zoom.value = Math.min(rect.width, rect.height) / mapSize * 0.9;
    panX.value = (rect.width - mapSize * zoom.value) / 2;
    panY.value = (rect.height - mapSize * zoom.value) / 2;
    startMovement();
    requestAnimationFrame(draw);
};

// Locate point under pointer coordinates
const findPointAt = (mx, my) => {
    const clickRadius = Math.max(12, 10 * zoom.value); // expand hit box if zoomed out
    
    for (let i = 0; i < points.value.length; i++) {
        const pt = points.value[i];
        const sx = pt.x * mapSize * zoom.value + panX.value;
        const sy = pt.y * mapSize * zoom.value + panY.value;
        const dist = Math.hypot(mx - sx, my - sy);
        
        if (dist <= clickRadius) {
            return pt;
        }
    }
    return null;
};

// Search Highlight
const onSearchInput = () => {
    if (!searchQuery.value) {
        matchedIndices.value.clear();
        matchedCount.value = 0;
        drawPoints.value = [...points.value];
        requestAnimationFrame(draw);
        return;
    }
    
    const query = searchQuery.value.toLowerCase().trim();
    matchedIndices.value.clear();
    
    points.value.forEach(pt => {
        const promptText = (pt.prompt || '').toLowerCase();
        const nameText = (pt.name || '').toLowerCase();
        if (promptText.includes(query) || nameText.includes(query)) {
            matchedIndices.value.add(pt.id);
        }
    });
    
    matchedCount.value = matchedIndices.value.size;
    
    // Pre-sort drawPoints once: matches drawn last (on top)
    drawPoints.value = [...points.value].sort((a, b) => {
        const aMatch = matchedIndices.value.has(a.id) ? 1 : 0;
        const bMatch = matchedIndices.value.has(b.id) ? 1 : 0;
        return aMatch - bMatch;
    });
    
    requestAnimationFrame(draw);
};

// Rebuild UMAP
const triggerRebuild = async () => {
    rebuilding.value = true;
    try {
        await PostToApi("ai-search/rebuild-siglip-map");
        loadingStatus.value = 'UMAP is running on server...';
        loading.value = true;
        // Start polling coords file status
        pollCoordsRebuild();
    } catch (e) {
        console.error("Error rebuilding map coords:", e);
        rebuilding.value = false;
    }
};

const pollCoordsRebuild = () => {
    const interval = setInterval(async () => {
        try {
            // Check status of SigLIP indexer as UMAP is linked
            const status = await GetFromApi("ai-search/siglip-status");
            if (status.status !== 'running') {
                clearInterval(interval);
                rebuilding.value = false;
                await loadMapData();
            }
        } catch (e) {
            clearInterval(interval);
            rebuilding.value = false;
            loading.value = false;
        }
    }, 1500);
};

// Like selected image
const likeImage = async () => {
    if (!selectedPoint.value) return;
    try {
        const iid = selectedPoint.value.id;
        const res = await PostToApi(`like/${iid}`);
        if (res) {
            isLiked.value = !isLiked.value;
            selectedPoint.value.likes = isLiked.value ? 1 : 0;
            // update original points entry
            const pt = points.value.find(p => p.id === iid);
            if (pt) {
                pt.likes = selectedPoint.value.likes;
            }
            requestAnimationFrame(draw);
        }
    } catch (e) {
        console.error("Error liking image:", e);
    }
};

// Load Map Data
const loadMapData = async () => {
    loading.value = true;
    loadingStatus.value = 'Downloading coordinates...';
    try {
        const res = await GetFromApi("ai-search/siglip-map");
        if (res) {
            points.value = res;
            drawPoints.value = [...res];
            nextTick(() => {
                resetView();
                loading.value = false;
            });
        }
    } catch (e) {
        console.error("Failed to load map data:", e);
        loadingStatus.value = 'Failed to load coordinates. Rebuilding...';
        // Try trigger UMAP coordinates calculation if missing
        await triggerRebuild();
    }
};

onMounted(() => {
    window.addEventListener('resize', resizeCanvas);
    loadMapData();
    // Delay canvas size initialization
    setTimeout(resizeCanvas, 200);
});

onBeforeUnmount(() => {
    window.removeEventListener('resize', resizeCanvas);
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
    }
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
    width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #2a2a35;
    border-radius: 2px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #C9A84C;
}
</style>
