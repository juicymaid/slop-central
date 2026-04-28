import json
from fastapi import APIRouter, HTTPException, Query
import random
import re
from typing import Any, Dict, List, Optional
import utils
from .images import add_boards_info
import os

router = APIRouter()

# Static model definitions as fallback
default_models = {}

model_cache: Optional[Dict[str, Dict[str, Any]]] = None

def load_models() -> Dict[str, Dict[str, Any]]:
    """Load models dynamically from image data"""

    global model_cache
    if model_cache is not None:
        return model_cache

    # Ensure images are loaded
    try:
        utils.load_images()
    except Exception:
        pass

    models: Dict[str, Dict[str, Any]] = {}
    images = utils.images_data

    for image in images.values():
        hash = image.get("ModelHash")
        if not hash:
            continue

        if hash not in models:
            models[hash] = {
                "Name": image.get("Model"),
                "Images": []
            }

        # prefer first non-empty model name
        if models[hash]["Name"] is None and image.get("Model"):
            models[hash]["Name"] = image.get("Model")

        models[hash]["Images"].append(image)

    model_cache = models

    return models if models else default_models

#lora cache
lora_cache: Optional[Dict[str, Dict[str, Any]]] = None


def load_loras() -> Dict[str, Dict[str, Any]]:
    """Load LoRAs dynamically from image data.
    LoRA is identified by tags like <lora:loraname:weight> within the prompt."""

    global lora_cache
    if lora_cache is not None:
        return lora_cache


    # Ensure images are loaded
    try:
        utils.load_images()
    except Exception:
        pass

    loras: Dict[str, Dict[str, Any]] = {}
    images = utils.images_data

    # regex to match <lora:name> or <lora:name:weight>
    pattern = re.compile(r"<\s*lora:([^:>]+)(?::[^>]+)?>", re.IGNORECASE)

    for image in images.values():
        prompt: str = image.get("Prompt") or ""
        if not prompt:
            continue

        # collect unique lora names per image to avoid double counting the same image
        names = set(m.group(1).strip() for m in pattern.finditer(prompt))
        for name in names:
            key = f"lora:{name}"
            if key not in loras:
                loras[key] = {
                    "Name": name,  # keep consistent with lookup in get_model_images
                    "hash": key,
                    "Images": []
                }
            loras[key]["Images"].append(image)
    lora_cache = loras
    return loras

# helpers
def _latest_date(images: List[Dict[str, Any]]) -> int:
    return max((img.get("CreatedDate") or 0) for img in images) if images else 0

def _select_cover_images(images: List[Dict[str, Any]], limit: int = 15) -> List[str]:
    if not images:
        return []
    if len(images) <= limit:
        return [img.get("Path") for img in images if img.get("Path")]
    return [img.get("Path") for img in random.sample(images, limit) if img.get("Path")]

@router.get("/models")
def get_models(
    sort: str = Query("name", description="Sort options: name, most_images, last_used"),
    type: str = Query("all", description="Type options: all, checkpoint, lora"),
):
    """API endpoint to get models (checkpoint and/or lora) with random cover images"""
    t = (type or "all").lower()
    allowed_types = {"all", "checkpoint", "lora"}
    if t not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid type. Must be one of: all, checkpoint, lora")

    models_list: List[Dict[str, Any]] = []

    if t in ("all", "checkpoint"):
        loaded_models = load_models()
        for hash, model_data in loaded_models.items():
            images = model_data.get("Images", [])
            models_list.append({
                "hash": hash,
                "name": model_data.get("Name") or hash,
                "type": "checkpoint",
                "image_count": len(images),
                "cover_images": _select_cover_images(images),
                "latest_date": _latest_date(images),
            })

    if t in ("all", "lora"):
        loaded_loras = load_loras()
        for lora in loaded_loras.values():
            images = lora.get("Images", [])
            models_list.append({
                "hash": lora["hash"],
                "name": lora["Name"],
                "type": "lora",
                "image_count": len(images),
                "cover_images": _select_cover_images(images),
                "latest_date": _latest_date(images),
            })

    # Sort the models based on the requested sort method
    if sort == "most_images":
        models_list.sort(key=lambda x: x["image_count"], reverse=True)
    elif sort == "last_used":
        models_list.sort(key=lambda x: x["latest_date"], reverse=True)
    else:  # Default to sorting by name
        models_list.sort(key=lambda x: (x["name"] or "").lower())

    # Remove the temporary latest_date field from the response
    for model in models_list:
        model.pop("latest_date", None)

    return models_list

