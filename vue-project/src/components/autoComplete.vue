<script setup>
import { GetFromApi } from '@/api';
import { onMounted, onUnmounted, ref, watch } from 'vue';



const emit = defineEmits(['update:input'])

const tags = ref([])

const results = ref([])

const selectedIndex = ref(0)

const isFocused = ref(false)

const cursorPosition = ref(0)

const currentTagStart = ref(0)

const currentTagEnd = ref(0)

const categoryMap = {
    "-1": "Invalid",
    "0": "General",
    "1": "Artist",
    "3": "Copyright",
    "4": "Character",
    "5": "Meta",

    "6": "Wildcard",
};
const categoryColorMap = {
    "-1": ["red", "maroon"],
    "0": ["lightblue", "dodgerblue"],
    "1": ["indianred", "firebrick"],
    "3": ["violet", "darkorchid"],
    "4": ["lightgreen", "darkgreen"],
    "5": ["orange", "darkorange"],

    "6": ["gray", "dimgray"],
}

const props = defineProps({
    input: {
        type: String,
        required: true
    },
    textareaRef: {
        type: null,
        default: null
    }
})  

function handleFocus() {
    isFocused.value = true
    updateCursorPosition()
}

function handleBlur() {
    isFocused.value = false
    setTimeout(() => {
        results.value = []
        lastSearchTerm = null
    }, 200)
}

function attachListeners() {
    if (props.textareaRef) {
        props.textareaRef.addEventListener('input', updateCursorPosition)
        props.textareaRef.addEventListener('click', updateCursorPosition)
        props.textareaRef.addEventListener('keyup', updateCursorPosition)
        props.textareaRef.addEventListener('focus', handleFocus)
        props.textareaRef.addEventListener('blur', handleBlur)
    }
}

watch(() => props.textareaRef, (newVal, oldVal) => {
    if (newVal && !oldVal) {
        attachListeners()
    }
})

onMounted(async () => {
    // Set up event listeners for cursor position and focus
    attachListeners()
    
    var csv = await fetch("/tags.csv")
        .then(response => response.text())
    var lines = csv.split("\n")
    
    var wildcardsData = await GetFromApi("wildcards")
    if (wildcardsData && wildcardsData.wildcards) {
        for (var w of wildcardsData.wildcards) {
            tags.value.push({
                tag: "__" + w + "__",
                category: "6",
                count: 0,
                aliases: []
            })
        }
    }

    //format 
    //tag,category,count,aliases
    //1girl,0,6008644,"1girls,sole_female"
    //aliases are seperated by commas

    for (var i = 0; i < lines.length; i++) {
        var line = lines[i].trim()
        var parts = line.split(",");

        if(parts.length >= 2) {
            var tag = parts[0].trim()
            var category = parts[1].trim()
            var count = parts[2] ? parseInt(parts[2].trim()) : 0
            var aliases = parts.slice(3).map(alias => alias.trim())

            tags.value.push({
                tag: tag.replaceAll("_", " "),
                category: category,
                count: count,
                aliases: aliases
            })
        }
    }

    window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
    window.removeEventListener('keydown', handleKeyDown)
    
    // Clean up textarea event listeners
    if (props.textareaRef) {
        props.textareaRef.removeEventListener('input', updateCursorPosition)
        props.textareaRef.removeEventListener('click', updateCursorPosition)
        props.textareaRef.removeEventListener('keyup', updateCursorPosition)
        props.textareaRef.removeEventListener('focus', handleFocus)
        props.textareaRef.removeEventListener('blur', handleBlur)
    }
})

let searchTimer = null
let lastSearchTerm = null
var currentTag = ''

function updateCursorPosition() {
    if (props.textareaRef && props.textareaRef.selectionStart !== undefined) {
        cursorPosition.value = props.textareaRef.selectionStart
        findCurrentTag()
    }
}

