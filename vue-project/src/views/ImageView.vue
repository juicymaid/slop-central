<template>
  <div class="max-w-[1600px] mx-auto px-4 md:px-6 transition-colors duration-200 mb-12">
    <!-- Main Image Error -->
    <div v-if="loadError"
      class="mb-12 bg-panel border border-slate rounded-[2rem] shadow-lg p-10 transition-colors duration-200 text-center">
      <svg class="mx-auto h-16 w-16 text-red-500 mb-6" fill="none" stroke="currentColor" stroke-width="1.5"
        viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round"
          d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
      </svg>
      <h2 class="text-2xl font-serif font-bold italic text-ivory mb-2">Failed to load image</h2>
      <p class="text-ivory/60 font-sans mb-8">{{ loadError }}</p>
      <button @click="Refresh()"
        class="magnetic-button px-6 py-3 bg-slate hover:bg-panel text-champagne border border-champagne/30 rounded-full font-sans font-semibold transition-colors shadow-[0_0_15px_rgba(201,168,76,0.1)]">Try
        again</button>
    </div>

    <!-- Skeleton Loader -->
    <div v-else-if="isLoading && !currentPin"
      class="main-image-section mb-12 bg-panel border border-slate rounded-[3rem] shadow-lg p-6 md:p-8 transition-colors duration-200">
      <div class="flex flex-col lg:flex-row gap-8">
        <div class="w-full lg:w-[55%] xl:w-[60%] flex-shrink-0">
          <div class="skeleton rounded-[2rem] w-full aspect-[3/4]"></div>
          <div class="flex justify-center mt-3">
            <div class="skeleton h-7 w-28 rounded-full"></div>
          </div>
        </div>
        <div class="w-full lg:flex-1 min-w-0 space-y-4">
          <div class="flex justify-between">
            <div class="skeleton h-5 w-16 rounded"></div>
            <div class="skeleton h-10 w-32 rounded-full"></div>
          </div>
          <div class="flex gap-2 border-b border-slate pb-3">
            <div class="skeleton h-8 w-32 rounded-t-lg"></div>
            <div class="skeleton h-8 w-36 rounded-t-lg"></div>
          </div>
          <div class="skeleton h-6 w-full rounded"></div>
          <div class="skeleton h-6 w-5/6 rounded"></div>
          <div class="skeleton h-6 w-4/6 rounded"></div>
          <div class="skeleton h-4 w-3/4 rounded mt-2"></div>
          <div class="flex gap-2 mt-4">
            <div class="skeleton h-9 w-28 rounded-md"></div>
            <div class="skeleton h-9 w-20 rounded-md"></div>
            <div class="skeleton h-9 w-28 rounded-md"></div>
          </div>
          <div class="skeleton h-4 w-40 rounded mt-4"></div>
          <div class="skeleton h-3 w-full rounded mt-4"></div>
          <div class="skeleton h-3 w-2/3 rounded"></div>
        </div>
      </div>
    </div>

    <!-- Main Image Section -->
    <div v-else-if="currentPin"
      class="main-image-section mb-12 bg-panel-50 backdrop-blur-2xl border border-slate rounded-[3rem] shadow-[0_4px_25px_rgba(0,0,0,0.5)] p-4 sm:p-6 md:p-8 transition-colors duration-200">
      <div class="flex flex-col lg:flex-row gap-6 lg:gap-10">
        <!-- Image column: flexes wider on large screens -->
        <div class="w-full lg:w-[55%] xl:w-[60%] flex-shrink-0 relative">
          <div ref="imageContainerRef" class="relative flex items-center justify-center overflow-hidden rounded-[2rem] bg-obsidian border border-slate shadow-lg select-none">
            <img ref="imageRef" @click="handleImageClick" @load="updateOverlayRect" :src="ImageSrc(currentPin.Path)" :alt="currentPin.Title"
              class="w-full max-h-[85vh] object-contain transition-shadow"
              :class="isVisualSearchActive ? 'cursor-crosshair' : 'cursor-zoom-in hover:shadow-xl'">

            <!-- Visual Search Crop Overlay Layer -->
            <div v-if="isVisualSearchActive"
              class="absolute pointer-events-auto overflow-hidden touch-none"
              :style="cropOverlayStyle"
              @pointerdown="onBackdropPointerDown">

              <!-- Crop Box with outer shadow mask -->
              <div class="absolute border-2 border-white/90 rounded-2xl shadow-[0_0_0_9999px_rgba(0,0,0,0.55),0_0_15px_rgba(255,255,255,0.3)] touch-none cursor-move z-10"
                :style="{
                  left: `${cropBox.x * 100}%`,
                  top: `${cropBox.y * 100}%`,
                  width: `${cropBox.width * 100}%`,
                  height: `${cropBox.height * 100}%`
                }"
                @pointerdown.stop="onPointerDown($event, 'move')">

                <!-- 4 Pinterest-style Corner L-brackets -->
                <div class="absolute -top-[4px] -left-[4px] w-7 h-7 border-t-[5px] border-l-[5px] border-white rounded-tl-xl shadow-[0_0_8px_rgba(0,0,0,0.8)] cursor-nwse-resize pointer-events-auto z-20"
                  @pointerdown.stop="onPointerDown($event, 'nw')"></div>
                <div class="absolute -top-[4px] -right-[4px] w-7 h-7 border-t-[5px] border-r-[5px] border-white rounded-tr-xl shadow-[0_0_8px_rgba(0,0,0,0.8)] cursor-nesw-resize pointer-events-auto z-20"
                  @pointerdown.stop="onPointerDown($event, 'ne')"></div>
                <div class="absolute -bottom-[4px] -left-[4px] w-7 h-7 border-b-[5px] border-l-[5px] border-white rounded-bl-xl shadow-[0_0_8px_rgba(0,0,0,0.8)] cursor-nesw-resize pointer-events-auto z-20"
                  @pointerdown.stop="onPointerDown($event, 'sw')"></div>
                <div class="absolute -bottom-[4px] -right-[4px] w-7 h-7 border-b-[5px] border-r-[5px] border-white rounded-br-xl shadow-[0_0_8px_rgba(0,0,0,0.8)] cursor-nwse-resize pointer-events-auto z-20"
                  @pointerdown.stop="onPointerDown($event, 'se')"></div>

                <!-- 4 Edge handles for axial resizing -->
                <div class="absolute -top-2 left-1/2 -translate-x-1/2 w-10 h-4 flex items-center justify-center cursor-ns-resize pointer-events-auto z-20"
                  @pointerdown.stop="onPointerDown($event, 'n')">
                  <div class="w-8 h-1.5 bg-white/95 rounded-full shadow-[0_0_4px_rgba(0,0,0,0.6)]"></div>
                </div>
                <div class="absolute -bottom-2 left-1/2 -translate-x-1/2 w-10 h-4 flex items-center justify-center cursor-ns-resize pointer-events-auto z-20"
                  @pointerdown.stop="onPointerDown($event, 's')">
                  <div class="w-8 h-1.5 bg-white/95 rounded-full shadow-[0_0_4px_rgba(0,0,0,0.6)]"></div>
                </div>
                <div class="absolute top-1/2 -left-2 -translate-y-1/2 w-4 h-10 flex items-center justify-center cursor-ew-resize pointer-events-auto z-20"
                  @pointerdown.stop="onPointerDown($event, 'w')">
                  <div class="w-1.5 h-8 bg-white/95 rounded-full shadow-[0_0_4px_rgba(0,0,0,0.6)]"></div>
                </div>
                <div class="absolute top-1/2 -right-2 -translate-y-1/2 w-4 h-10 flex items-center justify-center cursor-ew-resize pointer-events-auto z-20"
                  @pointerdown.stop="onPointerDown($event, 'e')">
                  <div class="w-1.5 h-8 bg-white/95 rounded-full shadow-[0_0_4px_rgba(0,0,0,0.6)]"></div>
                </div>

                <!-- Center move indicator -->
                <div class="absolute inset-0 flex items-center justify-center pointer-events-none opacity-0 hover:opacity-100 transition-opacity">
                  <div class="p-2 bg-black/60 backdrop-blur-sm rounded-full text-white shadow-md">
                    <Move class="w-4 h-4" />
                  </div>
                </div>
              </div>
            </div>

            <!-- Top-left controls when visual search is active -->
            <div v-if="isVisualSearchActive" class="absolute top-4 left-4 z-30 flex items-center gap-2">
              <button @click.stop="closeVisualSearch"
                class="p-2.5 bg-obsidian/85 hover:bg-obsidian text-ivory rounded-full backdrop-blur-md border border-slate/60 hover:border-champagne/50 transition-all shadow-lg flex items-center justify-center cursor-pointer"
                title="Close visual search">
                <X class="w-5 h-5" />
              </button>
              <span class="px-3 py-1 bg-obsidian/85 backdrop-blur-md rounded-full text-xs font-mono text-champagne border border-slate/60 flex items-center gap-1.5 shadow-md">
                <Search class="w-3.5 h-3.5" /> Visual Search
              </span>
            </div>

            <!-- Bottom-right action buttons -->
            <div class="absolute bottom-4 right-4 z-30 flex gap-2">
              <div @click.stop="toggleVisualSearch"
                :class="[
                  'backdrop-blur-2xl rounded-2xl p-3 cursor-pointer transition-all shadow-lg border',
                  isVisualSearchActive
                    ? 'bg-champagne text-obsidian border-champagne shadow-[0_0_15px_rgba(201,168,76,0.35)] scale-105'
                    : 'bg-dark-input/60 hover:bg-dark-input text-ivory/70 hover:text-ivory border-slate/60 hover:border-champagne/40'
                ]"
                :title="isVisualSearchActive ? 'Close visual search' : 'Visual search / select area'">
                <Search class="w-5 h-5" :class="isVisualSearchActive ? 'text-obsidian stroke-[2.5]' : 'text-ivory/80'" />
              </div>
            </div>
          </div>
          <!-- Rank Badge -->
          <RouterLink :to="'/rate?id=' + currentPin.Id">
            <div class="mb-2 flex justify-center mt-2">
              <span :class="[
                'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold shadow-sm',
                rank.unrated
                  ? 'bg-slate/60 text-ivory/60 ring-1 ring-slate border border-dotted border-ivory/20'
                  : 'bg-champagne/15 text-champagne ring-1 ring-champagne/40'
              ]">
                <img :src="rankBadgeSrc(rank.tier)" :alt="(rank.label || 'Unranked') + ' badge'"
                  class="h-6 w-6 object-contain" />
                <span>{{ rank.label || 'Unranked' }}</span>
              </span>
            </div>
          </RouterLink>
          <!-- Star Rating Overlay -->
          <div class="absolute top-0 right-0 p-3 flex gap-2">
            <div class="p-2 bg-black/20 hover:bg-black/30 rounded-full flex items-center gap-1 transition-colors">
              <div class="flex" @click.prevent.stop="">
                <Star v-for="star in 5" :key="star"
                  class="w-5 h-5 text-white cursor-pointer transition-colors duration-150" :class="{
                    'fill-yellow-400 text-yellow-400': star <= (currentPin.Rating || 0),
                    'hover:fill-yellow-200 hover:text-yellow-200': star <= hoverRating
                  }" @click.prevent.stop="rateImage(star)" @mouseenter="hoverRating = star"
                  @mouseleave="hoverRating = 0" />
              </div>
              <p v-if="currentPin.Rating > 0" class="text-white ml-1 font-medium text-sm">{{
                currentPin.Rating.toFixed(1) }}</p>
            </div>
          </div>

          <div>
            
          </div>
        </div>

        <!-- Visual Search Results Column -->
        <div v-if="isVisualSearchActive" class="w-full lg:flex-1 min-w-0 relative flex flex-col h-full">
          <div class="flex items-center justify-between pb-4 mb-4 border-b border-slate">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-2xl bg-champagne/15 border border-champagne/30 flex items-center justify-center text-champagne shadow-sm">
                <Search class="w-5 h-5" />
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <h2 class="text-xl font-serif font-bold text-ivory">Visual Search</h2>
                  <span v-if="!isVisualSearching && visualSearchResults.length"
                    class="text-xs font-mono px-2.5 py-0.5 rounded-full bg-champagne/15 text-champagne border border-champagne/30">
                    {{ visualSearchResults.length }} results
                  </span>
                </div>
                <p class="text-xs text-ivory/50 mt-0.5">Move or resize the selection box on the image to update</p>
              </div>
            </div>
            <button @click="closeVisualSearch"
              class="magnetic-button px-4 py-2 bg-slate hover:bg-panel text-ivory border border-slate hover:border-champagne/30 rounded-full text-xs font-sans font-semibold transition-all flex items-center gap-1.5 shadow-sm cursor-pointer">
              <X class="w-4 h-4" />
              <span>Done</span>
            </button>
          </div>

          <!-- Visual search loading state -->
          <div v-if="isVisualSearching" class="columns-2 sm:columns-3 gap-3 flex-1 overflow-y-auto max-h-[78vh] pr-1">
            <div v-for="n in 9" :key="n" class="mb-3 break-inside-avoid">
              <div class="skeleton rounded-2xl w-full" :style="{ height: (160 + (n % 4) * 50) + 'px' }"></div>
            </div>
          </div>

          <!-- Visual search error state -->
          <div v-else-if="visualSearchError" class="p-8 text-center bg-slate/20 rounded-3xl border border-slate my-auto">
            <p class="text-red-400 text-sm mb-3">{{ visualSearchError }}</p>
            <button @click="triggerCropSearch"
              class="px-5 py-2 bg-champagne text-obsidian font-semibold text-xs rounded-full hover:brightness-110 transition-all cursor-pointer">
              Retry Search
            </button>
          </div>

          <!-- Visual search empty state -->
          <div v-else-if="visualSearchResults.length === 0" class="p-10 text-center bg-slate/20 rounded-3xl border border-slate my-auto">
            <Search class="w-10 h-10 text-ivory/30 mx-auto mb-3" />
            <p class="text-ivory/70 font-serif text-lg">No visually matching images found</p>
            <p class="text-ivory/40 text-xs mt-1">Try expanding or moving the selection box over a different region.</p>
          </div>

          <!-- Visual search results grid -->
          <div v-else class="columns-2 sm:columns-3 gap-3 flex-1 overflow-y-auto max-h-[78vh] pr-1">
            <div v-for="pin in visualSearchResults" :key="pin.Id" class="mb-3 break-inside-avoid">
              <Image :pin="pin" />
            </div>
          </div>
        </div>

        <!-- Details column (standard mode) -->
        <div v-else class="w-full lg:flex-1 min-w-0 relative">
          <div class="flex justify-between gap-0">
            <div class="flex gap-2 items-center text-ivory/60">
              <Eye class="w-5 h-5" />
              <p class="font-mono text-sm uppercase tracking-widest">{{ currentPin.Clicks }}</p>
              <Tv class="w-5 h-5" />
            </div>
            <div v-if="currentPin.in_boards.length == 0" class="flex items-center gap-3">
              <div
                class="magnetic-button rounded-full px-4 py-2 hover:bg-slate cursor-pointer font-sans font-semibold text-ivory flex items-center transition-colors border border-transparent hover:border-slate"
                @click="showBoardDropdown = !showBoardDropdown">
                <span class="relative z-10 flex">
                  {{ currentPin.recommended_boards[selectedBoard]?.name || '' }}
                  <ChevronDown class="w-5 h-5 ml-1 mt-0.5" />
                </span>
              </div>
              <button
                class="magnetic-button px-6 py-2.5 bg-champagne hover:brightness-110 text-obsidian rounded-full font-sans font-semibold transition-colors shadow-lg"
                @click="saveToBoard(currentPin.recommended_boards[selectedBoard].id)">
                <span class="relative z-10">Save</span>
              </button>
            </div>
            <div v-else class="flex items-center gap-3">
              <RouterLink :to="'/board/' + currentPin.in_boards[0].id">
                <div
                  class="magnetic-button rounded-full px-4 py-2 hover:bg-slate cursor-pointer font-sans font-semibold text-champagne flex items-center underline-offset-4 hover:underline transition-colors">
                  <span class="relative z-10">{{ currentPin.in_boards[0].name || '' }}</span>
                </div>
              </RouterLink>
              <button
                class="magnetic-button px-6 py-2.5 bg-slate hover:bg-panel text-ivory border border-slate hover:border-champagne/30 rounded-full cursor-pointer transition-colors shadow-sm"
                @click="removeFromBoard(currentPin.in_boards[0].id)">
                <span class="relative z-10">Saved</span>
              </button>
            </div>
            <div v-if="showBoardDropdown" class="absolute right-8 top-8 mt-2 z-20">
              <BoardDropDown :pin="currentPin" @save-to="(id) => saveToBoard(id)" />
            </div>
          </div>

          <div class="flex mt-6 mb-6 border-b border-slate">
            <button v-if="!currentPin.GeneratedPrompt && currentPin.Prompt" @click="activeTab = 'original'" :class="[
              'px-6 py-3 text-sm font-sans font-semibold transition-colors duration-300',
              activeTab === 'original'
                ? 'text-champagne border-b-2 border-champagne'
                : 'text-ivory/60 hover:text-ivory hover:bg-slate/30'
            ]">
              Original Prompt
            </button>
            <button @click="activeTab = 'generated'" :class="[
              'px-6 py-3 text-sm font-sans font-semibold transition-colors duration-300',
              activeTab === 'generated' || currentPin.GeneratedPrompt
                ? 'text-champagne border-b-2 border-champagne'
                : 'text-ivory/60 hover:text-ivory hover:bg-slate/30'
            ]">
              Generated Prompt
            </button>
          </div>

          <h1 v-if="activeTab === 'generated' || currentPin.GeneratedPrompt"
            class="text-2xl font-serif leading-relaxed mb-6 text-ivory/90" v-html="formatPromptText(displayPromptText)"
            @click="showTaggerTags = !showTaggerTags"></h1>
          <h1 v-else class="text-2xl font-serif leading-relaxed mb-6 text-ivory/90"
            v-html="formatPromptText(displayPromptText)"></h1>

          <div v-if="displayLoras.length" class="mb-6">
            <div class="flex items-center justify-between mb-2">
              <p class="text-ivory/60 font-mono text-xs uppercase tracking-widest">Loras</p>
              <button @click="copyLoras"
                class="text-[11px] px-2.5 py-1 bg-slate/60 hover:bg-slate border border-slate text-ivory/70 hover:text-ivory rounded-full transition-all">
                {{ lorasCopied ? 'Copied' : 'Copy' }}
              </button>
            </div>
            <div class="flex flex-wrap gap-2">
              <RouterLink v-for="(lora, index) in displayLoras" :key="`${lora.name}-${lora.weight}-${index}`"
                :to="{ path: `/models/lora:${lora.name}` }"
                class="magnetic-button text-xs px-3 py-1.5 bg-slate/50 hover:bg-slate border border-slate text-ivory/80 hover:text-ivory rounded-full flex items-center transition-all">
                <span class="relative z-10">{{ lora.name }}</span>
                <span v-if="lora.weight" class="relative z-10 ml-2 text-champagne">{{ lora.weight }}</span>
              </RouterLink>
            </div>
          </div>


          <div v-if="promptGenerating"
            class="flex items-center mt-6 mb-6 bg-champagne/10 p-4 rounded-[1rem] border border-champagne/20 transition-colors">
            <div class="animate-spin mr-4 h-5 w-5 text-champagne">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"></circle>
                <path class="opacity-75" fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
                </path>
              </svg>
            </div>
            <span class="text-champagne font-mono tracking-widest uppercase text-sm">Generating Prompt</span>
          </div>

          <div v-if="activeTab === 'generated' && currentPin.TaggerTags" class="mb-4 mt-2">
            <div v-if="showTaggerTags" class="space-y-1.5 mt-2">
              <div v-for="(value, tag) in Object.entries(currentPin.TaggerTags)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 15)
                .reduce((obj, [key, val]) => ({ ...obj, [key]: val }), {})" :key="tag" class="flex items-center">
                <span class="w-24 text-sm truncate text-ivory/50">{{ tag }}</span>
                <div class="flex-1 bg-slate rounded-full h-2 overflow-hidden">
                  <div class="h-full rounded-full bg-champagne/70" :style="{ width: `${Math.round(value * 100)}%` }">
                  </div>
                </div>
                <span class="ml-2 text-xs text-ivory/40 w-12 text-right">
                  {{ Math.round(value * 100) }}%
                </span>
              </div>
              <button v-if="Object.keys(currentPin.TaggerTags).length > 15"
                class="text-xs text-champagne/80 hover:text-champagne mt-1 transition-colors"
                @click.stop="showAllTags = !showAllTags">
                {{ showAllTags ? 'Show less' : `Show ${Object.keys(currentPin.TaggerTags).length - 15} more tags` }}
              </button>
              <div v-if="showAllTags" class="space-y-1.5 mt-1">
                <div v-for="(value, tag) in Object.entries(currentPin.TaggerTags)
                  .sort(([, a], [, b]) => b - a)
                  .slice(15)
                  .reduce((obj, [key, val]) => ({ ...obj, [key]: val }), {})" :key="tag" class="flex items-center">
                  <span class="w-24 text-sm truncate text-ivory/50">{{ tag }}</span>
                  <div class="flex-1 bg-slate rounded-full h-2 overflow-hidden">
                    <div class="h-full rounded-full bg-champagne/70" :style="{ width: `${Math.round(value * 100)}%` }">
                    </div>
                  </div>
                  <span class="ml-2 text-xs text-ivory/40 w-12 text-right">
                    {{ Math.round(value * 100) }}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div
            v-if="(activeTab == 'original' && currentPin.Prompt) || (activeTab == 'generated' && currentPin.taggerPrompt) || hasWorkflow"
            class="flex flex-wrap items-center mt-8 mb-6 gap-3">
            <button @click="copyPrompt(false)"
              class="magnetic-button text-sm px-5 py-2.5 bg-slate/50 hover:bg-slate border border-slate text-ivory/80 hover:text-ivory rounded-full flex items-center transition-all">
              <span class="relative z-10 flex">
                <span>Copy prompt</span>
                <span v-if="copied" class="ml-2 text-green-400">✓</span>
              </span>
            </button>
            <button v-if="hasWorkflow" @click="copyWorkflow"
              class="magnetic-button text-sm px-5 py-2.5 bg-slate/50 hover:bg-slate border border-slate text-ivory/80 hover:text-ivory rounded-full flex items-center transition-all">
              <span class="relative z-10 flex items-center">
                <span>Copy workflow</span>
                <span v-if="workflowCopied" class="ml-2 text-green-400">✓</span>
              </span>
            </button>
            <button @click="remixImage"
              class="magnetic-button text-sm px-5 py-2.5 bg-champagne/10 hover:bg-champagne/20 border border-champagne/30 text-champagne rounded-full flex items-center transition-all shadow-[0_0_10px_rgba(201,168,76,0.1)]">
              <span class="relative z-10 flex">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15">
                  </path>
                </svg>
                <span>Remix</span>
              </span>
            </button>

            <RouterLink :to="{ path: '/canvas', query: { image: currentPin.Id } }"
              class="magnetic-button text-sm px-5 py-2.5 bg-slate/50 hover:bg-slate border border-slate text-ivory/80 hover:text-ivory rounded-full flex items-center transition-all">
              <span class="relative z-10">Edit in Canvas</span>
            </RouterLink>

            <button @click="PostToApi(`open-image-location/${currentPin.Id}`)"
              class="magnetic-button text-sm px-5 py-2.5 bg-slate/50 hover:bg-slate border border-slate text-ivory/80 hover:text-ivory rounded-full flex items-center transition-all">
              <span class="relative z-10">Open File Location</span>
            </button>

            <button @click="uploadToCivitai"
              class="magnetic-button text-sm px-5 py-2.5 bg-slate/50 hover:bg-slate border border-slate text-ivory/80 hover:text-ivory rounded-full flex items-center transition-all">
              <span class="relative z-10">Upload to CivitAI</span>
            </button>
          </div>

          <!-- Post Author / Origin Section -->
          <div v-if="currentPin.post_info" class="mt-8 mb-6 p-5 rounded-2xl bg-panel border border-slate shadow-lg relative overflow-hidden group">
            <div class="absolute top-0 right-0 w-48 h-48 bg-gradient-to-br from-champagne/10 to-transparent rounded-full blur-2xl pointer-events-none -mr-16 -mt-16"></div>
            <div class="flex items-center justify-between mb-3 relative z-10">
              <span class="text-xs font-mono uppercase tracking-widest text-champagne font-semibold flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-champagne animate-pulse"></span>
                Post Origin
              </span>
              <span v-if="currentPin.post_info.post?.created_at" class="text-xs font-mono text-ivory/40">
                {{ formatPostTime(currentPin.post_info.post.created_at) }}
              </span>
            </div>

            <div class="flex items-start gap-4 relative z-10">
              <RouterLink :to="'/user/' + currentPin.post_info.character.id" class="shrink-0 group/avatar">
                <div class="relative">
                  <img :src="currentPin.post_info.character.avatar || 'https://images.unsplash.com/photo-1511275539165-cc46b1ee89bf?w=100&h=100&fit=crop'"
                    alt=""
                    class="w-14 h-14 rounded-full object-cover border-2 border-slate group-hover/avatar:border-champagne transition-all shadow-md group-hover/avatar:scale-105" />
                </div>
              </RouterLink>

              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <RouterLink :to="'/user/' + currentPin.post_info.character.id" class="font-sans font-bold text-ivory hover:text-champagne transition-colors truncate">
                    {{ currentPin.post_info.character.name }}
                  </RouterLink>
                  <span class="text-xs font-mono text-ivory/40">@{{ currentPin.post_info.character.id }}</span>
                </div>

                <p v-if="currentPin.post_info.post?.title" class="text-sm font-sans text-ivory/90 mt-1 line-clamp-2 leading-relaxed">
                  "{{ currentPin.post_info.post.title }}"
                </p>

                <div class="flex items-center gap-2 mt-3 flex-wrap">
                  <RouterLink :to="'/user/' + currentPin.post_info.character.id"
                    class="magnetic-button text-xs px-3.5 py-1.5 bg-champagne text-obsidian rounded-full font-sans font-semibold hover:brightness-110 transition-all flex items-center gap-1 shadow-sm">
                    <span>View Profile</span>
                  </RouterLink>
                  <RouterLink :to="'/chat/' + currentPin.post_info.character.id"
                    class="magnetic-button text-xs px-3.5 py-1.5 bg-slate/60 hover:bg-slate border border-slate text-ivory rounded-full font-sans font-medium transition-all flex items-center gap-1">
                    <span>Chat</span>
                  </RouterLink>
                  <RouterLink :to="'/posts'"
                    class="magnetic-button text-xs px-3.5 py-1.5 bg-slate/40 hover:bg-slate/80 border border-slate/60 text-ivory/70 hover:text-ivory rounded-full font-sans transition-all">
                    <span>All Posts</span>
                  </RouterLink>
                </div>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-6 mt-8 mb-4 border-b border-slate pb-6">
            <RouterLink :to="'/models/' + currentPin.ModelHash">
              <div class="group">
                <p class="text-ivory/60 font-mono text-xs uppercase tracking-widest mb-1">Model</p>
                <p class="text-ivory font-sans font-semibold group-hover:text-champagne transition-colors">
                  {{ modelName }}
                </p>
              </div>
            </RouterLink>

            <RouterLink v-if="currentPin.post_info?.character?.id" :to="'/chat/' + currentPin.post_info.character.id">
              <div class="group">
                <p class="text-ivory/60 font-mono text-xs uppercase tracking-widest mb-1">Actions</p>
                <p class="text-ivory font-sans font-semibold group-hover:text-champagne transition-colors">
                  Chat with {{ currentPin.post_info.character.name }}
                </p>
              </div>
            </RouterLink>
            <RouterLink v-else :to="'/posts'">
              <div class="group">
                <p class="text-ivory/60 font-mono text-xs uppercase tracking-widest mb-1">Actions</p>
                <p class="text-ivory font-sans font-semibold group-hover:text-champagne transition-colors">
                  Explore Characters
                </p>
              </div>
            </RouterLink>

            <div>

            </div>

          </div>

          <div v-if="currentPin.NegativePrompt" class="mb-4">
            <p class="text-ivory/40 font-mono text-xs uppercase tracking-widest mb-2">Negative Prompt</p>
            <p class="text-ivory/60 font-serif text-sm leading-relaxed mb-6 line-clamp-4">{{ currentPin.NegativePrompt
            }}</p>
          </div>



          <!-- Comments Expand Accordion -->
          <div class="flex justify-between items-center mt-6" @click="showComments = !showComments; GetComments()">
            <div class="flex items-center">
              <h2 class="text-xl font-bold mb-4 text-ivory">Comments</h2>
              <button v-if="showComments" class="ml-3 mb-3 p-1.5 rounded-full hover:bg-slate transition-colors"
                @click.stop="GetComments(true)">
                <svg class="w-4 h-4 text-ivory/50" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15">
                  </path>
                </svg>
              </button>
            </div>
            <button
              class="flex items-center text-sm text-ivory/50 hover:text-ivory transition-colors focus:outline-none focus:ring-2 focus:ring-champagne/50 rounded"
              :aria-expanded="showComments.toString()" :aria-label="showComments ? 'Hide comments' : 'Show comments'">
              <svg class="w-6 h-6 transform transition-transform duration-200" :class="{ 'rotate-180': showComments }"
                fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"></path>
              </svg>
            </button>
          </div>

          <!--Comments-->
          <div v-if="showComments" class="mt-4 mb-6">
            <div v-if="fetchingComments" class="space-y-4 p-2">
              <div v-for="n in 3" :key="n" class="flex items-start space-x-3">
                <div class="skeleton w-10 h-10 rounded-full flex-shrink-0"></div>
                <div class="flex-1 space-y-2">
                  <div class="skeleton h-4 w-24 rounded"></div>
                  <div class="skeleton h-3 w-full rounded"></div>
                  <div class="skeleton h-3 w-3/4 rounded"></div>
                </div>
              </div>
            </div>
            <div v-else-if="commentError" class="p-4 text-center">
              <p class="text-red-400 text-sm mb-2">{{ commentError }}</p>
              <button @click="GetComments(true)"
                class="text-sm px-3 py-1.5 bg-champagne/10 text-champagne rounded-md hover:bg-champagne/20 transition-colors">Retry</button>
            </div>
            <div v-else class="space-y-4">
              <div v-for="(comment, index) in comments" :key="comment.Id" class="flex items-start space-x-3">

                <RouterLink :to="'/user/' + (comment.character_id || comment.username)">
                  <img :src="comment.avatar || `${apiUrl}/random-image-file?user=${comment.username}`"
                    :alt="`${comment.username}'s avatar`" class="w-10 h-10 rounded-full object-cover" />
                </RouterLink>
                <div class="w-full">
                  <RouterLink :to="'/user/' + (comment.character_id || comment.username)"
                    class="hover:text-champagne transition-colors">
                    <p class="text-ivory font-semibold">{{ comment.username }}</p>
                  </RouterLink>
                  <p class="text-ivory/70">{{ comment.content }}</p>
                  <!-- Replies section -->
                  <div v-if="comment.replies && comment.replies.length > 0"
                    class="mt-3 pl-4 border-l-2 border-slate space-y-3">
                    <div v-for="reply in comment.replies" :key="reply.Id" class="flex items-start space-x-3">
                      <img :src="reply.avatar || `${apiUrl}/random-image-file?user=${reply.username}`"
                        :alt="`${reply.username}'s avatar`" class="w-10 h-10 rounded-full object-cover" />
                      <div>
                        <p class="text-ivory font-semibold text-sm">{{ reply.username }}</p>
                        <p class="text-ivory/70 text-sm">{{ reply.content }}</p>
                      </div>
                    </div>
                  </div>
                  <div class="flex">
                    <img :src="`${apiUrl}/files/automatic/avatar.png`" alt="Your avatar"
                      class="w-8 h-8 mt-2.5 mr-1 rounded-full object-cover border border-slate" />
                    <input type="text" v-model="comment.reply" placeholder="Reply..."
                      class="mt-2 w-full p-2 bg-dark-input border border-slate rounded-lg focus:outline-none focus:ring-2 focus:ring-champagne/50 text-ivory placeholder-ivory/30 text-sm transition-colors duration-200"
                      @keyup.enter="postReply(comment.reply, index)" />
                  </div>

                </div>

              </div>
              <!-- Add a comment section -->

              <div class="mt-4">
                <div class="flex items-start space-x-3">
                  <img :src="`${apiUrl}/files/automatic/avatar.png`" alt="Your avatar"
                    class="w-10 h-10 rounded-full object-cover border border-slate" />
                  <div class="w-full">
                    <textarea v-model="newComment" placeholder="Add a comment..."
                      class="w-full p-3 bg-dark-input border border-slate rounded-lg focus:outline-none focus:ring-2 focus:ring-champagne/50 text-ivory placeholder-ivory/30 text-sm transition-colors duration-200"
                      rows="2"></textarea>
                    <div class="flex justify-end mt-2">
                      <button @click="postComment"
                        class="px-4 py-2 bg-champagne hover:brightness-110 text-obsidian text-sm font-medium rounded-full transition-colors duration-200 shadow-sm hover:shadow disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
                        :disabled="!newComment.trim()">
                        Post
                      </button>
                    </div>
                  </div>
                </div>
              </div>

            </div>

          </div>

          <div v-if="currentPin.nsfw_levels" class="mb-4 mt-2">
            <div class="flex justify-between items-center cursor-pointer"
              @click="showContentRating = !showContentRating">
              <div class="text-sm font-medium text-ivory/70">
                Content Rating
                <span v-if="!showContentRating && currentPin.nsfw_levels" class="ml-2 px-2 py-0.5 text-xs rounded-full"
                  :style="{ backgroundColor: getLevelColor(getHighestNsfwLevel()), color: '#fff' }">
                  {{ getHighestNsfwLevel().charAt(0).toUpperCase() + getHighestNsfwLevel().slice(1) }}
                </span>
              </div>
              <svg class="w-5 h-5 transform transition-transform duration-200 text-ivory/50"
                :class="{ 'rotate-180': showContentRating }" fill="none" stroke="currentColor" stroke-width="2"
                viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"></path>
              </svg>
            </div>

            <div v-if="showContentRating" class="space-y-1.5 mt-2">
              <div v-for="(value, level) in Object.entries(currentPin.nsfw_levels)
                .sort(([, a], [, b]) => b - a)
                .reduce((obj, [key, val]) => ({ ...obj, [key]: val }), {})" :key="level" class="flex items-center">
                <span class="w-24 text-sm capitalize text-ivory/50">{{ level }}</span>
                <div class="flex-1 bg-slate rounded-full h-2.5 overflow-hidden">
                  <div class="h-full rounded-full" :style="{
                    width: `${Math.round(value * 100)}%`,
                    backgroundColor: getLevelColor(level)
                  }"></div>
                </div>
                <span class="ml-2 text-xs text-ivory/40 w-12 text-right">
                  {{ Math.round(value * 100) }}%
                </span>
              </div>
            </div>
          </div>

          <button @click="() => showMetadata = !showMetadata"
            class="mt-6 text-sm text-ivory/50 hover:text-ivory transition-colors">
            {{ showMetadata ? 'Hide metadata' : 'Show metadata' }} ↓
          </button>
          <div v-if="showMetadata" class="mt-6">
            <h2 class="text-xl font-bold mb-4 text-ivory">Metadata</h2>
            <div class="bg-slate/40 p-4 rounded-lg transition-colors">
              <a :href="apiUrl + '/image/' + currentPin.Id" class="text-champagne hover:underline" target="_blank">view
                data</a>
              <div class="">
                <p class="text-ivory/70"><strong class="text-ivory">Id:</strong>
                  {{ currentPin.Id }}</p>
                <p class="text-ivory/70"><strong class="text-ivory">Seed:</strong>
                  {{ currentPin.Seed }}</p>
                <p class="text-ivory/70"><strong class="text-ivory">Width:</strong> {{ currentPin.Width }}</p>
                <p class="text-ivory/70"><strong class="text-ivory">Height:</strong> {{ currentPin.Height }}</p>
                <p class="text-ivory/70"><strong class="text-ivory">Steps:</strong> {{ currentPin.Steps }}</p>
                <p class="text-ivory/70"><strong class="text-ivory">Sampler:</strong> {{ currentPin.Sampler }}</p>
                <p class="text-ivory/70"><strong class="text-ivory">CFG
                    Scale:</strong> {{ currentPin.CFGScale }}</p>
                <p class="text-ivory/70"><strong class="text-ivory">phash:</strong> {{ currentPin.pHash }}</p>
                <p class="text-ivory/70"><strong class="text-ivory">FileName:</strong> {{ currentPin.FileName }}</p>
                <p class="text-ivory/70"><strong class="text-ivory">Path:</strong>
                  {{ currentPin.AbsolutePath || currentPin.Path }}</p>
                <p class="text-ivory/70"><strong class="text-ivory">CreatedDate:</strong> {{
                  formatDate(currentPin.CreatedDate)
                }}
                </p>
                <p class="text-ivory/70"><strong class="text-ivory">ModelHash:</strong> {{ currentPin.ModelHash }}</p>
                <p class="text-ivory/70"><strong class="text-ivory">Description:</strong>
                  <span v-if="currentPin.description" style="white-space: pre-line;">{{ currentPin.description }}</span>
                  <span v-else>N/A</span>
                </p>
                <p v-if="hasWorkflow" class="text-ivory/70"><strong class="text-ivory">Workflow:</strong>
                  <button @click="copyWorkflow" class="text-champagne hover:underline ml-1 cursor-pointer">
                    Copy workflow JSON
                  </button>
                  <span v-if="workflowCopied" class="ml-2 text-green-400">✓</span>
                </p>
              </div>
            </div>
          </div>


        </div>
      </div>
    </div>
    <div v-if="currentPin?.variations.length > 0" class="mt-8">
      <h2 class="text-2xl font-serif font-bold italic mb-6 text-ivory">Variations</h2>
      <div class="columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4">
        <Image v-for="pin in currentPin.variations" :key="pin.Id" :pin="pin" />
      </div>
    </div>
    <div v-if="currentPin?.identical_images.length > 0" class="mt-8">
      <h2 class="text-2xl font-serif font-bold italic mb-6 text-ivory">Identical Images</h2>
      <div class="columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4">
        <Image v-for="pin in currentPin.identical_images" :key="pin.Id" :pin="pin" />
      </div>
    </div>

  </div>
  <!-- Recommendations Section -->
  <div class=" mx-auto px-4 md:px-6 mt-12">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-xl font-bold text-ivory">More like this</h2>
      <select v-model="similarityMode" @change="RefreshRecommendations"
        class="bg-panel border border-slate text-ivory rounded-lg px-3 py-1.5 focus:outline-none focus:border-champagne text-sm cursor-pointer">
        <option value="full">Full Similarity</option>
        <option value="prompt">Prompt Only</option>
        <option value="hash">Visual Only</option>
        <option value="embedding">Neural (SigLIP)</option>
      </select>
    </div>
    <!-- Rec Error -->
    <div v-if="recError" class="bg-panel border border-slate rounded-xl shadow p-8 text-center">
      <svg class="mx-auto h-10 w-10 text-red-400 mb-3" fill="none" stroke="currentColor" stroke-width="1.5"
        viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round"
          d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
      </svg>
      <p class="text-ivory/50 mb-4">{{ recError }}</p>
      <button @click="retryRecommendations()"
        class="px-4 py-2 bg-champagne hover:brightness-110 text-obsidian rounded-lg text-sm font-medium transition-colors">Retry</button>
    </div>
    <!-- Rec Skeleton -->
    <div v-else-if="isLoading && recommendations.length === 0"
      class="columns-2 md:columns-3 lg:columns-4 xl:columns-5 gap-4 space-y-4">
      <div v-for="n in 12" :key="n" class="break-inside-avoid">
        <div class="skeleton rounded-lg w-full" :style="{ height: (180 + (n % 3) * 80) + 'px' }"></div>
      </div>
    </div>
    <ImageMasonry v-else :pins="recommendations" />
  </div>

  <!-- Tag color settings modal -->
  <div v-if="showTagColorSettings" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-panel border border-slate rounded-2xl p-6 max-w-md w-full shadow-xl">
      <h3 class="text-xl font-bold mb-4 text-ivory">Tag Color Settings</h3>
      <div class="space-y-4">
        <div v-for="(color, type) in tagColors" :key="type" class="flex items-center justify-between">
          <span class="text-ivory/70">{{ tagTypeToName(type) }}</span>
          <input type="color" v-model="tagColors[type]" class="w-10 h-10 rounded cursor-pointer" />
        </div>
      </div>
      <div class="flex justify-end mt-6 space-x-3">
        <button @click="resetTagColors"
          class="px-4 py-2 bg-slate hover:bg-slate/80 text-ivory rounded-lg transition-colors">
          Reset to Default
        </button>
        <button @click="saveTagColors"
          class="px-4 py-2 bg-champagne hover:brightness-110 text-obsidian rounded-lg transition-colors">
          Save
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount, inject, computed, nextTick } from 'vue'
import { apiUrl, GetFromApi, ImageSrc, PostToApi, webState } from '../api'
import Image from '../components/Image.vue'
import { useRoute } from 'vue-router'
import { Star, ChevronDown, Eye, Tv, Search, X, Move } from 'lucide-vue-next'
import BoardDropDown from '@/components/BoardDropDown.vue'
import ImageMasonry from '@/components/ImageMasonry.vue'
import { api as viewerApi } from 'v-viewer'

