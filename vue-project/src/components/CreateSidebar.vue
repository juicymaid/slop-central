<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { onUiUpdate } from '@/scripts/autoComplete'

import { useTextareaAutosize } from '@vueuse/core'
import { api as viewerApi } from 'v-viewer'
import {
    backendState,
    buildBackendRequest,
    getActiveBackend,
    getBackendBaseUrl,
    getBackendConfigStatus,
    loadBackendSettings
} from '@/backends'
import { loadFromFile, saveToFile } from '@/storage'

const chatHistory = ref([])


const textarea = useTextareaAutosize()

const workflow = ref('Text-to-image')
const model = ref('PerfectDeliberate')
const aspectRatio = ref('Portrait')
const draftMode = ref(false)
const showAdvanced = ref(true)
const activeTab = ref('generate')
const isResizing = ref(false)
const isFullscreen = ref(false)
const isCanvas = ref(false)
const showDefaultStyles = ref(false)
const compactMode = ref(false)
const styles = ref([])
const selectedStyleIds = ref([])
const showStyleManager = ref(false)
const isEditingStyle = ref(false)
const styleForm = reactive({
    id: null,
    name: '',
    tags: '',
    image: ''
})
const imageInput = reactive({
    preview: '',
    base64: '',
    name: '',
    size: 0,
    width: 0,
    height: 0
})
const imageInputRef = ref(null)
const showImageDropOverlay = ref(false)
const img2imgDenoise = ref(0.75)

const selectedStyles = computed(() => {
    const selected = new Set(selectedStyleIds.value)
    return styles.value.filter((style) => selected.has(style.id))
})
const selectedStyleTags = computed(() => {
    const tags = []
    selectedStyles.value.forEach((style) => {
        tags.push(...splitTags(style.tags))
    })
    return tags.join(', ')
})

const createStyleId = () => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID()
    }
    return `style_${Date.now()}_${Math.floor(Math.random() * 10000)}`
}

function splitTags(value) {
    if (!value) return []
    return value
        .split(',')
        .map((tag) => tag.trim())
        .filter((tag) => tag.length > 0)
}

function applyStylesToPrompt(prompt) {
    const baseTags = splitTags(prompt)
    const styleTags = selectedStyles.value.flatMap((style) => splitTags(style.tags))
    if (styleTags.length === 0) {
        return prompt
    }
    const merged = [...baseTags]
    styleTags.forEach((tag) => {
        if (!merged.includes(tag)) {
            merged.push(tag)
        }
    })
    return merged.join(', ')
}

function toggleStyleSelection(styleId) {
    if (selectedStyleIds.value.includes(styleId)) {
        selectedStyleIds.value = selectedStyleIds.value.filter((id) => id !== styleId)
    } else {
        selectedStyleIds.value = [...selectedStyleIds.value, styleId]
    }
}

function clearSelectedStyles() {
    selectedStyleIds.value = []
}

function startNewStyle() {
    isEditingStyle.value = false
    styleForm.id = null
    styleForm.name = ''
    styleForm.tags = ''
    styleForm.image = ''
}

function startEditStyle(style) {
    isEditingStyle.value = true
    styleForm.id = style.id
    styleForm.name = style.name || ''
    styleForm.tags = style.tags || ''
    styleForm.image = style.image || ''
}

function saveStyle() {
    const name = styleForm.name.trim()
    const tags = styleForm.tags.trim()
    if (!name || !tags) {
        return
    }

    const payload = {
        id: styleForm.id || createStyleId(),
        name,
        tags,
        image: styleForm.image.trim()
    }

    const existingIndex = styles.value.findIndex((style) => style.id === payload.id)
    if (existingIndex >= 0) {
        styles.value.splice(existingIndex, 1, payload)
    } else {
        styles.value.unshift(payload)
    }

    startNewStyle()
}

function removeStyle(styleId) {
    styles.value = styles.value.filter((style) => style.id !== styleId)
    selectedStyleIds.value = selectedStyleIds.value.filter((id) => id !== styleId)
}

function handleStyleImageUpload(event) {
    const file = event.target.files && event.target.files[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = () => {
        styleForm.image = typeof reader.result === 'string' ? reader.result : ''
    }
    reader.readAsDataURL(file)
    event.target.value = ''
}

function clearImageInput() {
    imageInput.preview = ''
    imageInput.base64 = ''
    imageInput.name = ''
    imageInput.size = 0
    imageInput.width = 0
    imageInput.height = 0
    if (imageInputRef.value) {
        imageInputRef.value.value = ''
    }
}

function openImageInputDialog() {
    if (imageInputRef.value) {
        imageInputRef.value.click()
    }
}

function updateImageInputDimensions(src) {
    if (!src) return
    const previewImage = new window.Image()
    previewImage.onload = () => {
        imageInput.width = previewImage.width
        imageInput.height = previewImage.height
    }
    previewImage.src = src
}

function setImageInputFromFile(file) {
    if (!file || !file.type || !file.type.startsWith('image/')) return

    const reader = new FileReader()
    reader.onload = () => {
        const dataUrl = typeof reader.result === 'string' ? reader.result : ''
        imageInput.preview = dataUrl
        imageInput.base64 = dataUrl.includes(',') ? dataUrl.split(',')[1] : ''
        imageInput.name = file.name || 'input-image'
        imageInput.size = file.size || 0
        imageInput.width = 0
        imageInput.height = 0

        updateImageInputDimensions(dataUrl)
    }
    reader.readAsDataURL(file)
}

function isHttpUrl(value) {
    return /^https?:\/\//i.test(value)
}

function getImageNameFromUrl(imageUrl) {
    try {
        const url = new URL(imageUrl)
        const name = url.pathname.split('/').filter(Boolean).pop()
        return name || 'input-image'
    } catch {
        return 'input-image'
    }
}

function getDropImageUrl(dataTransfer) {
    if (!dataTransfer) return ''

    const uriList = dataTransfer.getData('text/uri-list') || ''
    const uri = uriList
        .split('\n')
        .map((line) => line.trim())
        .find((line) => line && !line.startsWith('#'))
    if (isHttpUrl(uri)) return uri

    const text = (dataTransfer.getData('text/plain') || '').trim()
    if (isHttpUrl(text)) return text

    const html = dataTransfer.getData('text/html') || ''
    const match = html.match(/src\s*=\s*['"]([^'"]+)['"]/i)
    if (match && isHttpUrl(match[1])) return match[1]

    return ''
}

async function setImageInputFromUrl(imageUrl) {
    if (!isHttpUrl(imageUrl)) return

    if(imageUrl.includes("http://localhost:5173/image/")) {
        imageUrl = apiUrl + "/image-file/" + imageUrl.split("http://localhost:5173/image/")[1]
    }


    imageInput.preview = imageUrl
    imageInput.base64 = ''
    imageInput.name = getImageNameFromUrl(imageUrl)
    imageInput.size = 0
    imageInput.width = 0
    imageInput.height = 0

    updateImageInputDimensions(imageUrl)

    try {
        const response = await fetch(imageUrl)
        if (!response.ok) {
            throw new Error(`Failed to fetch image (${response.status})`)
        }
        const blob = await response.blob()
        if (!blob.type.startsWith('image/')) return

        const reader = new FileReader()
        reader.onload = () => {
            const dataUrl = typeof reader.result === 'string' ? reader.result : ''
            if (!dataUrl) return
            imageInput.preview = dataUrl
            imageInput.base64 = dataUrl.includes(',') ? dataUrl.split(',')[1] : ''
            imageInput.size = blob.size || 0
            updateImageInputDimensions(dataUrl)
        }
        reader.readAsDataURL(blob)
    } catch (error) {
        console.warn('Failed to load image from URL:', error)
    }
}

function handleImageInputChange(event) {
    const file = event.target.files && event.target.files[0]
    if (file) {
        setImageInputFromFile(file)
    }
    event.target.value = ''
}

async function handleImageInputDrop(event) {
    const file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0]
    if (file) {
        setImageInputFromFile(file)
        showImageDropOverlay.value = false
        return
    }

    const imageUrl = getDropImageUrl(event.dataTransfer)
    if (imageUrl) {
        await setImageInputFromUrl(imageUrl)
    }

    showImageDropOverlay.value = false
}


const samplerCost = {
    "Euler a": 0.8,
    "Euler": 0.8,
    "LMS": 0.9,
    "DDIM": 0.8,
    "DPM++ 2M": 1.2,
    "DPM++ 2M SDE": 1.2,
}

function calculateCost(request) {
    const baseCost = 1;
    const baseResolution = 512 * 512;
    const baseSamplerCost = samplerCost[request.sampler_name] || 1;
    const baseSteps = 30;

    var imageCost = baseCost * ((request.width * request.height) / baseResolution).toFixed(0) * baseSamplerCost * (request.steps / baseSteps) * request.batch_size * request.n_iter

    imageCost += calculateAdditionalCost(request)

    return Math.max(1, imageCost).toFixed(0)
}

function formatSizeMultiplier(request) {
    const baseResolution = 512 * 512;
    const mult = (request.width * request.height) / baseResolution;
    return mult.toFixed(0).replace(/\.00$/, '');
}

function calculateAdditionalCost(request) {
    const x = current_model.loras.length;
    return request.batch_size * request.n_iter * (0.5636713 - 0.01146222 * x + 0.07849689 * x * x).toFixed(0)
}

function formatStepsPercentage(request) {
    const baseSteps = 30;
    const pct = ((request.steps / baseSteps) - 1) * 100;
    return (pct > 0 ? '+' : '') + pct.toFixed(0) + '%';
}

function formatSamplerPercentage(request) {
    const baseSamplerCost = samplerCost[request.sampler_name] || 1;
    const pct = (baseSamplerCost - 1) * 100;
    return (pct > 0 ? '+' : '') + pct.toFixed(0) + '%';
}

const isDataUrl = (value) => typeof value === 'string' && value.startsWith('data:image/')

const resolveImageSrc = (image) => {
    if (!image) return ''
    if (isDataUrl(image)) return image
    return `data:image/png;base64,${image}`
}

const getImageExtension = (image) => {
    if (!image) return 'png'
    if (isDataUrl(image)) {
        const mime = image.slice('data:image/'.length).split(';')[0]
        return mime.split('/')[1] || mime || 'png'
    }
    return 'png'
}

const normalizeAiHordeImage = (image) => {
    if (!image) return ''
    if (isDataUrl(image)) return image
    return `data:image/webp;base64,${image}`
}

function showFullscreen(images) {
    console.log("Showing fullscreen for images:", images)
    viewerApi({
        images: (images || []).map(resolveImageSrc),
        options: { "inline": true, "button": true, "navbar": false, "title": false, "toolbar": false, "tooltip": false, "movable": true, "zoomable": true, "rotatable": true, "scalable": true, "transition": true, "fullscreen": true, "keyboard": true, }
    });
}

function showModelStyles() {
    if (!current_model.model || !current_model.model.model_name) {
        console.warn('Model or model_name is undefined.');
        return;
    }
    if (defaultStyles.value[current_model.model.model_name] == null) {
        defaultStyles.value[current_model.model.model_name] = {
            prompt_prefix: "",
            negative_prompt_prefix: ""
        }
    }
    showDefaultStyles.value = !showDefaultStyles.value
}
function getDefaultStyles() {
    if (defaultStyles.value[current_model.model.model_name]) {
        return defaultStyles.value[current_model.model.model_name]
    }
    else {
        defaultStyles.value[current_model.model.model_name] = {
            prompt_prefix: "",
            negative_prompt_prefix: ""
        }
        return defaultStyles.value[current_model.model.model_name]
    }
}

const samplers = ref([
    {
        "name": "DPM++ 2M",
        "aliases": [
            "k_dpmpp_2m"
        ],
        "options": {
            "scheduler": "karras"
        }
    },
    {
        "name": "DPM++ SDE",
        "aliases": [
            "k_dpmpp_sde"
        ],
        "options": {
            "scheduler": "karras",
            "second_order": true,
            "brownian_noise": true
        }
    },
    {
        "name": "DPM++ 2M SDE",
        "aliases": [
            "k_dpmpp_2m_sde"
        ],
        "options": {
            "scheduler": "exponential",
            "brownian_noise": true
        }
    },
    {
        "name": "DPM++ 2M SDE Heun",
        "aliases": [
            "k_dpmpp_2m_sde_heun"
        ],
        "options": {
            "scheduler": "exponential",
            "brownian_noise": true,
            "solver_type": "heun"
        }
    },
    {
        "name": "DPM++ 2S a",
        "aliases": [
            "k_dpmpp_2s_a"
        ],
        "options": {
            "scheduler": "karras",
            "uses_ensd": true,
            "second_order": true
        }
    },
    {
        "name": "DPM++ 3M SDE",
        "aliases": [
            "k_dpmpp_3m_sde"
        ],
        "options": {
            "scheduler": "exponential",
            "discard_next_to_last_sigma": true,
            "brownian_noise": true
        }
    },
    {
        "name": "Euler a",
        "aliases": [
            "k_euler_a",
            "k_euler_ancestral"
        ],
        "options": {
            "uses_ensd": true
        }
    },
    {
        "name": "Euler",
        "aliases": [
            "k_euler"
        ],
        "options": {}
    },
    {
        "name": "LMS",
        "aliases": [
            "k_lms"
        ],
        "options": {}
    },
    {
        "name": "Heun",
        "aliases": [
            "k_heun"
        ],
        "options": {
            "second_order": true
        }
    },
    {
        "name": "DPM2",
        "aliases": [
            "k_dpm_2"
        ],
        "options": {
            "scheduler": "karras",
            "discard_next_to_last_sigma": true,
            "second_order": true
        }
    },
    {
        "name": "DPM2 a",
        "aliases": [
            "k_dpm_2_a"
        ],
        "options": {
            "scheduler": "karras",
            "discard_next_to_last_sigma": true,
            "uses_ensd": true,
            "second_order": true
        }
    },
    {
        "name": "DPM fast",
        "aliases": [
            "k_dpm_fast"
        ],
        "options": {
            "uses_ensd": true
        }
    },
    {
        "name": "DPM adaptive",
        "aliases": [
            "k_dpm_ad"
        ],
        "options": {
            "uses_ensd": true
        }
    },
    {
        "name": "Restart",
        "aliases": [
            "restart"
        ],
        "options": {
            "scheduler": "karras",
            "second_order": true
        }
    },
    {
        "name": "HeunPP2",
        "aliases": [
            "heunpp2"
        ],
        "options": {}
    },
    {
        "name": "IPNDM",
        "aliases": [
            "ipndm"
        ],
        "options": {}
    },
    {
        "name": "IPNDM_V",
        "aliases": [
            "ipndm_v"
        ],
        "options": {}
    },
    {
        "name": "DEIS",
        "aliases": [
            "deis"
        ],
        "options": {}
    },
    {
        "name": "DDIM",
        "aliases": [
            "ddim"
        ],
        "options": {}
    },
    {
        "name": "DDIM CFG++",
        "aliases": [
            "ddim_cfgpp"
        ],
        "options": {}
    },
    {
        "name": "PLMS",
        "aliases": [
            "plms"
        ],
        "options": {}
    },
    {
        "name": "UniPC",
        "aliases": [
            "unipc"
        ],
        "options": {}
    },
    {
        "name": "LCM",
        "aliases": [
            "k_lcm"
        ],
        "options": {}
    },
    {
        "name": "DDPM",
        "aliases": [
            "ddpm"
        ],
        "options": {}
    }
])

const activeBackend = computed(() => getActiveBackend())
const backendCapabilities = computed(() => activeBackend.value.capabilities || {})
const url = computed(() => getBackendBaseUrl())
const isForgeBackend = computed(() => activeBackend.value.id === 'forge')
const canSelectModels = computed(() => backendCapabilities.value.supportsLocalModels)
const canSelectLoras = computed(() => backendCapabilities.value.supportsLoras)

//current selected model and loras
//save this in local storage


// Main API request object and state
//save this in local storage
import { request, UpdateVRAM, current_model, formatRequest, defaultStyles, GetFromApi, PostToApi } from '@/api'

const history = ref([])

const triggerWords = ref([])

// CTRL + Enter to generate image
window.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        GenerateImage()
    }
})


