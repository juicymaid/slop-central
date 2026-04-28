let settingState = {
    opts: null,
    tag_usage: [],
}

let opts = {}

//#region Globals
// Core components
var TAC_CFG = null;
var tagBasePath = "";
var modelKeywordPath = "";
var tacSelfTrigger = false;

// Tag completion data loaded from files
var allTags = [];
var translations = new Map();
var extras = [];
// Same for tag-likes
var wildcardFiles = [];
var wildcardExtFiles = [];
var yamlWildcards = [];
var umiWildcards = [];
var embeddings = [];
var hypernetworks = [];
var loras = [];
var lycos = [];
var modelKeywordDict = new Map();
var chants = [];
var styleNames = [];

// Selected model info for black/whitelisting
var currentModelHash = "";
var currentModelName = "";

// Current results
var results = [];
var resultCount = 0;

// Relevant for parsing
var previousTags = [];
var tagword = "";
var originalTagword = "";
let hideBlocked = false;

// Tag selection for keyboard navigation
var selectedTag = null;
var oldSelectedTag = null;
var resultCountBeforeNormalTags = 0;

// Lora keyword undo/redo history
var textBeforeKeywordInsertion = "";
var textAfterKeywordInsertion = "";
var lastEditWasKeywordInsertion = false;
var keywordInsertionUndone = false;

// UMI
var umiPreviousTags = [];

/// Extendability system:
/// Provides "queues" for other files of the script (or really any js)
/// to add functions to be called at certain points in the script.
/// Similar to a callback system, but primitive.

// Queues
const QUEUE_AFTER_INSERT = [];
const QUEUE_AFTER_SETUP = [];
const QUEUE_FILE_LOAD = [];
const QUEUE_AFTER_CONFIG_CHANGE = [];
const QUEUE_SANITIZE = [];

// List of parsers to try
const PARSERS = [];

//#endregion




//#region BaseParser
class FunctionNotOverriddenError extends Error {
    constructor(message = "", ...args) {
        super(message, ...args);
        this.message = message + " is an abstract base function and must be overwritten.";
    }
}

class BaseTagParser {
    triggerCondition = null;

    constructor(triggerCondition) {
        if (new.target === BaseTagParser) {
            throw new TypeError("Cannot construct abstract BaseCompletionParser directly");
        }
        this.triggerCondition = triggerCondition;
    }

    parse() {
        throw new FunctionNotOverriddenError("parse()");
    }
}
//#endregion




//#region AUTO-COMPLETE



const styleColors = {
    "--results-neutral-text": ["#e0e0e0", "black"],
    "--results-bg": ["#0b0f19", "#ffffff"],
    "--results-border-color": ["#4b5563", "#e5e7eb"],
    "--results-border-width": ["1px", "1.5px"],
    "--results-bg-odd": ["#111827", "#f9fafb"],
    "--results-hover": ["#1f2937", "#f5f6f8"],
    "--results-selected": ["#374151", "#e5e7eb"],
    "--meta-text-color": ["#6b6f7b", "#a2a9b4"],
    "--embedding-v1-color": ["lightsteelblue", "#2b5797"],
    "--embedding-v2-color": ["skyblue", "#2d89ef"],
    "--live-translation-rt": ["whitesmoke", "#222"],
    "--live-translation-color-1": ["lightskyblue", "#2d89ef"],
    "--live-translation-color-2": ["palegoldenrod", "#eb5700"],
    "--live-translation-color-3": ["darkseagreen", "darkgreen"],
}
const browserVars = {
    "--results-overflow-y": {
        "firefox": "scroll",
        "other": "auto"
    }
}
// Style for new elements. Gets appended to the Gradio root.
const autocompleteCSS = `
    #quicksettings [id^=setting_tac] {
        background-color: transparent;
        min-width: fit-content;
    }
    .autocompleteParent {
        display: flex;
        position: absolute;
        z-index: 999;
        max-width: calc(100% - 1.5rem);
        margin: 5px 0 0 0;
    }
    .autocompleteResults {
        background-color: var(--results-bg) !important;
        border: var(--results-border-width) solid var(--results-border-color) !important;
        color: var(--results-neutral-text) !important;
        border-radius: 12px !important;
        height: fit-content;
        flex-basis: fit-content;
        flex-shrink: 0;
        overflow-y: var(--results-overflow-y);
        overflow-x: hidden;
        word-break: break-word;
    }
    .sideInfo {
        display: none;
        position: relative;
        margin-left: 10px;
        height: 18rem;
        max-width: 16rem;
    }
    .sideInfo > img {
        object-fit: cover;
        height: 100%;
        width: 100%;
    }
    .autocompleteResultsList > li:nth-child(odd) {
        background-color: var(--results-bg-odd);
    }
    .autocompleteResultsList > li {
        list-style-type: none;
        padding: 10px;
        cursor: pointer;
    }
    .autocompleteResultsList > li:hover {
        background-color: var(--results-hover);
    }
    .autocompleteResultsList > li.selected {
        background-color: var(--results-selected);
    }
    .resultsFlexContainer {
        display: flex;
    }
    .acListItem {
        white-space: break-spaces;
        min-width: 100px;
    }
    .acMetaText {
        position: relative;
        flex-grow: 1;
        text-align: end;
        padding: 0 0 0 15px;
        white-space: nowrap;
        color: var(--meta-text-color);
    }
    .acMetaText.biased::before {
        content: "✨";
        margin-right: 2px;
    }
    .acWikiLink {
        padding: 0.5rem;
        margin: -0.5rem 0 -0.5rem -0.5rem;
    }
    .acWikiLink:hover {
        text-decoration: underline;
    }
    .acListItem.acEmbeddingV1 {
        color: var(--embedding-v1-color);
    }
    .acListItem.acEmbeddingV2 {
        color: var(--embedding-v2-color);
    }
    .acRuby {
        padding: var(--input-padding);
        color: #888;
        font-size: 0.8rem;
        user-select: none;
    }
    .acRuby > ruby {
        display: inline-flex;
        flex-direction: column-reverse;
        margin-top: 0.5rem;
        vertical-align: bottom;
        cursor: pointer;
    }
    .acRuby > ruby::hover {
        text-decoration: underline;
        text-shadow: 0 0 10px var(--live-translation-color-1);
    }
    .acRuby > :nth-child(3n+1) {
        color: var(--live-translation-color-1);
    }
    .acRuby > :nth-child(3n+2) {
        color: var(--live-translation-color-2);
    }
    .acRuby > :nth-child(3n+3) {
        color: var(--live-translation-color-3);
    }
    .acRuby > ruby > rt {
        line-height: 1rem;
        padding: 0px 5px 0px 0px;
        text-align: left;
        font-size: 1rem;
        color: var(--live-translation-rt);
    }
    .acListItem .acPathPart:nth-child(3n+1) {
        color: var(--live-translation-color-1);
    }
    .acListItem .acPathPart:nth-child(3n+2) {
        color: var(--live-translation-color-2);
    }
    .acListItem .acPathPart:nth-child(3n+3) {
        color: var(--live-translation-color-3);
    }
`;

async function loadTags(c) {


    // Load main tags and aliases
    if (allTags.length === 0 && c.tagFile && c.tagFile !== "None") {
        try {
            allTags = await loadCSV(`${tagBasePath}/${c.tagFile}`);
        } catch (e) {
            console.error("Error loading tags file: " + e);
            return;
        }
    }
    console.log("TAC: Loaded " + allTags.length + " tags from " + c.tagFile);
    await loadExtraTags(c);
}

async function loadExtraTags(c) {
    if (c.extra.extraFile && c.extra.extraFile !== "None") {
        try {
            extras = await loadCSV(`${tagBasePath}/${c.extra.extraFile}`);
            // Add translations to the main translation map for extra tags that have them
            extras.forEach(e => {
                if (e[4]) translations.set(e[0], e[4]);
            });
        } catch (e) {
            console.error("Error loading extra file: " + e);
            return;
        }
    }
}

async function loadTranslations(c) {
    if (c.translation.translationFile && c.translation.translationFile !== "None") {
        try {
            let tArray = await loadCSV(`${tagBasePath}/${c.translation.translationFile}`);
            tArray.forEach(t => {
                if (c.translation.oldFormat && t[2]) // if 2 doesn't exist, it's probably a new format file and the setting is on by mistake
                    translations.set(t[0], t[2]);
                else if (t[1])
                    translations.set(t[0], t[1]);
                else
                    translations.set(t[0], "Not found");
            });
        } catch (e) {
            console.error("Error loading translations file: " + e);
            return;
        }
    }
}

