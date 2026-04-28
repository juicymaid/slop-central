<script setup>
import { computed, reactive, ref } from 'vue';

const categories = [
    {
        key: 'hairColor',
        label: 'Hair color',
        multi: false,
        options: ['black hair', 'brown hair', 'blonde hair', 'red hair', 'white hair', 'pink hair', 'blue hair', 'green hair', 'purple hair', 'silver hair']
    },
    {
        key: 'eyeColor',
        label: 'Eye color',
        multi: false,
        options: ['brown eyes', 'blue eyes', 'green eyes', 'hazel eyes', 'gray eyes', 'amber eyes', 'purple eyes', 'red eyes']
    },
    {
        key: 'hairStyle',
        label: 'Hair style',
        multi: false,
        options: ['long hair', 'short hair', 'bob cut', 'ponytail', 'twin tails', 'braid', 'curly hair', 'straight hair', 'wavy hair', 'messy hair', 'bangs']
    },
    {
        key: 'bodyShape',
        label: 'Body shape',
        multi: false,
        options: ['petite', 'slim', 'athletic', 'curvy', 'chubby', 'tall']
    },
    {
        key: 'breastSize',
        label: 'Breast size',
        multi: false,
        options: ['small breasts', 'medium breasts', 'large breasts']
    },
    {
        key: 'clothes',
        label: 'Clothes',
        multi: true,
        options: ['t-shirt', 'hoodie', 'dress', 'school uniform', 'sweater', 'jacket', 'coat', 'skirt', 'jeans', 'shorts', 'bikini', 'swimsuit', 'lingerie', 'suit', 'kimono']
    },
    {
        key: 'extras',
        label: 'Extras',
        multi: true,
        options: ['smile', 'blush', 'glasses', 'earrings', 'hair ornament', 'choker', 'tattoo', 'freckles', 'makeup']
    }
];

const selections = reactive(
    categories.reduce((acc, cat) => {
        acc[cat.key] = cat.multi ? [] : '';
        return acc;
    }, {})
);

const customTagInput = ref('');
const customTags = ref([]);

const isSelected = (catKey, option) => {
    const value = selections[catKey];
    return Array.isArray(value) ? value.includes(option) : value === option;
};

const toggleOption = (catKey, option) => {
    const value = selections[catKey];
    if (Array.isArray(value)) {
        const idx = value.indexOf(option);
        if (idx >= 0) value.splice(idx, 1);
        else value.push(option);
        return;
    }
    selections[catKey] = value === option ? '' : option;
};

const removeTag = (tag) => {
    for (const cat of categories) {
        const value = selections[cat.key];
        if (Array.isArray(value)) {
            const idx = value.indexOf(tag);
            if (idx >= 0) value.splice(idx, 1);
        } else if (value === tag) {
            selections[cat.key] = '';
        }
    }
    const cIdx = customTags.value.indexOf(tag);
    if (cIdx >= 0) customTags.value.splice(cIdx, 1);
};

const addCustomTag = () => {
    const raw = customTagInput.value || '';
    const next = raw
        .split(',')
        .map(s => s.trim())
        .filter(Boolean);
    for (const tag of next) {
        if (!customTags.value.includes(tag)) customTags.value.push(tag);
    }
    customTagInput.value = '';
};

const resetAll = () => {
    for (const cat of categories) {
        selections[cat.key] = cat.multi ? [] : '';
    }
    customTags.value = [];
    customTagInput.value = '';
};

const selectedTags = computed(() => {
    const ordered = [];
    for (const cat of categories) {
        const value = selections[cat.key];
        if (Array.isArray(value)) ordered.push(...value);
        else if (value) ordered.push(value);
    }
    ordered.push(...customTags.value);
    // De-dupe while preserving order
    return [...new Set(ordered)];
});

const prompt = computed(() => selectedTags.value.join(', '));

const pillBase = 'inline-flex items-center rounded-full border px-3 py-1 text-sm transition select-none';
const pillOn = 'bg-slate-200 text-slate-900 border-slate-200 dark:bg-slate-100 dark:text-slate-900 dark:border-slate-100';
const pillOff = 'bg-transparent text-slate-200 border-slate-600 hover:border-slate-400 hover:bg-slate-900/40 dark:text-slate-200 dark:border-slate-700 dark:hover:border-slate-500 dark:hover:bg-slate-800/50';
</script>

<template>
    <div class="min-h-screen bg-slate-950 text-slate-100">
        <div class="mx-auto max-w-6xl px-4 py-8">
            <div class="flex items-start justify-between gap-4">
                <div>
                    <h1 class="text-2xl font-semibold tracking-tight">Generator</h1>
                    <p class="mt-1 text-sm text-slate-300">Pick traits using pills; your prompt updates instantly.</p>
                </div>
                <button
                    type="button"
                    class="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800"
                    @click="resetAll"
                >
                    Reset
                </button>
            </div>

            <div class="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
                <!-- Options -->
                <div class="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
                    <div class="space-y-6">
                        <div v-for="cat in categories" :key="cat.key">
                            <div class="flex items-center justify-between gap-3">
                                <h2 class="text-sm font-semibold text-slate-200">{{ cat.label }}</h2>
                                <span class="text-xs text-slate-400">{{ cat.multi ? 'Multi-select' : 'Single-select' }}</span>
                            </div>
                            <div class="mt-3 flex flex-wrap gap-2">
                                <button
                                    v-for="opt in cat.options"
                                    :key="opt"
                                    type="button"
                                    :class="[pillBase, isSelected(cat.key, opt) ? pillOn : pillOff]"
                                    :aria-pressed="isSelected(cat.key, opt)"
                                    @click="toggleOption(cat.key, opt)"
                                >
                                    {{ opt }}
                                </button>
                            </div>
                        </div>

                        <div>
                            <h2 class="text-sm font-semibold text-slate-200">Custom tags</h2>
                            <p class="mt-1 text-xs text-slate-400">Add any extra tags (comma-separated).</p>
                            <div class="mt-3 flex gap-2">
                                <input
                                    v-model="customTagInput"
                                    type="text"
                                    class="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500"
                                    placeholder="e.g. high detail, soft lighting"
                                    @keydown.enter.prevent="addCustomTag"
                                />
                                <button
                                    type="button"
                                    class="shrink-0 rounded-lg bg-slate-100 px-3 py-2 text-sm font-medium text-slate-900 hover:bg-white"
                                    @click="addCustomTag"
                                >
                                    Add
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Output -->
                <div class="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
                    <h2 class="text-sm font-semibold text-slate-200">Selected tags</h2>
                    <div v-if="selectedTags.length" class="mt-3 flex flex-wrap gap-2">
                        <span
                            v-for="tag in selectedTags"
                            :key="tag"
                            class="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-sm text-slate-200"
                        >
                            {{ tag }}
                            <button
                                type="button"
                                class="text-slate-400 hover:text-red-400"
                                @click="removeTag(tag)"
                                aria-label="Remove tag"
                                title="Remove"
                            >
                                ×
                            </button>
                        </span>
                    </div>
                    <p v-else class="mt-3 text-sm text-slate-400">No tags selected yet.</p>

                    <h2 class="mt-6 text-sm font-semibold text-slate-200">Prompt</h2>
                    <textarea
                        class="mt-3 h-40 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-500"
                        readonly
                        :rows="6"
                        :value="prompt"
                        placeholder="Your prompt will appear here…"
                    ></textarea>
                    <p class="mt-2 text-xs text-slate-400">This is just a comma-separated list of your selected pills.</p>
                </div>
            </div>
        </div>
    </div>
</template>