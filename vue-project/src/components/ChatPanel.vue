<template>
	<div class="flex flex-col h-full bg-[#0D0D12] text-[#FAF8F5]">
		<!-- Header -->
		<div class="flex items-center justify-between p-6 border-b border-[#2A2A35] hidden">
			<div class="flex items-center gap-3">
				<span class="text-sm font-sans font-semibold text-[#FAF8F5]">AI Chat</span>
				<span class="text-[10px] px-3 py-1 rounded-full font-mono uppercase tracking-widest"
					:class="webState?.backendAvailable ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-[#2A2A35]/50 text-[#FAF8F5]/60 border border-[#2A2A35]'">
					{{ webState?.backendAvailable ? 'Ready' : 'Offline' }}
				</span>
			</div>
			<div class="flex items-center gap-2">
				<button @click="clearChat"
					class="magnetic-button text-[#FAF8F5]/60 hover:text-[#FAF8F5] p-2 rounded-full transition-colors"
					title="Clear chat">
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
							d="M19 7l-.867 12.142A2 2 0 0 1 16.138 21H7.862a2 2 0 0 1-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v3M4 7h16" />
					</svg>
				</button>
			</div>
		</div>



		<!-- Messages -->
		<div ref="scrollArea" class="flex-1 min-h-0 overflow-y-auto px-6 py-4 space-y-4">



			<div v-for="(m, idx) in history" :key="m.id" class="flex items-start gap-3"
				:class="m.role === 'user' ? 'justify-end' : 'justify-start'">
				<!-- Assistant bubble -->
				<div v-if="m.role !== 'user'" class="flex items-start gap-3 max-w-[85%]">
					<div
						class="w-8 h-8 rounded-full bg-[#2A2A35] border border-[#C9A84C]/30 flex items-center justify-center text-xs font-serif font-bold italic text-[#C9A84C] shadow-[0_0_10px_rgba(201,168,76,0.1)] flex-shrink-0 mt-1">
						A</div>
					<!-- Text response -->
					<div v-if="(!m.type || m.type === 'text') && (m.text != '' || m.thinking)"
						class="bg-[#1A1A24] border border-[#2A2A35] rounded-2xl rounded-tl-sm px-5 py-4 text-sm leading-relaxed text-[#FAF8F5]/90 shadow-sm relative overflow-hidden group">
						<div class="absolute inset-0 bg-noise opacity-5 pointer-events-none"></div>
						<!-- Expandable thinking (modern AI-app style) -->
						<div v-if="m.thinking" class="mb-3">
							<button @click="toggleThinking(m)"
								class="w-full flex items-center justify-between text-[11px] font-mono tracking-widest uppercase text-[#FAF8F5]/40 hover:text-[#C9A84C] transition-colors"
								type="button">
								<span class="truncate">Thinking Process</span>
								<span class="text-xs transition-transform duration-300"
									:class="m.showThinking ? 'rotate-180 text-[#C9A84C]' : ''">▾</span>
							</button>
							<div v-if="m.showThinking"
								class="mt-2 text-[12px] font-mono text-[#FAF8F5]/50 whitespace-pre-wrap leading-relaxed border-l-2 border-[#2A2A35] pl-3 py-1">
								{{ m.thinking }}
							</div>
						</div>
						<div v-if="m.text" class="whitespace-pre-wrap font-sans relative z-10">
							{{ m.text }}
						</div>
					</div>
					<!-- Image response -->
					<div v-else-if="m.type === 'image'"
						class="bg-[#1A1A24] border border-[#2A2A35] rounded-[2rem] p-2 shadow-lg">
						<img :src="displaySrc(m.url)" alt="tool image" class="max-w-[480px] rounded-[1.5rem]" />
					</div>
					<!-- Search results -->
					<div v-else-if="m.type === 'search'"
						class="bg-[#1A1A24] border border-[#2A2A35] rounded-[2rem] p-5 w-full shadow-lg">
						<div class="flex flex-col md:flex-row gap-5">
							<div class="md:w-1/3">
								<div class="text-[10px] font-mono text-[#FAF8F5]/40 uppercase tracking-widest mb-2">
									Search Query</div>
								<div class="text-sm font-serif italic text-[#C9A84C] break-words">{{ m.query }}</div>
							</div>
							<div class="md:w-2/3">
								<div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
									<div v-for="it in (m.items || [])" :key="it.id"
										class="rounded-xl overflow-hidden border border-[#2A2A35]">
										<img :src="displaySrc(it.url)"
											class="w-full h-28 object-cover cursor-pointer hover:scale-105 transition-transform duration-500"
											:alt="it.prompt || ('image ' + it.id)" />
									</div>
								</div>
							</div>
						</div>
					</div>
					<!-- Status bubble -->
					<div v-else-if="m.type === 'status'"
						class="bg-[#0D0D12] border border-[#2A2A35] rounded-full px-4 py-2 text-xs font-mono text-[#FAF8F5]/60 shadow-inner">
						{{ m.text }}
					</div>
					<!-- Prompt bubble -->
					<div v-else-if="m.type === 'prompt'"
						class="bg-[#1A1A24] border border-[#2A2A35] rounded-2xl p-4 text-sm leading-relaxed whitespace-pre-wrap shadow-sm">
						<div class="flex items-start gap-4">
							<div class="flex-1">
								<div class="text-[10px] font-mono text-[#FAF8F5]/40 uppercase tracking-widest mb-2">
									Generated Prompt</div>
								<div class="break-words font-serif text-[#FAF8F5]/90">{{ m.prompt }}</div>
							</div>
							<button @click="copyPrompt(m.prompt)"
								class="magnetic-button text-[10px] font-mono uppercase tracking-widest px-3 py-1.5 rounded-lg border border-[#2A2A35] hover:border-[#C9A84C] hover:text-[#C9A84C] text-[#FAF8F5]/60 transition-colors">Copy</button>
						</div>
					</div>
					<!-- CivitAI images bubble -->
					<div v-else-if="m.type === 'civitai_images'"
						class="bg-[#1A1A24] border border-[#2A2A35] rounded-[2rem] p-5 w-full shadow-lg">
						<div class="flex items-center justify-between gap-3 mb-4">
							<div class="text-[10px] font-mono text-[#FAF8F5]/40 uppercase tracking-widest">CivitAI
								Images</div>
							<div class="text-[10px] font-mono text-[#FAF8F5]/40 uppercase tracking-widest"
								v-if="m.filters">
								<span v-if="m.filters.sort">Sort: <span class="text-[#C9A84C]">{{ m.filters.sort
								}}</span></span>
								<span v-if="m.filters.period" class="ml-3">Period: <span class="text-[#C9A84C]">{{
									m.filters.period }}</span></span>
							</div>
						</div>
						<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
							<div v-for="it in (m.items || [])" :key="it.id"
								class="bg-[#0D0D12] border border-[#2A2A35] rounded-xl overflow-hidden group hover:border-[#C9A84C]/40 transition-colors">
								<div class="aspect-[4/5] bg-[#1A1A24] overflow-hidden">
									<img :src="displaySrc(it.url)"
										class="object-cover w-full h-full group-hover:scale-105 transition-transform duration-500"
										:alt="it.prompt || ('image ' + it.id)" />
								</div>
								<div class="p-3">
									<div class="text-[10px] font-mono text-[#FAF8F5]/40 uppercase tracking-widest mb-1">
										Prompt</div>
									<div class="text-[12px] text-[#FAF8F5]/80 line-clamp-3">{{ it.prompt || 'Prompt unavailable' }}</div>
									<div
										class="mt-2 flex flex-wrap gap-2 text-[10px] font-mono text-[#FAF8F5]/40 uppercase tracking-widest">
										<span>Heart {{ formatCount(it.stats?.heartCount) }}</span>
										<span>Like {{ formatCount(it.stats?.likeCount) }}</span>
										<span>Comment {{ formatCount(it.stats?.commentCount) }}</span>
										<span>Laugh {{ formatCount(it.stats?.laughCount) }}</span>
										<span>Cry {{ formatCount(it.stats?.cryCount) }}</span>
									</div>
								</div>
							</div>
						</div>
					</div>
					<!-- CivitAI results bubble -->
					<div v-else-if="m.type === 'civitai'"
						class="bg-[#1A1A24] border border-[#2A2A35] rounded-[2rem] p-5 w-full shadow-lg">
						<div class="text-[10px] font-mono text-[#FAF8F5]/40 uppercase tracking-widest mb-4">CivitAI
							Search: <span class="text-[#C9A84C]">{{ m.query }}</span></div>
						<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
							<div v-for="model in m.items" :key="model.id"
								class="bg-[#0D0D12] border border-[#2A2A35] rounded-xl p-3 flex flex-col group hover:border-[#C9A84C]/50 transition-colors">
								<div v-if="model.cover_image_url"
									class="aspect-video bg-[#1A1A24] flex items-center justify-center overflow-hidden rounded-lg mb-3">
									<img :src="model.cover_image_url"
										class="object-cover w-full h-full group-hover:scale-105 transition-transform duration-500"
										:alt="model.name" />
								</div>
								<div class="font-sans font-semibold text-sm mb-1 text-[#FAF8F5] truncate"
									:title="model.name">{{ model.name }}</div>
								<div class="text-[11px] font-sans text-[#FAF8F5]/50 line-clamp-2 mb-3 mt-1"
									:title="model.description">{{ model.description }}</div>
								<a :href="model.url" target="_blank"
									class="mt-auto text-[10px] font-mono uppercase tracking-widest text-[#C9A84C] hover:text-[#FAF8F5] transition-colors">Open
									Model ↗</a>
							</div>
						</div>
					</div>
				</div>

				<!-- User bubble -->
				<div v-else class="flex items-start gap-3 max-w-[85%]">
					<div
						class="bg-[#2A2A35] border border-[#2A2A35] text-[#FAF8F5] rounded-2xl rounded-tr-sm px-5 py-3 text-sm leading-relaxed whitespace-pre-wrap shadow-sm font-sans mt-1">
						{{ m.text }}
					</div>
					<div
						class="w-8 h-8 rounded-full bg-[#C9A84C] flex items-center justify-center text-xs font-serif font-bold italic text-[#0D0D12] flex-shrink-0 mt-1">
						U</div>
				</div>
			</div>

			<!-- Typing indicator -->
			<div v-if="isResponding" class="flex items-start gap-3 mb-2">
				<div
					class="w-8 h-8 rounded-full bg-[#2A2A35] border border-[#C9A84C]/30 flex items-center justify-center text-xs font-serif font-bold italic text-[#C9A84C] shadow-[0_0_10px_rgba(201,168,76,0.1)] flex-shrink-0 animate-pulse">
					A</div>
				<div class="bg-[#1A1A24] border border-[#2A2A35] rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
					<span class="typing">
						<span class="dot bg-[#C9A84C]"></span>
						<span class="dot bg-[#C9A84C]"></span>
						<span class="dot bg-[#C9A84C]"></span>
					</span>
				</div>
			</div>
		</div>

		<!-- Composer -->
		<div class="border-t border-[#2A2A35] p-5 bg-[#0D0D12]">
			<div
				class="bg-[#1A1A24] border border-[#2A2A35] rounded-3xl p-3 shadow-inner focus-within:border-[#C9A84C]/50 transition-colors">
				<textarea ref="composer" v-model="draft"
					:placeholder="isResponding ? 'AiriX is computing...' : 'Initialize prompt sequence (Enter to send, Shift+Enter for newline)'"
					class="w-full bg-transparent text-sm text-[#FAF8F5] font-sans resize-none focus:outline-none placeholder-[#FAF8F5]/30 px-2 py-1"
					rows="1" :disabled="isResponding" @keydown.enter.exact.prevent="trySend()"
					@keydown.enter.shift.exact.stop @input="autoResize" />
				<div class="flex items-center justify-between mt-3 px-1">
					<div class="flex items-center gap-2 hidde">
						<button @click="insertAtCursor('{lora:example:1.0}')"
							class="text-[10px] uppercase font-mono tracking-widest px-3 py-1.5 rounded-lg border border-[#2A2A35] text-[#FAF8F5]/50 hover:text-[#C9A84C] hover:border-[#C9A84C] transition-colors"
							title="Insert LoRA tag">
							LoRA
						</button>
					</div>
					<div class="flex items-center gap-2">
						<button v-if="isResponding" @click="stopResponse"
							class="magnetic-button bg-[#2A2A35] hover:bg-[#1A1A24] border border-[#2A2A35] hover:border-red-500/50 text-[#FAF8F5] px-5 py-2 rounded-full text-sm font-semibold transition-colors">
							<span class="relative z-10">Halt</span>
						</button>
						<button v-else @click="trySend()"
							class="magnetic-button bg-[#C9A84C] hover:bg-[#B89A45] text-[#0D0D12] px-6 py-2 rounded-full text-sm font-semibold transition-colors"
							:disabled="!draft.trim()"
							:class="!draft.trim() ? 'opacity-50 cursor-not-allowed contrast-75' : 'shadow-[0_0_15px_rgba(201,168,76,0.2)]'">
							<span class="relative z-10">Transmit</span>
						</button>
					</div>
				</div>
			</div>
			<!-- Footer controls -->
			<div class="flex items-center justify-between mt-4 px-2">
				<div class="text-[10px] font-mono text-[#FAF8F5]/30 flex items-center gap-2 uppercase tracking-widest">
					<span class="w-1.5 h-1.5 rounded-full bg-[#C9A84C] animate-pulse"></span>
					AiriX Intelligence
				</div>
				<div class="flex items-center gap-3">
					<button @click="regenerateLast"
						class="text-[10px] font-mono uppercase tracking-widest px-3 py-1.5 rounded-lg text-[#FAF8F5]/50 hover:text-[#C9A84C] transition-colors">
						Regenerate
					</button>
					<button @click="clearChat"
						class="text-[10px] font-mono uppercase tracking-widest px-3 py-1.5 rounded-lg text-[#FAF8F5]/50 hover:text-red-400 transition-colors">
						Purge
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { wsUrl, webState, apiUrl, formatRequest } from '@/api'


