<script setup>
import { computed, onMounted, ref } from "vue";
import { GetRandomCharacter } from "@/scripts/randomCharacter";
import { formatRequest, webState } from "@/api";

const webuiUrl = ref('http://127.0.0.1:8000/')

// --- Ingredients ---
const ingredients = ref([
  // Breast size +
  { id: "milk",     name: "Milk",         color: "bg-slate-200",   effects: { breasts: 0.5 } },
  { id: "cream",    name: "Cream",        color: "bg-amber-100",   effects: { breasts: 1.0 } },
  { id: "whip",     name: "Whip Cream",   color: "bg-white",       effects: { breasts: 2.0 } },
  // Breast size -
  { id: "skim",     name: "Skim Milk",    color: "bg-blue-100",    effects: { breasts: -0.5 } },
  { id: "soy",      name: "Soy Milk",     color: "bg-yellow-50",   effects: { breasts: -1.5 } },
  // Weight +
  { id: "butter",   name: "Butter",       color: "bg-yellow-200",  effects: { weight: 1.0 } },
  { id: "sugar",    name: "Sugar",        color: "bg-amber-50",    effects: { weight: 0.5 } },
  { id: "syrup",    name: "Caramel Syrup",color: "bg-amber-400",   effects: { weight: 2.0 } },
  // Weight -
  { id: "diet",     name: "Diet Shot",    color: "bg-green-200",   effects: { weight: -1.0 } },
  { id: "espresso", name: "Espresso",     color: "bg-stone-800",   effects: { weight: -2.0 } },

  // Ass size +
  { id: "peach",    name: "Peach Juice",  color: "bg-orange-200",  effects: { ass: 1.0 } },
  { id: "squat",    name: "Squat Shake",  color: "bg-rose-300",    effects: { ass: 2.0 } },
  // Ass size -
  { id: "cardio",   name: "Cardio Mix",   color: "bg-sky-200",     effects: { ass: -1.0 } },
  // Thighs +
  { id: "thickmilk",name: "Thick Milk",   color: "bg-yellow-100",  effects: { thighs: 1.5 } },
  { id: "oat",      name: "Oat Milk",     color: "bg-amber-200",   effects: { thighs: 1.0 } },
  // Thighs -
  { id: "green",    name: "Green Tea",    color: "bg-lime-200",    effects: { thighs: -1.0 } },
  // Pregnancy
  { id: "fertil",   name: "Fertility Tea",color: "bg-teal-200",    effects: { pregnancy: 1.0 } },
  { id: "bloom",    name: "Bloom Elixir", color: "bg-fuchsia-200", effects: { pregnancy: 2.0 } },
  // Muscle +
  { id: "creatine", name: "Creatine",     color: "bg-red-300",     effects: { muscle: 3.0 } },
  { id: "bcaa",     name: "BCAA",         color: "bg-violet-300",  effects: { muscle: 2.0 } },
  // Muscle -
  { id: "collagen", name: "Collagen",     color: "bg-pink-100",    effects: { muscle: -2.0 } },
]);

const character_count = ref(10);
const characters_per_day = ref(3);
const day = ref(1);

