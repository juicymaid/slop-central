<template>
	<div class="min-h-screen bg-gray-950 text-gray-100">
		<div class="mx-auto max-w-5xl px-4 py-8">
			<div class="mb-6 flex items-center justify-between">
				<h1 class="text-2xl font-semibold">Edit Comic</h1>
				<div class="flex gap-2">
					<button
						class="inline-flex items-center rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-500"
						@click="$router.push(`/comics/${$route.params.id}/read`)"
					>
						<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
						</svg>
						Preview
					</button>
					<button
						class="inline-flex items-center rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500"
						@click="addPanel"
					>
						+ Add Panel
					</button>
					<button
						class="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
						@click="save"
					>
						Save
					</button>
				</div>
			</div>

			<div v-if="loading" class="flex items-center justify-center py-24 text-gray-400">
				<div class="inline-flex items-center gap-3">
					<svg class="h-5 w-5 animate-spin text-gray-400" viewBox="0 0 24 24" fill="none">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
						<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
					</svg>
					<span>Loading comic…</span>
				</div>
			</div>

			<div v-else class="space-y-6">
				<!-- Meta -->
				<div class="rounded-lg border border-gray-800 bg-gray-900/60 p-5">
					<div class="grid gap-4 md:grid-cols-2">
						<div class="flex flex-col">
							<label class="mb-1 text-sm text-gray-300">Title</label>
							<input
								v-model="currentComic.title"
								type="text"
								placeholder="Enter comic title"
								class="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-gray-100 placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
							/>
						</div>
						<div class="flex flex-col md:col-span-1">
							<label class="mb-1 text-sm text-gray-300">Topic</label>
							<input
								v-model="currentComic.topic"
								type="text"
								placeholder="Describe the topic"
								class="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-gray-100 placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
							/>
						</div>
					</div>
				</div>

				<!-- Panels -->
				<div class="space-y-5">
					<div
						v-for="(panel, pIdx) in currentComic.panels"
						:key="pIdx"
						class="rounded-lg border border-gray-800 bg-gray-900/60 p-5"
					>
						<div class="mb-4 flex items-center justify-between">
							<h2 class="text-lg font-medium">Panel {{ pIdx + 1 }}</h2>
							<div class="flex items-center gap-2">
								<button
									class="rounded-md border border-gray-700 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-800"
									@click="duplicatePanel(pIdx)"
								>
									Duplicate
								</button>
								<button
									class="rounded-md bg-rose-600 px-3 py-1.5 text-xs text-white hover:bg-rose-500"
									@click="removePanel(pIdx)"
								>
									Remove
								</button>
							</div>
						</div>

                        <div class="grid gap-4 md:grid-cols-2">
                            <div class="flex flex-col md:col-span-1">
                                <label class="mb-1 text-sm text-gray-300">Image Prompt</label>
                                <textarea
                                    v-model="panel.prompt"
                                    rows="3"
                                    placeholder="e.g., 1girl, name, tags..."
                                    class="mb-3 w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-gray-100 placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
                                ></textarea>
                                <div class="mb-3 flex items-center gap-2">
                                    <button
                                        class="inline-flex items-center rounded-md bg-sky-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-sky-500 disabled:cursor-not-allowed disabled:opacity-50"
                                        :disabled="!panel.prompt || panel.generating"
                                        @click="generateImage(pIdx)"
                                    >
                                        <svg v-if="panel.generating" class="mr-2 h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                                        </svg>
                                        <span>{{ panel.generating ? 'Generating…' : 'Generate Image' }}</span>
                                    </button>
                                </div>

								<!-- Image preview with draggable text overlays -->
								<div
									:ref="el => (panelContainers[pIdx] = el)"
									class="relative w-full rounded-md border border-gray-800 bg-gray-800"
								>
									<!-- Live preview during generation -->
									<template v-if="panel.generating && panel.preview">
										<img
											:src="panel.preview"
											alt="Generating preview"
											class="w-full h-auto object-contain"
											draggable="false"
										/>
										<div class="absolute bottom-2 right-2 rounded bg-black/60 px-2 py-1 text-xs text-white">
											{{ Math.round((panel.progress ?? 0) * 100) }}%
										</div>
									</template>
									<template v-else-if="panel.image">
										<img
											:src="panel.image"
											alt="Panel image"
											class="w-full h-auto object-contain"
											draggable="false"
										/>
									</template>
									<template v-else>
										<div class="flex min-h-48 w-full items-center justify-center text-sm text-gray-500">
											No image. 
										</div>
									</template>

									<!-- Draggable comic-style text overlays -->
									<div
										v-for="(txt, tIdx) in panel.texts"
										:key="'overlay-'+tIdx"
										:class="[
											'absolute cursor-move select-none font-comic',
											txt.style === 'speech' ? 'bubble-speech rounded-2xl border-2 border-black bg-white/95 px-3 py-2 text-black shadow-lg' :
											txt.style === 'label'  ? 'bubble-label rounded-full border-2 border-white bg-transparent px-3 py-1 text-white' :
											txt.style === 'box'    ? 'bubble-box rounded-sm border-2 border-black bg-white px-3 py-2 text-black shadow' :
											'bubble-outline text-white'
										]"
										:style="{
											left: (txt.x ?? 10) + '%',
											top: (txt.y ?? 10) + '%',
											fontSize: ((txt.size ?? 18)) + 'px'
										}"
										@pointerdown.stop="startDrag(pIdx, tIdx, $event)"
									>
										{{ txt.value || 'Text' }}
									</div>
								</div>
							</div>

							<div class="flex flex-col md:col-span-1">
								<div class="mb-1 flex items-center justify-between">
									<label class="text-sm text-gray-300">Texts</label>
									<button
										class="rounded-md border border-gray-700 px-2 py-1 text-xs text-gray-300 hover:bg-gray-800"
										@click="addText(pIdx)"
									>
										+ Add Text
									</button>
								</div>

								<div class="space-y-3">
									<div
										v-for="(txt, tIdx) in panel.texts"
										:key="tIdx"
										class="rounded-md border border-gray-800 bg-gray-900/60 p-3"
									>
										<div class="flex items-start gap-2">
											<input
												v-model="panel.texts[tIdx].value"
												type="text"
												placeholder="Speech bubble or caption"
												class="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-gray-100 placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
											/>
											<button
												class="mt-1 rounded-md bg-rose-600 px-2 py-1 text-xs text-white hover:bg-rose-500"
												@click="removeText(pIdx, tIdx)"
												title="Remove text"
											>
												✕
											</button>
										</div>
										<div class="mt-2 grid grid-cols-3 gap-2 text-xs text-gray-300">
											<div class="flex items-center gap-2">
												<span class="w-5">X</span>
												<input
													type="number"
													min="0"
													max="100"
													:step="1"
													v-model.number="panel.texts[tIdx].x"
													class="w-full rounded-md border border-gray-700 bg-gray-800 px-2 py-1 text-gray-100 focus:border-indigo-500 focus:outline-none"
												/>
												<span>%</span>
											</div>
											<div class="flex items-center gap-2">
												<span class="w-5">Y</span>
												<input
													type="number"
													min="0"
													max="100"
													:step="1"
													v-model.number="panel.texts[tIdx].y"
													class="w-full rounded-md border border-gray-700 bg-gray-800 px-2 py-1 text-gray-100 focus:border-indigo-500 focus:outline-none"
												/>
												<span>%</span>
											</div>
											<div class="flex items-center gap-2">
												<span class="w-10">Size</span>
												<input
													type="number"
													min="10"
													max="64"
													:step="1"
													v-model.number="panel.texts[tIdx].size"
													class="w-full rounded-md border border-gray-700 bg-gray-800 px-2 py-1 text-gray-100 focus:border-indigo-500 focus:outline-none"
												/>
												<span>px</span>
											</div>
											<div class="flex items-center gap-2 col-span-3">
												<span class="w-10">Style</span>
												<select
													v-model="panel.texts[tIdx].style"
													class="w-full rounded-md border border-gray-700 bg-gray-800 px-2 py-1 text-gray-100 focus:border-indigo-500 focus:outline-none"
												>
													<option value="speech">Speech</option>
													<option value="label">Label</option>
													<option value="box">Box</option>
													<option value="outline">Outline</option>
												</select>
											</div>
											<div class="col-span-3 text-gray-500">
												Drag on the image to reposition.
											</div>
										</div>
									</div>
									<div v-if="panel.texts.length === 0" class="text-sm text-gray-500">
										No texts yet. Add one above.
									</div>
								</div>
							</div>
						</div>
					</div>

					<div class="rounded-lg border border-gray-800 bg-gray-900/60 p-5">
						<div class="mb-4">
							<h2 class="text-lg font-medium mb-3">Generate Panel</h2>
							<div class="flex flex-col gap-3">
								<textarea
									v-model="generatePanelPrompt"
									rows="3"
									placeholder="Describe the panel you want to generate..."
									class="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-gray-100 placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
								></textarea>
								<button
									class="inline-flex items-center justify-center rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-500 disabled:cursor-not-allowed disabled:opacity-50"
									:disabled="generatingPanel"
									@click="generatePanel(-1)"
								>
									<svg v-if="generatingPanel" class="mr-2 h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
										<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
										<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
									</svg>
									<span>{{ generatingPanel ? 'Generating Panel…' : 'Generate Panel' }}</span>
								</button>
							</div>
						</div>
					</div>

					<div v-if="currentComic.panels.length === 0" class="rounded-md border border-dashed border-gray-800 p-6 text-center text-gray-400">
						No panels yet. Click “Add Panel” to get started.
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { apiUrl, formatRequest, GetFromApi, PostToApi } from '@/api';
import { onMounted, ref, onBeforeUnmount } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