const selectedBoard = ref(0)
const copied = ref(false)
const lorasCopied = ref(false)
const workflowCopied = ref(false)
const isDarkMode = inject('isDarkMode', ref(false))
const hoverRating = ref(0)
const showComments = ref(false)
const showAllTags = ref(false)
const showTagColorSettings = ref(false)


// Visual Search State
const isVisualSearchActive = ref(false)
const visualSearchResults = ref([])
const isVisualSearching = ref(false)
const visualSearchError = ref(null)
const imageContainerRef = ref(null)
const imageRef = ref(null)

const cropBox = ref({ x: 0.15, y: 0.15, width: 0.7, height: 0.7 })
const cropOverlayRect = ref({ left: 0, top: 0, width: 0, height: 0 })

const cropOverlayStyle = computed(() => {
  if (cropOverlayRect.value.width > 0 && cropOverlayRect.value.height > 0) {
    return {
      left: `${cropOverlayRect.value.left}px`,
      top: `${cropOverlayRect.value.top}px`,
      width: `${cropOverlayRect.value.width}px`,
      height: `${cropOverlayRect.value.height}px`
    }
  }
  return {
    left: '0px',
    top: '0px',
    width: '100%',
    height: '100%'
  }
})

let activeHandle = null
let dragStartPointer = { x: 0, y: 0 }
let dragStartCropBox = { x: 0.15, y: 0.15, width: 0.7, height: 0.7 }
let searchSeq = 0

