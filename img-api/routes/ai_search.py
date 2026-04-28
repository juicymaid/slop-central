from fastapi import APIRouter, Query, HTTPException
import utils
import math
import ollama
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