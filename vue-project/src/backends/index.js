import { reactive } from 'vue'
import { saveToFile, loadFromFile } from '@/storage'
import { current_model, defaultStyles } from '@/api'

const BACKEND_SETTINGS_FILE = 'backendSettings.json'

export const backendDefinitions = {
  forge: {
    id: 'forge',
    label: 'Forge',
    description: 'Local Forge/Automatic1111 API.',
    type: 'local',
    required: ['url'],
    fields: [
      {
        key: 'url',
        label: 'Forge URL',
        type: 'url',
        placeholder: 'http://127.0.0.1:7860/',
        hint: 'Local Forge WebUI base URL.',
      },
    ],
    defaultConfig: {
      url: 'http://127.0.0.1:7860/',
    },
    capabilities: {
      supportsLocalModels: true,
      supportsLoras: true,
      supportsExtensions: true,
      supportsProgress: true,
      supportsInterrupt: true,
      supportsModelThumbnails: true,
    },
  },
  comfyui: {
    id: 'comfyui',
    label: 'ComfyUI',
    description: 'Local ComfyUI server (placeholder adapter).',
    type: 'local',
    required: ['url'],
    fields: [
      {
        key: 'url',
        label: 'ComfyUI URL',
        type: 'url',
        placeholder: 'http://127.0.0.1:8888/',
        hint: 'Local ComfyUI base URL.',
      },
    ],
    defaultConfig: {
      url: 'http://127.0.0.1:8888/',
    },
    capabilities: {
      supportsLocalModels: false,
      supportsLoras: false,
      supportsExtensions: false,
      supportsProgress: false,
      supportsInterrupt: false,
      supportsModelThumbnails: false,
    },
  },
  aiHorde: {
    id: 'aiHorde',
    label: 'AI Horde',
    description: 'Cloud generation with API token (placeholder adapter).',
    type: 'cloud',
    required: ['apiToken'],
    fields: [
      {
        key: 'apiToken',
        label: 'API Token',
        type: 'password',
        placeholder: 'paste token here',
        hint: 'Your AI Horde API token.',
      },
      {
        key: 'baseUrl',
        label: 'API Base URL',
        type: 'url',
        placeholder: 'https://aihorde.net/api/v2',
        hint: 'Override only if you use a custom endpoint.',
      },
    ],
    defaultConfig: {
      apiToken: '',
      baseUrl: 'https://aihorde.net/api/v2',
    },
    capabilities: {
      supportsLocalModels: false,
      supportsLoras: false,
      supportsExtensions: false,
      supportsProgress: true,
      supportsInterrupt: true,
      supportsModelThumbnails: false,
    },
    samplerMap: {
      'Euler a': 'k_euler_a',
      'Euler': 'k_euler',
      'LMS': 'k_lms',
      'DDIM': 'DDIM',
      'DPM++ 2M': 'k_dpmpp_2m',
      'DPM++ 2M SDE': 'k_dpmpp_sde',
      'DPM++ SDE': 'k_dpmpp_sde',
      'DPM++ 2S a': 'k_dpmpp_2s_a',
      'DPM2': 'k_dpm_2',
      'DPM2 a': 'k_dpm_2_a',
      'Heun': 'k_heun',
      'DPM fast': 'k_dpm_fast',
      'DPM adaptive': 'k_dpm_adaptive',
      'LCM': 'lcm',
    },
  },
}

export const backendOptions = Object.values(backendDefinitions)

const defaultConfigs = backendOptions.reduce((acc, backend) => {
  acc[backend.id] = { ...backend.defaultConfig }
  return acc
}, {})

export const backendState = reactive({
  activeId: 'forge',
  configs: { ...defaultConfigs },
})

let backendSettingsLoaded = false

const normalizeBaseUrl = (value) => {
  if (!value) return ''
  const trimmed = String(value).trim()
  if (!trimmed) return ''
  return trimmed.endsWith('/') ? trimmed : `${trimmed}/`
}

const mergeBackendConfig = (backendId, incoming) => {
  const defaults = backendDefinitions[backendId]?.defaultConfig || {}
  return {
    ...defaults,
    ...(incoming || {}),
  }
}