//props
const props = defineProps({
	history: {
		type: Array,
		default: () => []
	}
})


const suggestions = [
	'Improve my prompt',
	'Suggest negative prompt',
	'Which sampler for portraits?',
	'Lower CFG but keep detail',
	'Add a background scene'
]

const draft = ref('')
const isResponding = ref(false)
const socket = ref(null)
let reconnectTimer = null
const sessionId = ref(localStorage.getItem('assistant_session_id') || generateSessionId())
localStorage.setItem('assistant_session_id', sessionId.value)
const scrollArea = ref(null)
const composer = ref(null)
let respondTimer = null

function toggleThinking(m) {
	// Make it reactive even if older messages don't have the flag
	m.showThinking = !m.showThinking
}

function displaySrc(u) {
	if (!u) return ''
	if (u.startsWith('data:image')) return u
	// server-relative -> absolute
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
	nextTick(() => {
		if (scrollArea.value) {
			scrollArea.value.scrollTop = scrollArea.value.scrollHeight
		}
	})
}

function autoResize() {
	if (!composer.value) return
	composer.value.style.height = 'auto'
	composer.value.style.height = `${composer.value.scrollHeight}px`
	scrollToBottom()
}

function useSuggestion(s) {
	draft.value = s
	nextTick(autoResize)
}