// --- Effect definitions ---
const Effects = {
  breasts: {
    min: -3,
    max: 8,
    lora: "Unfazed Breast Size Slider IL v1.0",
    label: "Breast Size",
    prompts: {
      "-3": "flat chest",
      "-2": "very small breasts",
      "-1": "small breasts",
      "0": "average breasts",
      "1": "medium breasts",
      "2": "large breasts",
      "3": "very large breasts",
      "4": "huge breasts",
      "5": "gigantic breasts",
      "6": "enormous breasts",
      "7": "massive breasts",
      "8": "colossal breasts"
    }
  },
  weight: {
    min: -3,
    max: 8,
    lora: "Body weight slider IXL 1.0_alpha16.0_rank32_full_last",
    label: "Weight",
    prompts: {
      "-3": "very thin, skinny, underweight",
      "-2": "thin, slender, lean",
      "-1": "slightly thin, fit",
      "0": "average weight",
      "1": "slightly overweight, chubby",
      "2": "overweight, plump",
      "3": "very overweight, heavyset",
      "4": "obese, large belly",
      "5": "very obese, huge belly",
      "6": "morbidly obese, gigantic belly",
      "7": "extremely obese, colossal belly",
      "8": "super obese, unimaginable belly"
    },
  },
  ass: {
    min: -3,
    max: 5,
    lora: "Ass Size Slider - Illustrious",
    label: "Ass Size",
    prompts: {
      "-3": " small ass",
      "0": "average ass",
      "1": "medium ass",
      "2": "large ass",
      "3": "very large ass"

    }
  },
  thighs: {
    min: -3,
    max: 5,
    lora: "Thighs slider IXL4_alpha16.0_rank32_full_last.safetensors",
    label: "Thigh Size",
    prompts:{
      "-3": "",
      "0": "average thighs",
      "1": "thick thighs",
    }
  },
  pregnancy:{
    min:0,
    max:4,
    lora: "pregnancy_slider",
    label: "Pregnancy",
    prompts:{
      "0": "",
      "1": "pregnant"
    }
  },
  muscle:{
    min:-10,
    max:10,
    lora: "muscle_slider_v4",
    prompts: {
      "-10": "very low muscle mass",
      "0": "average muscle mass",
      "2": "moderate muscle mass",
    }
  }
}

// --- Customer state ---
const customers = ref([]);
const currentCustomerIndex = ref(0);
const isGenerating = ref(false);
const mixedImage = ref(null);
const servedCount = ref(0);

const currentCustomer = computed(() => customers.value[currentCustomerIndex.value] || null);
const customerImage = computed(() => {
  const c = currentCustomer.value;
  if (!c) return null;
  return c.current_image || c.default_image;
});

// --- Effects prompt builder ---
function get_effects_prompt(effects) {
  let prompt = ""
  for (const effect in effects) {
    if (Effects[effect]) {
      const value = effects[effect]
      if (value === 0) continue
      const { lora } = Effects[effect]
      prompt += `<lora:${lora}:${value}> `

      // Add descriptive prompt for positive/negative values
      const range = Effects[effect].prompts
      if (range) {
        const closestValue = Object.keys(range).reduce((prev, curr) => {
          return Math.abs(curr - value) < Math.abs(prev - value) ? curr : prev;
        });
        prompt += range[closestValue] + " "
      }
    }
  }
  return prompt
}

// --- Image generation via SD API ---
async function generateImage(prompt) {
  const _request = formatRequest(prompt)
  console.log("Generating image with prompt:",_request.prompt);
  const response = await fetch(webuiUrl.value + 'sdapi/v1/txt2img', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(_request)
  })
  const result = await response.json()
  return "data:image/png;base64," + result.images[0]
}

// --- Generate all customers with random appearance & effect preferences ---
function generateCustomers() {
  const effectKeys = Object.keys(Effects);
  customers.value = [];
  for (let i = 0; i < character_count.value; i++) {
    const shuffled = [...effectKeys].sort(() => Math.random() - 0.5);
    const desired = [shuffled[0]];
    const disliked = shuffled.length > 1 ? [shuffled[1]] : [];
    customers.value.push({
      id: i,
      appearancePrompt: GetRandomCharacter(),
      desired_effects: desired,
      disliked_effects: disliked,
      default_image: null,
      current_image: null,
    });
  }
}

// --- Generate the neutral default image for a customer ---
async function generateDefaultImage(customer) {
  if (!customer || customer.default_image) return;
  isGenerating.value = true;
  try {
    const prompt = "1girl, " + customer.appearancePrompt + ", neutral expression, standing, looking at viewer";
    const image = await generateImage(prompt);
    customer.default_image = image;
    if (!customer.current_image) {
      customer.current_image = image;
    }
  } catch (e) {
    console.error("Failed to generate default image:", e);
  } finally {
    isGenerating.value = false;
  }
}