export const getBackendDefinition = (backendId) => backendDefinitions[backendId]

export const getBackendConfig = (backendId) => backendState.configs[backendId] || {}

export const getActiveBackend = () => {
  const definition = getBackendDefinition(backendState.activeId) || backendDefinitions.forge
  return {
    ...definition,
    config: getBackendConfig(definition.id),
  }
}

export const getBackendBaseUrl = (backendId = backendState.activeId) => {
  const definition = getBackendDefinition(backendId)
  if (!definition) return ''

  const config = getBackendConfig(backendId)
  if (definition.type === 'cloud') {
    return normalizeBaseUrl(config.baseUrl || definition.defaultConfig.baseUrl || '')
  }
  return normalizeBaseUrl(config.url || definition.defaultConfig.url || '')
}

export const getBackendConfigStatus = (backendId = backendState.activeId) => {
  const definition = getBackendDefinition(backendId)
  if (!definition) return { ok: false, missingFields: ['backend'] }

  const config = getBackendConfig(backendId)
  const missingFields = (definition.required || []).filter((field) => {
    const value = config[field]
    return value == null || String(value).trim().length === 0
  })

  return {
    ok: missingFields.length === 0,
    missingFields,
  }
}

export const setActiveBackend = (backendId) => {
  if (!backendDefinitions[backendId]) return
  backendState.activeId = backendId
}

export const updateBackendConfig = (backendId, patch) => {
  if (!backendDefinitions[backendId]) return
  if (!backendState.configs[backendId]) {
    backendState.configs[backendId] = mergeBackendConfig(backendId, {})
  }
  Object.assign(backendState.configs[backendId], patch)
}

export const loadBackendSettings = async () => {
  if (backendSettingsLoaded) return
  backendSettingsLoaded = true

  const stored = await loadFromFile(BACKEND_SETTINGS_FILE)
  if (!stored) return

  if (stored.activeId && backendDefinitions[stored.activeId]) {
    backendState.activeId = stored.activeId
  }

  if (stored.configs && typeof stored.configs === 'object') {
    backendOptions.forEach((backend) => {
      backendState.configs[backend.id] = mergeBackendConfig(backend.id, stored.configs[backend.id])
    })
  }
}

export const saveBackendSettings = async () => {
  await saveToFile(
    {
      activeId: backendState.activeId,
      configs: backendState.configs,
    },
    BACKEND_SETTINGS_FILE
  )
}

const mapSamplerName = (backendId, samplerName) => {
  const mapping = backendDefinitions[backendId]?.samplerMap || {}
  return mapping[samplerName] || samplerName
}

const buildLoraTag = (lora) => {
  const name =  lora?.name || lora?.path || 'lora'
  const weight = typeof lora?.weight === 'number' ? lora.weight : parseFloat(lora?.weight) || 1
  return ` <lora:${name}:${weight}>`
}

const AI_HORDE_CLIENT_AGENT = 'slop-central:0.1:local'

const clampNumber = (value, min, max) => {
  const numeric = Number(value)
  if (Number.isNaN(numeric)) return min
  return Math.min(max, Math.max(min, numeric))
}

const buildAiHordePrompt = (prompt, negativePrompt) => {
  const trimmedPrompt = (prompt || '').trim()
  const trimmedNegative = (negativePrompt || '').trim()
  if (!trimmedNegative) return trimmedPrompt
  return `${trimmedPrompt} ### ${trimmedNegative}`
}

const buildAiHordePayload = ({ baseRequest, inputImage, denoisingStrength } = {}) => {
  const totalImages = Math.max(1, (baseRequest.batch_size || 1) * (baseRequest.n_iter || 1))
  const params = {
    steps: clampNumber(baseRequest.steps ?? 30, 1, 500),
    cfg_scale: Number(baseRequest.cfg_scale ?? 7.5),
    sampler_name: mapSamplerName('aiHorde', baseRequest.sampler_name || 'Euler a'),
    height: clampNumber(baseRequest.height ?? 512, 64, 3072),
    width: clampNumber(baseRequest.width ?? 512, 64, 3072),
    n: clampNumber(totalImages, 1, 20),
  }

  if (baseRequest.seed != null && baseRequest.seed !== -1) {
    params.seed = String(baseRequest.seed)
  }

  if (inputImage) {
    params.denoising_strength = typeof denoisingStrength === 'number' ? denoisingStrength : 0.75
  }

  const payload = {
    prompt: buildAiHordePrompt(baseRequest.prompt, baseRequest.negative_prompt),
    params,
    nsfw: false,
    censor_nsfw: false,
    r2: false,
    shared: false,
  }

  if (inputImage) {
    payload.source_image = inputImage
    payload.source_processing = 'img2img'
  }

  return payload
}

