from fastapi import APIRouter, Query
from fastapi.responses import FileResponse, JSONResponse
import json
import random
import utils  # changed from "from .. import utils"
import subprocess

router = APIRouter()

webui_process = None

webui_start_bat_folder = "H:/ent/ai/StabilityMatrix/Packages/forge/"
webui_start_bat = webui_start_bat_folder + "run.bat"

@router.post("/webui/start")
def start_webui():
    global webui_process

    if webui_process and webui_process.poll() is None:
        return {"message": "Web UI is already running"}

    DETACHED_PROCESS = 0x00000008

    # Start the web UI process using cmd.exe to ensure the batch file runs correctly
    webui_process = subprocess.Popen(
        webui_start_bat, cwd=webui_start_bat_folder,
        creationflags=DETACHED_PROCESS,
    )
    return {"message": "Web UI started"}

url = "http://127.0.0.1:7860/"

@router.get("/webui/status")
def get_webui_status():
    is_running = webui_process is not None and webui_process.poll() is None
    return {"is_running": is_running, "url": url}

@router.post("/webui/unload_models")
async def unload_models():
    # post to /sdapi/v1/unload-checkpoint
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(url + "sdapi/v1/unload-checkpoint")
        if response.status_code == 200:
            return {"message": "Models unloaded successfully"}
        else:
            return {"message": "Failed to unload models", "status_code": response.status_code}



loras_folder = "H:\\ent\\ai\\StabilityMatrix\\Packages\\Backup\\models\\Lora"
models_folder = "H:\\ent\\ai\\StabilityMatrix\\Packages\\Backup\\models\\Stable-diffusion"

import os
@router.get("/webui/loras")
def get_loras():
    loras = []

    # Get all .safetensors files in the loras_folder recursively

    for root, dirs, files in os.walk(loras_folder):
        for file in files:
            if file.endswith(".safetensors"):
                lora_path = os.path.join(root, file)
                lora_name = os.path.splitext(file)[0]

                lora_config_path = lora_path.replace(".safetensors", ".json")
                lora_config = {}
                if os.path.exists(lora_config_path):
                    with open(lora_config_path, "r") as f:
                        lora_config = json.load(f)
                        
                civitai_data_path = lora_path.replace(".safetensors", ".civitai.info")
                civitai_data = {}
                if os.path.exists(civitai_data_path):
                    with open(civitai_data_path, "r") as f:
                        civitai_data = json.load(f)

                loras.append({"name": lora_name, "path": lora_path, "config": lora_config, "civitai": civitai_data})

    return loras

@router.get("/webui/model-image")
def get_model_image(model_path: str = Query(...)):
    """Return the model preview image as a file response (PNG)."""
    image_path = model_path.replace(".safetensors", ".png")

    if not os.path.exists(image_path):
        image_path = model_path.replace(".safetensors", ".preview.png")

    if os.path.exists(image_path):
        return FileResponse(image_path, media_type="image/png")
    #return FileResponse("files/placeholder.png", media_type="image/png")
    return JSONResponse({"error": "Image not found"}, status_code=404)