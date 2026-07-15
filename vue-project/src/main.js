import './assets/main.css'
import { initTheme } from './theme'

// Initialize customized theme colors immediately to prevent flash
initTheme()

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import MasonryWall from '@yeger/vue-masonry-wall'


import 'viewerjs/dist/viewer.css'
import VueViewer from 'v-viewer'

const app = createApp(App)

app.use(router)
app.use(MasonryWall)

app.use(VueViewer)

app.mount('#app')
