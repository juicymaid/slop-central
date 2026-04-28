import json
import os
import random
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from routes import images, rec, tags, boards, phashes, scan_images, scoring, tagger, models, comments, webui, chats, rate, comics, ai_search, stories, assistant
from fastapi.staticfiles import StaticFiles
from utils import (
    images_data, all_images, clicks_data, boards_data,
    IMAGES_FILE, LIKES_FILE, CLICKS_FILE, BOARDS_FILE
)
from fastapi import UploadFile
import requests
from fastapi import Request
from fastapi.responses import Response
from uvicorn import run
import multiprocessing
import asyncio
from fastapi import WebSocket, WebSocketDisconnect

import utils
import subprocess

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.mount("/files", StaticFiles(directory=os.path.abspath("files"), follow_symlink=True), name="files")

@app.get("/")
def read_root():
    #return index.html from current directory
    return FileResponse("index.html")

@app.post("/save-file") 
def save_file(file: UploadFile, filename: str = Query(..., description="Name of the file to save")):
    file_path = os.path.join("storage", filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return {"filename": filename, "message": "File saved successfully"}

@app.get("/storage-files/{filename}")
def get_storage_file(filename: str):
    file_path = os.path.join("storage", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

@app.websocket("/vram")
async def vram_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        # Optionally receive a one-time config from client
        # msg = await websocket.receive_text()
        while True:
            data = utils.get_vram_usage()
            await websocket.send_json(data)
            await asyncio.sleep(1.0)  # adjust push interval if needed
    except WebSocketDisconnect:
        pass
    except Exception as e:
        # ensure socket closes cleanly on unexpected errors
        try:
            await websocket.close()
        except Exception:
            pass

print("routes")
app.include_router(images.router)
app.include_router(tags.router)
app.include_router(boards.router)
app.include_router(phashes.router)
app.include_router(scoring.router)
app.include_router(scan_images.router)
app.include_router(tagger.router)
app.include_router(models.router)
app.include_router(comments.router)
app.include_router(webui.router)
app.include_router(chats.router)
app.include_router(rate.router)
app.include_router(comics.router)
app.include_router(ai_search.router)
app.include_router(stories.router)
app.include_router(utils.router)
# Assistant routes (includes WS /assistant)
app.include_router(assistant.router)
print("routes loaded")



FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")  # change if your dev server uses a different port
FRONTEND_DIR = os.getenv(
    "FRONTEND_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "vue-project")),
)

def ensure_frontend_running():
    # Skip if an env flag disables autostart
    if os.getenv("DISABLE_FRONTEND_AUTOSTART") == "1":
        print("Frontend autostart disabled via env.")
        return

    try:
        r = requests.get(FRONTEND_URL, timeout=0.5)
        if r.status_code < 500:
            print(f"Frontend already running at {FRONTEND_URL}")
            return
    except Exception:
        pass

    print("Starting frontend...")

    DETACHED_PROCESS = 0x00000008

    if not os.path.isdir(FRONTEND_DIR):
        print(f"Frontend directory not found: {FRONTEND_DIR}")
        return

    # run npm run dev
    subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
        shell=True,
        creationflags=DETACHED_PROCESS,
    )


@app.on_event("startup")
async def _startup_init():
    # Start loading the heavy JSON data in the background so the server can accept connections immediately.
    try:
        utils.ensure_loaded(block=False)
    except Exception as e:
        print(f"Failed to start background data load: {e}")

    # Start frontend autostart in background so it never blocks API startup.
    if os.getenv("DISABLE_FRONTEND_AUTOSTART") != "1":
        import threading
        threading.Thread(target=ensure_frontend_running, daemon=True).start()


@app.middleware("http")
async def _ensure_data_loaded(request: Request, call_next):
    # Skip endpoints that don't need image DB.
    path = request.url.path
    if (
        path == "/"
        or path.startswith("/files")
        or path.startswith("/storage-files")
        or path.startswith("/save-file")
        or path.startswith("/proxy")
        or path.startswith("/docs")
        or path.startswith("/openapi.json")
        or path.startswith("/redoc")
        or path.startswith("/status")
    ):
        return await call_next(request)

    # If a request hits before background load finishes, load (blocking) but off the event loop.
    try:
        await asyncio.to_thread(utils.ensure_loaded)
    except Exception as e:
        return Response(
            content=json.dumps({"error": "data_load_failed", "detail": str(e)}),
            media_type="application/json",
            status_code=500,
        )

    return await call_next(request)

@app.get("/proxy")
def proxy(url: str = Query(..., description="URL to proxy")):
    try:
        response = requests.get(url)
        return Response(content=response.content, media_type=response.headers.get('Content-Type', 'application/octet-stream'))
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