async function syncOptions() {

    if (settingState.opts !== null) {
        opts = settingState.opts;
    }

    if (opts == null) {
        opts = {
            // Main tag file
            tac_tagFile: "danbooru.csv",
            // Active in settings
            tac_active: true,
            tac_activeIn: {
                txt2img: true,
                img2img: true,
                negativePrompts: true,
                thirdParty: true,
                modelList: "",
                modelListMode: "Blacklist"
            },
            // Results related settings
            tac_slidingPopup: true,
            tac_maxResults: 5,
            tac_showAllResults: false,
            tac_resultStepLength: 100,
            tac_delayTime: 100,
            tac_useWildcards: true,
            tac_sortWildcardResults: true,
            tac_wildcardExclusionList: "",
            tac_skipWildcardRefresh: false,
            tac_useEmbeddings: true,
            tac_includeEmbeddingsInNormalResults: false,
            tac_useHypernetworks: true,
            tac_useLoras: true,
            tac_useLycos: true,
            tac_useLoraPrefixForLycos: true,
            tac_showWikiLinks: false,
            tac_showExtraNetworkPreviews: true,
            tac_modelSortOrder: "Name",
            tac_useStyleVars: false,
            // Frequency sorting settings
            tac_frequencySort: true,
            tac_frequencyFunction: "Logarithmic (weak)",
            tac_frequencyMinCount: 3,
            tac_frequencyMaxAge: 30,
            tac_frequencyRecommendCap: 10,
            tac_frequencyIncludeAlias: false,
            // Insertion related settings
            tac_replaceUnderscores: true,
            tac_escapeParentheses: true,
            tac_appendComma: true,
            tac_appendSpace: true,
            tac_alwaysSpaceAtEnd: true,
            tac_modelKeywordCompletion: "Never",
            tac_modelKeywordLocation: "Start of prompt",
            tac_wildcardCompletionMode: "To next folder level",
            // Alias settings
            tac_alias: {
                searchByAlias: true,
                onlyShowAlias: false
            },
            // Translation settings
            tac_translation: {
                translationFile: "None",
                oldFormat: false,
                searchByTranslation: true,
                liveTranslation: false,
            },
            // Extra file settings
            tac_extra: {
                extraFile: "extra-quality-tags.csv",
                addMode: "Insert before"
            },
            // Chant settings
            tac_chantFile: "demo-chants.json",
            tac_keymap: {
                "MoveUp": "ArrowUp",
                "MoveDown": "ArrowDown",
                "JumpUp": "PageUp",
                "JumpDown": "PageDown",
                "JumpToStart": "Home",
                "JumpToEnd": "End",
                "ChooseSelected": "Enter",
                "ChooseFirstOrSelected": "Tab",
                "Close": "Escape"
            },
            tac_colormap: {
                "danbooru": {
                    "-1": ["red", "maroon"],
                    "0": ["lightblue", "dodgerblue"],
                    "1": ["indianred", "firebrick"],
                    "3": ["violet", "darkorchid"],
                    "4": ["lightgreen", "darkgreen"],
                    "5": ["orange", "darkorange"]
                },
                "e621": {
                    "-1": ["red", "maroon"],
                    "0": ["lightblue", "dodgerblue"],
                    "1": ["gold", "goldenrod"],
                    "3": ["violet", "darkorchid"],
                    "4": ["lightgreen", "darkgreen"],
                    "5": ["tomato", "darksalmon"],
                    "6": ["red", "maroon"],
                    "7": ["whitesmoke", "black"],
                    "8": ["seagreen", "darkseagreen"]
                },
                "derpibooru": {
                    "-1": ["red", "maroon"],
                    "0": ["#60d160", "#3d9d3d"],
                    "1": ["#fff956", "#918e2e"],
                    "3": ["#fd9961", "#a14c2e"],
                    "4": ["#cf5bbe", "#6c1e6c"],
                    "5": ["#3c8ad9", "#1e5e93"],
                    "6": ["#a6a6a6", "#555555"],
                    "7": ["#47abc1", "#1f6c7c"],
                    "8": ["#7871d0", "#392f7d"],
                    "9": ["#df3647", "#8e1c2b"],
                    "10": ["#c98f2b", "#7b470e"],
                    "11": ["#e87ebe", "#a83583"]
                }
            }
        }
    }





    let newCFG = {
        // Main tag file
        tagFile: opts["tac_tagFile"],
        // Active in settings
        activeIn: {
            global: opts["tac_active"],
            txt2img: opts["tac_activeIn.txt2img"],
            img2img: opts["tac_activeIn.img2img"],
            negativePrompts: opts["tac_activeIn.negativePrompts"],
            thirdParty: opts["tac_activeIn.thirdParty"],
            modelList: opts["tac_activeIn.modelList"],
            modelListMode: opts["tac_activeIn.modelListMode"]
        },
        // Results related settings
        slidingPopup: opts["tac_slidingPopup"],
        maxResults: opts["tac_maxResults"],
        showAllResults: opts["tac_showAllResults"],
        resultStepLength: opts["tac_resultStepLength"],
        delayTime: opts["tac_delayTime"],
        useWildcards: opts["tac_useWildcards"],
        sortWildcardResults: opts["tac_sortWildcardResults"],
        useEmbeddings: opts["tac_useEmbeddings"],
        includeEmbeddingsInNormalResults: opts["tac_includeEmbeddingsInNormalResults"],
        useHypernetworks: opts["tac_useHypernetworks"],
        useLoras: opts["tac_useLoras"],
        useLycos: opts["tac_useLycos"],
        useLoraPrefixForLycos: opts["tac_useLoraPrefixForLycos"],
        showWikiLinks: opts["tac_showWikiLinks"],
        showExtraNetworkPreviews: opts["tac_showExtraNetworkPreviews"],
        modelSortOrder: opts["tac_modelSortOrder"],
        frequencySort: opts["tac_frequencySort"],
        frequencyFunction: opts["tac_frequencyFunction"],
        frequencyMinCount: opts["tac_frequencyMinCount"],
        frequencyMaxAge: opts["tac_frequencyMaxAge"],
        frequencyRecommendCap: opts["tac_frequencyRecommendCap"],
        frequencyIncludeAlias: opts["tac_frequencyIncludeAlias"],
        useStyleVars: opts["tac_useStyleVars"],
        // Insertion related settings
        replaceUnderscores: opts["tac_replaceUnderscores"],
        escapeParentheses: opts["tac_escapeParentheses"],
        appendComma: opts["tac_appendComma"],
        appendSpace: opts["tac_appendSpace"],
        alwaysSpaceAtEnd: opts["tac_alwaysSpaceAtEnd"],
        wildcardCompletionMode: opts["tac_wildcardCompletionMode"],
        modelKeywordCompletion: opts["tac_modelKeywordCompletion"],
        modelKeywordLocation: opts["tac_modelKeywordLocation"],
        wcWrap: opts["dp_parser_wildcard_wrap"] || "__", // to support custom wrapper chars set by dp_parser
        // Alias settings
        alias: {
            searchByAlias: opts["tac_alias.searchByAlias"],
            onlyShowAlias: opts["tac_alias.onlyShowAlias"]
        },
        // Translation settings
        translation: {
            translationFile: opts["tac_translation.translationFile"],
            oldFormat: opts["tac_translation.oldFormat"],
            searchByTranslation: opts["tac_translation.searchByTranslation"],
            liveTranslation: opts["tac_translation.liveTranslation"],
        },
        // Extra file settings
        extra: {
            extraFile: opts["tac_extra.extraFile"],
            addMode: opts["tac_extra.addMode"]
        },
        // Chant file settings
        chantFile: opts["tac_chantFile"],
        // Settings not from tac but still used by the script
        extraNetworksDefaultMultiplier: opts["extra_networks_default_multiplier"],
        extraNetworksSeparator: opts["extra_networks_add_text_separator"],
        // Custom mapping settings
        keymap: opts["tac_keymap"],
        colorMap: opts["tac_colormap"]
    }


    if (newCFG.alias.onlyShowAlias) {
        newCFG.alias.searchByAlias = true; // if only show translation, enable search by translation is necessary
    }

    // Reload translations if the translation file changed
    if (!TAC_CFG || newCFG.translation.translationFile !== TAC_CFG.translation.translationFile) {
        translations.clear();
        await loadTranslations(newCFG);
        await loadExtraTags(newCFG);
    }
    // Reload tags if the tag file changed (after translations so extra tag translations get re-added)
    if (!TAC_CFG || newCFG.tagFile !== TAC_CFG.tagFile || newCFG.extra.extraFile !== TAC_CFG.extra.extraFile) {
        allTags = [];
        await loadTags(newCFG);
    }

    // Refresh temp files if model sort order changed
    // Contrary to the other loads, this one shouldn't happen on a first time load
    if (TAC_CFG && newCFG.modelSortOrder !== TAC_CFG.modelSortOrder) {
        const dropdown = document.querySelector("#setting_tac_modelSortOrder");
        dropdown.style.opacity = 0.5;
        dropdown.style.pointerEvents = "none";
        await refreshTacTempFiles(true);
        dropdown.style.opacity = null;
        dropdown.style.pointerEvents = null;
    }

    // Update CSS if maxResults changed
    if (TAC_CFG && newCFG.maxResults !== TAC_CFG.maxResults) {
        document.querySelectorAll(".autocompleteResults").forEach(r => {
            r.style.maxHeight = `${newCFG.maxResults * 50}px`;
        });
    }

    // Remove ruby div if live preview was disabled
    if (newCFG.translation.liveTranslation === false) {
        [...document.querySelectorAll('.acRuby')].forEach(r => {
            r.remove();
        });
    }

    // Apply changes
    TAC_CFG = newCFG;

    // Callback
    await processQueue(QUEUE_AFTER_CONFIG_CHANGE, null);
}

// Create the result list div and necessary styling
function createResultsDiv(textArea) {
    let parentDiv = document.createElement("div");
    let resultsDiv = document.createElement("div");
    let resultsList = document.createElement("ul");
    let sideDiv = document.createElement("div");
    let sideDivImg = document.createElement("img");

    let textAreaId = getTextAreaIdentifier(textArea);
    let typeClass = textAreaId.replaceAll(".", " ");

    parentDiv.setAttribute("class", `autocompleteParent${typeClass}`);
    
    //z-index: 999
    parentDiv.style.zIndex = 999;
    

    resultsDiv.style.maxHeight = `${TAC_CFG.maxResults * 50}px`;
    resultsDiv.setAttribute("class", `autocompleteResults${typeClass} notranslate`);
    resultsDiv.setAttribute("translate", "no");
    resultsList.setAttribute("class", "autocompleteResultsList");
    resultsDiv.appendChild(resultsList);

    sideDiv.setAttribute("class", `autocompleteResults${typeClass} sideInfo`);
    sideDiv.appendChild(sideDivImg);

    parentDiv.appendChild(resultsDiv);
    parentDiv.appendChild(sideDiv);

    return parentDiv;
}