function insertAtCursor(text) {
	const el = composer.value
	if (!el) {
		draft.value += text
		return
	}
	const start = el.selectionStart || draft.value.length
	const end = el.selectionEnd || draft.value.length
	draft.value = draft.value.slice(0, start) + text + draft.value.slice(end)
	nextTick(() => {
		el.selectionStart = el.selectionEnd = start + text.length
		autoResize()
	})
}

function trySend() {
	if (!draft.value.trim() || isResponding.value) return
	const userText = draft.value.trim()
	props.history.push({ id: Date.now(), role: 'user', text: userText })
	draft.value = ''
	autoResize()
	scrollToBottom()
	ensureSocket()
	// Create assistant placeholder for streaming content
	props.history.push({ id: Date.now() + 1, role: 'assistant', text: '', thinking: '', showThinking: false })
	isResponding.value = true
	// Send to backend
	try {
		socket.value?.send(JSON.stringify({ type: 'user', content: userText }))
	} catch (e) { }
}

function stopResponse() {
	// Best-effort: notify server; if unsupported, no harm done
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
	// Find last user message
	const lastUser = [...props.history].reverse().find(m => m.role === 'user')
	if (!lastUser) return
	// Re-send last user message as new turn
	props.history.push({ id: Date.now(), role: 'user', text: lastUser.text })
	props.history.push({ id: Date.now() + 1, role: 'assistant', text: '', thinking: '', showThinking: false })
	isResponding.value = true
	ensureSocket()
	try { socket.value?.send(JSON.stringify({ type: 'user', content: lastUser.text })) } catch { }
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
		// Initialize/load session history
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
							role: m.role === 'user' ? 'user' : 'assistant',
							text: m.content,
							thinking: '',
							showThinking: false,
						})
					}
					scrollToBottom()
				}
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
				if (msg.tool === 'search_images') {
					props.history.push({ id: Date.now(), role: 'assistant', type: 'search', query: msg?.args?.query || '', items: Array.isArray(msg.result) ? msg.result : [] })
					scrollToBottom()
				} else if (msg.tool === 'show_image') {
					const url = msg?.result?.url || ''
					props.history.push({ id: Date.now(), role: 'assistant', type: 'image', url })
					scrollToBottom()
				} else if (msg.tool === 'generate_new_image') {
					const prompt = msg?.result?.prompt || ''
					props.history.push({ id: Date.now(), role: 'assistant', type: 'status', text: `Generating image for: ${prompt}` })
					startGeneration(prompt)
				} else if (msg.tool === 'show_prompt') {
					const prompt = msg?.result?.prompt || ''
					props.history.push({ id: Date.now(), role: 'assistant', type: 'prompt', prompt })
					scrollToBottom()
				} else if (msg.tool === 'search_civitai_models') {
					props.history.push({ id: Date.now(), role: 'assistant', type: 'civitai', query: msg?.args?.query || '', items: Array.isArray(msg.result) ? msg.result : [] })
					scrollToBottom()
				} else if (msg.tool === 'get_civitai_images') {
					const payload = msg.result || {}
					props.history.push({
						id: Date.now(),
						role: 'assistant',
						type: 'civitai_images',
						items: Array.isArray(payload.items) ? payload.items : [],
						metadata: payload.metadata || {},
						filters: payload.filters || {},
					})
					scrollToBottom()
				} else {
					const pretty = typeof msg.result === 'string' ? msg.result : JSON.stringify(msg.result, null, 2)
					props.history.push({ id: Date.now(), role: 'assistant', text: `Tool ${msg.tool}:\n${pretty}` })
					scrollToBottom()
				}
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
		} catch (e) { /* ignore */ }
	}

	ws.onerror = () => { }
	ws.onclose = () => {
		if (reconnectTimer) return
		reconnectTimer = setTimeout(() => {
			reconnectTimer = null
			connectSocket()
		}, 1000)
	}
}