function updateOverlayRect() {
  const img = imageRef.value || (typeof document !== 'undefined' ? document.querySelector('.main-image-section img') : null)
  if (!img) return
  const naturalW = img.naturalWidth || img.width || 1
  const naturalH = img.naturalHeight || img.height || 1
  const clientW = img.clientWidth || img.offsetWidth || 0
  const clientH = img.clientHeight || img.offsetHeight || 0

  if (!clientW || !clientH) return

  const naturalAspect = naturalW / naturalH
  const clientAspect = clientW / clientH

  let renderedW = clientW
  let renderedH = clientH
  let offsetLeft = 0
  let offsetTop = 0

  if (clientAspect > naturalAspect) {
    renderedH = clientH
    renderedW = clientH * naturalAspect
    offsetLeft = (clientW - renderedW) / 2
  } else {
    renderedW = clientW
    renderedH = clientW / naturalAspect
    offsetTop = (clientH - renderedH) / 2
  }

  cropOverlayRect.value = {
    left: Math.round(offsetLeft),
    top: Math.round(offsetTop),
    width: Math.round(renderedW),
    height: Math.round(renderedH)
  }
}

function clamp(val, min, max) {
  return Math.max(min, Math.min(max, val))
}

function toggleVisualSearch() {
  isVisualSearchActive.value = !isVisualSearchActive.value
  if (isVisualSearchActive.value) {
    cropBox.value = { x: 0.15, y: 0.15, width: 0.7, height: 0.7 }
    nextTick(() => {
      updateOverlayRect()
      triggerCropSearch()
    })
  }
}

