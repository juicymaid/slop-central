<template>
    <div class="max-w-[1280px] mx-auto px-4 sm:px-6 py-8 mb-16">
        <!-- Page Header & Quick Navigation -->
        <header class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-8 mb-8 border-b border-slate/60">
            <div>
                <h1 class="text-2xl sm:text-3xl font-sans font-bold tracking-tight text-ivory">System Maintenance & Scanner</h1>
                <p class="text-sm text-ivory/60 mt-1">Manage library indexing, metadata extraction, model info, embeddings, and database integrity.</p>
            </div>
            <!-- Quick Links -->
            <nav class="flex flex-wrap items-center gap-2">
                <RouterLink to="/models"
                    class="px-3.5 py-2 rounded-xl bg-panel hover:bg-slate text-ivory/80 hover:text-ivory text-xs font-medium border border-slate flex items-center gap-2 transition-colors">
                    <svg class="w-4 h-4 text-champagne" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10">
                        </path>
                    </svg>
                    <span>Models</span>
                </RouterLink>
                <RouterLink to="/civitai"
                    class="px-3.5 py-2 rounded-xl bg-panel hover:bg-slate text-ivory/80 hover:text-ivory text-xs font-medium border border-slate flex items-center gap-2 transition-colors">
                    <svg class="w-4 h-4 text-champagne" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z">
                        </path>
                    </svg>
                    <span>Civitai Gallery</span>
                </RouterLink>
                <RouterLink to="/trash"
                    class="px-3.5 py-2 rounded-xl bg-panel hover:bg-slate text-ivory/80 hover:text-ivory text-xs font-medium border border-slate flex items-center gap-2 transition-colors">
                    <svg class="w-4 h-4 text-ivory/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16">
                        </path>
                    </svg>
                    <span>Trash</span>
                </RouterLink>
            </nav>
        </header>

        <!-- Active Operations Activity Dock -->
        <section v-if="activeOperations.length > 0" class="mb-8 p-5 rounded-2xl bg-panel border border-champagne/40 shadow-sm" aria-label="Active background operations">
            <div class="flex items-center justify-between mb-3.5">
                <div class="flex items-center gap-2 text-champagne font-semibold text-xs tracking-wide">
                    <span class="w-2 h-2 rounded-full bg-champagne"></span>
                    <span>{{ activeOperations.length }} Operation{{ activeOperations.length > 1 ? 's' : '' }} In Progress</span>
                </div>
                <span class="text-ivory/40 font-mono text-[11px]">Live monitoring</span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <div v-for="op in activeOperations" :key="op.id"
                    @click="scrollToCard(op.id)"
                    class="p-3.5 rounded-xl bg-dark-input border border-slate hover:border-champagne/50 transition-colors cursor-pointer group">
                    <div class="flex items-center justify-between mb-1.5">
                        <span class="text-xs font-medium text-ivory group-hover:text-champagne transition-colors">{{ op.title }}</span>
                        <span class="text-xs font-mono font-semibold text-champagne">{{ op.percent }}%</span>
                    </div>
                    <div class="h-1.5 w-full bg-obsidian rounded-full overflow-hidden mb-2">
                        <div class="h-full bg-champagne transition-all duration-300 ease-out"
                            :style="{ width: `${op.percent}%` }"></div>
                    </div>
                    <div class="flex items-center justify-between text-[11px] font-mono text-ivory/50">
                        <span class="truncate max-w-[80%]">{{ op.message }}</span>
                        <span class="text-champagne/80 group-hover:underline">View &darr;</span>
                    </div>
                </div>
            </div>
        </section>

        <!-- Error Banner -->
        <div v-if="error" class="mb-8 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 font-mono text-xs flex items-center gap-3">
            <svg class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span>{{ errorMessage }}</span>
        </div>

        <div class="space-y-6">
            <!-- ========================================== -->
            <!-- 1. CIVITAI HELPER PANEL                    -->
            <!-- ========================================== -->
            <section id="civitai-helper" class="p-6 rounded-2xl bg-panel border border-slate">
                <!-- Section Header -->
                <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-5 pb-4 border-b border-slate/60">
                    <div>
                        <div class="flex items-center gap-2.5">
                            <svg class="w-5 h-5 text-champagne shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10">
                                </path>
                            </svg>
                            <h2 class="text-lg font-semibold text-ivory tracking-tight">Civitai Helper: Models & LoRAs</h2>
                            <span class="px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider rounded-md border"
                                :class="getStatusBadgeClass(civitaiStatus.status)">
                                {{ civitaiStatus.status }}
                            </span>
                        </div>
                        <p class="text-sm text-ivory/60 mt-1 max-w-2xl">
                            Finds models on Civitai via SHA256/AutoV2 hash, retrieves metadata (<code class="text-champagne font-mono text-xs">.civitai.info</code>), trigger words, and downloads the highest NSFW-rated cover preview.
                        </p>
                    </div>

                    <!-- Action buttons -->
                    <div class="flex flex-wrap items-center gap-2 shrink-0">
                        <button v-if="civitaiStatus.status === 'running'" @click="cancelCivitaiScan"
                            class="bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 px-4 py-2 rounded-xl text-xs font-medium flex items-center gap-2 transition-colors cursor-pointer">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                            <span>Cancel Scan</span>
                        </button>
                        <button v-else @click="startCivitaiScan"
                            class="bg-champagne hover:bg-[#D4B55E] text-obsidian px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer shadow-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                            </svg>
                            <span>Scan Models for Civitai</span>
                        </button>
                        <button @click="showSingleModelModal = !showSingleModelModal"
                            class="bg-dark-input hover:bg-slate text-ivory/80 hover:text-ivory px-3.5 py-2 rounded-xl text-xs font-medium border border-slate flex items-center gap-2 transition-colors cursor-pointer">
                            <svg class="w-4 h-4 text-champagne" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
                            </svg>
                            <span>{{ showSingleModelModal ? 'Hide URL Lookup' : 'Lookup by URL' }}</span>
                        </button>
                        <button @click="showCivitaiLogs = !showCivitaiLogs"
                            class="bg-dark-input hover:bg-slate text-ivory/70 hover:text-ivory px-3 py-2 rounded-xl text-xs font-mono border border-slate flex items-center gap-1.5 transition-colors cursor-pointer">
                            <span>Logs</span>
                            <span v-if="civitaiStatus.logs?.length" class="text-champagne">({{ civitaiStatus.logs.length }})</span>
                        </button>
                    </div>
                </div>

                <!-- Scan options -->
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 mb-5">
                    <label class="flex items-center gap-2.5 p-3 rounded-xl bg-dark-input border border-slate/60 text-xs text-ivory/80 cursor-pointer select-none hover:border-slate transition-colors">
                        <input type="checkbox" v-model="civitaiOptions.scanLoras" class="accent-champagne rounded w-4 h-4 cursor-pointer" />
                        <span>Scan LoRAs (<code class="text-champagne text-[11px]">Lora/</code>)</span>
                    </label>
                    <label class="flex items-center gap-2.5 p-3 rounded-xl bg-dark-input border border-slate/60 text-xs text-ivory/80 cursor-pointer select-none hover:border-slate transition-colors">
                        <input type="checkbox" v-model="civitaiOptions.scanCheckpoints" class="accent-champagne rounded w-4 h-4 cursor-pointer" />
                        <span>Scan Checkpoints (<code class="text-champagne text-[11px]">StableDiffusion/</code>)</span>
                    </label>
                    <label class="flex items-center gap-2.5 p-3 rounded-xl bg-dark-input border border-slate/60 text-xs text-ivory/80 cursor-pointer select-none hover:border-slate transition-colors">
                        <input type="checkbox" v-model="civitaiOptions.skipExisting" class="accent-champagne rounded w-4 h-4 cursor-pointer" />
                        <span>Skip Existing (Info & Preview)</span>
                    </label>
                    <label class="flex items-center gap-2.5 p-3 rounded-xl bg-dark-input border border-slate/60 text-xs text-ivory/80 cursor-pointer select-none hover:border-slate transition-colors">
                        <input type="checkbox" v-model="civitaiOptions.maxSizePreview" class="accent-champagne rounded w-4 h-4 cursor-pointer" />
                        <span>Highest Quality & NSFW Cover</span>
                    </label>
                </div>

                <!-- Single Model URL Lookup Panel (Collapsible) -->
                <div v-if="showSingleModelModal" class="p-4 rounded-xl bg-dark-input border border-slate mb-5 space-y-4">
                    <div class="flex items-center justify-between">
                        <h3 class="text-xs font-semibold text-champagne uppercase tracking-wider">Direct Civitai Lookup & Cover Download</h3>
                        <button @click="showSingleModelModal = false" class="text-ivory/40 hover:text-ivory text-xs font-mono transition-colors">Close</button>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-[11px] font-mono uppercase tracking-wider text-ivory/60 mb-1.5">Select Local Model</label>
                            <select v-model="singleLookup.modelPath"
                                class="w-full bg-obsidian border border-slate rounded-xl px-3 py-2 text-xs text-ivory focus:border-champagne focus:outline-none transition-colors">
                                <option value="" disabled>Select a model file...</option>
                                <option v-for="m in localModelsList" :key="m.path" :value="m.path">
                                    [{{ m.type.toUpperCase() }}] {{ m.name }} {{ m.has_info ? '✓ (has info)' : '✗ (missing info)' }}
                                </option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-[11px] font-mono uppercase tracking-wider text-ivory/60 mb-1.5">Civitai Model URL or ID</label>
                            <div class="flex gap-2">
                                <input type="text" v-model="singleLookup.urlOrId"
                                    placeholder="e.g. https://civitai.com/models/12345 or 12345"
                                    class="flex-1 bg-obsidian border border-slate rounded-xl px-3 py-2 text-xs text-ivory focus:border-champagne focus:outline-none transition-colors" />
                                <button @click="fetchSingleModelInfo" :disabled="singleLookup.loading || !singleLookup.modelPath || !singleLookup.urlOrId"
                                    class="bg-champagne hover:bg-[#D4B55E] text-obsidian font-semibold px-4 py-2 rounded-xl text-xs flex items-center gap-2 disabled:opacity-50 transition-colors cursor-pointer">
                                    <svg v-if="singleLookup.loading" class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    <span>Fetch</span>
                                </button>
                            </div>
                        </div>
                    </div>
                    <div v-if="singleLookup.result" class="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400">
                        <div class="font-semibold">{{ singleLookup.result.message }}</div>
                        <div class="text-[11px] text-emerald-300/80 mt-1 font-mono">
                            Model: {{ singleLookup.result.model_name }} | Version ID: {{ singleLookup.result.version_id }}
                            <span v-if="singleLookup.result.selected_image"> | Highest NSFW Level: {{ singleLookup.result.selected_image.nsfw_level }}</span>
                        </div>
                    </div>
                </div>

                <!-- Progress & Metrics -->
                <div class="pt-2">
                    <div v-if="civitaiStatus.status === 'running' || civitaiStatus.total > 0" class="mb-3">
                        <div class="h-1.5 w-full bg-obsidian overflow-hidden rounded-full mb-2">
                            <div class="h-full bg-champagne transition-all duration-300 ease-out"
                                :style="{ width: `${civitaiProgress}%` }"></div>
                        </div>
                        <div class="flex flex-wrap items-center justify-between gap-2 text-xs font-mono text-ivory/70">
                            <span>Progress: {{ civitaiStatus.processed }} / {{ civitaiStatus.total }} ({{ civitaiProgress }}%)</span>
                            <div class="flex items-center gap-4">
                                <span class="text-emerald-400">Updated: {{ civitaiStatus.successful }}</span>
                                <span class="text-amber-400">Failed / Unmatched: {{ civitaiStatus.failed }}</span>
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center justify-between text-xs font-mono text-ivory/50">
                        <span>Message</span>
                        <span class="text-right text-ivory/70 truncate max-w-[75%]">{{ civitaiStatus.message || 'Ready to scan.' }}</span>
                    </div>
                </div>

                <!-- Logs Drawer (Collapsible) -->
                <div v-if="showCivitaiLogs && civitaiStatus.logs?.length" class="mt-4 p-3 rounded-xl bg-obsidian border border-slate font-mono text-xs max-h-48 overflow-y-auto space-y-1">
                    <div v-for="(log, idx) in civitaiStatus.logs" :key="idx" class="flex items-start gap-2">
                        <span class="text-ivory/40 shrink-0">[{{ log.time }}]</span>
                        <span :class="log.type === 'success' ? 'text-emerald-400' : log.type === 'warning' ? 'text-amber-400' : log.type === 'error' ? 'text-red-400' : 'text-ivory/80'">
                            {{ log.message }}
                        </span>
                    </div>
                </div>
            </section>

            <!-- ========================================== -->
            <!-- 2. IMAGE LIBRARY SCANNER                   -->
            <!-- ========================================== -->
            <section id="library-scan" class="p-6 rounded-2xl bg-panel border border-slate">
                <!-- Section Header -->
                <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-5 pb-4 border-b border-slate/60">
                    <div>
                        <div class="flex items-center gap-2.5">
                            <svg class="w-5 h-5 text-champagne shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z">
                                </path>
                            </svg>
                            <h2 class="text-lg font-semibold text-ivory tracking-tight">Image Library Scanner</h2>
                            <span class="px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider rounded-md border"
                                :class="getStatusBadgeClass(isScanning ? 'running' : scanStatus === 'completed' ? 'completed' : 'idle')">
                                {{ isScanning ? 'running' : scanStatus === 'completed' ? 'completed' : 'idle' }}
                            </span>
                        </div>
                        <p class="text-sm text-ivory/60 mt-1 max-w-2xl">Discovers new generated images in storage folders, extracts prompt parameters, sampler, seed, model, and indexes them into the database.</p>
                    </div>
                    <div class="shrink-0">
                        <button @click="startScan"
                            class="bg-champagne hover:bg-[#D4B55E] text-obsidian px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer shadow-sm disabled:opacity-50"
                            :disabled="isScanning">
                            <svg v-if="!isScanning" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                            </svg>
                            <svg v-else class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span>{{ isScanning ? 'Scanning Library...' : 'Start Library Scan' }}</span>
                        </button>
                    </div>
                </div>

                <!-- Progress Details -->
                <div v-if="isScanning" class="mb-4">
                    <div v-if="scanStatus === 'retrieving_files'" class="space-y-2">
                        <div class="h-1.5 w-full bg-obsidian overflow-hidden rounded-full">
                            <div class="h-full bg-champagne transition-all duration-300 ease-out indeterminate-progress"></div>
                        </div>
                        <p class="text-xs font-mono text-ivory/60">{{ scanStatusMessage }}</p>
                    </div>
                    <div v-else-if="scanStatus === 'files_found' || scanStatus === 'scanning'" class="space-y-2">
                        <div class="h-1.5 w-full bg-obsidian overflow-hidden rounded-full">
                            <div class="h-full bg-champagne transition-all duration-300 ease-out"
                                :style="{ width: `${scanProgress}%` }"></div>
                        </div>
                        <div class="flex justify-between items-center text-xs font-mono text-ivory/70">
                            <p class="truncate max-w-[70%]">{{ scanStatusMessage }}</p>
                            <p v-if="scanTotal > 0">{{ scanProcessed }} / {{ scanTotal }} ({{ scanProgress }}%)</p>
                        </div>
                    </div>
                    <div v-else-if="scanStatus === 'saving'" class="space-y-2">
                        <div class="h-1.5 w-full bg-obsidian overflow-hidden rounded-full">
                            <div class="h-full bg-emerald-500 transition-all duration-300 ease-out indeterminate-progress"></div>
                        </div>
                        <p class="text-xs font-mono text-ivory/60">{{ scanStatusMessage }}</p>
                    </div>
                </div>

                <!-- Completed Status Banner -->
                <div v-if="scanStatus === 'completed' && !isScanning" class="p-3.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl mb-4">
                    <div class="flex items-center gap-2 text-emerald-400 text-xs font-semibold">
                        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                        <span>Scan Completed Successfully</span>
                    </div>
                    <p class="text-emerald-300/80 font-mono text-xs mt-1">
                        Processed {{ completedStats.totalProcessed }} images, added {{ completedStats.totalAdded }} new images.
                    </p>
                </div>

                <!-- Newly Discovered Images Preview -->
                <div v-if="newImages.length > 0" class="pt-4 border-t border-slate/60">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                        <div class="flex items-center gap-2">
                            <h3 class="text-sm font-semibold text-ivory">Newly Discovered Images</h3>
                            <span class="text-ivory/50 font-mono text-xs">({{ newImages.length }})</span>
                            <span v-if="newImages.length > displayedNewImages.length" class="text-champagne/80 font-mono text-xs">
                                (Showing newest {{ displayedNewImages.length }})
                            </span>
                        </div>

                        <!-- Limit Selector Controls -->
                        <div class="flex items-center gap-2 text-xs font-mono text-ivory/60">
                            <span>Limit:</span>
                            <div class="flex items-center bg-dark-input p-0.5 rounded-lg border border-slate">
                                <button v-for="opt in limitOptions" :key="opt"
                                    type="button"
                                    @click="newImagesLimit = opt"
                                    class="px-2.5 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer"
                                    :class="newImagesLimit === opt ? 'bg-champagne text-obsidian font-semibold shadow-sm' : 'text-ivory/60 hover:text-ivory'">
                                    {{ opt }}
                                </button>
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                        <div v-for="(image, index) in displayedNewImages" :key="image.Path || index" class="relative group aspect-square rounded-xl overflow-hidden border border-slate bg-obsidian">
                            <RouterLink v-if="image.Id" :to="'/image/' + image.Id" class="block w-full h-full">
                                <img :src="apiUrl + image.Path" alt="Discovered Image"
                                    loading="lazy"
                                    class="w-full h-full object-cover group-hover:opacity-90 transition-opacity" />
                            </RouterLink>
                            <div v-else class="w-full h-full">
                                <img :src="apiUrl + image.Path" alt="Discovered Image"
                                    loading="lazy"
                                    class="w-full h-full object-cover" />
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ========================================== -->
            <!-- 3. PERCEPTUAL HASH (PHASH) CALCULATOR      -->
            <!-- ========================================== -->
            <section id="phash-indexer" class="p-6 rounded-2xl bg-panel border border-slate">
                <!-- Section Header -->
                <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-5 pb-4 border-b border-slate/60">
                    <div>
                        <div class="flex items-center gap-2.5">
                            <svg class="w-5 h-5 text-champagne shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z">
                                </path>
                            </svg>
                            <h2 class="text-lg font-semibold text-ivory tracking-tight">Perceptual Hash Indexer (pHash)</h2>
                            <span class="px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider rounded-md border"
                                :class="getStatusBadgeClass(phashStatus.status)">
                                {{ phashStatus.status }}
                            </span>
                        </div>
                        <p class="text-sm text-ivory/60 mt-1 max-w-2xl">Computes 64-bit perceptual hashes for visual deduplication, similarity matching, and matchup recommendations.</p>
                    </div>
                    <div class="shrink-0">
                        <button @click="startphash"
                            class="bg-champagne hover:bg-[#D4B55E] text-obsidian px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer shadow-sm disabled:opacity-50"
                            :disabled="phashStatus.status === 'running'">
                            <svg v-if="phashStatus.status !== 'running'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                            </svg>
                            <svg v-else class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span>{{ phashStatus.status === 'running' ? 'Calculating...' : 'Calculate pHashes' }}</span>
                        </button>
                    </div>
                </div>

                <!-- Progress Details -->
                <div class="space-y-2">
                    <div v-if="phashStatus.status === 'running' || phashStatus.total > 0" class="space-y-2 mb-2">
                        <div class="h-1.5 w-full bg-obsidian overflow-hidden rounded-full">
                            <div class="h-full bg-champagne transition-all duration-300 ease-out"
                                :style="{ width: `${phashStatus.percent}%` }"></div>
                        </div>
                        <div class="flex justify-between text-xs font-mono text-ivory/70">
                            <span>Progress</span>
                            <span>{{ phashStatus.processed }} / {{ phashStatus.total }} ({{ phashStatus.percent }}%)</span>
                        </div>
                    </div>
                    <div class="flex items-center justify-between text-xs font-mono text-ivory/50">
                        <span>Message</span>
                        <span class="text-right text-ivory/70 truncate max-w-[75%]">{{ phashStatus.message || 'Ready to calculate.' }}</span>
                    </div>
                </div>
            </section>

            <!-- ========================================== -->
            <!-- 4. DATABASE PRUNER & INTEGRITY             -->
            <!-- ========================================== -->
            <section id="library-prune" class="p-6 rounded-2xl bg-panel border border-slate">
                <!-- Section Header -->
                <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-5 pb-4 border-b border-slate/60">
                    <div>
                        <div class="flex items-center gap-2.5">
                            <svg class="w-5 h-5 text-red-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16">
                                </path>
                            </svg>
                            <h2 class="text-lg font-semibold text-ivory tracking-tight">Library Integrity & Database Pruner</h2>
                            <span class="px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider rounded-md border"
                                :class="getStatusBadgeClass(pruneStatus.status)">
                                {{ pruneStatus.status }}
                            </span>
                        </div>
                        <p class="text-sm text-ivory/60 mt-1 max-w-2xl">Verifies file existence on disk, eliminates orphan database records, cleans duplicate paths, and synchronizes missing model names.</p>
                    </div>
                    <div class="shrink-0">
                        <button @click="startPruning"
                            class="bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 px-4 py-2 rounded-xl text-xs font-medium flex items-center gap-2 transition-colors cursor-pointer disabled:opacity-50"
                            :disabled="pruneStatus.status === 'running'">
                            <svg v-if="pruneStatus.status !== 'running'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                            <svg v-else class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span>{{ pruneStatus.status === 'running' ? 'Pruning...' : 'Prune Library' }}</span>
                        </button>
                    </div>
                </div>

                <!-- Progress Details -->
                <div class="space-y-2">
                    <div v-if="pruneStatus.status === 'running' || pruneStatus.total > 0" class="space-y-2 mb-2">
                        <div class="h-1.5 w-full bg-obsidian overflow-hidden rounded-full">
                            <div class="h-full bg-champagne transition-all duration-300 ease-out"
                                :style="{ width: `${pruneStatus.percent}%` }"></div>
                        </div>
                        <div class="flex flex-wrap items-center justify-between gap-2 text-xs font-mono text-ivory/70">
                            <span>Progress: {{ pruneStatus.percent }}%</span>
                            <div class="flex items-center gap-4">
                                <span class="text-red-400">Removed: {{ pruneStatus.files_removed }}</span>
                                <span class="text-amber-400">Missing: {{ pruneStatus.missing_removed }}</span>
                                <span class="text-blue-400">Duplicates: {{ pruneStatus.duplicates_removed }}</span>
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center justify-between text-xs font-mono text-ivory/50">
                        <span>Message</span>
                        <span class="text-right text-ivory/70 truncate max-w-[75%]">{{ pruneStatus.message || 'Ready to prune.' }}</span>
                    </div>
                </div>
            </section>

            <!-- ========================================== -->
            <!-- 5. METADATA & PROMPT RESTORATION           -->
            <!-- ========================================== -->
            <section id="prompt-restoration" class="p-6 rounded-2xl bg-panel border border-slate">
                <!-- Section Header -->
                <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-5 pb-4 border-b border-slate/60">
                    <div>
                        <div class="flex items-center gap-2.5">
                            <svg class="w-5 h-5 text-champagne shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H17"></path>
                            </svg>
                            <h2 class="text-lg font-semibold text-ivory tracking-tight">Metadata & Prompt Restoration</h2>
                            <span class="px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider rounded-md border"
                                :class="getStatusBadgeClass(promptUpdateStatus.update_inprogress ? 'running' : 'idle')">
                                {{ promptUpdateStatus.update_inprogress ? 'running' : 'idle' }}
                            </span>
                        </div>
                        <p class="text-sm text-ivory/60 mt-1 max-w-2xl">Re-scans files missing prompts or marked with generated tags to recover full parameters directly from embedded PNG/ComfyUI metadata.</p>
                    </div>
                    <div class="shrink-0">
                        <button @click="triggerPromptUpdate"
                            class="bg-champagne hover:bg-[#D4B55E] text-obsidian px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer shadow-sm disabled:opacity-50"
                            :disabled="promptUpdateStatus.update_inprogress">
                            <svg v-if="!promptUpdateStatus.update_inprogress" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H17"></path>
                            </svg>
                            <svg v-else class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span>{{ promptUpdateStatus.update_inprogress ? 'Updating...' : 'Restore Missing Prompts' }}</span>
                        </button>
                    </div>
                </div>

                <!-- Progress Details -->
                <div class="space-y-2">
                    <div v-if="promptUpdateStatus.update_inprogress" class="space-y-2 mb-2">
                        <div class="h-1.5 w-full bg-obsidian overflow-hidden rounded-full">
                            <div class="h-full bg-champagne transition-all duration-300 ease-out"
                                :style="{ width: `${promptUpdateProgress}%` }"></div>
                        </div>
                        <div class="flex justify-between text-xs font-mono text-ivory/70">
                            <span>Progress</span>
                            <span>{{ promptUpdateStatus.update_processed }} / {{ promptUpdateStatus.update_total }} ({{ promptUpdateProgress }}%)</span>
                        </div>
                    </div>
                    <div class="flex items-center justify-between text-xs font-mono text-ivory/50">
                        <span>Successful Updates</span>
                        <span class="text-emerald-400 font-semibold">{{ promptUpdateStatus.update_successful }}</span>
                    </div>
                </div>
            </section>

            <!-- ========================================== -->
            <!-- 6. SIGLIP 2 EMBEDDINGS                     -->
            <!-- ========================================== -->
            <section id="siglip-indexing" class="p-6 rounded-2xl bg-panel border border-slate">
                <!-- Section Header -->
                <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-5 pb-4 border-b border-slate/60">
                    <div>
                        <div class="flex items-center gap-2.5">
                            <svg class="w-5 h-5 text-champagne shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z">
                                </path>
                            </svg>
                            <h2 class="text-lg font-semibold text-ivory tracking-tight">Neural Search & Recommendations (SigLIP 2)</h2>
                            <span class="px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider rounded-md border"
                                :class="getStatusBadgeClass(siglipStatus.status)">
                                {{ siglipStatus.status }}
                            </span>
                        </div>
                        <p class="text-sm text-ivory/60 mt-1 max-w-2xl">Generates 768-dimensional deep visual embeddings to power natural language semantic search and similarity recommendations.</p>
                    </div>
                    <div class="flex flex-wrap items-center gap-2 shrink-0">
                        <button @click="startSiglipIndexing(false)"
                            class="bg-champagne hover:bg-[#D4B55E] text-obsidian px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer shadow-sm disabled:opacity-50"
                            :disabled="siglipStatus.status === 'running'">
                            <span>{{ siglipStatus.status === 'running' ? 'Indexing...' : 'Update Embeddings' }}</span>
                        </button>
                        <button @click="startSiglipIndexing(true)"
                            class="bg-dark-input hover:bg-red-500/20 text-ivory/70 hover:text-red-400 border border-slate hover:border-red-500/30 px-3.5 py-2 rounded-xl text-xs font-medium flex items-center gap-2 transition-colors cursor-pointer disabled:opacity-50"
                            :disabled="siglipStatus.status === 'running'">
                            <span>Force Rebuild All</span>
                        </button>
                    </div>
                </div>

                <!-- Progress Details -->
                <div class="space-y-2">
                    <div v-if="siglipStatus.status === 'running'" class="space-y-2 mb-2">
                        <div class="h-1.5 w-full bg-obsidian overflow-hidden rounded-full">
                            <div class="h-full bg-champagne transition-all duration-300 ease-out"
                                :style="{ width: `${siglipProgress}%` }"></div>
                        </div>
                        <div class="flex justify-between text-xs font-mono text-ivory/70">
                            <span>Progress</span>
                            <span>{{ siglipStatus.processed }} / {{ siglipStatus.total }} ({{ siglipProgress }}%)</span>
                        </div>
                    </div>
                    <div class="flex items-center justify-between text-xs font-mono text-ivory/50">
                        <span>Message</span>
                        <span class="text-right text-ivory/70 truncate max-w-[75%]">{{ siglipStatus.message || 'No active task.' }}</span>
                    </div>
                </div>
            </section>
        </div>
    </div>
