<script setup>
import { ref, onMounted, computed, reactive } from 'vue'
import { GetFromApi, PostToApi, apiUrl, formatRequest } from '../api'

const characters = ref([])
const allPosts = ref([])
const selectedCharacterId = ref(null)

const showCreateModal = ref(false)
const isEditing = ref(false)
const newChar = ref({
    id: '',
    name: '',
    avatar: '',
    description: '',
    prompt_prefix: ''
})

const showCreatePostModal = ref(false)
const postCharId = ref(null) // ID of character to post as
const newPost = ref({
    title: '',
    image_url: '',
    image: {
        rating: 'safe',
        appearance: '',
        clothing: '',
        pose: '',
        expression: '',
        setting: '',
        other_tags: ''
    }
})

const loadCharacters = async () => {
    characters.value = await GetFromApi('characters')
}

const loadPosts = async () => {
    allPosts.value = await GetFromApi('posts')
}

onMounted(() => {
    loadCharacters()
    loadPosts()
})

const selectedCharacter = computed(() => {
    if (!selectedCharacterId.value) return null
    return characters.value.find(c => c.id === selectedCharacterId.value)
})

const openCreateModal = () => {
    isEditing.value = false
    newChar.value = { id: '', name: '', avatar: '', description: '', prompt_prefix: '' }
    showCreateModal.value = true
}

const openEditModal = (char) => {
    isEditing.value = true
    newChar.value = { ...char }
    showCreateModal.value = true
}