// initialize with safe defaults for editing
const currentComic = ref({
	title: '',
	topic: '',
	panels: []
});
const loading = ref(true);

// Refs for per-panel image containers (for dragging math)
const panelContainers = ref([]);

// Drag state
const dragging = ref(null);

onMounted(async () => {
	await fetchComic();
});

// normalize fetched data and stop loading
async function fetchComic() {
	const id = route.params.id;
	const comic = await GetFromApi(`comics/${id}`);
	currentComic.value = {
		title: comic?.title ?? '',
		topic: comic?.topic ?? '',
		panels: Array.isArray(comic?.panels)
			? comic.panels.map(p => ({
					prompt: p?.prompt ?? '',
					image: p?.image ?? '',
					texts: Array.isArray(p?.texts)
						? p.texts.map(t =>
								typeof t === 'string'
									? { value: t, x: 10, y: 10, size: 18, style: 'speech' }
									: {
											value: t?.value ?? '',
											x: Number.isFinite(t?.x) ? t.x : 10,
											y: Number.isFinite(t?.y) ? t.y : 10,
											size: Number.isFinite(t?.size) ? t.size : 18,
											style: typeof t?.style === 'string' ? t.style : 'speech'
										}
						  )
						: []
				}))
			: []
	};
	loading.value = false;
}

