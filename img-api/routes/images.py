from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
import random
import utils
import heapq
import os
from fastapi.responses import StreamingResponse
from PIL import Image
from io import BytesIO
from routes import rec
import re
from collections import defaultdict
from routes import rate
from pathlib import Path
from pydantic import BaseModel
import base64
import uuid
from datetime import datetime
try:
    import numpy as np
except ImportError:
    np = None
router = APIRouter()

# Modified helper: retrieve the original image for similarity computation.
def add_boards_info(copy_img):
    # Use original image data which still contains 'tags_set'
    original = utils.images_data.get(copy_img["Id"], copy_img)
    recommended_boards = []
    for board in utils.boards_data.values():
        pinned_ids = board.get("images", [])
        total_score = 0
        valid_count = 0
        for pid in pinned_ids:
            pinned_image = utils.images_data.get(pid)
            if pinned_image:
                total_score += utils.compute_full_similarity(original, pinned_image)
                valid_count += 1
        avg_score = total_score / valid_count if valid_count else 0
        
        tag_count = 0

        # Incorporate board.tags into the recommendation score
        if board.get("tags"):
            board_tags = [t.strip().lower() for t in board["tags"].split(",") if t.strip()]

            for prompt in original["tags_set"]:
                for tag in board_tags:
                    if tag in prompt:
                        tag_count += 1
                        continue
                

        # Combine the average similarity score with the tag count
        if tag_count > 0:
            combined_score = avg_score + tag_count
        else:
            combined_score = avg_score
        
        recommended_boards.append({
            "id": board["id"],
            "name": board["name"],
            "cover_image": utils.images_data.get(board["images"][0], {}).get("Path") if board.get("images") else None,
            "pin_count": len(pinned_ids),
            "recommendation_score": combined_score,
            "tag_count": tag_count
        })
    recommended_boards.sort(key=lambda x: x["recommendation_score"], reverse=True)
    in_boards = []
    for board in utils.boards_data.values():
        if copy_img["Id"] in board.get("images", []):
            in_boards.append({
                "id": board["id"],
                "name": board["name"],
                "pin_count": len(board.get("images", []))
            })
    copy_img["recommended_boards"] = recommended_boards
    copy_img["in_boards"] = in_boards
    return copy_img

# Helper: predicted-or-actual conservative rating for sorting
def _predicted_or_actual_cr(img) -> float:
    try:
        r = rate.get_rating(img["Id"])
        if not rate.is_unrated(r):
            return rate.conservative_rating(r)
        # unrated -> predict using prompt + pHash
        prompt = img.get("Prompt") or ""
        phash = img.get("pHash") or img.get("phash") or img.get("hash") or ""
        res = rate._predict_from_meta(prompt, phash, top_k=20, alpha=0.6)
        if not res:
            return 0.0
        return float(res.get("predicted_conservative_rating", 0.0))
    except Exception:
        return 0.0


def _get_nsfw_levels(img):
    if not img:
        return None
    levels = img.get("nsfw_levels")
    if not isinstance(levels, dict):
        return None
    return levels


def _nsfw_score(img):
    levels = _get_nsfw_levels(img)
    if not levels:
        return None
    try:
        explicit = float(levels.get("explicit", 0) or 0)
        questionable = float(levels.get("questionable", 0) or 0)
        sensitive = float(levels.get("sensitive", 0) or 0)
        return (explicit * 1.5) + (questionable * 1.0) + (sensitive * 0.5)
    except (TypeError, ValueError):
        return None


def _sfw_score(img):
    levels = _get_nsfw_levels(img)
    if not levels:
        return None
    try:
        return float(levels.get("general", 0) or 0)
    except (TypeError, ValueError):
        return None


def _nsfw_sort_key(img):
    img = img or {}
    score = _nsfw_score(img)
    created = img.get("CreatedDate", 0) or 0
    if score is None:
        return (0, -1.0, created)
    return (1, score, created)


def _sfw_sort_key(img):
    img = img or {}
    score = _sfw_score(img)
    created = img.get("CreatedDate", 0) or 0
    if score is None:
        return (0, -1.0, created)
    return (1, score, created)

def _json_safe(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (set, tuple, list)):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if np:
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating,)):
            return float(value)
        if isinstance(value, (np.ndarray,)):
            return [_json_safe(v) for v in value.tolist()]
    # fallback
    return str(value)