function closeVisualSearch() {
  isVisualSearchActive.value = false
}

function handleImageClick() {
  if (isVisualSearchActive.value) return
  showFullscreen()
}

async function triggerCropSearch() {
  if (!currentPin.value || !isVisualSearchActive.value) return
  const currentSeq = ++searchSeq
  isVisualSearching.value = true
  visualSearchError.value = null
  try {
    const res = await PostToApi('similar-images/crop', {
      image_id: currentPin.value.Id,
      x: cropBox.value.x,
      y: cropBox.value.y,
      width: cropBox.value.width,
      height: cropBox.value.height,
      per_page: 30,
      exclude_self: true
    })
    if (currentSeq === searchSeq) {
      visualSearchResults.value = Array.isArray(res) ? res : []
    }
  } catch (err) {
    if (currentSeq === searchSeq) {
      visualSearchError.value = 'Failed to load visual search results.'
      console.error('Visual search error:', err)
    }
  } finally {
    if (currentSeq === searchSeq) {
      isVisualSearching.value = false
    }
  }
}

function onPointerDown(e, handle) {
  e.preventDefault()
  e.stopPropagation()
  try {
    e.target.setPointerCapture(e.pointerId)
  } catch {}
  activeHandle = handle
  dragStartPointer = { x: e.clientX, y: e.clientY }
  dragStartCropBox = { ...cropBox.value }
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)
  window.addEventListener('pointercancel', onPointerUp)
}