async function SaveCurrentSettings() {

    saveToFile(request, 'currentRequest.json')

    if (current_model.model != null && current_model.model.title != null) {
        saveToFile(current_model, 'currentModel.json')
    }

    // Save default styles to local storage
    saveDefaultStyles()

    console.log('Current settings saved successfully.')
}
async function loadCurrentSettings() {
    // Load current request settings from local storage
    const savedRequest = await loadFromFile('currentRequest.json')

    if (savedRequest) {
        Object.assign(request, savedRequest)
    }
    console.log('Current request loaded successfully:', request)

    // Load current model and loras from local storage
    const savedModel = await loadFromFile('currentModel.json')
    if (savedModel) {
        Object.assign(current_model, savedModel)
    }
    console.log('Current model loaded successfully:', current_model)


    // Load default styles from local storage
    loadDefaultStyles()


    console.log('Current settings loaded successfully.')
    console.log(document.getElementById('positive_prompt'))
}
function resetSettings() {
    // Reset request to default values
    request.prompt = ""
    request.negative_prompt = ""

    request.seed = -1
    request.sampler_name = "DPM++ 2M"
    request.batch_size = 1
    request.n_iter = 1
    request.steps = 25
    request.cfg_scale = 5
    request.width = 832
    request.height = 1216




    // Save the reset settings
    SaveCurrentSettings()
}
async function cancelGeneration() {
    //reset queue
    generationQueue.value = []

    isGenerating.value = false

    if (!backendCapabilities.value.supportsInterrupt || !url.value) {
        return
    }
    //interrupt ongoing generation
    const response = await fetch(url.value + 'sdapi/v1/interrupt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })

}

//watch for lora changes
watch(() => current_model.loras, async (newLoras) => {
    if (!backendCapabilities.value.supportsLoras) {
        triggerWords.value = []
        return
    }
    triggerWords.value = []
    let infoFiles = []
    for (const element of newLoras) {
        let infoPath = element.path.replace(".safetensors", ".civitai.info")

        //fetch /file=infoPath
        let response = await fetch(url.value + 'file=' + infoPath)
        if (response.ok) {
            let info = await response.json()
            info.file = element.path;
            infoFiles.push(info)
        } else {
            console.error('Failed to fetch info file:', response.statusText)
        }
    }
    //extract trigger words from infoFiles
    infoFiles.forEach(info => {
        if (info && info.trainedWords) {
            triggerWords.value.push(...info.trainedWords)

        }
    })

}, { deep: true });

//watch for model changes
watch(() => current_model.model, async (newModel) => {
    if (!backendCapabilities.value.supportsLocalModels) {
        return
    }
    if (newModel) {
        if (newModel.info != null) {
            return;
        }

        let infoFile = newModel.filename.replace(".safetensors", ".civitai.info");
        //fetch /file=infoFile
        let response = await fetch(url.value + 'file=' + infoFile);
        if (!response.ok) {
            console.error('Failed to fetch info file:', response.statusText);
            return;
        }
        let info = await response.json();
        // Process the info as needed

        console.log('Model info:', info);

        newModel.info = info || null;
    }
});

//watch for webState.remixImage
watch(() => webState.remixImage, async (newVal) => {
    if (newVal) {
        console.log("Remix image updated:", newVal);
        request.prompt = newVal.Prompt || request.prompt;
        request.negative_prompt = newVal.NegativePrompt || request.negative_prompt;
        request.steps = newVal.Steps || request.steps;
        request.cfg_scale = newVal.CFGScale || request.cfg_scale;
        request.sampler_name = newVal.Sampler || request.sampler_name;
        request.seed = newVal.Seed || request.seed;

        request.prompt = request.prompt.replaceAll(defaultStyles.value[current_model.model.model_name].prompt_prefix, '').trim();
        request.negative_prompt = request.negative_prompt.replaceAll(defaultStyles.value[current_model.model.model_name].negative_prompt_prefix, '').trim();

        if (backendCapabilities.value.supportsLoras && newVal.Prompt.includes("<lora:")) {
            let all_loras = await fetch(url.value + 'sdapi/v1/loras')
            if (!all_loras.ok) {
                console.error('Failed to fetch loras:', all_loras.statusText)
                return
            }
            const loras = await all_loras.json()

            //get all loras and strengths from prompt

            const loraMatches = newVal.Prompt.match(/<lora:([^:]+):([\d.]+)>/g) || [];
            current_model.loras = [];
            current_model.loras_not_found = [];
            loraMatches.forEach(match => {
                const [name, weight] = match.slice(6, -1).split(':');
                const lora = loras.find(l => l.name === name || l.alias === name);
                if (lora) {
                    current_model.loras.push({
                        ...lora,
                        name: name,
                        weight: parseFloat(weight) || 1.0
                    });
                } else {
                    current_model.loras_not_found.push({
                        name: name,
                        weight: parseFloat(weight) || 1.0
                    });
                }
            });

            //remove lora tags from prompt
            request.prompt = request.prompt.replace(/<lora:[^:]+:[\d.]+>/g, '').trim();

            autoResizePositivePrompt();
        }

    }
});

//watch for webState.sidebarWidth
watch(() => webState.sidebarWidth, (newWidth) => {
    if (newWidth !== 0) {
        autoResizePositivePrompt();
    }
});

watch(
    () => [backendState.activeId, backendState.configs[backendState.activeId]],
    () => {
        triggerWords.value = []
        getBackendStatus()
    },
    { deep: true }
)

//watch for change in request and model
let saveSettingsTimer = null;
watch([() => request, () => current_model.model], (newValues) => {
    clearTimeout(saveSettingsTimer);
    saveSettingsTimer = setTimeout(() => {
        SaveCurrentSettings()
    }, 500);
}, { deep: true });

let saveStyleLibraryTimer = null;
watch(styles, () => {
    clearTimeout(saveStyleLibraryTimer)
    saveStyleLibraryTimer = setTimeout(() => {
        saveStyleLibrary()
        sanitizeSelectedStyles()
    }, 300)
}, { deep: true })

let saveSelectedStylesTimer = null;
watch(selectedStyleIds, () => {
    clearTimeout(saveSelectedStylesTimer)
    saveSelectedStylesTimer = setTimeout(() => {
        saveSelectedStyles()
    }, 300)
}, { deep: true })

//watch request.prompt
watch(() => request.prompt, (newPrompt) => {
    autoResizePositivePrompt()
    request.prompt = newPrompt.replaceAll(defaultStyles.value[current_model.model.model_name].prompt_prefix, '').trim()
    request.prompt = newPrompt.replaceAll(",,", ',').trim()
})

//watch for history changes
watch(history, async (newHistory) => {
    if (newHistory.length > 0) {
        await saveToFile(newHistory, 'generationHistory.json')
    }
}, { deep: true })


async function saveDefaultStyles() {
    if (!defaultStyles.value || Object.keys(defaultStyles.value).length === 0) {
        console.warn('No default styles to save.')
        return
    }

    saveToFile(defaultStyles.value, 'defaultStyles.json')
}
async function loadDefaultStyles() {
    const styles = await loadFromFile('defaultStyles.json')
    if (styles) {
        defaultStyles.value = styles
    } else {
        defaultStyles.value = {}
    }
    if (defaultStyles.value[current_model.model.model_name] == null) {
        defaultStyles.value[current_model.model.model_name] = {
            prompt_prefix: "",
            negative_prompt_prefix: ""
        }
    }

    console.log('Default styles loaded successfully:', defaultStyles.value)
}

const styleLibraryFile = 'promptStyles.json'
const selectedStylesFile = 'selectedStyles.json'

async function saveStyleLibrary() {
    await saveToFile(styles.value, styleLibraryFile)
}

async function loadStyleLibrary() {
    const stored = await loadFromFile(styleLibraryFile)
    styles.value = Array.isArray(stored) ? stored : []
}

async function saveSelectedStyles() {
    await saveToFile(selectedStyleIds.value, selectedStylesFile)
}

async function loadSelectedStyles() {
    const stored = await loadFromFile(selectedStylesFile)
    selectedStyleIds.value = Array.isArray(stored) ? stored : []
}

function sanitizeSelectedStyles() {
    const styleIds = new Set(styles.value.map((style) => style.id))
    selectedStyleIds.value = selectedStyleIds.value.filter((id) => styleIds.has(id))
}

const extensions = ref([])

const adetailerAvailable = computed(() => {
    if (!backendCapabilities.value.supportsExtensions) return false
    return extensions.value.some(ext => ext.name === 'adetailer' && ext.enabled)
})
const blockCacheAvailable = computed(() => {
    if (!backendCapabilities.value.supportsExtensions) return false
    return extensions.value.some(ext => ext.name === 'sd-forge-blockcache' && ext.enabled)
})

const backendStatusChip = computed(() => {
    switch (webState.backendStatus) {
        case 'ready':
            return { label: 'Running', className: 'bg-green-600 text-[#FAF8F5]' }
        case 'starting':
            return { label: 'Starting', className: 'bg-yellow-500 text-[#FAF8F5]' }
        case 'misconfigured':
            return { label: 'Needs Setup', className: 'bg-orange-500 text-[#FAF8F5]' }
        case 'unsupported':
            return { label: 'Not Wired', className: 'bg-gray-600 text-[#FAF8F5]' }
        default:
            return { label: 'Stopped', className: 'bg-red-600 text-[#FAF8F5]' }
    }
})

const backendStatusDetail = computed(() => {
    if (webState.backendStatusMessage) return webState.backendStatusMessage
    if (webState.backendStatus === 'ready') {
        return 'Backend is active and ready to generate images.'
    }
    if (webState.backendStatus === 'starting') {
        return 'Backend is starting up. Please wait...'
    }
    if (webState.backendStatus === 'misconfigured') {
        return 'Backend needs configuration before it can run.'
    }
    if (webState.backendStatus === 'unsupported') {
        return 'Backend adapter not wired yet.'
    }
    return 'Backend is not running. Please launch to enable generation.'
})

const backendStatusDetailClass = computed(() => {
    switch (webState.backendStatus) {
        case 'ready':
            return 'text-gray-400'
        case 'starting':
            return 'text-yellow-400'
        case 'misconfigured':
            return 'text-orange-400'
        case 'unsupported':
            return 'text-gray-400'
        default:
            return 'text-red-400'
    }
})

const showLaunchBackend = computed(() => isForgeBackend.value && webState.backendStatus === 'stopped')

async function getBackendStatus() {
    const backend = activeBackend.value
    webState.backendId = backend.id
    webState.backendLabel = backend.label
    webState.backendStatusMessage = ''
    webState.backendRunning = false
    webState.backendAvailable = false
    webState.backendStatus = 'unknown'
    extensions.value = []

    const configStatus = getBackendConfigStatus(backend.id)
    if (!configStatus.ok) {
        webState.backendStatus = 'misconfigured'
        webState.backendStatusMessage = `Missing ${configStatus.missingFields.join(', ')}`
        return
    }

    if (!isForgeBackend.value) {
        webState.backendStatus = 'unsupported'
        webState.backendStatusMessage = `${backend.label} adapter not wired yet.`
        return
    }

    //check if backend is running on the apiUrl
    const response = await fetch(apiUrl + '/webui/status')
    if (response.ok) {
        const status = await response.json()
        webState.backendRunning = status.is_running
    } else {
        console.error('Failed to fetch backend status:', response.statusText)
        webState.backendRunning = false
    }

    webState.backendAvailable = false
    // If backend is not running, try to ping the backend
    try {
        const pingResponse = await fetch(url.value + 'app_id/')
        if (pingResponse.ok) {
            const pingResult = await pingResponse.json()
            webState.backendRunning = true
            webState.backendAvailable = true
            console.log('Backend ping successful:', pingResult)
        } else {
            console.log('Failed to ping backend:', pingResponse.statusText)
            webState.backendAvailable = false
            if (webState.backendRunning) {
                setTimeout(() => {
                    getBackendStatus()
                }, 100)
            }
        }
    } catch (error) {
        console.log('Failed to ping backend:', error)
        webState.backendAvailable = false
        if (webState.backendRunning) {
            setTimeout(() => {
                getBackendStatus()
            }, 100)
        }
    }

    webState.backendStatus = webState.backendAvailable
        ? 'ready'
        : webState.backendRunning
            ? 'starting'
            : 'stopped'

    if (!webState.backendRunning) {
        return
    }

    const extensionsResponse = await fetch(url.value + 'sdapi/v1/extensions')

    if (extensionsResponse.ok) {
        const extensionsData = await extensionsResponse.json()
        extensions.value = extensionsData || []
        console.log('Extensions loaded successfully:', extensions.value)
    } else {
        console.error('Failed to load extensions:', extensionsResponse.statusText)
    }
}
async function launchBackend() {

    if (!isForgeBackend.value) {
        console.warn('Launch backend is only supported for Forge right now.')
        return
    }

    console.log('Launching backend...')

    const response = await fetch(apiUrl + '/webui/start', { method: 'POST' })
    if (response.ok) {
        const result = await response.json()
        console.log('Backend launched successfully:', result)
        getBackendStatus()
    } else {
        console.error('Failed to launch backend:', response.statusText)
    }
}
async function LoadHistory() {
    const response = await fetch(apiUrl + '/storage-files/generationHistory.json')
    if (response.ok) {
        const historyData = await response.json()
        history.value = historyData || []
        console.log('History loaded successfully:', history.value)
    } else {
        console.error('Failed to load history:', response.statusText)
    }
}

const showDragOverlay = ref(false)

async function handlePromptDrop(event) {
    event.preventDefault()
    const data = event.dataTransfer.getData('text/plain')
    if (data) {

        //the front end website root url
        var websiteRootUrl = window.location.origin + '/'

        // Local Image URL
        if (data.replace(websiteRootUrl, '').includes("image/")) {
            var imageID = data.replace(websiteRootUrl, '').split("image/")[1]

            var image = await GetFromApi("image/" + imageID)

            if (image && image.Prompt) {
                request.prompt = image.Prompt
            }
        } else if (data.startsWith("http://") || data.startsWith("https://")) {
            var taggerPrompt = await PostToApi("interrogate?url=" + encodeURIComponent(data))
            request.prompt = taggerPrompt.tag_string ?? ""
        }

        else {
            request.prompt = data
        }

    } else {
        var file = event.dataTransfer.files[0];
        if (file) {
            console.log("File dropped:", file);

            var url = apiUrl + "/save-file?filename=interrogate_input_file.png";

            var formData = new FormData();
            formData.append('file', file);
            var response = await fetch(url, {
                method: 'POST',
                body: formData
            });

            var tagger = await PostToApi("interrogate?path=" + encodeURIComponent("./storage/interrogate_input_file.png"));

            request.prompt = tagger.tag_string ?? ""

        }
    }

    autoResizePositivePrompt()
    showDragOverlay.value = false
}

var generationCosts = ref({
    totalCosts: 0,
})

onMounted(async () => {
    await loadBackendSettings()
    getBackendStatus()
    onUiUpdate();
    LoadHistory();

    await loadCurrentSettings();

    await loadStyleLibrary()
    await loadSelectedStyles()
    sanitizeSelectedStyles()

    if (defaultStyles.value == null) {
        defaultStyles.value = {}
    }
    if (defaultStyles.value[current_model.model.model_name] == null) {
        defaultStyles.value[current_model.model.model_name] = {
            prompt_prefix: "",
            negative_prompt_prefix: ""
        }
    }


    autoResizePositivePrompt();

    if (isForgeBackend.value && backendCapabilities.value.supportsLocalModels && !current_model.model.title) {
        if (!url.value) {
            console.warn('Forge URL is missing. Skipping model bootstrap.')
        } else {
            const all_model_response = await fetch(url.value + 'sdapi/v1/sd-models')
            if (!all_model_response.ok) {
                console.error('Failed to fetch models:', all_model_response.statusText)
                return
            }
            const all_models = await all_model_response.json()

            const state_response = await fetch(url.value + 'state/config.json')
            if (!state_response.ok) {
                console.error('Failed to fetch state config:', state_response.statusText)
                return
            }
            const state_config = await state_response.json()
            let currentModelName = state_config.sd_model_checkpoint || state_config.sd_model || 'None'
            let currentModel = all_models.find(model => model.title.includes(currentModelName))

            if (currentModel) {
                current_model.model = { ...currentModel }
            }
            //load default styles from browser storage
            const styles = loadFromFile('defaultStyles.json')
            if (styles) {
                defaultStyles.value = JSON.parse(styles)
            }
            if (!defaultStyles.value[current_model.model.model_name]) {
                defaultStyles.value[current_model.model.model_name] = {
                    prompt_prefix: "",
                    negative_prompt_prefix: ""
                }
            }
        }
    }


    const _generationCosts = await loadFromFile("generationCosts.json")
    const _allTimeCost = await GetFromApi("get_cost")
    if (_generationCosts && _generationCosts.totalCosts !== undefined) {
        generationCosts.value.totalCosts = parseFloat(_generationCosts.totalCosts)
    }
    if (_allTimeCost && _allTimeCost.total_cost !== undefined) {
        generationCosts.value.allTimeCost = parseFloat(_allTimeCost.total_cost)
    }


    UpdateVRAM()


})

const showModelType = ref('none')
const showDownloadModal = ref(false)






// Computed properties for aspect ratio
const updateAspectRatio = (ratio) => {
    aspectRatio.value = ratio
    switch (ratio) {
        case 'Square':
            request.width = 1024
            request.height = 1024
            break
        case 'Landscape':
            request.width = 1216
            request.height = 832
            break
        case 'Portrait':
            request.width = 832
            request.height = 1216
            break
    }
}

import { apiUrl, webState } from '@/api'
import SelectModelModal from './SelectModelModal.vue'
import DownloadModel from './CivitAILoraModal.vue'
import CivitAILoraModal from './CivitAILoraModal.vue'
import DownloadLoraModal from './downloadLoraModal.vue'
import { getRandomPrompt } from '@/scripts/ranbooru'
import PillPrompt from './pillPrompt.vue'
import ChatPanel from './ChatPanel.vue'
import CanvasView from '@/views/canvasView.vue'
import AutoComplete from './autoComplete.vue'
import BackendSettingsPanel from './BackendSettingsPanel.vue'
import { Image, Settings } from 'lucide-vue-next'

const startResize = (e) => {
    isResizing.value = true
    document.addEventListener('mousemove', handleResize)
    document.addEventListener('mouseup', stopResize)
    e.preventDefault()
}

const handleResize = (e) => {
    if (isResizing.value) {
        const newWidth = Math.max(350, Math.min(600, e.clientX))
        webState.sidebarWidth = newWidth
    }
}

const stopResize = () => {
    isResizing.value = false
    document.removeEventListener('mousemove', handleResize)
    document.removeEventListener('mouseup', stopResize)
}

const toggleFullscreen = () => {
    isFullscreen.value = !isFullscreen.value

    if (isFullscreen.value) {
        // If entering fullscreen, save the current tab
        webState.previousTab = activeTab.value
        if (activeTab.value == 'generate') {
            activeTab.value = 'history'
        }
    } else {
        // If exiting fullscreen, restore the previous tab
        activeTab.value = webState.previousTab || 'generate'
    }
}
// Returns an array of all images in history items, including preview image as first, and in reverse order
const getAllHistoryImages = () => {
    // Flatten all images from history, include preview image if available, and reverse order
    let images = [];
    history.value.slice().reverse().forEach(item => {
        // If preview image exists, add it as the first image

        // Add all other images (in reverse order)
        if (item.images && item.images.length > 0) {
            item.images.slice().forEach((img, index) => {
                images.push({
                    image: img,
                    title: item.request && item.request.prompt ? item.request.prompt : 'No Title',
                    timestamp: item.timestamp || Date.now(),
                    id: item.id + (index + 1) || null,
                    isPreview: false
                });
            });
        }
    });
    return images;
}

const scanWebsocket = ref(null)
const isScanning = ref(false)

// Add progress tracking
const isGenerating = ref(false)
const generationProgress = ref(0)
const generationState = ref({})
const progressInterval = ref(null)
const AI_HORDE_POLL_INTERVAL_MS = 2000
const AI_HORDE_MAX_WAIT_MS = 15 * 60 * 1000
const aiHordeRequestState = reactive({
    id: null,
    cancelRequested: false,
    headers: null,
    statusUrl: '',
    checkUrl: ''
})

// Add WebSocket connection for scan
const connectScanWebSocket = () => {
    // Close any existing connection
    if (scanWebsocket.value && scanWebsocket.value.readyState !== WebSocket.CLOSED) {
        scanWebsocket.value.close()
    }

    // Import wsUrl from api
    import('@/api').then(({ wsUrl }) => {
        const _wsUrl = `${wsUrl}/ws/scan`

        scanWebsocket.value = new WebSocket(_wsUrl)

        scanWebsocket.value.onopen = () => {
            console.log('Scan WebSocket connection established')
            isScanning.value = true
        }

        scanWebsocket.value.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                handleScanWebSocketMessage(data)
            } catch (e) {
                console.error('Error parsing scan WebSocket message:', e)
            }
        }

        scanWebsocket.value.onerror = (event) => {
            console.error('Scan WebSocket error:', event)
            isScanning.value = false
        }

        scanWebsocket.value.onclose = () => {
            console.log('Scan WebSocket connection closed')
            isScanning.value = false
        }
    })
}

