# Slop Central

A personal AI-generated image gallery and management platform. Browse, search, organize, and generate Stable Diffusion images — with AI-powered tagging, rating, chat, and recommendations.

## Features

- **Gallery & Search** — Masonry grid browser with sort modes: newest, oldest, top-rated, random, and AI-predicted quality. Advanced search supports `model:`, `sampler:`, `steps:`, `cfg:`, `date:`, and `type:` filters.
- **Image Generation** — Integrated sidebar to send generation requests directly to a local Stable Diffusion WebUI (Forge). Supports model/LoRA selection, per-model prompt prefixes, and ADetailer.
- **AI Tagger** — Automatically tags images using WD14 tagger (deepdanbooru-based).
- **Image Chat** — Per-image AI chat powered by Ollama, with auto-generated descriptions.
- **AI Assistant (Airi)** — General-purpose assistant with tool use: search images, generate images, write comments, and browse CivitAI.
- **TrueSkill Rating** — Head-to-head competitive image rating using the TrueSkill algorithm.
- **Pinboards** — Pinterest-style boards for curating image collections.
- **Stories** — Auto-generated Google Photos-style highlight reels using Ollama.
- **Comics** — Create multi-panel AI comics with AI-generated dialogue.
- **CivitAI Browser** — Browse and download LoRAs and checkpoints from CivitAI within the app.
- **Trash / Restore** — Soft-delete workflow with permanent deletion from disk.
- **VRAM Monitor** — Real-time GPU memory usage streamed via WebSocket.
- **Canvas** — Inpainting/drawing canvas for img2img workflows.
- **Recommendations** — Tag-overlap and pHash similarity-based image recommendations.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3 (Composition API), Vite 6, Tailwind CSS v4, Vue Router 4 |
| Backend | Python, FastAPI, Uvicorn |
| AI / ML | WD14 Tagger (deepdanbooru + onnxruntime), Ollama (chat + embeddings), TrueSkill |
| Image Processing | Pillow, OpenCV, imagehash (pHash), sd_parsers |
| GPU Monitoring | GPUtil, nvidia-ml-py3 |
| External Services | Stable Diffusion WebUI / Forge, Ollama, CivitAI API |
| Data Storage | JSON flat files |

## Project Structure

```
├── img-api/               # Python FastAPI backend
│   ├── main.py            # App entry point, router registration
│   ├── utils.py           # Shared utilities, data loading, similarity
│   ├── requirements.txt   # Python dependencies
│   ├── start.bat          # Launch script
│   ├── routes/            # API route modules
│   │   ├── images.py      # Image CRUD, search, like/dislike, trash
│   │   ├── models.py      # Checkpoint and LoRA browsing
│   │   ├── boards.py      # Pinboard management
│   │   ├── tags.py        # Tag listing and autocomplete
│   │   ├── webui.py       # SD WebUI start/stop/unload control
│   │   ├── scan_images.py # Folder scanning via WebSocket
│   │   ├── tagger.py      # WD14 AI image tagging
│   │   ├── chats.py       # Per-image Ollama chat
│   │   ├── assistant.py   # AI assistant with tool use
│   │   ├── rate.py        # TrueSkill rating system
│   │   ├── comics.py      # Comics CRUD and generation
│   │   ├── stories.py     # AI highlight story generation
│   │   ├── comments.py    # Image comments and AI descriptions
│   │   └── rec.py         # Recommendation engine
│   └── storage/           # Runtime JSON state files
└── vue-project/           # Vue 3 frontend
    ├── src/
    │   ├── App.vue         # Root component (nav, search, dark mode)
    │   ├── api.js          # API client, reactive state, WebSocket helpers
    │   ├── router/         # SPA routes
    │   ├── views/          # Page-level components
    │   └── components/     # Reusable UI components
    └── package.json
```

## Prerequisites

The following must be installed and running before starting:

- **Python 3.10+** with pip
- **Node.js** and **pnpm** (or npm)
- **Stable Diffusion WebUI / Forge** running at `http://127.0.0.1:7860`
- **Ollama** running locally (for chat, tagging, and story features)

## Setup

### Backend

```bash
cd img-api

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
pip install "fastapi[standard]" uvicorn httpx trueskill GPUtil sd_parsers imagehash
```

**Configure paths** — the following files contain hardcoded local paths that must be updated to match your machine:

| File | What to update |
|---|---|
| `routes/scan_images.py` | Output folder paths to scan for new images |
| `routes/webui.py` | Path to your SD WebUI / Forge installation |
| `utils.py` | Path to SD wildcards folder |
| `main.py` | Path to the `vue-project/` folder |

### Frontend

```bash
cd vue-project
pnpm install
```

## Running

### Start the backend

```bash
cd img-api
.venv\Scripts\activate
fastapi dev main.py
```

The backend starts on `http://127.0.0.1:8000`. On startup it will automatically launch the frontend dev server unless the `DISABLE_FRONTEND_AUTOSTART=1` environment variable is set.

### Start the frontend (manual)

```bash
cd vue-project
pnpm run dev      # dev server at http://localhost:5173
pnpm run build    # production build
pnpm run preview  # preview production build
```

## API Overview

The backend exposes a REST + WebSocket API. Key endpoint groups:

| Group | Base path | Description |
|---|---|---|
| Images | `/all-images`, `/image/{id}`, `/search` | Feed, detail, search, like/dislike, trash |
| Generation | (proxied to SD WebUI) | Image generation via Stable Diffusion |
| Models | `/models` | Checkpoint and LoRA browsing |
| Boards | `/board` | Pinboard CRUD |
| Tags | `/tags`, `/autocomplete-tags` | Tag listing and autocomplete |
| Rating | `/rate/pair`, `/rate/result` | TrueSkill head-to-head rating |
| Chat | `/chat/{id}` | Per-image Ollama chat |
| Assistant | `WS /assistant` | AI assistant with tool use |
| Scanning | `WS /ws/scan` | Scan folders for new images |
| Stories | `/stories/generate` | AI story generation |
| Comics | `/comics` | Comics CRUD |
| VRAM | `WS /vram` | Real-time GPU memory usage |

## Data Storage

All application data is stored as JSON files in `img-api/`:

| File | Contents |
|---|---|
| `images.json` | Main image database (metadata, tags, prompts) |
| `likes.json` | Votes and star ratings |
| `ratings.json` | TrueSkill scores |
| `clicks.json` | Click tracking for recommendations |
| `boards.json` | Pinboard data |
| `comments.json` | Image comments and AI descriptions |
| `hashes.json` | Perceptual hashes for similarity search |
| `trash.json` | Trashed image IDs |
| `storage/generationHistory.json` | Generation request history |