// --- Determine emotion based on whether customer likes/dislikes the effects ---
function getEmotion(combinedEffects, customer) {
  let hasDesired = false;
  let hasDisliked = false;
  for (const effect in combinedEffects) {
    if (combinedEffects[effect] === 0) continue;
    if (customer.desired_effects.includes(effect)) hasDesired = true;
    if (customer.disliked_effects.includes(effect)) hasDisliked = true;
  }
  if (hasDesired && !hasDisliked) return "happy, smile, cheerful";
  if (hasDisliked && !hasDesired) return "angry, frown, annoyed";
  if (hasDesired && hasDisliked) return "neutral expression, uncertain";
  return "sad, disappointed";
}

// --- UI state ---
const selectedIngredients = ref([]);
const isMixing = ref(false);
const serveReady = ref(false);
const servedMessage = ref("");
const isTransitioning = ref(false);

const drinkName = computed(() => {
  if (selectedIngredients.value.length === 0) return "Empty Cup";
  return selectedIngredients.value.map(i => i.name).join(" + ") + " Latte";
});

const drinkColor = computed(() => {
  if (selectedIngredients.value.length === 0) return "bg-slate-100";
  if (selectedIngredients.value.some(i => i.id === "cocoa")) return "bg-amber-900";
  if (selectedIngredients.value.some(i => i.id === "coffee")) return "bg-amber-800";
  return "bg-amber-300";
});

// --- Drag handlers ---
const handleDragStart = (event, ingredientId) => {
  event.dataTransfer.setData("text/plain", ingredientId);
};

const handleIngredientDrop = (event) => {
  event.preventDefault();
  const ingredientId = event.dataTransfer.getData("text/plain");
  const ingredient = ingredients.value.find(i => i.id === ingredientId);
  if (!ingredient) return;
  if (serveReady.value || isMixing.value) return;
  selectedIngredients.value.push(ingredient);
};

// --- Mix: generate the transformed image with effects + emotion ---
const handleMix = async () => {
  if (selectedIngredients.value.length === 0 || !currentCustomer.value) return;
  isMixing.value = true;
  serveReady.value = false;
  servedMessage.value = "";

  // Accumulate effects from all ingredients
  const combinedEffects = {};
  for (const ingredient of selectedIngredients.value) {
    for (const [effect, value] of Object.entries(ingredient.effects || {})) {
      combinedEffects[effect] = (combinedEffects[effect] || 0) + value;
    }
  }
  // Clamp to min/max
  for (const effect in combinedEffects) {
    if (Effects[effect]) {
      combinedEffects[effect] = Math.max(
        Effects[effect].min,
        Math.min(Effects[effect].max, combinedEffects[effect])
      );
    }
  }

  const emotion = getEmotion(combinedEffects, currentCustomer.value);
  const effectsPrompt = get_effects_prompt(combinedEffects);
  const prompt = "1girl, " + currentCustomer.value.appearancePrompt + ", " + emotion + ", standing, looking at viewer, " + effectsPrompt;

  try {
    mixedImage.value = await generateImage(prompt);
    isMixing.value = false;
    serveReady.value = true;
  } catch (e) {
    console.error("Mix generation failed:", e);
    isMixing.value = false;
  }
};

const handleClear = () => {
  selectedIngredients.value = [];
  serveReady.value = false;
  servedMessage.value = "";
  mixedImage.value = null;
};

const handleDrinkDragStart = (event) => {
  if (!serveReady.value) return;
  event.dataTransfer.setData("text/plain", "drink-ready");
};

