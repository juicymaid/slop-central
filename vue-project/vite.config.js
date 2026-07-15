import './mock-localstorage.js'
import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import VueDevTools from 'vite-plugin-vue-devtools'

const localAppData = process.env.LOCALAPPDATA || ''
const codePath = localAppData ? `${localAppData}/Programs/Microsoft VS Code/bin/code.cmd`.replace(/\\/g, '/') : 'code'

export default defineConfig({
  plugins: [
    vue(), tailwindcss(),
    VueDevTools({
      launchEditor: codePath,
    }),
  ],
  server: {
    host: '0.0.0.0',
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  }
})