// Show or hide the results div
function isVisible(textArea) {
    let textAreaId = getTextAreaIdentifier(textArea);
    let parentDiv = document.querySelector('.autocompleteParent' + textAreaId);
    return parentDiv.style.display === "flex";
}
function showResults(textArea) {
    let textAreaId = getTextAreaIdentifier(textArea);
    let parentDiv = document.querySelector('.autocompleteParent' + textAreaId);
    parentDiv.style.display = "flex";

    if (TAC_CFG.slidingPopup) {
        let caretPosition = getCaretCoordinates(textArea, textArea.selectionEnd).left;
        let offset = Math.min(textArea.offsetLeft - textArea.scrollLeft + caretPosition, textArea.offsetWidth - parentDiv.offsetWidth);

        parentDiv.style.left = `${offset}px`;
    } else {
        if (parentDiv.style.left)
            parentDiv.style.removeProperty("left");
    }
    // Reset here too to make absolutely sure the browser registers it
    parentDiv.scrollTop = 0;

    // Ensure preview is hidden
    let previewDiv = document.querySelector(`.autocompleteParent${textAreaId} .sideInfo`);
    previewDiv.style.display = "none";
}
function hideResults(textArea) {
    let textAreaId = getTextAreaIdentifier(textArea);
    let resultsDiv = document.querySelector('.autocompleteParent' + textAreaId);

    if (!resultsDiv) return;

    resultsDiv.style.display = "none";
    selectedTag = null;
}

// Function to check activation criteria
function isEnabled() {
    if (TAC_CFG.activeIn.global) {
        // Skip check if the current model was not correctly detected, since it could wrongly disable the script otherwise
        if (!currentModelName || !currentModelHash) return true;

        let modelList = TAC_CFG.activeIn.modelList
            .split(",")
            .map(x => x.trim())
            .filter(x => x.length > 0);

        let shortHash = currentModelHash.substring(0, 10);
        let modelNameWithoutHash = currentModelName.replace(/\[.*\]$/g, "").trim();
        if (TAC_CFG.activeIn.modelListMode.toLowerCase() === "blacklist") {
            // If the current model is in the blacklist, disable
            return modelList.filter(x => x === currentModelName || x === modelNameWithoutHash || x === currentModelHash || x === shortHash).length === 0;
        } else {
            // If the current model is in the whitelist, enable.
            // An empty whitelist is ignored.
            return modelList.length === 0 || modelList.filter(x => x === currentModelName || x === modelNameWithoutHash || x === currentModelHash || x === shortHash).length > 0;
        }
    } else {
        return false;
    }
}

