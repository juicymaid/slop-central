from fastapi import APIRouter, Query
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
        