function onBackdropPointerDown(e) {
  e.preventDefault()
  e.stopPropagation()
  if (!imageContainerRef.value || cropOverlayRect.value.width <= 0) return
  const rect = e.currentTarget.getBoundingClientRect()
  const clickX = clamp((e.clientX - rect.left) / rect.width, 0, 1)
  const clickY = clamp((e.clientY - rect.top) / rect.height, 0, 1)

  try {
    e.target.setPointerCapture(e.pointerId)
  } catch {}

  activeHandle = 'draw'
  dragStartPointer = { x: e.clientX, y: e.clientY }
  dragStartCropBox = { x: clickX, y: clickY, width: 0.05, height: 0.05 }
  cropBox.value = { x: clickX, y: clickY, width: 0.05, height: 0.05 }

  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)
  window.addEventListener('pointercancel', onPointerUp)
}

function onPointerMove(e) {
  if (!activeHandle || cropOverlayRect.value.width <= 0 || cropOverlayRect.value.height <= 0) return

  const overlayW = cropOverlayRect.value.width
  const overlayH = cropOverlayRect.value.height
  const dx = (e.clientX - dragStartPointer.x) / overlayW
  const dy = (e.clientY - dragStartPointer.y) / overlayH
  const MIN_SIZE = 0.05

  if (activeHandle === 'move') {
    const newX = clamp(dragStartCropBox.x + dx, 0, 1 - dragStartCropBox.width)
    const newY = clamp(dragStartCropBox.y + dy, 0, 1 - dragStartCropBox.height)
    cropBox.value = {
      ...cropBox.value,
      x: Number(newX.toFixed(4)),
      y: Number(newY.toFixed(4))
    }
  } else if (activeHandle === 'se') {
    const newW = clamp(dragStartCropBox.width + dx, MIN_SIZE, 1 - dragStartCropBox.x)
    const newH = clamp(dragStartCropBox.height + dy, MIN_SIZE, 1 - dragStartCropBox.y)
    cropBox.value = { ...cropBox.value, width: Number(newW.toFixed(4)), height: Number(newH.toFixed(4)) }
  } else if (activeHandle === 'nw') {
    const newX = clamp(dragStartCropBox.x + dx, 0, dragStartCropBox.x + dragStartCropBox.width - MIN_SIZE)
    const newY = clamp(dragStartCropBox.y + dy, 0, dragStartCropBox.y + dragStartCropBox.height - MIN_SIZE)
    const newW = (dragStartCropBox.x + dragStartCropBox.width) - newX
    const newH = (dragStartCropBox.y + dragStartCropBox.height) - newY
    cropBox.value = { x: Number(newX.toFixed(4)), y: Number(newY.toFixed(4)), width: Number(newW.toFixed(4)), height: Number(newH.toFixed(4)) }
  } else if (activeHandle === 'ne') {
    const newY = clamp(dragStartCropBox.y + dy, 0, dragStartCropBox.y + dragStartCropBox.height - MIN_SIZE)
    const newW = clamp(dragStartCropBox.width + dx, MIN_SIZE, 1 - dragStartCropBox.x)
    const newH = (dragStartCropBox.y + dragStartCropBox.height) - newY
    cropBox.value = { ...cropBox.value, y: Number(newY.toFixed(4)), width: Number(newW.toFixed(4)), height: Number(newH.toFixed(4)) }
  } else if (activeHandle === 'sw') {
    const newX = clamp(dragStartCropBox.x + dx, 0, dragStartCropBox.x + dragStartCropBox.width - MIN_SIZE)
    const newH = clamp(dragStartCropBox.height + dy, MIN_SIZE, 1 - dragStartCropBox.y)
    const newW = (dragStartCropBox.x + dragStartCropBox.width) - newX
    cropBox.value = { ...cropBox.value, x: Number(newX.toFixed(4)), width: Number(newW.toFixed(4)), height: Number(newH.toFixed(4)) }
  } else if (activeHandle === 'n') {
    const newY = clamp(dragStartCropBox.y + dy, 0, dragStartCropBox.y + dragStartCropBox.height - MIN_SIZE)
    const newH = (dragStartCropBox.y + dragStartCropBox.height) - newY
    cropBox.value = { ...cropBox.value, y: Number(newY.toFixed(4)), height: Number(newH.toFixed(4)) }
  } else if (activeHandle === 's') {
    const newH = clamp(dragStartCropBox.height + dy, MIN_SIZE, 1 - dragStartCropBox.y)
    cropBox.value = { ...cropBox.value, height: Number(newH.toFixed(4)) }
  } else if (activeHandle === 'w') {
    const newX = clamp(dragStartCropBox.x + dx, 0, dragStartCropBox.x + dragStartCropBox.width - MIN_SIZE)
    const newW = (dragStartCropBox.x + dragStartCropBox.width) - newX
    cropBox.value = { ...cropBox.value, x: Number(newX.toFixed(4)), width: Number(newW.toFixed(4)) }
  } else if (activeHandle === 'e') {
    const newW = clamp(dragStartCropBox.width + dx, MIN_SIZE, 1 - dragStartCropBox.x)
    cropBox.value = { ...cropBox.value, width: Number(newW.toFixed(4)) }
  } else if (activeHandle === 'draw') {
    const startX = dragStartCropBox.x
    const startY = dragStartCropBox.y
    const currX = clamp(startX + dx, 0, 1)
    const currY = clamp(startY + dy, 0, 1)

    const x = Math.min(startX, currX)
    const y = Math.min(startY, currY)
    const width = Math.max(MIN_SIZE, Math.abs(currX - startX))
    const height = Math.max(MIN_SIZE, Math.abs(currY - startY))

    cropBox.value = {
      x: Number(clamp(x, 0, 1 - width).toFixed(4)),
      y: Number(clamp(y, 0, 1 - height).toFixed(4)),
      width: Number(width.toFixed(4)),
      height: Number(height.toFixed(4))
    }
  }
}

