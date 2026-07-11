from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
import utils
import math
import ollama
import siglip_utils
import numpy as np
import torch
import threading
from .images import add_boards_info

router = APIRouter()

def _cosine(a, na, b, nb):
    # a·b / (|a||b|)
    return sum(x*y for x, y in zip(a, b)) / (na * nb + 1e-12)

@router.post("/ai-search/rebuild")
def ai_search_rebuild(model: str = Query("nomic-embed-text"), force: bool = Query(False)):
    utils.load_images()
    result = utils.build_image_embeddings(model_name=model, force=force)
    return result

@router.get("/ai-search")
def ai_search(
    query: str = Query(..., description="Natural language or tag-style query"),
    model: str = Query("qwen3-embedding:4b"),
    top_k: int = Query(20, ge=1, le=200)
):
    utils.load_images()
    utils.load_embeddings()
    if not utils.image_embeddings:
        raise HTTPException(status_code=400, detail="Embeddings not built yet. POST /ai-search/rebuild first.")
    # Embed query
    q_resp = ollama.embeddings(model=model, prompt=query)
    q_vec = q_resp.get("embedding")
    if not q_vec:
        raise HTTPException(status_code=500, detail="Failed to embed query")
    q_norm = (sum(x*x for x in q_vec)) ** 0.5

    # Score all
    scored = []
    for img_id, rec in utils.image_embeddings.items():
        vec = rec["vec"]
        norm = rec["norm"]
        sim = _cosine(q_vec, q_norm, vec, norm)
        scored.append((sim, img_id))
    scored.sort(key=lambda x: x[0], reverse=True)
    page = scored[:top_k]

    results = []
    for sim, iid in page:
        img = utils.images_data.get(iid)
        if not img:
            continue
        copy_img = img.copy()
        copy_img.pop("tags_set", None)
        copy_img["semantic_score"] = round(sim, 4)
        copy_img = add_boards_info(copy_img)
        results.append(copy_img)
    return results

@router.post("/ai-search/rebuild-siglip")
def ai_search_rebuild_siglip(background_tasks: BackgroundTasks, force: bool = Query(False)):
    return siglip_utils.start_siglip_indexing(force=force, background_tasks=background_tasks)

@router.get("/ai-search/siglip-status")
def ai_search_siglip_status():
    return siglip_utils.siglip_indexing_status

_siglip_model_cpu = None
_siglip_processor_cpu = None
_siglip_lock = threading.Lock()

def get_siglip_cpu():
    global _siglip_model_cpu, _siglip_processor_cpu
    with _siglip_lock:
        if _siglip_model_cpu is None:
            from transformers import AutoProcessor, AutoModel
            _siglip_processor_cpu = AutoProcessor.from_pretrained("google/siglip2-base-patch16-224")
            _siglip_model_cpu = AutoModel.from_pretrained("google/siglip2-base-patch16-224").to("cpu")
        return _siglip_model_cpu, _siglip_processor_cpu

@router.get("/ai-search/siglip-search")
def siglip_search(
    query: str = Query(..., description="Natural language semantic image search"),
    top_k: int = Query(20, ge=1, le=200)
):
    utils.load_images()
    if siglip_utils.siglip_vectors is None or len(siglip_utils.siglip_ids) == 0:
        raise HTTPException(status_code=400, detail="SigLIP embeddings not built yet. POST /ai-search/rebuild-siglip first.")
        
    try:
        model, processor = get_siglip_cpu()
        inputs = processor(text=[query], return_tensors="pt", padding=True)
        with torch.no_grad():
            text_features = model.get_text_features(**inputs)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            q_vec = text_features.cpu().numpy().astype(np.float32)[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to embed query: {str(e)}")

    # Calculate similarities (dot product since vectors are normalized)
    similarities = siglip_utils.siglip_vectors @ q_vec
    
    # Sort
    sorted_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in sorted_indices:
        iid = siglip_utils.siglip_ids[idx]
        img = utils.images_data.get(iid)
        if not img:
            continue
        copy_img = img.copy()
        copy_img.pop("tags_set", None)
        copy_img["semantic_score"] = round(float(similarities[idx]), 4)
        copy_img = add_boards_info(copy_img)
        results.append(copy_img)
        
    return results

@router.post("/ai-search/rebuild-siglip-map")
def ai_search_rebuild_siglip_map(background_tasks: BackgroundTasks):
    siglip_utils.load_siglip_embeddings()
    if siglip_utils.siglip_vectors is None or len(siglip_utils.siglip_ids) == 0:
        raise HTTPException(status_code=400, detail="SigLIP embeddings not built yet. POST /ai-search/rebuild-siglip first.")
    background_tasks.add_task(siglip_utils.rebuild_siglip_2d_coords)
    return {"status": "started", "message": "UMAP dimensionality reduction started in the background."}

@router.get("/ai-search/siglip-map")
def get_siglip_map():
    import os
    import json
    utils.load_images()
    coords_path = "siglip_2d_coords.json"
    if not os.path.exists(coords_path):
        siglip_utils.load_siglip_embeddings()
        if siglip_utils.siglip_vectors is not None and len(siglip_utils.siglip_ids) > 0:
            # Rebuild on the fly synchronously if missing
            siglip_utils.rebuild_siglip_2d_coords()
        else:
            raise HTTPException(status_code=400, detail="SigLIP embeddings not built yet. POST /ai-search/rebuild-siglip first.")
            
    try:
        with open(coords_path, "r", encoding="utf-8") as f:
            coords_map = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read coordinates: {e}")
        
    result = []
    for iid_str, coord in coords_map.items():
        iid = int(iid_str)
        img = utils.images_data.get(iid)
        if not img:
            continue
        result.append({
            "id": iid,
            "path": img.get("Path", ""),
            "name": img.get("FileName", ""),
            "x": coord[0],
            "y": coord[1],
            "rating": img.get("Rating") or 0,
            "likes": img.get("Likes", 0),
            "prompt": img.get("Prompt") or img.get("prompt") or ""
        })
    return result