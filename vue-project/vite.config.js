import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// Vite config runs in Node, but vue-devtools expects a browser-like localStorage.
function ensureLocalStorage() {
  const storage = globalThis.localStorage
  if (storage && typeof storage.getItem === 'function') {
    return true
  }

  const store = new Map()
  const shim = {
    getItem: (key) => (store.has(key) ? store.get(key) : null),
    setItem: (key, value) => {
      store.set(key, String(value))
    },
    removeItem: (key) => {
      store.delete(key)
    },
    clear: () => {
      store.clear()
    },
    key: (index) => Array.from(store.keys())[index] ?? null,
    get length() {
      return store.size
    },
  }

  try {
    globalThis.localStorage = shim
  } catch {
    return false
  }

  return typeof globalThis.localStorage?.getItem === 'function'
}

// https://vite.dev/config/
export default defineConfig(async ({ command }) => {
  const plugins = [vue(), tailwindcss()]

  if (command === 'serve' && ensureLocalStorage()) {
    const { default: vueDevTools } = await import('vite-plugin-vue-devtools')
    plugins.push(vueDevTools({
      launchEditor: fileURLToPath(new URL('./ag-editor.cmd', import.meta.url)).replace(/\\/g, '/')
    }))
  }

  return {
    plugins,
    server: {
      host: '0.0.0.0',
    },
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      },
    }
  }
})
