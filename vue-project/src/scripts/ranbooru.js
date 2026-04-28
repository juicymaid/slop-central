/**
 * Ranbooru JavaScript Implementation
 * Fetches random prompts from various booru sites
 */

import { apiUrl } from "@/api";

const POST_AMOUNT = 100;
let COUNT = 100;

// Bad tags to remove
const BAD_TAGS = [
    'mixed-language_text', 'watermark', 'text', 'english_text', 'speech_bubble', 
    'signature', 'artist_name', 'censored', 'bar_censor', 'translation', 
    'twitter_username', 'twitter_logo', 'patreon_username', 'commentary_request', 
    'tagme', 'commentary', 'character_name', 'mosaic_censoring', 'instagram_username', 
    'text_focus', 'english_commentary', 'comic', 'translation_request', 'fake_text', 
    'translated', 'paid_reward_available', 'thought_bubble', 'multiple_views', 
    'silent_comic', 'out-of-frame_censoring', 'symbol-only_commentary', '3koma', 
    '2koma', 'character_watermark', 'spoken_question_mark', 'japanese_text', 
    'spanish_text', 'language_text', 'fanbox_username', 'commission', 'original', 
    'ai_generated', 'stable_diffusion', 'tagme_(artist)', 'text_bubble', 'qr_code', 
    'chinese_commentary', 'korean_text', 'partial_commentary', 'chinese_text', 
    'copyright_request', 'heart_censor', 'censored_nipples', 'page_number', 'scan', 
    'fake_magazine_cover', 'korean_commentary'
];

// Background tags
const COLORED_BG = [
    'black_background', 'aqua_background', 'white_background', 'colored_background', 
    'gray_background', 'blue_background', 'green_background', 'red_background', 
    'brown_background', 'purple_background', 'yellow_background', 'orange_background', 
    'pink_background', 'plain', 'transparent_background', 'simple_background', 
    'two-tone_background', 'grey_background'
];

const ADD_BG = ['outdoors', 'indoors'];
const BW_BG = ['monochrome', 'greyscale', 'grayscale'];

// Rating mappings
const RATINGS = {
    "e621": { "All": "All", "Safe": "safe", "Questionable": "questionable", "Explicit": "explicit" },
    "danbooru": { "All": "All", "Safe": "g", "Sensitive": "s", "Questionable": "q", "Explicit": "e" },
    "aibooru": { "All": "All", "Safe": "safe", "Questionable": "questionable", "Explicit": "explicit" },
    "yande.re": { "All": "All", "Safe": "safe", "Questionable": "questionable", "Explicit": "explicit" },
    "konachan": { "All": "All", "Safe": "safe", "Questionable": "questionable", "Explicit": "explicit" },
    "safebooru": { "All": "All" },
    "rule34": { "All": "All", "Safe": "safe", "Questionable": "questionable", "Explicit": "explicit" },
    "xbooru": { "All": "All", "Safe": "safe", "Questionable": "questionable", "Explicit": "explicit" },
    "gelbooru": { "All": "All", "Safe": "g", "Sensitive": "s", "Questionable": "q", "Explicit": "e" }
};

/**
 * Fetch data from different booru APIs
 */