// Handle incoming scan WebSocket messages
const handleScanWebSocketMessage = (data) => {
    console.log('Scan WebSocket message:', data)

    switch (data.type) {
        case 'image_discovered':
            // Check if this is a newly generated image by looking at the path
            if (data.image_path && data.image_path.includes('outputs')) {
                // Find the most recent history item that doesn't have an ID yet
                const recentItem = history.value[history.value.length - 1]
                if (recentItem && !recentItem.id) {
                    // Update the history item with the discovered image info
                    recentItem.id = data.image_id || Date.now()
                    recentItem.path = data.image_path
                    console.log('Updated history item with scanned image:', recentItem)
                }
            }
            break

        case 'complete':
            isScanning.value = false
            console.log('Scan completed', data.start_id)

            let start_id = data.start_id;
            let images_added = data.total_added;
            //add id to the last history item
            const recentItem = history.value[history.value.length - 1]
            if (recentItem && !recentItem.id) {
                recentItem.id = start_id || Date.now()
                recentItem.images_added = images_added || 0
                console.log('Updated history item with scan completion:', recentItem)
            }

            break

        case 'error':
            console.error('Scan error:', data.message)
            isScanning.value = false
            break
    }
}

// Add progress polling function
const pollProgress = async () => {
    try {
        if (!backendCapabilities.value.supportsProgress || !url.value) return
        const response = await fetch(url.value + 'sdapi/v1/progress')
        if (!response.ok) return

        const progress = await response.json()
        generationProgress.value = progress.progress
        generationState.value = progress.state || {}
        generationState.value.current_image = progress.current_image || null

        // Stop polling when generation is complete
        if (progress.progress >= 1 || progress.state?.job_count === 0) {
            clearInterval(progressInterval.value)
            progressInterval.value = null
        }
    } catch (error) {
        console.error('Failed to fetch progress:', error)
    }
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const updateAiHordeProgress = (status) => {
    if (!status) return
    const finished = status.finished || 0
    const processing = status.processing || 0
    const waiting = status.waiting || 0
    const restarted = status.restarted || 0
    const total = finished + processing + waiting + restarted

    if (total > 0) {
        generationProgress.value = Math.min(1, finished / total)
    }

    generationState.value = {
        ...generationState.value,
        sampling_step: finished,
        sampling_steps: total,
        job: status.queue_position != null
            ? `Queue ${status.queue_position}`
            : processing > 0
                ? 'Processing'
                : 'Queued'
    }
}

const pollAiHordeStatus = async (backendRequest, requestId) => {
    const startTime = Date.now()

    while (!aiHordeRequestState.cancelRequested) {
        if (Date.now() - startTime > AI_HORDE_MAX_WAIT_MS) {
            throw new Error('AI Horde request timed out.')
        }

        const checkResponse = await fetch(`${backendRequest.checkUrl}${requestId}`, {
            headers: backendRequest.headers
        })

        if (!checkResponse.ok) {
            throw new Error(`AI Horde status check failed: ${checkResponse.statusText}`)
        }

        const status = await checkResponse.json()
        updateAiHordeProgress(status)

        if (status.faulted) {
            throw new Error('AI Horde request faulted.')
        }

        if (status.is_possible === false) {
            throw new Error('AI Horde request cannot be fulfilled with available workers.')
        }

        if (status.done) {
            return status
        }

        await sleep(AI_HORDE_POLL_INTERVAL_MS)
    }

    return null
}

const processAiHordeRequest = async (backendRequest) => {
    aiHordeRequestState.cancelRequested = false
    aiHordeRequestState.headers = backendRequest.headers
    aiHordeRequestState.statusUrl = backendRequest.statusUrl
    aiHordeRequestState.checkUrl = backendRequest.checkUrl

    const response = await fetch(backendRequest.requestUrl, {
        method: 'POST',
        headers: backendRequest.headers,
        body: JSON.stringify(backendRequest.payload)
    })

    if (!response.ok) {
        throw new Error(`AI Horde request failed: ${response.statusText}`)
    }

    const asyncResult = await response.json()
    const requestId = asyncResult?.id
    if (!requestId) {
        throw new Error('AI Horde did not return a request id.')
    }

    aiHordeRequestState.id = requestId

    await pollAiHordeStatus(backendRequest, requestId)

    if (aiHordeRequestState.cancelRequested) {
        return null
    }

    const statusResponse = await fetch(`${backendRequest.statusUrl}${requestId}`, {
        headers: backendRequest.headers
    })

    if (!statusResponse.ok) {
        throw new Error(`AI Horde result fetch failed: ${statusResponse.statusText}`)
    }

    const statusData = await statusResponse.json()
    generationProgress.value = 1
    return statusData
}

var generationQueue = ref([])

async function GenerateImage() {

    if (!webState.backendAvailable) {
        console.warn('Backend not available:', webState.backendStatusMessage || webState.backendStatus)
        return
    }

    const plainRequest = formatRequest();
    plainRequest.prompt = applyStylesToPrompt(plainRequest.prompt)

    generationCosts.value.totalCosts += parseFloat(calculateCost(plainRequest))
    console.log("Estimated generation cost:", generationCosts.value.totalCosts)

    await saveToFile(generationCosts.value, "generationCosts.json")

    console.log(JSON.stringify(plainRequest))

    console.log("Adding request to generation queue")
    generationQueue.value.push({
        request: plainRequest,
        inputImage: imageInput.base64 || null,
        inputImageName: imageInput.name || null,
        denoisingStrength: img2imgDenoise.value
    })


    if (!isGenerating.value) {
        await ProcessRequest(generationQueue.value.shift())
    }
}


async function ProcessRequest(queueItem) {
    // Start progress tracking
    isGenerating.value = true
    generationProgress.value = 0
    generationState.value = {}

    if (progressInterval.value) {
        clearInterval(progressInterval.value)
        progressInterval.value = null
    }

    if (!queueItem) {
        isGenerating.value = false
        return
    }

    const baseRequest = queueItem.request || queueItem
    const inputImage = queueItem.inputImage || null
    const denoisingStrength = typeof queueItem.denoisingStrength === 'number'
        ? queueItem.denoisingStrength
        : img2imgDenoise.value
    const backendRequest = buildBackendRequest({
        baseRequest,
        inputImage,
        denoisingStrength
    })

    if (backendRequest.status !== 'ready') {
        console.warn('Backend request not ready:', backendRequest.reason)
        webState.backendStatus = backendRequest.status
        webState.backendStatusMessage = backendRequest.reason
        webState.backendAvailable = false
        isGenerating.value = false
        return
    }

    // Start polling progress every 500ms
    if (backendRequest.supportsProgress) {
        progressInterval.value = setInterval(pollProgress, 500)
    }

    //post to api /ollama/unload-models
    const unloadResponse = await fetch(apiUrl + '/ollama/unload-models', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ models: [current_model.model.model_name] })
    })

    //post to /sdapi/v1/txt2img with body as plainRequest
    const response = await fetch(backendRequest.requestUrl, {
        method: 'POST',
        headers: backendRequest.headers,
        body: JSON.stringify(backendRequest.payload)
    })
    if (!response.ok) {
        console.error('Failed to generate image:', response.statusText)
        // Stop progress tracking on error
        clearInterval(progressInterval.value)
        progressInterval.value = null

        if (generationQueue.value.length > 0) {
            // Process the next request in the queue
            console.log("Processing next request in queue")
            await ProcessRequest(generationQueue.value.shift())
        } else {
            isGenerating.value = false
        }

        return
    }
    const result = await response.json()

    // Stop progress tracking when generation completes
    clearInterval(progressInterval.value)
    progressInterval.value = null

    // Handle the result as needed, e.g., display the generated image

    const historyRequest = { ...baseRequest }
    if (inputImage) {
        historyRequest.img2img = true
        historyRequest.denoising_strength = denoisingStrength
        historyRequest.input_image_name = queueItem.inputImageName || null
    }

    const historyItem = {
        request: historyRequest,
        images: result.images,
        timestamp: Date.now(),
        // Will be updated by scan WebSocket
        id: null,
        path: null
    }

    history.value.push(historyItem)
    generationState.value.current_image = null // Reset current image state
    console.log('Image generated successfully:', result)


    connectScanWebSocket()

    if (generationQueue.value.length > 0) {
        // Process the next request in the queue
        console.log("Processing next request in queue")
        await ProcessRequest(generationQueue.value.shift())
    } else {
        isGenerating.value = false
    }
}

const queueLength = computed(() => {
    return generationQueue.value.length
})

function selectLora(modelId) {
    downloadLoraId.value = modelId;
}

function selectModel(model) {

    if (showModelType.value === 'lora') {

        if (current_model.loras.find(l => l.name === model.name)) {
            //remove
            current_model.loras = current_model.loras.filter(l => l.name !== model.name)
            return
        }
        //get civitai info for this lora
        let infoPath = model.path.replace(".safetensors", ".civitai.info")


        current_model.loras.push({ ...model, weight: 1.0 })
        return
    } else if (showModelType.value == 'checkpoint') {
        current_model.model = { ...model }

        //default styles for this model
        if (!defaultStyles.value[model.model_name]) {
            defaultStyles.value[model.model_name] = {
                prompt_prefix: "",
                negative_prompt_prefix: ""
            }
        }

        return
    }
}

const placeholderImage = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDUwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMzMzIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk5vIEltYWdlPC90ZXh0Pjwvc3ZnPg==';

const getModelImage = (model, attempt = 0) => {
    if (!backendCapabilities.value.supportsModelThumbnails || !url.value) return placeholderImage;
    if (!model.filename && !model.path) return placeholderImage;

    let modelPath = model.path || model.filename;
    let baseUrl = url.value + 'sd_extra_networks/thumb?filename=';

    if (attempt === 0) {
        return baseUrl + modelPath.replace(".safetensors", ".png");
    } else if (attempt === 1) {
        return baseUrl + modelPath.replace(".safetensors", ".preview.png");
    } else {
        return placeholderImage;
    }
};

async function OpenLoraData(path) {
    const response = await GetFromApi("model-metadata/?path=" + encodeURIComponent(path))
    if (response) {
        downloadLoraId.value = response.modelId;
    }
}

const handleImageError = (event, model) => {
    const img = event.target;
    const currentSrc = img.src;

    if (currentSrc === getModelImage(model, 0)) {
        img.src = getModelImage(model, 1);
    } else if (currentSrc === getModelImage(model, 1)) {
        img.src = getModelImage(model, 2);
    }
};

// History management functions
const loadFromHistory = (historyRequest) => {
    // Copy all settings from history item to current request
    Object.assign(request, historyRequest);

    // Update aspect ratio based on dimensions
    if (request.width === 1024 && request.height === 1024) {
        aspectRatio.value = 'Square';
    } else if (request.width === 1216 && request.height === 832) {
        aspectRatio.value = 'Landscape';
    } else if (request.width === 832 && request.height === 1216) {
        aspectRatio.value = 'Portrait';
    }

    // Switch to generate tab
    activeTab.value = 'generate';
};

