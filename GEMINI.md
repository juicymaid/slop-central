# Gemini Developer Guide: Slop Central

Welcome to **Slop Central** — a personal AI-generated image gallery and management platform. This file acts as a shortcut to help you understand the architecture, data schemas, and backend/frontend patterns without needing to scan the entire workspace.

---

## 🏗️ Project Architecture & Stack

Slop Central is a split-stack local application:

- **Backend**: Python 3.10+ FastAPI serving REST endpoints and WebSockets.
- **Frontend**: Vue 3 (Composition API), Vite 6, Tailwind CSS v4, and Vue Router 4.
- **External Dependencies**:
  - **Stable Diffusion WebUI / Forge** running at `http://127.0.0.1:7860` (proxied for image generation, checkpoints, LoRAs).
  - **LM STUDIO** running locally (for AI assistant tools, chat, and story descriptions).
  - **WD14 Tagger (ONNX)**: Runs locally within the FastAPI runtime to tag images.

---

## 📂 Key Files & Directories

### 🐍 Backend (`img-api/`)
- [main.py](file:///h:/ent/ai/slop-central/img-api/main.py) — Entry point. Sets up FastAPI, middleware, handles automatic frontend dev server launching, and registers routes.
- [utils.py](file:///h:/ent/ai/slop-central/img-api/utils.py) — Critical utilities. Contains database JSON loader/saver helpers, image parsing logic (`sd_parsers`), path configurations, and similarity math (pHash similarity).
- [routes/](file:///h:/ent/ai/slop-central/img-api/routes/) — Submodules for each feature. Key routes:
  - [images.py](file:///h:/ent/ai/slop-central/img-api/routes/images.py) — Core CRUD, advanced searching, and soft-delete/trash management.
  - [mcp.py](file:///h:/ent/ai/slop-central/img-api/routes/mcp.py) — JSON-RPC style Model Context Protocol (MCP) server endpoints exposing assistant tools.
  - [assistant.py](file:///h:/ent/ai/slop-central/img-api/routes/assistant.py) — Ollama-based chat assistant (`Airi`) with custom tools (search, generate, comment, CivitAI).
  - [rate.py](file:///h:/ent/ai/slop-central/img-api/routes/rate.py) — Head-to-head matchmaker and rating updater using the TrueSkill algorithm.
  - [scan_images.py](file:///h:/ent/ai/slop-central/img-api/routes/scan_images.py) — Handles filesystem folder scanning via WebSocket connections.
  - [tagger.py](file:///h:/ent/ai/slop-central/img-api/routes/tagger.py) — Integrates WD14 Danbooru tags predictor using `onnxruntime`.

### ⚡ Frontend (`vue-project/`)
- [src/api.js](file:///h:/ent/ai/slop-central/vue-project/src/api.js) — Central API communication hub containing reactive states, API call wrappers, and WebSocket connection helpers.
- [src/App.vue](file:///h:/ent/ai/slop-central/vue-project/src/App.vue) — Root component holding global shell, top navigation, search bar, and dark mode toggles.
- [src/views/](file:///h:/ent/ai/slop-central/vue-project/src/views/) — Primary page-level modules:
  - `galleryView.vue` — Masonry image feed with grid size, sort modes, and filter controls.
  - `canvasView.vue` — Inpainting, sketching, and canvas operations.
  - `rateView.vue` — Side-by-side comparison rating view.
- [src/components/](file:///h:/ent/ai/slop-central/vue-project/src/components/) — Reusable elements:
  - `CreateSidebar.vue` — Panel containing SD generation options, LoRA/checkpoint selections, prompts, and controls.
  - `ChatPanel.vue` — Inline chat sidebar for communicating with Ollama about a specific image.

---

## 💾 Data Store Schemas (JSON flat-files)

All databases are stored as flat JSON files in `img-api/storage/` (or `img-api/` parent directory):

- `images.json` — Maps ID (hash/UUID) to metadata:
  ```json
  {
    "id": {
      "path": "absolute/path/to/img.png",
      "width": 1024,
      "height": 1024,
      "created_at": 1719600000.0,
      "prompt": "prompt text",
      "negative_prompt": "negative prompt",
      "steps": 28,
      "sampler": "Euler a",
      "cfg": 7.0,
      "seed": 12345,
      "model": "model_name",
      "tags": ["tag1", "tag2"],
      "custom_tags": ["my_tag"]
    }
  }
  ```
- `likes.json` — User star ratings (1-5 stars) and favorite boolean flags.
- `ratings.json` — TrueSkill model scores containing `mu` (mean skill value) and `sigma` (uncertainty value) per image ID.
- `boards.json` — Pinboards mapping board IDs to lists of image IDs.
- `hashes.json` — Maps image IDs to perceptual hashes (pHash) for duplicate detection and similarity matching.
- `comments.json` — Maps image IDs to comments and AI descriptions.
- `trash.json` — List of image IDs currently moved to the Trash bin.

---

## 🛠️ Codebase Patterns & Development Guidelines

1. **JSON Database Locking**: When reading or writing JSON database files, use the helper functions in [utils.py](file:///h:/ent/ai/slop-central/img-api/utils.py) to prevent concurrency race conditions.
2. **Adding a New Route**:
   - Create a module under `img-api/routes/<name>.py`.
   - Instantiate an `APIRouter` with prefix.
   - Register it in `img-api/main.py` using `app.include_router(<module>.router)`.
3. **Hardcoded Paths Warning**:
   - Watch out for hardcoded directory structures in [img-api/routes/scan_images.py](file:///h:/ent/ai/slop-central/img-api/routes/scan_images.py), [img-api/routes/webui.py](file:///h:/ent/ai/slop-central/img-api/routes/webui.py), [img-api/utils.py](file:///h:/ent/ai/slop-central/img-api/utils.py), and [img-api/main.py](file:///h:/ent/ai/slop-central/img-api/main.py). Adjust these paths if you're configuring a new folder to scan or WebUI path.
4. **WebSocket Communication**:
   - Real-time features (GPU VRAM monitoring, assistant chats, image folder scanning) are driven by WebSockets.
   - Always verify socket connection state and lifecycle hooks inside Vue components before sending messages.