</template>

<script setup>
import { GetFromApi, PostToApi, apiUrl, wsUrl } from '@/api';
import { ref, computed, onMounted, onBeforeUnmount, inject, reactive } from 'vue';

const isDarkMode = inject('isDarkMode', ref(false));

// ==========================================
// 1. CIVITAI HELPER STATE & METHODS
// ==========================================
const civitaiStatus = ref({
    status: 'idle',
    total: 0,
    processed: 0,
    successful: 0,
    failed: 0,
    skipped: 0,
    percent: 0,
    current_model: '',
    current_type: '',
    message: '',
    logs: [],
});
const civitaiOptions = reactive({
    scanLoras: true,
    scanCheckpoints: true,
    skipExisting: true,
    maxSizePreview: true,
});
const civitaiInterval = ref(null);
const showCivitaiLogs = ref(false);
const showSingleModelModal = ref(false);
const localModelsList = ref([]);
const singleLookup = reactive({
    modelPath: '',
    urlOrId: '',
    loading: false,
    result: null,
});

const civitaiProgress = computed(() => {
    if (civitaiStatus.value.total > 0) {
        return Math.round((civitaiStatus.value.processed / civitaiStatus.value.total) * 100);
    }
    return civitaiStatus.value.percent || 0;
});

const fetchCivitaiStatus = async () => {
    try {
        const res = await GetFromApi('civitai-helper/status');
        if (res) {
            civitaiStatus.value = res;
        }
    } catch (e) {
        console.error('Error fetching Civitai Helper status:', e);
    }
};

