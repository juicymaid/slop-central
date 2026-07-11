<template>
  <div class="w-full px-6 transition-colors duration-200 mb-12">
    <!-- Main Image Error -->
    <div v-if="loadError"
      class="mb-12 bg-[#1A1A24] border border-[#2A2A35] rounded-[2rem] shadow-lg p-10 transition-colors duration-200 text-center">
      <svg class="mx-auto h-16 w-16 text-red-500 mb-6" fill="none" stroke="currentColor" stroke-width="1.5"
        viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round"
          d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
      </svg>
      <h2 class="text-2xl font-serif font-bold italic text-[#FAF8F5] mb-2">Failed to load image</h2>
      <p class="text-[#FAF8F5]/60 font-sans mb-8">{{ loadError }}</p>
      <button @click="Refresh()"
        class="magnetic-button px-6 py-3 bg-[#2A2A35] hover:bg-[#1A1A24] text-[#C9A84C] border border-[#C9A84C]/30 rounded-full font-sans font-semibold transition-colors shadow-[0_0_15px_rgba(201,168,76,0.1)] cursor-pointer">Try
        again</button>
    </div>

    <!-- Skeleton Loader -->
    <div v-else-if="isLoading && !currentPin"
      class="main-image-section mb-12 bg-[#1A1A24] border border-[#2A2A35] rounded-[3rem] shadow-lg p-8 transition-colors duration-200">
      <div class="flex flex-col md:flex-row gap-8">
        <div class="w-full md:w-1/2">
          <div class="skeleton rounded-lg w-full aspect-[3/4]"></div>
          <div class="flex justify-center mt-3">
            <div class="skeleton h-7 w-28 rounded-full"></div>
          </div>
        </div>
        <div class="w-full md:w-1/2 space-y-4">
          <div class="flex justify-between">
            <div class="skeleton h-5 w-16 rounded"></div>
            <div class="skeleton h-10 w-32 rounded-full"></div>
          </div>
          <div class="flex gap-2 border-b border-gray-200 dark:border-gray-700 pb-3">
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

    <!-- Unified Split View -->
    <div v-else-if="currentPin" class="flex flex-row gap-6 w-full mt-6 items-start">

      <!-- LEFT COLUMN: Sticky Pin Card + Pins flowing under it -->
      <div :class="[isDesktop ? 'flex-shrink-0' : 'w-full']" :style="isDesktop ? { flex: `${leftColCount} 0 0%` } : {}"
        class="flex flex-col gap-6">

        <!-- Details Card -->
        <div
          class="bg-[#14141A] border border-[#2A2A35] rounded-[2.5rem] shadow-[0_8px_30px_rgba(0,0,0,0.6)] flex flex-col md:flex-row w-full overflow-hidden">

          <!-- Image Section (Flush Left) -->
          <div
            class="flex-grow relative bg-[#09090C] flex flex-col justify-center select-none overflow-hidden min-h-[300px] md:min-h-[400px]">
            <img @click="showFullscreen" :src="ImageSrc(currentPin.Path)" :alt="currentPin.Title"
              class="w-full h-auto object-contain cursor-zoom-in">
          </div>

          <!-- Details Section (Right half of card) -->
          <div class="w-full md:w-[380px] md:flex-shrink-0 p-8 flex flex-col gap-6 bg-[#14141A]">
            <div class="flex justify-between items-center mb-6 w-full">
              <div class="flex items-center gap-4 text-[#FAF8F5]/60">
                <div class="flex gap-2 items-center" title="Views">
                  <Eye class="w-4 h-4" />
                  <p class="font-mono text-xs uppercase tracking-widest">{{ currentPin.Clicks }}</p>
                </div>
                <div class="flex gap-2 items-center" title="Feed Displays">
                  <Tv class="w-4 h-4" />
                  <p class="font-mono text-xs uppercase tracking-widest">{{ currentPin.Shows || 0 }}</p>
                </div>
              </div>

              <!-- Board Dropdown & Save Button -->
              <div class="flex items-center gap-3 relative">
                <div v-if="currentPin.in_boards.length == 0" class="flex items-center gap-3">
                  <div
                    class="magnetic-button rounded-full px-4.5 py-2 hover:bg-[#2A2A35] cursor-pointer font-sans font-semibold text-[#FAF8F5] flex items-center transition-colors border border-transparent hover:border-[#2A2A35] text-xs"
                    @click="showBoardDropdown = !showBoardDropdown">
                    <span class="relative z-10 flex">
                      {{ currentPin.recommended_boards[selectedBoard]?.name || '' }}
                      <ChevronDown class="w-4 h-4 ml-1 mt-0.5" />
                    </span>
                  </div>
                  <button
                    class="magnetic-button px-5 py-2 bg-[#C9A84C] hover:bg-[#B89A45] text-[#0D0D12] rounded-full font-sans font-semibold transition-colors shadow-lg text-xs cursor-pointer"
                    @click="saveToBoard(currentPin.recommended_boards[selectedBoard].id)">
                    <span class="relative z-10">Save</span>
                  </button>
                </div>
                <div v-else class="flex items-center gap-3">
                  <RouterLink :to="'/board/' + currentPin.in_boards[0].id">
                    <div
                      class="magnetic-button rounded-full px-4 py-2 hover:bg-[#2A2A35] cursor-pointer font-sans font-semibold text-[#C9A84C] flex items-center underline-offset-4 hover:underline transition-colors text-xs">
                      <span class="relative z-10">{{ currentPin.in_boards[0].name || '' }}</span>
                    </div>
                  </RouterLink>
                  <button
                    class="magnetic-button px-5 py-2 bg-[#2A2A35] hover:bg-[#1A1A24] text-[#FAF8F5] border border-[#2A2A35] hover:border-[#C9A84C]/30 rounded-full cursor-pointer transition-colors shadow-sm text-xs"
                    @click="removeFromBoard(currentPin.in_boards[0].id)">
                    <span class="relative z-10">Saved</span>
                  </button>
                </div>
                <div v-if="showBoardDropdown" class="absolute right-0 top-10 mt-2 z-20 w-[180px]">
                  <BoardDropDown :pin="currentPin" @save-to="(id) => saveToBoard(id)" />
                </div>
              </div>
            </div>

            <!-- Scrollable Content Area -->
            <div class="flex flex-col gap-6">

              <!-- Rank & Rating Stars -->
              <div class="flex flex-wrap items-center justify-between gap-4 border-b border-[#2A2A35]/35 pb-4">
                <RouterLink :to="'/rate?id=' + currentPin.Id">
                  <span :class="[
                    'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold shadow-sm',
                    rank.unrated
                      ? 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 ring-1 ring-gray-300 dark:ring-gray-600 border border-dotted border-gray-400 dark:border-gray-500'
                      : 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400 ring-1 ring-blue-300 dark:ring-blue-600'
                  ]">
                    <img :src="rankBadgeSrc(rank.tier)" :alt="(rank.label || 'Unranked') + ' badge'"
                      class="h-6 w-6 object-contain" />
                    <span>{{ rank.label || 'Unranked' }}</span>
                  </span>
                </RouterLink>

                <div
                  class="flex items-center gap-1.5 bg-[#2A2A35]/30 px-3 py-1.5 rounded-full border border-[#2A2A35]/50">
                  <Star v-for="star in 5" :key="star"
                    class="w-4 h-4 text-white cursor-pointer transition-colors duration-150" :class="{
                      'fill-yellow-400 text-yellow-400': star <= (currentPin.Rating || 0),
                      'hover:fill-yellow-200 hover:text-yellow-200': star <= hoverRating
                    }" @click.prevent.stop="rateImage(star)" @mouseenter="hoverRating = star"
                    @mouseleave="hoverRating = 0" />
                  <p v-if="currentPin.Rating > 0" class="text-white ml-1 font-medium text-xs">{{
                    currentPin.Rating.toFixed(1) }}</p>
                </div>
              </div>

              <!-- Prompt Tabs -->
              <div>
                <div class="flex border-b border-[#2A2A35] mb-4">
                  <button v-if="!currentPin.GeneratedPrompt && currentPin.Prompt" @click="activeTab = 'original'"
                    :class="[
                      'px-4 py-2 text-xs font-sans font-semibold transition-colors duration-300',
                      activeTab === 'original'
                        ? 'text-[#C9A84C] border-b-2 border-[#C9A84C]'
                        : 'text-[#FAF8F5]/60 hover:text-[#FAF8F5]'
                    ]">
                    Original Prompt
                  </button>
                  <button @click="activeTab = 'generated'" :class="[
                    'px-4 py-2 text-xs font-sans font-semibold transition-colors duration-300',
                    activeTab === 'generated' || currentPin.GeneratedPrompt
                      ? 'text-[#C9A84C] border-b-2 border-[#C9A84C]'
                      : 'text-[#FAF8F5]/60 hover:text-[#FAF8F5]'
                  ]">
                    Generated Prompt
                  </button>
                </div>

                <h1 v-if="activeTab === 'generated' || currentPin.GeneratedPrompt"
                  class="text-sm font-sans font-medium leading-relaxed text-[#FAF8F5]/90 mb-4 select-text"
                  v-html="formatPromptText(displayPromptText)" @click="showTaggerTags = !showTaggerTags"></h1>
                <h1 v-else class="text-sm font-sans font-medium leading-relaxed text-[#FAF8F5]/90 mb-4 select-text"
                  v-html="formatPromptText(displayPromptText)"></h1>
              </div>

              <!-- TaggerTags / NSFW Ratings -->
              <div v-if="activeTab === 'generated' && currentPin.TaggerTags" class="mb-4">
                <div v-if="showTaggerTags" class="space-y-1.5">
                  <div v-for="(value, tag) in Object.entries(currentPin.TaggerTags)
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 15)
                    .reduce((obj, [key, val]) => ({ ...obj, [key]: val }), {})" :key="tag" class="flex items-center">
                    <span class="w-24 text-xs truncate text-[#FAF8F5]/50">{{ tag }}</span>
                    <div class="flex-1 bg-gray-200 dark:bg-gray-700/60 rounded-full h-1.5 overflow-hidden">
                      <div class="h-full rounded-full bg-[#C9A84C]" :style="{ width: `${Math.round(value * 100)}%` }">
                      </div>
                    </div>
                    <span class="ml-2 text-[10px] text-gray-500 dark:text-gray-400 w-12 text-right">
                      {{ Math.round(value * 100) }}%
                    </span>
                  </div>
                  <button v-if="Object.keys(currentPin.TaggerTags).length > 15"
                    class="text-xs text-[#C9A84C] hover:text-[#FAF8F5] mt-1 cursor-pointer"
                    @click.stop="showAllTags = !showAllTags">
                    {{ showAllTags ? 'Show less' : `Show ${Object.keys(currentPin.TaggerTags).length - 15} more tags` }}
                  </button>
                  <div v-if="showAllTags" class="space-y-1.5 mt-1">
                    <div v-for="(value, tag) in Object.entries(currentPin.TaggerTags)
                      .sort(([, a], [, b]) => b - a)
                      .slice(15)
                      .reduce((obj, [key, val]) => ({ ...obj, [key]: val }), {})" :key="tag" class="flex items-center">
                      <span class="w-24 text-xs truncate text-[#FAF8F5]/50">{{ tag }}</span>
                      <div class="flex-1 bg-gray-200 dark:bg-gray-700/60 rounded-full h-1.5 overflow-hidden">
                        <div class="h-full rounded-full bg-[#C9A84C]" :style="{ width: `${Math.round(value * 100)}%` }">
                        </div>
                      </div>
                      <span class="ml-2 text-[10px] text-gray-500 dark:text-gray-400 w-12 text-right">
                        {{ Math.round(value * 100) }}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Loras Section -->
              <div v-if="displayLoras.length">
                <div class="flex items-center justify-between mb-2">
                  <p class="text-[#FAF8F5]/40 font-mono text-[10px] uppercase tracking-widest">Loras</p>
                  <button @click="copyLoras"
                    class="text-[9px] px-2 py-0.5 bg-[#2A2A35]/60 hover:bg-[#2A2A35] border border-[#2A2A35] text-[#FAF8F5]/70 hover:text-[#FAF8F5] rounded-full transition-all cursor-pointer">
                    {{ lorasCopied ? 'Copied' : 'Copy' }}
                  </button>
                </div>
                <div class="flex flex-wrap gap-1.5">
                  <RouterLink v-for="(lora, index) in displayLoras" :key="`${lora.name}-${lora.weight}-${index}`"
                    :to="{ path: `/models/lora:${lora.name}` }"
                    class="magnetic-button text-[10px] px-2.5 py-1 bg-[#2A2A35]/50 hover:bg-[#2A2A35] border border-[#2A2A35] text-[#FAF8F5]/80 hover:text-[#FAF8F5] rounded-full flex items-center transition-all">
                    <span class="relative z-10">{{ lora.name }}</span>
                    <span v-if="lora.weight" class="relative z-10 ml-1.5 text-[#C9A84C]">{{ lora.weight }}</span>
                  </RouterLink>
                </div>
              </div>

              <!-- Action Buttons (Copy prompt, Remix, Edit, Open Location) -->
              <div
                v-if="(activeTab == 'original' && currentPin.Prompt) || (activeTab == 'generated' && currentPin.taggerPrompt)"
                class="flex flex-wrap gap-2 pt-2 border-t border-[#2A2A35]/30">
                <button @click="copyPrompt(false)"
                  class="magnetic-button text-[11px] px-4 py-2 bg-[#2A2A35]/50 hover:bg-[#2A2A35] border border-[#2A2A35] text-[#FAF8F5]/80 hover:text-[#FAF8F5] rounded-full flex items-center transition-all cursor-pointer">
                  <span class="relative z-10 flex">
                    <span>Copy prompt</span>
                    <span v-if="copied" class="ml-2 text-green-400">✓</span>
                  </span>
                </button>
                <button @click="remixImage"
                  class="magnetic-button text-[11px] px-4 py-2 bg-[#C9A84C]/10 hover:bg-[#C9A84C]/20 border border-[#C9A84C]/30 text-[#C9A84C] hover:text-[#C9A84C] rounded-full flex items-center transition-all cursor-pointer shadow-[0_0_10px_rgba(201,168,76,0.1)]">
                  <span class="relative z-10 flex">
                    <svg class="w-3 h-3 mr-1.5 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                      xmlns="http://www.w3.org/2000/svg">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15">
                      </path>
                    </svg>
                    <span>Remix</span>
                  </span>
                </button>

                <RouterLink :to="{ path: '/canvas', query: { image: currentPin.Id } }"
                  class="magnetic-button text-[11px] px-4 py-2 bg-[#2A2A35]/50 hover:bg-[#2A2A35] border border-[#2A2A35] text-[#FAF8F5]/80 hover:text-[#FAF8F5] rounded-full flex items-center transition-all cursor-pointer">
                  <span class="relative z-10">Edit in Canvas</span>
                </RouterLink>

                <button @click="PostToApi(`open-image-location/${currentPin.Id}`)"
                  class="magnetic-button text-[11px] px-4 py-2 bg-[#2A2A35]/50 hover:bg-[#2A2A35] border border-[#2A2A35] text-[#FAF8F5]/80 hover:text-[#FAF8F5] rounded-full flex items-center transition-all cursor-pointer">
                  <span class="relative z-10">Open Location</span>
                </button>
              </div>

              <!-- Model & Actions -->
              <div class="flex items-center gap-6 border-t border-[#2A2A35]/30 pt-4">
                <RouterLink :to="'/models/' + currentPin.ModelHash">
                  <div class="group">
                    <p class="text-[#FAF8F5]/40 font-mono text-[9px] uppercase tracking-widest mb-1">Model</p>
                    <p
                      class="text-xs text-[#FAF8F5] font-sans font-semibold group-hover:text-[#C9A84C] transition-colors">
                      {{ currentPin.Model ?? currentPin.ModelHash }}
                    </p>
                  </div>
                </RouterLink>

                <RouterLink :to="'/chat/' + currentPin.Id">
                  <div class="group">
                    <p class="text-[#FAF8F5]/40 font-mono text-[9px] uppercase tracking-widest mb-1">Actions</p>
                    <p
                      class="text-xs text-[#FAF8F5] font-sans font-semibold group-hover:text-[#C9A84C] transition-colors">
                      Chat with character
                    </p>
                  </div>
                </RouterLink>
              </div>

              <!-- Negative Prompt -->
              <div v-if="currentPin.NegativePrompt" class="border-t border-[#2A2A35]/30 pt-4">
                <p class="text-[#FAF8F5]/40 font-mono text-[9px] uppercase tracking-widest mb-1.5">Negative Prompt</p>
                <p class="text-xs text-[#FAF8F5]/70 font-sans leading-relaxed select-text">{{ currentPin.NegativePrompt
                }}</p>
              </div>

              <!-- Content Rating -->
              <div v-if="currentPin.nsfw_levels" class="border-t border-[#2A2A35]/30 pt-4">
                <div class="flex justify-between items-center cursor-pointer"
                  @click="showContentRating = !showContentRating">
                  <div class="text-xs font-mono uppercase tracking-widest text-[#FAF8F5]/40">
                    Content Rating
                    <span v-if="!showContentRating && currentPin.nsfw_levels"
                      class="ml-2 px-2 py-0.5 text-[9px] font-sans rounded-full"
                      :style="{ backgroundColor: getLevelColor(getHighestNsfwLevel()), color: '#fff' }">
                      {{ getHighestNsfwLevel().charAt(0).toUpperCase() + getHighestNsfwLevel().slice(1) }}
                    </span>
                  </div>
                  <svg class="w-4 h-4 transform transition-transform duration-200"
                    :class="{ 'rotate-180': showContentRating }" fill="none" stroke="currentColor" stroke-width="2"
                    viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"></path>
                  </svg>
                </div>

                <div v-if="showContentRating" class="space-y-1.5 mt-3">
                  <div v-for="(value, level) in Object.entries(currentPin.nsfw_levels)
                    .sort(([, a], [, b]) => b - a)
                    .reduce((obj, [key, val]) => ({ ...obj, [key]: val }), {})" :key="level" class="flex items-center">
                    <span class="w-24 text-xs capitalize text-[#FAF8F5]/50">{{ level }}</span>
                    <div class="flex-1 bg-gray-200 dark:bg-gray-700/60 rounded-full h-1.5 overflow-hidden">
                      <div class="h-full rounded-full" :style="{
                        width: `${Math.round(value * 100)}%`,
                        backgroundColor: getLevelColor(level)
                      }"></div>
                    </div>
                    <span class="ml-2 text-[10px] text-gray-500 dark:text-gray-400 w-12 text-right">
                      {{ Math.round(value * 100) }}%
                    </span>
                  </div>
                </div>
              </div>

              <!-- Variations & Identical Images -->
              <div v-if="currentPin.variations.length > 0" class="border-t border-[#2A2A35]/30 pt-4">
                <h2 class="text-sm font-bold uppercase tracking-wider text-[#FAF8F5]/80 mb-3">Variations</h2>
                <div class="grid grid-cols-3 gap-2">
                  <Image v-for="pin in currentPin.variations" :key="pin.Id" :pin="pin" />
                </div>
              </div>
              <div v-if="currentPin.identical_images.length > 0" class="border-t border-[#2A2A35]/30 pt-4">
                <h2 class="text-sm font-bold uppercase tracking-wider text-[#FAF8F5]/80 mb-3">Identical Images</h2>
                <div class="grid grid-cols-3 gap-2">
                  <Image v-for="pin in currentPin.identical_images" :key="pin.Id" :pin="pin" />
                </div>
              </div>

              <!-- Comments Section (Pinterest style) -->
              <div class="border-t border-[#2A2A35]/30 pt-4">
                <div class="flex justify-between items-center cursor-pointer"
                  @click="showComments = !showComments; GetComments()">
                  <div class="flex items-center">
                    <h2 class="text-sm font-bold uppercase tracking-wider text-[#FAF8F5]/80">Comments</h2>
                    <button v-if="showComments"
                      class="ml-2 p-1 rounded-full hover:bg-[#2A2A35] transition-colors cursor-pointer"
                      @click.stop="GetComments(true)">
                      <svg class="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15">
                        </path>
                      </svg>
                    </button>
                  </div>
                  <button
                    class="flex items-center text-gray-400 hover:text-white transition-colors focus:outline-none rounded">
                    <svg class="w-5 h-5 transform transition-transform duration-200"
                      :class="{ 'rotate-180': showComments }" fill="none" stroke="currentColor" stroke-width="2"
                      viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"></path>
                    </svg>
                  </button>
                </div>

                <div v-if="showComments" class="mt-4">
                  <div v-if="fetchingComments" class="space-y-4 p-2">
                    <div v-for="n in 3" :key="n" class="flex items-start space-x-3">
                      <div class="skeleton w-10 h-10 rounded-full flex-shrink-0"></div>
                      <div class="flex-1 space-y-2">
                        <div class="skeleton h-4 w-24 rounded"></div>
                        <div class="skeleton h-3 w-full rounded"></div>
                      </div>
                    </div>
                  </div>
                  <div v-else-if="commentError" class="p-4 text-center">
                    <p class="text-red-500 dark:text-red-400 text-sm mb-2">{{ commentError }}</p>
                    <button @click="GetComments(true)"
                      class="text-sm px-3 py-1.5 bg-[#2A2A35] text-white rounded-md hover:bg-[#1A1A24] transition-colors cursor-pointer">Retry</button>
                  </div>
                  <div v-else class="space-y-4">
                    <div v-for="(comment, index) in comments" :key="comment.Id" class="flex items-start space-x-3">
                      <RouterLink :to="'/user/' + (comment.character_id || comment.username)">
                        <img :src="comment.avatar || `${apiUrl}/random-image-file?user=${comment.username}`"
                          :alt="`${comment.username}'s avatar`" class="w-8 h-8 rounded-full object-cover" />
                      </RouterLink>
                      <div class="w-full">
                        <RouterLink :to="'/user/' + (comment.character_id || comment.username)"
                          class="hover:text-[#C9A84C] transition-colors">
                          <p class="text-[#FAF8F5] font-semibold text-xs">{{ comment.username }}</p>
                        </RouterLink>
                        <p class="text-[#FAF8F5]/80 text-xs mt-0.5 select-text">{{ comment.content }}</p>
                        <!-- Replies -->
                        <div v-if="comment.replies && comment.replies.length > 0"
                          class="mt-2 pl-3 border-l border-[#2A2A35] space-y-2.5">
                          <div v-for="reply in comment.replies" :key="reply.Id" class="flex items-start space-x-2">
                            <img :src="reply.avatar || `${apiUrl}/random-image-file?user=${reply.username}`"
                              :alt="`${reply.username}'s avatar`" class="w-7 h-7 rounded-full object-cover" />
                            <div>
                              <p class="text-[#FAF8F5] font-semibold text-[11px]">{{ reply.username }}</p>
                              <p class="text-[#FAF8F5]/80 text-[11px] mt-0.5 select-text">{{ reply.content }}</p>
                            </div>
                          </div>
                        </div>
                        <!-- Reply input -->
                        <div class="flex items-center gap-2 mt-2">
                          <img :src="`${apiUrl}/files/automatic/avatar.png`" alt="Your avatar"
                            class="w-6 h-6 rounded-full object-cover border border-[#2A2A35]" />
                          <input type="text" v-model="comment.reply" placeholder="Reply..."
                            class="w-full p-1.5 bg-[#0D0D12] border border-[#2A2A35] rounded-xl focus:outline-none focus:border-[#C9A84C]/50 text-xs text-[#FAF8F5] placeholder-[#FAF8F5]/30 transition-colors"
                            @keyup.enter="postReply(comment.reply, index)" />
                        </div>
                      </div>
                    </div>

                    <!-- Add Comment input -->
                    <div class="mt-4 border-t border-[#2A2A35]/35 pt-4">
                      <div class="flex items-start space-x-3">
                        <img :src="`${apiUrl}/files/automatic/avatar.png`" alt="Your avatar"
                          class="w-8 h-8 rounded-full object-cover border border-[#2A2A35]" />
                        <div class="w-full">
                          <textarea v-model="newComment" placeholder="Add a comment..."
                            class="w-full p-2.5 bg-[#0D0D12] border border-[#2A2A35] rounded-2xl focus:outline-none focus:border-[#C9A84C]/50 text-xs text-[#FAF8F5] placeholder-[#FAF8F5]/30 transition-colors"
                            rows="2"></textarea>
                          <div class="flex justify-end mt-1.5">
                            <button @click="postComment"
                              class="px-4 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded-full transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                              :disabled="!newComment.trim()">
                              Post
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Metadata Panel -->
              <div class="border-t border-[#2A2A35]/30 pt-4">
                <button @click="() => showMetadata = !showMetadata"
                  class="text-xs text-gray-400 hover:text-white transition-colors cursor-pointer">
                  {{ showMetadata ? 'Hide technical metadata' : 'Show technical metadata' }} ↓
                </button>
                <div v-if="showMetadata" class="mt-4">
                  <div
                    class="bg-[#0D0D12] border border-[#2A2A35]/60 p-4 rounded-2xl transition-colors font-mono text-[10px] text-[#FAF8F5]/70 flex flex-col gap-1.5">
                    <div class="flex justify-between border-b border-[#2A2A35]/15 pb-1">
                      <span class="text-gray-500">Seed:</span>
                      <span>{{ currentPin.Seed }}</span>
                    </div>
                    <div class="flex justify-between border-b border-[#2A2A35]/15 pb-1">
                      <span class="text-gray-500">Dimensions:</span>
                      <span>{{ currentPin.Width }} × {{ currentPin.Height }}</span>
                    </div>
                    <div class="flex justify-between border-b border-[#2A2A35]/15 pb-1">
                      <span class="text-gray-500">Steps:</span>
                      <span>{{ currentPin.Steps }}</span>
                    </div>
                    <div class="flex justify-between border-b border-[#2A2A35]/15 pb-1">
                      <span class="text-gray-500">Sampler:</span>
                      <span>{{ currentPin.Sampler }}</span>
                    </div>
                    <div class="flex justify-between border-b border-[#2A2A35]/15 pb-1">
                      <span class="text-gray-500">CFG Scale:</span>
                      <span>{{ currentPin.CFGScale }}</span>
                    </div>
                    <div class="flex justify-between border-b border-[#2A2A35]/15 pb-1">
                      <span class="text-gray-500">pHash:</span>
                      <span>{{ currentPin.pHash }}</span>
                    </div>
                    <div class="flex justify-between border-b border-[#2A2A35]/15 pb-1">
                      <span class="text-gray-500">Filename:</span>
                      <span class="truncate max-w-[180px]" :title="currentPin.FileName">{{ currentPin.FileName }}</span>
                    </div>
                    <div class="flex justify-between border-b border-[#2A2A35]/15 pb-1">
                      <span class="text-gray-500">Created:</span>
                      <span>{{ formatDate(currentPin.CreatedDate) }}</span>
                    </div>
                    <div class="flex flex-col gap-1 mt-1">
                      <span class="text-gray-500">Description:</span>
                      <div
                        class="bg-[#14141A] p-2 rounded-xl text-[10px] leading-relaxed break-words whitespace-pre-wrap select-text border border-[#2A2A35]/40 max-h-[100px] overflow-y-auto">
                        {{ currentPin.description || 'N/A' }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

            </div>

          </div>
        </div>

        <!-- Section Header for under-card recommendations on mobile/desktop if recommendations exist -->
        <div v-if="recommendations.length > 0 && !isDesktop" class="mt-6">
          <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">More like this</h2>
        </div>

        <!-- Pins flowing under the card (Grouped into left-side columns) -->
        <div v-if="recommendations.length > 0" class="w-full flex gap-6 items-start">
          <div class="flex-1 min-w-0 flex flex-col gap-6" v-for="colIdx in leftColCount" :key="colIdx">
            <Image v-for="pin in getLeftPins(colIdx - 1)" :key="pin.Id" :pin="pin" />
          </div>
        </div>
      </div>

      <!-- RIGHT COLUMN: Related Pins Masonry (Spans the remaining width, pins start at the top) -->
      <div v-if="isDesktop" :style="{ flex: `${rightColCount} 0 0%` }" class="flex flex-col gap-6">

        <!-- Similarity selector at the top-right -->
        <div class="flex justify-between items-center mb-2 w-full">
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">More like this</h2>
          <select v-model="similarityMode" @change="RefreshRecommendations"
            class="bg-[#1A1A24] border border-[#2A2A35] text-[#FAF8F5] rounded-lg px-3 py-1.5 focus:outline-none focus:border-[#C9A84C] text-sm cursor-pointer">
            <option value="full">Full Similarity</option>
            <option value="prompt">Prompt Only</option>
            <option value="hash">Visual Only</option>
            <option value="embedding">Neural (SigLIP)</option>
          </select>
        </div>

        <!-- Rec Error -->
        <div v-if="recError" class="bg-white dark:bg-gray-800 rounded-xl shadow p-8 text-center">
          <svg class="mx-auto h-10 w-10 text-red-400 dark:text-red-500 mb-3" fill="none" stroke="currentColor"
            stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          <p class="text-gray-500 dark:text-gray-400 mb-4">{{ recError }}</p>
          <button @click="retryRecommendations()"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors cursor-pointer">Retry</button>
        </div>

        <!-- Rec Skeleton -->
        <div v-else-if="isLoading && recommendations.length === 0" class="flex gap-6 w-full items-start">
          <div class="flex-1 min-w-0 flex flex-col gap-6" v-for="colIdx in rightColCount" :key="colIdx">
            <div v-for="n in 3" :key="n" class="skeleton rounded-lg w-full"
              :style="{ height: (180 + (n % 3) * 80) + 'px' }"></div>
          </div>
        </div>

        <!-- Columns 2 to N -->
        <div v-else class="flex gap-6 w-full items-start">
          <div class="flex-1 min-w-0 flex flex-col gap-6" v-for="colIdx in rightColCount" :key="colIdx">
            <Image v-for="pin in getRightPins(colIdx - 1)" :key="pin.Id" :pin="pin" />
          </div>
        </div>

      </div>
    </div>
  </div>

  <!-- Add color settings modal -->
  <div v-if="showTagColorSettings" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full shadow-xl">
      <h3 class="text-xl font-bold mb-4 text-gray-900 dark:text-white">Tag Color Settings</h3>
      <div class="space-y-4">
        <div v-for="(color, type) in tagColors" :key="type" class="flex items-center justify-between">
          <span class="text-gray-700 dark:text-gray-300">{{ tagTypeToName(type) }}</span>
          <input type="color" v-model="tagColors[type]" class="w-10 h-10 rounded cursor-pointer" />
        </div>
      </div>
      <div class="flex justify-end mt-6 space-x-3">
        <button @click="resetTagColors"
          class="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white rounded-lg transition-colors">
          Reset to Default
        </button>
        <button @click="saveTagColors"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
          Save
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount, inject, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Star, ChevronDown, Eye, Tv } from 'lucide-vue-next'
import BoardDropDown from '@/components/BoardDropDown.vue'
import ImageMasonry from '@/components/ImageMasonry.vue'