async function fetchBooruData(booru, tags = '', maxPages = 10, rating = 'All', postId = '') {
    const page = Math.floor(Math.random() * maxPages);
    let url = '';
    let addTags = tags ? `+${tags.replace(/,/g, '+')}` : '';
    
    // Add rating filter if not 'All'
    if (rating !== 'All' && RATINGS[booru][rating]) {
        addTags += `+rating:${RATINGS[booru][rating]}`;
    }

    // Always exclude animated content
    addTags = `-animated${addTags}`;
    addTags += ' -furry -furry_focus -futa_only -futanari -gay -male/male -male_only -male_penetrating_male -penis_focus -penis_size_difference -tentacle_on_male -1futa -femboy -bara_tits -bara -anthro -canine_genitalia -male_masturbation -reptile '

    addTags = addTags.replace(" ", "+")


    switch (booru) {
        case 'gelbooru':
            url = `https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit=${POST_AMOUNT}&pid=${page}&tags=${encodeURIComponent(addTags)}`;
            break;
        case 'safebooru':
            url = `https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1&limit=${POST_AMOUNT}&pid=${page}&tags=${encodeURIComponent(addTags)}`;
            break;
        case 'rule34':
            url = `https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&api_key=1eee46ec7bc85a93e10cd74310ebab08db0ac7a45baba8f1173286902286676889c783342bc3a0a467d18e24a74e6f56e9d078225c717e1055c2ee3192f44ddf&user_id=1696472&json=1&limit=${POST_AMOUNT}&pid=${page}&tags=${encodeURIComponent(addTags)}`;
            break;
        case 'danbooru':
            url = `https://danbooru.donmai.us/posts.json?limit=${POST_AMOUNT}&page=${page}&tags=${encodeURIComponent(addTags)}`;
            break;
        case 'konachan':
            url = `https://konachan.com/post.json?limit=${POST_AMOUNT}&page=${page}&tags=${encodeURIComponent(addTags)}`;
            break;
        case 'yande.re':
            url = `https://yande.re/post.json?limit=${POST_AMOUNT}&page=${page}&tags=${encodeURIComponent(addTags)}`;
            break;
        case 'aibooru':
            url = `https://aibooru.online/posts.json?limit=${POST_AMOUNT}&page=${page}&tags=${encodeURIComponent(addTags)}`;
            break;
        case 'xbooru':
            url = `https://xbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit=${POST_AMOUNT}&pid=${page}&tags=${encodeURIComponent(addTags)}`;
            break;
        case 'e621':
            url = `https://e621.net/posts.json?limit=${POST_AMOUNT}&page=${page}&tags=${encodeURIComponent(addTags)}`;
            break;
        default:
            throw new Error(`Unsupported booru: ${booru}`);
    }

    console.log(`Fetching from ${booru}:`, url);

    url = apiUrl + "/proxy?url=" + encodeURIComponent(url);

    try {
        const response = await fetch(url, {
            headers: {
                'User-Agent': 'RanbooruJS/1.0'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return normalizeData(data, booru);
    } catch (error) {
        console.error(`Error fetching from ${booru}:`, error);
        throw error;
    }
}

/**
 * Normalize data structure across different booru APIs
 */
function normalizeData(data, booru) {
    let posts = [];

    switch (booru) {
        case 'gelbooru':
            posts = data.post || [];
            COUNT = data['@attributes']?.count || posts.length;
            break;
        case 'e621':
            posts = data.posts || [];
            // Normalize e621 tags structure
            posts = posts.map(post => ({
                ...post,
                tags: flattenE621Tags(post.tags),
                score: post.score?.total || 0
            }));
            break;
        case 'danbooru':
        case 'aibooru':
            posts = data || [];
            // Normalize tag field
            posts = posts.map(post => ({
                ...post,
                tags: post.tag_string || post.tags
            }));
            break;
        case 'xbooru':
        case 'safebooru':
            posts = data || [];
            // Add full URL for these sites
            posts = posts.map(post => ({
                ...post,
                file_url: post.file_url || `https://${booru === 'xbooru' ? 'xbooru.com' : 'safebooru.org'}/images/${post.directory}/${post.image}`
            }));
            break;
        default:
            posts = data || [];
    }

    COUNT = posts.length;
    return { post: posts };
}

/**
 * Flatten e621 tags structure
 */
function flattenE621Tags(tags) {
    if (typeof tags === 'string') return tags;
    
    const sublevels = ['general', 'artist', 'copyright', 'character', 'species'];
    let allTags = [];
    
    for (const sublevel of sublevels) {
        if (tags[sublevel]) {
            allTags = allTags.concat(tags[sublevel]);
        }
    }
    
    return allTags.join(' ');
}

/**
 * Clean tags by removing bad tags and unwanted content
 */
function cleanTags(tags, removeTags = [], changeDash = false) {
    let tagList = tags.split(/[,\s]+/).filter(tag => tag.trim());
    
    // Remove bad tags
    const allBadTags = [...BAD_TAGS, ...removeTags];
    tagList = tagList.filter(tag => {
        const cleanTag = tag.trim().toLowerCase();
        return !allBadTags.some(badTag => {
            if (badTag.includes('*')) {
                return cleanTag.includes(badTag.replace('*', ''));
            }
            return cleanTag === badTag.toLowerCase();
        });
    });

    // Convert underscores to spaces if requested
    if (changeDash) {
        tagList = tagList.map(tag => tag.replace(/_/g, ' '));
    }

    // Remove duplicates while preserving order
    const seen = new Set();
    tagList = tagList.filter(tag => {
        const cleanTag = tag.trim().toLowerCase();
        if (seen.has(cleanTag)) return false;
        seen.add(cleanTag);
        return true;
    });

    return tagList.join(', ');
}

/**
 * Apply background modifications
 */
function modifyBackground(prompt, changeBackground) {
    let additionalPrompt = '';
    let tagsToRemove = [];

    switch (changeBackground) {
        case 'Add Background':
            additionalPrompt = `detailed_background, ${ADD_BG[Math.floor(Math.random() * ADD_BG.length)]}`;
            tagsToRemove = COLORED_BG;
            break;
        case 'Remove Background':
            const randomBg = COLORED_BG[Math.floor(Math.random() * COLORED_BG.length)];
            additionalPrompt = `plain_background, simple_background, ${randomBg}`;
            tagsToRemove = ADD_BG;
            break;
        case 'Remove All':
            tagsToRemove = [...COLORED_BG, ...ADD_BG];
            break;
    }

    return { additionalPrompt, tagsToRemove };
}

/**
 * Apply color modifications
 */
function modifyColor(prompt, changeColor) {
    let additionalPrompt = '';
    let tagsToRemove = [];

    switch (changeColor) {
        case 'Colored':
            tagsToRemove = BW_BG;
            break;
        case 'Limited Palette':
            additionalPrompt = '(limited_palette:1.3)';
            break;
        case 'Monochrome':
            additionalPrompt = BW_BG.join(', ');
            break;
    }

    return { additionalPrompt, tagsToRemove };
}

/**
 * Shuffle array elements
 */
function shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

/**
 * Limit the number of tags in a prompt
 */
function limitTags(prompt, limit, mode = 'percentage') {
    const tags = prompt.split(',').map(tag => tag.trim()).filter(tag => tag);
    
    if (mode === 'percentage') {
        const numTags = Math.floor(tags.length * limit);
        return tags.slice(0, numTags).join(', ');
    } else if (mode === 'max') {
        return tags.slice(0, limit).join(', ');
    }
    
    return prompt;
}

/**
 * Main function to get a random prompt from booru
 */
export async function getRandomPrompt(options = {}) {
    var {
        booru = 'safebooru',
        tags = '',
        maxPages = 10,
        rating = 'All',
        removeTags = [],
        removeBadTags = true,
        shuffleTags = true,
        changeDash = true,
        changeBackground = "Don't Change",
        changeColor = "Colored",
        sortingOrder = 'Random',
        limitTagsPercent = 1.0,
        maxTags = 100,
        basePrompt = ''
    } = options;

    try {

        console.log('Fetching random prompt with query:', tags)

        // Fetch data from booru
        const data = await fetchBooruData(booru, tags, maxPages, rating);
        
        if (!data.post || data.post.length === 0) {
            throw new Error('No posts found with the given tags');
        }

        // Sort posts if needed
        let posts = data.post;
        if (sortingOrder === 'High Score') {
            posts.sort((a, b) => (b.score || 0) - (a.score || 0));
        } else if (sortingOrder === 'Low Score') {
            posts.sort((a, b) => (a.score || 0) - (b.score || 0));
        }

        // Select random post
        const randomIndex = Math.floor(Math.random() * posts.length);
        const selectedPost = posts[randomIndex];

        // Get and clean tags
        let postTags = selectedPost.tags || '';
        if (typeof postTags !== 'string') {
            postTags = String(postTags);
        }

        // Apply modifications
        let finalPrompt = basePrompt;
        let allRemoveTags = [...removeTags];

        // Handle background changes
        if (changeBackground !== "Don't Change") {
            const bgMod = modifyBackground(finalPrompt, changeBackground);
            if (bgMod.additionalPrompt) {
                finalPrompt = finalPrompt ? `${finalPrompt}, ${bgMod.additionalPrompt}` : bgMod.additionalPrompt;
            }
            allRemoveTags = [...allRemoveTags, ...bgMod.tagsToRemove];
        }

        // Handle color changes
        if (changeColor !== "Don't Change") {
            const colorMod = modifyColor(finalPrompt, changeColor);
            if (colorMod.additionalPrompt) {
                finalPrompt = finalPrompt ? `${finalPrompt}, ${colorMod.additionalPrompt}` : colorMod.additionalPrompt;
            }
            allRemoveTags = [...allRemoveTags, ...colorMod.tagsToRemove];
        }

        // Clean the post tags
        const cleanedTags = cleanTags(
            postTags, 
            removeBadTags ? allRemoveTags : removeTags, 
            changeDash
        );

        // Shuffle tags if requested
        let finalTags = cleanedTags;
        if (shuffleTags && cleanedTags) {
            const tagArray = cleanedTags.split(',').map(tag => tag.trim());
            const shuffledTags = shuffleArray(tagArray);
            finalTags = shuffledTags.join(', ');
        }

        // Limit tags
        if (limitTagsPercent < 1.0) {
            finalTags = limitTags(finalTags, limitTagsPercent, 'percentage');
        }
        if (maxTags < 100) {
            finalTags = limitTags(finalTags, maxTags, 'max');
        }

        // Combine with base prompt
        const result = finalPrompt && finalTags ? 
            `${finalPrompt}, ${finalTags}` : 
            finalPrompt || finalTags;

        return {
            prompt: result,
            originalTags: postTags,
            postUrl: selectedPost.file_url || selectedPost.preview_url,
            postId: selectedPost.id,
            score: selectedPost.score || 0,
            booru: booru
        };

    } catch (error) {
        console.error('Error getting random prompt:', error);
        throw error;
    }
}


