import { reactive } from "vue"

export const apiUrl = 'http://127.0.0.1:8000'
export const wsUrl = 'ws://127.0.0.1:8000'

export async function GetFromApi(endpoint) {
  const response = await fetch(`${apiUrl}/${endpoint}`)
  return await response.json()
}

export const webState = reactive({
  sidebarWidth: 0,
  remixImage: null,
    backendId: 'forge',
    backendLabel: 'Forge',
    backendRunning: false,
    backendAvailable: false,
    backendStatus: 'unknown',
    backendStatusMessage: '',
  // added for VRAM WS
  vramSocket: null,
  vram: null,
  vramUsage: 0,
})
export const request = reactive({
    prompt: "",
    negative_prompt: "",
    styles: [],
    seed: -1,
    sampler_name: "DPM++ 2M",
    batch_size: 1,
    n_iter: 1,
    steps: 25,
    cfg_scale: 5,
    width: 832,
    height: 1216,
    send_images: true,
    save_images: true,
    do_not_save_grid: true,
    resize_mode:1,
})
export const current_model = reactive({
    model: {
        title: null,
        model_name: null,
        hash: null,
        sha256: null,
        filename: null
    },
    loras: [

    ],
    loras_not_found: []
})

export async function PostToApi(endpoint, data) {
    const response = await fetch(`${apiUrl}/${endpoint}`, {
        method: 'POST',
        headers: {
        'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    return await response.json()
}

export async function UpdateVRAM(params) {
    // Switch from HTTP polling to a single WS connection that streams updates
    if (webState.sidebarWidth === 0) {
        // Close socket if sidebar not open
        if (webState.vramSocket && webState.vramSocket.readyState === WebSocket.OPEN) {
            try { webState.vramSocket.close() } catch {}
        }
        webState.vramSocket = null
        return
    }

    // Already connected and streaming
    if (webState.vramSocket && webState.vramSocket.readyState === WebSocket.OPEN) {
        return
    }

    // Create (or recreate) the websocket connection
    const ws = new WebSocket(`${wsUrl}/vram`)
    webState.vramSocket = ws

    ws.onopen = () => {
        // no-op; server will push periodically
        // if you need to pass params, send once here:
        // ws.send(JSON.stringify({ type: 'config', ...params }))
    }

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data)
            if (!data.gpus || data.gpus.length === 0) {
                console.error("No GPU data available")
                return
            }
            webState.vram = data.gpus[0]
            webState.vramUsage = webState.vram.memory_util
        } catch (e) {
            console.error("Failed to parse VRAM WS message:", e)
        }
    }

    ws.onerror = (err) => {
        console.error("VRAM WebSocket error:", err)
    }

    ws.onclose = () => {
        webState.vramSocket = null
        // Attempt to reconnect if sidebar is still open
        if (webState.sidebarWidth > 0) {
            setTimeout(() => UpdateVRAM(params), 1000)
        }
    }
}

export function ImageSrc(path){
    return `${apiUrl}${path}`
}

export const defaultStyles = reactive({})

export function formatRequest(prompt=null) {
        // Unproxy the request object to a plain JS object
    const plainRequest = { ...request }

    if (prompt) {
        plainRequest.prompt = prompt
    }

    if (!defaultStyles.value[current_model.model.model_name]) {
        defaultStyles.value[current_model.model.model_name] = {
            prompt_prefix: "",
            negative_prompt_prefix: ""
        }
    }
    plainRequest.negative_prompt = defaultStyles.value[current_model.model.model_name].negative_prompt_prefix + plainRequest.negative_prompt
    plainRequest.prompt = defaultStyles.value[current_model.model.model_name].prompt_prefix + plainRequest.prompt
    return plainRequest
}

// story helpers
export async function listStories() {
  return await GetFromApi('stories')
}

export async function getStory(storyId) {
  return await GetFromApi(`stories/${storyId}`)
}

export async function generateStory() {
  // backend expects POST with empty body
  return await PostToApi('stories/generate', {})
}