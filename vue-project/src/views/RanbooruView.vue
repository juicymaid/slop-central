<template>
    <div class="flex flex-col items-center  h-screen bg-gray-900 text-white">
        <h1 class="text-4xl font-bold mb-6">Ranbooru Image Generator</h1>
        <p class="text-lg mb-4">Click the button below to generate a random image prompt.</p>
        <input v-model="query" type="text" placeholder="Enter your prompt here"
            class="w-full max-w-md p-3 mb-4 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <button @click="randomizePrompt"
            class="px-6 py-3 bg-blue-600 hover:bg-blue-500 transition rounded-lg text-white font-semibold">
            Generate Random Prompt
        </button>
        <div class="mt-6 w-full max-w-5xl grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <div
                v-for="(item, index) in currentPrompts"
                :key="index"
                @click="remix(item.prompt)"
                class="p-4 bg-gray-800 border border-gray-700 rounded-lg shadow-lg flex flex-col cursor-pointer"
            >
                <h2 class="text-xl font-semibold mb-2">Prompt {{ index + 1 }}</h2>
                <p class="mb-2 break-words truncate">{{ item.prompt }}</p>

                <template v-if="item.postUrl">
                    <video
                        v-if="/\.mp4(\?.*)?$/i.test(item.postUrl)"
                        :src="item.postUrl"
                        controls
                        muted
                        loop
                        playsinline
                        class="w-full h-auto rounded-lg mb-2 cursor-pointer"
                        @click="showImage = item"
                    ></video>
                    <img
                        v-else
                        :src="item.postUrl"
                        alt="Generated Image"
                        class="w-full h-auto rounded-lg mb-2 cursor-pointer"
                        @click="showImage = item"
                    />
                </template>
            </div>
        </div>
    </div>
</template>


<script setup>
import { ref } from 'vue';
import { getRandomPrompt } from '@/scripts/ranbooru';
import { webState } from '@/api';

const query = ref('');

const currentPrompts = ref([

]);

function remix(prompt) {
    webState.remixImage = {
        Prompt: prompt,
    }
}

async function randomizePrompt() {

    let count = 10;
    currentPrompts.value = []; // Clear previous prompts

    console.log('Generating', count, 'random prompts with query:', query.value);

    for (let i = 0; i < count; i++) {
        const prompts = await getRandomPrompt({
            booru: 'rule34',           // Which booru to use
            tags: query.value,    // Search tags
            basePrompt: '',    // Base prompt to prepend
            shuffleTags: true,            // Randomize tag order
            maxTags: 50,                  // Limit number of tags
            changeBackground: 'Add Background', // Background modification
            rating: 'All'                // Content rating filter
        });
        // Ensure we always have an array to spread
        const items = Array.isArray(prompts) ? prompts : [prompts];
        currentPrompts.value.push(...items);
    }

}
</script>