<template>
  <div class="ranbooru-container ">
    <!-- Main Ranbooru Section -->
    <div class="accordion-section">
      <div class="accordion-header" @click="toggleAccordion('ranbooru')">
        <h3>Ranbooru</h3>
        <input type="checkbox" v-model="enabled" @click.stop />
      </div>
      
      <div v-if="accordions.ranbooru" class="accordion-content text-white">
        <!-- Booru Selection -->
        <div class="form-group">
          <label>Booru:</label>
          <select v-model="selectedBooru" @change="onBooruChange">
            <option v-for="booru in booruOptions" :key="booru" :value="booru">
              {{ booru }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>Max Pages:</label>
          <input type="range" v-model="maxPages" min="1" max="100" />
          <span>{{ maxPages }}</span>
        </div>

        <!-- Post Section -->
        <h4>Post</h4>
        <div class="form-group">
          <label>Post ID:</label>
          <input type="text" v-model="postId" placeholder="Enter post ID" />
        </div>

        <!-- Tags Section -->
        <h4>Tags</h4>
        <div class="form-group">
          <label>Tags to Search (Pre):</label>
          <input type="text" v-model="searchTags" placeholder="Enter search tags" />
        </div>

        <div class="form-group">
          <label>Tags to Remove (Post):</label>
          <input type="text" v-model="removeTags" placeholder="Enter tags to remove" />
        </div>

        <div class="form-group">
          <label>Mature Rating:</label>
          <div class="radio-group">
            <label v-for="rating in availableRatings" :key="rating">
              <input type="radio" v-model="matureRating" :value="rating" />
              {{ rating }}
            </label>
          </div>
        </div>

        <!-- Options -->
        <div class="checkbox-group">
          <label><input type="checkbox" v-model="removeBadTags" /> Remove bad tags</label>
          <label><input type="checkbox" v-model="shuffleTags" /> Shuffle tags</label>
          <label><input type="checkbox" v-model="changeDash" /> Convert "_" to spaces</label>
          <label><input type="checkbox" v-model="samePrompt" /> Use same prompt for all images</label>
          <label v-if="selectedBooru === 'gelbooru'">
            <input type="checkbox" v-model="fringeBenefits" /> Fringe Benefits
          </label>
        </div>

        <!-- Gelbooru API Credentials -->
        <div v-if="selectedBooru === 'gelbooru'" class="credentials-section">
          <h4>Gelbooru API Credentials</h4>
          <div v-if="!hasSavedCredentials">
            <div class="form-group">
              <label>API Key:</label>
              <input type="password" v-model="apiKey" placeholder="Enter your Gelbooru API key" />
            </div>
            <div class="form-group">
              <label>User ID:</label>
              <input type="text" v-model="userId" placeholder="Enter your Gelbooru user ID" />
            </div>
            <label><input type="checkbox" v-model="saveCredentials" /> Save credentials</label>
          </div>
          <div v-else>
            <p class="credentials-status">✓ Credentials loaded</p>
            <button @click="clearCredentials" class="btn-secondary">Clear saved credentials</button>
          </div>
        </div>

        <!-- Limit and Background Options -->
        <div class="form-group">
          <label>Limit tags:</label>
          <input type="range" v-model="limitTags" min="0.05" max="1.0" step="0.05" />
          <span>{{ limitTags }}</span>
        </div>

        <div class="form-group">
          <label>Max tags:</label>
          <input type="range" v-model="maxTags" min="1" max="100" />
          <span>{{ maxTags }}</span>
        </div>

        <div class="form-group">
          <label>Change Background:</label>
          <select v-model="changeBackground">
            <option v-for="option in backgroundOptions" :key="option" :value="option">
              {{ option }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>Change Color:</label>
          <select v-model="changeColor">
            <option v-for="option in colorOptions" :key="option" :value="option">
              {{ option }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>Sorting Order:</label>
          <div class="radio-group">
            <label v-for="order in sortingOptions" :key="order">
              <input type="radio" v-model="sortingOrder" :value="order" />
              {{ order }}
            </label>
          </div>
        </div>

        <!-- Img2Img Section -->
        <div class="accordion-subsection">
          <div class="accordion-header" @click="toggleAccordion('img2img')">
            <h4>Img2Img</h4>
          </div>
          <div v-if="accordions.img2img" class="accordion-content">
            <div class="checkbox-group">
              <label><input type="checkbox" v-model="useImg2img" /> Use img2img</label>
              <label><input type="checkbox" v-model="useIp" /> Send to Controlnet</label>
              <label><input type="checkbox" v-model="useLastImg" /> Use last image as img2img</label>
              <label><input type="checkbox" v-model="cropCenter" /> Crop Center</label>
              <label><input type="checkbox" v-model="useDeepbooru" /> Use Deepbooru</label>
            </div>

            <div class="form-group">
              <label>Denoising:</label>
              <input type="range" v-model="denoising" min="0.05" max="1.0" step="0.05" />
              <span>{{ denoising }}</span>
            </div>

            <div class="form-group">
              <label>Deepbooru Tags Position:</label>
              <div class="radio-group">
                <label v-for="pos in deepbooruPositions" :key="pos">
                  <input type="radio" v-model="typeDeepbooru" :value="pos" />
                  {{ pos }}
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- Extra Options -->
        <div class="accordion-subsection">
          <div class="accordion-header" @click="toggleAccordion('extra')">
            <h4>Extra</h4>
          </div>
          <div v-if="accordions.extra" class="accordion-content">
            <!-- Mix Prompts -->
            <div class="option-box">
              <label><input type="checkbox" v-model="mixPrompt" /> Mix prompts</label>
              <div v-if="mixPrompt" class="form-group">
                <label>Mix amount:</label>
                <input type="range" v-model="mixAmount" min="2" max="10" />
                <span>{{ mixAmount }}</span>
              </div>
            </div>

            <!-- Chaos Mode -->
            <div class="option-box">
              <label>Chaos Mode:</label>
              <div class="radio-group">
                <label v-for="mode in chaosModes" :key="mode">
                  <input type="radio" v-model="chaosMode" :value="mode" />
                  {{ mode }}
                </label>
              </div>
              <div v-if="chaosMode !== 'None'" class="form-group">
                <label>Chaos Amount %:</label>
                <input type="range" v-model="chaosAmount" min="0.1" max="1" step="0.05" />
                <span>{{ chaosAmount }}</span>
              </div>
            </div>

            <!-- Negative Mode -->
            <div class="option-box">
              <label>Negative Mode:</label>
              <div class="radio-group">
                <label v-for="mode in negativeModes" :key="mode">
                  <input type="radio" v-model="negativeMode" :value="mode" />
                  {{ mode }}
                </label>
              </div>
              <label><input type="checkbox" v-model="useSameSeed" /> Use same seed for all pictures</label>
            </div>

            <div class="option-box">
              <label><input type="checkbox" v-model="useCache" /> Use cache</label>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="action-buttons">
          <button @click="searchImages" class="btn-primary" :disabled="loading">
            {{ loading ? 'Searching...' : 'Search Images' }}
          </button>
          <button @click="clearForm" class="btn-secondary">Clear Form</button>
        </div>
      </div>
    </div>

    <!-- LoRAnado Section -->
    <div class="accordion-section">
      <div class="accordion-header" @click="toggleAccordion('loranado')">
        <h3>LoRAnado</h3>
        <input type="checkbox" v-model="loraEnabled" @click.stop />
      </div>
      
      <div v-if="accordions.loranado" class="accordion-content">
        <div class="checkbox-group">
          <label><input type="checkbox" v-model="loraLockPrev" /> Lock previous LoRAs</label>
        </div>

        <div class="form-group">
          <label>LoRAs Subfolder:</label>
          <input type="text" v-model="loraFolder" placeholder="Enter LoRA folder path" />
        </div>

        <div class="form-group">
          <label>LoRAs Amount:</label>
          <input type="range" v-model="loraAmount" min="1" max="10" />
          <span>{{ loraAmount }}</span>
        </div>

        <div class="form-group">
          <label>Min LoRAs Weight:</label>
          <input type="range" v-model="loraMin" min="-1.0" max="1.0" step="0.1" />
          <span>{{ loraMin }}</span>
        </div>

        <div class="form-group">
          <label>Max LoRAs Weight:</label>
          <input type="range" v-model="loraMax" min="-1.0" max="1.0" step="0.1" />
          <span>{{ loraMax }}</span>
        </div>

        <div class="form-group">
          <label>LoRAs Custom Weights:</label>
          <input type="text" v-model="loraCustomWeights" placeholder="Enter custom weights (comma-separated)" />
        </div>
      </div>
    </div>

    <!-- Results Section -->
    <div v-if="searchResults.length > 0" class="results-section">
      <h3>Search Results</h3>
      <div class="results-grid">
        <div v-for="(result, index) in searchResults" :key="index" class="result-item">
          <img :src="result.previewUrl" :alt="`Result ${index + 1}`" @error="handleImageError" />
          <div class="result-info">
            <p><strong>Score:</strong> {{ result.score || 'N/A' }}</p>
            <p class="tags">{{ result.tags.substring(0, 100) }}...</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RanbooruComponent',
  data() {
    return {
      // Main toggles
      enabled: false,
      loraEnabled: false,
      
      // Accordion states
      accordions: {
        ranbooru: false,
        img2img: false,
        extra: false,
        loranado: false
      },

      // Booru options
      booruOptions: ['safebooru', 'rule34', 'danbooru', 'gelbooru', 'konachan', 'yande.re', 'aibooru', 'xbooru', 'e621'],
      selectedBooru: 'safebooru',
      maxPages: 100,

      // Post and tags
      postId: '',
      searchTags: '',
      removeTags: '',
      matureRating: 'All',

      // Options
      removeBadTags: true,
      shuffleTags: true,
      changeDash: false,
      samePrompt: false,
      fringeBenefits: true,

      // Gelbooru credentials
      apiKey: '',
      userId: '',
      saveCredentials: false,
      hasSavedCredentials: false,

      // Limits and appearance
      limitTags: 1.0,
      maxTags: 100,
      changeBackground: "Don't Change",
      changeColor: "Don't Change",
      sortingOrder: 'Random',

      // Img2img options
      useImg2img: false,
      useIp: false,
      useLastImg: false,
      cropCenter: false,
      useDeepbooru: false,
      denoising: 0.75,
      typeDeepbooru: 'Add Before',

      // Extra options
      mixPrompt: false,
      mixAmount: 2,
      chaosMode: 'None',
      chaosAmount: 0.5,
      negativeMode: 'None',
      useSameSeed: false,
      useCache: true,

      // LoRA options
      loraLockPrev: false,
      loraFolder: '',
      loraAmount: 1,
      loraMin: -1.0,
      loraMax: 1.0,
      loraCustomWeights: '',

      // State
      loading: false,
      error: '',
      searchResults: [],

      // Constants
      backgroundOptions: ["Don't Change", "Add Background", "Remove Background", "Remove All"],
      colorOptions: ["Don't Change", "Colored", "Limited Palette", "Monochrome"],
      sortingOptions: ['Random', 'High Score', 'Low Score'],
      deepbooruPositions: ['Add Before', 'Add After', 'Replace'],
      chaosModes: ['None', 'Chaos', 'Less Chaos'],
      negativeModes: ['None', 'Negative'],

      // Rating mappings
      ratingTypes: {
        none: { All: 'All' },
        full: { All: 'All', Safe: 'safe', Questionable: 'questionable', Explicit: 'explicit' },
        single: { All: 'All', Safe: 'g', Sensitive: 's', Questionable: 'q', Explicit: 'e' }
      },

      ratings: {
        'e621': 'full',
        'danbooru': 'single',
        'aibooru': 'full',
        'yande.re': 'full',
        'konachan': 'full',
        'safebooru': 'none',
        'rule34': 'full',
        'xbooru': 'full',
        'gelbooru': 'single'
      },

      // Bad tags to remove
      badTags: [
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
      ]
    }
  },

  computed: {
    availableRatings() {
      const ratingType = this.ratings[this.selectedBooru] || 'none';
      return Object.keys(this.ratingTypes[ratingType]);
    }
  },

  methods: {
    toggleAccordion(section) {
      this.accordions[section] = !this.accordions[section];
    },

    onBooruChange() {
      // Reset mature rating when booru changes
      this.matureRating = 'All';
      // Clear credentials when switching away from Gelbooru
      if (this.selectedBooru !== 'gelbooru') {
        this.apiKey = '';
        this.userId = '';
        this.hasSavedCredentials = false;
      }
    },

    clearCredentials() {
      this.apiKey = '';
      this.userId = '';
      this.hasSavedCredentials = false;
      // Here you would also clear from localStorage or your storage mechanism
      localStorage.removeItem('gelbooru_credentials');
    },

    async searchImages() {


      this.loading = true;
      this.error = '';
      
      try {
        // Validate inputs
        this.validateInputs();

        // Build search parameters
        const searchParams = this.buildSearchParams();
        
        // Perform search
        const results = await this.performSearch(searchParams);
        
        // Process results
        this.searchResults = this.processResults(results);
        
      } catch (err) {
        this.error = err.message;
        console.error('Search error:', err);
      } finally {
        this.loading = false;
      }
    },

    validateInputs() {
      // Check booru-specific limitations
      if (this.selectedBooru === 'konachan' && this.postId) {
        throw new Error('Konachan does not support post IDs');
      }
      if (this.selectedBooru === 'yande.re' && this.postId) {
        throw new Error('Yande.re does not support post IDs');
      }
      if (this.selectedBooru === 'e621' && this.postId) {
        throw new Error('e621 does not support post IDs');
      }
      if (this.selectedBooru === 'danbooru' && this.searchTags.split(',').length > 1) {
        throw new Error('Danbooru does not support multiple tags. You can have only one tag.');
      }
    },

    buildSearchParams() {
      let tags = this.searchTags;
      
      // Add background modifications
      if (this.changeBackground !== "Don't Change") {
        const backgroundMods = {
          'Add Background': 'detailed_background,outdoors',
          'Remove Background': 'plain_background,simple_background',
          'Remove All': ''
        };
        if (backgroundMods[this.changeBackground]) {
          tags += (tags ? ',' : '') + backgroundMods[this.changeBackground];
        }
      }

      // Add color modifications
      if (this.changeColor !== "Don't Change") {
        const colorMods = {
          'Limited Palette': '(limited_palette:1.3)',
          'Monochrome': 'monochrome,greyscale'
        };
        if (colorMods[this.changeColor]) {
          tags += (tags ? ',' : '') + colorMods[this.changeColor];
        }
      }

      return {
        booru: this.selectedBooru,
        tags: tags,
        postId: this.postId,
        maxPages: this.maxPages,
        rating: this.matureRating,
        sortingOrder: this.sortingOrder,
        apiKey: this.apiKey,
        userId: this.userId
      };
    },

    async performSearch(params) {
      // This would be your actual API call logic
      // For now, returning mock data
      const mockResults = {
        post: Array.from({ length: 10 }, (_, i) => ({
          id: i + 1,
          score: Math.floor(Math.random() * 100),
          tags: `tag${i + 1} character${i + 1} series${i + 1} rating:safe`,
          file_url: `https://via.placeholder.com/300x300?text=Image${i + 1}`,
          preview_url: `https://via.placeholder.com/150x150?text=Thumb${i + 1}`
        }))
      };

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      return mockResults;
    },

    processResults(data) {
      let posts = data.post || [];

      // Apply sorting
      if (this.sortingOrder === 'High Score') {
        posts.sort((a, b) => (b.score || 0) - (a.score || 0));
      } else if (this.sortingOrder === 'Low Score') {
        posts.sort((a, b) => (a.score || 0) - (b.score || 0));
      } else {
        // Random - shuffle array
        posts = this.shuffleArray([...posts]);
      }

      // Clean tags if needed
      return posts.map(post => ({
        ...post,
        tags: this.cleanTags(post.tags || ''),
        previewUrl: post.preview_url || post.file_url || 'https://via.placeholder.com/150x150?text=NoImage'
      }));
    },

    cleanTags(tagString) {
      if (!tagString) return '';
      
      let tags = tagString.split(' ').filter(tag => tag.trim());
      
      // Remove bad tags if enabled
      if (this.removeBadTags) {
        tags = tags.filter(tag => !this.badTags.includes(tag));
      }

      // Apply remove tags
      if (this.removeTags) {
        const removeList = this.removeTags.split(',').map(t => t.trim());
        tags = tags.filter(tag => !removeList.includes(tag));
      }

      // Convert underscores to spaces if enabled
      if (this.changeDash) {
        tags = tags.map(tag => tag.replace(/_/g, ' '));
      }

      // Shuffle if enabled
      if (this.shuffleTags) {
        tags = this.shuffleArray([...tags]);
      }

      // Apply tag limits
      if (this.limitTags < 1) {
        const limitCount = Math.floor(tags.length * this.limitTags);
        tags = tags.slice(0, limitCount);
      }

      if (this.maxTags > 0 && tags.length > this.maxTags) {
        tags = tags.slice(0, this.maxTags);
      }

      return tags.join(' ');
    },

    shuffleArray(array) {
      const shuffled = [...array];
      for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
      }
      return shuffled;
    },

    clearForm() {
      // Reset form to defaults
      Object.assign(this.$data, this.$options.data());
    },

    handleImageError(event) {
      event.target.src = 'https://via.placeholder.com/150x150?text=Error';
    }
  },

  mounted() {
    // Load saved credentials if any
    const savedCreds = localStorage.getItem('gelbooru_credentials');
    if (savedCreds) {
      try {
        const creds = JSON.parse(savedCreds);
        this.apiKey = creds.apiKey || '';
        this.userId = creds.userId || '';
        this.hasSavedCredentials = !!(creds.apiKey && creds.userId);
      } catch (e) {
        console.error('Error loading saved credentials:', e);
      }
    }
  },

  watch: {
    saveCredentials(newVal) {
      if (newVal && this.apiKey && this.userId) {
        localStorage.setItem('gelbooru_credentials', JSON.stringify({
          apiKey: this.apiKey,
          userId: this.userId
        }));
        this.hasSavedCredentials = true;
      }
    }
  }
}
</script>

<style scoped>
.ranbooru-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.accordion-section {
  margin-bottom: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}

.accordion-header {
  background: #f5f5f5;
  padding: 15px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #ddd;
}

.accordion-header:hover {
  background: #e9e9e9;
}

.accordion-header h3,
.accordion-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.accordion-content {
  padding: 20px;
}

.accordion-subsection {
  margin: 15px 0;
  border: 1px solid #eee;
  border-radius: 4px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-group input[type="range"] {
  width: 70%;
  margin-right: 10px;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 15px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  font-weight: normal;
}

.checkbox-group input[type="checkbox"] {
  width: auto;
  margin-right: 8px;
}

.radio-group {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.radio-group label {
  display: flex;
  align-items: center;
  font-weight: normal;
}

.radio-group input[type="radio"] {
  width: auto;
  margin-right: 5px;
}

.credentials-section {
  background: #f9f9f9;
  padding: 15px;
  border-radius: 4px;
  margin: 15px 0;
}

.credentials-status {
  color: #28a745;
  font-weight: 500;
  margin: 10px 0;
}

.option-box {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  margin: 10px 0;
}

.action-buttons {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.btn-primary,
.btn-secondary {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-primary:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

.results-section {
  margin-top: 30px;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.result-item {
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  background: white;
}

.result-item img {
  width: 100%;
  height: 150px;
  object-fit: cover;
}

.result-info {
  padding: 10px;
}

.result-info p {
  margin: 5px 0;
  font-size: 12px;
}

.tags {
  color: #666;
  word-break: break-all;
}

.error-message {
  background: #f8d7da;
  color: #721c24;
  padding: 15px;
  border-radius: 4px;
  margin: 20px 0;
  border: 1px solid #f5c6cb;
}

h4 {
  color: #495057;
  margin: 20px 0 10px 0;
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

@media (max-width: 768px) {
  .ranbooru-container {
    padding: 10px;
  }

  .accordion-header {
    padding: 10px;
  }

  .accordion-content {
    padding: 15px;
  }

  .radio-group {
    flex-direction: column;
    gap: 8px;
  }

  .results-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 15px;
  }

  .action-buttons {
    flex-direction: column;
  }
}
</style>