const saveCharacter = async () => {
    try {
        if (!newChar.value.id || !newChar.value.name) return

        if (isEditing.value) {
            await fetch(`${apiUrl}/characters/${newChar.value.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newChar.value)
            })
        } else {
            await PostToApi('characters', newChar.value)
        }

        showCreateModal.value = false
        await loadCharacters()
        selectedCharacterId.value = newChar.value.id
    } catch (e) {
        console.error(e)
    }
}

const openPostModal = (charId) => {
    postCharId.value = charId
    newPost.value = {
        title: '',
        image_url: '',
        image: { rating: 'safe', appearance: '', clothing: '', pose: '', expression: '', setting: '', other_tags: '' }
    }
    showCreatePostModal.value = true
}

const createPost = async () => {
    try {
        const targetCharId = postCharId.value || selectedCharacterId.value
        if (!targetCharId) return

        await PostToApi(`characters/${targetCharId}/posts`, newPost.value)
        showCreatePostModal.value = false
        await loadCharacters()
        await loadPosts()
    } catch (e) {
        console.error(e)
    }
}

const isPublishing = ref(false)
const postAmount = ref(1)
const isGeneratingAll = ref(false)

async function generateAllMissingImages() {
    if (isGeneratingAll.value) return
    isGeneratingAll.value = true
    try {
        const postsToGenerate = filteredPosts.value.filter(p => !p.image_url && !getGenState(p).generating)
        for (const p of postsToGenerate) {
            if (!isGeneratingAll.value) break
            await generateImage(p)
        }
    } catch (e) {
        console.error('Failed to generate all images:', e)
    } finally {
        isGeneratingAll.value = false
    }
}

async function publishPost(charId = null) {
    if (isPublishing.value) return
    isPublishing.value = true
    try {
        const targetCharId = charId || selectedCharacterId.value
        let url = `${apiUrl}/generate-post`
        if (targetCharId) url += `?character_id=${targetCharId}`

        for (let i = 0; i < postAmount.value; i++) {
            const res = await fetch(url, { method: 'POST' })
            if (!res.ok) throw new Error('generate-post failed')
            await refreshFeed()
        }
    } catch (e) {
        console.error('Publish failed:', e)
    } finally {
        isPublishing.value = false
    }
}

async function refreshFeed() {
    await loadCharacters()
    await loadPosts()
}

const filteredPosts = computed(() => {
    if (!selectedCharacterId.value) return allPosts.value
    return allPosts.value.filter(p => p.character?.id === selectedCharacterId.value)
})
const sdUrl = ref('http://127.0.0.1:7860/')
const sleep = ms => new Promise(r => setTimeout(r, ms))

// Track generation state per post by created_at key
const genState = reactive({})
function getGenState(post) {
    const key = post.created_at || post.title
    if (!genState[key]) genState[key] = { generating: false, progress: 0, preview: '' }
    return genState[key]
}

function dataURLtoFile(dataurl, filename) {
    var arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1],
        bstr = atob(arr[arr.length - 1]), n = bstr.length, u8arr = new Uint8Array(n);
    while (n--) u8arr[n] = bstr.charCodeAt(n);
    return new File([u8arr], filename, { type: mime });
}

function postToPromt(post) {
    var prompt = [
        post.image?.rating || '',
        '1girl',
        post.character?.prompt_prefix || post.prompt_prefix || '',
        post.image?.camera_angle || '',
        post.image?.appearance || '',
        post.image?.body || '',
        post.image?.breast_size || '',
        post.image?.clothing || '',
        post.image?.pose || '',
        post.image?.expression || '',
        post.image?.setting || '',
        post.image?.other_tags || ''
    ].join(', ')
    prompt = prompt.replace(/,\s*,+/g, ',').replace(/^,|,$/g, '').trim()
    return prompt
}

async function generateImage(post) {
    const state = getGenState(post)
    state.generating = true
    state.progress = 0
    state.preview = ''

    // Build prompt from post image fields

    prompt = postToPromt(post)


    console.log(prompt)


    try {
        const _request = formatRequest(prompt)
        console.log('Generate post image:', _request)

        const genPromise = fetch(sdUrl.value + 'sdapi/v1/txt2img', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(_request)
        }).then(async res => {
            if (!res.ok) throw new Error('txt2img failed')
            return res.json()
        })

        // Poll progress with preview
        const poll = (async () => {
            while (state.generating) {
                try {
                    const progRes = await fetch(sdUrl.value + 'sdapi/v1/progress?skip_current_image=false')
                    if (progRes.ok) {
                        const data = await progRes.json()
                        state.progress = typeof data?.progress === 'number' ? data.progress : 0
                        if (data?.current_image) state.preview = 'data:image/png;base64,' + data.current_image
                    }
                } catch (_) { }
                await sleep(500)
            }
        })()

        const result = await genPromise
        const imageB64 = 'image/png;base64,' + result.images[0]
        const file = dataURLtoFile('data:' + imageB64, 'post.png')

        // Find character id and post index for upload
        const charId = post.character?.id
        if (!charId) throw new Error('No character ID on post')

        // Find post index within the character's posts
        const char = characters.value.find(c => c.id === charId)
        const postIndex = char ? char.posts.findIndex(p => p.created_at === post.created_at) : -1
        if (postIndex < 0) throw new Error('Could not find post index')

        const formData = new FormData()
        formData.append('file', file)

        const uploadRes = await fetch(`${apiUrl}/characters/${charId}/posts/${postIndex}/image`, {
            method: 'POST',
            body: formData
        })
        const uploadJson = await uploadRes.json()
        if (!uploadRes.ok) throw new Error(uploadJson?.detail || 'Upload failed')

        post.image_url = apiUrl + uploadJson.image_url + '?t=' + Date.now()
        refreshFeed()
    } catch (e) {
        console.error('Image generation failed:', e)
    } finally {
        state.generating = false
        state.progress = 0
        state.preview = ''
    }
}

</script>

<template>
    <div class="max-w-4xl mx-auto py-8 space-y-8">
        <!-- Top Bar / Cast List -->
        <div class="bg-[#14141A] rounded-2xl border border-[#2A2A35] p-5 shadow-lg w-full">

            <div class="flex items-center justify-between mb-4 border-b border-[#2A2A35] pb-4">
                <h2 class="text-[#FAF8F5] font-sans font-bold tracking-tight text-xl">Cast of Characters</h2>
                <div class="flex items-center gap-3">
                    <button @click="selectedCharacterId = null"
                        class="py-2 px-4 flex items-center gap-2 rounded-xl transition-all duration-300 text-sm font-medium"
                        :class="selectedCharacterId === null ? 'bg-[#C9A84C] text-[#0D0D12] shadow-[0_0_15px_rgba(201,168,76,0.3)]' : 'bg-[#2A2A35] text-[#FAF8F5] hover:bg-[#3f3f4e]'">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10">
                            </path>
                        </svg>
                        Global Feed
                    </button>

                    <button @click="openCreateModal"
                        class="py-2 px-4 bg-transparent border border-[#C9A84C] text-[#C9A84C] rounded-xl font-bold font-sans text-sm transition-all duration-300 hover:bg-[#C9A84C] hover:text-[#0D0D12] hover:shadow-[0_0_15px_rgba(201,168,76,0.2)]">
                        + Create Character
                    </button>
                </div>
            </div>

            <div class="flex gap-4 overflow-x-auto pb-2 custom-scrollbar">
                <div v-for="char in characters" :key="char.id" @click="selectedCharacterId = char.id"
                    class="flex-shrink-0 flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all duration-300 border border-transparent max-w-[240px]"
                    :class="selectedCharacterId === char.id ? 'bg-[#2A2A35] border-[#C9A84C]/30 shadow-sm' : 'bg-[#0D0D12]/50 hover:bg-[#2A2A35]/50'">
                    <img :src="char.avatar || 'https://images.unsplash.com/photo-1511275539165-cc46b1ee89bf?w=100&h=100&fit=crop'"
                        class="w-12 h-12 rounded-full object-cover shadow-md border border-[#2A2A35] flex-shrink-0">
                    <div class="overflow-hidden">
                        <span class="block text-[#FAF8F5] text-sm font-semibold truncate hidden">{{ char.name }}</span>
                        <span class="block text-[#FAF8F5]/50 font-mono text-xs truncate hidden">@{{ char.id }}</span>
                    </div>
                </div>
                <div v-if="characters.length === 0" class="text-[#FAF8F5]/50 font-mono text-sm py-3 px-2 italic">
                    No characters assembled yet.
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="mx-auto w-full">
            <!-- GLOBAL FEED -->
            <div v-if="!selectedCharacterId" class="space-y-8">
                <div class="flex items-center justify-between pb-6 border-b border-[#2A2A35]">
                    <h1 class="text-3xl font-bold font-sans tracking-tight text-[#FAF8F5]">Global Feed</h1>
                    <div class="flex items-center gap-3">
                        <button @click="refreshFeed"
                            class="p-2.5 bg-[#2A2A35] text-[#FAF8F5] rounded-full hover:bg-[#3f3f4e] transition-all duration-300 border border-[#FAF8F5]/10"
                            title="Refresh feed">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                        </button>
                        <button v-if="filteredPosts.some(p => !p.image_url)" @click="generateAllMissingImages"
                            :disabled="isGeneratingAll"
                            class="px-5 py-2.5 bg-[#2A2A35] text-[#FAF8F5] rounded-full font-bold font-sans text-sm hover:bg-[#3f3f4e] transition-all duration-300 border border-[#FAF8F5]/10 disabled:opacity-50 flex items-center gap-2">
                            <span v-if="isGeneratingAll" class="flex items-center gap-2">
                                <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                                        stroke-width="4"></circle>
                                    <path class="opacity-75" fill="currentColor"
                                        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                                </svg>
                                Generating...
                            </span>
                            <span v-else>Generate Missing Images</span>
                        </button>
                        <div v-if="characters.length > 0"
                            class="flex items-center bg-[#C9A84C] rounded-full shadow-[0_0_15px_rgba(201,168,76,0.3)] transition-all overflow-hidden"
                            :class="{ 'opacity-50 pointer-events-none': isPublishing }">
                            <input type="number" v-model="postAmount" min="1" max="10"
                                class="w-14 bg-transparent text-[#0D0D12] px-3 py-2.5 text-sm text-center outline-none border-r border-[#0D0D12]/20 font-bold font-sans"
                                title="Amount of posts to generate">
                            <button @click="publishPost(null)" :disabled="isPublishing"
                                class="px-5 py-2.5 text-[#0D0D12] font-bold font-sans text-sm hover:bg-black/5 transition-all h-full">
                                <span v-if="isPublishing" class="flex items-center gap-2">
                                    <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                                            stroke-width="4"></circle>
                                        <path class="opacity-75" fill="currentColor"
                                            d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                                    </svg>
                                    Generating…
                                </span>
                                <span v-else>Generate</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- PROFILE VIEW -->
            <div v-else-if="selectedCharacter" class="space-y-8">
                <div class="bg-[#14141A] rounded-2xl border border-[#2A2A35] p-8 relative shadow-xl overflow-hidden">
                    <div
                        class="absolute top-0 right-0 w-80 h-80 bg-gradient-to-br from-[#C9A84C]/10 to-transparent rounded-full blur-3xl -mr-40 -mt-40">
                    </div>

                    <div class="flex flex-col gap-6 relative z-10">
                        <div class="flex justify-between items-start">
                            <div class="flex gap-6 items-center">
                                <img :src="selectedCharacter.avatar || 'https://images.unsplash.com/photo-1511275539165-cc46b1ee89bf?w=150&h=150&fit=crop'"
                                    class="w-32 h-32 rounded-full object-cover shadow-[0_0_20px_rgba(0,0,0,0.5)] border-2 border-[#2A2A35]">
                                <div>
                                    <h1 class="text-4xl font-bold font-sans tracking-tight text-[#FAF8F5]">{{
                                        selectedCharacter.name }}</h1>
                                    <p class="text-[#C9A84C] font-mono text-sm mt-1">@{{ selectedCharacter.id }}</p>
                                </div>
                            </div>
                            <div class="flex gap-3">
                                <button @click="openEditModal(selectedCharacter)"
                                    class="px-5 py-2.5 bg-[#2A2A35] text-[#FAF8F5] rounded-full font-bold font-sans text-sm hover:bg-[#3f3f4e] transition-all duration-300 border border-[#FAF8F5]/10">
                                    Edit Profile
                                </button>
                                <button @click="refreshFeed"
                                    class="px-5 py-2.5 bg-[#2A2A35] text-[#FAF8F5] rounded-full font-bold font-sans text-sm hover:bg-[#3f3f4e] transition-all duration-300 border border-[#FAF8F5]/10">
                                    Refresh
                                </button>
                                <button v-if="filteredPosts.some(p => !p.image_url)" @click="generateAllMissingImages"
                                    :disabled="isGeneratingAll"
                                    class="px-5 py-2.5 bg-[#2A2A35] text-[#FAF8F5] rounded-full font-bold font-sans text-sm hover:bg-[#3f3f4e] transition-all duration-300 border border-[#FAF8F5]/10 disabled:opacity-50 flex items-center gap-2">
                                    <span v-if="isGeneratingAll" class="flex items-center gap-2">
                                        <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                                                stroke-width="4"></circle>
                                            <path class="opacity-75" fill="currentColor"
                                                d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                                        </svg>
                                        Generating...
                                    </span>
                                    <span v-else>Generate Missing Images</span>
                                </button>
                                <div class="flex items-center bg-[#C9A84C] rounded-full shadow-[0_0_15px_rgba(201,168,76,0.3)] transition-all overflow-hidden"
                                    :class="{ 'opacity-50 pointer-events-none': isPublishing }">
                                    <input type="number" v-model="postAmount" min="1" max="10"
                                        class="w-14 bg-transparent text-[#0D0D12] px-3 py-2.5 text-sm text-center outline-none border-r border-[#0D0D12]/20 font-bold font-sans"
                                        title="Amount of posts to generate">
                                    <button @click="publishPost(selectedCharacter.id)" :disabled="isPublishing"
                                        class="px-5 py-2.5 text-[#0D0D12] font-bold font-sans text-sm hover:bg-black/5 transition-all h-full">
                                        <span v-if="isPublishing" class="flex items-center gap-2">
                                            <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                                                    stroke-width="4"></circle>
                                                <path class="opacity-75" fill="currentColor"
                                                    d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                                            </svg>
                                            Generating…
                                        </span>
                                        <span v-else>Publish</span>
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div class="p-6 bg-[#0D0D12]/50 rounded-xl border border-[#2A2A35]/50">
                            <h3 class="text-xs font-mono text-[#FAF8F5]/40 uppercase tracking-widest mb-3">Description
                            </h3>
                            <p class="text-[#FAF8F5]/90 font-sans leading-relaxed text-[15px] line-clamp-6">
                                {{
                                    selectedCharacter.description || 'A figure shrouded in mystery.' }}</p>
                        </div>
                    </div>
                </div>

                <h3 class="text-xl font-bold font-sans tracking-tight text-[#FAF8F5] border-b border-[#2A2A35] pb-4">
                    Posts</h3>


            </div>
        </div>
        <div class="space-y-6">
            <div v-for="(post, index) in filteredPosts" :key="post.created_at || index"
                class="bg-[#14141A] rounded-2xl border border-[#2A2A35] overflow-hidden shadow-lg transition-transform duration-300 hover:-translate-y-1 hover:shadow-xl hover:border-[#2A2A35]/80">
                <div class="p-6 flex gap-4">
                    <img @click="selectedCharacterId = post.character.id"
                        :src="post.character?.avatar || 'https://images.unsplash.com/photo-1511275539165-cc46b1ee89bf?w=100&h=100&fit=crop'"
                        class="w-12 h-12 rounded-full object-cover shadow-sm border border-[#2A2A35] cursor-pointer hover:opacity-80 transition-opacity">
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 mb-2 cursor-pointer w-max"
                            @click="selectedCharacterId = post.character.id">
                            <span class="font-bold font-sans text-[#FAF8F5] hover:text-[#C9A84C] transition-colors">{{
                                post.character?.name }}</span>
                            <span class="text-[#FAF8F5]/40 font-mono text-sm">@{{ post.character?.id }}</span>
                        </div>
                        <p class="text-[#FAF8F5]/90 font-sans leading-relaxed text-[15px] mb-4 whitespace-pre-wrap">
                            {{ post.title }}</p>

                        <div class="rounded-xl border border-[#2A2A35] overflow-hidden bg-[#0D0D12]">
                            <!-- Live preview during generation -->
                            <template v-if="getGenState(post).generating && getGenState(post).preview">
                                <div class="relative">
                                    <img :src="getGenState(post).preview"
                                        class="w-full h-auto max-h-[700px] object-cover opacity-80" />
                                    <div
                                        class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-[#0D0D12] to-transparent p-4">
                                        <div class="flex items-center gap-3">
                                            <div class="flex-1 h-1.5 bg-[#2A2A35] rounded-full overflow-hidden">
                                                <div class="h-full bg-[#C9A84C] rounded-full transition-all duration-300 shadow-[0_0_8px_rgba(201,168,76,0.5)]"
                                                    :style="{ width: Math.round(getGenState(post).progress * 100) + '%' }">
                                                </div>
                                            </div>
                                            <span class="text-[#C9A84C] font-mono text-xs font-bold">{{
                                                Math.round(getGenState(post).progress * 100) }}%</span>
                                        </div>
                                    </div>
                                </div>
                            </template>
                            <!-- Generating but no preview yet -->
                            <template v-else-if="getGenState(post).generating">
                                <div class="flex flex-col items-center justify-center py-16 gap-4">
                                    <svg class="w-8 h-8 animate-spin text-[#C9A84C]" viewBox="0 0 24 24" fill="none">
                                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                                            stroke-width="4"></circle>
                                        <path class="opacity-75" fill="currentColor"
                                            d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                                    </svg>
                                    <span class="text-[#FAF8F5]/60 font-mono text-sm">Generating image…</span>
                                </div>
                            </template>
                            <!-- Final image -->
                            <img v-else-if="post.image_url" :src="apiUrl + post.image_url"
                                class="w-full h-auto  object-cover">

                            <!-- Prompt card (no image yet) -->
                            <div v-else class="relative p-8 font-mono text-sm bg-cover bg-center group"
                                :style="{ backgroundImage: `url('${apiUrl}/random-image-file?seed=${post.created_at}')` }">
                                <div
                                    class="absolute inset-0 bg-[#0D0D12]/90 backdrop-blur-sm group-hover:backdrop-blur-none transition-all duration-500">
                                </div>



                                <div class="relative z-10  transition-opacity duration-300">
                                    <div class="flex items-center gap-3 mb-6 border-b border-[#2A2A35] pb-4">
                                        <div class="h-2 w-2 rounded-full bg-[#C9A84C] shadow-[0_0_8px_#C9A84C]">
                                        </div>
                                        <span class="text-[#C9A84C] uppercase tracking-[0.2em] text-xs font-bold">Image
                                            Prompt</span>
                                    </div>
                                    <div class="grid grid-cols-2 gap-x-8 gap-y-4 text-[#FAF8F5]/90">
                                        <div v-if="post.image.rating" class="flex flex-col"><span
                                                class="text-[#FAF8F5]/40 text-xs uppercase tracking-widest mb-1">Rating</span><span
                                                class="text-[#FAF8F5] bg-[#2A2A35] px-2 py-1 rounded inline-block w-max">{{
                                                    post.image.rating }}</span></div>
                                        <div v-if="post.image.appearance" class="flex flex-col"><span
                                                class="text-[#FAF8F5]/40 text-xs uppercase tracking-widest mb-1">Appearance</span>{{
                                                    post.image.appearance }}</div>
                                        <div v-if="post.image.breast_size" class="flex flex-col"><span
                                                class="text-[#FAF8F5]/40 text-xs uppercase tracking-widest mb-1">Breast
                                                Size</span>{{
                                                    post.image.breast_size }}</div>
                                        <div v-if="post.image.clothing" class="flex flex-col"><span
                                                class="text-[#FAF8F5]/40 text-xs uppercase tracking-widest mb-1">Clothing</span>{{
                                                    post.image.clothing }}</div>
                                        <div v-if="post.image.pose" class="flex flex-col"><span
                                                class="text-[#FAF8F5]/40 text-xs uppercase tracking-widest mb-1">Pose</span>{{
                                                    post.image.pose }}</div>
                                        <div v-if="post.image.camera_angle" class="flex flex-col"><span
                                                class="text-[#FAF8F5]/40 text-xs uppercase tracking-widest mb-1">Camera
                                                Angle</span>{{
                                                    post.image.camera_angle }}</div>
                                        <div v-if="post.image.expression" class="flex flex-col"><span
                                                class="text-[#FAF8F5]/40 text-xs uppercase tracking-widest mb-1">Expression</span>{{
                                                    post.image.expression }}</div>
                                        <div v-if="post.image.setting" class="flex flex-col"><span
                                                class="text-[#FAF8F5]/40 text-xs uppercase tracking-widest mb-1">Setting</span>{{
                                                    post.image.setting }}</div>
                                        <div v-if="post.image.other_tags"
                                            class="flex flex-col col-span-2 mt-2 pt-4 border-t border-[#2A2A35]/50">
                                            <span class="text-[#FAF8F5]/40 text-xs uppercase tracking-widest mb-1">Other
                                                Tags</span><span class="text-[#C9A84C]/80">{{
                                                    post.image.other_tags }}</span>
                                        </div>
                                    </div>
                                    <div class="flex justify-end mt-4">
                                        <button class="px-5 py-2.5 bg-[#C9A84C] text-[#0D0D12] rounded-full font-bold
                                                            font-sans text-sm shadow-[0_0_15px_rgba(201,168,76,0.3)]
                                                            hover:scale-105 transition-all duration-300"
                                            @click="generateImage(post)">Generate</button>
                                    </div>
                                </div>
                            </div>

                        </div>
                    </div>
                </div>
                <div v-if="allPosts.length === 0" class="py-24 text-center">
                    <p class="text-[#FAF8F5]/50 font-mono text-sm">The network is silent. Create a character and
                        publish a record.</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Create/Edit Character Modal -->
    <div v-if="showCreateModal"
        class="fixed inset-0 bg-[#0D0D12]/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
        <div
            class="bg-[#14141A] rounded-2xl border border-[#2A2A35] p-8 w-full max-w-2xl max-h-[90vh] overflow-y-auto custom-scrollbar shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
            <h2 class="text-2xl font-bold font-sans tracking-tight text-[#FAF8F5] mb-6">{{ isEditing ? 'Edit Profile' :
                'New Character' }}</h2>
            <div class="space-y-5">
                <div class="grid grid-cols-2 gap-5">
                    <div>
                        <label class="block text-xs font-mono text-[#FAF8F5]/50 uppercase tracking-widest mb-2">ID
                            (username)</label>
                        <input v-model="newChar.id" type="text" :disabled="isEditing"
                            class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-xl px-4 py-3 text-[#FAF8F5] font-sans focus:outline-none focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] transition-all disabled:opacity-50">
                    </div>
                    <div>
                        <label class="block text-xs font-mono text-[#FAF8F5]/50 uppercase tracking-widest mb-2">Display
                            Name</label>
                        <input v-model="newChar.name" type="text"
                            class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-xl px-4 py-3 text-[#FAF8F5] font-sans focus:outline-none focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] transition-all">
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-mono text-[#FAF8F5]/50 uppercase tracking-widest mb-2">Avatar
                        URL</label>
                    <input v-model="newChar.avatar" type="text"
                        class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-xl px-4 py-3 text-[#FAF8F5] font-sans focus:outline-none focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] transition-all">
                </div>
                <div>
                    <label
                        class="block text-xs font-mono text-[#FAF8F5]/50 uppercase tracking-widest mb-2 flex justify-between">
                        <span>Description</span>
                    </label>
                    <textarea v-model="newChar.description"
                        class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-xl px-4 py-3 text-[#FAF8F5] font-sans focus:outline-none focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] transition-all h-64 resize-y"></textarea>
                </div>
                <div>
                    <label class="block text-xs font-mono text-[#FAF8F5]/50 uppercase tracking-widest mb-2">Prompt
                        Prefix</label>
                    <input v-model="newChar.prompt_prefix" type="text"
                        class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-xl px-4 py-3 text-[#FAF8F5] font-sans focus:outline-none focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] transition-all">
                </div>
            </div>
            <div class="flex justify-end gap-4 mt-8 pt-6 border-t border-[#2A2A35]">
                <button @click="showCreateModal = false"
                    class="px-5 py-2.5 font-sans font-medium text-[#FAF8F5]/60 hover:text-[#FAF8F5] transition-colors">Discard</button>
                <button @click="saveCharacter"
                    class="px-6 py-2.5 bg-[#C9A84C] text-[#0D0D12] rounded-xl font-bold font-sans shadow-[0_0_15px_rgba(201,168,76,0.2)] hover:shadow-[0_0_25px_rgba(201,168,76,0.4)] transition-all">
                    {{ isEditing ? 'Save Changes' : 'Manifest' }}
                </button>
            </div>
        </div>
    </div>

    <!-- Create Post Modal -->
    <div v-if="showCreatePostModal"
        class="fixed inset-0 bg-[#0D0D12]/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
        <div
            class="bg-[#14141A] rounded-2xl border border-[#2A2A35] p-8 w-full max-w-3xl max-h-[90vh] overflow-y-auto shadow-[0_20px_50px_rgba(0,0,0,0.5)] custom-scrollbar">
            <h2 class="text-2xl font-bold font-sans tracking-tight text-[#FAF8F5] mb-6">Compose Chronicle</h2>

            <div class="space-y-6">
                <div v-if="!selectedCharacterId && postCharId === null">
                    <label class="block text-xs font-mono text-[#FAF8F5]/50 uppercase tracking-widest mb-2">Author
                        (Character)</label>
                    <select v-model="postCharId"
                        class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-xl px-4 py-3 text-[#FAF8F5] font-sans focus:outline-none focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] transition-all appearance-none cursor-pointer">
                        <option :value="null" disabled>Select an entity...</option>
                        <option v-for="char in characters" :key="char.id" :value="char.id">{{ char.name }}</option>
                    </select>
                </div>

                <div>
                    <label
                        class="block text-xs font-mono text-[#FAF8F5]/50 uppercase tracking-widest mb-2">Narrative</label>
                    <textarea v-model="newPost.title"
                        class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-xl px-4 py-3 text-[#FAF8F5] font-sans focus:outline-none focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] transition-all h-28 resize-none"
                        placeholder="What transpires?"></textarea>
                </div>
                <div>
                    <label class="block text-xs font-mono text-[#FAF8F5]/50 uppercase tracking-widest mb-2">Visual
                        Record (URL)</label>
                    <input v-model="newPost.image_url" type="text"
                        class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-xl px-4 py-3 text-[#FAF8F5] font-sans focus:outline-none focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] transition-all"
                        placeholder="Leave empty to use concept data">
                </div>

                <div class="border-t border-[#2A2A35] pt-6 mt-2">
                    <h3 class="text-[15px] font-sans font-semibold text-[#FAF8F5] mb-4 flex items-center gap-2">
                        <span class="w-1.5 h-1.5 rounded-full bg-[#C9A84C]"></span> Conceptual Parameters
                    </h3>
                    <div class="grid grid-cols-2 gap-5">
                        <div>
                            <label
                                class="block text-xs font-mono text-[#FAF8F5]/50 uppercase tracking-widest mb-2">Rating</label>
                            <select v-model="newPost.image.rating"
                                class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-xl px-4 py-3 text-[#FAF8F5] font-sans focus:outline-none focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] transition-all appearance-none cursor-pointer">
                                <option value="safe">Safe</option>
                                <option value="sensitive">Sensitive</option>
                                <option value="questionable">Questionable</option>
                                <option value="explicit">Explicit</option>
                            </select>
                        </div>
                        <div>
                            <label
                                class="block text-xs font-mono text-[#FAF8F5]/50 uppercase tracking-widest mb-2">Appearance</label>
                            <input v-model="newPost.image.appearance" type="text"
                                class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-xl px-4 py-3 text-[#FAF8F5] font-sans focus:outline-none focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] transition-all">
                        </div>
                        <div>
                            <label
                                class="block text-xs font-mono text-[#FAF8F5]/50 uppercase tracking-widest mb-2">Attire</label>
                            <input v-model="newPost.image.clothing" type="text"
                                class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-xl px-4 py-3 text-[#FAF8F5] font-sans focus:outline-none focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] transition-all">
                        </div>
                        <div>
                            <label
                                class="block text-xs font-mono text-[#FAF8F5]/50 uppercase tracking-widest mb-2">Stance</label>
                            <input v-model="newPost.image.pose" type="text"
                                class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-xl px-4 py-3 text-[#FAF8F5] font-sans focus:outline-none focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] transition-all">
                        </div>
                        <div>
                            <label
                                class="block text-xs font-mono text-[#FAF8F5]/50 uppercase tracking-widest mb-2">Visage</label>
                            <input v-model="newPost.image.expression" type="text"
                                class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-xl px-4 py-3 text-[#FAF8F5] font-sans focus:outline-none focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] transition-all">
                        </div>
                        <div>
                            <label
                                class="block text-xs font-mono text-[#FAF8F5]/50 uppercase tracking-widest mb-2">Environment</label>
                            <input v-model="newPost.image.setting" type="text"
                                class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-xl px-4 py-3 text-[#FAF8F5] font-sans focus:outline-none focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] transition-all">
                        </div>
                        <div class="col-span-2">
                            <label
                                class="block text-xs font-mono text-[#FAF8F5]/50 uppercase tracking-widest mb-2">Signatures
                                (Tags)</label>
                            <input v-model="newPost.image.other_tags" type="text"
                                class="w-full bg-[#0D0D12] border border-[#2A2A35] rounded-xl px-4 py-3 text-[#FAF8F5] font-sans focus:outline-none focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C] transition-all">
                        </div>
                    </div>
                </div>
            </div>
            <div class="flex justify-end gap-4 mt-8 pt-6 border-t border-[#2A2A35]">
                <button @click="showCreatePostModal = false"
                    class="px-5 py-2.5 font-sans font-medium text-[#FAF8F5]/60 hover:text-[#FAF8F5] transition-colors">Discard</button>
                <button @click="createPost" :disabled="!postCharId && !selectedCharacterId"
                    class="px-6 py-2.5 bg-[#C9A84C] text-[#0D0D12] rounded-xl font-bold font-sans shadow-[0_0_15px_rgba(201,168,76,0.2)] hover:shadow-[0_0_25px_rgba(201,168,76,0.4)] transition-all disabled:opacity-50 disabled:hover:scale-100 disabled:hover:shadow-[0_0_15px_rgba(201,168,76,0.2)] disabled:cursor-not-allowed">Publish</button>
            </div>
        </div>
    </div>
</template>

<style scoped>
/* Custom scrollbar for the modal and profiles */
.custom-scrollbar::-webkit-scrollbar {
    width: 8px;
}

.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
    border-radius: 4px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #2A2A35;
    border-radius: 4px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #C9A84C;
}
</style>