const WEIGHT_REGEX = /[([]([^()[\]:|]+)(?::(?:\d+(?:\.\d+)?|\.\d+))?[)\]]/g;
const POINTY_REGEX = /<[^\s,<](?:[^\t\n\r,<>]*>|[^\t\n\r,> ]*)/g;
const COMPLETED_WILDCARD_REGEX = /__[^\s,_][^\t\n\r,_]*[^\s,_]__[^\s,_]*/g;
const STYLE_VAR_REGEX = /\$\(?[^$|\[\],\s]*\)?/g;
const NORMAL_TAG_REGEX = /[^\s,|<>\[\]:]+_\([^\s,|<>\[\]:]*\)?|[^\s,|<>():\[\]]+|</g;
const RUBY_TAG_REGEX = /[\w\d<][\w\d' \-?!/$%]{2,}>?/g;
const TAG_REGEX = () => { return new RegExp(`${POINTY_REGEX.source}|${COMPLETED_WILDCARD_REGEX.source.replaceAll("__", escapeRegExp(TAC_CFG.wcWrap))}|${STYLE_VAR_REGEX.source}|${NORMAL_TAG_REGEX.source}`, "g"); }

let sanitizeResults;

function notifyValueChangedForFrameworks(textArea) {
    // Vue (v-model) listens to `input` events. When we set `value` manually,
    // the DOM updates but the reactive model won't unless we emit an event.
    try {
        textArea.dispatchEvent(new Event("input", { bubbles: true }));
        textArea.dispatchEvent(new Event("change", { bubbles: true }));
    } catch (e) {
        // Older browsers / odd environments: fall back to simple event init.
        try {
            const inputEvent = document.createEvent("Event");
            inputEvent.initEvent("input", true, true);
            textArea.dispatchEvent(inputEvent);
        } catch (_ignored) { }
    }
}

// On click, insert the tag into the prompt textbox with respect to the cursor position
async function insertTextAtCursor(textArea, result, tagword, tabCompletedWithoutChoice = false) {
    let text = result.text;
    let tagType = result.type;

    let cursorPos = textArea.selectionStart;
    var sanitizedText = text

    // Run sanitize queue and use first result as sanitized text
    sanitizeResults = await processQueueReturn(QUEUE_SANITIZE, null, tagType, text);

    if (sanitizeResults && sanitizeResults.length > 0) {
        sanitizedText = sanitizeResults[0];
    } else {
        sanitizedText = TAC_CFG.replaceUnderscores ? text.replaceAll("_", " ") : text;

        if (TAC_CFG.escapeParentheses && tagType === ResultType.tag) {
            sanitizedText = sanitizedText
                .replaceAll("(", "\\(")
                .replaceAll(")", "\\)")
                .replaceAll("[", "\\[")
                .replaceAll("]", "\\]");
        }
    }

    if ((tagType === ResultType.wildcardFile || tagType === ResultType.yamlWildcard)
        && tabCompletedWithoutChoice
        && TAC_CFG.wildcardCompletionMode !== "Always fully"
        && sanitizedText.includes("/")) {
        if (TAC_CFG.wildcardCompletionMode === "To next folder level") {
            let regexMatch = sanitizedText.match(new RegExp(`${escapeRegExp(tagword)}([^/]*\\/?)`, "i"));
            if (regexMatch) {
                let pathPart = regexMatch[0];
                // In case the completion would have just added a slash, try again one level deeper
                if (pathPart === `${tagword}/`) {
                    pathPart = sanitizedText.match(new RegExp(`${escapeRegExp(tagword)}\\/([^/]*\\/?)`, "i"))[0];
                }
                sanitizedText = pathPart;
            }
        } else if (TAC_CFG.wildcardCompletionMode === "To first difference") {
            let firstDifference = 0;
            let longestResult = results.map(x => x.text.length).reduce((a, b) => Math.max(a, b));
            // Compare the results to each other to find the first point where they differ
            for (let i = 0; i < longestResult; i++) {
                let char = results[0].text[i];
                if (results.every(x => x.text[i] === char)) {
                    firstDifference++;
                } else {
                    break;
                }
            }
            // Don't cut off the __ at the end if it is already the full path
            if (firstDifference > 0 && firstDifference < longestResult) {
                // +2 because the sanitized text already has the __ at the start but the matched text doesn't
                sanitizedText = sanitizedText.substring(0, firstDifference + TAC_CFG.wcWrap.length);
            } else if (firstDifference === 0) {
                sanitizedText = tagword;
            }
        }
    }

    // Frequency db update
    if (TAC_CFG.frequencySort) {
        let name = null;

        switch (tagType) {
            case ResultType.wildcardFile:
            case ResultType.yamlWildcard:
                // We only want to update the frequency for a full wildcard, not partial paths
                if (sanitizedText.endsWith(TAC_CFG.wcWrap))
                    name = text
                break;
            case ResultType.chant:
                // Chants use a slightly different format
                name = result.aliases;
                break;
            default:
                name = text;
                break;
        }

        if (name && name.length > 0) {
            // Check if it's a negative prompt
            let textAreaId = getTextAreaIdentifier(textArea);
            let isNegative = textAreaId.includes("n");
            // Sanitize name for API call
            name = encodeURIComponent(name)
            // Call API & update db
            increaseUseCount(name, tagType, isNegative)
        }
    }

    var prompt = textArea.value;

    // Edit prompt text
    let editStart = Math.max(cursorPos - tagword.length, 0);
    let editEnd = Math.min(cursorPos + tagword.length, prompt.length);
    let surrounding = prompt.substring(editStart, editEnd);
    let match = surrounding.match(new RegExp(escapeRegExp(`${tagword}`), "i"));
    let afterInsertCursorPos = editStart + match.index + sanitizedText.length;

    var optionalSeparator = "";
    let extraNetworkTypes = [ResultType.hypernetwork, ResultType.lora];
    let noCommaTypes = [ResultType.wildcardFile, ResultType.yamlWildcard, ResultType.umiWildcard].concat(extraNetworkTypes);
    if (!noCommaTypes.includes(tagType)) {
        // Append comma if enabled and not already present
        let beforeComma = surrounding.match(new RegExp(`${escapeRegExp(tagword)}[,:]`, "i")) !== null;
        if (TAC_CFG.appendComma)
            optionalSeparator = beforeComma ? "" : ",";
        // Add space if enabled
        if (TAC_CFG.appendSpace && !beforeComma)
            optionalSeparator += " ";
        // If at end of prompt and enabled, override the normal setting if not already added
        if (!TAC_CFG.appendSpace && TAC_CFG.alwaysSpaceAtEnd)
            optionalSeparator += surrounding.match(new RegExp(`${escapeRegExp(tagword)}$`, "im")) !== null ? " " : "";
    } else if (extraNetworkTypes.includes(tagType)) {
        // Use the dedicated separator for extra networks if it's defined, otherwise fall back to space
        optionalSeparator = TAC_CFG.extraNetworksSeparator || " ";
    }

    // Escape $ signs since they are special chars for the replace function
    // We need four since we're also escaping them in replaceAll in the first place
    sanitizedText = sanitizedText.replaceAll("$", "$$$$");

    // Replace partial tag word with new text, add comma if needed
    let insert = surrounding.replace(match, sanitizedText + optionalSeparator);

    // Add back start
    var newPrompt = prompt.substring(0, editStart) + insert + prompt.substring(editEnd);

    // Add lora/lyco keywords if enabled and found
    let keywordsLength = 0;

    if (TAC_CFG.modelKeywordCompletion !== "Never" && (tagType === ResultType.lora || tagType === ResultType.lyco)) {
        let keywords = null;
        // Check built-in activation words first
        if (tagType === ResultType.lora || tagType === ResultType.lyco) {
            let info = await fetchTacAPI(`tacapi/v1/lora-info/${result.text}`)
            if (info && info["activation text"]) {
                keywords = info["activation text"];
            }
        }

        if (!keywords && modelKeywordPath.length > 0 && result.hash && result.hash !== "NOFILE" && result.hash.length > 0) {
            let nameDict = modelKeywordDict.get(result.hash);
            let names = [result.text + ".safetensors", result.text + ".pt", result.text + ".ckpt"];

            // No match, try to find a sha256 match from the cache file
            if (!nameDict) {
                const sha256 = await fetchTacAPI(`/tacapi/v1/lora-cached-hash/${result.text}`)
                if (sha256) {
                    nameDict = modelKeywordDict.get(sha256);
                }
            }

            if (nameDict) {
                let found = false;
                names.forEach(name => {
                    if (!found && nameDict.has(name)) {
                        found = true;
                        keywords = nameDict.get(name);
                    }
                });

                if (!found)
                    keywords = nameDict.get("none");
            }
        }

        if (keywords && keywords.length > 0) {
            textBeforeKeywordInsertion = newPrompt;

            if (TAC_CFG.modelKeywordLocation === "Start of prompt")
                newPrompt = `${keywords}, ${newPrompt}`; // Insert keywords
            else if (TAC_CFG.modelKeywordLocation === "End of prompt")
                newPrompt = `${newPrompt}, ${keywords}`; // Insert keywords
            else {
                let keywordStart = prompt[editStart - 1] === " " ? editStart - 1 : editStart;
                newPrompt = prompt.substring(0, keywordStart) + `, ${keywords} ${insert}` + prompt.substring(editEnd);
            }


            textAfterKeywordInsertion = newPrompt;
            keywordInsertionUndone = false;
            setTimeout(() => lastEditWasKeywordInsertion = true, 200)

            keywordsLength = keywords.length + 2; // +2 for the comma and space
        }
    }

    // Insert into prompt textbox and reposition cursor
    textArea.value = newPrompt;
    textArea.selectionStart = afterInsertCursorPos + optionalSeparator.length + keywordsLength;
    textArea.selectionEnd = textArea.selectionStart

    // Keep reactive frameworks (Vue v-model) in sync
    notifyValueChangedForFrameworks(textArea);

    // Set self trigger flag to show wildcard contents after the filename was inserted
    if ([ResultType.wildcardFile, ResultType.yamlWildcard, ResultType.umiWildcard].includes(result.type))
        tacSelfTrigger = true;
    if (tagType === ResultType.wildcardTag || tagType === ResultType.wildcardFile || tagType === ResultType.yamlWildcard)
        tacSelfTrigger = true;

    // Update previous tags with the edited prompt to prevent re-searching the same term
    let weightedTags = [...newPrompt.matchAll(WEIGHT_REGEX)]
        .map(match => match[1]);
    let tags = newPrompt.match(TAG_REGEX())
    if (weightedTags !== null) {
        tags = tags.filter(tag => !weightedTags.some(weighted => tag.includes(weighted)))
            .concat(weightedTags);
    }
    previousTags = tags;

    // Callback
    let returns = await processQueueReturn(QUEUE_AFTER_INSERT, null, tagType, sanitizedText, newPrompt, textArea);
    // Return if any queue function returned true (has handled hide/show already)
    if (returns.some(x => x === true))
        return;

    // Hide results after inserting, if it hasn't been hidden already by a queue function
    if (!hideBlocked && isVisible(textArea)) {
        hideResults(textArea);
    }
}

function addResultsToList(textArea, results, tagword, resetList) {
    let textAreaId = getTextAreaIdentifier(textArea);
    let resultDiv = document.querySelector('.autocompleteResults' + textAreaId);
    let resultsList = resultDiv.querySelector('ul');

    // Reset list, selection and scrollTop since the list changed
    if (resetList) {
        resultsList.innerHTML = "";
        selectedTag = null;
        oldSelectedTag = null;
        resultDiv.scrollTop = 0;
        resultCount = 0;
    }

    // Find right colors from config
    let tagFileName = TAC_CFG.tagFile.split(".")[0];
    let tagColors = TAC_CFG.colorMap;
    let mode = 0;
    let nextLength = Math.min(results.length, resultCount + TAC_CFG.resultStepLength);

    for (let i = resultCount; i < nextLength; i++) {
        let result = results[i];

        // Skip if the result is null or undefined
        if (!result)
            continue;

        let li = document.createElement("li");

        let flexDiv = document.createElement("div");
        flexDiv.classList.add("resultsFlexContainer");
        li.appendChild(flexDiv);

        let itemText = document.createElement("div");
        itemText.classList.add("acListItem");

        let displayText = "";
        // If the tag matches the tagword, we don't need to display the alias
        if (result.type === ResultType.chant) {
            displayText = escapeHTML(result.aliases);
        } else if (result.aliases && !result.text.includes(tagword)) { // Alias
            let splitAliases = result.aliases.split(",");
            let bestAlias = splitAliases.find(a => a.toLowerCase().includes(tagword));

            // search in translations if no alias matches
            if (!bestAlias) {
                let tagOrAlias = pair => pair[0] === result.text || splitAliases.includes(pair[0]);
                var tArray = [...translations];
                if (tArray) {
                    var translationKey = [...translations].find(pair => tagOrAlias(pair) && pair[1].includes(tagword));
                    if (translationKey)
                        bestAlias = translationKey[0];
                }
            }

            displayText = escapeHTML(bestAlias);

            // Append translation for alias if it exists and is not what the user typed
            if (translations.has(bestAlias) && translations.get(bestAlias) !== bestAlias && bestAlias !== result.text)
                displayText += `[${translations.get(bestAlias)}]`;

            if (!TAC_CFG.alias.onlyShowAlias && result.text !== bestAlias)
                displayText += " ➝ " + result.text;
        } else { // No alias
            displayText = escapeHTML(result.text);
        }

        // Append translation for result if it exists
        if (translations.has(result.text))
            displayText += `[${translations.get(result.text)}]`;

        // Print search term bolded in result
        itemText.innerHTML = displayText.replace(tagword, `<b>${tagword}</b>`);

        const splitTypes = [ResultType.wildcardFile, ResultType.yamlWildcard]
        if (splitTypes.includes(result.type) && itemText.innerHTML.includes("/")) {
            let parts = itemText.innerHTML.split("/");
            let lastPart = parts[parts.length - 1];
            parts = parts.slice(0, parts.length - 1);

            itemText.innerHTML = "<span class='acPathPart'>" + parts.join("</span><span class='acPathPart'>/") + "</span>" + "/" + lastPart;
        }

        // Add wiki link if the setting is enabled and a supported tag set loaded
        if (TAC_CFG.showWikiLinks
            && (result.type === ResultType.tag)
            && (tagFileName.toLowerCase().startsWith("danbooru") || tagFileName.toLowerCase().startsWith("e621"))) {
            let wikiLink = document.createElement("a");
            wikiLink.classList.add("acWikiLink");
            wikiLink.innerText = "?";
            wikiLink.title = "Open external wiki page for this tag"

            let linkPart = displayText;
            // Only use alias result if it is one
            if (displayText.includes("➝"))
                linkPart = displayText.split(" ➝ ")[1];

            // Remove any trailing translations
            if (linkPart.includes("[")) {
                linkPart = linkPart.split("[")[0]
            }

            linkPart = encodeURIComponent(linkPart);

            // Set link based on selected file
            let tagFileNameLower = tagFileName.toLowerCase();
            if (tagFileNameLower.startsWith("danbooru")) {
                wikiLink.href = `https://danbooru.donmai.us/wiki_pages/${linkPart}`;
            } else if (tagFileNameLower.startsWith("e621")) {
                wikiLink.href = `https://e621.net/wiki_pages/${linkPart}`;
            }

            wikiLink.target = "_blank";
            flexDiv.appendChild(wikiLink);
        }

        flexDiv.appendChild(itemText);

        // Add post count & color if it's a tag
        // Wildcards & Embeds have no tag category
        if (result.category) {
            // Set the color of the tag
            let cat = result.category;
            let colorGroup = tagColors[tagFileName];
            // Default to danbooru scheme if no matching one is found
            if (!colorGroup)
                colorGroup = tagColors["danbooru"];

            // Set tag type to invalid if not found
            if (!colorGroup[cat])
                cat = "-1";

            flexDiv.style = `color: ${colorGroup[cat][mode]};`;
        }

        // Post count
        if (result.count && !isNaN(result.count) && result.count !== Number.MAX_SAFE_INTEGER) {
            let postCount = result.count;
            let formatter;

            // Danbooru formats numbers with a padded fraction for 1M or 1k, but not for 10/100k
            if (postCount >= 1000000 || (postCount >= 1000 && postCount < 10000))
                formatter = Intl.NumberFormat("en", { notation: "compact", minimumFractionDigits: 1, maximumFractionDigits: 1 });
            else
                formatter = Intl.NumberFormat("en", { notation: "compact" });

            let formattedCount = formatter.format(postCount);

            let countDiv = document.createElement("div");
            countDiv.textContent = formattedCount;
            countDiv.classList.add("acMetaText");
            flexDiv.appendChild(countDiv);
        } else if (result.meta) { // Check if there is meta info to display
            let metaDiv = document.createElement("div");
            metaDiv.textContent = result.meta;
            metaDiv.classList.add("acMetaText");

            // Add version info classes if it is an embedding
            if (result.type === ResultType.embedding) {
                if (result.meta.startsWith("v1"))
                    itemText.classList.add("acEmbeddingV1");
                else if (result.meta.startsWith("v2"))
                    itemText.classList.add("acEmbeddingV2");
            }

            flexDiv.appendChild(metaDiv);
        }

        // Add small ✨ marker to indicate usage sorting
        if (result.usageBias) {
            flexDiv.querySelector(".acMetaText").classList.add("biased");
            flexDiv.title = "✨ Frequent tag. Ctrl/Cmd + click to reset usage count."
        }

        // Check if it's a negative prompt
        let isNegative = textAreaId.includes("n");

        // Add listener
        li.addEventListener("click", (e) => {
            if (e.ctrlKey || e.metaKey) {
                resetUseCount(result.text, result.type, !isNegative, isNegative);
                flexDiv.querySelector(".acMetaText").classList.remove("biased");
            } else {
                insertTextAtCursor(textArea, result, tagword);
            }
        });
        // Add element to list
        resultsList.appendChild(li);
    }
    resultCount = nextLength;

    if (resetList) {
        selectedTag = null;
        oldSelectedTag = null;
        resultDiv.scrollTop = 0;
    }
}

async function updateSelectionStyle(textArea, newIndex, oldIndex) {
    let textAreaId = getTextAreaIdentifier(textArea);
    let resultDiv = document.querySelector('.autocompleteResults' + textAreaId);
    let resultsList = resultDiv.querySelector('ul');
    let items = resultsList.getElementsByTagName('li');

    if (oldIndex != null) {
        items[oldIndex].classList.remove('selected');
    }

    // make it safer
    if (newIndex !== null) {
        let selected = items[newIndex];
        selected.classList.add('selected');

        // Set scrolltop to selected item
        resultDiv.scrollTop = selected.offsetTop - resultDiv.offsetTop;
    }

    // Show preview if enabled and the selected type supports it
    if (newIndex !== null) {
        let selectedResult = results[newIndex];
        let selectedType = selectedResult.type;
        // These types support previews (others could technically too, but are not native to the webui gallery)
        let previewTypes = [ResultType.embedding, ResultType.hypernetwork, ResultType.lora, ResultType.lyco];

        let previewDiv = document.querySelector(`.autocompleteParent${textAreaId} .sideInfo`);

        if (TAC_CFG.showExtraNetworkPreviews && previewTypes.includes(selectedType)) {
            let img = previewDiv.querySelector("img");
            // String representation of our type enum
            const typeString = Object.keys(ResultType)[selectedType - 1].toLowerCase();
            // Get image from API
            let url = await getTacExtraNetworkPreviewURL(selectedResult.text, typeString);
            if (url) {
                img.src = url;
                previewDiv.style.display = "block";
            } else {
                previewDiv.style.display = "none";
            }
        } else {
            previewDiv.style.display = "none";
        }
    }
}

function updateRuby(textArea, prompt) {
    if (!TAC_CFG.translation.liveTranslation) return;
    if (!TAC_CFG.translation.translationFile || TAC_CFG.translation.translationFile === "None") return;

    let ruby = document.querySelector('.acRuby' + getTextAreaIdentifier(textArea));
    if (!ruby) {
        let textAreaId = getTextAreaIdentifier(textArea);
        let typeClass = textAreaId.replaceAll(".", " ");
        ruby = document.createElement("div");
        ruby.setAttribute("class", `acRuby${typeClass} notranslate`);
        textArea.parentNode.appendChild(ruby);
    }

    ruby.innerText = prompt;

    let bracketEscapedPrompt = prompt.replaceAll("\\(", "$").replaceAll("\\)", "%");

    let rubyTags = bracketEscapedPrompt.match(RUBY_TAG_REGEX);
    if (!rubyTags) return;

    rubyTags.sort((a, b) => b.length - a.length);
    rubyTags = new Set(rubyTags);

    const prepareTag = (tag) => {
        tag = tag.replaceAll("$", "\\(").replaceAll("%", "\\)");

        let unsanitizedTag = tag
            .replaceAll(" ", "_")
            .replaceAll("\\(", "(")
            .replaceAll("\\)", ")");

        const translation = translations?.get(tag) || translations?.get(unsanitizedTag);

        let escapedTag = escapeRegExp(tag);
        return { tag, escapedTag, translation };
    }

    const replaceOccurences = (text, tuple) => {
        let { tag, escapedTag, translation } = tuple;
        let searchRegex = new RegExp(`(?<!<ruby>)(?:\\b)${escapedTag}(?:\\b|$|(?=[,|: \\t\\n\\r]))(?!<rt>)`, "g");
        return text.replaceAll(searchRegex, `<ruby>${escapeHTML(tag)}<rt>${translation}</rt></ruby>`);
    }

    let html = escapeHTML(prompt);

    // First try to find direct matches
    [...rubyTags].forEach(tag => {
        let tuple = prepareTag(tag);

        if (tuple.translation) {
            html = replaceOccurences(html, tuple);
        } else {
            let subTags = tuple.tag.split(" ").filter(x => x.trim().length > 0);
            // Return if there is only one word
            if (subTags.length === 1) return;

            let subHtml = tag.replaceAll("$", "\\(").replaceAll("%", "\\)");

            let translateNgram = (windows) => {
                windows.forEach(window => {
                    let combinedTag = window.join(" ");
                    let subTuple = prepareTag(combinedTag);

                    if (subTuple.tag.length <= 2) return;

                    if (subTuple.translation) {
                        subHtml = replaceOccurences(subHtml, subTuple);
                    }
                });
            }

            // Perform n-gram sliding window search
            translateNgram(toNgrams(subTags, 3));
            translateNgram(toNgrams(subTags, 2));
            translateNgram(toNgrams(subTags, 1));

            let escapedTag = escapeRegExp(tuple.tag);

            let searchRegex = new RegExp(`(?<!<ruby>)(?:\\b)${escapedTag}(?:\\b|$|(?=[,|: \\t\\n\\r]))(?!<rt>)`, "g");
            html = html.replaceAll(searchRegex, subHtml);
        }
    });

    ruby.innerHTML = html;

    // Add listeners for auto selection
    const childNodes = [...ruby.childNodes];
    [...ruby.children].forEach(child => {
        const textBefore = childNodes.slice(0, childNodes.indexOf(child)).map(x => x.childNodes[0]?.textContent || x.textContent).join("")
        child.onclick = () => rubyTagClicked(child, textBefore, prompt, textArea);
    });
}

function rubyTagClicked(node, textBefore, prompt, textArea) {
    let selectionText = node.childNodes[0].textContent;

    // Find start and end position of the tag in the prompt
    let startPos = prompt.indexOf(textBefore) + textBefore.length;
    let endPos = startPos + selectionText.length;

    // Select in text area
    textArea.focus();
    textArea.setSelectionRange(startPos, endPos);
}

// Check if the last edit was the keyword insertion, and catch undo/redo in that case
function checkKeywordInsertionUndo(textArea, event) {
    if (TAC_CFG.modelKeywordCompletion === "Never") return;

    switch (event.inputType) {
        case "historyUndo":
            if (lastEditWasKeywordInsertion && !keywordInsertionUndone) {
                keywordInsertionUndone = true;
                textArea.value = textBeforeKeywordInsertion;
                tacSelfTrigger = true;
            }
            break;
        case "historyRedo":
            if (lastEditWasKeywordInsertion && keywordInsertionUndone) {
                keywordInsertionUndone = false;
                textArea.value = textAfterKeywordInsertion;
                tacSelfTrigger = true;
            }
        case undefined:
            // no-op
            break;
        default:
            // Everything else deactivates the keyword undo and returns to normal undo behavior
            lastEditWasKeywordInsertion = false;
            keywordInsertionUndone = false;
            textBeforeKeywordInsertion = "";
            textAfterKeywordInsertion = "";
            break;
    }
}

async function autocomplete(textArea, prompt, fixedTag = null) {
    // Return if the function is deactivated in the UI
    if (!isEnabled()) return;

    // Guard for empty prompt
    if (prompt.length === 0) {
        hideResults(textArea);
        previousTags = [];
        tagword = "";
        return;
    }

    if (fixedTag === null) {
        // Match tags with RegEx to get the last edited one
        // We also match for the weighting format (e.g. "tag:1.0") here, and combine the two to get the full tag word set
        let weightedTags = [...prompt.matchAll(WEIGHT_REGEX)]
            .map(match => match[1]);
        let tags = prompt.match(TAG_REGEX())
        if (weightedTags !== null && tags !== null) {
            tags = tags.filter(tag => !weightedTags.some(weighted => tag.includes(weighted) && !tag.startsWith("<[") && !tag.startsWith("$(")))
                .concat(weightedTags);
        }

        // Guard for no tags
        if (!tags || tags.length === 0) {
            previousTags = [];
            tagword = "";
            hideResults(textArea);
            return;
        }

        let tagCountChange = tags.length - previousTags.length;
        let diff = difference(tags, previousTags);
        previousTags = tags;

        // Guard for no difference / only whitespace remaining / last edited tag was fully removed
        if (diff === null || diff.length === 0 || (diff.length === 1 && tagCountChange < 0)) {
            if (!hideBlocked) hideResults(textArea);
            return;
        }

        tagword = diff[0]

        // Guard for empty tagword
        if (tagword === null || tagword.length === 0) {
            hideResults(textArea);
            return;
        }
    } else {
        tagword = fixedTag;
    }

    results = [];
    resultCountBeforeNormalTags = 0;
    tagword = tagword.toLowerCase().replace(/[\n\r]/g, "");

    // Needed for slicing check later
    let normalTags = false;

    // Process all parsers
    let resultCandidates = (await processParsers(textArea, prompt))?.filter(x => x.length > 0);
    // If one ore more result candidates match, use their results
    if (resultCandidates && resultCandidates.length > 0) {
        // Flatten our candidate(s)
        results = resultCandidates.flat();
        // Sort results, but not if it's umi tags since they are sorted by count
        if (!(resultCandidates.length === 1 && results[0].type === ResultType.umiWildcard))
            results = results.sort(getSortFunction());
    }
    // Else search the normal tag list
    if (!resultCandidates || resultCandidates.length === 0
        || (TAC_CFG.includeEmbeddingsInNormalResults && !(tagword.startsWith("<") || tagword.startsWith("*<")))
    ) {
        normalTags = true;
        resultCountBeforeNormalTags = results.length;

        // Create escaped search regex with support for * as a start placeholder
        let searchRegex;
        if (tagword.startsWith("*")) {
            tagword = tagword.slice(1);
            searchRegex = new RegExp(`${escapeRegExp(tagword)}`, 'i');
        } else {
            searchRegex = new RegExp(`(^|[^a-zA-Z])${escapeRegExp(tagword)}`, 'i');
        }

        // Both normal tags and aliases/translations are included depending on the config
        let baseFilter = (x) => x[0].toLowerCase().search(searchRegex) > -1;
        let aliasFilter = (x) => x[3] && x[3].toLowerCase().search(searchRegex) > -1;
        let translationFilter = (x) => (translations.has(x[0]) && translations.get(x[0]).toLowerCase().search(searchRegex) > -1)
            || x[3] && x[3].split(",").some(y => translations.has(y) && translations.get(y).toLowerCase().search(searchRegex) > -1);

        let fil;
        if (TAC_CFG.alias.searchByAlias && TAC_CFG.translation.searchByTranslation)
            fil = (x) => baseFilter(x) || aliasFilter(x) || translationFilter(x);
        else if (TAC_CFG.alias.searchByAlias && !TAC_CFG.translation.searchByTranslation)
            fil = (x) => baseFilter(x) || aliasFilter(x);
        else if (TAC_CFG.translation.searchByTranslation && !TAC_CFG.alias.searchByAlias)
            fil = (x) => baseFilter(x) || translationFilter(x);
        else
            fil = (x) => baseFilter(x);

        // Add final results
        allTags.filter(fil).forEach(t => {
            let result = new AutocompleteResult(t[0].trim(), ResultType.tag)
            result.category = t[1];
            result.count = t[2];
            result.aliases = t[3];
            results.push(result);
        });

        // Add extras
        if (TAC_CFG.extra.extraFile) {
            let extraResults = [];

            extras.filter(fil).forEach(e => {
                let result = new AutocompleteResult(e[0].trim(), ResultType.extra)
                result.category = e[1] || 0; // If no category is given, use 0 as the default
                result.meta = e[2] || "Custom tag";
                result.aliases = e[3] || "";
                extraResults.push(result);
            });

            if (TAC_CFG.extra.addMode === "Insert before") {
                results = extraResults.concat(results);
            } else {
                results = results.concat(extraResults);
            }
        }
    }

    // Guard for empty results
    if (!results || results.length === 0) {
        //console.log('No results found for "' + tagword + '"');
        hideResults(textArea);
        return;
    }

    // Sort again with frequency / usage count if enabled
    if (TAC_CFG.frequencySort) {
        // Split our results into a list of names and types
        let tagNames = [];
        let aliasNames = [];
        let types = [];
        // Limit to 2k for performance reasons
        const aliasTypes = [ResultType.tag, ResultType.extra];
        results.slice(0, 2000).forEach(r => {
            const name = r.type === ResultType.chant ? r.aliases : r.text;
            // Add to alias list or tag list depending on if the name includes the tagword
            // (the same criteria is used in the filter in calculateUsageBias)
            if (aliasTypes.includes(r.type) && !name.includes(tagword)) {
                aliasNames.push(name);
            } else {
                tagNames.push(name);
            }
            types.push(r.type);
        });

        // Check if it's a negative prompt
        let textAreaId = getTextAreaIdentifier(textArea);
        let isNegative = textAreaId.includes("n");

        // Request use counts from the DB
        const names = TAC_CFG.frequencyIncludeAlias ? tagNames.concat(aliasNames) : tagNames;
        const counts = await getUseCounts(names, types, isNegative) || [];


        // Pre-calculate weights to prevent duplicate work
        const resultBiasMap = new Map();
        results.forEach(result => {
            const name = result.type === ResultType.chant ? result.aliases : result.text;
            const type = result.type;
            // Find matching pair from DB results
            const useStats = counts.find(c => c.name === name && c.type === type);
            const uses = useStats?.count || 0;
            // Calculate & set weight
            const weight = calculateUsageBias(result, result.count, uses)


            resultBiasMap.set(result, weight);
        });
        // Actual sorting with the pre-calculated weights
        results = results.sort((a, b) => {
            return resultBiasMap.get(b) - resultBiasMap.get(a);
        });
    }

    // Slice if the user has set a max result count and we are not in a extra networks / wildcard list
    if (!TAC_CFG.showAllResults && normalTags) {
        results = results.slice(0, TAC_CFG.maxResults + resultCountBeforeNormalTags);
    }

    addResultsToList(textArea, results, tagword, true);
    showResults(textArea);
}
let validKeys;
function navigateInList(textArea, event) {
    // Return if the function is deactivated in the UI or the current model is excluded due to white/blacklist settings
    if (!isEnabled()) return;


    let keys = TAC_CFG.keymap;


    // Close window if Home or End is pressed while not a keybinding, since it would break completion on leaving the original tag
    if ((event.key === "Home" || event.key === "End") && !Object.values(keys).includes(event.key)) {
        hideResults(textArea);
        return;
    }

    // All set keys that are not None or empty are valid
    // Default keys are: ArrowUp, ArrowDown, PageUp, PageDown, Home, End, Enter, Tab, Escape
    validKeys = Object.values(keys).filter(x => x !== "None" && x !== "");

    if (!validKeys.includes(event.key)) return;
    if (!isVisible(textArea)) return
    // Add modifier keys to base as text+.
    let modKey = "";
    if (event.ctrlKey) modKey += "Ctrl+";
    if (event.altKey) modKey += "Alt+";
    if (event.shiftKey) modKey += "Shift+";
    if (event.metaKey) modKey += "Meta+";
    modKey += event.key;

    oldSelectedTag = selectedTag;

    switch (modKey) {
        case keys["MoveUp"]:
            if (selectedTag === null) {
                selectedTag = resultCount - 1;
            } else {
                selectedTag = (selectedTag - 1 + resultCount) % resultCount;
            }
            break;
        case keys["MoveDown"]:
            if (selectedTag === null) {
                selectedTag = 0;
            } else {
                selectedTag = (selectedTag + 1) % resultCount;
            }
            break;
        case keys["JumpUp"]:
            if (selectedTag === null || selectedTag === 0) {
                selectedTag = resultCount - 1;
            } else {
                selectedTag = (Math.max(selectedTag - 5, 0) + resultCount) % resultCount;
            }
            break;
        case keys["JumpDown"]:
            if (selectedTag === null || selectedTag === resultCount - 1) {
                selectedTag = 0;
            } else {
                selectedTag = Math.min(selectedTag + 5, resultCount - 1) % resultCount;
            }
            break;
        case keys["JumpToStart"]:
            if (TAC_CFG.includeEmbeddingsInNormalResults &&
                selectedTag > resultCountBeforeNormalTags &&
                resultCountBeforeNormalTags > 0
            ) {
                selectedTag = resultCountBeforeNormalTags;
            } else {
                selectedTag = 0;
            }
            break;
        case keys["JumpToEnd"]:
            // Jump to the end of the list, or the end of embeddings if they are included in the normal results
            if (TAC_CFG.includeEmbeddingsInNormalResults &&
                selectedTag < resultCountBeforeNormalTags &&
                resultCountBeforeNormalTags > 0
            ) {
                selectedTag = Math.min(resultCountBeforeNormalTags, resultCount - 1);
            } else {
                selectedTag = resultCount - 1;
            }
            break;
        case keys["ChooseSelected"]:
            if (selectedTag !== null) {
                insertTextAtCursor(textArea, results[selectedTag], tagword);
            } else {
                hideResults(textArea);
                return;
            }
            break;
        case keys["ChooseFirstOrSelected"]:
            let withoutChoice = false;
            if (selectedTag === null) {
                selectedTag = 0;
                withoutChoice = true;
            } else if (TAC_CFG.wildcardCompletionMode === "To next folder level") {
                withoutChoice = true;
            }
            insertTextAtCursor(textArea, results[selectedTag], tagword, withoutChoice);
            break;
        case keys["Close"]:
            hideResults(textArea);
            break;
        default:
            if (event.ctrlKey || event.altKey || event.shiftKey || event.metaKey) return;
    }
    let moveKeys = [keys["MoveUp"], keys["MoveDown"], keys["JumpUp"], keys["JumpDown"], keys["JumpToStart"], keys["JumpToEnd"]];
    if (selectedTag === resultCount - 1 && moveKeys.includes(event.key)) {
        addResultsToList(textArea, results, tagword, false);
    }
    // Update highlighting
    if (selectedTag !== null)
        updateSelectionStyle(textArea, selectedTag, oldSelectedTag);

    // Prevent default behavior
    event.preventDefault();
    event.stopPropagation();
}

async function refreshTacTempFiles(api = false) {
    const reload = async () => {
        wildcardFiles = [];
        wildcardExtFiles = [];
        umiWildcards = [];
        embeddings = [];
        hypernetworks = [];
        loras = [];
        lycos = [];
        modelKeywordDict.clear();
        await processQueue(QUEUE_FILE_LOAD, null);

        console.log("TAC: Refreshed temp files");
    }

    if (api) {
        await postTacAPI("tacapi/v1/refresh-temp-files");
        await reload();
    } else {
        setTimeout(async () => {
            await reload();
        }, 2000);
    }
}

function addAutocompleteToArea(area) {
    let textAreaId = getTextAreaIdentifier(area);
    console.log("Adding autocomplete to area " + textAreaId);

    // Only add listeners once
    if (!area.classList.contains('autocomplete')) {
        // Add our new element
        var resultsDiv = createResultsDiv(area);
        area.parentNode.insertBefore(resultsDiv, area.nextSibling);
        // Hide by default so it doesn't show up on page load
        hideResults(area);

        // Add autocomplete event listener
        area.addEventListener('input', (e) => {
            updateRuby(area, area.value);

            // Cancel autocomplete itself if the event has no inputType
            if (!e.inputType && !tacSelfTrigger) return;
            tacSelfTrigger = false;

            debounce(autocomplete(area, area.value), TAC_CFG.delayTime);
            checkKeywordInsertionUndo(area, e);
        });
        // Add focusout event listener
        area.addEventListener('focusout', debounce(() => {
            if (!hideBlocked)
                hideResults(area);
        }, 400));
        // Add up and down arrow event listener
        area.addEventListener('keydown', (e) => navigateInList(area, e));
        // CompositionEnd fires after the user has finished IME composing
        // We need to block hide here to prevent the enter key from insta-closing the results
        area.addEventListener('compositionend', () => {
            hideBlocked = true;
            setTimeout(() => { hideBlocked = false; }, 100);
        });

        // Add class so we know we've already added the listeners
        area.classList.add('autocomplete');
    }
}

// One-time setup, triggered from onUiUpdate
async function setup() {

    console.log("Setting up")

    // Load external files needed by completion extensions
    await processQueue(QUEUE_FILE_LOAD, null);

    // Find all textareas
    let textAreas = getTextAreas();

    // Not found, we're on a page without prompt textareas
    if (textAreas.every(v => v === null || v === undefined)) return;

    // Already added or unnecessary to add
    if (document.querySelector('.autocompleteParent.p')) {
        if (document.querySelector('.autocompleteParent.n')) {
            return;
        }
    }


    textAreas.forEach(area => addAutocompleteToArea(area));

    // Add style to dom
    let acStyle = document.createElement('style');
    let mode = 0;
    // Check if we are on webkit
    let browser = navigator.userAgent.toLowerCase().indexOf('firefox') > -1 ? "firefox" : "other";

    let css = autocompleteCSS;
    // Replace vars with actual values (can't use actual css vars because of the way we inject the css)
    Object.keys(styleColors).forEach((key) => {
        css = css.replaceAll(`var(${key})`, styleColors[key][mode]);
    })
    Object.keys(browserVars).forEach((key) => {
        css = css.replaceAll(`var(${key})`, browserVars[key][browser]);
    })

    if (acStyle.styleSheet) {
        acStyle.styleSheet.cssText = css;
    } else {
        acStyle.appendChild(document.createTextNode(css));
    }
    document.head.appendChild(acStyle);


    // Callback
    await processQueue(QUEUE_AFTER_SETUP, null);

    console.log("Setup done")
}
var tacLoading = false;
export async function onUiUpdate() {

    
    if( getTextAreas().length === 0 ) {

        // No text areas found, so we can't do anything
        //try again in 1 second
        setTimeout(onUiUpdate, 100);

        return;
    }
    
    console.log("UI updated")

    if (tacLoading) return;
    if (TAC_CFG) return;

    console.log("TAC: Loading config and setting up");

    tacLoading = true;
    // Get our tag base path from the temp file
    tagBasePath = "/src/scripts/tags"
    // Load config from webui opts
    await syncOptions();
    // Rest of setup
    setup();
    tacLoading = false;
}
//#endregion




//#region result.js
// Result data type for cleaner use of optional completion result properties

// Type enum
const ResultType = Object.freeze({
    "tag": 1,
    "extra": 2,
    "embedding": 3,
    "wildcardTag": 4,
    "wildcardFile": 5,
    "yamlWildcard": 6,
    "umiWildcard": 7,
    "hypernetwork": 8,
    "lora": 9,
    "lyco": 10,
    "chant": 11,
    "styleName": 12
});

// Class to hold result data and annotations to make it clearer to use
class AutocompleteResult {
    // Main properties
    text = "";
    type = ResultType.tag;

    // Additional info, only used in some cases
    category = null;
    count = Number.MAX_SAFE_INTEGER;
    usageBias = null;
    aliases = null;
    meta = null;
    hash = null;
    sortKey = null;

    // Constructor
    constructor(text, type) {
        this.text = text;
        this.type = type;
    }
}
//#endregion



//#region textAreas.js
// Utility functions to select text areas the script should work on,
// including third party options.
// Supported third party options so far:
// - Dataset Tag Editor

// Core text area selectors
const core = [
    "#positive_prompt",
    "#negative_prompt",
    ".positive-prompt",
    ".negative-prompt",
    
];


function getTextAreas() {
    // First get all core text areas
    let textAreas = [...document.querySelectorAll(core.join(", "))];
    
    return textAreas;
}



const thirdPartyIdSet = new Set();
// Get the identifier for the text area to differentiate between positive and negative
function getTextAreaIdentifier(textArea) {
    let txt2img_p = document.querySelector('#positive_prompt');
    let txt2img_n = document.querySelector('#negative_prompt');
    let img2img_p = document.querySelector('#img2img_prompt > label > textarea');
    let img2img_n = document.querySelector('#img2img_neg_prompt > label > textarea');

    let modifier = "";
    switch (textArea) {
        case txt2img_p:
            modifier = ".txt2img.p";
            break;
        case txt2img_n:
            modifier = ".txt2img.n";
            break;
        case img2img_p:
            modifier = ".img2img.p";
            break;
        case img2img_n:
            modifier = ".img2img.n";
            break;
        default:
            // If the text area is not a core text area, it must be a third party text area
            // Add it to the set of third party text areas and get its index as a unique identifier
            if (!thirdPartyIdSet.has(textArea))
                thirdPartyIdSet.add(textArea);

            modifier = `.thirdParty.ta${[...thirdPartyIdSet].indexOf(textArea)}`;
            break;
    }
    return modifier;
}

//#endregion




//#region caretPosition
// From https://github.com/component/textarea-caret-position

// We'll copy the properties below into the mirror div.
// Note that some browsers, such as Firefox, do not concatenate properties
// into their shorthand (e.g. padding-top, padding-bottom etc. -> padding),
// so we have to list every single property explicitly.
var properties = [
    'direction',  // RTL support
    'boxSizing',
    'width',  // on Chrome and IE, exclude the scrollbar, so the mirror div wraps exactly as the textarea does
    'height',
    'overflowX',
    'overflowY',  // copy the scrollbar for IE

    'borderTopWidth',
    'borderRightWidth',
    'borderBottomWidth',
    'borderLeftWidth',
    'borderStyle',

    'paddingTop',
    'paddingRight',
    'paddingBottom',
    'paddingLeft',

    // https://developer.mozilla.org/en-US/docs/Web/CSS/font
    'fontStyle',
    'fontVariant',
    'fontWeight',
    'fontStretch',
    'fontSize',
    'fontSizeAdjust',
    'lineHeight',
    'fontFamily',

    'textAlign',
    'textTransform',
    'textIndent',
    'textDecoration',  // might not make a difference, but better be safe

    'letterSpacing',
    'wordSpacing',

    'tabSize',
    'MozTabSize'

];

var isBrowser = (typeof window !== 'undefined');
var isFirefox = (isBrowser && window.mozInnerScreenX != null);

function getCaretCoordinates(element, position, options) {
    if (!isBrowser) {
        throw new Error('textarea-caret-position#getCaretCoordinates should only be called in a browser');
    }

    var debug = options && options.debug || false;
    if (debug) {
        var el = document.querySelector('#input-textarea-caret-position-mirror-div');
        if (el) el.parentNode.removeChild(el);
    }

    // The mirror div will replicate the textarea's style
    var div = document.createElement('div');
    div.id = 'input-textarea-caret-position-mirror-div';
    document.body.appendChild(div);

    var style = div.style;
    var computed = window.getComputedStyle ? window.getComputedStyle(element) : element.currentStyle;  // currentStyle for IE < 9
    var isInput = element.nodeName === 'INPUT';

    // Default textarea styles
    style.whiteSpace = 'pre-wrap';
    if (!isInput)
        style.wordWrap = 'break-word';  // only for textarea-s

    // Position off-screen
    style.position = 'absolute';  // required to return coordinates properly
    if (!debug)
        style.visibility = 'hidden';  // not 'display: none' because we want rendering

    // Transfer the element's properties to the div
    properties.forEach(function (prop) {
        if (isInput && prop === 'lineHeight') {
            // Special case for <input>s because text is rendered centered and line height may be != height
            if (computed.boxSizing === "border-box") {
                var height = parseInt(computed.height);
                var outerHeight =
                    parseInt(computed.paddingTop) +
                    parseInt(computed.paddingBottom) +
                    parseInt(computed.borderTopWidth) +
                    parseInt(computed.borderBottomWidth);
                var targetHeight = outerHeight + parseInt(computed.lineHeight);
                if (height > targetHeight) {
                    style.lineHeight = height - outerHeight + "px";
                } else if (height === targetHeight) {
                    style.lineHeight = computed.lineHeight;
                } else {
                    style.lineHeight = 0;
                }
            } else {
                style.lineHeight = computed.height;
            }
        } else {
            style[prop] = computed[prop];
        }
    });

    if (isFirefox) {
        // Firefox lies about the overflow property for textareas: https://bugzilla.mozilla.org/show_bug.cgi?id=984275
        if (element.scrollHeight > parseInt(computed.height))
            style.overflowY = 'scroll';
    } else {
        style.overflow = 'hidden';  // for Chrome to not render a scrollbar; IE keeps overflowY = 'scroll'
    }

    div.textContent = element.value.substring(0, position);
    // The second special handling for input type="text" vs textarea:
    // spaces need to be replaced with non-breaking spaces - http://stackoverflow.com/a/13402035/1269037
    if (isInput)
        div.textContent = div.textContent.replace(/\s/g, '\u00a0');

    var span = document.createElement('span');
    // Wrapping must be replicated *exactly*, including when a long word gets
    // onto the next line, with whitespace at the end of the line before (#7).
    // The  *only* reliable way to do that is to copy the *entire* rest of the
    // textarea's content into the <span> created at the caret position.
    // For inputs, just '.' would be enough, but no need to bother.
    span.textContent = element.value.substring(position) || '.';  // || because a completely empty faux span doesn't render at all
    div.appendChild(span);

    var coordinates = {
        top: span.offsetTop + parseInt(computed['borderTopWidth']),
        left: span.offsetLeft + parseInt(computed['borderLeftWidth']),
        height: parseInt(computed['lineHeight'])
    };

    if (debug) {
        span.style.backgroundColor = '#aaa';
    } else {
        document.body.removeChild(div);
    }

    return coordinates;
}
//#region 


//#region UTILS
// Utility functions for tag autocomplete

// Parse the CSV file into a 2D array. Doesn't use regex, so it is very lightweight.
// We are ignoring newlines in quote fields since we expect one-line entries and parsing would break for unclosed quotes otherwise
function parseCSV(str) {
    const arr = [];
    let quote = false;  // 'true' means we're inside a quoted field

    // Iterate over each character, keep track of current row and column (of the returned array)
    for (let row = 0, col = 0, c = 0; c < str.length; c++) {
        let cc = str[c], nc = str[c + 1];        // Current character, next character
        arr[row] = arr[row] || [];             // Create a new row if necessary
        arr[row][col] = arr[row][col] || '';   // Create a new column (start with empty string) if necessary

        // If the current character is a quotation mark, and we're inside a
        // quoted field, and the next character is also a quotation mark,
        // add a quotation mark to the current column and skip the next character
        if (cc == '"' && quote && nc == '"') { arr[row][col] += cc; ++c; continue; }

        // If it's just one quotation mark, begin/end quoted field
        if (cc == '"') { quote = !quote; continue; }

        // If it's a comma and we're not in a quoted field, move on to the next column
        if (cc == ',' && !quote) { ++col; continue; }

        // If it's a newline (CRLF), skip the next character and move on to the next row and move to column 0 of that new row
        if (cc == '\r' && nc == '\n') { ++row; col = 0; ++c; quote = false; continue; }

        // If it's a newline (LF or CR) move on to the next row and move to column 0 of that new row
        if (cc == '\n') { ++row; col = 0; quote = false; continue; }
        if (cc == '\r') { ++row; col = 0; quote = false; continue; }

        // Otherwise, append the current character to the current column
        arr[row][col] += cc;
    }
    return arr;
}

// Load file
async function readFile(filePath, json = false, cache = false) {
    let response = await fetch(`${filePath}`);

    if (response.status != 200) {
        console.error(`Error loading file "${filePath}": ` + response.status, response.statusText);
        return null;
    }

    if (json)
        return await response.json();
    else
        return await response.text();
}

// Load CSV
async function loadCSV(path) {
    console.log("Loading CSV: " + path);
    let text = await readFile(path);
    return parseCSV(text);
}

// Fetch API
async function fetchTacAPI(url, json = true, cache = false) {
    if (!cache) {
        const appendChar = url.includes("?") ? "&" : "?";
        url += `${appendChar}${new Date().getTime()}`
    }

    let response = await fetch(url);

    if (response.status != 200) {
        console.error(`Error fetching API endpoint "${url}": ` + response.status, response.statusText);
        return null;
    }

    if (json)
        return await response.json();
    else
        return await response.text();
}

async function postTacAPI(url, body = null) {
    let response = await fetch(url, {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: body
    });

    if (response.status != 200) {
        console.error(`Error posting to API endpoint "${url}": ` + response.status, response.statusText);
        return null;
    }

    return await response.json();
}

// Extra network preview thumbnails
async function getTacExtraNetworkPreviewURL(filename, type) {
    const previewJSON = await fetchTacAPI(`tacapi/v1/thumb-preview/${filename}?type=${type}`, true, true);
    if (previewJSON?.url) {
        const properURL = `sd_extra_networks/thumb?filename=${previewJSON.url}`;
        if ((await fetch(properURL)).status == 200) {
            return properURL;
        } else {
            // create blob url
            const blob = await (await fetch(`tacapi/v1/thumb-preview-blob/${filename}?type=${type}`)).blob();
            return URL.createObjectURL(blob);
        }
    } else {
        return null;
    }
}

// Debounce function to prevent spamming the autocomplete function
var dbTimeOut;
const debounce = (func, wait = 300) => {
    return function (...args) {
        if (dbTimeOut) {
            clearTimeout(dbTimeOut);
        }

        dbTimeOut = setTimeout(() => {
            func.apply(this, args);
        }, wait);
    }
}

// Difference function to fix duplicates not being seen as changes in normal filter
function difference(a, b) {
    if (a.length == 0) {
        return b;
    }
    if (b.length == 0) {
        return a;
    }

    return [...b.reduce((acc, v) => acc.set(v, (acc.get(v) || 0) - 1),
        a.reduce((acc, v) => acc.set(v, (acc.get(v) || 0) + 1), new Map())
    )].reduce((acc, [v, count]) => acc.concat(Array(Math.abs(count)).fill(v)), []);
}

// Object flatten function adapted from https://stackoverflow.com/a/61602592
// $roots keeps previous parent properties as they will be added as a prefix for each prop.
// $sep is just a preference if you want to seperate nested paths other than dot.
function flatten(obj, roots = [], sep = ".") {
    return Object.keys(obj).reduce(
        (memo, prop) =>
            Object.assign(
                // create a new object
                {},
                // include previously returned object
                memo,
                Object.prototype.toString.call(obj[prop]) === "[object Object]"
                    ? // keep working if value is an object
                    flatten(obj[prop], roots.concat([prop]), sep)
                    : // include current prop and value and prefix prop with the roots
                    { [roots.concat([prop]).join(sep)]: obj[prop] }
            ),
        {}
    );
}

// Calculate biased tag score based on post count and frequent usage
function calculateUsageBias(result, count, uses) {
    // Check setting conditions
    if (uses < TAC_CFG.frequencyMinCount) {
        uses = 0;
    } else if (uses != 0) {
        result.usageBias = true;
    }

    switch (TAC_CFG.frequencyFunction) {
        case "Logarithmic (weak)":
            return Math.log(1 + count) + Math.log(1 + uses);
        case "Logarithmic (strong)":
            return Math.log(1 + count) + 2 * Math.log(1 + uses);
        case "Usage first":
            return uses;
        default:
            return count;
    }
}
// Beautify return type for easier parsing
function mapUseCountArray(useCounts, posAndNeg = false) {
    return useCounts.map(useCount => {
        if (posAndNeg) {
            return {
                "name": useCount[0],
                "type": useCount[1],
                "count": useCount[2],
                "negCount": useCount[3],
                "lastUseDate": useCount[4]
            }
        }
        return {
            "name": useCount[0],
            "type": useCount[1],
            "count": useCount[2],
            "lastUseDate": useCount[3]
        }
    });
}
// Call API endpoint to increase bias of tag in the database
function increaseUseCount(tagName, type, negative = false) {

    const tagUsage = settingState.tag_usage.find(t => t.name === tagName && t.type === type);
    if (tagUsage) {
        if (negative)
            tagUsage.negCount++;
        else
            tagUsage.count++;
    } else {
        settingState.tag_usage.push({
            "name": tagName,
            "type": type,
            "count": negative ? 0 : 1,
            "negCount": negative ? 1 : 0,
            "lastUseDate": new Date().toISOString().slice(0, 19).replace("T", " "),
            "usageBias":0,
        });
    }

}
async function getUseCounts(tagNames, types, negative = false) {

    let response = [];


    for (let i = 0; i < tagNames.length; i++) {
        for (let t of settingState.tag_usage) {
            if (t.name === tagNames[i] && t.type === types[i]) {
                response.push({
                    "name": t.name,
                    "type": t.type,
                    "count": negative ? t.negCount : t.count,
                    "lastUseDate": t.lastUseDate,
                    "usageBias":t.usageBias,
                })
            }

        }
    }

    return response;
}
async function resetUseCount(tagName, type, resetPosCount, resetNegCount) {
    
    const tagUsage = settingState.tag_usage.find(t => t.name === tagName && t.type === type);
    if (tagUsage) {
        if (resetPosCount)
            tagUsage.count = 0;
        if (resetNegCount)
            tagUsage.negCount = 0;
    }

}

// Sliding window function to get possible combination groups of an array
function toNgrams(inputArray, size) {
    return Array.from(
        { length: inputArray.length - (size - 1) }, //get the appropriate length
        (_, index) => inputArray.slice(index, index + size) //create the windows
    );
}

function escapeRegExp(string, wildcardMatching = false) {
    if (wildcardMatching) {
        // Escape all characters except asterisks and ?, which should be treated separately as placeholders.
        return string.replace(/[-[\]{}()+.,\\^$|#\s]/g, '\\$&').replace(/\*/g, '.*').replace(/\?/g, '.');
    }
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
}
function escapeHTML(unsafeText) {
    let div = document.createElement('div');
    div.textContent = unsafeText;
    return div.innerHTML;
}

// Sort functions
function getSortFunction() {
    let criterion = TAC_CFG.modelSortOrder || "Name";

    const textSort = (a, b, reverse = false) => {
        // Assign keys so next sort is faster
        if (!a.sortKey) {
            a.sortKey = a.type === ResultType.chant
                ? a.aliases
                : a.text;
        }
        if (!b.sortKey) {
            b.sortKey = b.type === ResultType.chant
                ? b.aliases
                : b.text;
        }

        return reverse ? b.sortKey.localeCompare(a.sortKey) : a.sortKey.localeCompare(b.sortKey);
    }
    const numericSort = (a, b, reverse = false) => {
        const noKey = reverse ? "-1" : Number.MAX_SAFE_INTEGER;
        let aParsed = parseFloat(a.sortKey || noKey);
        let bParsed = parseFloat(b.sortKey || noKey);

        if (aParsed === bParsed) {
            return textSort(a, b, false);
        }

        return reverse ? bParsed - aParsed : aParsed - bParsed;
    }

    return (a, b) => {
        switch (criterion) {
            case "Date Modified (newest first)":
                return numericSort(a, b, true);
            case "Date Modified (oldest first)":
                return numericSort(a, b, false);
            default:
                return textSort(a, b);
        }
    }
}

// Queue calling function to process global queues
async function processQueue(queue, context, ...args) {
    for (let i = 0; i < queue.length; i++) {
        await queue[i].call(context, ...args);
    }
}
// The same but with return values
async function processQueueReturn(queue, context, ...args) {
    let qeueueReturns = [];
    for (let i = 0; i < queue.length; i++) {
        let returnValue = await queue[i].call(context, ...args);
        if (returnValue)
            qeueueReturns.push(returnValue);
    }
    return qeueueReturns;
}
// Specific to tag completion parsers
async function processParsers(textArea, prompt) {
    // Get all parsers that have a successful trigger condition
    let matchingParsers = PARSERS.filter(parser => parser.triggerCondition());
    // Guard condition
    if (matchingParsers.length === 0) {
        return null;
    }

    let parseFunctions = matchingParsers.map(parser => parser.parse);
    // Process them and return the results
    return await processQueueReturn(parseFunctions, null, textArea, prompt);
}
//#endregion