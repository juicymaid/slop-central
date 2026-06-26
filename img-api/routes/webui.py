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


from fastapi import Request
from fastapi.responses import StreamingResponse
import httpx

@router.api_route("/sdapi/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def proxy_sdapi(path: str, request: Request):
    # 1. If generating images (txt2img or img2img), unload LM Studio models only if manage_vram is enabled
    is_generation = path in ("v1/txt2img", "v1/img2img")
    if is_generation:
        from routes.ai_settings import load_ai_settings
        _settings = load_ai_settings()
        if _settings.manage_vram:
            print(f"[VRAM] Image generation request detected ({path}). Triggering LM Studio model unload...")
            utils.unload_lm_studio_models_sync()
        else:
            print(f"[VRAM] Image generation request detected ({path}). manage_vram=False — skipping unload.")
        
        # Log that we are about to run SD WebUI generation
        try:
            async with httpx.AsyncClient() as client:
                opt_resp = await client.get(url.rstrip("/") + "/sdapi/v1/options", timeout=3)
                if opt_resp.status_code == 200:
                    current_sd_model = opt_resp.json().get("sd_model_checkpoint", "Unknown")
                    print(f"[VRAM] Stable Diffusion WebUI generating image using model: {current_sd_model}")
        except Exception:
            pass

    # 2. Forward the request to the real SD WebUI
    sd_url = url.rstrip("/") + "/sdapi/" + path
    
    query_params = request.query_params
    headers = dict(request.headers)
    headers.pop("host", None)
    
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        try:
            req = client.build_request(
                method=request.method,
                url=sd_url,
                params=query_params,
                headers=headers,
                content=body,
                timeout=None  # Generation can take a long time
            )
            resp = await client.send(req, stream=True)
            
            return StreamingResponse(
                resp.aiter_bytes(),
                status_code=resp.status_code,
                headers=dict(resp.headers)
            )
        except Exception as e:
            print(f"[VRAM] Error proxying to SD WebUI: {e}")
            return JSONResponse({"error": f"SD Proxy error: {str(e)}"}, status_code=500)