// panel and text editors
function addPanel() {
	currentComic.value.panels.push({
		prompt: '',
		image: '',
		texts: [{ value: '', x: 10, y: 10, size: 18, style: 'speech' }],
		preview: '',
		progress: 0,
		generating: false
	});
}
function duplicatePanel(index) {
	const src = currentComic.value.panels[index];
	currentComic.value.panels.splice(index + 1, 0, {
		prompt: src.prompt,
		image: src.image,
		texts: src.texts.map(t => ({ value: t.value, x: t.x, y: t.y, size: t.size ?? 18, style: t.style ?? 'speech' })),
		preview: '',
		progress: 0,
		generating: false
	});
}
function removePanel(index) {
	currentComic.value.panels.splice(index, 1);
}
function addText(panelIndex) {
	currentComic.value.panels[panelIndex].texts.push({ value: '', x: 10, y: 10, size: 18, style: 'speech' });
}
function removeText(panelIndex, textIndex) {
	currentComic.value.panels[panelIndex].texts.splice(textIndex, 1);
}

const previewImage = ref(null);

function dataURLtoFile(dataurl, filename) {
    var arr = dataurl.split(','),
        mime = arr[0].match(/:(.*?);/)[1],
        bstr = atob(arr[arr.length - 1]), 
        n = bstr.length, 
        u8arr = new Uint8Array(n);
    while(n--){
        u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, {type:mime});
}

