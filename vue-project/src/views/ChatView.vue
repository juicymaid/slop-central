<template>
    <div class="h-[calc(100vh-5.25rem)] max-w-[1600px] mx-auto flex flex-col relative overflow-hidden bg-[#0D0D12] text-[#FAF8F5] font-sans rounded-3xl border border-[#2A2A35] shadow-2xl">
        <!-- Ambient decorative background glow -->
        <div class="absolute -top-40 -left-40 w-96 h-96 bg-[#C9A84C]/10 rounded-full blur-3xl pointer-events-none"></div>
        <div class="absolute -bottom-40 -right-40 w-96 h-96 bg-[#C9A84C]/5 rounded-full blur-3xl pointer-events-none"></div>

        <div class="flex flex-1 min-h-0 relative z-10">
            <!-- ── Left Sidebar (Conversations & Characters) ────────────────────── -->
            <aside :class="[
                'w-80 md:w-88 flex-shrink-0 bg-[#14141A]/90 backdrop-blur-xl border-r border-[#2A2A35] flex flex-col transition-all duration-300 z-30',
                mobileSidebarOpen ? 'fixed inset-y-0 left-0 w-80 z-50 shadow-2xl md:relative md:shadow-none' : 'hidden md:flex'
            ]">
                <!-- Sidebar Header -->
                <div class="p-5 border-b border-[#2A2A35]/80 flex items-center justify-between">
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="w-2 h-2 rounded-full bg-[#C9A84C] animate-pulse"></span>
                            <h2 class="font-serif italic font-bold text-xl text-[#FAF8F5] tracking-tight">Chronicles</h2>
                        </div>
                        <p class="text-[10px] font-mono text-[#FAF8F5]/40 uppercase tracking-widest mt-0.5">Personas & Dialogues</p>
                    </div>

                    <div class="flex items-center gap-1.5">
                        <button @click="refreshAll" :disabled="isRefreshing"
                            class="p-2 rounded-xl text-[#FAF8F5]/50 hover:text-[#C9A84C] hover:bg-[#1A1A24] border border-transparent hover:border-[#2A2A35] transition-all"
                            title="Refresh chats & personas">
                            <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': isRefreshing }" />
                        </button>
                        <router-link to="/posts"
                            class="p-2 rounded-xl text-[#FAF8F5]/50 hover:text-[#C9A84C] hover:bg-[#1A1A24] border border-transparent hover:border-[#2A2A35] transition-all"
                            title="Explore more characters">
                            <Compass class="w-4 h-4" />
                        </router-link>
                        <button v-if="mobileSidebarOpen" @click="mobileSidebarOpen = false"
                            class="md:hidden p-2 rounded-xl text-[#FAF8F5]/50 hover:text-white hover:bg-[#1A1A24]">
                            <X class="w-4 h-4" />
                        </button>
                    </div>
                </div>

                <!-- Search Filter & Navigation Tabs -->
                <div class="px-4 pt-3 pb-2 space-y-2.5">
                    <!-- Search Input -->
                    <div class="relative">
                        <input v-model="searchQuery" type="text" placeholder="Search personas..."
                            class="w-full bg-[#0D0D12] text-xs font-sans text-[#FAF8F5] placeholder-[#FAF8F5]/30 border border-[#2A2A35] rounded-xl pl-9 pr-3 py-2 focus:outline-none focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] transition-all" />
                        <Search class="w-3.5 h-3.5 text-[#FAF8F5]/30 absolute left-3 top-2.5" />
                        <button v-if="searchQuery" @click="searchQuery = ''" class="absolute right-2.5 top-2.5 text-[#FAF8F5]/40 hover:text-white">
                            <X class="w-3.5 h-3.5" />
                        </button>
                    </div>

                    <!-- Category Filter Tabs -->
                    <div class="flex p-1 bg-[#0D0D12] rounded-xl border border-[#2A2A35]/60">
                        <button v-for="tab in ['all', 'characters', 'recent']" :key="tab"
                            @click="sidebarTab = tab"
                            :class="[
                                'flex-1 py-1.5 text-[11px] font-mono capitalize rounded-lg transition-all',
                                sidebarTab === tab
                                    ? 'bg-[#C9A84C] text-[#0D0D12] font-bold shadow-sm'
                                    : 'text-[#FAF8F5]/50 hover:text-[#FAF8F5]'
                            ]">
                            {{ tab }}
                        </button>
                    </div>
                </div>

                <!-- Sidebar Scrollable List -->
                <div class="flex-1 min-h-0 overflow-y-auto px-3 py-2 space-y-4 custom-scrollbar">
                    <!-- Characters Section -->
                    <div v-if="(sidebarTab === 'all' || sidebarTab === 'characters') && filteredCharacters.length">
                        <div class="flex items-center justify-between px-2 mb-2">
                            <span class="text-[10px] font-mono uppercase tracking-widest text-[#C9A84C] font-semibold">Active Personas</span>
                            <span class="text-[10px] font-mono text-[#FAF8F5]/40">{{ filteredCharacters.length }}</span>
                        </div>

                        <div class="space-y-1">
                            <router-link v-for="char in filteredCharacters" :key="char.id"
                                :to="{ name: 'chat', params: { id: char.id } }"
                                @click="mobileSidebarOpen = false"
                                :class="[
                                    'flex items-center gap-3 p-2.5 rounded-2xl border transition-all duration-200 group',
                                    route.params.id === char.id
                                        ? 'bg-[#1A1A24] border-[#C9A84C]/50 shadow-md ring-1 ring-[#C9A84C]/20'
                                        : 'bg-[#14141A]/50 border-transparent hover:border-[#2A2A35] hover:bg-[#1A1A24]/60'
                                ]">
                                <div class="relative shrink-0">
                                    <img :src="char.avatar || `${apiUrl}/random-image-file?user=${char.id}`"
                                        class="w-11 h-11 rounded-full object-cover border border-[#2A2A35] group-hover:border-[#C9A84C]/50 transition-all shadow-sm" />
                                    <span class="absolute bottom-0 right-0 w-3 h-3 rounded-full bg-emerald-500 border-2 border-[#14141A]"></span>
                                </div>

                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center justify-between">
                                        <h4 :class="[
                                            'font-sans font-semibold text-xs truncate',
                                            route.params.id === char.id ? 'text-[#C9A84C]' : 'text-[#FAF8F5] group-hover:text-[#C9A84C] transition-colors'
                                        ]">
                                            {{ char.name }}
                                        </h4>
                                        <span class="text-[9px] font-mono text-[#FAF8F5]/30">@{{ char.id }}</span>
                                    </div>
                                    <p class="text-[11px] text-[#FAF8F5]/50 truncate mt-0.5 font-light">
                                        {{ char.description || 'Start a roleplay chronicle…' }}
                                    </p>
                                </div>
                            </router-link>
                        </div>
                    </div>

                    <!-- Recent Dialogues Section -->
                    <div v-if="(sidebarTab === 'all' || sidebarTab === 'recent') && filteredRecentChats.length">
                        <div class="flex items-center justify-between px-2 mb-2">
                            <span class="text-[10px] font-mono uppercase tracking-widest text-[#FAF8F5]/40 font-semibold">Recent Dialogues</span>
                            <span class="text-[10px] font-mono text-[#FAF8F5]/40">{{ filteredRecentChats.length }}</span>
                        </div>

                        <div class="space-y-1">
                            <router-link v-for="c in filteredRecentChats" :key="c.chat_id"
                                :to="{ name: 'chat', params: { id: c.chat_id } }"
                                @click="mobileSidebarOpen = false"
                                :class="[
                                    'flex items-center gap-3 p-2.5 rounded-2xl border transition-all duration-200 group',
                                    route.params.id === c.chat_id
                                        ? 'bg-[#1A1A24] border-[#C9A84C]/50 shadow-md ring-1 ring-[#C9A84C]/20'
                                        : 'bg-[#14141A]/50 border-transparent hover:border-[#2A2A35] hover:bg-[#1A1A24]/60'
                                ]">
                                <div class="relative shrink-0">
                                    <img :src="getChatAvatar(c)"
                                        class="w-11 h-11 rounded-full object-cover border border-[#2A2A35] group-hover:border-[#C9A84C]/50 transition-all shadow-sm" />
                                </div>
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center justify-between">
                                        <h4 :class="[
                                            'font-sans font-semibold text-xs truncate',
                                            route.params.id === c.chat_id ? 'text-[#C9A84C]' : 'text-[#FAF8F5] group-hover:text-[#C9A84C] transition-colors'
                                        ]">
                                            {{ getChatTitle(c) }}
                                        </h4>
                                        <span v-if="c.messages?.length" class="text-[9px] font-mono text-[#FAF8F5]/30">
                                            {{ c.messages.length }} msgs
                                        </span>
                                    </div>
                                    <p class="text-[11px] text-[#FAF8F5]/50 truncate mt-0.5 font-light">
                                        {{ getLastMessageText(c) }}
                                    </p>
                                </div>
                            </router-link>
                        </div>
                    </div>

                    <!-- Empty State for Sidebar -->
                    <div v-if="!filteredCharacters.length && !filteredRecentChats.length" class="py-12 text-center">
                        <MessageSquare class="w-8 h-8 text-[#2A2A35] mx-auto mb-2" />
                        <p class="text-xs font-mono text-[#FAF8F5]/40">No conversations match filter</p>
                    </div>
                </div>
            </aside>

            <!-- Backdrop for mobile sidebar -->
            <div v-if="mobileSidebarOpen" @click="mobileSidebarOpen = false"
                class="fixed inset-0 bg-[#0D0D12]/70 backdrop-blur-sm z-40 md:hidden"></div>

            <!-- ── Main Chat Area ────────────────────────────────────────────────── -->
            <main class="flex-1 min-w-0 flex flex-col bg-[#0D0D12] relative overflow-hidden">
                <!-- Chat Topbar -->
                <header class="px-6 py-4 border-b border-[#2A2A35] bg-[#14141A]/70 backdrop-blur-md flex items-center justify-between z-20">
                    <div class="flex items-center gap-3.5 min-w-0">
                        <button @click="mobileSidebarOpen = true"
                            class="md:hidden p-2 -ml-2 rounded-xl text-[#FAF8F5]/70 hover:text-white hover:bg-[#1A1A24]">
                            <MessageSquare class="w-5 h-5" />
                        </button>

                        <template v-if="chatData?.character || currentCharacter">
                            <div class="relative shrink-0 group/avatar">
                                <img :src="activePersonaAvatar"
                                    class="w-11 h-11 rounded-full object-cover border border-[#C9A84C]/40 shadow-md group-hover/avatar:border-[#C9A84C] transition-all" />
                                <span class="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-400 border border-[#14141A]"></span>
                            </div>

                            <div class="min-w-0">
                                <div class="flex items-center gap-2">
                                    <h3 class="font-sans font-bold text-base text-[#FAF8F5] truncate">
                                        {{ activePersonaName }}
                                    </h3>
                                    <span class="px-2 py-0.5 rounded-full bg-[#C9A84C]/15 border border-[#C9A84C]/30 text-[#C9A84C] text-[10px] font-mono">
                                        Persona
                                    </span>
                                </div>
                                <div class="flex items-center gap-2 text-xs font-mono text-[#FAF8F5]/40 truncate">
                                    <span v-if="isTyping" class="text-[#C9A84C] flex items-center gap-1.5 animate-pulse">
                                        <span class="w-1.5 h-1.5 rounded-full bg-[#C9A84C]"></span>
                                        {{ isGeneratingImage ? 'Manifesting image…' : 'Composing reply…' }}
                                    </span>
                                    <span v-else class="flex items-center gap-1 text-emerald-400/80">
                                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                                        Ready to converse
                                    </span>
                                    <span>•</span>
                                    <span class="truncate">{{ activePersonaSubtext }}</span>
                                </div>
                            </div>
                        </template>

                        <div v-else class="flex items-center gap-3">
                            <div class="w-10 h-10 rounded-full bg-[#1A1A24] border border-[#2A2A35] flex items-center justify-center text-[#C9A84C]">
                                <Sparkles class="w-5 h-5" />
                            </div>
                            <div>
                                <h3 class="font-sans font-bold text-sm text-[#FAF8F5]">Slop Central Chronicles</h3>
                                <p class="text-xs font-mono text-[#FAF8F5]/40">Select a persona to begin conversation</p>
                            </div>
                        </div>
                    </div>

                    <!-- Header Actions -->
                    <div class="flex items-center gap-2">
                        <template v-if="route.params.id">
                            <!-- View Profile -->
                            <router-link :to="'/user/' + route.params.id"
                                class="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#1A1A24] hover:bg-[#2A2A35] border border-[#2A2A35] hover:border-[#C9A84C]/40 text-xs font-sans text-[#FAF8F5]/80 hover:text-[#FAF8F5] transition-all">
                                <User class="w-3.5 h-3.5 text-[#C9A84C]" />
                                <span>Profile</span>
                            </router-link>
                            <!-- Clear Chat History -->
                            <button @click="showClearConfirm = true"
                                class="p-2 rounded-xl text-[#FAF8F5]/50 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-all"
                                title="Clear conversation history">
                                <Trash2 class="w-4 h-4" />
                            </button>

                            <!-- Persona Dossier Toggle -->
                            <button @click="infoDrawerOpen = !infoDrawerOpen"
                                :class="[
                                    'p-2 rounded-xl border transition-all',
                                    infoDrawerOpen
                                        ? 'bg-[#C9A84C]/15 border-[#C9A84C]/40 text-[#C9A84C]'
                                        : 'text-[#FAF8F5]/50 hover:text-[#FAF8F5] hover:bg-[#1A1A24] border-transparent hover:border-[#2A2A35]'
                                ]"
                                title="Toggle persona dossier">
                                <Info class="w-4 h-4" />
                            </button>
                        </template>
                    </div>
                </header>

                <!-- ── Chat Messages Container ───────────────────────────────────── -->
                <div ref="messagesContainer" class="flex-1 min-h-0 overflow-y-auto px-4 md:px-8 py-6 space-y-6 custom-scrollbar">
                    <!-- Welcome / Empty State when no chat selected -->
                    <div v-if="!route.params.id" class="h-full flex flex-col items-center justify-center py-16 text-center max-w-lg mx-auto">
                        <div class="w-20 h-20 rounded-3xl bg-gradient-to-br from-[#1A1A24] to-[#14141A] border border-[#2A2A35] flex items-center justify-center shadow-xl mb-6 relative group">
                            <Sparkles class="w-10 h-10 text-[#C9A84C] group-hover:scale-110 transition-transform" />
                            <div class="absolute inset-0 bg-[#C9A84C]/10 rounded-3xl blur-xl opacity-50"></div>
                        </div>

                        <h2 class="font-serif italic text-3xl font-bold text-[#FAF8F5] mb-2 tracking-tight">Enter the Chronicles</h2>
                        <p class="text-sm font-sans text-[#FAF8F5]/60 leading-relaxed mb-8">
                            Converse with vivid AI characters and roleplay companions. Select a persona to embark upon dialogue.
                        </p>
                        <!-- Quick Persona Cards -->
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left">
                            <router-link v-for="char in characters.slice(0, 4)" :key="char.id"
                                :to="{ name: 'chat', params: { id: char.id } }"
                                class="p-3.5 rounded-2xl bg-[#14141A] border border-[#2A2A35] hover:border-[#C9A84C]/50 hover:bg-[#1A1A24] transition-all flex items-center gap-3 group">
                                <img :src="char.avatar || `${apiUrl}/random-image-file?user=${char.id}`"
                                    class="w-10 h-10 rounded-full object-cover border border-[#2A2A35] group-hover:scale-105 transition-transform" />
                                <div class="min-w-0 flex-1">
                                    <h4 class="font-bold text-xs text-[#FAF8F5] group-hover:text-[#C9A84C] transition-colors truncate">{{ char.name }}</h4>
                                    <p class="text-[11px] font-mono text-[#FAF8F5]/40 truncate">@{{ char.id }}</p>
                                </div>
                            </router-link>
                        </div>
                    </div>

                    <!-- Active Chat Message Stream -->
                    <template v-else>
                        <!-- Persona Introduction Header Card -->
                        <div class="p-6 rounded-3xl bg-gradient-to-b from-[#14141A] to-[#14141A]/50 border border-[#2A2A35] text-center max-w-xl mx-auto shadow-lg relative overflow-hidden mb-8">
                            <div class="absolute top-0 right-0 w-32 h-32 bg-[#C9A84C]/10 rounded-full blur-2xl pointer-events-none"></div>
                            
                            <img :src="activePersonaAvatar"
                                class="w-20 h-20 rounded-full object-cover border-2 border-[#C9A84C] mx-auto mb-3 shadow-xl hover:scale-105 transition-transform cursor-pointer"
                                @click="openImage(activePersonaAvatar)" />

                            <h3 class="font-serif italic font-bold text-2xl text-[#FAF8F5] mb-1">{{ activePersonaName }}</h3>
                            <p class="text-xs font-mono text-[#C9A84C] mb-3">@{{ route.params.id }}</p>
                            <p class="text-xs font-sans text-[#FAF8F5]/70 leading-relaxed max-w-md mx-auto line-clamp-3">
                                {{ activePersonaDescription }}
                            </p>

                            <!-- Starting Conversation Prompt Chips -->
                            <div v-if="!chatMessages.length" class="flex flex-wrap gap-2 justify-center mt-5">
                                <button v-for="prompt in starterPrompts" :key="prompt"
                                    @click="sendMessageDirect(prompt)"
                                    class="text-xs font-sans px-3.5 py-1.5 rounded-full bg-[#1A1A24] border border-[#2A2A35] text-[#FAF8F5]/80 hover:text-[#C9A84C] hover:border-[#C9A84C]/40 transition-all hover:scale-102">
                                    "{{ prompt }}"
                                </button>
                            </div>
                        </div>

                        <!-- Messages List -->
                        <div v-for="(msg, idx) in chatMessages" :key="msg.id || idx" class="space-y-4">
                            <!-- Skip system or tool messages if present in raw stream -->
                            <template v-if="msg.role !== 'tool' && msg.role !== 'system'">
                                <!-- ── User Message (Right Aligned) ─────────────── -->
                                <div v-if="msg.isUser || msg.role === 'user'" class="flex justify-end gap-3 group">
                                    <div class="flex flex-col items-end max-w-[80%] md:max-w-[70%]">
                                        <!-- Attached Image if any -->
                                        <div v-if="msg.image" class="mb-2 rounded-2xl overflow-hidden border border-[#C9A84C]/30 shadow-lg cursor-pointer max-w-sm">
                                            <img :src="msg.image" alt="Attached" class="w-full h-auto object-cover hover:scale-102 transition-transform"
                                                @click="openImage(msg.image)" />
                                        </div>

                                        <!-- Message Bubble -->
                                        <div class="p-4 rounded-3xl rounded-tr-sm bg-gradient-to-br from-[#C9A84C]/20 to-[#C9A84C]/10 border border-[#C9A84C]/30 text-[#FAF8F5] shadow-md">
                                            <p class="text-sm font-sans whitespace-pre-wrap leading-relaxed">{{ msg.text }}</p>
                                        </div>

                                        <!-- Timestamp -->
                                        <span class="text-[10px] font-mono text-[#FAF8F5]/30 mt-1 px-2">
                                            {{ formatMsgTime(msg) }}
                                        </span>
                                    </div>

                                    <!-- User Avatar Pill -->
                                    <div class="w-8 h-8 rounded-full bg-[#C9A84C] text-[#0D0D12] font-bold text-xs flex items-center justify-center shrink-0 shadow-md">
                                        U
                                    </div>
                                </div>

                                <!-- ── Assistant / Persona Message (Left Aligned) ─── -->
                                <div v-else class="flex items-start gap-3.5 group max-w-[85%] md:max-w-[75%]">
                                    <!-- Persona Avatar -->
                                    <img :src="activePersonaAvatar"
                                        class="w-9 h-9 rounded-full object-cover border border-[#2A2A35] shrink-0 mt-1 shadow-sm" />

                                    <div class="flex flex-col items-start min-w-0 flex-1">
                                        <!-- Model Badge (if provided) -->
                                        <div v-if="msg.model" class="text-[10px] font-mono text-[#FAF8F5]/30 mb-1 flex items-center gap-1.5">
                                            <Bot class="w-3 h-3 text-[#C9A84C]" />
                                            <span>{{ msg.model }}</span>
                                        </div>

                                        <!-- Expandable Thinking Block -->
                                        <div v-if="msg.thinking" class="w-full mb-3">
                                            <button @click="toggleExpanded(expandedThoughts, msg.id || idx)"
                                                class="flex items-center gap-2 text-[11px] font-mono uppercase tracking-wider text-[#FAF8F5]/50 hover:text-[#C9A84C] py-1 px-2 rounded-lg bg-[#14141A] border border-[#2A2A35]/60 transition-colors">
                                                <ChevronRight class="w-3.5 h-3.5 transition-transform duration-200"
                                                    :class="{ 'rotate-90': isExpanded(expandedThoughts, msg.id || idx) }" />
                                                <span>Reasoning Trace ({{ msg.thinking_duration || '2.4s' }})</span>
                                            </button>
                                            <div v-show="isExpanded(expandedThoughts, msg.id || idx)"
                                                class="mt-1.5 p-3.5 rounded-2xl bg-[#0D0D12] border border-[#2A2A35] text-xs font-mono text-[#FAF8F5]/60 leading-relaxed whitespace-pre-wrap">
                                                {{ msg.thinking }}
                                            </div>
                                        </div>

                                        <!-- Message Content Bubble -->
                                        <div class="p-4 rounded-3xl rounded-tl-sm bg-[#14141A] border border-[#2A2A35] shadow-lg text-[#FAF8F5] w-full">
                                            <!-- Rendered Markdown Body -->
                                            <div class="prose prose-invert prose-sm max-w-none text-[#FAF8F5]/90 leading-relaxed"
                                                v-html="renderMarkdown(msg.text)" />

                                            <!-- Inline Image Manifestation -->
                                            <div v-if="msg.image || msg.image_prompt" class="mt-4 pt-3 border-t border-[#2A2A35]/80 space-y-3">
                                                <!-- Image Prompt Pill -->
                                                <div v-if="msg.image_prompt" class="flex items-center gap-1.5 flex-wrap">
                                                    <span class="text-[10px] font-mono uppercase tracking-widest text-[#C9A84C] bg-[#C9A84C]/10 border border-[#C9A84C]/20 px-2 py-0.5 rounded-full flex items-center gap-1">
                                                        <Sparkles class="w-2.5 h-2.5" /> Prompt
                                                    </span>
                                                    <span class="text-xs font-mono text-[#FAF8F5]/50 truncate max-w-sm">{{ msg.image_prompt }}</span>
                                                </div>

                                                <!-- Image Display -->
                                                <div v-if="msg.image" class="relative group/genimg rounded-2xl overflow-hidden border border-[#2A2A35] bg-[#0D0D12] max-w-md shadow-xl">
                                                    <img :src="msg.image" alt="Generated artifact"
                                                        class="w-full h-auto object-cover hover:scale-102 transition-transform duration-300 cursor-pointer"
                                                        @click="openImage(msg.image)" />
                                                    
                                                    <!-- Hover Actions Overlay -->
                                                    <div class="absolute inset-0 bg-[#0D0D12]/60 opacity-0 group-hover/genimg:opacity-100 transition-opacity flex items-center justify-center gap-2">
                                                        <button @click="openImage(msg.image)"
                                                            class="px-3 py-1.5 rounded-full bg-[#C9A84C] text-[#0D0D12] font-bold text-xs font-sans shadow-lg flex items-center gap-1 hover:brightness-110">
                                                            <Maximize2 class="w-3.5 h-3.5" /> Fullscreen
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Timestamp -->
                                        <span class="text-[10px] font-mono text-[#FAF8F5]/30 mt-1 px-2">
                                            {{ formatMsgTime(msg) }}
                                        </span>
                                    </div>
                                </div>
                            </template>
                        </div>

                        <!-- Typing / Generation Indicator -->
                        <div v-if="isTyping" class="flex items-center gap-3">
                            <img :src="activePersonaAvatar"
                                class="w-8 h-8 rounded-full object-cover border border-[#2A2A35] animate-pulse" />
                            <div class="px-4 py-3 rounded-2xl bg-[#14141A] border border-[#2A2A35] flex items-center gap-2">
                                <span class="w-2 h-2 rounded-full bg-[#C9A84C] animate-bounce"></span>
                                <span class="w-2 h-2 rounded-full bg-[#C9A84C] animate-bounce [animation-delay:0.2s]"></span>
                                <span class="w-2 h-2 rounded-full bg-[#C9A84C] animate-bounce [animation-delay:0.4s]"></span>
                                <span class="text-xs font-mono text-[#FAF8F5]/40 ml-1">
                                    {{ isGeneratingImage ? 'Manifesting image artifact…' : `${activePersonaName} is typing…` }}
                                </span>
                            </div>
                        </div>
                    </template>
                </div>

                <!-- ── Input Dock Container ──────────────────────────────────────── -->
                <div v-if="route.params.id" class="p-4 md:p-6 border-t border-[#2A2A35] bg-[#14141A]/60 backdrop-blur-xl relative z-20">
                    <!-- Suggested reply chips -->
                    <div v-if="chatMessages.length && !isTyping" class="flex gap-2 overflow-x-auto pb-2.5 mb-1 custom-scrollbar text-xs">
                        <button v-for="prompt in contextualSuggestions" :key="prompt"
                            @click="sendMessageDirect(prompt)"
                            class="whitespace-nowrap px-3 py-1 rounded-full bg-[#1A1A24] border border-[#2A2A35] text-[#FAF8F5]/70 hover:text-[#C9A84C] hover:border-[#C9A84C]/40 transition-all text-xs font-sans">
                            {{ prompt }}
                        </button>
                    </div>

                    <!-- Image Attachment Preview -->
                    <div v-if="attachedImageBase64" class="mb-3 relative inline-block">
                        <div class="relative rounded-2xl overflow-hidden border-2 border-[#C9A84C] shadow-lg w-24 h-24">
                            <img :src="attachedImageBase64" class="w-full h-full object-cover" />
                            <button @click="attachedImageBase64 = null"
                                class="absolute top-1 right-1 p-1 rounded-full bg-[#0D0D12]/80 text-white hover:bg-red-500 transition-colors">
                                <X class="w-3 h-3" />
                            </button>
                        </div>
                    </div>

                    <!-- Input Bar -->
                    <div class="flex items-center gap-2 bg-[#0D0D12] rounded-2xl border border-[#2A2A35] p-2 focus-within:border-[#C9A84C] focus-within:ring-1 focus-within:ring-[#C9A84C] transition-all shadow-inner">
                        <!-- Attachment Buttons -->
                        <button @click="triggerFileInput"
                            class="p-2.5 rounded-xl text-[#FAF8F5]/40 hover:text-[#C9A84C] hover:bg-[#14141A] transition-colors"
                            title="Attach image">
                            <Paperclip class="w-5 h-5" />
                        </button>

                        <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="handleFileSelected" />

                        <!-- Text Area Input -->
                        <textarea v-model="newMessage"
                            @keydown.enter.exact.prevent="sendMessage"
                            rows="1"
                            placeholder="Converse with persona… (Shift+Enter for newline)"
                            class="flex-1 bg-transparent text-sm text-[#FAF8F5] placeholder-[#FAF8F5]/30 focus:outline-none resize-none py-2 px-1 max-h-32 custom-scrollbar font-sans"></textarea>

                        <!-- Send Button -->
                        <button @click="sendMessage"
                            :disabled="(!newMessage.trim() && !attachedImageBase64) || isTyping"
                            class="w-10 h-10 rounded-xl bg-[#C9A84C] text-[#0D0D12] flex items-center justify-center font-bold hover:brightness-110 active:scale-95 disabled:opacity-40 disabled:pointer-events-none transition-all shadow-[0_0_12px_rgba(201,168,76,0.2)]">
                            <Send class="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </main>

            <!-- ── Right Persona Dossier Drawer ─────────────────────────────────── -->
            <aside v-if="infoDrawerOpen && route.params.id"
                class="w-80 border-l border-[#2A2A35] bg-[#14141A]/95 backdrop-blur-xl flex flex-col z-20 overflow-y-auto custom-scrollbar p-6 space-y-6">
                <div class="flex items-center justify-between pb-4 border-b border-[#2A2A35]">
                    <h3 class="font-serif italic font-bold text-lg text-[#FAF8F5]">Persona Dossier</h3>
                    <button @click="infoDrawerOpen = false" class="p-1 rounded-lg text-[#FAF8F5]/40 hover:text-white">
                        <X class="w-4 h-4" />
                    </button>
                </div>

                <!-- High-res Avatar Card -->
                <div class="text-center">
                    <img :src="activePersonaAvatar"
                        class="w-32 h-32 rounded-3xl object-cover border-2 border-[#C9A84C]/40 mx-auto shadow-2xl mb-4 hover:scale-102 transition-transform cursor-pointer"
                        @click="openImage(activePersonaAvatar)" />
                    <h4 class="font-bold text-lg text-[#FAF8F5]">{{ activePersonaName }}</h4>
                    <p class="text-xs font-mono text-[#C9A84C] mt-0.5">@{{ route.params.id }}</p>
                </div>

                <!-- Quick Navigation Links -->
                <div class="space-y-2">
                    <router-link :to="'/user/' + route.params.id"
                        class="w-full flex items-center justify-between p-3 rounded-xl bg-[#1A1A24] border border-[#2A2A35] hover:border-[#C9A84C]/50 text-xs font-sans font-semibold text-[#FAF8F5] transition-all group">
                        <span class="flex items-center gap-2">
                            <User class="w-4 h-4 text-[#C9A84C]" />
                            <span>Character Profile</span>
                        </span>
                        <ChevronRight class="w-4 h-4 text-[#FAF8F5]/30 group-hover:text-[#C9A84C] group-hover:translate-x-0.5 transition-all" />
                    </router-link>

                    <router-link :to="'/user/' + route.params.id + '?tab=media'"
                        class="w-full flex items-center justify-between p-3 rounded-xl bg-[#1A1A24] border border-[#2A2A35] hover:border-[#C9A84C]/50 text-xs font-sans font-semibold text-[#FAF8F5] transition-all group">
                        <span class="flex items-center gap-2">
                            <Sparkles class="w-4 h-4 text-[#C9A84C]" />
                            <span>Media Gallery</span>
                        </span>
                        <ChevronRight class="w-4 h-4 text-[#FAF8F5]/30 group-hover:text-[#C9A84C] group-hover:translate-x-0.5 transition-all" />
                    </router-link>
                </div>

                <!-- Backstory & Personality -->
                <div class="space-y-2">
                    <span class="text-[10px] font-mono uppercase tracking-widest text-[#FAF8F5]/40 font-semibold block">Background</span>
                    <div class="p-3.5 rounded-2xl bg-[#0D0D12] border border-[#2A2A35] text-xs font-sans text-[#FAF8F5]/80 leading-relaxed whitespace-pre-wrap max-h-60 overflow-y-auto custom-scrollbar">
                        {{ activePersonaDescription }}
                    </div>
                </div>

                <!-- Prompt Prefix / Tags (if available) -->
                <div v-if="currentCharacter?.prompt_prefix || chatData?.image_prompt" class="space-y-2">
                    <span class="text-[10px] font-mono uppercase tracking-widest text-[#FAF8F5]/40 font-semibold block">Style Trigger Tokens</span>
                    <div class="p-3 rounded-xl bg-[#0D0D12] border border-[#2A2A35] text-[11px] font-mono text-[#C9A84C]/90 break-words">
                        {{ currentCharacter?.prompt_prefix || chatData?.image_prompt }}
                    </div>
                </div>
            </aside>
        </div>

        <!-- ── Image Lightbox Modal ──────────────────────────────────────────── -->
        <div v-if="selectedImage" @click="closeImage"
            class="fixed inset-0 bg-[#0D0D12]/90 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <div class="relative max-w-4xl max-h-[90vh] rounded-3xl overflow-hidden border border-[#2A2A35] bg-[#14141A] shadow-2xl" @click.stop>
                <img :src="selectedImage" alt="Enlarged preview" class="max-h-[85vh] w-auto object-contain" />
                <button @click="closeImage"
                    class="absolute top-4 right-4 p-2 rounded-full bg-[#0D0D12]/80 text-[#FAF8F5] hover:text-[#C9A84C] border border-[#2A2A35] hover:border-[#C9A84C] transition-all">
                    <X class="w-5 h-5" />
                </button>
            </div>
        </div>

        <!-- ── Clear Chat Confirmation Modal ─────────────────────────────────── -->
        <div v-if="showClearConfirm" @click="showClearConfirm = false"
            class="fixed inset-0 bg-[#0D0D12]/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div class="bg-[#14141A] border border-[#2A2A35] rounded-3xl p-6 max-w-sm w-full shadow-2xl space-y-4" @click.stop>
                <h4 class="font-serif italic font-bold text-xl text-[#FAF8F5]">Clear Chronicle?</h4>
                <p class="text-xs font-sans text-[#FAF8F5]/60 leading-relaxed">
                    This will wipe the message history for this conversation. This action cannot be reversed.
                </p>
                <div class="flex justify-end gap-2 pt-2">
                    <button @click="showClearConfirm = false"
                        class="px-4 py-2 rounded-xl text-xs font-sans text-[#FAF8F5]/60 hover:text-white hover:bg-[#1A1A24] transition-all">
                        Cancel
                    </button>
                    <button @click="confirmClearChat"
                        class="px-4 py-2 rounded-xl text-xs font-sans font-bold bg-red-500 text-white hover:bg-red-600 transition-all shadow-md">
                        Clear All
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { apiUrl, formatRequest, GetFromApi, request } from '@/api';
import { ref, computed, nextTick, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { marked } from 'marked';
import {
    MessageSquare,
    Send,
    Sparkles,
    Trash2,
    User,
    Info,
    RefreshCw,
    ChevronRight,
    X,
    Bot,
    Paperclip,
    Search,
    Compass,
    Eye,
    Maximize2
} from 'lucide-vue-next';

// Configure marked for clean markdown
marked.setOptions({ breaks: true, gfm: true });

function renderMarkdown(content) {
    if (!content) return '';
    try {
        return marked.parse(content);
    } catch {
        return content;
    }
}

const route = useRoute();

// Reactive State
const chatData = ref(null);
const allChats = ref([]);
const characters = ref([]);
const newMessage = ref('');
const isTyping = ref(false);
const isGeneratingImage = ref(false);
const isRefreshing = ref(false);
const selectedImage = ref(null);
const messagesContainer = ref(null);
const fileInput = ref(null);
const attachedImageBase64 = ref(null);

// UI Controls
const searchQuery = ref('');
const sidebarTab = ref('all');
const mobileSidebarOpen = ref(false);
const infoDrawerOpen = ref(false);
const showClearConfirm = ref(false);
const expandedThoughts = ref({});

function toggleExpanded(store, id) {
    store.value[id] = !store.value[id];
}
function isExpanded(store, id) {
    return !!store.value[id];
}

// Active Persona Computeds
const isCharacterChat = computed(() => {
    return true;
});

const currentCharacter = computed(() => {
    if (!route.params.id) return null;
    return characters.value.find(c => c.id === route.params.id);
});

const activePersonaName = computed(() => {
    if (currentCharacter.value?.name) return currentCharacter.value.name;
    if (chatData.value?.character?.character_name) return chatData.value.character.character_name;
    return 'Companion';
});

const activePersonaAvatar = computed(() => {
    if (currentCharacter.value?.avatar) return currentCharacter.value.avatar;
    if (chatData.value?.character?.avatar) return chatData.value.character.avatar;
    if (route.params.id) {
        return `${apiUrl}/random-image-file?user=${route.params.id}`;
    }
    return 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&h=120&fit=crop';
});

const activePersonaDescription = computed(() => {
    if (currentCharacter.value?.description) return currentCharacter.value.description;
    if (chatData.value?.character?.short_description) return chatData.value.character.short_description;
    return 'A captivating companion ready to share thoughts, adventures, and imagery.';
});

const activePersonaSubtext = computed(() => {
    if (currentCharacter.value?.description) return currentCharacter.value.description.slice(0, 45) + '…';
    if (chatData.value?.character?.short_description) return chatData.value.character.short_description.slice(0, 45) + '…';
    return 'Interactive Companion';
});

const chatMessages = computed(() => {
    return chatData.value?.messages || [];
});

// Starters & Contextual Suggestions
const starterPrompts = [
    "Tell me about yourself.",
    "What are you thinking right now?",
    "Can you describe what you're wearing?",
    "Tell me a secret nobody else knows."
];

const contextualSuggestions = [
    "Can you send a selfie?",
    "What should we do next?",
    "Describe your surroundings.",
    "Tell me something cute."
];

// Filtering Sidebar Items
const filteredCharacters = computed(() => {
    const q = searchQuery.value.trim().toLowerCase();
    if (!q) return characters.value;
    return characters.value.filter(c =>
        c.name?.toLowerCase().includes(q) ||
        c.id?.toLowerCase().includes(q) ||
        c.description?.toLowerCase().includes(q)
    );
});

const filteredRecentChats = computed(() => {
    const q = searchQuery.value.trim().toLowerCase();
    // Only keep character-based chats
    let list = allChats.value.filter(c =>
        c.is_character_chat ||
        c.character ||
        characters.value.some(char => char.id === c.chat_id)
    );
    if (q) {
        list = list.filter(c =>
            c.chat_id?.toLowerCase().includes(q) ||
            c.character?.character_name?.toLowerCase().includes(q) ||
            characters.value.find(char => char.id === c.chat_id)?.name?.toLowerCase().includes(q) ||
            c.messages?.[c.messages.length - 1]?.text?.toLowerCase().includes(q)
        );
    }
    return list;
});

function getChatAvatar(c) {
    if (c.character?.avatar) return c.character.avatar;
    const charMatch = characters.value.find(char => char.id === c.chat_id);
    if (charMatch?.avatar) return charMatch.avatar;
    return `${apiUrl}/random-image-file?user=${c.chat_id}`;
}

function getChatTitle(c) {
    if (c.character?.character_name) return c.character.character_name;
    const charMatch = characters.value.find(char => char.id === c.chat_id);
    if (charMatch?.name) return charMatch.name;
    return c.chat_id;
}
function getLastMessageText(c) {
    if (!c.messages || !c.messages.length) return 'New chronicle started…';
    const last = c.messages[c.messages.length - 1];
    return last.text || (last.image ? 'Sent an image' : 'Message');
}

function formatMsgTime(msg) {
    if (msg.time) return msg.time;
    if (msg.timestamp) {
        const d = new Date(typeof msg.timestamp === 'number' && msg.timestamp < 10000000000 ? msg.timestamp * 1000 : msg.timestamp);
        if (!isNaN(d.getTime())) {
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
    }
    return '';
}

// ── Backend Communications ───────────────────────────────────────────────────

async function refreshAll() {
    isRefreshing.value = true;
    try {
        await Promise.all([RefreshChat(), loadCharacters()]);
    } finally {
        isRefreshing.value = false;
    }
}

async function RefreshChat() {
    if (route.params.id) {
        try {
            const res = await fetch(`${apiUrl}/chat/${route.params.id}`);
            if (res.ok) {
                chatData.value = await res.json();
            }
        } catch (e) {
            console.error('Failed to load active chat:', e);
        }
    }

    try {
        const chatsRes = await fetch(`${apiUrl}/chats`);
        if (chatsRes.ok) {
            allChats.value = await chatsRes.json();
        }
    } catch (e) {
        console.error('Failed to load recent chats:', e);
    }

    nextTick(() => {
        scrollToBottom();
    });
}

async function loadCharacters() {
    try {
        const data = await GetFromApi('characters');
        if (data && Array.isArray(data)) {
            characters.value = data;
        }
    } catch (e) {
        console.error('Failed to load characters:', e);
    }
}

async function sendMessageDirect(text) {
    newMessage.value = text;
    await sendMessage();
}

async function sendMessage() {
    const textToSend = newMessage.value.trim();
    const imageToSend = attachedImageBase64.value;
    if ((!textToSend && !imageToSend) || !route.params.id) return;

    newMessage.value = '';
    attachedImageBase64.value = null;

    if (!chatData.value) {
        chatData.value = { chat_id: route.params.id, messages: [] };
    }
    if (!chatData.value.messages) {
        chatData.value.messages = [];
    }

    // Optimistically push user message
    const optimisticMsg = {
        id: Date.now(),
        text: textToSend,
        image: imageToSend,
        isUser: true,
        timestamp: Date.now() / 1000
    };
    chatData.value.messages.push(optimisticMsg);

    isTyping.value = true;
    scrollToBottom();

    try {
        const body = {
            image_request: { ...request }
        };

        const response = await fetch(`${apiUrl}/chat/${route.params.id}/message?message=${encodeURIComponent(textToSend)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const responseData = await response.json();

        // If the persona decided to generate an image
        if (responseData.image_prompt) {
            isGeneratingImage.value = true;
            try {
                const _req = formatRequest(responseData.image_prompt);
                const txt2imgResponse = await fetch(`${apiUrl}/sdapi/v1/txt2img`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(_req)
                });

                if (txt2imgResponse.ok) {
                    const result = await txt2imgResponse.json();
                    if (result?.images?.[0]) {
                        // Associate image with the message in backend
                        const msgIdx = chatData.value.messages.length - 1;
                        await fetch(`${apiUrl}/chat/${route.params.id}/${msgIdx}/image`, {
                            method: 'POST'
                        });
                    }
                }
            } catch (imgErr) {
                console.error('Failed to generate persona image:', imgErr);
            } finally {
                isGeneratingImage.value = false;
            }
        }
    } catch (e) {
        console.error('Error sending message:', e);
    } finally {
        isTyping.value = false;
        await RefreshChat();
    }
}

async function confirmClearChat() {
    if (!route.params.id) return;
    try {
        await fetch(`${apiUrl}/chat/${route.params.id}`, { method: 'DELETE' });
        if (chatData.value) {
            chatData.value.messages = [];
        }
        showClearConfirm.value = false;
        await RefreshChat();
    } catch (e) {
        console.error('Failed to clear chat:', e);
    }
}

// ── Image Attachment Handling ─────────────────────────────────────────────────

function triggerFileInput() {
    fileInput.value?.click();
}

function handleFileSelected(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
        attachedImageBase64.value = event.target?.result;
    };
    reader.readAsDataURL(file);
    e.target.value = '';
}

function openImage(url) {
    selectedImage.value = url;
}

function closeImage() {
    selectedImage.value = null;
}

function scrollToBottom() {
    nextTick(() => {
        if (messagesContainer.value) {
            messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
        }
    });
}

onMounted(() => {
    RefreshChat();
    loadCharacters();
});

watch(() => route.params.id, () => {
    RefreshChat();
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
    width: 5px;
    height: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #2A2A35;
    border-radius: 9999px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #C9A84C;
}
</style>