function onPointerUp(e) {
  if (activeHandle) {
    try {
      if (e?.target?.releasePointerCapture && e?.pointerId != null) {
        e.target.releasePointerCapture(e.pointerId)
      }
    } catch {}
    activeHandle = null
    window.removeEventListener('pointermove', onPointerMove)
    window.removeEventListener('pointerup', onPointerUp)
    window.removeEventListener('pointercancel', onPointerUp)
    triggerCropSearch()
  }
}
function formatPostTime(timestamp) {
  if (!timestamp) return ''
  const d = new Date(timestamp * 1000)
  const now = new Date()
  const diff = (now - d) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return Math.floor(diff / 60) + 'm ago'
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago'
  if (diff < 604800) return Math.floor(diff / 86400) + 'd ago'
  return d.toLocaleDateString()
}

// Default color scheme for tag types
const defaultTagColors = {
  6: '#D3D3D3', // Other Light gray
  0: '#ffffff', // General - White
  1: '#337ab7', // Artist - Blue
  3: '#f0ad4e', // Copyright - Orange
  4: '#d9534f', // Character - Red
  5: '#808080', // Meta - dark gray
};

// User customizable color scheme
const tagColors = ref(JSON.parse(localStorage.getItem('tagColors')) || { ...defaultTagColors });

