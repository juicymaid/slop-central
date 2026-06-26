<template>
    <div
        class="flex h-screen w-full flex-col bg-[#0D0D12] text-[#FAF8F5] overflow-hidden selection:bg-[#C9A84C]/30 fixed inset-0 pt-16 font-sans">

        <div class="flex flex-1 min-h-0 relative">

            <!-- Main Canvas Viewport -->
            <main ref="viewportRef" class="relative flex-1 overflow-hidden bg-[#07070A]" @wheel.prevent="onWheel">
                <!-- Premium Gold Radial Grid Pattern -->
                <div class="absolute inset-0 pointer-events-none opacity-10"
                    style="background-image: radial-gradient(#C9A84C 1px, transparent 1px); background-size: 24px 24px;">
                </div>

                <div v-if="!hasImage"
                    class="absolute inset-0 flex flex-col items-center justify-center text-zinc-500 pointer-events-none space-y-4">
                    <div class="h-16 w-16 rounded-full border border-[#C9A84C]/20 flex items-center justify-center bg-[#C9A84C]/5 shadow-[0_0_20px_rgba(201,168,76,0.1)]">
                        <svg class="w-8 h-8 text-[#C9A84C]/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                        </svg>
                    </div>
                    <p class="text-xs uppercase tracking-[0.2em] text-[#C9A84C]/70">Upload an image to start tailoring</p>
                </div>

                <!-- Floating Canvas Container -->
                <div class="absolute inset-0 overflow-auto flex items-center justify-center p-12 outline-none mb-12"
                    ref="scrollContainerRef">
                    <div v-if="hasImage"
                        class="relative transition-transform duration-75 ease-out origin-center shadow-[0_20px_50px_rgba(0,0,0,0.8)] border border-[#C9A84C]/10"
                        :style="{
                            width: canvasWidth + 'px',
                            height: canvasHeight + 'px',
                            transform: `scale(${zoom})`
                        }" @pointerleave="onPointerUp">
                        
                        <!-- Base canvas (contains uploaded image) -->
                        <canvas ref="baseCanvasRef" class="block bg-zinc-900 pointer-events-none" />

                        <!-- Preview of generated replacement -->
                        <img v-if="hasGeneratedPreview" :src="currentGeneratedImage"
                            class="absolute left-0 top-0 h-full w-full pointer-events-none object-contain" />

                        <!-- Mask canvas (for painting / SAM overlay) -->
                        <canvas ref="maskCanvasRef" class="absolute left-0 top-0 touch-none"
                            :class="[cursorClass, hasGeneratedPreview ? 'opacity-0 pointer-events-none' : 'opacity-100']"
                            @pointerdown="onPointerDown" @pointermove="onPointerMove" @pointerup="onPointerUp"
                            @pointercancel="onPointerUp" @contextmenu.prevent />

                        <!-- Resize Handles with luxury theme -->
                        <div class="pointer-events-none absolute -inset-[1px] border border-[#C9A84C]/35 z-50">
                            <div class="absolute inset-0 border border-white/5"></div>

                            <!-- Left handle -->
                            <div class="pointer-events-auto absolute left-0 top-0 h-full w-6 -translate-x-3 cursor-ew-resize group flex items-center justify-center"
                                @pointerdown="(e) => onResizeHandleDown(e, 'l')">
                                <div
                                    class="h-10 w-1 rounded-full bg-transparent group-hover:bg-[#C9A84C] transition-all duration-300 shadow-[0_0_8px_rgba(201,168,76,0.8)]">
                                </div>
                            </div>

                            <!-- Right handle -->
                            <div class="pointer-events-auto absolute right-0 top-0 h-full w-6 translate-x-3 cursor-ew-resize group flex items-center justify-center"
                                @pointerdown="(e) => onResizeHandleDown(e, 'r')">
                                <div
                                    class="h-10 w-1 rounded-full bg-transparent group-hover:bg-[#C9A84C] transition-all duration-300 shadow-[0_0_8px_rgba(201,168,76,0.8)]">
                                </div>
                            </div>

                            <!-- Top handle -->
                            <div class="pointer-events-auto absolute left-0 top-0 w-full h-6 -translate-y-3 cursor-ns-resize group flex items-center justify-center"
                                @pointerdown="(e) => onResizeHandleDown(e, 't')">
                                <div
                                    class="w-10 h-1 rounded-full bg-transparent group-hover:bg-[#C9A84C] transition-all duration-300 shadow-[0_0_8px_rgba(201,168,76,0.8)]">
                                </div>
                            </div>

                            <!-- Bottom handle -->
                            <div class="pointer-events-auto absolute left-0 bottom-0 w-full h-6 translate-y-3 cursor-ns-resize group flex items-center justify-center"
                                @pointerdown="(e) => onResizeHandleDown(e, 'b')">
                                <div
                                    class="w-10 h-1 rounded-full bg-transparent group-hover:bg-[#C9A84C] transition-all duration-300 shadow-[0_0_8px_rgba(201,168,76,0.8)]">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Floating Glassmorphic Viewport Zoom / Reset Controls -->
                <div v-if="hasImage" 
                    class="absolute bottom-6 right-6 z-20 flex items-center gap-2 bg-[#0D0D12]/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-[#2A2A35]/40 shadow-[0_10px_30px_rgba(0,0,0,0.5)]">
                    <button @click="setZoom(zoom - 0.1)" class="text-zinc-400 hover:text-[#C9A84C] transition-colors p-1" title="Zoom Out">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"/></svg>
                    </button>
                    <span class="w-14 text-center tabular-nums text-[11px] font-mono font-medium text-zinc-300">{{ Math.round(zoom * 100) }}%</span>
                    <button @click="setZoom(zoom + 0.1)" class="text-zinc-400 hover:text-[#C9A84C] transition-colors p-1" title="Zoom In">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                    </button>
                    <div class="w-[1px] h-4 bg-[#2A2A35]/50 mx-1"></div>
                    <button @click="fitView" class="text-zinc-400 hover:text-[#C9A84C] transition-colors text-[10px] font-semibold px-1 uppercase tracking-wider">
                        Fit
                    </button>
                </div>

                <!-- Premium Glassmorphic Loading Overlay for SAM Segmentation -->
                <div v-if="isSegmenting"
                    class="absolute inset-0 bg-[#0D0D12]/75 backdrop-blur-[4px] z-40 flex flex-col items-center justify-center transition-all duration-300">
                    <div class="bg-[#0D0D12] border border-[#C9A84C]/20 p-8 rounded-xl shadow-[0_20px_60px_rgba(0,0,0,0.8)] flex flex-col items-center gap-4 max-w-sm text-center relative overflow-hidden">
                        <div class="absolute -right-16 -top-16 w-32 h-32 bg-[#C9A84C]/5 rounded-full blur-2xl"></div>
                        
                        <!-- Luxury Golden Spinner -->
                        <div class="relative w-16 h-16">
                            <div class="absolute inset-0 rounded-full border-2 border-[#C9A84C]/10"></div>
                            <div class="absolute inset-0 rounded-full border-2 border-t-[#C9A84C] animate-spin"></div>
                            <div class="absolute inset-2 rounded-full border border-dashed border-[#C9A84C]/30 animate-[spin_10s_linear_infinite_reverse]"></div>
                        </div>
                        
                        <div class="space-y-1 mt-2">
                            <h3 class="text-xs uppercase font-bold tracking-[0.15em] text-[#FAF8F5]">AI Segmenting</h3>
                            <p class="text-[10px] font-mono tracking-widest text-[#C9A84C] uppercase">{{ samProgressLabel }}</p>
                        </div>
                        
                        <div class="w-48 h-1 bg-[#2A2A35]/30 rounded-full overflow-hidden mt-1">
                            <div class="h-full bg-gradient-to-r from-[#C9A84C] to-[#E3C77D] transition-all duration-300"
                                :style="{ width: `${Math.round(samProgressPct * 100)}%` }">
                            </div>
                        </div>
                        
                        <button @click="denyOrCancel"
                            class="mt-4 px-4 py-1.5 rounded border border-[#2A2A35] text-[10px] uppercase tracking-wider text-zinc-400 hover:text-red-400 hover:border-red-500/30 transition-all duration-200">
                            Cancel Process
                        </button>
                    </div>
                </div>
            </main>

            <!-- Luxury Workspace Sidebar -->
            <aside
                class="w-[340px] shrink-0 border-l border-[#2A2A35]/30 bg-[#0D0D12] flex flex-col z-10 shadow-[0_0_40px_rgba(0,0,0,0.8)] select-none">
                
                <!-- Sidebar Header -->
                <div class="p-5 border-b border-[#2A2A35]/20 space-y-3 bg-[#09090D]">
                    <div class="flex flex-col gap-1">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2.5">
                                <div class="h-5 w-5 rounded-full border border-[#C9A84C] flex items-center justify-center bg-[#C9A84C]/10 shadow-[0_0_8px_rgba(201,168,76,0.3)]">
                                    <div class="h-1.5 w-1.5 rounded-full bg-[#C9A84C]"></div>
                                </div>
                                <span class="font-bold uppercase tracking-[0.12em] text-[#FAF8F5] text-xs font-sans">Inpaint Studio</span>
                            </div>
                            <span class="text-[9px] uppercase tracking-[0.18em] text-[#C9A84C] font-mono">Atelier v1.1</span>
                        </div>
                        <div class="flex items-center justify-between text-[11px] text-[#2A2A35] border-t border-[#2A2A35]/20 pt-2 mt-1">
                            <span class="italic text-zinc-500 font-serif">Fine Canvas Refining</span>
                            <span class="font-mono text-zinc-400" v-if="hasImage">{{ canvasWidth }} × {{ canvasHeight }}px</span>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-2 pt-1">
                        <button
                            class="rounded border border-[#2A2A35] py-2 text-xs font-semibold uppercase tracking-wider text-zinc-300 hover:text-white hover:border-[#C9A84C]/40 bg-transparent transition-all duration-300 disabled:opacity-30"
                            :disabled="!hasImage || isGenerating" @click="fitView">
                            Fit Canvas
                        </button>
                        
                        <button
                            class="w-full rounded bg-gradient-to-r from-[#C9A84C] to-[#E3C77D] py-2 text-xs font-bold uppercase tracking-wider text-[#0D0D12] hover:from-[#E3C77D] hover:to-[#C9A84C] transition-all duration-300 shadow-[0_4px_12px_rgba(201,168,76,0.15)] hover:shadow-[0_4px_16px_rgba(201,168,76,0.3)] disabled:opacity-30"
                            :disabled="!hasImage || isGenerating || isSegmenting" @click="generatePreview">
                            {{ isGenerating ? 'Refining…' : 'Generate' }}
                        </button>
                    </div>

                    <!-- Progress bar for regular generation -->
                    <div v-if="isGenerating" class="space-y-1.5 pt-1.5">
                        <div class="flex justify-between text-[10px] font-mono uppercase tracking-wider text-zinc-400">
                            <span>{{ progressLabel }}</span>
                            <span class="text-[#C9A84C] font-semibold">{{ Math.round(progressPct * 100) }}%</span>
                        </div>
                        <div class="h-1 w-full rounded bg-[#2A2A35]/30 overflow-hidden">
                            <div class="h-full bg-gradient-to-r from-[#C9A84C] to-[#E3C77D]" :style="{ width: `${Math.round(progressPct * 100)}%` }">
                            </div>
                        </div>
                    </div>
                </div>

                <div class="flex-1 overflow-y-auto p-5 space-y-6">
                    <!-- Source Selection -->
                    <div class="space-y-2">
                        <h3 class="text-[10px] font-bold uppercase tracking-[0.15em] text-[#C9A84C]">Canvas Source</h3>
                        <label
                            class="flex w-full cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-[#2A2A35] bg-[#0A0A0F]/50 hover:bg-[#C9A84C]/5 hover:border-[#C9A84C]/40 transition-all duration-300 h-20 group relative overflow-hidden">
                            <div class="absolute inset-0 bg-gradient-to-br from-transparent to-[#C9A84C]/2 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                            <div class="flex items-center gap-2.5 z-10">
                                <svg class="h-4.5 w-4.5 text-zinc-400 group-hover:text-[#C9A84C] transition-colors duration-300" fill="none"
                                    stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
                                </svg>
                                <span class="text-xs uppercase tracking-wider text-zinc-400 group-hover:text-[#FAF8F5] transition-colors duration-300">Upload Canvas Image</span>
                            </div>
                            <input type="file" class="hidden" accept="image/*" @change="onPickFile" />
                        </label>
                        <div v-if="imageError" class="text-xs font-medium text-red-400 px-1">{{ imageError }}</div>
                    </div>

                    <!-- Tools Section: Paint vs SAM Segment -->
                    <div class="space-y-4">
                        <div class="flex justify-between items-center">
                            <h3 class="text-[10px] font-bold uppercase tracking-[0.15em] text-[#C9A84C]">Mask Strategy</h3>
                        </div>

                        <!-- Elegant Tab Switcher -->
                        <div class="grid grid-cols-2 gap-1 bg-[#050508] p-1 rounded-md border border-[#2A2A35]/30">
                            <button @click="activeTab = 'manual'"
                                class="flex items-center justify-center gap-2 rounded py-2 text-[10px] font-bold uppercase tracking-wider transition-all duration-300"
                                :class="activeTab === 'manual' ? 'bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/20 shadow-sm' : 'text-zinc-500 hover:text-zinc-300'">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>
                                Brush Tool
                            </button>
                            <button @click="activeTab = 'sam'"
                                class="flex items-center justify-center gap-2 rounded py-2 text-[10px] font-bold uppercase tracking-wider transition-all duration-300"
                                :class="activeTab === 'sam' ? 'bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/20 shadow-sm' : 'text-zinc-500 hover:text-zinc-300'">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
                                AI SAM Tool
                            </button>
                        </div>

                        <!-- Tab 1: Manual Brush Tools -->
                        <div v-show="activeTab === 'manual'" class="space-y-4 pt-1">
                            <div class="space-y-2">
                                <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Brush Mode</span>
                                <div class="grid grid-cols-2 gap-1 rounded bg-[#050508] p-1 border border-[#2A2A35]/30">
                                    <button @click="mode = 'paint'"
                                        class="flex items-center justify-center rounded py-1.5 text-[10px] font-bold uppercase tracking-wider transition-all duration-300"
                                        :class="mode === 'paint' ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/20 shadow-sm' : 'text-zinc-500 hover:text-zinc-300'">Paint</button>
                                    <button @click="mode = 'erase'"
                                        class="flex items-center justify-center rounded py-1.5 text-[10px] font-bold uppercase tracking-wider transition-all duration-300"
                                        :class="mode === 'erase' ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/20 shadow-sm' : 'text-zinc-500 hover:text-zinc-300'">Erase</button>
                                </div>
                            </div>

                            <div class="space-y-1.5 p-3 rounded-lg bg-[#07070A]/50 border border-[#2A2A35]/15">
                                <div class="flex justify-between text-[11px]">
                                    <span class="text-zinc-400 font-medium uppercase tracking-wider">Brush Size</span>
                                    <span class="text-[#C9A84C] font-mono font-semibold">{{ brushSize }}px</span>
                                </div>
                                <input v-model.number="brushSize" type="range" min="1" max="300"
                                    class="custom-slider w-full" />
                            </div>

                            <!-- Transform dimensions and offsets -->
                            <div class="p-3 rounded-lg bg-[#07070A]/50 border border-[#2A2A35]/15 space-y-3">
                                <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Transform Canvas</span>
                                <div class="grid grid-cols-2 gap-2 text-xs">
                                    <div>
                                        <label class="text-zinc-500 block mb-1 text-[9px] uppercase tracking-wider">Canvas W</label>
                                        <input v-model.number="canvasWidth" type="number"
                                            class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded px-2.5 py-1 text-zinc-300 text-xs focus:outline-none focus:border-[#C9A84C]/40">
                                    </div>
                                    <div>
                                        <label class="text-zinc-500 block mb-1 text-[9px] uppercase tracking-wider">Canvas H</label>
                                        <input v-model.number="canvasHeight" type="number"
                                            class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded px-2.5 py-1 text-zinc-300 text-xs focus:outline-none focus:border-[#C9A84C]/40">
                                    </div>
                                    <div>
                                        <label class="text-zinc-500 block mb-1 text-[9px] uppercase tracking-wider">Offset X</label>
                                        <input v-model.number="imageOffsetX" type="number"
                                            class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded px-2.5 py-1 text-zinc-300 text-xs focus:outline-none focus:border-[#C9A84C]/40">
                                    </div>
                                    <div>
                                        <label class="text-zinc-500 block mb-1 text-[9px] uppercase tracking-wider">Offset Y</label>
                                        <input v-model.number="imageOffsetY" type="number"
                                            class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded px-2.5 py-1 text-zinc-300 text-xs focus:outline-none focus:border-[#C9A84C]/40">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Tab 2: AI SAM Segmenter Tools -->
                        <div v-show="activeTab === 'sam'" class="space-y-4 pt-1">
                            <div class="space-y-2">
                                <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Segment Prompt</span>
                                <textarea v-model="samPrompt"
                                    class="w-full resize-none rounded-lg bg-[#050508] p-3 text-xs text-[#FAF8F5] placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-[#C9A84C]/50 border border-[#2A2A35] transition-all duration-300"
                                    rows="3" placeholder="Identify segment e.g. clothes, hair, skin..."></textarea>
                                
                                <!-- Premium Preset tags -->
                                <div class="space-y-1">
                                    <span class="text-[9px] font-semibold uppercase tracking-wider text-zinc-500">Quick Presets</span>
                                    <div class="flex flex-wrap gap-1">
                                        <button v-for="preset in samPresets" :key="preset.name"
                                            @click="selectPreset(preset.prompt)"
                                            :class="samPrompt.includes(preset.prompt) ? 'bg-[#C9A84C]/15 text-[#C9A84C] border-[#C9A84C]/40 shadow-[0_0_8px_rgba(201,168,76,0.15)]' : 'bg-transparent text-zinc-400 border-[#2A2A35] hover:border-[#C9A84C]/35 hover:text-zinc-200'"
                                            class="text-[9px] px-2 py-0.5 rounded border transition-all duration-250 font-mono tracking-tight uppercase">
                                            {{ preset.name }}
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <div class="p-3 rounded-lg bg-[#07070A]/50 border border-[#2A2A35]/15 space-y-4">
                                <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-500">SAM Parameters</span>
                                
                                <div class="space-y-1.5">
                                    <div class="flex justify-between text-[10px]">
                                        <span class="text-zinc-400">Threshold</span>
                                        <span class="text-[#C9A84C] font-mono font-semibold">{{ samThreshold.toFixed(2) }}</span>
                                    </div>
                                    <input v-model.number="samThreshold" type="range" min="0.05" max="1" step="0.05"
                                        class="custom-slider w-full" />
                                </div>

                                <div class="space-y-1.5">
                                    <div class="flex justify-between text-[10px]">
                                        <span class="text-zinc-400">Refine Iterations</span>
                                        <span class="text-[#C9A84C] font-mono font-semibold">{{ samRefineIterations }}</span>
                                    </div>
                                    <input v-model.number="samRefineIterations" type="range" min="0" max="10" step="1"
                                        class="custom-slider w-full" />
                                </div>

                                <div class="space-y-2">
                                    <span class="text-[9px] uppercase tracking-wider text-zinc-500">Mask Insertion Mode</span>
                                    <div class="grid grid-cols-2 gap-1 rounded bg-[#050508] p-1 border border-[#2A2A35]/30">
                                        <button @click="samMaskMode = 'replace'"
                                            class="flex items-center justify-center rounded py-1.5 text-[9px] font-bold uppercase tracking-wider transition-all duration-300"
                                            :class="samMaskMode === 'replace' ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/20 shadow-sm' : 'text-zinc-500 hover:text-zinc-300'">Replace</button>
                                        <button @click="samMaskMode = 'add'"
                                            class="flex items-center justify-center rounded py-1.5 text-[9px] font-bold uppercase tracking-wider transition-all duration-300"
                                            :class="samMaskMode === 'add' ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/20 shadow-sm' : 'text-zinc-500 hover:text-zinc-300'">Append</button>
                                    </div>
                                </div>

                                <div class="flex items-center justify-between border-t border-[#2A2A35]/15 pt-2.5 mt-2">
                                    <span class="text-[9px] uppercase tracking-wider text-zinc-400 font-semibold">Invert SAM Mask</span>
                                    <label class="relative inline-flex items-center cursor-pointer">
                                        <input type="checkbox" v-model="samInvertMask" class="sr-only peer">
                                        <div class="w-8 h-4 bg-[#181822] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-[#FAF8F5] after:border-[#2A2A35] after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-[#C9A84C] border border-[#2A2A35]/50"></div>
                                    </label>
                                </div>
                            </div>

                            <button @click="runSamSegmentation"
                                class="w-full rounded border border-[#C9A84C]/35 bg-[#C9A84C]/5 py-2.5 text-xs font-bold uppercase tracking-[0.08em] text-[#C9A84C] hover:bg-[#C9A84C]/10 transition-all duration-300 disabled:opacity-30 flex items-center justify-center gap-2 shadow-[0_4px_16px_rgba(201,168,76,0.05)] hover:shadow-[0_4px_20px_rgba(201,168,76,0.15)]"
                                :disabled="!hasImage || isSegmenting || isGenerating">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                                Extract Segment
                            </button>
                        </div>

                        <button @click="clearMask"
                            class="w-full rounded border border-[#2A2A35] bg-transparent py-2 text-xs font-semibold uppercase tracking-wider text-zinc-400 hover:bg-[#2A2A35]/15 hover:text-zinc-200 transition-colors disabled:opacity-30"
                            :disabled="!hasImage">Clear Mask</button>
                    </div>

                    <!-- Generation Panel -->
                    <div class="space-y-4 border-t border-[#2A2A35]/20 pt-6">
                        <h3 class="text-[10px] font-bold uppercase tracking-[0.15em] text-[#C9A84C]">Generation Parameters</h3>
                        
                        <div class="space-y-2">
                            <label class="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Inpainting Prompt</label>
                            <textarea id="positive_prompt" v-model="prompt"
                                class="positive_prompt w-full resize-none rounded-lg bg-[#050508] p-3 text-xs text-[#FAF8F5] placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-[#C9A84C]/50 border border-[#2A2A35] transition-all duration-300"
                                rows="3" placeholder="Describe the replacement detail..."></textarea>
                        </div>

                        <div class="space-y-1.5 p-3 rounded-lg bg-[#07070A]/50 border border-[#2A2A35]/15">
                            <div class="flex justify-between text-[11px]">
                                <span class="text-zinc-400 font-medium uppercase tracking-wider">Denoising Strength</span>
                                <span class="text-[#C9A84C] font-mono font-semibold">{{ denoise.toFixed(2) }}</span>
                            </div>
                            <input v-model.number="denoise" type="range" min="0" max="1" step="0.01"
                                class="custom-slider w-full" />
                        </div>

                        <div class="space-y-1.5 p-3 rounded-lg bg-[#07070A]/50 border border-[#2A2A35]/15">
                            <div class="flex justify-between text-[11px]">
                                <span class="text-zinc-400 font-medium uppercase tracking-wider">Batch Size</span>
                                <span class="text-[#C9A84C] font-mono font-semibold">{{ imageCount }}</span>
                            </div>
                            <input v-model.number="imageCount" type="range" min="1" max="8" step="1"
                                class="custom-slider w-full" :disabled="isGenerating" />
                        </div>

                        <!-- Loras section -->
                        <div class="space-y-2.5">
                            <div class="flex justify-between items-center">
                                <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-500">Loras ({{ selectedLoras.length }}/{{ maxLoras }})</span>
                                <button
                                    class="rounded border border-[#C9A84C]/25 bg-transparent px-2.5 py-1 text-[9px] uppercase tracking-wider text-[#C9A84C] hover:bg-[#C9A84C]/5 transition-all duration-300 disabled:opacity-30 font-semibold"
                                    :disabled="isGenerating || selectedLoras.length >= maxLoras || !loras?.length"
                                    @click="selectedLoras.push({ name: loras[0].name, path: loras[0].path, weight: 1 })">
                                    + Add Lora
                                </button>
                            </div>

                            <div
                                v-for="(lora, idx) in selectedLoras"
                                :key="`${lora?.path || 'lora'}-${idx}`"
                                class="rounded bg-[#050508] p-3 text-xs border border-[#2A2A35]/30 space-y-2.5 relative group">
                                
                                <div class="flex items-center gap-2">
                                    <select
                                        class="flex-1 bg-[#0D0D12] border border-[#2A2A35] rounded px-2 py-1 text-zinc-300 focus:outline-none focus:border-[#C9A84C]/50 text-xs transition-colors"
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
                                        class="text-zinc-500 hover:text-red-400 transition-colors text-lg leading-none px-1"
                                        :disabled="isGenerating"
                                        @click="selectedLoras.splice(idx, 1)"
                                        aria-label="Remove lora"
                                        title="Remove">
                                        &times;
                                    </button>
                                </div>

                                <div class="space-y-1">
                                    <div class="flex justify-between text-[10px]">
                                        <span class="text-zinc-500">STRENGTH</span>
                                        <span class="font-mono text-[#C9A84C]">{{ (typeof lora.weight === 'number' ? lora.weight : 1).toFixed(2) }}</span>
                                    </div>

                                    <input
                                        type="range"
                                        min="0"
                                        max="5"
                                        step="0.01"
                                        class="custom-slider w-full"
                                        :disabled="isGenerating"
                                        :value="typeof lora.weight === 'number' ? lora.weight : 1"
                                        @input="(e) => { lora.weight = e.target.valueAsNumber }" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Preview Mask section -->
                <div v-if="previewUrl" class="p-4 border-t border-[#2A2A35]/35 bg-[#07070A]">
                    <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-zinc-500">Active Mask Snapshot</div>
                    <img :src="previewUrl"
                        class="w-full rounded border border-[#2A2A35]/30 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4IiBoZWlnaHQ9IjgiPjxwYXRoIGQ9Ik0wIDBoNHY0SDB6TTQgNGg0djhINFoiIGZpbGw9IiMzMzMiIGZpbGwtb3BhY2l0eT0iMC40Ii8+PC9zdmc+')] object-contain h-24" />
                </div>
            </aside>
        </div>

        <!-- Floating Glassmorphic Generation Navigation Pill -->
        <div v-if="isGenerating || generatedImages.length > 0"
            class="fixed bottom-8 left-1/2 -translate-x-1/2 z-30 border border-[#C9A84C]/25 bg-[#0D0D12]/90 backdrop-blur-md rounded-xl shadow-[0_12px_45px_rgba(0,0,0,0.85)] max-w-2xl px-6 py-4 flex items-center justify-between gap-6 transition-all duration-300 border-l-[4px] border-l-[#C9A84C]">
            
            <div class="flex items-center gap-3 text-xs">
                <span class="relative flex h-2 w-2">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#C9A84C] opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-2 w-2 bg-[#C9A84C]"></span>
                </span>
                <span class="text-zinc-300 font-medium font-sans uppercase tracking-wider" v-if="isGenerating">Refining Canvas…</span>
                <span class="text-zinc-300 font-medium font-sans uppercase tracking-wider" v-else>Batch Complete</span>
                <span class="text-[#C9A84C] font-mono font-bold" v-if="generatedImages.length">({{ currentGeneratedIndex + 1 }}/{{ generatedImages.length }})</span>
            </div>

            <div class="flex items-center gap-2 border-l border-[#2A2A35]/40 pl-6 border-r pr-6 mr-1">
                <button
                    class="rounded border border-[#2A2A35] bg-transparent px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-zinc-300 hover:text-[#FAF8F5] hover:border-[#C9A84C]/40 transition-all duration-200 disabled:opacity-20"
                    :disabled="generatedImages.length <= 1" @click="prevGenerated">
                    Prev
                </button>
                <button
                    class="rounded border border-[#2A2A35] bg-transparent px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-zinc-300 hover:text-[#FAF8F5] hover:border-[#C9A84C]/40 transition-all duration-200 disabled:opacity-20"
                    :disabled="generatedImages.length <= 1" @click="nextGenerated">
                    Next
                </button>
                <button
                    class="rounded border border-[#2A2A35] bg-transparent px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-zinc-300 hover:text-[#FAF8F5] hover:border-[#C9A84C]/40 transition-all duration-200 disabled:opacity-20"
                    :disabled="!generatedImages.length" @click="toggleGeneratedPreview">
                    {{ showGeneratedPreview ? 'Hide Output' : 'Show Output' }}
                </button>
            </div>

            <div class="flex items-center gap-2">
                <button
                    class="rounded border border-[#2A2A35] bg-transparent px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-zinc-400 hover:text-red-400 hover:border-red-500/20 transition-all duration-200"
                    @click="denyOrCancel">
                    {{ isGenerating ? 'Cancel' : 'Deny' }}
                </button>
                <button
                    class="rounded border border-[#C9A84C]/35 bg-[#C9A84C]/5 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-[#C9A84C] hover:bg-[#C9A84C]/10 transition-all duration-200 disabled:opacity-30"
                    :disabled="isGenerating" @click="retryGeneration">
                    Retry
                </button>
                <button
                    class="rounded bg-gradient-to-r from-[#C9A84C] to-[#E3C77D] px-4 py-1.5 text-[10px] font-bold uppercase tracking-wider text-[#0D0D12] hover:from-[#E3C77D] hover:to-[#C9A84C] transition-all duration-200 disabled:opacity-30"
                    :disabled="!generatedImages.length" @click="acceptGenerated">
                    Accept
                </button>
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

// --- Strategy Selection ---
const activeTab = ref('manual') // 'manual' or 'sam'

// --- AI SAM State ---
const samPrompt = ref('clothes,')
const samThreshold = ref(0.5)
const samRefineIterations = ref(2)
const samMaskMode = ref('replace') // 'replace' or 'add'
const samInvertMask = ref(false)
const samModel = ref('sam3.1_multiplex_fp16.safetensors')
const isSegmenting = ref(false)
const samProgressPct = ref(0)
const samProgressLabel = ref('')

// --- SAM Presets ---
const samPresets = [
    { name: 'Clothes', prompt: 'clothes,' },
    { name: 'Hair', prompt: 'hair,' },
    { name: 'Face', prompt: 'face,' },
    { name: 'Skin', prompt: 'skin,' },
    { name: 'Underwear', prompt: 'underwear, bikini, lingerie,' },
    { name: 'Background', prompt: 'background,' },
    { name: 'Shoes', prompt: 'shoes, boots, footwear,' },
    { name: 'Accessories', prompt: 'glasses, necklace, jewelry, watch, hat,' }
]

function selectPreset(promptText) {
    if (!samPrompt.value) {
        samPrompt.value = promptText
    } else {
        if (samPrompt.value.includes(promptText)) {
            // Remove preset and clean up commas
            samPrompt.value = samPrompt.value
                .replace(promptText, '')
                .replace(/,\s*,/g, ',')
                .replace(/^,|,$/g, '')
                .trim()
            if (!samPrompt.value.endsWith(',') && samPrompt.value.length > 0) {
                samPrompt.value += ','
            }
        } else {
            // Append preset safely
            samPrompt.value = (samPrompt.value.trim().endsWith(',') 
                ? samPrompt.value.trim() 
                : samPrompt.value.trim() + ',') + ' ' + promptText
        }
    }
}

// --- Loras ---
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

    // 4. Update state
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
    if (isGenerating.value || isSegmenting.value) {
        activeGenerationToken++
        await interruptComfyUi()
        closeComfyWs()
        isGenerating.value = false
        isSegmenting.value = false
        progressLabel.value = 'Canceled'
        samProgressLabel.value = 'Canceled'
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

                const workflow = JSON.parse(JSON.stringify(inpaintWorkflow))
                workflow["9"].inputs.text = workflow["9"].inputs.text.replace('prompt', prompt.value)
                workflow["40"].inputs.denoise = denoise.value
                workflow["54"].inputs.amount = imageCount.value
                workflow["40"].inputs.seed = Math.floor(Math.random() * 9007199254740991)
                workflow["33"].inputs.image = uploadedPath

                workflow["53"].inputs.lora_01 = selectedLoras.value[0]?.path || 'None'
                workflow["53"].inputs.strength_01 = selectedLoras.value[0]?.weight || 0

                workflow["53"].inputs.lora_02 = selectedLoras.value[1]?.path || 'None'
                workflow["53"].inputs.strength_02 = selectedLoras.value[1]?.weight || 0

                workflow["53"].inputs.lora_03 = selectedLoras.value[2]?.path || 'None'
                workflow["53"].inputs.strength_03 = selectedLoras.value[2]?.weight || 0
                
                workflow["53"].inputs.lora_04 = selectedLoras.value[3]?.path || 'None'
                workflow["53"].inputs.strength_04 = selectedLoras.value[3]?.weight || 0

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

// --- AI SAM Segmenter ---
async function runSamSegmentation() {
    const img = imageEl.value
    const base = baseCanvasRef.value
    if (!img || !base) return

    if (isSegmenting.value || isGenerating.value) return

    // 1. Snapshot the current canvas base image representation
    const out = document.createElement('canvas')
    out.width = canvasWidth.value
    out.height = canvasHeight.value
    const outCtx = out.getContext('2d')
    if (!outCtx) return

    outCtx.drawImage(
        img,
        imageOffsetX.value,
        imageOffsetY.value,
        img.naturalWidth * imageScale.value,
        img.naturalHeight * imageScale.value
    )
    const dataUrl = out.toDataURL('image/png')

    const thisToken = ++activeGenerationToken
    isSegmenting.value = true
    imageError.value = ''
    samProgressPct.value = 0
    samProgressLabel.value = 'Uploading image'

    try {
        const uploadedPath = await uploadImageToComfyUi(dataUrl)
        if (thisToken !== activeGenerationToken) return

        // 2. Build the workflow using the user's ComfyUI flow mapping
        const workflow = {
            "143": {
                "inputs": {
                    "upscale_method": "nearest-exact",
                    "megapixels": 1.1,
                    "resolution_steps": 1,
                    "image": [
                        "144",
                        0
                    ]
                },
                "class_type": "ImageScaleToTotalPixels",
                "_meta": {
                    "title": "ImageScaleToTotalPixels"
                }
            },
            "144": {
                "inputs": {
                    "image": uploadedPath
                },
                "class_type": "LoadImage",
                "_meta": {
                    "title": "Load Image"
                }
            },
            "146": {
                "inputs": {
                    "images": [
                        "147",
                        0
                    ]
                },
                "class_type": "PreviewImage",
                "_meta": {
                    "title": "Preview Image"
                }
            },
            "147": {
                "inputs": {
                    "image": [
                        "143",
                        0
                    ],
                    "alpha": [
                        "142:75",
                        0
                    ]
                },
                "class_type": "JoinImageWithAlpha",
                "_meta": {
                    "title": "Join Image with Alpha"
                }
            },
            "142:75": {
                "inputs": {
                    "threshold": samThreshold.value,
                    "refine_iterations": samRefineIterations.value,
                    "individual_masks": false,
                    "model": [
                        "142:77",
                        0
                    ],
                    "image": [
                        "143",
                        0
                    ],
                    "conditioning": [
                        "142:78",
                        0
                    ]
                },
                "class_type": "SAM3_Detect",
                "_meta": {
                    "title": "SAM3 Detect"
                }
            },
            "142:78": {
                "inputs": {
                    "text": samPrompt.value,
                    "clip": [
                        "142:77",
                        1
                    ]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {
                    "title": "CLIP Text Encode (Prompt)"
                }
            },
            "142:77": {
                "inputs": {
                    "ckpt_name": samModel.value
                },
                "class_type": "CheckpointLoaderSimple",
                "_meta": {
                    "title": "Load Checkpoint"
                }
            }
        }

        samProgressLabel.value = 'Connecting WS'
        comfyWs = await connectComfyWs()
        if (thisToken !== activeGenerationToken) return

        samProgressLabel.value = 'Queueing SAM'
        const queued = await queueComfyPrompt(workflow)
        const promptId = queued?.prompt_id
        if (!promptId) throw new Error('ComfyUI did not return a prompt_id for SAM')
        activePromptId = promptId
        samProgressLabel.value = 'Segmenting'

        let currentNode = ''
        let receivedMaskUrl = null

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
                        if (m > 0) samProgressPct.value = Math.max(0, Math.min(1, v / m))
                        return
                    }

                    if (message?.type === 'executing') {
                        const data = message?.data
                        if (data?.prompt_id !== activePromptId) return
                        if (data?.node == null) {
                            // If execution is complete and we got the mask URL, finish
                            if (receivedMaskUrl) {
                                resolve()
                            }
                            return
                        }
                        currentNode = String(data?.node)
                        return
                    }

                    if (message?.type === 'executed') {
                        const data = message?.data
                        if (data?.prompt_id !== activePromptId) return
                        
                        // Node "146" is the PreviewImage node
                        if (String(data?.node) === '146') {
                            const images = data?.output?.images || []
                            if (images.length > 0) {
                                const imgInfo = images[0]
                                const filename = imgInfo.filename
                                const type = imgInfo.type || 'temp'
                                const subfolder = imgInfo.subfolder || ''
                                receivedMaskUrl = `http://${comfyServerAddress}/view?filename=${encodeURIComponent(filename)}&type=${encodeURIComponent(type)}&subfolder=${encodeURIComponent(subfolder)}`
                                resolve()
                            }
                        }
                        return
                    }

                    return
                }

                // Fallback: If we receive the image as binary bytes while executing PreviewImage node 146
                if (currentNode === '146') {
                    try {
                        const buf = evt.data instanceof ArrayBuffer ? evt.data : await evt.data.arrayBuffer()
                        const imageBytes = buf.slice(8)
                        const blob = new Blob([imageBytes])
                        receivedMaskUrl = await new Promise((r) => {
                            const reader = new FileReader()
                            reader.onload = () => r(String(reader.result))
                            reader.readAsDataURL(blob)
                        })
                        resolve()
                    } catch (e) {
                        console.error('Error reading SAM binary bytes:', e)
                    }
                }
            }
            comfyWs.onclose = () => resolve()
            comfyWs.onerror = (e) => reject(e)
        })

        if (thisToken !== activeGenerationToken) return

        if (!receivedMaskUrl) {
            throw new Error('Did not receive segmented mask from ComfyUI WebSocket')
        }

        samProgressLabel.value = 'Drawing mask'
        await applyAlphaMaskToCanvas(receivedMaskUrl, samMaskMode.value, samInvertMask.value)

        samProgressPct.value = 1
        samProgressLabel.value = 'Success'
    } catch (err) {
        if (thisToken !== activeGenerationToken) return
        imageError.value = String(err?.message || err || 'SAM segmentation failed')
        samProgressLabel.value = 'Error'
    } finally {
        if (thisToken !== activeGenerationToken) return
        isSegmenting.value = false
        closeComfyWs()
        activePromptId = null
    }
}

// --- Draw SAM Alpha Mask onto base Canvas Mask ---
async function applyAlphaMaskToCanvas(imgUrl, mode = 'replace', invert = false) {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    await new Promise((resolve, reject) => {
        img.onload = resolve
        img.onerror = reject
        img.src = imgUrl
    })

    const mask = maskCanvasRef.value
    if (!mask) return
    const ctx = mask.getContext('2d')
    if (!ctx) return

    // 1. Create temporary canvas to format the incoming image
    const tmp = document.createElement('canvas')
    tmp.width = mask.width
    tmp.height = mask.height
    const tmpCtx = tmp.getContext('2d')
    if (!tmpCtx) return

    // 2. Draw incoming image (which has mask in alpha)
    tmpCtx.drawImage(img, 0, 0, mask.width, mask.height)

    // 3. Color either opaque or transparent pixels red (using native compositing)
    // If invert is true, color the transparent parts (source-out)
    // If invert is false, color the opaque parts (source-in)
    tmpCtx.globalCompositeOperation = invert ? 'source-out' : 'source-in'
    tmpCtx.fillStyle = 'rgba(239, 68, 68, 0.7)'
    tmpCtx.fillRect(0, 0, tmp.width, tmp.height)

    // 4. Draw formatted red mask onto the main mask canvas
    if (mode === 'replace') {
        ctx.clearRect(0, 0, mask.width, mask.height)
    }
    
    ctx.globalCompositeOperation = 'source-over'
    ctx.drawImage(tmp, 0, 0)
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

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&family=Playfair+Display:ital,wght@1,400;1,600&display=swap');

/* Luxury Dark Premium Midnight Luxe aesthetics */
.font-sans {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

.font-serif {
    font-family: 'Playfair Display', Georgia, Cambria, "Times New Roman", Times, serif;
}

.font-mono {
    font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

/* Custom Scrollbars */
::-webkit-scrollbar {
    width: 5px;
    height: 5px;
}
::-webkit-scrollbar-track {
    background: #0D0D12;
}
::-webkit-scrollbar-thumb {
    background: #2A2A35;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #C9A84C;
}

/* Luxury Range Slider CSS Overrides */
.custom-slider {
    -webkit-appearance: none;
    appearance: none;
    width: 100%;
    height: 4px;
    background: #181822;
    border-radius: 2px;
    outline: none;
    transition: background 0.3s;
}

.custom-slider::-webkit-slider-runnable-track {
    width: 100%;
    height: 4px;
    cursor: pointer;
    background: #1C1C26;
    border-radius: 2px;
}

.custom-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #C9A84C;
    border: 1.5px solid #FAF8F5;
    cursor: pointer;
    margin-top: -4px;
    box-shadow: 0 0 8px rgba(201, 168, 76, 0.4);
    transition: transform 0.15s, background-color 0.15s;
}

.custom-slider::-webkit-slider-thumb:hover {
    transform: scale(1.2);
    background: #FAF8F5;
    border-color: #C9A84C;
}

.custom-slider::-moz-range-thumb {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #C9A84C;
    border: 1.5px solid #FAF8F5;
    cursor: pointer;
    box-shadow: 0 0 8px rgba(201, 168, 76, 0.4);
    transition: transform 0.15s, background-color 0.15s;
}

.custom-slider::-moz-range-thumb:hover {
    transform: scale(1.2);
    background: #FAF8F5;
    border-color: #C9A84C;
}
</style>