@router.get("/models/{model_hash}")
def get_model_images(
    model_hash: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    sort: str = Query("new", description="Sort order: old, new, top, random")
):
    """API endpoint to get paginated images for a specific model"""
    utils.load_images()  # Ensure images are loaded

    model_images: List[Dict[str, Any]] = []

    is_lora = "lora:" in model_hash

    if is_lora:
        # find all images that have <lora:name:...> in their prompt
        needle = f"<{model_hash}:"
        for image in utils.all_images:
            prompt = image.get("Prompt") or ""
            if needle in prompt:
                model_images.append(image)
    else:
        loaded_models = load_models()
        if model_hash not in loaded_models:
            raise HTTPException(status_code=404, detail="Model not found")
        model_images = loaded_models[model_hash].get("Images", [])

    # Remove duplicate images based on Id
    seen_ids = set()
    unique_images: List[Dict[str, Any]] = []
    for img in model_images:
        img_id = img.get("Id")
        if img_id is None or img_id in seen_ids:
            continue
        seen_ids.add(img_id)
        unique_images.append(img)
    model_images = unique_images

    # Sort images based on the requested sort method
    if sort == "old":
        sorted_images = sorted(model_images, key=lambda x: x.get("CreatedDate") or 0)
    elif sort == "new":
        sorted_images = sorted(model_images, key=lambda x: x.get("CreatedDate") or 0, reverse=True)
    elif sort == "top":
        sorted_images = sorted(model_images, key=lambda x: x.get("Likes") or 0, reverse=True)
    elif sort == "random":
        sorted_images = model_images.copy()
        random.shuffle(sorted_images)
    else:
        sorted_images = sorted(model_images, key=lambda x: x.get("CreatedDate") or 0, reverse=True)

    # Calculate pagination
    start = (page - 1) * per_page
    end = start + per_page
    paginated_images = sorted_images[start:end]

    # Remove internal tags_set from response and add boards info
    result: List[Dict[str, Any]] = []
    for img in paginated_images:
        img_copy = img.copy()
        img_copy.pop("tags_set", None)
        img_copy = add_boards_info(img_copy)
        result.append(img_copy)

    name: Optional[str] = model_hash
    if not is_lora:
        # fall back to hash if name missing
        loaded_models = loaded_models if "loaded_models" in locals() else load_models()
        name = loaded_models.get(model_hash, {}).get("Name") or model_hash

    return {
        "name": name,
        "hash": model_hash,
        "total": len(model_images),
        "page": page,
        "per_page": per_page,
        "total_pages": (len(model_images) + per_page - 1) // per_page,
        "images": result
    }
    start = (page - 1) * per_page
    end = start + per_page
    paginated_images = sorted_images[start:end]
    
    # Remove internal tags_set from response
    result = []
    for img in paginated_images:
        img_copy = img.copy()
        img_copy.pop("tags_set", None)
        img_copy = add_boards_info(img_copy)
        result.append(img_copy)
    
    # Return paginated response

    name = model_hash

    if not is_lora:
        name = loaded_models[model_hash]["Name"]

    return {
        "name": name,
        "hash": model_hash,
        "total": len(model_images),
        "page": page,
        "per_page": per_page,
        "total_pages": (len(model_images) + per_page - 1) // per_page,
        "images": result
    }


@router.get("/model-metadata/")
def get_model_metadata(path: str):

    metadataPath = path.replace(".safetensors", ".civitai.info").replace(".ckpt", ".civitai.info")

    # Load metadata from file
    if not os.path.isfile(metadataPath):
        raise HTTPException(status_code=404, detail="Metadata file not found")
    
    with open(metadataPath, "r") as f:
        metadata = f.read()

    return json.loads(metadata)