function tagTypeToName(type) {
  const types = {
    0: 'General',
    1: 'Artist',
    3: 'Copyright',
    4: 'Character',
    5: 'Meta'
  };
  return types[type] || `Type ${type}`;
}

function resetTagColors() {
  tagColors.value = { ...defaultTagColors };
}

function saveTagColors() {
  localStorage.setItem('tagColors', JSON.stringify(tagColors.value));
  showTagColorSettings.value = false;
}

function copyPrompt(full = false) {
  if (!currentPin.value) return

  let promptString = ''

  if (activeTab.value == 'original') {
    promptString = currentPin.value.Prompt
  } else {
    promptString = currentPin.value.taggerPrompt
  }

  let prompt = promptString
    + "\nNegative prompt: " + currentPin.value.NegativePrompt
    + "\n Steps: " + currentPin.value.Steps
    + ", Sampler: " + currentPin.value.Sampler
    + ", CFG scale: " + currentPin.value.CFGScale
    + ", Seed: " + currentPin.value.Seed
    + ", Size: " + currentPin.value.Width + "x" + currentPin.value.Height

  if (!full) {
    prompt = promptString
  }

  navigator.clipboard.writeText(prompt)
    .then(() => {
      copied.value = true
      setTimeout(() => {
        copied.value = false
      }, 2000)
    })
    .catch(err => {
      console.error('Failed to copy prompt: ', err)
    })
}

function copyLoras() {
  if (!displayLoras.value.length) return

  const loraText = displayLoras.value
    .map((lora) => lora.full || `<lora:${lora.name}:${lora.weight}>`)
    .join(', ')

  navigator.clipboard.writeText(loraText)
    .then(() => {
      lorasCopied.value = true
      setTimeout(() => {
        lorasCopied.value = false
      }, 2000)
    })
    .catch(err => {
      console.error('Failed to copy loras: ', err)
    })
}

const workflowString = computed(() => {
  if (!currentPin.value || !currentPin.value.Workflow) return ''
  const wf = currentPin.value.Workflow
  if (typeof wf === 'object') {
    if (Object.keys(wf).length === 0) return ''
    try {
      return JSON.stringify(wf, null, 2)
    } catch (e) {
      return ''
    }
  }
  if (typeof wf === 'string') {
    const trimmed = wf.trim()
    if (!trimmed || trimmed === '{}' || trimmed === '[]' || trimmed === 'null' || trimmed === '""') return ''
    try {
      const parsed = JSON.parse(trimmed)
      if (parsed && typeof parsed === 'object' && (Array.isArray(parsed) ? parsed.length > 0 : Object.keys(parsed).length > 0)) {
        return JSON.stringify(parsed, null, 2)
      }
      return ''
    } catch (e) {
      return trimmed
    }
  }
  return ''
})

const hasWorkflow = computed(() => !!workflowString.value)

function copyWorkflow() {
  if (!workflowString.value) return

  navigator.clipboard.writeText(workflowString.value)
    .then(() => {
      workflowCopied.value = true
      setTimeout(() => {
        workflowCopied.value = false
      }, 2000)
    })
    .catch(err => {
      console.error('Failed to copy workflow: ', err)
    })
}

const route = useRoute()
const currentPin = ref(null)
const recommendations = ref([])
const similarityMode = ref('embedding')

const rank = ref({})

let page = 1
const isLoading = ref(false)
const hasScrolledPastImage = ref(false)

const showBoardDropdown = ref(false)

const showMetadata = ref(false)

const promptGenerating = ref(false)

const activeTab = ref('original')

const comments = ref([])
const fetchingComments = ref(false)

const showTaggerTags = ref(false)
const showContentRating = ref(false)

const loadError = ref(null)
const recError = ref(null)
const commentError = ref(null)

const displayPromptRaw = computed(() => {
  if (!currentPin.value) return ''
  if (activeTab.value === 'generated' || currentPin.value.GeneratedPrompt) {
    return currentPin.value.taggerPrompt || ''
  }
  return currentPin.value.Prompt || ''
})

const displayPromptText = computed(() => stripLoraTags(displayPromptRaw.value))
const displayLoras = computed(() => dedupeLoras(extractLoras(displayPromptRaw.value)))
const modelName = computed(() => {
  if (!currentPin.value) return ''
  if (Array.isArray(currentPin.value.Model)) {
    try {
      const workflow = JSON.parse(currentPin.value.Workflow ?? '{}')
      const nodeId = parseFloat(currentPin.value.Model[0] ?? '')
      const node = workflow?.nodes?.find((n) => n.id === nodeId)
      const val = node?.widgets_values?.[currentPin.value.Model[1] ?? 0]
      if (typeof val === 'string') {
        return val.replace(".safetensors", "")
      }
      return val != null ? String(val) : ''
    } catch (e) {
      console.error('Error parsing workflow for model name:', e)
      return ''
    }
  }
  return currentPin.value.Model ?? currentPin.value.ModelHash ?? ''
})

function pinsMatch(a, b) {
  if (!a || !b) return false
  if (a.Id && b.Id && a.Id === b.Id) return true
  if (a.Path && b.Path && a.Path.toLowerCase() === b.Path.toLowerCase()) return true
  return false
}
function dedupePins(pins = []) {
  return pins.filter((pin, idx, arr) => arr.findIndex(candidate => pinsMatch(candidate, pin)) === idx)
}
function filterUniquePins(existing = [], incoming = []) {
  return incoming.filter(pin => !existing.some(existingPin => pinsMatch(existingPin, pin)))
}

const loadMore = async () => {
  if (isLoading.value) return
  isLoading.value = true
  try {
    page++
    const newData = await GetFromApi(`similar-images/${route.params.id}?per_page=20&page=${page}&mode=${similarityMode.value}`)
    const uniqueNewData = filterUniquePins(recommendations.value, dedupePins(newData))
    recommendations.value = [...recommendations.value, ...uniqueNewData]
  } catch (err) {
    page-- // revert so next scroll attempt retries the same page
    console.error('Error loading more recommendations:', err)
  } finally {
    isLoading.value = false
  }
}

const handleScroll = () => {
  // Check if scrolled past the current image
  const imageSection = document.querySelector('.main-image-section')
  if (imageSection) {
    const rect = imageSection.getBoundingClientRect()
    hasScrolledPastImage.value = rect.bottom < 0
  }


  if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 10) {
    loadMore()
  }
}

// Convert Windows FileTime to JavaScript Date and format it
function formatDate(fileTime) {
  if (!fileTime) return 'N/A';

  // Windows FileTime is measured in 100-nanosecond intervals since January 1, 1601 UTC
  // First, convert to milliseconds by dividing by 10,000
  const windowsEpochInMilliseconds = fileTime / 10000;

  // Windows epoch starts on January 1, 1601 UTC
  // JavaScript epoch starts on January 1, 1970 UTC
  // The difference is 11,644,473,600,000 milliseconds
  const epochDifference = 11644473600000;

  // Convert to JavaScript timestamp
  const jsTimestamp = windowsEpochInMilliseconds - epochDifference;

  // Create a Date object
  const date = new Date(jsTimestamp);

  // Format the date as a string
  return date.toLocaleString();
}

//watch for changes in activetab
watch(activeTab, async (newTab) => {
  if (newTab === 'generated') {
    if (!promptGenerating.value && !currentPin.value.taggerPrompt) {
      promptGenerating.value = true
      await PostToApi("generate_tagger_prompt_for/" + currentPin.value.Id)
      promptGenerating.value = false
      Refresh()
      activeTab.value = 'generated'
    }
  }
})



let tag_data = {}

/**
 * Function to format prompt text by coloring tags and making them clickable links to /search?q=tag.
 * LoRA tags are stripped before formatting and shown in the LoRAs section.
 * Adds underline on hover and pointer cursor.
 */