const selectedBoard = ref(0)
const copied = ref(false)
const lorasCopied = ref(false)
const isDarkMode = inject('isDarkMode', ref(false))
const hoverRating = ref(0)
const showComments = ref(false)

const windowWidth = ref(window.innerWidth)
const updateWindowWidth = () => {
  windowWidth.value = window.innerWidth
}
const isDesktop = computed(() => windowWidth.value >= 1280) // xl breakpoint
const columnCount = computed(() => {
  if (windowWidth.value < 640) return 2
  if (windowWidth.value < 1024) return 3
  if (windowWidth.value < 1280) return 4
  if (windowWidth.value < 1536) return 5
  return 6
})
const leftColCount = computed(() => {
  if (!isDesktop.value) return columnCount.value
  return columnCount.value >= 5 ? 3 : 2
})
const rightColCount = computed(() => {
  if (!isDesktop.value) return 0
  return columnCount.value - leftColCount.value
})
const getLeftPins = (colIdx) => {
  return recommendations.value.filter((p, pi) => {
    const c = pi % columnCount.value
    return c === colIdx
  })
}
const getRightPins = (colIdx) => {
  return recommendations.value.filter((p, pi) => {
    const c = pi % columnCount.value
    return c === (colIdx + leftColCount.value)
  })
}
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

    const normalizedTag = tag.toLowerCase().replace(/[\s_]+/g, '_');
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