const url = ref('http://127.0.0.1:7860/')
// Helper to build absolute URL from API base + relative path
function toAbsoluteImageUrl(path) {
	if (!path) return '';
	if (/^https?:\/\//i.test(path)) return path;
	return apiUrl.replace(/\/$/, '') + '/' + String(path).replace(/^\//, '');
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function generateImage(panelIndex) {
	const panel = currentComic.value.panels[panelIndex];
	panel.generating = true;
	panel.progress = 0;
	panel.preview = '';

	try {
		const prompt = panel.prompt;
		const _request = formatRequest(prompt);
        console.log(_request);

		// Start generation (do not await yet)
		const genPromise = fetch(url.value + 'sdapi/v1/txt2img', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(_request)
		}).then(async res => {
			if (!res.ok) throw new Error('txt2img failed');
			return res.json();
		});

		// Start polling progress with preview image
		const poll = (async () => {
			while (panel.generating) {
				try {
					const progRes = await fetch(url.value + 'sdapi/v1/progress?skip_current_image=false', { method: 'GET' });
					if (progRes.ok) {
						const data = await progRes.json();
						panel.progress = typeof data?.progress === 'number' ? data.progress : 0;
						if (data?.current_image) {
							panel.preview = 'data:image/png;base64,' + data.current_image;
						}
					}
				} catch (_) {
					/* ignore polling errors */
				}
				await sleep(500);
			}
		})();

		// Wait for generation, then upload to backend
		const result = await genPromise;
		const imageB64 = 'image/png;base64,' + result.images[0];
		const file = dataURLtoFile('data:' + imageB64, panelIndex + '.png');

		const formData = new FormData();
		formData.append('file', file);

		const uploadRes = await fetch(apiUrl + '/comics/' + route.params.id + '/panels/' + panelIndex + '/image', {
			method: 'POST',
			body: formData
		});
		const uploadJson = await uploadRes.json();
		if (!uploadRes.ok) throw new Error(uploadJson?.detail || 'Upload failed');

        panel.image = ''; // clear old image to force refresh

		panel.image = toAbsoluteImageUrl(uploadJson.image_url);
	} catch (e) {
		console.error(e);
	} finally {
		panel.generating = false; // stops polling loop
		panel.progress = 0;
		panel.preview = '';
	}
	save();
}
const generatePanelPrompt = ref('');
const generatingPanel = ref(false);

async function generatePanel(panelIndex) {

	generatingPanel.value = true;

	const instructions = generatePanelPrompt.value.trim();
	
	let endpoint = `comics/${route.params.id}/generate-panel/${panelIndex}?instructions=` + encodeURIComponent(instructions);
	const response = await GetFromApi(endpoint);

	generatingPanel.value = false;

	fetchComic();
}

// placeholder save: wire to your API as needed
function save() {
	// e.g., await PutToApi(`comics/${route.params.id}`, currentComic.value)
	console.log('Saving comic:', (JSON.stringify(currentComic.value)));
    PostToApi("comics/"+route.params.id, (currentComic.value));
}

// Drag handlers
function startDrag(pIdx, tIdx, e) {
	const el = panelContainers.value[pIdx];
	const target = e.currentTarget;
	if (!el || !target) return;
	
	const rect = el.getBoundingClientRect();
	const bubbleRect = target.getBoundingClientRect();
	
	// Calculate offset from pointer to element's top-left corner
	const offsetX = e.clientX - bubbleRect.left;
	const offsetY = e.clientY - bubbleRect.top;
	
	dragging.value = { 
		pIdx, 
		tIdx, 
		rect, 
		bubbleWidth: bubbleRect.width,
		bubbleHeight: bubbleRect.height,
		offsetX,
		offsetY
	};
	
	window.addEventListener('pointermove', onDragMove);
	window.addEventListener('pointerup', stopDrag);
}

function onDragMove(e) {
	if (!dragging.value) return;
	const { pIdx, tIdx, rect, bubbleWidth, bubbleHeight, offsetX, offsetY } = dragging.value;
	
	// Calculate position accounting for the initial pointer offset
	const pixelX = e.clientX - rect.left - offsetX;
	const pixelY = e.clientY - rect.top - offsetY;
	
	// Convert to percentage
	const percentX = (pixelX / rect.width) * 100;
	const percentY = (pixelY / rect.height) * 100;
	
	// Calculate max boundaries based on bubble size
	const maxX = 100 - (bubbleWidth / rect.width) * 100;
	const maxY = 100 - (bubbleHeight / rect.height) * 100;
	
	// Clamp values
	const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
	
	const panel = currentComic.value.panels[pIdx];
	const t = panel.texts[tIdx];
	t.x = Math.round(clamp(percentX, 0, maxX) * 10) / 10; // Round to 1 decimal
	t.y = Math.round(clamp(percentY, 0, maxY) * 10) / 10;
}

function stopDrag() {
	window.removeEventListener('pointermove', onDragMove);
	window.removeEventListener('pointerup', stopDrag);
	dragging.value = null;
}

onBeforeUnmount(() => {
	stopDrag();
});
</script>

<style scoped>
/* filepath: H:/ent/ai/NewFolder/vue-project/src/views/comicPage.vue */
/* Comic-y font stack */
.font-comic {
  font-family: "Bangers", "Comic Sans MS", "Comic Neue", Impact, system-ui, sans-serif;
  letter-spacing: 0.3px;
}

/* Variants */
.bubble-speech {
  position: absolute;
  box-shadow: 0 4px 10px rgba(0,0,0,0.35);
}
.bubble-speech::after {
  content: "";
  position: absolute;
  bottom: -8px;
  right: 16px;
  width: 0;
  height: 0;
  border-width: 8px 8px 0 8px;
  border-style: solid;
  border-color: #000000 transparent transparent transparent; /* tail border */
}
.bubble-speech::before {
  content: "";
  position: absolute;
  bottom: -6px;
  right: 16px;
  width: 0;
  height: 0;
  border-width: 6px 6px 0 6px;
  border-style: solid;
  border-color: rgba(255,255,255,0.95) transparent transparent transparent; /* tail fill */
}

.bubble-label {
  backdrop-filter: blur(0px);
}

.bubble-box {
  /* simple box; tailless */
}

.bubble-outline {
  /* outline text: simulate stroke via shadows */
  text-shadow:
    -1px -1px 0 #000,
     1px -1px 0 #000,
    -1px  1px 0 #000,
     1px  1px 0 #000,
     0   -1.5px 0 #000,
     0    1.5px 0 #000,
    -1.5px 0    0 #000,
     1.5px 0    0 #000;
}
</style>