// --- Serve: apply mixed image, transition to next customer ---
const handleCustomerDrop = async (event) => {
  event.preventDefault();
  const payload = event.dataTransfer.getData("text/plain");
  if (payload !== "drink-ready" || !serveReady.value) return;

  // Show the mixed result on the current customer
  if (mixedImage.value && currentCustomer.value) {
    currentCustomer.value.current_image = mixedImage.value;
  }

  servedMessage.value = `Served: ${drinkName.value}!`;
  servedCount.value++;
  selectedIngredients.value = [];
  serveReady.value = false;
  mixedImage.value = null;

  // Advance to next customer
  const nextIndex = currentCustomerIndex.value + 1;
  if (nextIndex < customers.value.length) {
    const nextCustomer = customers.value[nextIndex];

    // Start generating next customer's default image + 5s minimum display timer
    const genPromise = generateDefaultImage(nextCustomer);
    const timerPromise = new Promise(resolve => setTimeout(resolve, 5000));

    // Wait for both generation to complete AND 5s to elapse
    await Promise.all([genPromise, timerPromise]);

    // Transition to next customer
    isTransitioning.value = true;
    currentCustomerIndex.value = nextIndex;
    servedMessage.value = "";
    setTimeout(() => { isTransitioning.value = false; }, 500);
  } else {
    // All customers served
    setTimeout(() => {
      servedMessage.value = "All customers served! Day complete!";
    }, 2000);
  }
};

const preventDrop = (event) => event.preventDefault();

// --- Initialize on mount ---
onMounted(async () => {
  generateCustomers();
  await generateDefaultImage(customers.value[0]);
});
</script>