let cardObserver = null
onMounted(async () => {
  Refresh()
  window.addEventListener('scroll', handleScroll)
  window.addEventListener('resize', updateWindowWidth)
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
  window.removeEventListener('resize', updateWindowWidth)

})

watch(() => route.params.id, async () => {
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

import { api as viewerApi } from 'v-viewer'
import { GetFromApi, ImageSrc } from '@/api'
import Image from '@/components/Image.vue'

function showFullscreen() {
  const images = [
    ImageSrc(currentPin.value.Path)
  ];
  viewerApi({
    images: images,
    options: { "inline": true, "button": true, "navbar": false, "title": false, "toolbar": false, "tooltip": false, "movable": true, "zoomable": true, "rotatable": true, "scalable": true, "transition": true, "fullscreen": true, "keyboard": true, }
  });
}

</script>

<style scoped>
.max-w-7xl {
  max-width: 80rem;
}

.quality-tag {
  color: #888888;
  opacity: 0.7;
}

:deep(.quality-tag) {
  color: #888888;
  opacity: 0.7;
}

:deep(.dark .quality-tag) {
  color: #aaaaaa;
  opacity: 0.7;
}

/* Add button to open tag color settings */
.tag-settings-button {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
  padding: 5px;
  border-radius: 4px;
  background-color: rgba(0, 0, 0, 0.1);
  cursor: pointer;
}

.dark .tag-settings-button {
  background-color: rgba(255, 255, 255, 0.1);
}

.skeleton {
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
}

:global(.dark) .skeleton {
  background: linear-gradient(90deg, #374151 25%, #4b5563 50%, #374151 75%);
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
