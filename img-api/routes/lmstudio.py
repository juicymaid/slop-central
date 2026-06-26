"""
LM Studio API routes — model listing and status.
"""
from fastapi import APIRouter
import httpx

router = APIRouter()

LM_STUDIO_BASE = "http://127.0.0.1:1234"


@router.get("/lmstudio/models")
async def get_lmstudio_models():
    """Return list of model IDs available in LM Studio (loaded + unloaded)."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{LM_STUDIO_BASE}/api/v1/models")
            if resp.status_code == 200:
                data = resp.json()
                models = data.get("models", []) or data.get("data", []) or []
                # Return just the model keys/ids for use in dropdowns
                return [m.get("id") or m.get("key") or m.get("model_id") for m in models if m.get("id") or m.get("key") or m.get("model_id")]
    except Exception as e:
        print(f"[LMStudio] Failed to fetch models: {e}")

    # Fallback: try OpenAI-compat endpoint
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{LM_STUDIO_BASE}/v1/models")
            if resp.status_code == 200:
                data = resp.json()
                models = data.get("data", []) or []
                return [m.get("id") for m in models if m.get("id")]
    except Exception as e:
        print(f"[LMStudio] Failed to fetch models (v1/models): {e}")

    return []


@router.get("/lmstudio/loaded-models")
async def get_lmstudio_loaded_models():
    """Return list of currently loaded model instances in LM Studio."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{LM_STUDIO_BASE}/api/v1/models")
            if resp.status_code == 200:
                data = resp.json()
                models = data.get("models", []) or []
                loaded = []
                for m in models:
                    if m.get("loaded_instances"):
                        loaded.append({
                            "id": m.get("id") or m.get("key"),
                            "instances": m.get("loaded_instances"),
                        })
                return loaded
    except Exception as e:
        print(f"[LMStudio] Failed to fetch loaded models: {e}")
    return []