onMounted(() => {
	connectSocket()
	nextTick(() => {
		autoResize()
		scrollToBottom()
	})
})

onBeforeUnmount(() => {
	try { socket.value?.close() } catch { }
	if (reconnectTimer) clearTimeout(reconnectTimer)
})

async function startGeneration(prompt) {
	try {
		const payload = formatRequest(prompt)
		const resp = await fetch('http://127.0.0.1:8000/sdapi/v1/txt2img', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(payload),
		})
		const data = await resp.json()
		if (data?.images?.length) {
			const src = `data:image/png;base64,${data.images[0]}`
			props.history.push({ id: Date.now(), role: 'assistant', type: 'image', url: src })
		} else {
			props.history.push({ id: Date.now(), role: 'assistant', text: 'Generation finished but no images returned.' })
		}
	} catch (e) {
		props.history.push({ id: Date.now(), role: 'assistant', text: `Generation failed: ${e}` })
	} finally {
		scrollToBottom()
	}
}

function generateSessionId() {
	return 'sess_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8)
}

function copyPrompt(p) {
	try { navigator.clipboard.writeText(p) } catch { }
}
</script>

<style scoped>
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

.dot:nth-child(2) {
	animation-delay: 0.2s;
}

.dot:nth-child(3) {
	animation-delay: 0.4s;
}

@keyframes blink {

	0%,
	80%,
	100% {
		opacity: 0.2;
		transform: translateY(0px);
	}

	40% {
		opacity: 1;
		transform: translateY(-2px);
	}
}
</style>