const fetchLocalModels = async () => {
    try {
        const res = await GetFromApi('civitai-helper/local-models?type=all');
        if (res && res.models) {
            localModelsList.value = res.models;
        }
    } catch (e) {
        console.error('Error fetching local models:', e);
    }
};

const startCivitaiScan = async () => {
    try {
        const types = [];
        if (civitaiOptions.scanLoras) types.push('lora');
        if (civitaiOptions.scanCheckpoints) types.push('checkpoint');

        if (types.length === 0) {
            alert('Please select at least one model type to scan (LoRAs or Checkpoints).');
            return;
        }

        await PostToApi('civitai-helper/scan', {
            model_types: types,
            skip_existing: civitaiOptions.skipExisting,
            download_preview: true,
            max_size_preview: civitaiOptions.maxSizePreview,
        });

        await fetchCivitaiStatus();
        startCivitaiPolling();
    } catch (e) {
        console.error('Error starting Civitai scan:', e);
    }
};

const cancelCivitaiScan = async () => {
    try {
        await PostToApi('civitai-helper/cancel', {});
        await fetchCivitaiStatus();
    } catch (e) {
        console.error('Error cancelling Civitai scan:', e);
    }
};

const fetchSingleModelInfo = async () => {
    if (!singleLookup.modelPath || !singleLookup.urlOrId) return;
    singleLookup.loading = true;
    singleLookup.result = null;
    try {
        const res = await PostToApi('civitai-helper/fetch-model-by-url', {
            model_path: singleLookup.modelPath,
            url_or_id: singleLookup.urlOrId,
            download_preview: true,
            max_size_preview: civitaiOptions.maxSizePreview,
        });
        singleLookup.result = res;
        await fetchLocalModels();
    } catch (e) {
        console.error('Error in single model lookup:', e);
        alert(e.message || 'Failed to fetch model info from Civitai.');
    } finally {
        singleLookup.loading = false;
    }
};