def _sanitize_image_dict(d):
    return _json_safe(d)

@router.get("/image/{image_id}")
def get_image_details(image_id: str):
    # Support "random" as a valid image_id input.
    if image_id.lower() == "random":
        image = random.choice(utils.all_images)
    else:
        try:
            image_id_int = int(image_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid image ID")
        image = utils.images_data.get(image_id_int)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
    
    utils.increment_click(image["Id"])
    copy_img = image.copy()
    copy_img.pop("tags_set", None)
    
    # Track IDs to prevent duplicates
    identical_ids = set()
    variation_ids = set()
    identical_images = []
    variation_images = []
    
    for img in utils.all_images:
        if img["Id"] == image["Id"]:
            continue
        
        if (img.get("Prompt") == "" or image.get("Prompt") == ""):
            continue

        if img.get("Prompt") is None or image.get("Prompt") is None:
            continue

        if img.get("Prompt") == "No prompt found" or image.get("Prompt") == "No prompt found":
            continue

        if (img.get("CFGScale") == image.get("CFGScale") and
            img.get("ModelHash") == image.get("ModelHash") and
            img.get("NegativePrompt") == image.get("NegativePrompt") and
            img.get("Prompt") == image.get("Prompt") and
            img.get("Sampler") == image.get("Sampler") and
            img.get("Steps") == image.get("Steps")):
            copy_candidate = img.copy()
            copy_candidate.pop("tags_set", None)
            if img.get("Seed") == image.get("Seed"):
                # Only add if not already in the list
                if img["Id"] not in identical_ids:
                    identical_images.append(copy_candidate)
                    identical_ids.add(img["Id"])
            else:
                # Only add if not already in the list
                if img["Id"] not in variation_ids:
                    variation_images.append(copy_candidate)
                    variation_ids.add(img["Id"])
                    
    copy_img["identical_images"] = identical_images
    copy_img["variations"] = variation_images
    copy_img = add_boards_info(copy_img)
    return _sanitize_image_dict(copy_img)

@router.get("/image-file/{image_id}")
def get_image_file(image_id: str):

    if not image_id.isdigit():
        raise HTTPException(status_code=400, detail="Invalid image ID format")

    image = utils.images_data.get(int(image_id))
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    file_path = image.get("Path")

    file_path = file_path.replace("/files", utils.api_file_root)

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(file_path)


@router.get("/image-thumbnail/{image_id}")
def get_image_thumbnail(image_id: int, size: int = Query(128)):
    image = utils.images_data.get(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    file_path = image.get("Path")
    if not file_path:
        raise HTTPException(status_code=404, detail="Path not specified")
        
    file_path = file_path.replace("/files", utils.api_file_root)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Original file not found")

    # Setup cache directory
    cache_dir = os.path.join(utils.api_file_root, "thumbnails_cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{image_id}_{size}.jpg")

    if os.path.exists(cache_path):
        return FileResponse(cache_path, media_type="image/jpeg")

    # Generate thumbnail
    try:
        from PIL import Image as PILImage
        img = PILImage.open(file_path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail((size, size))
        img.save(cache_path, "JPEG", quality=85)
        return FileResponse(cache_path, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate thumbnail: {str(e)}")
@router.get("/all-images")
def get_all_images(
    page: int = 1,
    per_page: int = 10,
    sort: str = Query("new", description="Sort order: old, new, top, random, home, predict, nsfw, sfw, most_viewed, least_viewed")
):
    start = (page - 1) * per_page
    end = start + per_page

    if sort == "home":
        recommendations = rec.get_recommended_images()
        # Apply pagination after building the full list
        selected = recommendations[start:end]
    else:
        if sort == "old":
            selected = sorted(utils.all_images, key=lambda x: x.get("CreatedDate", 0))[start:end]
        elif sort == "new":
            selected = sorted(utils.all_images, key=lambda x: x.get("CreatedDate", 0), reverse=True)[start:end]
        elif sort == "top":
            #use conservative rating from rate.pyrate.get_conservative_rating(image_id)
            selected = sorted(utils.all_images, key=lambda x: rate.get_conservative_rating(x["Id"]), reverse=True)[start:end]
        elif sort == "random":
            lst = utils.all_images[:]
            random.shuffle(lst)
            selected = lst[start:end]
        elif sort == "predict":
            # Use a bounded heap to collect only top N = page*per_page by predicted/actual CR
            top_n = max(page * per_page, per_page)
            heap = []  # min-heap of (cr, created, img)
            for img in utils.all_images:
                cr = _predicted_or_actual_cr(img)
                item = (cr, img.get("CreatedDate", 0), img)
                if len(heap) < top_n:
                    heapq.heappush(heap, item)
                else:
                    if item > heap[0]:
                        heapq.heapreplace(heap, item)
            ordered = sorted(heap, reverse=True)
            selected = [img for _, __, img in ordered[start:end]]
        elif sort == "nsfw":
            selected = sorted(utils.all_images, key=_nsfw_sort_key, reverse=True)[start:end]
        elif sort == "sfw":
            selected = sorted(utils.all_images, key=_sfw_sort_key, reverse=True)[start:end]
        elif sort == "most_viewed":
            selected = sorted(
                utils.all_images,
                key=lambda x: (
                    (x.get("Clicks", 0) or 0) + (x.get("Shows", 0) or 0),
                    x.get("CreatedDate", 0) or 0,
                    x.get("Id", 0)
                ),
                reverse=True
            )[start:end]
        elif sort == "least_viewed":
            selected = sorted(
                utils.all_images,
                key=lambda x: (
                    (x.get("Clicks", 0) or 0) + (x.get("Shows", 0) or 0),
                    - (x.get("CreatedDate", 0) or 0),
                    - x.get("Id", 0)
                )
            )[start:end]
        else:
            selected = sorted(utils.all_images, key=lambda x: x.get("CreatedDate", 0), reverse=True)[start:end]

    result = []
    for img in selected:
        # Resolve the original in-memory dictionary to ensure persistent counts are updated
        iid = img.get("Id")
        orig_img = utils.images_data.get(iid)
        
        if orig_img:
            utils.increment_show(iid)
            img["Shows"] = orig_img["Shows"]
            img["last_shown"] = orig_img.get("last_shown")
        else:
            img["Shows"] = img.get("Shows", 0) + 1
            
        copy_img = img.copy()
        copy_img.pop("tags_set", None)
        copy_img = add_boards_info(copy_img)
        result.append(_sanitize_image_dict(copy_img))
    return result

@router.get("/similar-images/{image_id}")
def get_similar_images(image_id: int, page: int = 1, per_page: int = 5, mode: str = Query("full", description="Similarity mode: full, prompt, hash, embedding, clip")):
    target = utils.images_data.get(image_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target image not found")

    if mode in ("embedding", "clip"):
        import siglip_utils
        similar_pairs = siglip_utils.get_similar_images_by_siglip(image_id, top_k=page * per_page)
        
        start = (page - 1) * per_page
        result = []
        for iid, score in similar_pairs[start:]:
            img = utils.images_data.get(iid)
            if not img:
                continue
            utils.increment_show(iid)
            copy_img = img.copy()
            copy_img.pop("tags_set", None)
            copy_img["similarity_score"] = round(score, 3)
            copy_img = add_boards_info(copy_img)
            result.append(_sanitize_image_dict(copy_img))
        return result

    candidates = []
    for img in utils.all_images:
        if img["Id"] == image_id:
            continue

        score = utils.compute_full_similarity(target, img, mode=mode)
        if score > 0:
            candidates.append((score, img))

    top_n = page * per_page
    best_candidates = heapq.nlargest(top_n, candidates, key=lambda x: x[0])

    start = (page - 1) * per_page
    result = []
    for score, img in best_candidates[start:]:
        utils.increment_show(img["Id"])
        copy_img = img.copy()
        copy_img.pop("tags_set", None)
        copy_img["similarity_score"] = round(score, 3)
        copy_img = add_boards_info(copy_img)
        result.append(_sanitize_image_dict(copy_img))
    return result
# Lightweight in-memory search index for faster queries
_SEARCH_INDEX = {
    "built_for_count": 0,
    "word_to_ids": defaultdict(set),
    "id_to_text": {},
    "tags_by_id": {},
    "type_to_ids": defaultdict(set),
    "model_key_to_ids": defaultdict(set),
    "sampler_to_ids": defaultdict(set),
    "steps_to_ids": defaultdict(set),
    "cfg_to_ids": defaultdict(set),
    "likes": {},
    "created": {},
}


def _norm(s):
    # Robust normalization: accept list/tuple/set, Path, numbers, etc.
    if s is None:
        return ""
    if isinstance(s, (list, tuple, set)):
        s = " ".join(str(x) for x in s if x is not None)
    elif isinstance(s, Path):
        s = str(s)
    elif not isinstance(s, str):
        s = str(s)
    return s.strip().lower()


def _tokenize(s):
    return re.findall(r"[a-z0-9]+", _norm(s))


def _ensure_index():
    # Rebuild if size changed or index empty
    count = len(utils.all_images)
    if _SEARCH_INDEX["built_for_count"] == count and _SEARCH_INDEX["id_to_text"]:
        return

    # Reset
    for k in list(_SEARCH_INDEX.keys()):
        if isinstance(_SEARCH_INDEX[k], dict) or isinstance(_SEARCH_INDEX[k], defaultdict):
            _SEARCH_INDEX[k].clear()

    # Build
    for img in utils.all_images:
        try:
            img_id = img["Id"]

            prompt = _norm(img.get("Prompt"))
            raw_tags = img.get("tags_set") or []
            tags = [t for t in (_norm(t) for t in raw_tags) if t]

            text = (prompt + " " + " ".join(tags)).strip().lower()
            _SEARCH_INDEX["id_to_text"][img_id] = text
            _SEARCH_INDEX["tags_by_id"][img_id] = tags

            # Words index
            for tok in set(_tokenize(text)):
                _SEARCH_INDEX["word_to_ids"][tok].add(img_id)

            # File type (extension)
            ext = os.path.splitext(str(img.get("Path", "")))[1].lower().lstrip(".")
            if ext:
                _SEARCH_INDEX["type_to_ids"][ext].add(img_id)
                # Normalize jpg/jpeg to both keys
                if ext == "jpeg":
                    _SEARCH_INDEX["type_to_ids"]["jpg"].add(img_id)
                if ext == "jpg":
                    _SEARCH_INDEX["type_to_ids"]["jpeg"].add(img_id)

            # Model name/hash tokens
            mn = _norm(img.get("ModelName"))
            mh = _norm(img.get("ModelHash"))
            model_tokens = set(_tokenize(mn))
            if mh:
                model_tokens.add(mh)
            for mk in model_tokens:
                if mk:
                    _SEARCH_INDEX["model_key_to_ids"][mk].add(img_id)

            # Sampler (both full string and tokens)
            sampler = _norm(img.get("Sampler"))
            if sampler:
                _SEARCH_INDEX["sampler_to_ids"][sampler].add(img_id)
                for tok in set(_tokenize(sampler)):
                    _SEARCH_INDEX["sampler_to_ids"][tok].add(img_id)

            # Numeric filters as strings
            steps = _norm(img.get("Steps"))
            cfg = _norm(img.get("CFGScale"))
            if steps:
                _SEARCH_INDEX["steps_to_ids"][steps].add(img_id)
            if cfg:
                _SEARCH_INDEX["cfg_to_ids"][cfg].add(img_id)

            # Likes / Created
            try:
                _SEARCH_INDEX["likes"][img_id] = int(img.get("Likes", 0) or 0)
            except Exception:
                _SEARCH_INDEX["likes"][img_id] = 0
            try:
                _SEARCH_INDEX["created"][img_id] = int(img.get("CreatedDate", 0) or 0)
            except Exception:
                _SEARCH_INDEX["created"][img_id] = 0

        except Exception:
            # Skip bad records, continue building the index
            continue

    # Only mark as built after successful pass
    _SEARCH_INDEX["built_for_count"] = count


def _parse_query(q):
    # Extract "quoted phrases" and remaining terms
    phrases = []
    terms = []
    for m in re.finditer(r'"([^"]+)"|(\S+)', q):
        if m.group(1):
            phrases.append(m.group(1).strip().lower())
        else:
            terms.append(m.group(2))

    # Split into advanced and basic
    advanced = {}
    basic_raw = []
    for t in terms:
        if ":" in t:
            k, v = t.split(":", 1)
            advanced[_norm(k)] = _norm(v)
        else:
            basic_raw.append(t)

    basic_tokens = _tokenize(" ".join(basic_raw))
    return phrases, basic_tokens, advanced


@router.get("/search")
def search_images(
    query: str = Query(..., description="Search query"),
    page: int = 1,
    per_page: int = 10,
    sort: str = Query("new", description="Sort order: old, new, top, random, relevance, predict, nsfw, sfw, ai"),
    can_return_empty: bool = Query(False, description="Allow empty results")
):
    _ensure_index()
    phrases, basic_tokens, advanced = _parse_query(query or "")
    candidates = set(_SEARCH_INDEX["id_to_text"].keys())

    def _union_from_keys(index_map, needle):
        needle = _norm(needle)
        out = set()
        for k, ids in index_map.items():
            if needle in k:
                out |= ids
        return out

    # Advanced: type
    if "type" in advanced:
        tset = _SEARCH_INDEX["type_to_ids"].get(advanced["type"], set())
        candidates &= tset
        if not candidates:
            if can_return_empty:
                return []
            raise HTTPException(status_code=404, detail="No images match type filter")

    # Advanced: model
    if "model" in advanced:
        mset = _union_from_keys(_SEARCH_INDEX["model_key_to_ids"], advanced["model"])
        candidates &= mset
        if not candidates:
            if can_return_empty:
                return []
        if not candidates:
            raise HTTPException(status_code=404, detail="No images match model filter")

    # Advanced: sampler
    if "sampler" in advanced:
        sset = _union_from_keys(_SEARCH_INDEX["sampler_to_ids"], advanced["sampler"])
        candidates &= sset
        if not candidates:
            if can_return_empty:
                return []
            raise HTTPException(status_code=404, detail="No images match sampler filter")

    # Advanced: steps
    if "steps" in advanced:
        sset = _SEARCH_INDEX["steps_to_ids"].get(advanced["steps"], set())
        candidates &= sset
        if not candidates:
            if can_return_empty:
                return []
            raise HTTPException(status_code=404, detail="No images match steps filter")

    # Advanced: cfg
    if "cfg" in advanced:
        cset = _SEARCH_INDEX["cfg_to_ids"].get(advanced["cfg"], set())
        candidates &= cset
        if not candidates:
            if can_return_empty:
                return []
            raise HTTPException(status_code=404, detail="No images match cfg filter")

    # Advanced: date (date:yyyy | date:yyyy-mm | date:yyyy-mm-dd)
    if "date" in advanced:
        from datetime import datetime
        import calendar
        date_str = advanced["date"]
        parts = [p for p in date_str.split("-") if p]
        try:
            if len(parts) == 1:
                y = int(parts[0])
                start_dt = datetime(y, 1, 1)
                end_dt = datetime(y, 12, 31, 23, 59, 59, 999999)
            elif len(parts) == 2:
                y = int(parts[0]); m = int(parts[1])
                last = calendar.monthrange(y, m)[1]
                start_dt = datetime(y, m, 1)
                end_dt = datetime(y, m, last, 23, 59, 59, 999999)
            elif len(parts) >= 3:
                y = int(parts[0]); m = int(parts[1]); d = int(parts[2])
                start_dt = datetime(y, m, d)
                end_dt = datetime(y, m, d, 23, 59, 59, 999999)
            else:
                raise ValueError("invalid date")
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid date filter format")

        def _match_date(img_id):
            ticks = _SEARCH_INDEX["created"].get(img_id, 0)
            if not ticks:
                return False
            try:
                dt = utils.ticksToDatetime(int(ticks))
            except Exception:
                return False
            return start_dt <= dt <= end_dt

        candidates = {i for i in candidates if _match_date(i)}
        if not candidates:
            if can_return_empty:
                return []
            raise HTTPException(status_code=404, detail="No images match date filter")

    # Basic token filtering
    if basic_tokens:
        for tok in set(basic_tokens):
            ids = _SEARCH_INDEX["word_to_ids"].get(tok)
            if not ids:
                ids = {i for i in candidates if tok in _SEARCH_INDEX["id_to_text"][i]}
            candidates &= ids
            if not candidates:
                break

    # Phrase filtering
    for ph in phrases:
        candidates = {i for i in candidates if ph in _SEARCH_INDEX["id_to_text"][i]}
        if not candidates:
            break

    if not candidates:
        if can_return_empty:
            return []
        raise HTTPException(status_code=404, detail="No images match your search query")

    ids_list = list(candidates)

    if sort == "old":
        ids_list.sort(key=lambda i: _SEARCH_INDEX["created"].get(i, 0))
    elif sort == "new":
        ids_list.sort(key=lambda i: _SEARCH_INDEX["created"].get(i, 0), reverse=True)
    elif sort == "top":
        liked_images = [img for img in utils.all_images if img.get("Likes", 0) > 0]
        ids_list.sort(
            key=lambda i: (
                utils.images_data.get(i, {}).get("Likes", 0),
                utils.compute_custom_score(utils.images_data.get(i, {}), liked_images, []),
            ),
            reverse=True,
        )
    elif sort == "random":
        random.shuffle(ids_list)
    elif sort == "predict":
        scored = []
        for i in ids_list:
            img = utils.images_data.get(i)
            if not img:
                continue
            cr = _predicted_or_actual_cr(img)
            scored.append((cr, _SEARCH_INDEX["created"].get(i, 0), i))
        scored.sort(reverse=True)
        ids_list = [i for _, __, i in scored]
    elif sort == "nsfw":
        ids_list.sort(key=lambda i: _nsfw_sort_key(utils.images_data.get(i)), reverse=True)
    elif sort == "sfw":
        ids_list.sort(key=lambda i: _sfw_sort_key(utils.images_data.get(i)), reverse=True)
    elif sort == "ai":
        import siglip_utils
        if siglip_utils.siglip_vectors is None or len(siglip_utils.siglip_ids) == 0:
            raise HTTPException(status_code=400, detail="SigLIP embeddings not built yet. Please rebuild embeddings in the Scanner page.")
        try:
            from .ai_search import get_siglip_cpu
            import torch
            model, processor = get_siglip_cpu()
            inputs = processor(text=[query], return_tensors="pt", padding=True)
            with torch.no_grad():
                text_features = model.get_text_features(**inputs)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                q_vec = text_features.cpu().numpy().astype(np.float32)[0]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to embed search query: {str(e)}")
            
        def get_siglip_similarity(cid):
            idx = siglip_utils.siglip_id_to_index.get(cid)
            if idx is not None:
                return float(siglip_utils.siglip_vectors[idx] @ q_vec)
            return 0.0
            
        ids_list.sort(key=get_siglip_similarity, reverse=True)
    else:
        btok_set = set(basic_tokens)
        def rel(i):
            score = 0
            text = _SEARCH_INDEX["id_to_text"][i]
            words_in_text = set(_tokenize(text))
            for tok in btok_set:
                if tok in words_in_text:
                    score += 2
                elif tok in text:
                    score += 1
            tags = _SEARCH_INDEX["tags_by_id"].get(i, [])
            for tok in btok_set:
                if any(tok in t for t in tags):
                    score += 1
            for ph in phrases:
                if ph and ph in text:
                    score += 3
            score += 0.0000001 * _SEARCH_INDEX["created"].get(i, 0)
            return score
        ids_list.sort(key=rel, reverse=True)

    start = max((page - 1) * per_page, 0)
    end = start + per_page
    page_ids = ids_list[start:end]

    result = []
    for img_id in page_ids:
        img = utils.images_data.get(img_id)
        if not img:
            continue
        copy_img = img.copy()
        copy_img.pop("tags_set", None)
        copy_img = add_boards_info(copy_img)
        result.append(_sanitize_image_dict(copy_img))

    return result

@router.post("/like/{image_id}")
def like_image(image_id: int):
    image = utils.images_data.get(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image["Likes"] = image.get("Likes", 0) + 1
    utils.save_votes()
    return {"message": f"Image {image_id} liked", "Likes": image["Likes"]}

@router.post("/rate/{image_id}")
def rate_image(image_id: int, rating: int):
    image = utils.images_data.get(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image["Rating"] = rating
    utils.save_votes()
    return {"message": f"Image {image_id} rated", "Rating": image["Rating"]}

@router.post("/dislike/{image_id}")
def dislike_image(image_id: int):
    image = utils.images_data.get(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image["Dislikes"] = image.get("Dislikes", 0) + 1
    utils.save_votes()
    return {"message": f"Image {image_id} disliked", "Dislikes": image["Dislikes"]}

@router.get("/liked-images")
def get_liked_images(page: int = 1, per_page: int = 10):
    # Filter images with a rating greater than 0, treating None as 0
    rated = [img for img in utils.all_images if (img.get("Rating") or 0) > 0]
    # Sort by highest rating first, then by CreatedDate descending as tiebreaker 
    rated.sort(key=lambda x: ((x.get("Rating") or 0), x.get("CreatedDate", 0)), reverse=True)
    start = (page - 1) * per_page
    end = start + per_page
    response = []
    for img in rated[start:end]:
        copy_img = img.copy()
        copy_img.pop("tags_set", None)
        copy_img = add_boards_info(copy_img)
        response.append(_sanitize_image_dict(copy_img))
    return response

fallback_folders = [
    r"E:\unity\cache\_\ai\stable-diffusion-webui\outputs\deepfake\out",
    r"E:\unity\cache\_\ai\stable-diffusion-webui\outputs\deepfake\out\Saved"
]


@router.get("/random-image")
def get_random_image(user: str = Query(None, description="User name")):
    if not utils.all_images:
        raise HTTPException(status_code=404, detail="No images available")
    img = random.choice(utils.all_images)
    copy_img = img.copy()
    copy_img.pop("tags_set", None)
    copy_img = add_boards_info(copy_img)
    return _sanitize_image_dict(copy_img)

@router.get("/random-image-file")
def get_random_image_file(user: str = Query(None, description="User name")):
    if user is not None:
        if user.lower() == "you":
            return FileResponse(utils.api_file_root + "/automatic/avatar.png", media_type="image/png")
        # Use user parameter as seed for random selection
        random.seed(hash(user))

    if not utils.all_images:
        raise HTTPException(status_code=404, detail="No images available")
    
    # filter out images older than 638032826282616142 CreatedDate
    images = [img for img in utils.all_images.copy() if img.get("CreatedDate", 0) >= 638032826282616142]

    image = random.choice(images)
    image_path = image.get("Path")
    image_path = image_path.replace("/files", utils.api_file_root)
    if not os.path.exists(image_path):
        for folder in fallback_folders:
            fallback_path = os.path.join(folder, os.path.basename(image_path))
            if os.path.exists(fallback_path):
                image_path = fallback_path
                break
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found")
    
    random.seed()  # Reset seed to avoid affecting other random calls
    return FileResponse(image_path, media_type="image/jpeg")

@router.post("/open-image-location/{image_id}")
def open_image_location(image_id: int):
    import subprocess
    import platform

    image = utils.images_data.get(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    file_path = image.get("Path")
    file_path = file_path.replace("/files", utils.api_file_root)

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image file not found")

    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["explorer", "/select,", os.path.normpath(file_path)])
        elif system == "Darwin":  # macOS
            subprocess.run(["open", "-R", file_path])
        else:  # Assume Linux
            subprocess.run(["xdg-open", os.path.dirname(file_path)])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open file location: {str(e)}")

    return {"message": "File location opened successfully"}


# ---------------------------------------------------------------------------
# Trash routes
# ---------------------------------------------------------------------------

import time as _time
from typing import List
from pydantic import BaseModel


class BulkTrashRequest(BaseModel):
    image_ids: List[int]


def _trash_image(image_id: int):
    """Move a single image to trash (in-memory + persist)."""
    image = utils.images_data.get(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    if image_id in utils.trash_data:
        return  # already trashed

    utils.trash_data[image_id] = {"TrashedAt": int(_time.time())}
    # Remove from active list
    try:
        utils.all_images.remove(image)
    except ValueError:
        pass
    utils.save_trash()

class CloudImageRequest(BaseModel):
    image_base64: str
    prompt: str = ""
    negative_prompt: str = ""
    sampler: str = ""
    cfg_scale: float = 7.0
    steps: int = 30
    seed: int = -1
    width: int = 512
    height: int = 512
    model_name: str = ""
    model_hash: str = ""

@router.post("/save-cloud")
def save_cloud_image(req: CloudImageRequest):
    utils.ensure_loaded()
    
    # Decode image
    image_base64_data = req.image_base64.split(",")[1] if "," in req.image_base64 else req.image_base64
    image_data = base64.b64decode(image_base64_data)
    
    # Generate filename and folder
    today_str = datetime.now().strftime("%Y-%m-%d")
    folder_path = os.path.join(utils.api_file_root, "automatic", "cloud", today_str)
    os.makedirs(folder_path, exist_ok=True)
    
    file_name = f"{uuid.uuid4().hex}.png"
    file_path = os.path.join(folder_path, file_name)
    
    # Save the file
    with open(file_path, "wb") as f:
        f.write(image_data)
        
    # Generate new ID
    new_id = 0
    if utils.all_images:
        new_id = max(img.get("Id", 0) for img in utils.all_images) + 1
    else:
        new_id = 1
        
    phash = utils.compute_phash(file_path)
    
    new_img = {
        "Id": new_id,
        "Path": f"/files/automatic/cloud/{today_str}/{file_name}",
        "CreatedDate": utils.datetimeToTicks(datetime.now()),
        "Prompt": req.prompt,
        "NegativePrompt": req.negative_prompt,
        "Sampler": req.sampler,
        "CFGScale": req.cfg_scale,
        "Steps": req.steps,
        "Seed": req.seed,
        "Width": req.width,
        "Height": req.height,
        "ModelName": req.model_name,
        "ModelHash": req.model_hash,
        "Likes": 0,
        "Dislikes": 0,
        "Rating": 0,
        "Clicks": 0,
        "tags_set": {tag.strip().lower() for tag in req.prompt.split(",") if tag.strip()}
    }
    
    if phash:
        new_img["pHash"] = phash
        
    utils.raw_all_images.append(new_img.copy())
    utils.all_images.append(new_img)
    utils.images_data[new_id] = new_img
    
    utils.save_images()
    
    safe_img = new_img.copy()
    safe_img.pop("tags_set", None)
    return _sanitize_image_dict(safe_img)


@router.post("/delete/{image_id}")
def delete_image(image_id: int):
    """Move an image to the trash."""
    _trash_image(image_id)
    return {"message": f"Image {image_id} moved to trash"}


@router.post("/trash/bulk")
def bulk_trash_images(body: BulkTrashRequest):
    """Move multiple images to the trash at once."""
    trashed = []
    not_found = []
    for image_id in body.image_ids:
        if not utils.images_data.get(image_id):
            not_found.append(image_id)
            continue
        _trash_image(image_id)
        trashed.append(image_id)
    return {"trashed": trashed, "not_found": not_found}


@router.get("/trash")
def get_trash(page: int = 1, per_page: int = 60):
    """List all images currently in the trash."""
    trashed_ids = list(utils.trash_data.keys())
    # Sort by trashed date, newest first
    trashed_ids.sort(key=lambda i: utils.trash_data[i].get("TrashedAt", 0), reverse=True)
    start = (page - 1) * per_page
    end = start + per_page
    result = []
    for img_id in trashed_ids[start:end]:
        img = utils.images_data.get(img_id)
        if not img:
            continue
        copy_img = img.copy()
        copy_img.pop("tags_set", None)
        copy_img["TrashedAt"] = utils.trash_data[img_id].get("TrashedAt")
        result.append(_sanitize_image_dict(copy_img))
    return {"items": result, "total": len(trashed_ids), "page": page, "per_page": per_page}


@router.post("/trash/restore/{image_id}")
def restore_image(image_id: int):
    """Restore an image from the trash back to the active collection."""
    if image_id not in utils.trash_data:
        raise HTTPException(status_code=404, detail="Image not in trash")
    image = utils.images_data.get(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    del utils.trash_data[image_id]
    # Add back to active list
    utils.all_images.append(image)
    utils.save_trash()
    return {"message": f"Image {image_id} restored"}


@router.post("/trash/empty")
def empty_trash():
    """Permanently delete all images in the trash."""
    deleted = []
    errors = []
    ids_to_delete = list(utils.trash_data.keys())
    for image_id in ids_to_delete:
        try:
            image = utils.images_data.get(image_id)
            if image:
                file_path = image.get("Path", "")
                if file_path:
                    file_path = file_path.replace("/files", utils.api_file_root)
                    if os.path.exists(file_path):
                        print(f"Deleting file: {file_path}")
                        os.remove(file_path)
            # Remove from all data structures
            utils.images_data.pop(image_id, None)
            del utils.trash_data[image_id]
            # Remove from raw_all_images
            utils.raw_all_images[:] = [
                img for img in utils.raw_all_images if img.get("Id") != image_id
            ]
            deleted.append(image_id)
        except Exception as e:
            errors.append({"id": image_id, "error": str(e)})
    utils.save_images()
    utils.save_trash()
    return {"deleted": deleted, "errors": errors}