const downloadImages = (images) => {
    images.forEach((image, index) => {
        const link = document.createElement('a');
        link.href = `data:image/png;base64,${image}`;
        link.download = `generated-image-${Date.now()}-${index + 1}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });
};

const deleteHistoryItem = (index) => {
    history.value.splice(index, 1);
};

const clearHistory = () => {
    if (confirm('Are you sure you want to clear all generation history?')) {
        history.value = [];
    }
};



onBeforeUnmount(() => {
    // Close scan WebSocket connection when component is unmounted
    if (scanWebsocket.value && scanWebsocket.value.readyState !== WebSocket.CLOSED) {
        scanWebsocket.value.close()
    }

    // Clear progress polling interval
    if (progressInterval.value) {
        clearInterval(progressInterval.value)
        progressInterval.value = null
    }
})

// Add these reactive variables after the existing refs
const copiedIndex = ref(null)
const copiedAll = ref(false)


async function addTriggerWord(word, index) {
    if (!request.prompt.includes(word)) {
        const trimmedPrompt = request.prompt.trim()
        if (trimmedPrompt) {
            request.prompt = trimmedPrompt + (trimmedPrompt.endsWith(',') ? ' ' : ', ') + word
        } else {
            request.prompt = word
        }
    } else {
        //remove word from prompt
        request.prompt = request.prompt.split(',').map(w => w.trim()).filter(w => w !== word).join(', ')
    }
}
async function addAllTriggerWords() {
    let addedWords = []
    triggerWords.value.forEach(word => {
        if (!request.prompt.includes(word)) {
            const trimmedPrompt = request.prompt.trim()
            if (trimmedPrompt) {
                request.prompt = trimmedPrompt + (trimmedPrompt.endsWith(',') ? ' ' : ', ') + word
            } else {
                request.prompt = word
            }
            addedWords.push(word)
        }
    })
}

const downloadLoraId = ref(null)

function autoResizeTextArea(target) {
    target.style.height = 'auto';
    target.style.height = target.scrollHeight + 'px';
}

const positivePrompt = ref();

const negativePrompt = ref();

function autoResizePositivePrompt() {

    if (positivePrompt.value == null) {
        return;
    }

    //wait 100ms
    setTimeout(() => {
        autoResizeTextArea(positivePrompt.value);
    }, 100);


}



async function randomizePrompt(source) {

    if (source == 'booru') {
        const prompts = await getRandomPrompt({
            booru: 'rule34',           // Which booru to use
            tags: '',    // Search tags
            basePrompt: '',    // Base prompt to prepend
            shuffleTags: true,            // Randomize tag order
            maxTags: 50,                  // Limit number of tags
            changeBackground: 'Add Background', // Background modification
            rating: 'All'                // Content rating filter
        });
        console.log('Randomized prompt:', prompts);
        request.prompt = prompts.prompt;
    }
    else if (source == 'local') {
        const response = await fetch(apiUrl + '/random-image')
        if (!response.ok) {
            console.error('Failed to fetch random image:', response.statusText)
            return
        }
        const data = await response.json()
        if (data.taggerPrompt) {
            request.prompt = data.taggerPrompt
        } else {
            const taggerPrompt = await PostToApi("generate_tagger_prompt_for/" + encodeURIComponent(data.Id))
            request.prompt = taggerPrompt.prompt ?? ""
        }
    }
    else if (source == "ai") {

    }

}
const promptEnhanceRequest = ref("");
const promptEnhanceInProgress = ref(false)
async function enhancePrompt() {
    promptEnhanceInProgress.value = true
    let url = apiUrl + '/prompt-enhance?prompt=' + encodeURIComponent(request.prompt) + "&request=" + encodeURIComponent(promptEnhanceRequest.value)
    const response = await fetch(url)
    promptEnhanceInProgress.value = false
    if (!response.ok) {
        console.error('Failed to enhance prompt:', response.statusText)
        return
    }
    const data = await response.json()
    request.prompt = data.enhanced_prompt || request.prompt
}

async function unloadSD() {
    if (!isForgeBackend.value || !url.value) {
        return
    }
    const response = await fetch(url.value + 'sdapi/v1/unload-checkpoint', { method: 'POST' })
    if (response.ok) console.log('SD unloaded')
}

async function unloadLLM() {
    const response = await fetch(apiUrl + '/ollama/unload-models', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    if (response.ok) console.log('LLM unloaded')
}

</script>

<template>



    <SelectModelModal
        v-if="showModelType !== 'none' && ((showModelType === 'checkpoint' && canSelectModels) || (showModelType === 'lora' && canSelectLoras))"
        :modelType="showModelType" :url="url" class="z-[51]" @close="showModelType = 'none'"
        @select="selectModel" :current_loras="current_model.loras" />
    <CivitAILoraModal v-if="showDownloadModal == true && canSelectLoras" :baseModel="current_model.model.info?.baseModel"
        class="z-[51]" @close="showDownloadModal = false" @select="selectLora" :webuiUrl="url" />
    <DownloadLoraModal v-if="downloadLoraId != null && canSelectLoras" :modelId="downloadLoraId" class="z-[52]"
        @close="downloadLoraId = null" :url="url" />




    <div v-else :class="[
        isFullscreen ? 'fixed inset-0 flex' : 'fixed top-0 left-0',
        webState.sidebarWidth == 0 ? 'hidden' : ''
    ]" :style="isFullscreen ? {} : { width: `${webState.sidebarWidth}px`, height: '100vh' }"
        class="bg-[#0D0D12] text-[#FAF8F5] shadow-2xl z-50">

        <div v-if="showStyleManager"
            class="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 backdrop-blur-sm"
            @click.self="showStyleManager = false">
            <div class="w-full max-w-3xl bg-[#0F0F16] border border-[#2A2A35] rounded-xl shadow-2xl">
                <div class="flex items-center justify-between px-4 py-3 border-b border-[#2A2A35]">
                    <h3 class="text-lg font-semibold text-[#FAF8F5]">Styles</h3>
                    <button @click="showStyleManager = false" class="text-gray-400 hover:text-[#FAF8F5] p-1 rounded">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                <div class="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="space-y-2">
                        <div class="flex items-center justify-between">
                            <h4 class="text-sm font-medium text-gray-300">Saved Styles</h4>
                            <button @click="startNewStyle"
                                class="text-xs text-gray-400 hover:text-[#FAF8F5]">New</button>
                        </div>
                        <div class="max-h-[360px] overflow-y-auto space-y-2">
                            <div v-if="styles.length === 0" class="text-xs text-gray-400 italic">
                                No styles yet.
                            </div>
                            <div v-for="style in styles" :key="style.id" @click="startEditStyle(style)"
                                class="flex items-center justify-between bg-[#1A1A24] border border-[#2A2A35] rounded-lg px-3 py-2 pointer-cursor">
                                <div class="flex items-center gap-2 min-w-0">
                                    <img :src="style.image || placeholderImage" alt=""
                                        class="w-9 h-9 rounded-full object-cover border border-gray-700" />
                                    <div class="min-w-0">
                                        <p class="text-sm font-medium text-[#FAF8F5] truncate">{{ style.name }}</p>
                                        <p class="text-xs text-gray-400 truncate">{{ style.tags }}</p>
                                    </div>
                                </div>
                                <div class="flex items-center gap-2">
                                    <button @click="startEditStyle(style)"
                                        class="text-xs text-blue-400 hover:text-blue-300">Edit</button>
                                    <button @click="removeStyle(style.id)"
                                        class="text-xs text-red-400 hover:text-red-300">Delete</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="bg-[#1A1A24] border border-[#2A2A35] rounded-lg p-3 space-y-3">
                        <div class="flex items-center justify-between">
                            <h4 class="text-sm font-medium text-gray-300">
                                {{ isEditingStyle ? 'Edit Style' : 'New Style' }}
                            </h4>
                            <button v-if="isEditingStyle" @click="startNewStyle"
                                class="text-xs text-gray-400 hover:text-[#FAF8F5]">Clear</button>
                        </div>
                        <div class="space-y-2">
                            <label class="text-xs text-gray-400 font-medium">Name</label>
                            <input v-model="styleForm.name" type="text" placeholder="Style name"
                                class="w-full bg-[#0f0f15] border border-[#2A2A35] text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500" />
                        </div>
                        <div class="space-y-2">
                            <label class="text-xs text-gray-400 font-medium">Tags</label>
                            <textarea v-model="styleForm.tags" rows="3" placeholder="comma-separated tags"
                                class="w-full bg-[#0f0f15] border border-[#2A2A35] text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500 resize-none"></textarea>
                        </div>
                        <div class="space-y-2">
                            <label class="text-xs text-gray-400 font-medium">Image</label>
                            <input v-model="styleForm.image" type="text" placeholder="Image URL or data URI"
                                class="w-full bg-[#0f0f15] border border-[#2A2A35] text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500" />
                            <div class="flex items-center gap-3">
                                <input type="file" accept="image/*" @change="handleStyleImageUpload"
                                    class="text-xs text-gray-400" />
                                <img :src="styleForm.image || placeholderImage" alt=""
                                    class="w-10 h-10 rounded-full object-cover border border-gray-700" />
                            </div>
                        </div>
                        <div class="flex items-center gap-2 pt-1">
                            <button @click="saveStyle" :disabled="!styleForm.name.trim() || !styleForm.tags.trim()"
                                :class="(!styleForm.name.trim() || !styleForm.tags.trim()) ? 'bg-gray-700 text-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-[#FAF8F5]'"
                                class="px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                                {{ isEditingStyle ? 'Save' : 'Add' }}
                            </button>
                            <button @click="startNewStyle"
                                class="bg-[#0f0f15] border border-[#2A2A35] text-gray-300 hover:text-[#FAF8F5] px-4 py-2 rounded-lg text-sm">
                                Reset
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Sidebar -->
        <div :style="isFullscreen ? { width: `${webState.sidebarWidth}px` } : {}"
            class="flex flex-col h-full bg-[#0D0D12] border-r border-gray-700">
            <!-- Fixed Header with close button -->
            <div class="flex items-center justify-between p-4 border-b border-gray-700 flex-shrink-0">
                <!-- Fixed Tab Navigation -->
                <div class="flex flex-shrink-0 bg-[#0D0D12] rounded-lg overflow-hidden p-1 space-x-1">
                    <button v-if="!isFullscreen" @click="activeTab = 'generate'"
                        :class="activeTab === 'generate' ? 'bg-[#1A1A24] text-[#FAF8F5]' : 'text-gray-400 hover:text-[#FAF8F5] hover:bg-[#1A1A24]'"
                        class="flex items-center justify-center w-10 h-10 rounded transition-colors">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                    </button>
                    <button @click="activeTab = 'history'"
                        :class="activeTab === 'history' ? 'bg-[#1A1A24] text-[#FAF8F5]' : 'text-gray-400 hover:text-[#FAF8F5] hover:bg-[#1A1A24]'"
                        class="flex items-center justify-center w-10 h-10 rounded transition-colors relative">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div v-if="isScanning"
                            class="absolute top-1 right-1 w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                    </button>
                    <button @click="activeTab = 'gallery'"
                        :class="activeTab === 'gallery' ? 'bg-[#1A1A24] text-[#FAF8F5]' : 'text-gray-400 hover:text-[#FAF8F5] hover:bg-[#1A1A24]'"
                        class="flex items-center justify-center w-10 h-10 rounded transition-colors relative">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                            class="lucide lucide-layout-grid-icon lucide-layout-grid">
                            <rect width="7" height="7" x="3" y="3" rx="1" />
                            <rect width="7" height="7" x="14" y="3" rx="1" />
                            <rect width="7" height="7" x="14" y="14" rx="1" />
                            <rect width="7" height="7" x="3" y="14" rx="1" />
                        </svg>
                        <div v-if="isScanning"
                            class="absolute top-1 right-1 w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                    </button>
                    <button @click="activeTab = 'chat'"
                        :class="activeTab === 'chat' ? 'bg-[#1A1A24] text-[#FAF8F5]' : 'text-gray-400 hover:text-[#FAF8F5] hover:bg-[#1A1A24]'"
                        class="flex items-center justify-center w-10 h-10 rounded transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                            class="lucide lucide-bot-message-square-icon lucide-bot-message-square">
                            <path d="M12 6V2H8" />
                            <path d="M15 11v2" />
                            <path d="M2 12h2" />
                            <path d="M20 12h2" />
                            <path
                                d="M20 16a2 2 0 0 1-2 2H8.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 4 20.286V8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2z" />
                            <path d="M9 11v2" />
                        </svg>
                    </button>
                    <button @click="activeTab = 'settings'"
                        :class="activeTab === 'settings' ? 'bg-[#1A1A24] text-[#FAF8F5]' : 'text-gray-400 hover:text-[#FAF8F5] hover:bg-[#1A1A24]'"
                        class="flex items-center justify-center w-10 h-10 rounded transition-colors" title="Settings">
                        <Settings class="w-5 h-5" />
                    </button>
                </div>
                <!-- VRAM usage rectangle with label inside at left bottom -->
                <div v-if="webState.vramUsage" class="w-full flex items-center justify-center mx-4 relative group">
                    <div class="relative flex-1 h-8">
                        <div class="w-full h-full bg-gray-700 rounded-lg overflow-hidden cursor-pointer">
                            <div class="bg-blue-500 h-full transition-all duration-300"
                                :style="{ width: `${webState.vramUsage * 100}%` }"></div>
                        </div>
                        <span class="absolute left-2 bottom-1 text-xs font-bold text-[#FAF8F5]">
                            VRAM
                        </span>
                        <span class="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-bold text-[#FAF8F5]">
                            {{ (webState.vramUsage * 100).toFixed(1) }}%
                        </span>
                    </div>

                    <!-- Dropdown Menu -->
                    <div
                        class="absolute top-full left-0 mt-2 w-40 bg-[#1A1A24] border border-[#2A2A35] rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-40">
                        <button @click="unloadSD()"
                            class="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-[#FAF8F5] transition-colors rounded-t-lg">
                            Unload SD
                        </button>
                        <button @click="unloadLLM()"
                            class="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-[#FAF8F5] transition-colors rounded-b-lg border-t border-[#2A2A35]">
                            Unload LLM
                        </button>
                    </div>
                </div>

                <div class="flex items-center space-x-2">

                    <button @click="toggleFullscreen"
                        class="text-gray-400 hover:text-[#FAF8F5] p-1 rounded transition-colors"
                        :title="isFullscreen ? 'Exit fullscreen' : 'Fullscreen'">
                        <svg v-if="!isFullscreen" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                        </svg>
                        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M9 9V4.5M9 9H4.5M9 9L3.5 3.5M15 9v-4.5M15 9h4.5M15 9l5.5-5.5M9 15v4.5M9 15H4.5M9 15l-5.5 5.5M15 15h4.5M15 15v4.5m0-4.5l5.5 5.5" />
                        </svg>
                    </button>
                    <button @click="webState.sidebarWidth = 0"
                        class="text-gray-400 hover:text-[#FAF8F5] p-1 rounded transition-colors" title="Close">
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd"
                                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                clip-rule="evenodd" />
                        </svg>
                    </button>
                </div>
            </div>

            <!-- Scrollable Content Area -->
            <div class="flex-1 flex flex-col min-h-0">
                <!-- Generate Tab Content -->
                <div v-show="activeTab === 'generate' || isFullscreen" class="flex-1 flex flex-col min-h-0">
                    <!-- Scrollable middle section -->
                    <div class="flex-1 overflow-y-auto p-4 space-y-6">
                        <!-- Tabs -->
                        <div class="flex bg-[#1A1A24] rounded-lg p-1 hidden">
                            <button
                                class="flex-1 bg-blue-600 text-[#FAF8F5] font-medium py-2 px-4 rounded-md text-sm">Image</button>
                            <button
                                class="flex-1 text-gray-400 font-medium py-2 px-4 rounded-md text-sm hover:text-[#FAF8F5]">Video</button>
                        </div>

                        <!-- Workflow -->
                        <div class="hidden">
                            <div class="flex items-center space-x-2 mb-2">
                                <label class="text-sm text-gray-300 font-medium">Workflow</label>
                                <span
                                    class="bg-green-500 text-black text-xs px-2 py-0.5 rounded-full font-bold">NEW</span>
                            </div>
                            <select v-model="workflow"
                                class="w-full bg-[#1A1A24] border border-[#2A2A35] text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500 appearance-none">
                                <option>Text-to-image</option>
                                <option>ComfyUI (coming soon)</option>
                            </select>
                        </div>
                        <!-- Start BackEnd Options with status (isrunning/stopped) and launch button if stopped-->
                        <div class="mb-4">
                            <div class="flex items-center justify-between mb-2">
                                <label class="text-sm text-gray-300 font-medium flex items-center gap-2">
                                    Backend Status
                                    <span class="text-xs text-gray-400">{{ activeBackend.label }}</span>
                                    <span
                                        class="px-2 py-0.5 rounded-full text-xs font-semibold"
                                        :class="backendStatusChip.className">
                                        {{ backendStatusChip.label }}
                                    </span>
                                    <button @click="getBackendStatus()"
                                        class="cursor-pointer text-gray-400 hover:text-[#FAF8F5]">
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                                            stroke-width="1.5" stroke="currentColor" class="w-4">
                                            <path stroke-linecap="round" stroke-linejoin="round"
                                                d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
                                        </svg>
                                    </button>
                                </label>
                                <div class="flex items-center gap-2">
                                    <button @click="activeTab = 'settings'"
                                        class="bg-[#1A1A24] border border-[#2A2A35] text-xs text-gray-300 hover:text-[#FAF8F5] px-3 py-1.5 rounded-md font-medium">
                                        Settings
                                    </button>
                                    <button v-if="showLaunchBackend" @click="launchBackend()"
                                        class="bg-blue-600 hover:bg-blue-700 text-[#FAF8F5] text-xs px-3 py-1.5 rounded-md font-medium">
                                        Launch Backend
                                    </button>
                                </div>
                            </div>
                            <div class="text-xs" :class="backendStatusDetailClass">
                                {{ backendStatusDetail }}
                            </div>
                        </div>

                        <!--Compact mode toggle-->
                        <div class="flex items-center justify-between mb-2">
                            <label class="text-sm text-gray-300 font-medium">Compact Mode</label>
                            <button @click="compactMode = !compactMode"
                                :class="compactMode ? 'bg-blue-600' : 'bg-gray-700'"
                                class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none">
                                <span :class="compactMode ? 'translate-x-6' : 'translate-x-1'"
                                    class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform" />
                            </button>
                        </div>


                        <!-- Model -->
                        <div v-if="!compactMode">
                            <div v-if="!backendCapabilities.supportsLocalModels"
                                class="bg-[#1A1A24] border border-[#2A2A35] rounded-lg p-4 text-sm text-gray-300">
                                <p class="font-medium text-[#FAF8F5] mb-1">Models are backend-specific</p>
                                <p class="text-xs text-gray-400">
                                    The current backend does not expose local models. Switch to Forge or configure a
                                    compatible adapter in Settings.
                                </p>
                            </div>
                            <div v-else>
                                <div class="flex items-center justify-between mb-2">
                                    <div class="flex items-center space-x-2">
                                        <label class="text-sm text-gray-300 font-medium">Model</label>
                                        <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor"
                                            viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                    </div>
                                </div>
                                <div class="bg-[#1A1A24] border border-[#2A2A35] rounded-lg">
                                <!-- Model Section -->
                                <div class="p-3 flex items-center justify-between gap-4">
                                    <div class="flex items-center gap-2 min-w-0">
                                        <img :src="getModelImage(current_model.model, 0)" alt=""
                                            class="w-16 h-16 rounded-xl object-cover aspect-square bg-gradient-to-br from-orange-400 to-red-500 border-2 border-gray-700 shadow-md"
                                            @error="handleImageError($event, current_model.model)" />

                                        <div class="min-w-0">
                                            <p
                                                class="text-base md:text-lg font-semibold text-[#FAF8F5] flex items-center gap-2 truncate">
                                                <span class="truncate">
                                                    {{
                                                        current_model?.model?.title?.split('\\').pop().replace(".safetensors",
                                                            "")
                                                    }}
                                                </span>
                                                <a v-if="current_model.model.info?.modelId"
                                                    :href="`https://civitai.com/models/${current_model.model.info.modelId}`"
                                                    target="_blank" rel="noopener noreferrer"
                                                    class="ml-1 text-blue-400 hover:underline flex items-center"
                                                    title="View on Civitai">
                                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none"
                                                        viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"
                                                        class="w-4 h-4 mr-1">
                                                        <path strokeLinecap="round" strokeLinejoin="round"
                                                            d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                                                    </svg>

                                                    <span class="hidden sm:inline"></span>
                                                </a>
                                            </p>
                                            <p class="text-xs text-gray-400 truncate max-w-[180px] md:max-w-xs">
                                                {{ current_model.model.title }}
                                            </p>
                                        </div>
                                    </div>
                                    <div class="flex gap-2 flex-shrink-0">
                                        <button @click="showModelStyles()"
                                            class="bg-blue-600 hover:bg-blue-700 text-[#FAF8F5] text-xs px-2 py-1 rounded-md font-medium flex items-center gap-1 shadow"
                                            title="Edit Model Prefixes">
                                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                                                stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                                                <path stroke-linecap="round" stroke-linejoin="round"
                                                    d="M9.53 16.122a3 3 0 0 0-5.78 1.128 2.25 2.25 0 0 1-2.4 2.245 4.5 4.5 0 0 0 8.4-2.245c0-.399-.078-.78-.22-1.128Zm0 0a15.998 15.998 0 0 0 3.388-1.62m-5.043-.025a15.994 15.994 0 0 1 1.622-3.395m3.42 3.42a15.995 15.995 0 0 0 4.764-4.648l3.876-5.814a1.151 1.151 0 0 0-1.597-1.597L14.146 6.32a15.996 15.996 0 0 0-4.649 4.763m3.42 3.42a6.776 6.776 0 0 0-3.42-3.42" />
                                            </svg>
                                        </button>
                                        <button @click="showModelType = 'checkpoint'"
                                            class="bg-blue-600 hover:bg-blue-700 text-[#FAF8F5] text-xs px-3 py-1.5 rounded-md font-medium shadow flex items-center gap-1">
                                            <span class="text-lg leading-none">⚡</span>
                                            <span class="hidden sm:inline">Swap</span>
                                        </button>
                                    </div>
                                </div>
                                <!-- Default Styles Section -->
                                <div v-if="showDefaultStyles" class="border-t border-[#2A2A35] p-3 space-y-2">
                                    <!--Prompt Prefix input-->
                                    <div class="space-y-2">
                                        <label class="text-sm text-gray-300 font-medium block mb-1">Prompt Prefix
                                        </label>
                                        <input v-model="getDefaultStyles().prompt_prefix" @input="saveDefaultStyles"
                                            type="text" placeholder="Enter prompt prefix"
                                            class="w-full bg-[#232323] border border-[#2A2A35] focus:border-blue-500 text-xs text-[#FAF8F5] px-3 py-2 rounded-lg transition-colors placeholder-gray-500" />
                                    </div>
                                    <!--Prompt Prefix input-->
                                    <div class="space-y-2">
                                        <label class="text-sm text-gray-300 font-medium block mb-1">Negative prompt
                                            Prefix</label>
                                        <input @input="saveDefaultStyles"
                                            v-model="getDefaultStyles().negative_prompt_prefix" type="text"
                                            placeholder="Enter negative prompt prefix"
                                            class="w-full bg-[#232323] border border-[#2A2A35] focus:border-blue-500 text-xs text-[#FAF8F5] px-3 py-2 rounded-lg transition-colors placeholder-gray-500" />
                                    </div>
                                    <!--Override Sampler-->
                                    <div class="space-y-2">
                                        <label class="text-sm text-gray-300 font-medium block mb-1">Override
                                            Sampler</label>
                                        <select v-model="getDefaultStyles().override_sampler"
                                            @change="saveDefaultStyles"
                                            class="w-full bg-[#232323] border border-[#2A2A35] focus:border-blue-500 text-xs text-[#FAF8F5] px-3 py-2 rounded-lg transition-colors">
                                            <option :value="null"></option>
                                            <option v-for="sampler in samplers" :key="sampler.name"
                                                :value="sampler.name">{{ sampler.name }}</option>


                                        </select>
                                    </div>
                                </div>

                                <!-- Additional Resources Section -->
                                <div v-if="backendCapabilities.supportsLoras"
                                    :class="current_model.showLoras ? 'border-b border-[#2A2A35]' : ''"
                                    class="border-t border-[#2A2A35] p-2"
                                    @click="current_model.showLoras = !current_model.showLoras">
                                    <div class="flex items-center justify-between ">
                                        <div>
                                            <span class="text-sm text-gray-300 font-medium">Additional Resources</span>
                                            <!--lora count-->
                                            <span
                                                class="ml-1 bg-blue-600/80 text-[#FAF8F5] rounded-full px-2 py-0.5 text-xs font-semibold">{{
                                                    current_model.loras.length }}</span>
                                            <span v-if="current_model.loras_not_found.length > 0"
                                                class="ml-1 bg-red-600/80 text-[#FAF8F5] rounded-full px-2 py-0.5 text-xs font-semibold">{{
                                                    current_model.loras_not_found.length }}</span>
                                        </div>
                                        <div class="flex items-center space-x-1">
                                            <button @click="showDownloadModal = !showDownloadModal"
                                                class="text-blue-400 hover:text-blue-300 text-xs font-medium border border-dashed border-[#2A2A35] hover:border-blue-400 px-3 py-1 rounded-md transition-colors">
                                                + Download
                                            </button>
                                            <button @click="showModelType = 'lora'"
                                                class="text-blue-400 hover:text-blue-300 text-xs font-medium border border-dashed border-[#2A2A35] hover:border-blue-400 px-3 py-1 rounded-md transition-colors mr-1.5">
                                                + Add
                                            </button>
                                            <!--arrow to indicate collapsible content-->
                                            <svg :class="current_model.showLoras ? 'transform rotate-180' : ''"
                                                class="w-4 h-4 text-gray-400 transition-transform duration-200"
                                                fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                    d="M19 9l-7 7-7-7" />
                                            </svg>
                                        </div>
                                    </div>

                                </div>
                                <!-- LoRA Section -->
                                <div v-if="backendCapabilities.supportsLoras && current_model.showLoras"
                                    class=" mx-2 mb-2 mt-3 space-y-2">
                                    <h3 v-if="current_model.loras.length > 0" class="text-sm text-gray-300 font-medium">
                                        LoRA Models</h3>
                                    <!-- lora -->
                                    <div v-for="(lora, index) in current_model.loras" class="">
                                        <div class="flex items-center justify-between mb-2">
                                            <div class="flex items-center space-x-2">
                                                <img :src="getModelImage(lora, 0)" alt=""
                                                    class="w-12 h-12 rounded object-cover bg-gradient-to-br from-purple-400 to-pink-500"
                                                    @error="handleImageError($event, lora)" />
                                                <span class="text-sm text-[#FAF8F5] font-medium">{{ lora.name }}</span>
                                                <button class="cursor-pointer" @click="OpenLoraData(lora.path)"> <svg
                                                        class="w-4 h-4" fill="none" stroke="currentColor"
                                                        viewBox="0 0 24 24">
                                                        <path stroke-linecap="round" stroke-linejoin="round"
                                                            stroke-width="2"
                                                            d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14">
                                                        </path>
                                                    </svg></button>
                                            </div>
                                            <div class="flex items-center space-x-2">
                                                <button class="text-gray-400 hover:text-[#FAF8F5]"
                                                    @click="current_model.loras.splice(index, 1)">
                                                    <svg class="w-4 h-4" fill="none" stroke="currentColor"
                                                        viewBox="0 0 24 24">
                                                        <path stroke-linecap="round" stroke-linejoin="round"
                                                            stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                                                    </svg>
                                                </button>
                                            </div>
                                        </div>
                                        <div class="flex items-center space-x-2">
                                            <div class="flex-1 relative">
                                                <input type="range" min="0" max="2" step="0.1" v-model="lora.weight"
                                                    class="w-full h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer slider">
                                            </div>
                                            <input type="number" v-model="lora.weight" min="-1" max="2" step="0.1"
                                                class="w-16 bg-[#1A1A24] border border-[#2A2A35] text-xs rounded px-2 py-1 text-center text-[#FAF8F5]">

                                        </div>
                                    </div>
                                    <div v-if="current_model.loras.length == 0" class="text-xs text-gray-400 italic">
                                        No Resources Added.
                                    </div>
                                    <div v-if="current_model.loras_not_found.length > 0" class="mt-3">
                                        <h3 class="text-sm text-red-400 font-medium">LoRA Models Not Found</h3>
                                        <ul class="list-disc list-inside text-xs text-gray-400">
                                            <li v-for="(lora, index) in current_model.loras_not_found" :key="index">{{
                                                lora.name }}</li>
                                        </ul>


                                    </div>
                                </div>
                                </div>
                            </div>
                        </div>

                        <!-- Styles -->
                        <div class="mt-4">
                            <div class="flex items-center justify-between mb-2">
                                <label class="text-sm text-gray-300 font-medium">Styles</label>
                                <div class="flex items-center gap-2">
                                    <button @click="showStyleManager = true"
                                        class="text-xs text-blue-400 hover:text-blue-300">Manage</button>
                                    <button v-if="selectedStyleIds.length > 0" @click="clearSelectedStyles"
                                        class="text-xs text-gray-400 hover:text-[#FAF8F5]">Clear</button>
                                </div>
                            </div>
                            <div v-if="styles.length === 0" class="text-xs text-gray-400 italic">
                                No styles saved yet.
                            </div>
                            <div v-else class="flex flex-wrap gap-2">
                                <button v-for="style in styles" :key="style.id" type="button"
                                    @click="toggleStyleSelection(style.id)"
                                    class="flex items-center gap-2 px-2 py-1 rounded-full border text-xs transition-colors"
                                    :class="selectedStyleIds.includes(style.id)
                                        ? 'bg-blue-600/20 border-blue-500 text-blue-100'
                                        : 'bg-[#1A1A24] border-[#2A2A35] text-gray-300 hover:bg-[#232323]'">
                                    <img :src="style.image || placeholderImage" alt=""
                                        class="w-6 h-6 rounded-full object-cover border border-gray-700" />
                                    <span class="truncate max-w-[140px]">{{ style.name }}</span>
                                </button>
                            </div>
                            <div v-if="selectedStyleTags" class="mt-2 text-xs text-gray-400 break-words hidden">
                                Adds: {{ selectedStyleTags }}
                            </div>
                        </div>



                        <!-- Prompts -->
                        <div>
                            <div class="flex items-center justify-between mb-2">
                                <label class="text-sm text-gray-300 font-medium">Prompt</label>
                                <div class="cursor-pointer ">
                                    <input type="text" v-model="promptEnhanceRequest"
                                        placeholder="Enter your prompt here"
                                        class="hidden w-48 bg-[#232323] border border-[#2A2A35] focus:border-blue-500 text-xs text-[#FAF8F5] px-3 py-1 rounded-lg transition-colors placeholder-gray-500 mr-2" />
                                    <button :title="promptEnhanceInProgress ? 'Enhancing…' : 'AI'"
                                        @click="enhancePrompt()" :disabled="promptEnhanceInProgress"
                                        :class="promptEnhanceInProgress ? 'opacity-60 cursor-not-allowed' : ''">
                                        <template v-if="promptEnhanceInProgress">
                                            <svg class="animate-spin w-5 h-5 text-blue-400" viewBox="0 0 24 24">
                                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                                                    stroke-width="4" />
                                                <path class="opacity-75" fill="currentColor"
                                                    d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                                            </svg>
                                        </template>
                                        <template v-else>
                                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
                                                viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                                stroke-linecap="round" stroke-linejoin="round"
                                                class="lucide lucide-sparkles-icon lucide-sparkles">
                                                <path
                                                    d="M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z" />
                                                <path d="M20 2v4" />
                                                <path d="M22 4h-4" />
                                                <circle cx="4" cy="20" r="2" />
                                            </svg>
                                        </template>
                                    </button>
                                    <button @click="randomizePrompt('local')">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
                                            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                            stroke-linecap="round" stroke-linejoin="round"
                                            class="lucide lucide-dice1-icon lucide-dice-1">
                                            <rect width="18" height="18" x="3" y="3" rx="2" ry="2" />
                                            <path d="M12 12h.01" />
                                        </svg> </button>
                                    <button @click="randomizePrompt('booru')">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
                                            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                            stroke-linecap="round" stroke-linejoin="round"
                                            class="lucide lucide-dice2-icon lucide-dice-2">
                                            <rect width="18" height="18" x="3" y="3" rx="2" ry="2" />
                                            <path d="M15 9h.01" />
                                            <path d="M9 15h.01" />
                                        </svg> </button>
                                    <button @click="randomizePrompt('ai')">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
                                            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                            stroke-linecap="round" stroke-linejoin="round"
                                            class="lucide lucide-dice3-icon lucide-dice-3">
                                            <rect width="18" height="18" x="3" y="3" rx="2" ry="2" />
                                            <path d="M16 8h.01" />
                                            <path d="M12 12h.01" />
                                            <path d="M8 16h.01" />
                                        </svg></button>
                                </div>
                            </div>

                            <div class="bg-[#1A1A24] border border-[#2A2A35] rounded-lg p-3 space-y-1">
                                <div class="relative rounded-lg" @dragenter.prevent="(e) => { showDragOverlay = true; }"
                                    @dragover.prevent @dragleave="(e) => { showDragOverlay = false; }"
                                    @drop.prevent="handlePromptDrop">
                                    <textarea id="positive_prompt" v-model="request.prompt"
                                        placeholder="Your prompt goes here..."
                                        class="positive_prompt w-full text-sm border-[#2A2A35] resize-none focus:outline-none focus:border-blue-500 placeholder-gray-500"
                                        rows="3" ref="positivePrompt" @input="autoResizeTextArea($event.target)" />

                                    <AutoComplete v-model:input="request.prompt" :textareaRef="positivePrompt" />
                                    <div v-if="showDragOverlay"
                                        class="drop-overlay absolute inset-0 z-10 rounded-lg border-2 border-dashed border-blue-400 bg-black/60 backdrop-blur-sm flex items-center justify-center px-4 text-center text-[#FAF8F5] text-sm font-semibold pointer-events-none">
                                        Drop here to Interrogate
                                    </div>
                                </div>

                                <!-- Trigger Words -->
                                <div v-if="triggerWords.length > 0" class="border-t border-[#2A2A35] pt-2">
                                    <label class="text-sm text-gray-300 font-medium block mb-2">Trigger Words</label>
                                    <div class="flex flex-wrap items-center gap-2 mb-2">
                                        <button v-for="(word, index) in triggerWords" :key="index" type="button"
                                            @click="addTriggerWord(word, index)"
                                            class="text-[#FAF8F5] px-2 py-1 rounded text-xs cursor-pointer transition-colors flex items-center gap-1 relative border border-[#2A2A35] hover:bg-purple-700"
                                            :class="request.prompt.includes(word) ? 'bg-purple-500 border-purple-400' : 'bg-[#232323]'">
                                            {{ word }}

                                            <span v-if="copiedIndex === index"
                                                class="absolute -top-6 left-1/2 -translate-x-1/2 bg-black text-[#FAF8F5] text-xs px-1.5 py-0.5 rounded shadow">Copied!</span>
                                        </button>
                                        <button @click="addAllTriggerWords"
                                            class="text-blue-400 hover:text-blue-300 text-xs font-medium px-3 py-1.5 rounded border border-[#2A2A35] hover:border-blue-400 transition-colors">
                                            Add All
                                        </button>
                                        <span v-if="copiedAll"
                                            class="ml-1 text-purple-400 text-xs font-medium">Copied!</span>
                                    </div>
                                </div>

                            </div>

                            <!--<PillPrompt :prompt="request.prompt"/>-->




                            <div class="mt-3">
                                <label class="text-sm text-gray-300 font-medium block mb-2">Negative Prompt</label>
                                <div class="relative rounded-lg">
                                    <input id="negative_prompt" type="text" v-model="request.negative_prompt"
                                        placeholder="Negative Prompt"
                                        class="w-full bg-[#1A1A24] border border-[#2A2A35] text-sm p-3 rounded-lg focus:outline-none focus:border-blue-500 placeholder-gray-500"
                                        ref="negativePrompt" />
                                    <AutoComplete v-model:input="request.negative_prompt"
                                        :textareaRef="negativePrompt" />
                                </div>

                            </div>
                        </div>

                        <!--Image input-->
                        <div>
                            <label class="text-sm text-gray-300 font-medium block mb-2">Img2Img</label>
                            <div class="bg-[#1A1A24] border border-[#2A2A35] rounded-lg">
                                <input ref="imageInputRef" type="file" accept="image/*" class="hidden"
                                    @change="handleImageInputChange" />
                                <div class="relative rounded-lg border border-dashed border-[#2A2A35] p-3 transition-colors cursor-pointer hover:border-blue-500 overflow-hidden"
                                    :class="imageInput.preview ? 'border-transparent min-h-42' : ''"
                                    @click="openImageInputDialog" @dragenter.prevent="showImageDropOverlay = true"
                                    @dragover.prevent @dragleave="showImageDropOverlay = false"
                                    @drop.prevent="handleImageInputDrop">
                                    <div v-if="imageInput.preview"
                                        class="absolute inset-0 bg-cover bg-center z-0"
                                        :style="{
                                            backgroundImage: `url(${imageInput.preview})`,
                                            filter: `blur(${Math.round((img2imgDenoise || 0) * 10)}px)`,
                                            transform: 'scale(1.05)'
                                        }"
                                        aria-hidden="true"></div>
                                    <div v-if="!imageInput.preview" class="flex items-center gap-2 text-gray-400 text-sm">
                                        <Image class="w-5 h-5" />
                                        <p>Drop images here or click to select</p>
                                    </div>
                                    <div v-if="imageInput.preview" class="absolute inset-0 z-10 flex flex-col gap-3 p-3"
                                        @click.stop>
                                        <div class="flex items-start justify-between gap-2">
                                            <div class="bg-black/45 text-xs text-gray-100 px-3 py-2 rounded-lg backdrop-blur-sm">
                                                <p class="text-sm font-semibold text-gray-100">Image2Image</p>
                                                <p class="text-[11px] text-gray-200/80">Transform your image.</p>
                                            </div>
                                            <button type="button" @click.stop="clearImageInput"
                                                class="bg-black/50 text-gray-100 hover:text-white text-xs font-semibold w-8 h-8 rounded-md backdrop-blur-sm flex items-center justify-center">
                                                X
                                            </button>
                                        </div>
                                        <div
                                            class="mt-auto bg-black/45 text-xs text-gray-100 px-3 py-3 rounded-lg backdrop-blur-sm border border-white/10">
                                            <div class="flex items-center justify-between text-xs text-gray-200">
                                                <span>Denoise strength</span>
                                                <span>{{ img2imgDenoise.toFixed(2) }}</span>
                                            </div>
                                            <input type="range" min="0" max="1" step="0.05"
                                                v-model.number="img2imgDenoise" @click.stop
                                                class="mt-2 w-full h-3 bg-white/25 rounded-full appearance-none cursor-pointer slider accent-blue-400"
                                                :style="{ background: `linear-gradient(to right, rgba(59,130,246,0.9) 0%, rgba(59,130,246,0.9) ${img2imgDenoise * 100}%, rgba(255,255,255,0.25) ${img2imgDenoise * 100}%, rgba(255,255,255,0.25) 100%)` }">
                                        </div>
                                    </div>
                                    <div v-if="showImageDropOverlay"
                                        class="drop-overlay absolute inset-0 z-10 rounded-lg border-2 border-dashed border-blue-400 bg-black/60 backdrop-blur-sm flex items-center justify-center px-4 text-center text-[#FAF8F5] text-sm font-semibold pointer-events-none">
                                        Drop image to use as input
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Aspect Ratio -->
                        <div v-if="!compactMode">
                            <label class="text-sm text-gray-300 font-medium block mb-3">Aspect Ratio</label>
                            <div class="bg-[#1A1A24] border border-[#2A2A35] rounded-lg p-1 flex">
                                <button @click="updateAspectRatio('Square')"
                                    :class="aspectRatio === 'Square' ? 'bg-gray-700 text-[#FAF8F5]' : 'text-gray-300 hover:text-[#FAF8F5]'"
                                    class="flex flex-col items-center py-2 px-2 rounded-md text-xs font-medium transition-colors w-full">
                                    <div class="w-4 h-4 border border-current rounded mb-1"></div>
                                    <span>Square</span>
                                    <span class="text-xs opacity-60">1024x1024</span>
                                </button>
                                <button @click="updateAspectRatio('Landscape')"
                                    :class="aspectRatio === 'Landscape' ? 'bg-gray-700 text-[#FAF8F5]' : 'text-gray-300 hover:text-[#FAF8F5]'"
                                    class="flex flex-col items-center py-2 px-2 rounded-md text-xs font-medium transition-colors w-full">
                                    <div class="w-5 h-3 border border-current rounded mb-1"></div>
                                    <span>Landscape</span>
                                    <span class="text-xs opacity-60">1216x832</span>
                                </button>
                                <button @click="updateAspectRatio('Portrait')"
                                    :class="aspectRatio === 'Portrait' ? 'bg-gray-700 text-[#FAF8F5]' : 'text-gray-300 hover:text-[#FAF8F5]'"
                                    class="flex flex-col items-center py-2 px-2 rounded-md text-xs font-medium transition-colors w-full">
                                    <div class="w-3 h-5 border border-current rounded mb-1"></div>
                                    <span>Portrait</span>
                                    <span class="text-xs opacity-60">832x1216</span>
                                </button>
                            </div>
                        </div>



                        <!-- Advanced Section -->
                        <div v-if="!compactMode" class="bg-[#1A1A24] border border-[#2A2A35] rounded-lg">
                            <button @click="showAdvanced = !showAdvanced"
                                class="w-full flex items-center justify-between p-4 text-left">
                                <span class="text-sm font-medium text-gray-300">Advanced</span>
                                <svg :class="{ 'rotate-180': showAdvanced }"
                                    class="w-4 h-4 text-gray-400 transition-transform" fill="none" stroke="currentColor"
                                    viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M19 9l-7 7-7-7" />
                                </svg>
                            </button>

                            <div v-show="showAdvanced" class="px-4 pb-4 space-y-6 border-t border-gray-700">
                                <!-- CFG Scale -->
                                <div class="pt-4">
                                    <div class="flex items-center justify-between mb-2 w-full">
                                        <label class="text-sm font-medium text-gray-300">CFG Scale</label>
                                        <div
                                            class="flex bg-[#1a1a1a] rounded-lg overflow-hidden border border-[#2A2A35]">
                                            <button @click="request.cfg_scale = 4"
                                                :class="request.cfg_scale <= 5 ? 'bg-gray-700 text-[#FAF8F5]' : 'text-gray-400 hover:text-[#FAF8F5] hover:bg-gray-800'"
                                                class="flex-1 py-1 px-2 text-xs font-medium transition-all duration-200 flex items-center justify-center gap-1">
                                                <svg class="w-3 h-3" fill="none" stroke="currentColor"
                                                    viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round"
                                                        stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                                </svg>
                                                Creative
                                            </button>
                                            <button @click="request.cfg_scale = 7"
                                                :class="request.cfg_scale > 5 && request.cfg_scale <= 8 ? 'bg-blue-600 text-[#FAF8F5]' : 'text-gray-400 hover:text-[#FAF8F5] hover:bg-gray-800'"
                                                class="flex-1 py-1 px-2 text-xs font-medium transition-all duration-200 flex items-center justify-center gap-1 border-x border-[#2A2A35]">
                                                <svg class="w-3 h-3" fill="none" stroke="currentColor"
                                                    viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round"
                                                        stroke-width="2"
                                                        d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                                                </svg>
                                                Balanced
                                            </button>
                                            <button @click="request.cfg_scale = 10"
                                                :class="request.cfg_scale > 8 ? 'bg-gray-700 text-[#FAF8F5]' : 'text-gray-400 hover:text-[#FAF8F5] hover:bg-gray-800'"
                                                class="flex-1 py-1 px-2 text-xs font-medium transition-all duration-200 flex items-center justify-center gap-1">
                                                <svg class="w-3 h-3" fill="none" stroke="currentColor"
                                                    viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round"
                                                        stroke-width="2"
                                                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                </svg>
                                                Precise
                                            </button>
                                        </div>
                                    </div>
                                    <div class="flex items-center space-x-3">
                                        <div
                                            class="flex items-center bg-[#1a1a1a] border border-[#2A2A35] rounded-lg overflow-hidden shadow-sm">
                                            <input type="number" min="1" max="10" step="0.5" v-model="request.cfg_scale"
                                                class="bg-transparent text-[#FAF8F5] text-center font-medium w-12 py-2 px-1 focus:outline-none focus:bg-[#1A1A24] transition-colors" />
                                            <div class="flex flex-col border-l border-[#2A2A35]">
                                                <button type="button"
                                                    @click="request.cfg_scale = Math.min(request.cfg_scale + 0.5, 10)"
                                                    class="px-2 py-1 text-xs text-gray-400 hover:text-[#FAF8F5] hover:bg-[#1A1A24] transition-colors">
                                                    <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                                        <path fill-rule="evenodd"
                                                            d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"
                                                            clip-rule="evenodd" />
                                                    </svg>
                                                </button>
                                                <button type="button"
                                                    @click="request.cfg_scale = Math.max(request.cfg_scale - 0.5, 1)"
                                                    class="px-2 py-1 text-xs text-gray-400 hover:text-[#FAF8F5] hover:bg-[#1A1A24] transition-colors border-t border-[#2A2A35]">
                                                    <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                                        <path fill-rule="evenodd"
                                                            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                                                            clip-rule="evenodd" />
                                                    </svg>
                                                </button>
                                            </div>
                                        </div>

                                        <div class="flex-1 relative">
                                            <input type="range" min="1" max="10" step="0.5" v-model="request.cfg_scale"
                                                class="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer slider focus:outline-none    mb-1"
                                                :style="{ background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(request.cfg_scale - 1) / 9 * 100}%, #4b5563 ${(request.cfg_scale - 1) / 9 * 100}%, #4b5563 100%)` }">

                                        </div>
                                    </div>

                                </div>

                                <!-- Sampler -->
                                <div>
                                    <div class="flex items-center justify-between mb-2">
                                        <label class="text-sm font-medium text-gray-300">Sampler</label>
                                        <div
                                            class="flex bg-[#1a1a1a] rounded-lg overflow-hidden border border-[#2A2A35]">
                                            <button @click="request.sampler_name = 'Euler a'"
                                                :class="request.sampler_name === 'Euler a' ? 'bg-blue-600 text-[#FAF8F5]' : 'text-gray-400 hover:text-[#FAF8F5] hover:bg-gray-800'"
                                                class="flex-1 py-1 px-2 text-xs font-medium transition-all duration-200 flex items-center justify-center gap-1">
                                                <svg class="w-3 h-3" fill="none" stroke="currentColor"
                                                    viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round"
                                                        stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                                </svg>
                                                Fast
                                            </button>
                                            <button @click="request.sampler_name = 'DPM++ 2M'"
                                                :class="request.sampler_name === 'DPM++ 2M' ? 'bg-blue-600 text-[#FAF8F5]' : 'text-gray-400 hover:text-[#FAF8F5] hover:bg-gray-800'"
                                                class="flex-1 py-1 px-2 text-xs font-medium transition-all duration-200 flex items-center justify-center gap-1 border-x border-[#2A2A35]">
                                                <svg class="w-3 h-3" fill="none" stroke="currentColor"
                                                    viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round"
                                                        stroke-width="2"
                                                        d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                                                </svg>
                                                Popular
                                            </button>
                                        </div>
                                    </div>
                                    <div v-if="defaultStyles[current_model.model.model_name]?.override_sampler">
                                        <div
                                            class="flex items-center bg-[#1a1a1a] border border-[#2A2A35] text-sm rounded-lg px-3 py-2">
                                            <span class="flex-1">
                                                {{
                                                    defaultStyles[current_model.model.model_name]?.override_sampler
                                                }}
                                            </span>

                                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                                                stroke-width="1.5" stroke="currentColor"
                                                class="w-4 h-4 text-gray-400 ml-2">
                                                <path stroke-linecap="round" stroke-linejoin="round"
                                                    d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
                                            </svg>

                                        </div>
                                    </div>
                                    <div v-else>
                                        <select v-model="request.sampler_name"
                                            class="w-full bg-[#1a1a1a] border border-[#2A2A35] text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500">
                                            <option v-for="sampler in samplers" :key="sampler.name"
                                                :value="sampler.name">{{ sampler.name }}
                                            </option>
                                        </select>
                                    </div>
                                </div>

                                <!-- Steps -->
                                <div>
                                    <div class="flex items-center justify-between mb-2">
                                        <label class="text-sm font-medium text-gray-300">Steps</label>
                                        <div
                                            class="flex bg-[#1a1a1a] rounded-lg overflow-hidden border border-[#2A2A35]">
                                            <button @click="request.steps = 14"
                                                :class="request.steps <= 14 ? 'bg-gray-700 text-[#FAF8F5]' : 'text-gray-400 hover:text-[#FAF8F5] hover:bg-gray-800'"
                                                class="flex-1 py-1 px-2 text-xs font-medium transition-all duration-200 flex items-center justify-center gap-1">
                                                <svg class="w-3 h-3" fill="none" stroke="currentColor"
                                                    viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round"
                                                        stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                                </svg>
                                                Fast
                                            </button>
                                            <button @click="request.steps = 24"
                                                :class="request.steps > 14 && request.steps <= 33 ? 'bg-blue-600 text-[#FAF8F5]' : 'text-gray-400 hover:text-[#FAF8F5] hover:bg-gray-800'"
                                                class="flex-1 py-1 px-2 text-xs font-medium transition-all duration-200 flex items-center justify-center gap-1 border-x border-[#2A2A35]">
                                                <svg class="w-3 h-3" fill="none" stroke="currentColor"
                                                    viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round"
                                                        stroke-width="2"
                                                        d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                                                </svg>
                                                Balanced
                                            </button>
                                            <button @click="request.steps = 34"
                                                :class="request.steps > 33 ? 'bg-gray-700 text-[#FAF8F5]' : 'text-gray-400 hover:text-[#FAF8F5] hover:bg-gray-800'"
                                                class="flex-1 py-1 px-2 text-xs font-medium transition-all duration-200 flex items-center justify-center gap-1">
                                                <svg class="w-3 h-3" fill="none" stroke="currentColor"
                                                    viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round"
                                                        stroke-width="2"
                                                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                </svg>
                                                High
                                            </button>
                                        </div>
                                    </div>
                                    <div class="flex items-center space-x-3">
                                        <div
                                            class="flex items-center bg-[#1a1a1a] border border-[#2A2A35] rounded-lg overflow-hidden shadow-sm">
                                            <input type="number" min="1" max="50" v-model="request.steps"
                                                class="bg-transparent text-[#FAF8F5] text-center font-medium w-12 py-2 px-1 focus:outline-none focus:bg-[#1A1A24] transition-colors" />
                                            <div class="flex flex-col border-l border-[#2A2A35]">
                                                <button type="button"
                                                    @click="request.steps = Math.min(request.steps + 1, 50)"
                                                    class="px-2 py-1 text-xs text-gray-400 hover:text-[#FAF8F5] hover:bg-[#1A1A24] transition-colors">
                                                    <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                                        <path fill-rule="evenodd"
                                                            d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"
                                                            clip-rule="evenodd" />
                                                    </svg>
                                                </button>
                                                <button type="button"
                                                    @click="request.steps = Math.max(request.steps - 1, 1)"
                                                    class="px-2 py-1 text-xs text-gray-400 hover:text-[#FAF8F5] hover:bg-[#1A1A24] transition-colors border-t border-[#2A2A35]">
                                                    <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                                        <path fill-rule="evenodd"
                                                            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                                                            clip-rule="evenodd" />
                                                    </svg>
                                                </button>
                                            </div>
                                        </div>

                                        <div class="flex-1 relative">
                                            <input type="range" min="1" max="50" v-model="request.steps"
                                                class="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer slider focus:outline-none mb-1"
                                                :style="{ background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(request.steps - 1) / 49 * 100}%, #4b5563 ${(request.steps - 1) / 49 * 100}%, #4b5563 100%)` }">
                                        </div>
                                    </div>
                                </div>

                                <!-- Seed -->
                                <div>
                                    <div class="flex items-center justify-between mb-3">
                                        <label class="text-sm font-medium text-gray-300">Seed</label>
                                        <div
                                            class="flex bg-[#1a1a1a] rounded-lg overflow-hidden border border-[#2A2A35]">
                                            <button @click="request.seed = -1"
                                                :class="request.seed === -1 ? 'bg-blue-600 text-[#FAF8F5]' : 'text-gray-400 hover:text-[#FAF8F5] hover:bg-gray-800'"
                                                class="flex-1 py-1 px-2 text-xs font-medium transition-all duration-200 flex items-center justify-center gap-1">
                                                <svg class="w-3 h-3" fill="none" stroke="currentColor"
                                                    viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round"
                                                        stroke-width="2"
                                                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                                </svg>
                                                Random
                                            </button>
                                            <button
                                                @click="request.seed = request.seed === -1 ? Math.floor(Math.random() * 4294967295) : request.seed"
                                                :class="request.seed !== -1 ? 'bg-gray-700 text-[#FAF8F5]' : 'text-gray-400 hover:text-[#FAF8F5] hover:bg-gray-800'"
                                                class="flex-1 py-1 px-2 text-xs font-medium transition-all duration-200 flex items-center justify-center gap-1">
                                                <svg class="w-3 h-3" fill="none" stroke="currentColor"
                                                    viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round"
                                                        stroke-width="2"
                                                        d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
                                                </svg>
                                                Fixed
                                            </button>
                                        </div>
                                    </div>

                                    <div class="space-y-3">
                                        <!-- Seed Input (when fixed mode is selected) -->
                                        <div v-if="request.seed !== -1" class="relative">
                                            <input type="number" v-model="request.seed" min="0" max="4294967295"
                                                step="1" placeholder="Enter seed value (0-4294967295)"
                                                class="w-full bg-[#1a1a1a] border border-[#2A2A35] text-sm text-[#FAF8F5] px-3 py-2.5 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 transition-all placeholder-gray-500 pr-20" />

                                            <!-- Quick Action Buttons -->
                                            <div class="absolute right-2 top-2 flex space-x-1">
                                                <button @click="request.seed = Math.floor(Math.random() * 4294967295)"
                                                    class="bg-gray-700 hover:bg-gray-600 text-gray-300 hover:text-[#FAF8F5] p-1.5 rounded text-xs transition-colors"
                                                    title="Generate random seed">
                                                    <svg class="w-3 h-3" fill="none" stroke="currentColor"
                                                        viewBox="0 0 24 24">
                                                        <path stroke-linecap="round" stroke-linejoin="round"
                                                            stroke-width="2"
                                                            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                                    </svg>
                                                </button>
                                                <button @click="navigator.clipboard.writeText(request.seed.toString())"
                                                    class="bg-gray-700 hover:bg-gray-600 text-gray-300 hover:text-[#FAF8F5] p-1.5 rounded text-xs transition-colors"
                                                    title="Copy seed">
                                                    <svg class="w-3 h-3" fill="none" stroke="currentColor"
                                                        viewBox="0 0 24 24">
                                                        <path stroke-linecap="round" stroke-linejoin="round"
                                                            stroke-width="2"
                                                            d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                                    </svg>
                                                </button>
                                            </div>
                                        </div>

                                        <!-- Random Seed Display -->
                                        <div v-else
                                            class="bg-[#1a1a1a] border border-[#2A2A35] rounded-lg px-3 py-2.5 flex items-center justify-between">
                                            <div class="flex items-center gap-2 text-gray-400">
                                                <span class="text-sm">Random seed will be generated</span>
                                            </div>
                                            <div class="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded font-mono">
                                                Auto
                                            </div>
                                        </div>

                                        <!-- Seed Info -->
                                        <div class="text-xs text-gray-500 flex items-start gap-2">
                                            <svg class="w-3 h-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor"
                                                viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                            </svg>
                                            <span class="leading-relaxed">
                                                Use the same seed to reproduce identical results. Random mode generates
                                                a different image each time.
                                            </span>
                                        </div>
                                    </div>

                                </div>
                                <!-- Adetailer -->
                                <div v-if="adetailerAvailable && !compactMode"
                                    class="flex items-center justify-between ">
                                    <div class="flex items-center space-x-2">
                                        <label class="text-sm text-gray-300 font-medium">ADetailer</label>
                                    </div>
                                    <label class="relative inline-flex items-center cursor-pointer">
                                        <input type="checkbox" v-model="current_model.adetailer" class="sr-only peer">
                                        <div
                                            class="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600">
                                        </div>
                                    </label>
                                </div>

                                <!-- Block Cache -->
                                <div v-if="blockCacheAvailable && !compactMode" class="space-y-3 mt-4">
                                    <div class="flex items-center justify-between">
                                        <div class="flex items-center space-x-2">
                                            <label class="text-sm text-gray-300 font-medium">First Block Cache /
                                                TeaCache</label>
                                        </div>
                                        <label class="relative inline-flex items-center cursor-pointer">
                                            <input type="checkbox" v-model="current_model.blockCache"
                                                class="sr-only peer">
                                            <div
                                                class="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600">
                                            </div>
                                        </label>
                                    </div>
                                    <div v-if="current_model.blockCache" class="space-y-4 pt-2">
                                        <div class="flex items-center justify-between w-full">
                                            <label class="text-sm text-gray-400 font-medium">Method</label>
                                            <div
                                                class="flex bg-[#1a1a1a] rounded-lg overflow-hidden border border-[#2A2A35]">
                                                <button @click="current_model.blockCacheMethod = 'First Block Cache'"
                                                    :class="(!current_model.blockCacheMethod || current_model.blockCacheMethod === 'First Block Cache') ? 'bg-blue-600 text-[#FAF8F5]' : 'text-gray-400 hover:text-[#FAF8F5] hover:bg-gray-800'"
                                                    class="flex-1 py-1 px-3 text-xs font-medium transition-all duration-200 flex items-center justify-center">
                                                    First Block Cache
                                                </button>
                                                <button @click="current_model.blockCacheMethod = 'TeaCache'"
                                                    :class="current_model.blockCacheMethod === 'TeaCache' ? 'bg-blue-600 text-[#FAF8F5]' : 'text-gray-400 hover:text-[#FAF8F5] hover:bg-gray-800'"
                                                    class="flex-1 py-1 px-3 text-xs font-medium transition-all duration-200 flex items-center justify-center border-l border-[#2A2A35]">
                                                    TeaCache
                                                </button>
                                            </div>
                                        </div>
                                        <div>
                                            <label
                                                class="text-sm text-gray-400 font-medium block mb-2">Threshold</label>
                                            <div class="flex items-center space-x-3 w-full">
                                                <div
                                                    class="flex items-center bg-[#1a1a1a] border border-[#2A2A35] rounded-lg overflow-hidden shadow-sm">
                                                    <input type="number" step="0.01" min="0" max="1"
                                                        v-model="current_model.blockCacheThreshold"
                                                        class="bg-transparent text-[#FAF8F5] text-center font-medium w-16 py-1.5 px-1 focus:outline-none focus:bg-[#1A1A24] transition-colors"
                                                        placeholder="0.1" />
                                                </div>
                                                <div class="flex-1 relative">
                                                    <input type="range" min="0" max="1" step="0.01"
                                                        v-model="current_model.blockCacheThreshold"
                                                        class="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer slider focus:outline-none mb-1"
                                                        :style="{ background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(current_model.blockCacheThreshold !== undefined ? current_model.blockCacheThreshold : 0.1) * 100}%, #4b5563 ${(current_model.blockCacheThreshold !== undefined ? current_model.blockCacheThreshold : 0.1) * 100}%, #4b5563 100%)` }">
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!--Preview-->
                        <div class="bg-[#1A1A24] border border-[#2A2A35] rounded-lg p-4">
                            <h3 class="text-sm font-medium text-gray-300 mb-2">Preview</h3>

                            <img @click="showFullscreen([`data:image/png;base64,${history[history.length - 1].images[0]}`])"
                                v-if="generationState.current_image || history.length > 0" :src="generationState.current_image
                                    ? `data:image/png;base64,${generationState.current_image}`
                                    : `data:image/png;base64,${history[history.length - 1].images[0]}`"
                                :alt="generationState.current_image ? 'Generated Preview' : 'Image URL Preview'"
                                class="h-96 w-full object-contain rounded-lg" />

                            <div v-else class="flex items-center justify-center h-48">
                                <span class="text-gray-400">No preview available</span>
                            </div>
                        </div>

                    </div>



                    <!-- Fixed Bottom Section -->
                    <div class="flex-shrink-0 border-t border-[#2A2A35] p-4 bg-[#1A1A24] rounded-t-lg">
                        <div class="flex items-center justify-between mb-4">
                            <div class="flex items-center space-x-2 w-full">
                                <template v-if="isGenerating">
                                    <span class="text-blue-400 text-sm">⚡ Generating...</span>
                                    <div class="flex-1 bg-gray-600 rounded-full h-2 overflow-hidden mx-2">
                                        <div class="bg-blue-500 h-full transition-all duration-300 ease-out relative overflow-hidden"
                                            :style="{ width: `${Math.round(generationProgress * 100)}%` }">
                                            <div class="absolute inset-0 w-full bg-gradient-to-r from-transparent via-white/30 to-transparent"
                                                style="animation: shimmer 1.5s infinite;"></div>
                                            <component :is="'style'">
                                                @keyframes shimmer {
                                                0% { transform: translateX(-100%); }
                                                100% { transform: translateX(100%); }
                                                }
                                            </component>
                                        </div>
                                    </div>
                                    <span class="text-gray-400 text-xs">
                                        {{ generationState.sampling_step || 0 }}/{{ generationState.sampling_steps || 0
                                        }}
                                    </span>
                                    <span class="text-gray-400 text-xs ml-2">
                                        {{ Math.round(generationProgress * 100) }}%
                                    </span>
                                    <span class="text-gray-400 text-xs ml-2">
                                        {{ generationQueue.length }} in queue
                                    </span>
                                </template>
                                <template v-else>
                                    <span class="text-gray-400 text-sm">
                                        No active generation
                                    </span>
                                </template>
                            </div>
                        </div>

                        <!-- Quantity -->
                        <div class="flex items-center justify-between mb-4">
                            <span class="text-sm text-gray-300 font-medium">Quantity</span>
                            <select v-model="request.batch_size"
                                class="bg-[#1A1A24] border border-[#2A2A35] text-sm rounded px-2 py-1 focus:outline-none focus:border-blue-500">
                                <option :value="1">1</option>
                                <option :value="2">2</option>
                                <option :value="3">3</option>
                                <option :value="4">4</option>
                            </select>
                        </div>

                        <!-- Generate Button -->
                        <div class="flex space-x-2 relative  items-stretch group-hover:z-50">
                            <!-- Generate Button -->
                            <button @click="GenerateImage" :disabled="!webState.backendAvailable"
                                :class="!webState.backendAvailable ? 'bg-gray-700 text-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-white'"
                                class="flex-1 py-3 rounded-lg font-semibold text-sm transition-colors flex items-center justify-center shadow-lg">
                                <span>{{ isGenerating ? 'Add to Queue' : 'Generate' }}</span>
                                <div
                                    class="flex items-center bg-black/20 px-2 py-0.5 ml-2 mt-0.5 rounded text-xs font-bold font-mono">
                                    <svg class="w-3.5 h-3.5 mr-1 text-white" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M13 10V3L4 14h7v7l9-11h-7z" />
                                    </svg>
                                    {{ calculateCost(request) }}
                                </div>
                            </button>

                            <div class="group">
                                <!-- Hover Tooltip/Popover -->
                                <div
                                    class="absolute bottom-full right-0 mb-3 w-[320px] bg-[#1C1C22] border border-[#2A2A35] rounded-lg shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-[100] text-sm text-[#FAF8F5] overflow-hidden pointer-events-none">
                                    <div
                                        class="flex justify-between items-center p-3 border-b border-[#2A2A35] bg-[#1C1C22] text-gray-300">
                                        <h4 class="font-medium text-sm">Generation Cost Breakdown</h4>
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                    </div>
                                    <div class="flex flex-col text-gray-300 bg-[#1C1C22]">

                                        <div v-if="request.batch_size * request.n_iter != 1"
                                            class="flex justify-between items-center px-4 py-3 border-b border-[#2A2A35]">
                                            <span>Quantity</span>
                                            <span class="font-mono text-gray-200">{{ request.batch_size * request.n_iter
                                            }}x</span>
                                        </div>
                                        <div
                                            class="flex justify-between items-center px-4 py-3 border-b border-[#2A2A35]">
                                            <span>Size</span>
                                            <span class="font-mono text-gray-200">{{ formatSizeMultiplier(request)
                                            }}x</span>
                                        </div>
                                        <div
                                            class="flex justify-between items-center px-4 py-3 border-b border-[#2A2A35]">
                                            <span>Steps</span>
                                            <span class="font-mono text-gray-200">{{ formatStepsPercentage(request)
                                            }}</span>
                                        </div>
                                        <div v-if="formatSamplerPercentage(request) != '0%'"
                                            class="flex justify-between items-center px-4 py-3 border-b border-[#2A2A35]">
                                            <span>Sampler</span>
                                            <span class="font-mono text-gray-200">{{ formatSamplerPercentage(request)
                                            }}</span>
                                        </div>
                                        <!-- Base Cost -->
                                        <div
                                            class="flex justify-between items-center px-4 py-4 border-b border-[#2A2A35] bg-[#22222b]">
                                            <span class="font-bold text-[#FAF8F5]">Base Cost</span>
                                            <div class="flex items-center font-bold text-base text-[#FAF8F5]">
                                                {{ calculateCost(request) - calculateAdditionalCost(request) }}
                                                <svg class="w-4 h-4 ml-1 text-[#3b82f6]" fill="currentColor"
                                                    viewBox="0 0 24 24">
                                                    <path d="M13 10V3L4 14h7v7l9-11h-7z" />
                                                </svg>
                                            </div>
                                        </div>
                                        <div
                                            class="flex justify-between items-center px-4 py-4 border-b border-[#2A2A35] bg-[#1A1A24]">
                                            <span class="text-gray-300">Additional Resource Cost</span>
                                            <div class="flex items-center text-sm font-medium text-gray-200">
                                                {{ calculateAdditionalCost(request) }}
                                                <svg class="w-4 h-4 ml-1 text-[#3b82f6]" fill="currentColor"
                                                    viewBox="0 0 24 24">
                                                    <path d="M13 10V3L4 14h7v7l9-11h-7z" />
                                                </svg>
                                            </div>
                                        </div>
                                        <div class="flex justify-between items-center px-4 py-4 bg-[#1C1C22]">
                                            <span class="text-gray-300 font-medium">Total Spent</span>
                                            <div class="flex items-center text-sm font-bold text-gray-200">
                                                {{ Math.round(generationCosts?.totalCosts || 0) }}
                                                <svg class="w-4 h-4 ml-1 text-[#3b82f6]" fill="currentColor"
                                                    viewBox="0 0 24 24">
                                                    <path d="M13 10V3L4 14h7v7l9-11h-7z" />
                                                </svg>
                                                {{ generationCosts?.allTimeCost?.toLocaleString() }}
                                                <svg class="w-4 h-4 ml-1 text-[#3b82f6]" fill="currentColor"
                                                    viewBox="0 0 24 24">
                                                    <path d="M13 10V3L4 14h7v7l9-11h-7z" />
                                                </svg>
                                            </div>
                                        </div>

                                    </div>
                                </div>


                            </div>



                            <button v-if="isGenerating" @click="cancelGeneration"
                                class="bg-[#1A1A24] border border-[#2A2A35] hover:bg-gray-700 font-semibold px-4 rounded-lg text-sm transition-colors flex items-center justify-center">
                                Cancel
                            </button>
                            <button v-else @click="resetSettings" :disabled="isGenerating"
                                class="bg-[#1A1A24] border border-[#2A2A35] hover:bg-gray-700 font-semibold px-4 rounded-lg text-sm transition-colors flex items-center justify-center">
                                Reset
                            </button>
                        </div>
                    </div>
                </div>

                <!-- History Tab Content (only show in sidebar when not fullscreen) -->
                <div v-show="activeTab === 'history' && !isFullscreen" class="flex-1 flex flex-col min-h-0">
                    <div class="flex-1 overflow-y-auto p-4">

                        <!-- Current Generation (if generating) -->
                        <div v-if="isGenerating"
                            class="bg-blue-900/20 border border-blue-500/30 rounded-lg overflow-hidden mb-2">
                            <div class="p-3">
                                <div class="flex items-center justify-between mb-3">
                                    <div class="flex items-center space-x-2">
                                        <div class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                                        <span class="text-sm font-medium text-blue-400">Generating...</span>
                                    </div>
                                    <span class="text-xs text-gray-400">
                                        {{ Math.round(generationProgress * 100) }}%
                                    </span>
                                </div>

                                <!-- Progress Bar -->
                                <div class="mb-3">
                                    <div class="flex justify-between text-xs text-gray-400 mb-1">
                                        <span>Step {{ generationState.sampling_step || 0 }}/{{
                                            generationState.sampling_steps || 0
                                            }}</span>
                                        <span>{{ generationState.job || 'Processing' }}</span>
                                    </div>
                                    <div class="bg-gray-700 rounded-full h-2 overflow-hidden">
                                        <div class="bg-blue-500 h-full transition-all duration-300 ease-out"
                                            :style="{ width: `${Math.round(generationProgress * 100)}%` }"></div>
                                    </div>
                                </div>

                                <!-- Current Prompt -->
                                <div class="mb-3">
                                    <p class="text-sm text-gray-200 leading-relaxed">{{ request.prompt }}</p>
                                    <p v-if="request.negative_prompt" class="text-xs text-gray-400 mt-2 italic">
                                        Negative: {{ request.negative_prompt }}
                                    </p>
                                </div>

                                <!-- Preview Image if available -->
                                <div class="mb-3">
                                    <img :src="`data:image/png;base64,${generationState.current_image}`"
                                        alt="Generation preview" class="rounded-lg opacity-80 h-80" />
                                    <p class="text-xs text-gray-500 mt-1 text-center">Live Preview</p>
                                </div>

                                <!-- Generation Settings Summary -->
                                <div class="text-xs text-gray-400 space-y-1">
                                    <div class="flex justify-between">
                                        <span>Model:</span>
                                        <span>{{ current_model.model.model_name || 'Unknown' }}</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>Size:</span>
                                        <span>{{ request.width }}×{{ request.height }}</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>CFG Scale:</span>
                                        <span>{{ request.cfg_scale }}</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>Sampler:</span>
                                        <span>{{ request.sampler_name }}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div v-if="history.length == 0" class="text-center text-gray-400 py-12">
                            <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor"
                                viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <h3 class="text-lg font-medium mb-2">No Generation History</h3>
                            <p class="text-sm">Your generated images will appear here</p>
                        </div>

                        <!-- History Items -->
                        <div v-if="activeTab == 'history'" class="space-y-4">



                            <div v-for="(item, index) in history.slice().reverse()" :key="index"
                                class="bg-[#1A1A24] border border-[#2A2A35] rounded-lg overflow-hidden">

                                <!-- Prompt Info -->
                                <div class="p-3 pb-2">
                                    <div class="mb-3">
                                        <p class="text-sm text-gray-200 leading-relaxed">{{ item.request.prompt }}</p>
                                        <p v-if="item.request.negative_prompt"
                                            class="text-xs text-gray-400 mt-2 italic">
                                            Negative: {{ item.request.negative_prompt }}
                                        </p>
                                    </div>
                                </div>

                                <!-- Image Grid -->
                                <div class="px-3 pb-3">
                                    <div class="flex gap-2 mb-2 overflow-auto">
                                        <div v-for="(image, imgIndex) in item.images" class="relative">
                                            <img @click="showFullscreen([`data:image/png;base64,${image}`])"
                                                :key="imgIndex" :src="`data:image/png;base64,${image}`"
                                                alt="Generated image"
                                                class="object-cover cursor-pointer transition-transform duration-300 h-64 ml-2 mb-2 rounded-lg shadow-md shadow-gray-800" />
                                            <RouterLink v-if="item.id" :to="`/image/${item.id + imgIndex + 1}`"
                                                @click="isFullscreen = false"
                                                class="absolute top-2 right-2 bg-gray-900/80 hover:bg-blue-600 text-[#FAF8F5] rounded-full p-2 shadow transition"
                                                title="Open image in new tab">
                                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                                                    stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                                                    <path stroke-linecap="round" stroke-linejoin="round"
                                                        d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                                                </svg>
                                            </RouterLink>
                                        </div>
                                    </div>

                                    <!-- Action Buttons -->
                                    <div class="flex space-x-2">
                                        <button @click="loadFromHistory(item.request)"
                                            class="flex-1 bg-blue-600 hover:bg-blue-700 text-[#FAF8F5] text-xs font-medium py-2 px-3 rounded-lg transition-colors">
                                            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor"
                                                viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                                            </svg>
                                            Use Settings
                                        </button>
                                        <button @click="downloadImages(item.images)"
                                            class="bg-[#1a1a1a] hover:bg-gray-700 border border-[#2A2A35] text-gray-300 hover:text-[#FAF8F5] text-xs font-medium py-2 px-3 rounded-lg transition-colors">
                                            <svg class="w-4 h-4 inline" fill="none" stroke="currentColor"
                                                viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                    d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                            </svg>
                                        </button>
                                        <button @click="deleteHistoryItem(history.length - 1 - index)"
                                            class="bg-red-600 hover:bg-red-700 text-[#FAF8F5] text-xs font-medium py-2 px-3 rounded-lg transition-colors">
                                            <svg class="w-4 h-4 inline" fill="none" stroke="currentColor"
                                                viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                            </svg>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- History Actions -->
                    <div v-if="history.length > 0" class="flex-shrink-0 border-t border-gray-700 p-4 bg-[#1a1a1a]">
                        <button @click="clearHistory"
                            class="w-full bg-red-600 hover:bg-red-700 text-[#FAF8F5] text-sm font-medium py-2 px-4 rounded-lg transition-colors">
                            Clear All History
                        </button>
                    </div>
                </div>

                <div v-if="activeTab == 'gallery' && !isFullscreen" class="flex-1 overflow-y-auto px-2 py-4">
                    {{ }}
                    <div class="grid grid-cols-2 gap-2">
                        <img v-if="generationState?.current_image && isGenerating"
                            :src="'data:image/png;base64,' + generationState.current_image" alt=""
                            class="w-full shadow-lg hover:shadow-xl transition-shadow rounded-lg" />
                        <div v-for="(item, index) in getAllHistoryImages()" :key="index"
                            class="group bg-[#181818] overflow-hidden relative ">
                            <img @click="showFullscreen([`data:image/png;base64,${item.image}`])"
                                :src="'data:image/png;base64,' + item.image" alt=""
                                class="w-full shadow-lg hover:shadow-xl transition-shadow rounded-lg" />
                            <RouterLink v-if="item.id && item.id != 1" :to="`/image/${item.id}`"
                                @click="isFullscreen = false"
                                class="absolute top-2 right-2 bg-gray-900/80 hover:bg-blue-600 text-[#FAF8F5] rounded-full p-2 shadow transition"
                                title="Open image in new tab">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                                    stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                                    <path stroke-linecap="round" stroke-linejoin="round"
                                        d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                                </svg>
                            </RouterLink>
                        </div>
                    </div>
                </div>

                <div v-if="activeTab == 'chat' && !isFullscreen" class="flex-1 flex flex-col min-h-0">
                    <ChatPanel :history="chatHistory" />
                </div>

                <div v-if="activeTab == 'settings' && !isFullscreen" class="flex-1 overflow-y-auto p-4">
                    <BackendSettingsPanel />
                </div>
            </div>

        </div>

        <div v-if="isFullscreen && activeTab == 'chat'" class="flex-1 flex flex-col min-h-0">
            <ChatPanel :history="chatHistory" />
        </div>

        <!-- Fullscreen History Gallery -->
        <div v-else-if="isFullscreen" class="flex-1 bg-[#0a0a0a] flex flex-col">
            <div class="border-b border-gray-700 px-8 py-6">
                <h2 class="text-3xl font-bold text-[#FAF8F5] mb-1">Generation History</h2>
            </div>



            <div v-if="activeTab == 'history'" class="flex-1 overflow-y-auto px-8 py-6">
                <!-- Current Generation Preview in Fullscreen -->
                <div v-if="isGenerating" class="mb-8 max-w-2xl mx-auto ">
                    <div class="relative rounded-2xl overflow-hidden shadow-2xl bg-black">
                        <!-- No image yet placeholder -->
                        <div v-if="!generationState.current_image"
                            class="flex flex-col items-center justify-center min-h-[480px] text-gray-500">
                            <svg class="w-16 h-16 mb-3 opacity-30 animate-pulse" fill="none" stroke="currentColor"
                                viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            <p class="text-sm">Waiting for first step…</p>
                        </div>

                        <!-- Image with b&w→color reveal bottom-to-top -->
                        <template v-if="generationState.current_image">
                            <!-- Grayscale base (always fully visible) -->
                            <img :src="`data:image/png;base64,${generationState.current_image}`"
                                alt="Generation preview" class="w-full object-contain max-h-[60vh] "
                                style="filter: grayscale(100%) brightness(0.9);" />
                            <!-- Color layer revealed from bottom to top -->
                            <img :src="`data:image/png;base64,${generationState.current_image}`" alt=""
                                class="absolute inset-0 w-full object-contain max-h-[60vh]"
                                :style="{ clipPath: `inset(${100 - Math.round(generationProgress * 100)}% 0 0 0)`, transition: 'clip-path 0.3s ease-out' }" />
                        </template>

                        <!-- Progress overlay pinned to bottom -->
                        <div
                            class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent px-5 pt-10 pb-4">
                            <div class="flex items-center justify-between text-[#FAF8F5] text-sm mb-2">
                                <div class="flex items-center gap-2">
                                    <div class="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></div>
                                    <span class="font-medium">Step {{ generationState.sampling_step || 0 }}/{{
                                        generationState.sampling_steps || 0 }}</span>
                                </div>
                                <span class="font-semibold tabular-nums">{{ Math.round(generationProgress * 100)
                                }}%</span>
                            </div>
                            <div class="bg-white/20 rounded-full h-1 overflow-hidden">
                                <div class="bg-blue-400 h-full transition-all duration-300 ease-out"
                                    :style="{ width: `${Math.round(generationProgress * 100)}%` }"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <div v-if="history.length == 0" class="flex flex-col items-center justify-center h-full text-gray-400">
                    <svg class="w-24 h-24 mb-6 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <h3 class="text-2xl font-semibold mb-2">No History Yet</h3>
                    <p class="text-base text-gray-500">Your generated images will appear here</p>
                </div>

                <div v-else class="">



                    <div v-for="(item, index) in history.slice().reverse()" :key="item.id ?? item.timestamp ?? index"
                        class="group bg-[#181818] rounded-xl overflow-hidden relative shadow-lg hover:shadow-xl transition-shadow mb-3 border border-white/5">

                        <!-- Header / Prompt -->
                        <div class="p-4 border-b border-white/5">
                            <div class="flex items-start justify-between gap-3">
                                <div class="min-w-0 flex-1">
                                    <p class="text-sm font-semibold text-[#FAF8F5] line-clamp-2 break-words"
                                        :title="item.request?.prompt || ''">
                                        {{ item.request?.prompt || 'No prompt' }}
                                    </p>
                                    <p v-if="item.request?.negative_prompt"
                                        class="mt-1 text-xs italic text-gray-400 line-clamp-1 break-words"
                                        :title="item.request?.negative_prompt || ''">
                                        Negative: {{ item.request?.negative_prompt }}
                                    </p>
                                </div>

                                <div class="flex flex-col items-end text-[11px] text-gray-400 whitespace-nowrap">
                                    <span v-if="item.timestamp">{{ new Date(item.timestamp).toLocaleString() }}</span>
                                    <span class="mt-1 px-2 py-0.5 rounded-full bg-black/40 border border-white/10">
                                        {{ (item.images?.length || 0) }} image{{ (item.images?.length || 0) === 1 ? '' :
                                            's' }}
                                    </span>
                                </div>
                            </div>

                            <!-- Quick stats -->
                            <div class="mt-3 flex flex-wrap gap-2 text-[11px] text-gray-300">
                                <span class="px-2 py-1 rounded-md bg-black/30 border border-white/10">
                                    {{ item.request?.width }}×{{ item.request?.height }}
                                </span>
                                <span class="px-2 py-1 rounded-md bg-black/30 border border-white/10">
                                    Steps: {{ item.request?.steps }}
                                </span>
                                <span class="px-2 py-1 rounded-md bg-black/30 border border-white/10">
                                    CFG: {{ item.request?.cfg_scale }}
                                </span>
                                <span class="px-2 py-1 rounded-md bg-black/30 border border-white/10">
                                    {{ item.request?.sampler_name }}
                                </span>
                                <span class="px-2 py-1 rounded-md bg-black/30 border border-white/10">
                                    Seed: {{ item.request?.seed }}
                                </span>
                            </div>
                        </div>

                        <!-- Images -->
                        <div class="relative p-3">
                            <div class="flex gap-3 overflow-x-auto pb-2 snap-x snap-mandatory">
                                <div v-for="(image, imgIndex) in (item.images || [])"
                                    :key="`${item.id ?? item.timestamp ?? index}-${imgIndex}`"
                                    class="relative flex-shrink-0 snap-start">

                                    <img @click="showFullscreen([`data:image/png;base64,${image}`])"
                                        :src="`data:image/png;base64,${image}`" :alt="`Generated image ${imgIndex + 1}`"
                                        loading="lazy" decoding="async"
                                        class="h-[30rem] w-auto rounded-lg object-cover bg-black/30 ring-1 ring-white/10 shadow-md shadow-black/40 transition-transform duration-300 group-hover:scale-[1.01]" />

                                    <!-- Index badge -->
                                    <div
                                        class="absolute bottom-2 left-2 bg-black/70 text-[#FAF8F5] text-[11px] px-2 py-1 rounded-md border border-white/10">
                                        #{{ imgIndex + 1 }}
                                    </div>

                                    <!-- Open link -->
                                    <RouterLink v-if="item.id" :to="`/image/${item.id + imgIndex + 1}`"
                                        @click="isFullscreen = false"
                                        class="absolute top-2 right-2 bg-gray-900/80 hover:bg-blue-600 text-[#FAF8F5] rounded-full p-2 shadow transition"
                                        title="Open image in new tab" aria-label="Open image">
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                                            stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                                            <path stroke-linecap="round" stroke-linejoin="round"
                                                d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                                        </svg>
                                    </RouterLink>
                                </div>
                            </div>

                            <!-- subtle fade edges for horizontal scroll -->
                            <div
                                class="pointer-events-none absolute inset-y-0 left-0 w-10 bg-gradient-to-r from-[#181818] to-transparent">
                            </div>
                            <div
                                class="pointer-events-none absolute inset-y-0 right-0 w-10 bg-gradient-to-l from-[#181818] to-transparent">
                            </div>
                        </div>


                        <!-- Floating Action Buttons -->
                        <div
                            class="absolute top-2 right-2 flex flex-col space-y-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button @click="loadFromHistory(item.request)"
                                class="bg-blue-600 hover:bg-blue-700 text-[#FAF8F5] rounded-full p-2 shadow">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                                </svg>
                            </button>
                            <button @click="downloadImages(item.images)"
                                class="bg-gray-800 hover:bg-gray-700 text-[#FAF8F5] rounded-full p-2 shadow">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                            </button>
                            <button @click="deleteHistoryItem(history.length - 1 - index)"
                                class="bg-red-600 hover:bg-red-700 text-[#FAF8F5] rounded-full p-2 shadow">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div v-if="activeTab == 'gallery'" class="flex-1 overflow-y-auto  py-6 px-3">
                {{ }}
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                    <img v-if="generationState?.current_image && isGenerating"
                        :src="'data:image/png;base64,' + generationState.current_image" alt=""
                        class="w-full shadow-lg hover:shadow-xl transition-shadow rounded-lg" />
                    <div v-for="(item, index) in getAllHistoryImages()" :key="index"
                        class="group bg-[#181818] overflow-hidden relative ">
                        <img @click="showFullscreen([`data:image/png;base64,${item.image}`])"
                            :src="'data:image/png;base64,' + item.image" alt=""
                            class="w-full shadow-lg hover:shadow-xl transition-shadow rounded-lg" />
                        <RouterLink v-if="item.id != 1" :to="`/image/${item.id}`" @click="isFullscreen = false"
                            class="absolute top-2 right-2 bg-gray-900/80 hover:bg-blue-600 text-[#FAF8F5] rounded-full p-2 shadow transition"
                            title="Open image in new tab">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5"
                                stroke="currentColor" class="w-4 h-4">
                                <path stroke-linecap="round" stroke-linejoin="round"
                                    d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                            </svg>
                        </RouterLink>
                    </div>
                </div>
            </div>


            <div v-if="history.length > 0" class="border-t border-gray-700 px-8 py-4 bg-[#0a0a0a]">
                <button @click="clearHistory"
                    class="bg-red-600 hover:bg-red-700 text-[#FAF8F5] text-sm font-medium py-3 px-6 rounded-lg transition">
                    Clear All History
                </button>
            </div>
        </div>


        <!-- Resize Handle (only show when not fullscreen) -->
        <div v-if="!isFullscreen" @mousedown="startResize"
            class="w-1 bg-gray-700 hover:bg-blue-500 cursor-col-resize transition-colors relative group">
            <div class="absolute inset-y-0 -left-1 -right-1 group-hover:bg-blue-500/20"></div>
        </div>
    </div>
    <div class="fixed bottom-0 z-50 hidden" :style="{ left: `${webState.sidebarWidth}px` }">
        <img v-if="generationState.current_image || history.length > 0" :src="generationState.current_image
            ? `data:image/png;base64,${generationState.current_image}`
            : `data:image/png;base64,${history[history.length - 1].images[0]}`"
            :alt="generationState.current_image ? 'Generated Preview' : 'Image URL Preview'"
            class="h-96 w-full object-contain rounded-lg" />
    </div>

</template>

<style scoped>
.slider::-webkit-slider-thumb {
    appearance: none;
    height: 16px;
    width: 16px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
    border: 2px solid #1a1a1a;
}

.slider::-moz-range-thumb {
    height: 16px;
    width: 16px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
    border: 2px solid #1a1a1a;
}

/* Prevent text selection during resize */
.cursor-col-resize {
    user-select: none;
}
</style>