function findCurrentTag() {
    const text = props.input
    const cursor = cursorPosition.value
    
    // Find the start and end of the current tag segment
    let start = cursor
    let end = cursor
    
    // Find start of current tag (go backwards to find comma or start of string)
    while (start > 0 && text[start - 1] !== ',') {
        start--
    }
    
    // Find end of current tag (go forwards to find comma or end of string)
    while (end < text.length && text[end] !== ',') {
        end++
    }
    
    currentTagStart.value = start
    currentTagEnd.value = end
    
    // Extract the current tag and trim whitespace
    currentTag = text.substring(start, end).trim().toLowerCase()
    
    // Only search if the tag has changed to avoid resetting selectedIndex on non-mutating events
    if (currentTag === lastSearchTerm) return
    lastSearchTerm = currentTag
    
    // Trigger search with the current tag
    searchForTags(currentTag)
}

function searchForTags(searchTerm) {
    if (!isFocused.value || !searchTerm || searchTerm.length < 2) {
        results.value = []
        return
    }
    
    clearTimeout(searchTimer)
    searchTimer = setTimeout(() => {
        var matchingTags = tags.value.filter(t => {
            const matchesTag = t.tag.includes(searchTerm)
            const matchesAlias = t.aliases.some(alias => alias.includes(searchTerm))
            
            // Filter out wildcards if no underscores are present in the search term
            if (t.category === "6" && !searchTerm.includes('_')) {
                return false
            }
            
            return matchesTag || matchesAlias
        })
        results.value = matchingTags.slice(0, 10)
        selectedIndex.value = 0
    }, 50)
}

watch(() => props.input, () => {
    updateCursorPosition()
})

function handleKeyDown(e) {
    if (!results.value.length) return

    if (e.key === 'ArrowDown') {
        e.preventDefault()
        selectedIndex.value = (selectedIndex.value + 1) % results.value.length
    } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        selectedIndex.value = (selectedIndex.value - 1 + results.value.length) % results.value.length
    } else if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault()
        ApplyTag(results.value[selectedIndex.value])
    } else if (e.key === 'Escape') {
        results.value = []
        lastSearchTerm = null
    }
}

function ApplyTag(result) {
    var insertion = result.tag
    var text = props.input
    
    // Replace the current tag at cursor position
    var beforeTag = text.substring(0, currentTagStart.value)
    var afterTag = text.substring(currentTagEnd.value)
    
    // Add spacing if needed
    var spacing = ''
    if (currentTagStart.value > 0 && !beforeTag.endsWith(' ')) {
        spacing = ' '
    }
    
    var newText = beforeTag + spacing + insertion + ', ' + afterTag
    emit('update:input', newText)
    results.value = []
    
    // Update cursor position to after the inserted tag
    setTimeout(() => {
        if (props.textareaRef) {
            props.textareaRef.focus()
            var newCursorPos = currentTagStart.value + spacing.length + insertion.length + 2
            props.textareaRef.setSelectionRange(newCursorPos, newCursorPos)
            updateCursorPosition()
        }
    }, 0)
}

</script>

<template>
    <div v-if="results.length > 0" class="absolute z-50 w-full bg-[#1A1A24]/90 backdrop-blur-xl rounded-[2rem] border border-[#2A2A35] overflow-y-auto p-3 max-h-64 top-full mt-2 shadow-[0_8px_30px_rgb(0,0,0,0.5)]">
        <div v-for="(result, index) in results" :key="result.tag"
             @click="ApplyTag(result)"
             @mouseenter="selectedIndex = index"
             :class="['px-4 py-2.5 rounded-2xl cursor-pointer transition-colors flex items-center mb-1 last:mb-0',
                      index === selectedIndex ? 'bg-[#2A2A35] shadow-inner' : 'hover:bg-[#2A2A35]/50']"
             :style="{ borderLeft: `4px solid ${categoryColorMap[result.category][0]}` }">
            <div class="flex justify-between items-center w-full ml-2">
                <span class="font-sans font-medium text-[#FAF8F5]">{{ result.tag }}</span>
                <span class="text-xs text-[#FAF8F5]/60 flex items-center font-mono">
                    <span class="inline-block px-2 py-1 rounded-md text-[10px] uppercase tracking-widest mr-3 font-sans font-bold shadow-sm"
                          :style="{ backgroundColor: categoryColorMap[result.category][1], color: 'white' }">
                        {{ categoryMap[result.category] }}
                    </span>
                    <span>{{ result.count.toLocaleString() }}</span>
                </span>
            </div>
        </div>
    </div>
</template>