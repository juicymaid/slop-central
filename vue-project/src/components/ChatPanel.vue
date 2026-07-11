<template>
	<div class="flex flex-col h-full bg-[#0D0D12] text-[#FAF8F5] relative overflow-hidden">

		<!-- ── Messages ─────────────────────────────────────────────────────── -->
		<div ref="scrollArea" class="flex-1 min-h-0 overflow-y-auto scroll-smooth">
			<!-- Empty state -->
			<div v-if="!history || history.length === 0"
				class="h-full flex flex-col items-center justify-center opacity-60 py-20">
				<ClearArt class="max-h-[280px] object-contain rounded-xl" />
				<p class="text-xs uppercase font-mono tracking-widest text-[#FAF8F5]/40 mt-5">AiriX Standby</p>
				<!-- Suggestion chips -->
				<div class="flex flex-wrap gap-2 justify-center mt-6 max-w-xs">
					<button v-for="s in suggestions" :key="s" @click="useSuggestion(s)"
						class="text-[11px] font-mono px-3 py-1.5 rounded-full border border-[#2A2A35] text-[#FAF8F5]/50 hover:text-[#C9A84C] hover:border-[#C9A84C]/50 transition-all duration-200">
						{{ s }}
					</button>
				</div>
			</div>

			<!-- Message list -->
			<div v-else class="px-4 py-5 space-y-5">
				<template v-for="(m, idx) in history" :key="m.id">

					<!-- RAG Context Pill (injected before assistant response) -->
					<div v-if="m.type === 'rag_context'" class="flex justify-center">
						<button @click="toggleRagPanel(m.id)"
							class="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-widest px-3 py-1 rounded-full border transition-all duration-200"
							:class="ragPanelOpen[m.id]
								? 'bg-violet-500/10 border-violet-500/30 text-violet-400'
								: 'bg-[#1A1A24] border-[#2A2A35] text-[#FAF8F5]/40 hover:text-violet-400 hover:border-violet-500/30'">
							<span class="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse"></span>
							RAG: {{ m.rag_docs?.length || 0 }} context · {{ m.active_skills?.length || 0 }} skills
							<span class="transition-transform duration-200"
								:class="ragPanelOpen[m.id] ? 'rotate-180' : ''">▾</span>
						</button>
					</div>

					<!-- RAG Context Expanded Panel -->
					<Transition name="slide-down">
						<div v-if="m.type === 'rag_context' && ragPanelOpen[m.id]"
							class="mx-2 bg-[#0F0F18] border border-violet-500/20 rounded-xl overflow-hidden">
							<!-- Skills chips -->
							<div v-if="m.active_skills?.length" class="px-4 pt-3 pb-2 border-b border-[#1A1A24]">
								<div class="text-[10px] font-mono text-violet-400/60 uppercase tracking-widest mb-2">Active Skills</div>
								<div class="flex flex-wrap gap-1.5">
									<span v-for="skill in m.active_skills" :key="skill.name"
										class="flex items-center gap-1 text-[10px] font-mono px-2.5 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-300">
										<span class="w-1 h-1 rounded-full bg-violet-400"></span>
										{{ skill.name.replace(/_/g, ' ') }}
									</span>
								</div>
							</div>
							<!-- RAG Docs -->
							<div v-if="m.rag_docs?.length" class="px-4 py-3 space-y-2.5">
								<div class="text-[10px] font-mono text-violet-400/60 uppercase tracking-widest mb-2">Retrieved Context</div>
								<div v-for="(doc, i) in m.rag_docs" :key="i"
									class="bg-[#1A1A24] rounded-lg p-2.5 group hover:border-violet-500/20 border border-transparent transition-colors">
									<div class="flex items-center justify-between mb-1">
										<div class="flex items-center gap-1.5">
											<span class="text-[9px] font-mono uppercase tracking-widest px-1.5 py-0.5 rounded bg-violet-500/10 text-violet-400">
												{{ doc.type || 'prompt' }}
											</span>
											<span v-if="doc.image_id" class="text-[9px] font-mono text-[#FAF8F5]/30">
												{{ doc.image_id.substring(0, 8) }}…
											</span>
										</div>
										<span class="text-[9px] font-mono text-[#FAF8F5]/30">score={{ doc.score }}</span>
									</div>
									<p class="text-[11px] text-[#FAF8F5]/60 leading-relaxed line-clamp-2">{{ doc.text }}</p>
									<a v-if="doc.url && doc.image_id"
										:href="`${apiUrl}${doc.url}`" target="_blank"
										class="inline-flex items-center gap-1 mt-1.5 text-[10px] font-mono text-violet-400 hover:text-violet-300 transition-colors">
										<img :src="`${apiUrl}${doc.url}`" class="w-6 h-6 object-cover rounded" />
										View image
									</a>
								</div>
							</div>
						</div>
					</Transition>

					<!-- Skip tool messages (they're attached to assistant messages) -->
					<template v-if="m.role !== 'tool' && m.type !== 'rag_context'">

						<!-- ── User message ──────────────────────────────────────────── -->
						<Message v-if="m.role === 'user'" from="user" class="msg-enter">
							<div class="flex flex-col gap-2 items-end max-w-[85%]">
								<!-- Attached images -->
								<div v-if="m.images?.length" class="flex flex-wrap gap-2 justify-end">
									<img v-for="(img, idx2) in m.images" :key="idx2"
										:src="displaySrc(img)"
										class="max-w-[160px] max-h-[120px] object-cover rounded-xl border border-[#2A2A35]" />
								</div>
								<MessageContent v-if="m.text">
									<MessageResponse>{{ m.text }}</MessageResponse>
								</MessageContent>
							</div>
							<!-- User avatar -->
							<div class="w-7 h-7 rounded-full bg-[#C9A84C] flex items-center justify-center text-xs font-serif font-bold italic text-[#0D0D12] flex-shrink-0 self-end">
								U
							</div>
						</Message>

						<!-- ── Assistant message ────────────────────────────────────── -->
						<Message v-else-if="m.role === 'assistant' && (!m.type || m.type === 'text')" from="assistant" class="msg-enter">
							<!-- Airi avatar -->
							<div class="w-7 h-7 rounded-full bg-[#2A2A35] border border-[#C9A84C]/30 flex items-center justify-center text-xs font-serif font-bold italic text-[#C9A84C] shadow-[0_0_10px_rgba(201,168,76,0.1)] flex-shrink-0 self-end">
								A
							</div>

							<MessageContent v-if="m.text || m.thinking || m.tool_calls?.length">
								<!-- Thinking block -->
								<div v-if="m.thinking" class="mb-2.5">
									<button @click="toggleThinking(m)"
										class="w-full flex items-center justify-between text-[10px] font-mono tracking-widest uppercase text-[#FAF8F5]/40 hover:text-[#C9A84C] transition-colors"
										type="button">
										<span class="truncate">Thought for {{ m.thinking_duration || '...' }} seconds</span>
										<span class="text-xs transition-transform duration-300"
											:class="m.showThinking ? 'rotate-180 text-[#C9A84C]' : ''">▾</span>
									</button>
									<div v-if="m.showThinking"
										class="mt-2 text-[11px] font-mono text-[#FAF8F5]/50 whitespace-pre-wrap leading-relaxed border-l-2 border-[#2A2A35] pl-3 py-1">
										{{ m.thinking }}
									</div>
								</div>

								<!-- Tool calls -->
								<div v-if="m.tool_calls?.length" class="space-y-2 mb-2.5">
									<div v-for="tc in m.tool_calls" :key="tc.id"
										class="border border-gray-800 rounded-lg overflow-hidden bg-gray-950/20 text-left">
										<!-- Header -->
										<div @click="toggleExpandedResult(tc.id)"
											class="flex items-center justify-between px-2.5 py-2 bg-gray-900/20 cursor-pointer select-none">
											<div class="flex items-center gap-2">
												<span class="w-2 h-2 rounded-full" :class="getToolColor(tc.function.name)"></span>
												<span class="text-xs font-semibold text-blue-400">{{ getToolPrettyName(tc.function.name) }}</span>
											</div>
											<div class="flex items-center gap-1.5">
												<span class="text-[9px] text-gray-500 bg-gray-900/60 px-1.5 py-0.5 rounded font-mono">{{ getToolNamespace(tc.function.name) }}</span>
												<span class="text-[10px] text-gray-400 transition-transform duration-200"
													:class="isResultExpanded(tc.id) ? 'rotate-90' : ''">▶</span>
											</div>
										</div>
										<!-- Body -->
										<div v-show="isResultExpanded(tc.id)" class="divide-y divide-gray-800/50 text-[#FAF8F5]/80">
											<div class="p-2.5 bg-gray-950/40 text-xs font-mono">
												<div @click.stop="toggleExpandedArgs(tc.id)"
													class="cursor-pointer flex items-center gap-1.5 text-gray-400 hover:text-gray-200 select-none mb-1">
													<span class="transition-transform duration-200" :class="{ 'rotate-90': isArgsExpanded(tc.id) }">▶</span>
													<span class="font-semibold">Arguments:</span>
													<span v-if="!isArgsExpanded(tc.id)" class="text-gray-500 truncate max-w-[200px]">{{ tc.function.arguments }}</span>
												</div>
												<pre v-show="isArgsExpanded(tc.id)"
													class="mt-1 p-2 bg-gray-950/80 rounded border border-gray-900 text-gray-300 overflow-x-auto whitespace-pre-wrap text-[11px]">{{ formatJson(tc.function.arguments) }}</pre>
											</div>
											<div v-if="getToolResult(tc.id)" class="p-2.5 bg-gray-950/40 text-xs font-mono">
												<div @click.stop="toggleExpandedResultSection(tc.id)"
													class="cursor-pointer flex items-center gap-1.5 text-gray-400 hover:text-gray-200 select-none">
													<span class="transition-transform duration-200" :class="{ 'rotate-90': isResultSectionExpanded(tc.id) }">▶</span>
													<span class="font-semibold">Result:</span>
												</div>
												<pre v-show="isResultSectionExpanded(tc.id)"
													class="mt-1 p-2 bg-gray-950/80 rounded border border-gray-900 text-gray-300 overflow-x-auto whitespace-pre-wrap text-[11px] max-h-[200px] overflow-y-auto">{{ formatJson(getToolResult(tc.id)) }}</pre>
											</div>
										</div>
									</div>
								</div>

								<!-- Text response -->
								<MessageResponse v-if="m.text">{{ m.text }}</MessageResponse>
							</MessageContent>
						</Message>

						<!-- ── Image result ──────────────────────────────────────────── -->
						<Message v-else-if="m.type === 'image'" from="assistant" class="msg-enter">
							<div class="w-7 h-7 rounded-full bg-[#2A2A35] border border-[#C9A84C]/30 flex items-center justify-center text-xs font-serif font-bold italic text-[#C9A84C] flex-shrink-0 self-end">A</div>
							<div class="bg-[#1A1A24] border border-[#2A2A35] rounded-[1.5rem] p-2 shadow-lg max-w-[85%]">
								<img :src="displaySrc(m.url)" alt="Generated image"
									class="max-w-[480px] rounded-[1.25rem] w-full" />
							</div>
						</Message>

						<!-- ── Search results grid ───────────────────────────────────── -->
						<div v-else-if="m.type === 'search'" class="msg-enter">
							<div class="bg-[#1A1A24] border border-[#2A2A35] rounded-2xl p-4 shadow-lg">
								<div class="flex items-center gap-2 mb-3">
									<span class="w-2 h-2 rounded-full bg-amber-400"></span>
									<span class="text-[10px] font-mono text-[#FAF8F5]/40 uppercase tracking-widest">Search:</span>
									<span class="text-sm font-serif italic text-[#C9A84C]">{{ m.query }}</span>
								</div>
								<div class="grid grid-cols-3 sm:grid-cols-4 gap-2">
									<div v-for="it in (m.items || [])" :key="it.id"
										class="rounded-xl overflow-hidden border border-[#2A2A35] group">
										<img :src="displaySrc(it.url)"
											class="w-full h-24 object-cover cursor-pointer group-hover:scale-105 transition-transform duration-500"
											:alt="it.prompt || ('image ' + it.id)" />
									</div>
								</div>
							</div>
						</div>

						<!-- ── Status pill ───────────────────────────────────────────── -->
						<div v-else-if="m.type === 'status'" class="flex justify-center msg-enter">
							<div class="bg-[#0D0D12] border border-[#2A2A35] rounded-full px-4 py-1.5 text-[11px] font-mono text-[#FAF8F5]/50 flex items-center gap-2">
								<span class="w-1.5 h-1.5 rounded-full bg-[#C9A84C] animate-pulse"></span>
								{{ m.text }}
							</div>
						</div>

						<!-- ── Prompt copyable ───────────────────────────────────────── -->
						<Message v-else-if="m.type === 'prompt'" from="assistant" class="msg-enter">
							<div class="w-7 h-7 rounded-full bg-[#2A2A35] border border-[#C9A84C]/30 flex items-center justify-center text-xs font-serif font-bold italic text-[#C9A84C] flex-shrink-0 self-end">A</div>
							<div class="bg-[#1A1A24] border border-[#2A2A35] rounded-2xl p-4 max-w-[85%]">
								<div class="text-[10px] font-mono text-[#FAF8F5]/40 uppercase tracking-widest mb-2">Generated Prompt</div>
								<div class="text-sm font-serif text-[#FAF8F5]/90 break-words mb-3">{{ m.prompt }}</div>
								<button @click="copyPrompt(m.prompt)"
									class="text-[10px] font-mono uppercase tracking-widest px-3 py-1.5 rounded-lg border border-[#2A2A35] hover:border-[#C9A84C] hover:text-[#C9A84C] text-[#FAF8F5]/50 transition-colors">
									Copy
								</button>
							</div>
						</Message>

						<!-- ── CivitAI Images ─────────────────────────────────────────── -->
						<div v-else-if="m.type === 'civitai_images'" class="msg-enter">
							<div class="bg-[#1A1A24] border border-[#2A2A35] rounded-2xl p-4 shadow-lg">
								<div class="flex items-center justify-between mb-3">
									<div class="text-[10px] font-mono text-[#FAF8F5]/40 uppercase tracking-widest">CivitAI Images</div>
									<div v-if="m.filters" class="text-[10px] font-mono text-[#FAF8F5]/30">
										<span v-if="m.filters.sort">{{ m.filters.sort }}</span>
										<span v-if="m.filters.period"> · {{ m.filters.period }}</span>
									</div>
								</div>
								<div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
									<div v-for="it in (m.items || [])" :key="it.id"
										class="bg-[#0D0D12] border border-[#2A2A35] rounded-xl overflow-hidden group hover:border-[#C9A84C]/30 transition-colors">
										<div class="aspect-[4/5] overflow-hidden">
											<img :src="displaySrc(it.url)"
												class="object-cover w-full h-full group-hover:scale-105 transition-transform duration-500"
												:alt="it.prompt || ('image ' + it.id)" />
										</div>
										<div class="p-2.5">
											<div class="text-[10px] text-[#FAF8F5]/60 line-clamp-2">{{ it.prompt || 'No prompt' }}</div>
											<div class="mt-1.5 flex flex-wrap gap-2 text-[9px] font-mono text-[#FAF8F5]/30">
												<span>♥ {{ formatCount(it.stats?.heartCount) }}</span>
												<span>👍 {{ formatCount(it.stats?.likeCount) }}</span>
											</div>
										</div>
									</div>
								</div>
							</div>
						</div>

						<!-- ── CivitAI Models ─────────────────────────────────────────── -->
						<div v-else-if="m.type === 'civitai'" class="msg-enter">
							<div class="bg-[#1A1A24] border border-[#2A2A35] rounded-2xl p-4 shadow-lg">
								<div class="text-[10px] font-mono text-[#FAF8F5]/40 uppercase tracking-widest mb-3">
									CivitAI Search: <span class="text-[#C9A84C]">{{ m.query }}</span>
								</div>
								<div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
									<div v-for="model in m.items" :key="model.id"
										class="bg-[#0D0D12] border border-[#2A2A35] rounded-xl p-3 flex flex-col group hover:border-[#C9A84C]/40 transition-colors">
										<div v-if="model.cover_image_url"
											class="aspect-video bg-[#1A1A24] overflow-hidden rounded-lg mb-2.5">
											<img :src="model.cover_image_url"
												class="object-cover w-full h-full group-hover:scale-105 transition-transform duration-500"
												:alt="model.name" />
										</div>
										<div class="font-sans font-semibold text-sm text-[#FAF8F5] truncate mb-1">{{ model.name }}</div>
										<div class="text-[11px] text-[#FAF8F5]/50 line-clamp-2 mb-2">{{ model.description }}</div>
										<a :href="model.url" target="_blank"
											class="mt-auto text-[10px] font-mono uppercase tracking-widest text-[#C9A84C] hover:text-[#FAF8F5] transition-colors">
											Open Model ↗
										</a>
									</div>
								</div>
							</div>
						</div>

					</template>
				</template>

				<!-- Typing indicator -->
				<Message v-if="isResponding" from="assistant" class="msg-enter">
					<div class="w-7 h-7 rounded-full bg-[#2A2A35] border border-[#C9A84C]/30 flex items-center justify-center text-xs font-serif font-bold italic text-[#C9A84C] flex-shrink-0 self-end animate-pulse">A</div>
					<MessageContent>
						<span class="typing">
							<span class="dot bg-[#C9A84C]"></span>
							<span class="dot bg-[#C9A84C]"></span>
							<span class="dot bg-[#C9A84C]"></span>
						</span>
					</MessageContent>
				</Message>

			</div>
		</div>

		<!-- ── Composer ──────────────────────────────────────────────────────── -->
		<div class="border-t border-[#2A2A35] bg-[#0D0D12]">
			<!-- Skills bar (shown when skills are active for the pending message) -->
			<Transition name="slide-down">
				<div v-if="activeSkillNames.length" class="px-4 pt-3 pb-0 flex flex-wrap gap-1.5">
					<span v-for="sname in activeSkillNames" :key="sname"
						class="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-300 transition-all">
						<span class="w-1 h-1 rounded-full bg-violet-400"></span>
						{{ sname.replace(/_/g, ' ') }}
					</span>
				</div>
			</Transition>

			<div class="p-4">
				<div class="bg-[#1A1A24] border border-[#2A2A35] rounded-2xl p-3 focus-within:border-[#C9A84C]/50 transition-colors shadow-inner">

					<!-- Image attachment previews -->
					<div v-if="attachedImages.length > 0" class="flex flex-wrap gap-2 mb-2.5 px-1">
						<div v-for="(img, idx) in attachedImages" :key="idx"
							class="relative group w-14 h-14 rounded-lg overflow-hidden border border-[#2A2A35]">
							<img :src="img" class="w-full h-full object-cover" />
							<button @click="attachedImages.splice(idx, 1)"
								class="absolute top-0.5 right-0.5 bg-red-600/80 text-white rounded-full w-4 h-4 flex items-center justify-center text-[9px] hover:bg-red-600 transition-colors">
								&times;
							</button>
						</div>
					</div>

					<!-- Textarea -->
					<textarea ref="composer" v-model="draft"
						:placeholder="isResponding ? 'AiriX is computing…' : 'Message AiriX (Enter to send, Shift+Enter for newline)'"
						class="w-full bg-transparent text-sm text-[#FAF8F5] font-sans resize-none focus:outline-none placeholder-[#FAF8F5]/25 px-1 py-1 leading-relaxed"
						rows="1" :disabled="isResponding"
						@keydown.enter.exact.prevent="trySend()"
						@keydown.enter.shift.exact.stop
						@input="autoResize"
						@paste="onPaste" />

					<!-- Actions row -->
					<div class="flex items-center justify-between mt-2.5 px-1">
						<div class="flex items-center gap-2">
							<button @click="insertAtCursor('{lora:example:1.0}')"
								class="text-[10px] uppercase font-mono tracking-widest px-2.5 py-1 rounded-lg border border-[#2A2A35] text-[#FAF8F5]/40 hover:text-[#C9A84C] hover:border-[#C9A84C]/50 transition-colors">
								LoRA
							</button>
							<button @click="triggerFileInput"
								class="text-[10px] uppercase font-mono tracking-widest px-2.5 py-1 rounded-lg border border-[#2A2A35] text-[#FAF8F5]/40 hover:text-[#C9A84C] hover:border-[#C9A84C]/50 transition-colors">
								Attach
							</button>
							<input type="file" ref="fileInput" class="hidden" accept="image/*" multiple @change="onFileChanged" />
						</div>

						<div class="flex items-center gap-2">
							<!-- Regenerate -->
							<button v-if="!isResponding" @click="regenerateLast"
								class="text-[10px] font-mono uppercase tracking-widest px-2.5 py-1 rounded-lg text-[#FAF8F5]/40 hover:text-[#C9A84C] transition-colors">
								Regen
							</button>
							<!-- Purge -->
							<button @click="clearChat"
								class="text-[10px] font-mono uppercase tracking-widest px-2.5 py-1 rounded-lg text-[#FAF8F5]/40 hover:text-red-400 transition-colors">
								Clear
							</button>
							<!-- Stop / Send -->
							<button v-if="isResponding" @click="stopResponse"
								class="flex items-center gap-1.5 bg-[#2A2A35] hover:bg-[#1A1A24] border border-[#2A2A35] hover:border-red-500/50 text-[#FAF8F5] px-4 py-1.5 rounded-full text-sm font-semibold transition-colors">
								<span class="w-2 h-2 rounded-sm bg-red-400"></span>
								Halt
							</button>
							<button v-else @click="trySend()"
								:disabled="!draft.trim() && attachedImages.length === 0"
								:class="(!draft.trim() && attachedImages.length === 0) ? 'opacity-40 cursor-not-allowed' : 'shadow-[0_0_12px_rgba(201,168,76,0.25)] hover:bg-[#B89A45]'"
								class="bg-[#C9A84C] text-[#0D0D12] px-5 py-1.5 rounded-full text-sm font-semibold transition-all duration-200">
								Send
							</button>
						</div>
					</div>
				</div>

				<!-- Footer -->
				<div class="flex items-center justify-between mt-2 px-1">
					<div class="text-[10px] font-mono text-[#FAF8F5]/20 flex items-center gap-1.5 uppercase tracking-widest">
						<span class="w-1 h-1 rounded-full bg-[#C9A84C] animate-pulse"></span>
						AiriX Intelligence
					</div>
					<div v-if="ragStatus" class="text-[10px] font-mono text-[#FAF8F5]/20 flex items-center gap-1">
						<span class="w-1 h-1 rounded-full" :class="ragStatus.indexed ? 'bg-green-400' : 'bg-yellow-400 animate-pulse'"></span>
						RAG {{ ragStatus.indexed ? ragStatus.document_count + ' docs' : 'indexing…' }}
					</div>
				</div>
			</div>
		</div>

	</div>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { wsUrl, webState, apiUrl, formatRequest } from '@/api'
import ClearArt from './ClearArt.vue'
import { Message, MessageContent, MessageResponse } from '@/components/ai-elements/message'

// Props
const props = defineProps({
	history: { type: Array, default: () => [] }
})

const suggestions = [
	'Show me random images',
	'Search for blonde hair',
	'Generate a forest scene',
	'Find CivitAI LoRAs',
	'Show trending CivitAI',
]

// Refs
const draft = ref('')
const attachedImages = ref([])
const fileInput = ref(null)
const isResponding = ref(false)
const socket = ref(null)
let reconnectTimer = null
const sessionId = ref(localStorage.getItem('assistant_session_id') || generateSessionId())
localStorage.setItem('assistant_session_id', sessionId.value)
const scrollArea = ref(null)
const composer = ref(null)

// RAG
const ragStatus = ref(null)
const ragPanelOpen = ref({})

// Skill preview — shows which skills might fire based on current draft
const allSkills = ref([])
const activeSkillNames = computed(() => {
	if (!draft.value.trim() || !allSkills.value.length) return []
	const msg = draft.value.toLowerCase()
	return allSkills.value
		.filter(s => s.trigger_keywords?.some(kw => msg.includes(kw.toLowerCase())))
		.map(s => s.name)
})

// Load skills list and RAG status
async function loadMeta() {
	try {
		const [skillsRes, ragRes] = await Promise.all([
			fetch(`${apiUrl}/skills`),
			fetch(`${apiUrl}/rag/status`),
		])
		if (skillsRes.ok) allSkills.value = await skillsRes.json()
		if (ragRes.ok) ragStatus.value = await ragRes.json()
	} catch { }
}

// RAG poll (every 5s while indexing)
let ragPollTimer = null
function startRagPoll() {
	ragPollTimer = setInterval(async () => {
		try {
			const res = await fetch(`${apiUrl}/rag/status`)
			if (res.ok) {
				ragStatus.value = await res.json()
				if (ragStatus.value?.indexed) clearInterval(ragPollTimer)
			}
		} catch { }
	}, 5000)
}

function toggleRagPanel(id) {
	ragPanelOpen.value[id] = !ragPanelOpen.value[id]
}

// ── ComfyUI ──────────────────────────────────────────────────────────────────
const comfyServerAddress = '127.0.0.1:8888'
const comfyClientId = 'chat_' + Date.now() + '_' + Math.floor(Math.random() * 1000)

const comfyTxt2ImgWorkflow = {
  "3": { "inputs": { "seed": 416319843187324, "steps": 8, "cfg": 1, "sampler_name": "euler", "scheduler": "simple", "denoise": 1, "model": ["76", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["91", 0] }, "class_type": "KSampler", "_meta": { "title": "KSampler" } },
  "6": { "inputs": { "text": "<PROMPT>", "clip": ["76", 1] }, "class_type": "CLIPTextEncode", "_meta": { "title": "CLIP Text Encode (Positive Prompt)" } },
  "7": { "inputs": { "text": "sfw blurry ugly bad", "clip": ["76", 1] }, "class_type": "CLIPTextEncode", "_meta": { "title": "CLIP Text Encode (Negative Prompt)" } },
  "8": { "inputs": { "samples": ["3", 0], "vae": ["17", 0] }, "class_type": "VAEDecode", "_meta": { "title": "VAE Decode" } },
  "9": { "inputs": { "filename_prefix": "ComfyUI", "images": ["8", 0] }, "class_type": "SaveImage", "_meta": { "title": "Save Image" } },
  "11": { "inputs": { "shift": 4, "model": ["16", 0] }, "class_type": "ModelSamplingAuraFlow", "_meta": { "title": "ModelSamplingAuraFlow" } },
  "16": { "inputs": { "unet_name": "z_image_turbo_fp8_e4m3fn.safetensors", "weight_dtype": "default" }, "class_type": "UNETLoader", "_meta": { "title": "Load Diffusion Model" } },
  "17": { "inputs": { "vae_name": "ae.safetensors" }, "class_type": "VAELoader", "_meta": { "title": "Load VAE" } },
  "28": { "inputs": { "value": 1920 }, "class_type": "PrimitiveInt", "_meta": { "title": "Int" } },
  "29": { "inputs": { "value": 1088 }, "class_type": "PrimitiveInt", "_meta": { "title": "Int" } },
  "37": { "inputs": { "width": ["29", 0], "height": ["28", 0], "batch_size": 1 }, "class_type": "EmptyLatentImage", "_meta": { "title": "Empty Latent Image" } },
  "76": { "inputs": { "lora_01": "ZiT\\Mystic-XXX-ZIT-V7.safetensors", "strength_01": 0.35, "lora_02": "ZiT\\RealisticSnapshot-Zimage-Turbov5.safetensors", "strength_02": 0.5, "lora_03": "ZiT\\breast_size_v2_loraholic.safetensors", "strength_03": 3, "lora_04": "ZiT\\PerfectBreastsZIT_v10.safetensors", "strength_04": 0.5, "model": ["11", 0], "clip": ["99", 0] }, "class_type": "Lora Loader Stack (rgthree)", "_meta": { "title": "Lora Loader Stack (rgthree)" } },
  "82": { "inputs": { "value": 1024 }, "class_type": "PrimitiveInt", "_meta": { "title": "Int" } },
  "83": { "inputs": { "width": ["101", 0], "height": ["101", 1], "batch_size": 1 }, "class_type": "EmptyLatentImage", "_meta": { "title": "Empty Latent Image" } },
  "84": { "inputs": { "value": 1664 }, "class_type": "PrimitiveInt", "_meta": { "title": "Int" } },
  "91": { "inputs": { "selection_setting": 1, "input_1": ["37", 0], "input_2": ["83", 0] }, "class_type": "TwoWaySwitch", "_meta": { "title": "1 - final draft, 2 - rough draft" } },
  "99": { "inputs": { "clip_name": "Qwen3-4b-Z-Image-Engineer-V4-Q5_K_S.gguf", "type": "lumina2", "device": "default" }, "class_type": "ClipLoaderGGUF", "_meta": { "title": "GGUF CLIP Loader" } },
  "101": { "inputs": { "aspect_ratio": "2:3 (Portrait Photo)", "megapixels": 1, "multiple": 8 }, "class_type": "ResolutionSelector", "_meta": { "title": "Resolution Selector" } },
}

const comfyInpaintWorkflow = {
  "3": { "inputs": { "seed": 195269461328067, "steps": 8, "cfg": 1, "sampler_name": "res_multistep", "scheduler": "simple", "denoise": 1, "model": ["146", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["147", 0] }, "class_type": "KSampler" },
  "6": { "inputs": { "text": "<PROMPT>", "clip": ["76", 1] }, "class_type": "CLIPTextEncode" },
  "7": { "inputs": { "text": "sfw blurry ugly bad", "clip": ["76", 1] }, "class_type": "CLIPTextEncode" },
  "8": { "inputs": { "samples": ["3", 0], "vae": ["17", 0] }, "class_type": "VAEDecode" },
  "9": { "inputs": { "filename_prefix": "deepfake/ComfyUI", "images": ["8", 0] }, "class_type": "SaveImage" },
  "11": { "inputs": { "shift": 4, "model": ["16", 0] }, "class_type": "ModelSamplingAuraFlow" },
  "16": { "inputs": { "unet_name": "z_image_turbo_fp8_e4m3fn.safetensors", "weight_dtype": "default" }, "class_type": "UNETLoader" },
  "17": { "inputs": { "vae_name": "ae.safetensors" }, "class_type": "VAELoader" },
  "76": { "inputs": { "lora_01": "ZiT\\Mystic-XXX-ZIT-V7.safetensors", "strength_01": 0.35, "lora_02": "ZiT\\RealisticSnapshot-Zimage-Turbov5.safetensors", "strength_02": 0.5, "lora_03": "ZiT\\breast_size_v2_loraholic.safetensors", "strength_03": 3, "lora_04": "ZiT\\PerfectBreastsZIT_v10.safetensors", "strength_04": 0.5, "model": ["11", 0], "clip": ["99", 0] }, "class_type": "Lora Loader Stack (rgthree)" },
  "99": { "inputs": { "clip_name": "Qwen3-4b-Z-Image-Engineer-V4-Q5_K_S.gguf", "type": "lumina2", "device": "default" }, "class_type": "ClipLoaderGGUF" },
  "140": { "inputs": { "name": "Z-Image-Turbo-Fun-Controlnet-Union-2.1-lite-2602-8steps.safetensors" }, "class_type": "ModelPatchLoader" },
  "145": { "inputs": { "grow_mask_by": 6 }, "class_type": "VAEEncodeForInpaint" },
  "146": { "inputs": { "strength": 0.75, "model": ["76", 0], "model_patch": ["140", 0], "vae": ["17", 0], "inpaint_image": ["122:116", 0], "mask": ["122:15", 0] }, "class_type": "ZImageFunControlnet" },
  "147": { "inputs": { "width": ["122:141", 0], "height": ["122:141", 1], "batch_size": 1 }, "class_type": "EmptySD3LatentImage" },
  "148": { "inputs": { "image": "pasted/image (25).png" }, "class_type": "LoadImage" },
  "122:2": { "inputs": { "threshold": 0.5, "refine_iterations": 2, "individual_masks": false, "model": ["122:4", 0], "image": ["122:116", 0], "conditioning": ["122:117", 0] }, "class_type": "SAM3_Detect" },
  "122:116": { "inputs": { "upscale_method": "lanczos", "megapixels": 1, "resolution_steps": 1, "image": ["148", 0] }, "class_type": "ImageScaleToTotalPixels" },
  "122:4": { "inputs": { "ckpt_name": "sam3.1_multiplex_fp16.safetensors" }, "class_type": "CheckpointLoaderSimple" },
  "122:5": { "inputs": { "mask": ["122:2", 0] }, "class_type": "MaskPreview" },
  "122:117": { "inputs": { "text": "<SAM_PROMPT>", "clip": ["122:4", 1] }, "class_type": "CLIPTextEncode" },
  "122:118": { "inputs": { "image": ["122:116", 0], "alpha": ["122:15", 0] }, "class_type": "JoinImageWithAlpha" },
  "122:15": { "inputs": { "expand": 24, "incremental_expandrate": 0, "tapered_corners": true, "flip_input": false, "blur_radius": 12, "lerp_alpha": 1, "decay_factor": 1, "fill_holes": true, "mask": ["122:2", 0] }, "class_type": "GrowMaskWithBlur" },
  "122:141": { "inputs": { "image": ["122:116", 0] }, "class_type": "GetImageSize" },
}

// ── ComfyUI helpers (unchanged from original) ─────────────────────────────
async function uploadImageToComfyUi(dataUrl) {
	let blob
	if (dataUrl.startsWith('data:image')) {
		blob = await (await fetch(dataUrl)).blob()
	} else {
		const res = await fetch(dataUrl)
		if (!res.ok) throw new Error(`Failed to fetch image source from backend: ${res.status}`)
		blob = await res.blob()
	}
	const file = new File([blob], `chat-inpaint-${Date.now()}.png`, { type: blob.type || 'image/png' })
	const form = new FormData()
	form.append('image', file)
	const res = await fetch(`http://${comfyServerAddress}/upload/image`, { method: 'POST', body: form })
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
		method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
	})
	if (!res.ok) throw new Error(`ComfyUI queue failed: ${res.status}`)
	return await res.json()
}

function connectComfyWs() {
	return new Promise((resolve, reject) => {
		const ws = new WebSocket(`ws://${comfyServerAddress}/ws?clientId=${encodeURIComponent(comfyClientId)}`)
		ws.onopen = () => resolve(ws)
		ws.onerror = (e) => reject(e)
	})
}

// ── Input helpers ─────────────────────────────────────────────────────────
function triggerFileInput() { fileInput.value?.click() }

function onFileChanged(e) {
	const files = e.target.files
	if (!files) return
	for (let i = 0; i < files.length; i++) {
		const reader = new FileReader()
		reader.onload = (ev) => { if (ev.target?.result) attachedImages.value.push(String(ev.target.result)) }
		reader.readAsDataURL(files[i])
	}
	e.target.value = ''
}

function onPaste(e) {
	const items = e.clipboardData?.items
	if (!items) return
	for (let i = 0; i < items.length; i++) {
		if (items[i].type.indexOf('image') !== -1) {
			const blob = items[i].getAsFile()
			if (blob) {
				const reader = new FileReader()
				reader.onload = (ev) => { if (ev.target?.result) attachedImages.value.push(String(ev.target.result)) }
				reader.readAsDataURL(blob)
			}
		}
	}
}

function toggleThinking(m) { m.showThinking = !m.showThinking }

function displaySrc(u) {
	if (!u) return ''
	if (u.startsWith('data:image')) return u
	if (u.startsWith('/')) return `${apiUrl}${u}`
	return u
}

function formatCount(value) {
	const n = Number(value)
	if (!Number.isFinite(n)) return '0'
	if (n >= 1000000) return `${(n / 1000000).toFixed(1)}m`
	if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
	return String(n)
}

function scrollToBottom() {
	nextTick(() => { if (scrollArea.value) scrollArea.value.scrollTop = scrollArea.value.scrollHeight })
}

function autoResize() {
	if (!composer.value) return
	composer.value.style.height = 'auto'
	composer.value.style.height = `${composer.value.scrollHeight}px`
	scrollToBottom()
}

function useSuggestion(s) { draft.value = s; nextTick(autoResize) }

function insertAtCursor(text) {
	const el = composer.value
	if (!el) { draft.value += text; return }
	const start = el.selectionStart || draft.value.length
	const end = el.selectionEnd || draft.value.length
	draft.value = draft.value.slice(0, start) + text + draft.value.slice(end)
	nextTick(() => { el.selectionStart = el.selectionEnd = start + text.length; autoResize() })
}

function trySend() {
	if ((!draft.value.trim() && attachedImages.value.length === 0) || isResponding.value) return
	const userText = draft.value.trim()
	const imgsToSend = [...attachedImages.value]
	props.history.push({ id: Date.now(), role: 'user', text: userText, images: imgsToSend })
	draft.value = ''
	attachedImages.value = []
	autoResize()
	scrollToBottom()
	ensureSocket()
	props.history.push({ id: Date.now() + 1, role: 'assistant', text: '', thinking: '', showThinking: false })
	isResponding.value = true
	try { socket.value?.send(JSON.stringify({ type: 'user', content: userText, images: imgsToSend })) } catch { }
}

function stopResponse() {
	try { socket.value?.send(JSON.stringify({ type: 'stop' })) } catch { }
	isResponding.value = false
}

function clearChat() {
	stopResponse()
	props.history.splice(0)
	try { socket.value?.send(JSON.stringify({ type: 'reset' })) } catch { }
}

function regenerateLast() {
	if (isResponding.value) return
	const lastUser = [...props.history].reverse().find(m => m.role === 'user')
	if (!lastUser) return
	props.history.push({ id: Date.now(), role: 'user', text: lastUser.text, images: lastUser.images || [] })
	props.history.push({ id: Date.now() + 1, role: 'assistant', text: '', thinking: '', showThinking: false })
	isResponding.value = true
	ensureSocket()
	try { socket.value?.send(JSON.stringify({ type: 'user', content: lastUser.text, images: lastUser.images || [] })) } catch { }
}

function ensureSocket() {
	if (socket.value && socket.value.readyState === WebSocket.OPEN) return
	connectSocket()
}

function connectSocket() {
	try { if (socket.value) socket.value.close() } catch { }
	const ws = new WebSocket(`${wsUrl}/assistant`)
	socket.value = ws

	ws.onopen = () => {
		try { ws.send(JSON.stringify({ type: 'init', session_id: sessionId.value })) } catch { }
	}

	ws.onmessage = (event) => {
		try {
			const msg = JSON.parse(event.data)

			if (msg.type === 'history') {
				if (props.history.length === 0 && Array.isArray(msg.messages)) {
					for (const m of msg.messages) {
						props.history.push({
							id: Date.now() + Math.random(),
							role: m.role || 'assistant',
							text: m.content,
							thinking: m.thinking || '',
							showThinking: false,
							images: m.images || [],
							tool_calls: m.tool_calls || null,
							tool_call_id: m.tool_call_id || null,
							type: m.type || null,
							url: m.url || null,
							items: m.items || null,
							query: m.query || null,
							prompt: m.prompt || null,
							filters: m.filters || null,
						})
					}
					scrollToBottom()
				}

			} else if (msg.type === 'rag_context') {
				// Insert RAG context as a special history entry (for UI display)
				const entry = {
					id: Date.now() + Math.random(),
					role: 'system',
					type: 'rag_context',
					rag_docs: msg.rag_docs || [],
					active_skills: msg.active_skills || [],
				}
				props.history.push(entry)
				scrollToBottom()

			} else if (msg.type === 'content') {
				const last = [...props.history].reverse().find(m => m.role === 'assistant')
				if (last) {
					if (typeof last.text !== 'string') last.text = ''
					last.text += msg.delta || ''
				} else {
					props.history.push({ id: Date.now(), role: 'assistant', text: msg.delta || '', thinking: '', showThinking: false })
				}
				scrollToBottom()

			} else if (msg.type === 'tool_result') {
				const last = [...props.history].reverse().find(m => m.role === 'assistant')
				if (last) {
					if (!last.tool_calls) last.tool_calls = []
					if (!last.tool_calls.some(tc => tc.function.name === msg.tool)) {
						last.tool_calls.push({
							id: `call_${msg.tool}_${Date.now()}`,
							type: 'function',
							function: {
								name: msg.tool,
								arguments: typeof msg.args === 'string' ? msg.args : JSON.stringify(msg.args)
							}
						})
					}
				}
				const resultStr = typeof msg.result === 'string' ? msg.result : JSON.stringify(msg.result, null, 2)
				props.history.push({
					id: Date.now() + Math.random(),
					role: 'tool',
					tool_call_id: last && last.tool_calls ? last.tool_calls[last.tool_calls.length - 1].id : `call_${msg.tool}_${Date.now()}`,
					text: resultStr
				})

				// Custom visualizations
				if (msg.tool === 'search_images') {
					props.history.push({ id: Date.now(), role: 'assistant', type: 'search', query: msg?.args?.query || '', items: Array.isArray(msg.result) ? msg.result : [] })
				} else if (msg.tool === 'show_image') {
					props.history.push({ id: Date.now(), role: 'assistant', type: 'image', url: msg?.result?.url || '' })
				} else if (msg.tool === 'generate_new_image') {
					const prompt = msg?.result?.prompt || ''
					const statusMsg = { id: Date.now(), role: 'assistant', type: 'status', text: `Generating image for: ${prompt}` }
					props.history.push(statusMsg)
					startGeneration(prompt, statusMsg)
				} else if (msg.tool === 'inpaint_image') {
					const imageId = msg?.result?.image_id || ''
					const samPrompt = msg?.result?.sam_prompt || ''
					const prompt = msg?.result?.prompt || ''
					const statusMsg = { id: Date.now(), role: 'assistant', type: 'status', text: `Inpainting image ${imageId} (${samPrompt}) → ${prompt}` }
					props.history.push(statusMsg)
					startInpaint(imageId, samPrompt, prompt, statusMsg)
				} else if (msg.tool === 'show_prompt') {
					props.history.push({ id: Date.now(), role: 'assistant', type: 'prompt', prompt: msg?.result?.prompt || '' })
				} else if (msg.tool === 'search_civitai_models') {
					props.history.push({ id: Date.now(), role: 'assistant', type: 'civitai', query: msg?.args?.query || '', items: Array.isArray(msg.result) ? msg.result : [] })
				} else if (msg.tool === 'get_civitai_images') {
					const payload = msg.result || {}
					props.history.push({ id: Date.now(), role: 'assistant', type: 'civitai_images', items: Array.isArray(payload.items) ? payload.items : [], metadata: payload.metadata || {}, filters: payload.filters || {} })
				} else if (msg.tool === 'search_knowledge_base') {
					// RAG tool was called explicitly — show results as a search-style card
					const results = Array.isArray(msg.result) ? msg.result : []
					props.history.push({
						id: Date.now(), role: 'assistant', type: 'search',
						query: msg?.args?.query || 'knowledge base search',
						items: results.filter(r => r.image_id).map(r => ({ id: r.image_id, url: r.url, prompt: r.text }))
					})
				}
				scrollToBottom()

			} else if (msg.type === 'thinking') {
				isResponding.value = true
				const last = [...props.history].reverse().find(m => m.role === 'assistant')
				if (last) {
					if (typeof last.thinking !== 'string') last.thinking = ''
					last.thinking += msg.delta || ''
				}
			} else if (msg.type === 'message_end') {
				isResponding.value = false
				scrollToBottom()
			}
		} catch { }
	}

	ws.onerror = () => { }
	ws.onclose = () => {
		if (reconnectTimer) return
		reconnectTimer = setTimeout(() => { reconnectTimer = null; connectSocket() }, 1000)
	}
}

onMounted(() => {
	connectSocket()
	loadMeta()
	startRagPoll()
	nextTick(() => { autoResize(); scrollToBottom() })
})

onBeforeUnmount(() => {
	try { socket.value?.close() } catch { }
	if (reconnectTimer) clearTimeout(reconnectTimer)
	if (ragPollTimer) clearInterval(ragPollTimer)
})

// ── ComfyUI generation (unchanged) ───────────────────────────────────────
async function startGeneration(promptText, statusMsg) {
	let comfyWs = null
	try {
		const workflow = JSON.parse(JSON.stringify(comfyTxt2ImgWorkflow))
		workflow["6"].inputs.text = promptText
		workflow["3"].inputs.seed = Math.floor(Math.random() * 9007199254740991)
		comfyWs = await connectComfyWs()
		const queued = await queueComfyPrompt(workflow)
		const promptId = queued?.prompt_id
		if (!promptId) throw new Error('ComfyUI did not return a prompt_id')
		let receivedImgUrl = null
		await new Promise((resolve, reject) => {
			comfyWs.onmessage = async (evt) => {
				if (typeof evt.data === 'string') {
					let message; try { message = JSON.parse(evt.data) } catch { return }
					if (message?.type === 'progress') {
						const v = Number(message?.data?.value); const m = Number(message?.data?.max)
						if (m > 0 && statusMsg) statusMsg.text = `Generating image: ${Math.round((v / m) * 100)}%`
						return
					}
					if (message?.type === 'executing') {
						const data = message?.data
						if (data?.prompt_id !== promptId) return
						if (data?.node == null) { if (receivedImgUrl) resolve(); else reject(new Error('No image received')); return }
					}
					if (message?.type === 'executed') {
						const data = message?.data
						if (data?.prompt_id !== promptId || String(data?.node) !== '9') return
						const images = data?.output?.images || []
						if (images.length > 0) {
							const imgInfo = images[0]
							receivedImgUrl = `http://${comfyServerAddress}/view?filename=${encodeURIComponent(imgInfo.filename)}&type=${encodeURIComponent(imgInfo.type || 'output')}&subfolder=${encodeURIComponent(imgInfo.subfolder || '')}`
							resolve()
						}
					}
				}
			}
			comfyWs.onclose = () => resolve()
			comfyWs.onerror = (e) => reject(e)
		})
		if (receivedImgUrl) props.history.push({ id: Date.now(), role: 'assistant', type: 'image', url: receivedImgUrl })
		else props.history.push({ id: Date.now(), role: 'assistant', text: 'Generation finished but no image URL obtained.' })
	} catch (e) {
		props.history.push({ id: Date.now(), role: 'assistant', text: `Generation failed: ${e.message || e}` })
	} finally {
		try { comfyWs?.close() } catch { }
		scrollToBottom()
	}
}

async function startInpaint(imageId, samPrompt, promptText, statusMsg) {
	let comfyWs = null
	try {
		let id = String(imageId).trim()
		const match = id.match(/(\d+)/); if (match) id = match[1]
		const imgUrl = `${apiUrl}/image-file/${encodeURIComponent(id)}`
		const uploadedPath = await uploadImageToComfyUi(imgUrl)
		const workflow = JSON.parse(JSON.stringify(comfyInpaintWorkflow))
		workflow["6"].inputs.text = promptText
		workflow["122:117"].inputs.text = samPrompt
		workflow["148"].inputs.image = uploadedPath
		workflow["3"].inputs.seed = Math.floor(Math.random() * 9007199254740991)
		comfyWs = await connectComfyWs()
		const queued = await queueComfyPrompt(workflow)
		const promptId = queued?.prompt_id
		if (!promptId) throw new Error('ComfyUI did not return a prompt_id')
		let receivedImgUrl = null
		await new Promise((resolve, reject) => {
			comfyWs.onmessage = async (evt) => {
				if (typeof evt.data === 'string') {
					let message; try { message = JSON.parse(evt.data) } catch { return }
					if (message?.type === 'progress') {
						const v = Number(message?.data?.value); const m = Number(message?.data?.max)
						if (m > 0 && statusMsg) statusMsg.text = `Inpainting image: ${Math.round((v / m) * 100)}%`
						return
					}
					if (message?.type === 'executing') {
						const data = message?.data
						if (data?.prompt_id !== promptId) return
						if (data?.node == null) { if (receivedImgUrl) resolve(); else reject(new Error('No image received')); return }
					}
					if (message?.type === 'executed') {
						const data = message?.data
						if (data?.prompt_id !== promptId || String(data?.node) !== '9') return
						const images = data?.output?.images || []
						if (images.length > 0) {
							const imgInfo = images[0]
							receivedImgUrl = `http://${comfyServerAddress}/view?filename=${encodeURIComponent(imgInfo.filename)}&type=${encodeURIComponent(imgInfo.type || 'output')}&subfolder=${encodeURIComponent(imgInfo.subfolder || '')}`
							resolve()
						}
					}
				}
			}
			comfyWs.onclose = () => resolve()
			comfyWs.onerror = (e) => reject(e)
		})
		if (receivedImgUrl) props.history.push({ id: Date.now(), role: 'assistant', type: 'image', url: receivedImgUrl })
		else props.history.push({ id: Date.now(), role: 'assistant', text: 'Inpainting finished but no image URL obtained.' })
	} catch (e) {
		props.history.push({ id: Date.now(), role: 'assistant', text: `Inpainting failed: ${e.message || e}` })
	} finally {
		try { comfyWs?.close() } catch { }
		scrollToBottom()
	}
}

function generateSessionId() {
	return 'sess_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8)
}

function copyPrompt(p) { try { navigator.clipboard.writeText(p) } catch { } }

// ── Tool call UI helpers ──────────────────────────────────────────────────
const expandedResults = ref({})
const expandedArgs = ref({})
const expandedResultSections = ref({})

function toggleExpandedResult(id) { expandedResults.value[id] = !expandedResults.value[id] }
function isResultExpanded(id) { return expandedResults.value[id] !== false }
function toggleExpandedArgs(id) { expandedArgs.value[id] = !expandedArgs.value[id] }
function isArgsExpanded(id) { return !!expandedArgs.value[id] }
function toggleExpandedResultSection(id) { expandedResultSections.value[id] = !expandedResultSections.value[id] }
function isResultSectionExpanded(id) { return expandedResultSections.value[id] !== false }

function getToolResult(toolCallId) {
	const toolMsg = props.history.find(m => m.role === 'tool' && m.tool_call_id === toolCallId)
	return toolMsg ? toolMsg.text : null
}

function formatJson(val) {
	if (!val) return ''
	if (typeof val === 'object') return JSON.stringify(val, null, 2)
	try { return JSON.stringify(JSON.parse(val), null, 2) } catch { return val }
}

function getToolPrettyName(name) {
	const map = {
		search_images: 'Search Images', get_random_images: 'Get Random Images', show_image: 'Show Image',
		generate_new_image: 'Generate Image', inpaint_image: 'Inpaint Image',
		search_civitai_models: 'Search CivitAI', get_civitai_images: 'CivitAI Images',
		show_prompt: 'Show Prompt', search_knowledge_base: 'Knowledge Base', search: 'Web Search', 'visit-website': 'Visit Website',
	}
	return map[name] || name
}

function getToolNamespace(name) {
	const map = {
		search_images: 'local/images', get_random_images: 'local/random', show_image: 'local/show',
		generate_new_image: 'local/generate', inpaint_image: 'local/inpaint',
		search_civitai_models: 'civitai/models', get_civitai_images: 'civitai/images',
		show_prompt: 'local/prompt', search_knowledge_base: 'rag/search',
		search: 'web/search', 'visit-website': 'web/visit',
	}
	return map[name] || 'mcp/' + name
}

function getToolColor(name) {
	if (['search', 'search_images', 'search_civitai_models', 'search_knowledge_base'].includes(name)) return 'bg-amber-400'
	if (['visit-website', 'show_image'].includes(name)) return 'bg-blue-400'
	if (name === 'generate_new_image') return 'bg-emerald-400'
	if (name === 'inpaint_image') return 'bg-violet-400'
	return 'bg-green-400'
}
</script>

<style scoped>
/* Message enter animation */
.msg-enter {
	animation: msgIn 0.25s ease-out both;
}

@keyframes msgIn {
	from { opacity: 0; transform: translateY(8px); }
	to   { opacity: 1; transform: translateY(0); }
}

/* Slide-down for RAG panel */
.slide-down-enter-active,
.slide-down-leave-active {
	transition: all 0.2s ease;
	overflow: hidden;
}
.slide-down-enter-from,
.slide-down-leave-to {
	opacity: 0;
	max-height: 0;
}
.slide-down-enter-to,
.slide-down-leave-from {
	opacity: 1;
	max-height: 800px;
}

/* Typing indicator */
.typing {
	display: inline-flex;
	align-items: center;
	gap: 4px;
}
.dot {
	width: 6px;
	height: 6px;
	border-radius: 9999px;
	background: #a3a3a3;
	animation: blink 1.2s infinite ease-in-out;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink {
	0%, 80%, 100% { opacity: 0.2; transform: translateY(0); }
	40%           { opacity: 1;   transform: translateY(-2px); }
}
</style>