<template>
  <section class="h-screen w-full overflow-hidden bg-stone-900 fixed top-0 left-0 z-40 select-none">
    <!-- Background Image -->
    <div class="absolute inset-0 z-0">
      <img src="/cafebg.jpg" alt="Cafe Background" class="h-full w-full object-cover opacity-30" />
      <div class="absolute inset-0 bg-gradient-to-r from-stone-950/80 via-stone-900/50 to-stone-950/80"></div>
    </div>

    <!-- Main Horizontal Layout -->
    <div class="relative z-10 flex h-full w-full">

      <!-- LEFT: Character Panel (~45% width) -->
      <div class="relative flex h-full w-[45%] flex-col items-center justify-end overflow-hidden"
        @drop="handleCustomerDrop" @dragover="preventDrop">
        <!-- Ambient glow behind character -->
        <div
          class="absolute bottom-[10%] left-1/2 -translate-x-1/2 h-[500px] w-[500px] rounded-full bg-amber-500/10 blur-[120px]">
        </div>

        <!-- Order Ticket -->
        <div v-if="currentCustomer"
          class="absolute left-6 top-6 z-30 w-56 rounded-2xl bg-yellow-50/95 px-5 py-4 shadow-2xl ring-2 ring-amber-300/60 backdrop-blur-sm">
          <p class="text-[10px] font-semibold uppercase tracking-widest text-amber-500">Customer #{{ currentCustomer.id + 1 }}</p>
          <div class="mt-2">
            <p class="text-[10px] font-bold uppercase text-green-600">Wants:</p>
            <p v-for="e in currentCustomer.desired_effects" :key="'d-'+e" class="text-xs font-semibold text-stone-700">+ {{ Effects[e]?.label || e }}</p>
          </div>
          <div class="mt-1">
            <p class="text-[10px] font-bold uppercase text-red-500">Dislikes:</p>
            <p v-for="e in currentCustomer.disliked_effects" :key="'x-'+e" class="text-xs font-semibold text-stone-700">- {{ Effects[e]?.label || e }}</p>
          </div>
          <div class="mt-3 flex items-center gap-1.5">
            <div class="h-2 w-2 animate-pulse rounded-full" :class="isMixing ? 'bg-amber-400' : 'bg-green-400'"></div>
            <span class="text-[10px] font-bold uppercase" :class="isMixing ? 'text-amber-600' : 'text-green-600'">{{ isMixing ? 'Mixing...' : 'Waiting' }}</span>
          </div>
        </div>

        <!-- Day / Score badge -->
        <div
          class="absolute right-6 top-6 z-30 rounded-xl bg-stone-800/90 px-4 py-3 text-center shadow-xl ring-1 ring-amber-500/20 backdrop-blur-sm">
          <p class="text-[10px] font-semibold uppercase tracking-widest text-amber-400">Day {{ day }}</p>
          <p class="text-xs text-stone-400 mt-1">{{ servedCount }}/{{ character_count }} served</p>
        </div>

        <!-- Settings button -->
        <button
          class="absolute right-6 bottom-8 z-30 flex items-center justify-center rounded-xl bg-stone-800/90 p-3 shadow-xl ring-1 ring-amber-500/20 backdrop-blur-sm transition hover:bg-stone-700/90 hover:ring-amber-400/50"
          @click="webState.sidebarWidth = webState.sidebarWidth === 0 ? 500 : 0"
          title="Settings">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>

        <!-- Served feedback -->
        <Transition name="fade">
          <div v-if="servedMessage"
            class="absolute top-1/4 z-40 rounded-2xl bg-green-500/90 px-8 py-4 text-center shadow-2xl backdrop-blur-sm">
            <p class="text-lg font-extrabold text-white">{{ servedMessage }}</p>
          </div>
        </Transition>

        <!-- Character sprite (large, fills most of the left panel) -->
        <div class="relative z-20 mb-0 flex items-end justify-center" style="height: 85%;">
          <!-- Loading state -->
          <div v-if="isGenerating && !customerImage"
            class="flex flex-col items-center justify-center gap-4 text-amber-300">
            <div class="h-16 w-16 animate-spin rounded-full border-4 border-amber-400 border-t-transparent"></div>
            <p class="text-sm font-bold">Generating customer...</p>
          </div>
          <!-- Customer image -->
          <img v-else-if="customerImage" :src="customerImage" alt="Customer"
            class="h-full max-h-[85vh] w-auto object-contain object-bottom drop-shadow-2xl transition-all duration-500"
            :class="[servedMessage ? 'scale-105' : 'hover:scale-[1.02]', isTransitioning ? 'opacity-0' : 'opacity-100']"
            style="filter: drop-shadow(0 30px 50px rgba(0,0,0,0.7));" />
          <!-- Fallback placeholder -->
          <div v-else class="flex flex-col items-center justify-center gap-4 text-stone-500">
            <div class="h-32 w-32 rounded-full bg-stone-800 flex items-center justify-center text-4xl">?</div>
            <p class="text-sm font-bold">No customer yet</p>
          </div>
        </div>

        <!-- Counter ledge across the bottom of the character panel -->
        <div
          class="absolute bottom-0 left-0 z-30 h-3 w-full bg-gradient-to-b from-amber-600 via-amber-700 to-amber-800 shadow-lg">
        </div>
      </div>

      <!-- Vertical Counter Edge -->
      <div class="relative z-30 w-1.5 bg-gradient-to-b from-amber-700 via-amber-800 to-amber-900 shadow-xl"></div>

      <!-- RIGHT: Workspace Panel (~55% width) -->
      <div class="relative flex h-full w-[55%] flex-col">

        <!-- Wood texture overlay -->
        <div
          class="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] from-amber-800/15 via-transparent to-transparent">
        </div>

        <!-- Top: Cup display area -->
        <div class="relative z-10 flex flex-1 items-center justify-center px-10">
          <div class="flex flex-col items-center gap-6">
            <!-- Drink Cup -->
            <div
              class="group flex cursor-pointer flex-col items-center gap-3 rounded-3xl bg-gradient-to-br from-stone-800/80 to-stone-900/90 p-8 shadow-2xl backdrop-blur-md ring-1 transition-all duration-200"
              :class="serveReady
                ? 'cursor-grab ring-amber-400/60 shadow-amber-400/30 hover:scale-105 hover:shadow-amber-400/50'
                : 'cursor-not-allowed ring-stone-700/40 opacity-50'" draggable="true"
              @dragstart="handleDrinkDragStart">
              <!-- Cup Visual -->
              <div class="relative h-36 w-28">
                <div
                  class="absolute bottom-0 h-28 w-28 rounded-b-3xl bg-gradient-to-b from-stone-100 via-stone-50 to-white shadow-2xl"
                  style="clip-path: polygon(12% 0%, 88% 0%, 100% 100%, 0% 100%);"></div>
                <div
                  :class="['absolute bottom-2 left-3 right-3 h-24 rounded-b-2xl shadow-inner transition-colors duration-500', drinkColor]">
                </div>
                <div
                  class="absolute left-1/2 top-0 -translate-x-1/2 rounded-full px-4 py-1.5 text-xs font-extrabold text-white shadow-lg"
                  :class="serveReady ? 'bg-gradient-to-r from-green-400 to-emerald-500' : 'bg-gradient-to-r from-amber-400 to-amber-500'">
                  {{ serveReady ? "✓ READY" : selectedIngredients.length > 0 ? "MIXING" : "EMPTY" }}
                </div>
              </div>
              <p class="text-sm font-bold text-amber-200">{{ drinkName }}</p>
              <p v-if="serveReady" class="text-[10px] font-semibold uppercase tracking-widest text-amber-400/70">
                Drag to customer to serve
              </p>
            </div>
          </div>
        </div>

        <!-- Middle: Mix Station -->
        <div class="relative z-10 px-8 pb-4">
          <div
            class="rounded-2xl border-2 border-dashed bg-gradient-to-br from-stone-900/80 to-stone-950/80 p-5 shadow-xl backdrop-blur-md transition-colors duration-200"
            :class="selectedIngredients.length > 0 ? 'border-amber-400/50 ring-1 ring-amber-500/20' : 'border-stone-600/40'"
            @drop="handleIngredientDrop" @dragover="preventDrop">
            <div class="mb-3 flex items-center justify-between">
              <p class="text-sm font-extrabold uppercase tracking-wider text-amber-300">Mix Station</p>
              <div class="flex gap-2">
                <button
                  class="rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 px-6 py-2 text-xs font-extrabold text-white shadow-lg transition-all hover:from-amber-400 hover:to-amber-500 hover:shadow-amber-500/30 disabled:cursor-not-allowed disabled:opacity-30"
                  :disabled="selectedIngredients.length === 0 || isMixing" @click="handleMix">
                  {{ isMixing ? "MIXING..." : "MIX" }}
                </button>
                <button
                  class="rounded-xl border border-stone-600 bg-stone-800/80 px-4 py-2 text-xs font-bold text-stone-400 transition hover:bg-stone-700 hover:text-stone-200"
                  @click="handleClear">
                  CLEAR
                </button>
              </div>
            </div>

            <div class="flex min-h-[52px] flex-wrap items-center justify-center gap-2 rounded-xl bg-stone-950/40 p-3">
              <span v-for="(item, index) in selectedIngredients" :key="`${item.id}-${index}`"
                :class="['flex items-center gap-1 rounded-full px-4 py-1.5 text-xs font-bold shadow-lg ring-1 ring-black/10', item.color]">
                {{ item.name }}
              </span>
              <span v-if="selectedIngredients.length === 0" class="text-xs text-stone-600">
                Drag ingredients here...
              </span>
            </div>
          </div>
        </div>

        <!-- Bottom: Ingredient Shelf -->
        <div class="relative z-10 border-t border-stone-700/40 bg-stone-950/60 px-8 py-5 backdrop-blur-sm">
          <p class="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-amber-500/80">Ingredients</p>
          <div class="grid grid-cols-5 gap-3">
            <div v-for="ingredient in ingredients" :key="ingredient.id"
              class="group cursor-grab transition-all active:cursor-grabbing" draggable="true"
              @dragstart="(event) => handleDragStart(event, ingredient.id)">
              <div
                class="flex flex-col items-center gap-2 rounded-xl bg-gradient-to-br from-stone-800 to-stone-850 p-3 shadow-lg ring-1 ring-stone-700/50 transition-all duration-150 hover:-translate-y-1 hover:shadow-xl hover:ring-amber-500/40 group-active:scale-95">
                <div class="flex h-12 w-12 items-center justify-center rounded-lg shadow-md"
                  :class="[ingredient.color]"></div>
                <p class="text-[11px] font-bold text-stone-200">{{ ingredient.name }}</p>
                
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>