const startCivitaiPolling = () => {
    if (civitaiInterval.value) return;
    civitaiInterval.value = setInterval(async () => {
        await fetchCivitaiStatus();
        if (civitaiStatus.value.status !== 'running') {
            stopCivitaiPolling();
            fetchLocalModels();
        }
    }, 1000);
};

const stopCivitaiPolling = () => {
    if (civitaiInterval.value) {
        clearInterval(civitaiInterval.value);
        civitaiInterval.value = null;
    }
};

// ==========================================
// 2. IMAGE LIBRARY SCANNER STATE & METHODS
// ==========================================
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
const newImagesLimit = ref(48);
const limitOptions = [24, 48, 96, 'All'];
const websocket = ref(null);

const displayedNewImages = computed(() => {
    const list = newImages.value;
    if (newImagesLimit.value === 'All') {
        return [...list].reverse();
    }
    const limit = Number(newImagesLimit.value);
    const start = Math.max(0, list.length - limit);
    return list.slice(start).reverse();
});
const completedStats = ref({
    totalProcessed: 0,
    totalAdded: 0,
});

const fetchScanStatus = async () => {
    try {
        const res = await GetFromApi('scan-status');
        if (res) {
            if (res.scan_inprogress) {
                isScanning.value = true;
                scanStatus.value = res.status || 'scanning';
                scanStatusMessage.value = res.message || 'Scanning library...';
                scanProcessed.value = res.processed || 0;
                scanSuccessful.value = res.successful || 0;
                scanTotal.value = res.total || 0;
                scanProgress.value = res.percent || 0;
                latestFile.value = res.latest_file || '';
                if (Array.isArray(res.scanned_images) && res.scanned_images.length > 0) {
                    newImages.value = res.scanned_images;
                } else if (Array.isArray(res.new_images) && res.new_images.length > 0) {
                    newImages.value = res.new_images.map((p) => ({ Path: p }));
                }
                connectWebSocket('monitor');
            } else if (res.status === 'completed' && res.completed_stats) {
                completedStats.value = res.completed_stats;
                scanStatus.value = 'completed';
            }
        }
    } catch (e) {
        console.error('Error fetching scan status:', e);
    }
};