function formatPromptText(promptText) {
  if (!promptText) return '';

  // Helper to escape HTML special characters
  function escapeHtml(text) {
    return text.replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Create a clickable tag link with color
  function tagLink(text, color, queryOverride) {
    const query = queryOverride != null ? queryOverride : text.trim();
    const href = `/search?q=${encodeURIComponent(query)}`;
    return `<a href="${href}" style="color: ${color}; text-decoration: none;" class="hover:underline cursor-pointer">${escapeHtml(text)}</a>`;
  }

  const sanitizedText = promptText.replace(/<lora:[^>]+>/gi, ' ');

  // Split by comma, semicolon, or newline, but keep delimiters for coloring
  const tagRegex = /([^,;\n]+)([;,]|\n)?/g;
  let match;
  let html = '';

  while ((match = tagRegex.exec(sanitizedText)) !== null) {
    let tag = match[1].trim();
    let delimiter = match[2] || '';

    const normalizedTag = tag.toLowerCase().replace(/[\s_]+/g, '_').replace(/[^a-z0-9_]/g, '').replace('(', '').replace(')', '');
    const alternateTag = tag.toLowerCase();
    let tagType = tag_data[normalizedTag] || tag_data[alternateTag];
    if (tagType == undefined) tagType = 6;
    const color = tagColors.value[tagType] || 'inherit';
    html += tagLink(tag, color);

    // Add colored delimiter if present (not clickable)
    if (delimiter) {
      const normalizedTag = tag.toLowerCase().replace(/[\s_]+/g, '_');
      const alternateTag = tag.toLowerCase();
      let tagType = tag_data[normalizedTag] || tag_data[alternateTag];
      if (tagType == undefined) tagType = 6;
      const color = tagColors.value[tagType] || 'inherit';
      html += `<span style="color: ${color};">${escapeHtml(delimiter)} </span>`;
    }
  }

  return html;
}

function extractLoras(promptText) {
  if (!promptText) return [];
  const loraRegex = /<lora:([^:>]+):([^>]+)>/gi;
  const loras = [];
  let match;
  while ((match = loraRegex.exec(promptText)) !== null) {
    loras.push({
      name: match[1].trim(),
      weight: match[2].trim(),
      full: match[0]
    });
  }
  return loras;
}

function dedupeLoras(loras = []) {
  const seen = new Set();
  return loras.filter((lora) => {
    const key = `${lora.name}:${lora.weight}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function stripLoraTags(promptText) {
  if (!promptText) return '';
  const loraRegex = /<lora:[^>]+>/gi;
  const withoutLoras = promptText.replace(loraRegex, ' ');
  const tokens = withoutLoras
    .split(/[,;\n]/)
    .map((part) => part.trim())
    .filter(Boolean);
  return tokens.join(', ');
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

async function GetComments(override = false) {
  if (comments.value.length > 0 && !override)
    return

  fetchingComments.value = true
  commentError.value = null

  try {
    comments.value = await GetFromApi('comments/' + currentPin.value.Id + "?override=" + override)
  } catch (err) {
    commentError.value = 'Could not load comments.'
    console.error('Error loading comments:', err)
  } finally {
    fetchingComments.value = false
  }
}
const newComment = ref('')
async function postComment() {
  comments.value.push({
    content: newComment.value,
    username: 'you',
    replies: []
  })
  var encodedComment = encodeURIComponent(newComment.value)
  newComment.value = ''
  await PostToApi('comments/' + currentPin.value.Id + '/comment?message=' + encodedComment)

  comments.value = await GetFromApi('comments/' + currentPin.value.Id)
}

function getHighestNsfwLevel() {
  if (!currentPin.value || !currentPin.value.nsfw_levels) return 'general';

  // Find the highest level based on the values
  const levels = Object.entries(currentPin.value.nsfw_levels);
  if (levels.length === 0) return 'general';

  // Sort levels by value (descending) and return the first one
  const highestLevel = levels.sort(([, a], [, b]) => b - a)[0][0];
  return highestLevel;
}

async function postReply(reply, index) {

  //make sure replies is an array
  if (!comments.value[index].replies)
    comments.value[index].replies = []

  comments.value[index].replies.push({
    content: reply,
    username: 'you'
  })
  var encodedReply = encodeURIComponent(reply)
  comments.value[index].reply = ''
  await PostToApi('comments/' + currentPin.value.Id + '/reply/' + index + '?message=' + encodedReply)
  comments.value = await GetFromApi('comments/' + currentPin.value.Id)
}

onMounted(async () => {
  Refresh()
  window.addEventListener('scroll', handleScroll)
  window.addEventListener('resize', updateOverlayRect)
  //scroll to the top of the page on mount
  window.scrollTo(0, 0)

  try {
    const response = await fetch("/tags.csv")
    const text = await response.text()

    const lines = text.split('\n')

    for (let line of lines) {
      if (!line.trim()) continue

      // Basic CSV parsing (handles simple cases)
      let parts = line.split(',')
      if (parts.length >= 2) {
        const name = parts[0].toLowerCase()
        const type = parseInt(parts[1])

        if (!isNaN(type)) {
          tag_data[name] = type

          // Also add version without underscores to help with matching
          const nameWithoutUnderscores = name.replace(/_/g, ' ')
          if (nameWithoutUnderscores !== name) {
            tag_data[nameWithoutUnderscores] = type
          }
        }
      }
    }
    console.log("Loaded", Object.keys(tag_data).length, "tags")
  } catch (error) {
    console.error("Error loading tag data:", error)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('resize', updateOverlayRect)
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('pointerup', onPointerUp)
  window.removeEventListener('pointercancel', onPointerUp)
})

watch(() => route.params.id, async () => {
  isVisualSearchActive.value = false
  visualSearchResults.value = []
  await Refresh();

  if (hasScrolledPastImage.value) {
    window.scrollTo({ top: 0, behavior: 'instant' });
  }
  hasScrolledPastImage.value = false;
})

async function Refresh() {

  activeTab.value = 'original'

  comments.value = []
  showComments.value = false
  loadError.value = null
  recError.value = null

  page = 1
  isLoading.value = true
  try {
    const imageId = route.params.id
    currentPin.value = await GetFromApi(`image/${imageId}`)

    // Fetch recommendations separately so image still shows on rec failure
    await RefreshRecommendations()

    try {
      rank.value = await GetFromApi('predict/' + imageId)
    } catch (rankErr) {
      rank.value = { unrated: true }
      console.error('Error loading rank:', rankErr)
    }
  } catch (err) {
    loadError.value = err?.message || 'Something went wrong loading this image.'
    console.error('Error loading image:', err)
  } finally {
    isLoading.value = false
  }

  if (currentPin.value && !currentPin.value.Prompt) {
    promptGenerating.value = true
    const imageId = route.params.id
    await PostToApi("generate_prompt_for/" + imageId)
    promptGenerating.value = false
    Refresh()
  }
}

async function retryRecommendations() {
  await RefreshRecommendations()
}

async function RefreshRecommendations() {
  recError.value = null
  isLoading.value = true
  try {
    page = 1
    const imageId = route.params.id
    const fetchedRec = await GetFromApi(`similar-images/${imageId}?per_page=20&page=${page}&mode=${similarityMode.value}`)
    const initialUnique = filterUniquePins(currentPin.value ? [currentPin.value] : [], dedupePins(fetchedRec))
    recommendations.value = initialUnique
  } catch (err) {
    recError.value = 'Could not load recommendations.'
    console.error('Error retrying recommendations:', err)
  } finally {
    isLoading.value = false
  }
}

// Add this function to the existing script section
function getLevelColor(level) {
  const colors = {
    general: '#4ade80', // green
    sensitive: '#facc15', // yellow
    questionable: '#fb923c', // orange
    explicit: '#ef4444' // red
  };
  return colors[level] || '#9ca3af'; // default gray
}

async function saveToBoard(boardId) {
  showBoardDropdown.value = false
  await PostToApi('board/' + boardId + '/pin?image_id=' + currentPin.value.Id);
  Refresh()
}
async function removeFromBoard(boardId) {
  showBoardDropdown.value = false
  await PostToApi('board/' + boardId + '/unpin?image_id=' + currentPin.value.Id);
  Refresh()
}

function remixImage() {
  webState.remixImage = { ...currentPin.value };
  console.log("Remixing image", { ...currentPin.value });
  webState.sidebarWidth = 500;
}

// Function to handle star rating
async function rateImage(rating) {
  try {
    await PostToApi(`rate/${currentPin.value.Id}?rating=${rating}`)
    currentPin.value.Rating = rating
  } catch (error) {
    console.error('Error rating image:', error)
  }
}

function showFullscreen() {
  const images = [
    ImageSrc(currentPin.value.Path)
  ];
  viewerApi({
    images: images,
    options: { "inline": true, "button": true, "navbar": false, "title": false, "toolbar": false, "tooltip": false, "movable": true, "zoomable": true, "rotatable": true, "scalable": true, "transition": true, "fullscreen": true, "keyboard": true, }
  });
}

function uploadToCivitai() {
  if (!currentPin.value) return;
  const path = currentPin.value.AbsolutePath || currentPin.value.Path;
  const url = `https://civitai.red/posts/create?path=${encodeURIComponent(path)}`;
  window.open(url, '_blank');
}

</script>

<style scoped>
.quality-tag {
  color: #888888;
  opacity: 0.7;
}

:deep(.quality-tag) {
  color: #888888;
  opacity: 0.7;
}

.skeleton {
  background: linear-gradient(90deg, var(--color-slate) 25%, var(--color-panel) 50%, var(--color-slate) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
}

@keyframes skeleton-shimmer {
  0% {
    background-position: 200% 0;
  }

  100% {
    background-position: -200% 0;
  }
}
</style>
