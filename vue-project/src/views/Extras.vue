<template>
    <div class="p-6">
        <h1 class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">Extras</h1>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            <RouterLink v-for="page in pages" :key="page.path" :to="page.path"
                class="group relative block rounded-xl overflow-hidden shadow-md hover:shadow-xl transition-shadow duration-300 bg-gray-100 dark:bg-gray-800 aspect-video cursor-pointer">
                <!-- page preview image -->
                <img :src="page.img" class="absolute inset-0 w-full h-full object-cover" :alt="page.label"
                    aria-hidden="true" />

                <!-- click shield so the RouterLink captures all interaction -->
                <div class="absolute inset-0 z-10"></div>

                <!-- label bar at the bottom -->
                <div
                    class="absolute bottom-0 left-0 right-0 z-20 bg-black/50 backdrop-blur-sm px-3 py-2 translate-y-0 group-hover:bg-black/70 transition-colors duration-200">
                    <span class="text-white text-sm font-semibold truncate block">{{ page.label }}</span>
                </div>
            </RouterLink>
        </div>
    </div>
</template>

<script setup>
const pages = [
    { label: 'Civitai Images', path: '/civitai', img: '/covers/civitaipage.png' },
    { label: 'Ranbooru', path: '/ranbooru', img: '/covers/ranbooru.png' },
    { label: 'Rate Images', path: '/rate', img: '/covers/rate.png' },
    { label: 'Comics', path: '/comics', img: '/covers/comics.png' },
    { label: 'Canvas', path: '/canvas', img: '/covers/canvas.png' },
    { label: 'Cafe Game', path: '/cafe', img: '/covers/cafe.png' },
    { label: 'Chats', path: '/chat/45863', img: '/covers/chat.png' },
    { label: 'Rule34', path: '/rule34', img: '' },
    { label: 'Posts', path: '/posts', img: '' },
]
</script>