const connectWebSocket = (action = 'auto') => {
    if (websocket.value && websocket.value.readyState !== WebSocket.CLOSED) {
        websocket.value.close();
    }

    const _wsUrl = `${wsUrl}/ws/scan?action=${action}`;
    websocket.value = new WebSocket(_wsUrl);

    websocket.value.onopen = () => {
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
        if (isScanning.value && scanStatus.value !== 'completed' && !error.value) {
            setTimeout(async () => {
                const res = await GetFromApi('scan-status');
                if (res && res.scan_inprogress) {
                    connectWebSocket('monitor');
                } else {
                    isScanning.value = false;
                }
            }, 2000);
        } else {
            isScanning.value = false;
        }
    };
};

const handleWebSocketMessage = (data) => {
    switch (data.type) {
        case 'status':
            scanStatus.value = data.status;
            scanStatusMessage.value = data.message;

            if (data.total_files) {
                scanTotal.value = data.total_files;
            }

            if (data.status === 'completed') {
                isScanning.value = false;
                completedStats.value = {
                    totalProcessed: data.total_processed || 0,
                    totalAdded: data.total_added || 0,
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
            if (data.image_path) {
                const exists = newImages.value.some((img) => img.Path === data.image_path);
                if (!exists) {
                    newImages.value.push({ Path: data.image_path, Id: data.image_id || null });
                }
            }
            scanProcessed.value = data.processed;
            scanSuccessful.value = data.successful;
            scanTotal.value = data.total;
            scanProgress.value = data.percent;
            break;

        case 'image_failed':
            scanProcessed.value = data.processed;
            scanSuccessful.value = data.successful;
            scanTotal.value = data.total;
            scanProgress.value = data.percent;
            break;

        case 'error':
            error.value = true;
            errorMessage.value = data.message || 'An error occurred during library scan';
            isScanning.value = false;
            break;

        case 'complete':
            scanStatus.value = 'completed';
            scanStatusMessage.value = data.message;
            isScanning.value = false;
            completedStats.value = {
                totalProcessed: data.total_processed || 0,
                totalAdded: data.total_added || 0,
            };
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

const startScan = () => {
    scanStatus.value = 'starting';
    scanStatusMessage.value = 'Connecting...';
    scanProcessed.value = 0;
    scanSuccessful.value = 0;
    scanTotal.value = 0;
    scanProgress.value = 0;
    latestFile.value = '';
    error.value = false;
    errorMessage.value = '';
    newImages.value = [];
    connectWebSocket('start');
};

// ==========================================
// 3. PHASH CALCULATION STATE & METHODS
// ==========================================
const phashStatus = ref({
    status: 'idle',
    processed: 0,
    total: 0,
    percent: 0,
    message: '',
});
const phashInterval = ref(null);

const fetchPhashStatus = async () => {
    try {
        const res = await GetFromApi('phash-status');
        if (res) {
            phashStatus.value = res;
        }
    } catch (e) {
        console.error('Error fetching pHash status:', e);
    }
};

const startphash = async () => {
    try {
        await PostToApi('calculate-phashes', {});
        await fetchPhashStatus();
        startPhashPolling();
    } catch (e) {
        console.error('Error starting pHash calculation:', e);
    }
};

const startPhashPolling = () => {
    if (phashInterval.value) return;
    phashInterval.value = setInterval(async () => {
        await fetchPhashStatus();
        if (phashStatus.value.status !== 'running') {
            stopPhashPolling();
        }
    }, 1000);
};

const stopPhashPolling = () => {
    if (phashInterval.value) {
        clearInterval(phashInterval.value);
        phashInterval.value = null;
    }
};

// ==========================================
// 4. PRUNING STATE & METHODS
// ==========================================
const pruneStatus = ref({
    status: 'idle',
    processed: 0,
    total: 0,
    percent: 0,
    files_removed: 0,
    missing_removed: 0,
    duplicates_removed: 0,
    models_filled: 0,
    message: '',
});
const pruneInterval = ref(null);

const fetchPruneStatus = async () => {
    try {
        const res = await GetFromApi('prune-status');
        if (res) {
            pruneStatus.value = res;
        }
    } catch (e) {
        console.error('Error fetching prune status:', e);
    }
};

const startPruning = async () => {
    try {
        await PostToApi('prune-images', {});
        await fetchPruneStatus();
        startPrunePolling();
    } catch (e) {
        console.error('Error starting prune:', e);
    }
};

const startPrunePolling = () => {
    if (pruneInterval.value) return;
    pruneInterval.value = setInterval(async () => {
        await fetchPruneStatus();
        if (pruneStatus.value.status !== 'running') {
            stopPrunePolling();
        }
    }, 1000);
};

const stopPrunePolling = () => {
    if (pruneInterval.value) {
        clearInterval(pruneInterval.value);
        pruneInterval.value = null;
    }
};

// ==========================================
// 5. PROMPT RESTORATION STATE & METHODS
// ==========================================
const promptUpdateStatus = ref({
    update_inprogress: false,
    update_total: 0,
    update_processed: 0,
    update_successful: 0,
    update_error: false,
});
const promptUpdateInterval = ref(null);
const promptUpdateProgress = computed(() => {
    if (promptUpdateStatus.value.update_total > 0) {
        return Math.round((promptUpdateStatus.value.update_processed / promptUpdateStatus.value.update_total) * 100);
    }
    return 0;
});

const fetchPromptUpdateStatus = async () => {
    try {
        const res = await GetFromApi('prompt-update-status');
        if (res) {
            promptUpdateStatus.value = res;
        }
    } catch (e) {
        console.error('Error fetching prompt update status:', e);
    }
};

const triggerPromptUpdate = async () => {
    try {
        await PostToApi('update-missing-prompts', {});
        await fetchPromptUpdateStatus();
        startPromptUpdatePolling();
    } catch (e) {
        console.error('Error starting prompt update:', e);
    }
};

const startPromptUpdatePolling = () => {
    if (promptUpdateInterval.value) return;
    promptUpdateInterval.value = setInterval(async () => {
        await fetchPromptUpdateStatus();
        if (!promptUpdateStatus.value.update_inprogress) {
            stopPromptUpdatePolling();
        }
    }, 1000);
};

const stopPromptUpdatePolling = () => {
    if (promptUpdateInterval.value) {
        clearInterval(promptUpdateInterval.value);
        promptUpdateInterval.value = null;
    }
};

// ==========================================
// 6. SIGLIP 2 EMBEDDINGS STATE & METHODS
// ==========================================
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
        const res = await GetFromApi('ai-search/siglip-status');
        if (res) {
            siglipStatus.value = res;
        }
    } catch (e) {
        console.error('Error fetching SigLIP status:', e);
    }
};

const startSiglipIndexing = async (force = false) => {
    try {
        await PostToApi(`ai-search/rebuild-siglip?force=${force}`);
        await fetchSiglipStatus();
        startSiglipPolling();
    } catch (e) {
        console.error('Error starting SigLIP indexing:', e);
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

// Smooth scroll helper for active tasks banner
const scrollToCard = (id) => {
    const el = document.getElementById(id);
    if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
};

// Summary of all active background operations for persistent monitoring
const activeOperations = computed(() => {
    const list = [];
    if (isScanning.value || (scanStatus.value && !['idle', 'completed', 'error', ''].includes(scanStatus.value))) {
        list.push({
            id: 'library-scan',
            title: 'Image Library Scanner',
            status: scanStatus.value || 'scanning',
            percent: scanProgress.value || 0,
            message: scanStatusMessage.value || `${scanProcessed.value} / ${scanTotal.value || '?'} images`,
        });
    }
    if (civitaiStatus.value.status === 'running') {
        list.push({
            id: 'civitai-helper',
            title: 'Civitai Model Downloader',
            status: 'running',
            percent: civitaiProgress.value || 0,
            message: `${civitaiStatus.value.processed} / ${civitaiStatus.value.total} models`,
        });
    }
    if (phashStatus.value.status === 'running') {
        list.push({
            id: 'phash-indexer',
            title: 'pHash Indexer',
            status: 'running',
            percent: phashStatus.value.percent || 0,
            message: `${phashStatus.value.processed} / ${phashStatus.value.total} hashes`,
        });
    }
    if (pruneStatus.value.status === 'running') {
        list.push({
            id: 'library-prune',
            title: 'Database Pruner',
            status: 'running',
            percent: pruneStatus.value.percent || 0,
            message: `${pruneStatus.value.processed} / ${pruneStatus.value.total} records`,
        });
    }
    if (promptUpdateStatus.value.update_inprogress) {
        list.push({
            id: 'prompt-restoration',
            title: 'Prompt Restoration',
            status: 'running',
            percent: promptUpdateProgress.value || 0,
            message: `${promptUpdateStatus.value.update_processed} / ${promptUpdateStatus.value.update_total} files`,
        });
    }
    if (siglipStatus.value.status === 'running') {
        list.push({
            id: 'siglip-indexing',
            title: 'SigLIP 2 Embeddings',
            status: 'running',
            percent: siglipProgress.value || 0,
            message: `${siglipStatus.value.processed} / ${siglipStatus.value.total} vectors`,
        });
    }
    return list;
});

// Helper for status badge styling
const getStatusBadgeClass = (status) => {
    const s = String(status || '').toLowerCase();
    if (s === 'running' || s === 'scanning') {
        return 'bg-champagne/15 border-champagne/40 text-champagne';
    }
    if (s === 'completed') {
        return 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400';
    }
    if (s === 'error') {
        return 'bg-red-500/15 border-red-500/30 text-red-400';
    }
    if (s === 'cancelled') {
        return 'bg-amber-500/15 border-amber-500/30 text-amber-400';
    }
    return 'bg-dark-input border-slate text-ivory/50';
};

// Lifecycle
onMounted(async () => {
    // 1. Civitai helper
    await fetchCivitaiStatus();
    if (civitaiStatus.value.status === 'running') {
        startCivitaiPolling();
    }
    await fetchLocalModels();

    // 2. Library Image Scanner
    await fetchScanStatus();

    // 3. pHash
    await fetchPhashStatus();
    if (phashStatus.value.status === 'running') {
        startPhashPolling();
    }

    // 4. Prune
    await fetchPruneStatus();
    if (pruneStatus.value.status === 'running') {
        startPrunePolling();
    }

    // 5. Prompt Update
    await fetchPromptUpdateStatus();
    if (promptUpdateStatus.value.update_inprogress) {
        startPromptUpdatePolling();
    }

    // 6. SigLIP 2
    await fetchSiglipStatus();
    if (siglipStatus.value.status === 'running') {
        startSiglipPolling();
    }
});

onBeforeUnmount(() => {
    stopCivitaiPolling();
    stopPhashPolling();
    stopPrunePolling();
    stopPromptUpdatePolling();
    stopSiglipPolling();

    if (websocket.value && websocket.value.readyState !== WebSocket.CLOSED) {
        websocket.value.close();
    }
});
</script>

<style scoped>
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
