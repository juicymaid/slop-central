import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/image/:id',
      name: 'image',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/ImageView.vue'),
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('../views/SearchView.vue'),
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
    },
    {
      path: '/board/:id',
      name: 'board',
      component: () => import('../views/BoardView.vue'),
    },
    {
      path: "/scan",
      name: "scan",
      component: () => import("../views/ScanView.vue"),
    },
    {
      path: "/models/:hash",
      name: "model",
      component: () => import("../views/modelView.vue"),
    },
    {
      path: "/models",
      name: "models",
      component: () => import("../views/modelsView.vue"),
    },
    {
      path: "/test",
      name: "test",
      component: () => import("../views/testPage.vue"),
    },
    {
      path: "/civitai",
      name: "Civitai Images",
      component: () => import("../views/civitAiPage.vue"),
    },
    {
      path: "/ranbooru",
      name: "Ranbooru",
      component: () => import("../views/RanbooruView.vue"),
    },
    {
      path: "/chat/:id",
      name: "chat",
      component: () => import("../views/ChatView.vue"),
    },
    {
      path: "/rate",
      name: "rate",
      component: () => import("../views/rateView.vue"),
    },
    {
      path: "/comics/:id",
      name: "comic",
      component: () => import("../views/comicPage.vue"),
    },
    {
      path: "/comics/:id/read",
      name: "comic-read",
      component: () => import("../views/comicReadView.vue"),
    },
    {
      path: "/comics",
      name: "comics",
      component: () => import("../views/comicsPage.vue"),
    },
    {
      path: '/vn',
      name: 'vn',
      component: () => import('../views/vn.vue'),
    },
    {
      path: '/generator',
      name: 'generator',
      component: () => import('../views/generatorView.vue'),
    },
    {
      path: "/canvas",
      name: "canvas",
      component: () => import("../views/canvasView.vue"),
    },
    {
      path: '/cafe',
      name: 'cafe',
      component: () => import('../views/cafeView.vue'),
    },
    {
      path: '/trash',
      name: 'trash',
      component: () => import('../views/TrashView.vue'),
    },
    {
      path: "/extras",
      name: "extras",
      component: () => import("../views/Extras.vue"),
    },
    {
      path: "/rule34",
      name: "rule34",
      component: () => import("../views/rule34.vue"),
    },
    {
      path: "/user/:username",
      name: "user",
      component: () => import("../views/userProfile.vue"),
    },
    {
      path: "/posts",
      name: "posts",
      component: () => import("../views/posts.vue")
    },
    {
      path: "/hentai",
      name: "hentai",
      component: () => import("../views/hentaiView.vue")
    },
    {
      path: "/hentai/:id",
      name: "hentai-viewer",
      component: () => import("../views/hentaiViewer.vue")
    },
    {
      path: "/map",
      name: "map",
      component: () => import("../views/EmbeddingMapView.vue")
    },
  ],
})

export default router