const applyForgeOverrides = (baseRequest) => {
  const request = { ...baseRequest }

  if (current_model?.loras?.length) {
    const tags = current_model.loras.map(buildLoraTag).join('')
    request.prompt = `${request.prompt || ''}${tags}`
  }

  const modelName = current_model?.model?.model_name
  if (modelName) {
    request.override_settings = {
      sd_model_checkpoint: modelName,
    }
    request.override_settings_restore_afterwards = false
  }

  const defaultStyle = modelName ? defaultStyles.value?.[modelName] : null
  if (defaultStyle?.override_sampler) {
    request.sampler_name = defaultStyle.sampler || request.sampler_name
  }

  request.sampler_name = mapSamplerName('forge', request.sampler_name)

  if (current_model?.adetailer) {
    request.alwayson_scripts = request.alwayson_scripts || {}
    request.alwayson_scripts.adetailer = {
      args: [
        true,
        {
          ad_model: 'face_yolov8n.pt',
        },
      ],
    }
  }

  if (current_model?.blockCache) {
    request.alwayson_scripts = request.alwayson_scripts || {}
    request.alwayson_scripts['first block cache / teacache'] = {
      args: [
        true,
        current_model.blockCacheMethod || 'First Block Cache',
        parseFloat(current_model.blockCacheThreshold ?? 0.1),
        1,
        0,
        false,
      ],
    }
  }

  return request
}

export const buildBackendRequest = ({ baseRequest, inputImage, denoisingStrength } = {}) => {
  const backend = getActiveBackend()
  const configStatus = getBackendConfigStatus(backend.id)

  if (!configStatus.ok) {
    return {
      status: 'misconfigured',
      backend,
      reason: `Missing ${configStatus.missingFields.join(', ')}`,
    }
  }

  if (backend.id === 'aiHorde') {
    const baseUrl = getBackendBaseUrl('aiHorde')
    const payload = buildAiHordePayload({ baseRequest: baseRequest || {}, inputImage, denoisingStrength })

    return {
      status: 'ready',
      backend,
      adapter: 'aiHorde',
      mode: 'async',
      requestUrl: `${baseUrl}generate/async`,
      checkUrl: `${baseUrl}generate/check/`,
      statusUrl: `${baseUrl}generate/status/`,
      cancelUrl: `${baseUrl}generate/status/`,
      headers: {
        'Content-Type': 'application/json',
        apikey: backend.config.apiToken,
        'Client-Agent': AI_HORDE_CLIENT_AGENT,
      },
      payload,
      supportsProgress: false,
      supportsInterrupt: true,
    }
  }

  if (backend.id !== 'forge') {
    return {
      status: 'unsupported',
      backend,
      reason: `${backend.label} adapter not wired yet.`,
    }
  }

  const baseUrl = getBackendBaseUrl('forge')
  const payload = applyForgeOverrides(baseRequest || {})
  const endpoint = inputImage ? 'sdapi/v1/img2img' : 'sdapi/v1/txt2img'

  if (inputImage) {
    payload.init_images = [inputImage]
    payload.denoising_strength = typeof denoisingStrength === 'number' ? denoisingStrength : 0.75
  }

  return {
    status: 'ready',
    backend,
    requestUrl: `${baseUrl}${endpoint}`,
    progressUrl: `${baseUrl}sdapi/v1/progress`,
    interruptUrl: `${baseUrl}sdapi/v1/interrupt`,
    headers: {
      'Content-Type': 'application/json',
    },
    payload,
    supportsProgress: true,
    supportsInterrupt: true,
  }
}
