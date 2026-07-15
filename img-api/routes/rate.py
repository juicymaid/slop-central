from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import random
import utils
import trueskill
import json
from pathlib import Path
from typing import Dict
import time
from typing import Optional
import math
import threading
import heapq

router = APIRouter()

# TrueSkill environment (you can tweak these params if needed)
env = trueskill.TrueSkill(draw_probability=0.0)  # no ties in your case

# In-memory ratings store (replace with DB later)
# Store Rating objects instead of floats
ratings: Dict[int, trueskill.Rating] = {}

# ---------- Fast caches for prediction ----------
_CACHE_LOCK = threading.RLock()
_META_CACHE: dict[int, tuple[set[str], int, int]] = {}  # image_id -> (tokens, phash_int, phash_bits)
_TOKEN_INDEX: dict[str, set[int]] = {}                  # token -> set(image_id)
_RATED_IDS: set[int] = set()                            # ids with rating not "unrated"
_MEAN_CR: float = 0.0                                   # cached mean conservative rating over rated ids

# Tunables for large datasets
_MAX_CANDIDATES = 5000        # cap candidate comparisons per query
_TIME_BUDGET_MS = 150         # soft time budget for similarity loop

def _ensure_images_loaded():
    try:
        if not getattr(utils, "images_data", None):
            utils.load_images()
    except Exception:
        pass

def _phash_to_int_bits(h: str) -> tuple[int, int]:
    if not h:
        return (0, 0)
    try:
        return (int(h, 16), len(h) * 4)
    except Exception:
        return (0, 0)

def _get_prompt_phash(image_id: int) -> tuple[str, str]:
    images = getattr(utils, "images_data", {}) or {}
    img = images.get(image_id) or {}
    prompt = img.get("Prompt") or img.get("prompt") or ""
    phash = img.get("pHash") or img.get("phash") or img.get("hash") or ""
    return str(prompt), str(phash)

def _index_tokens(image_id: int, tokens: set[str]) -> None:
    for t in tokens:
        _TOKEN_INDEX.setdefault(t, set()).add(image_id)

def _deindex_tokens(image_id: int, tokens: set[str]) -> None:
    for t in tokens:
        s = _TOKEN_INDEX.get(t)
        if s:
            s.discard(image_id)
            if not s:
                _TOKEN_INDEX.pop(t, None)

def _ensure_meta_cached(image_id: int) -> tuple[set[str], int, int]:
    with _CACHE_LOCK:
        cached = _META_CACHE.get(image_id)
        if cached:
            return cached
        # Build cache
        prompt, phash = _get_prompt_phash(image_id)
        tokens = _tokenize(prompt)
        ph_int, ph_bits = _phash_to_int_bits(phash)
        _META_CACHE[image_id] = (tokens, ph_int, ph_bits)
        _index_tokens(image_id, tokens)
        return _META_CACHE[image_id]

def _remove_meta(image_id: int) -> None:
    with _CACHE_LOCK:
        cached = _META_CACHE.pop(image_id, None)
        if cached:
            tokens, _, _ = cached
            _deindex_tokens(image_id, tokens)

def _recompute_rated_cache() -> None:
    global _RATED_IDS, _MEAN_CR
    with _CACHE_LOCK:
        rated_ids: list[int] = []
        total_cr = 0.0
        for i, r in ratings.items():
            cr = r.mu - 3 * r.sigma  # inline conservative_rating
            if cr > 0.01:            # same threshold as is_unrated
                rated_ids.append(i)
                total_cr += cr
        _RATED_IDS = set(rated_ids)
        _MEAN_CR = (total_cr / len(rated_ids)) if rated_ids else 0.0

def _on_rating_changed(image_id: int) -> None:
    # Keep rated set, mean and meta index in sync
    r = ratings.get(image_id)
    with _CACHE_LOCK:
        was_rated = image_id in _RATED_IDS
        now_rated = (r is not None) and (not is_unrated(r))
        if now_rated and not was_rated:
            _RATED_IDS.add(image_id)
            # lazily ensure meta on demand; avoid full prewarm
        elif was_rated and not now_rated:
            _RATED_IDS.discard(image_id)
            _remove_meta(image_id)
        # Recompute mean cheaply (full recompute for correctness/simplicity)
        _recompute_rated_cache()

# JSON persistence setup
RATINGS_FILE = Path(__file__).resolve().parent.parent / "ratings.json"

def _rating_to_dict(r: trueskill.Rating) -> dict:
    return {"mu": r.mu, "sigma": r.sigma}

def _save_ratings_to_file() -> None:
    try:
        conn = utils.get_db_connection()
        cursor = conn.cursor()
        for k, v in ratings.items():
            cursor.execute(
                "INSERT OR REPLACE INTO trueskill_ratings (image_id, mu, sigma) VALUES (?, ?, ?)",
                (int(k), v.mu, v.sigma)
            )
            cursor.execute(
                "UPDATE images SET rating = ? WHERE id = ?",
                (v.mu, int(k))
            )
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error saving ratings to SQLite:", e)

def _load_ratings_from_file() -> None:
    global ratings
    _ensure_images_loaded()
    try:
        conn = utils.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT image_id, mu, sigma FROM trueskill_ratings")
        for row in cursor.fetchall():
            ratings[int(row["image_id"])] = env.create_rating(mu=row["mu"], sigma=row["sigma"])
        conn.close()
    except Exception as e:
        print("Error loading ratings from SQLite:", e)
    # keep caches consistent
    _recompute_rated_cache()

# Request models
class MatchResult(BaseModel):
    winner_id: int
    loser_id: int

def get_rating(image_id: int) -> trueskill.Rating:
    """Get rating, default to 25±8.333 (standard TrueSkill initial values)."""
    if image_id not in ratings:
        ratings[image_id] = env.create_rating()
    return ratings[image_id]

# Load ratings at import time
_load_ratings_from_file()

@router.post("/match")
def record_match(result: MatchResult):
    winner = get_rating(result.winner_id)
    loser = get_rating(result.loser_id)

    # Update ratings with TrueSkill
    (winner_new,), (loser_new,) = env.rate([[winner], [loser]])
    ratings[result.winner_id] = winner_new
    ratings[result.loser_id] = loser_new
    _save_ratings_to_file()
    # Update caches incrementally
    _on_rating_changed(result.winner_id)
    _on_rating_changed(result.loser_id)

    w_cr = winner_new.mu - 3 * winner_new.sigma
    l_cr = loser_new.mu - 3 * loser_new.sigma
    w_rank = rank_from_cr(w_cr)
    l_rank = rank_from_cr(l_cr)

    return {
        "winner": {
            "id": result.winner_id,
            "mu": winner_new.mu,
            "sigma": winner_new.sigma,
            "conservative_rating": w_cr,
            "rank_tier": w_rank["tier"],
            "rank_subrank": w_rank["subrank"],
            "rank_label": w_rank["label"],
        },
        "loser": {
            "id": result.loser_id,
            "mu": loser_new.mu,
            "sigma": loser_new.sigma,
            "conservative_rating": l_cr,
            "rank_tier": l_rank["tier"],
            "rank_subrank": l_rank["subrank"],
            "rank_label": l_rank["label"],
        },
    }

@router.get("/score/{image_id}")
def get_score(image_id: int):
    rating = get_rating(image_id)
    cr = rating.mu - 3 * rating.sigma
    rinfo = rank_from_cr(cr)
    return {
        "id": image_id,
        "mu": rating.mu,
        "sigma": rating.sigma,
        "conservative_rating": cr,
        "rank_tier": rinfo["tier"],
        "rank_subrank": rinfo["subrank"],
        "rank_label": rinfo["label"],
    }


@router.post("/score/remove/{image_id}")
def remove_score(image_id: int):
    if image_id in ratings:
        del ratings[image_id]
        _save_ratings_to_file()
        _on_rating_changed(image_id)
        return {"message": "Score removed successfully"}
    raise HTTPException(status_code=404, detail="Image not found")


# Keep track of recently shown pairs (to avoid repeats)
_last_matchup: tuple[int, int] | None = None


def conservative_rating(r: trueskill.Rating) -> float:
    return r.mu - 3 * r.sigma

# ----- Rank helpers -----
_TIERS = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ruby"]  # ordered from low to high

def _rank_from_value(value: int) -> dict:
    if value <= 0:
        return {"tier": "Unranked", "subrank": None, "label": "Unranked", "value": 0}
    v = max(1, min(20, int(value)))
    idx = v - 1
    tier_idx = idx // 4
    sub = 4 - (idx % 4)
    tier = _TIERS[tier_idx]
    return {"tier": tier, "subrank": sub, "label": f"{tier} {sub}", "value": v}

def _cr_min_max() -> Optional[tuple[float, float]]:
    # Use only rated items to establish dynamic bounds
    crs = [conservative_rating(r) for r in ratings.values() if not is_unrated(r)]
    if not crs:
        return None
    return (min(crs), max(crs))

def rank_from_cr(cr: float) -> dict:
    # Treat exact 0 as Unranked (default TrueSkill conservative rating)
    if abs(cr) < 1e-12:
        return {"tier": "Unranked", "subrank": None, "label": "Unranked", "value": 0}

    bounds = _cr_min_max()
    if not bounds:
        # Fallback to fixed bins if we have no rated items yet
        idx = int(min(19, max(0, math.floor((cr - 1e-12) / 2.5))))
        return _rank_from_value(idx + 1)

    min_cr, max_cr = bounds
    if math.isclose(min_cr, max_cr):
        # Degenerate case: all same -> center-ish
        return _rank_from_value(10)

    # Map [min_cr .. max_cr] linearly to values [1 .. 20]
    if cr <= min_cr:
        v = 1
    elif cr >= max_cr:
        v = 20
    else:
        norm = (cr - min_cr) / (max_cr - min_cr)  # 0..1
        v = int(round(1 + norm * 19))
        v = max(1, min(20, v))

    return _rank_from_value(v)

def average_rank_from_cr(cr1: float, cr2: float) -> dict:
    v1 = rank_from_cr(cr1)["value"]
    v2 = rank_from_cr(cr2)["value"]
    vals = [v for v in (v1, v2) if v > 0]
    if not vals:
        return _rank_from_value(0)
    avg = int(round(sum(vals) / len(vals)))
    return _rank_from_value(avg)

def get_conservative_rating(image_id: int) -> float:
    r = get_rating(image_id)
    return conservative_rating(r)


def is_unrated(r: trueskill.Rating) -> bool:
    return conservative_rating(r) <= 0.01

def remove_ratings_for_missing_images():
    """Remove ratings for images that no longer exist."""
    _ensure_images_loaded()
    images = utils.images_data
    if not images:
        return

    valid_ids = set(images.keys())
    to_remove = [img_id for img_id in ratings.keys() if img_id not in valid_ids]
    for img_id in to_remove:
        del ratings[img_id]
        _on_rating_changed(img_id)

    if to_remove:
        _save_ratings_to_file()


remove_ratings_for_missing_images()

@router.get("/matchup")
def get_matchup(image1_id: Optional[int] = None):
    global _last_matchup

    try:
        utils.load_images()
    except Exception:
        pass

    images = utils.images_data
    if len(images) < 2:
        return {"error": "Not enough images to create a matchup"}

    img_ids = list(images.keys())

    # Ensure all have ratings
    for img_id in img_ids:
        _ = get_rating(img_id)

    # Separate groups
    rated = [(i, r) for i, r in ratings.items() if not is_unrated(r)]
    unrated = [(i, r) for i, r in ratings.items() if is_unrated(r)]

    # If the first image is specified, use it and pick a suitable opponent
    if image1_id is not None:
        if image1_id not in images:
            return {"error": "Invalid or unknown image1_id"}
        img1_id = image1_id
        r1 = get_rating(img1_id)
        is_r1_unrated = is_unrated(r1)

        # Candidate pools excluding img1
        rated_ex = [(i, r) for i, r in rated if i != img1_id]
        unrated_ex = [(i, r) for i, r in unrated if i != img1_id]
        others = [i for i in img_ids if i != img1_id]

        choice = random.random()
        img2_id: Optional[int] = None

        # 40%: encourage rated/unrated exploration pairing
        if rated_ex and unrated_ex and choice < 0.4:
            if is_r1_unrated:
                img2_id, _ = random.choice(rated_ex)
            else:
                img2_id, _ = random.choice(unrated_ex)

        # 40%: close rated-vs-rated if img1 is rated and there is another rated
        elif (not is_r1_unrated) and rated_ex and choice < 0.8:
            rated_sorted = sorted(
                rated_ex,
                key=lambda x: abs(conservative_rating(x[1]) - conservative_rating(r1))
            )
            img2_id, _ = rated_sorted[0]

        # 20% (or fallback): random opponent
        if img2_id is None:
            img2_id = random.choice(others)

    else:
        # Original random/exploration/exploitation behavior
        choice = random.random()
        if unrated and rated and choice < 0.4:
            # 40%: rated vs unrated
            img1_id, _ = random.choice(rated)
            img2_id, _ = random.choice(unrated)
        elif len(rated) >= 2 and choice < 0.8:
            # 40%: rated vs rated (close skill)
            img1_id, r1 = random.choice(rated)
            rated_sorted = sorted(
                rated,
                key=lambda x: abs(conservative_rating(x[1]) - conservative_rating(r1))
            )
            for img2_id, _ in rated_sorted:
                if img2_id != img1_id:
                    break
            else:
                img2_id, _ = random.choice(rated)
        else:
            # 20%: totally random
            img1_id, img2_id = random.sample(img_ids, 2)

    # Avoid repeating last matchup
    if _last_matchup and {img1_id, img2_id} == set(_last_matchup) and len(img_ids) > 2:
        if image1_id is not None:
            prev_other = _last_matchup[0] if _last_matchup[1] == img1_id else _last_matchup[1]
            candidates = [i for i in img_ids if i != img1_id and i != prev_other]
            if not candidates:
                candidates = [i for i in img_ids if i != img1_id]
            img2_id = random.choice(candidates)
        else:
            img1_id, img2_id = random.sample(img_ids, 2)

    _last_matchup = (img1_id, img2_id)

    # Gather data
    img1 = images.get(img1_id, {})
    img2 = images.get(img2_id, {})
    r1 = get_rating(img1_id)
    r2 = get_rating(img2_id)
    cr1 = conservative_rating(r1)
    cr2 = conservative_rating(r2)
    rank1 = rank_from_cr(cr1)
    rank2 = rank_from_cr(cr2)
    avg_rank = average_rank_from_cr(cr1, cr2)

    # ----- New: predicted winner (using predicted ratings only) -----
    meta1 = _get_image_meta(img1_id)
    meta2 = _get_image_meta(img2_id)
    pred1 = _predict_from_meta(meta1["prompt"], meta1["phash"], top_k=20, alpha=0.6) if meta1 else None
    pred2 = _predict_from_meta(meta2["prompt"], meta2["phash"], top_k=20, alpha=0.6) if meta2 else None
    pred_cr1 = pred1["predicted_conservative_rating"] if pred1 else cr1
    pred_cr2 = pred2["predicted_conservative_rating"] if pred2 else cr2
    pred_rank1 = rank_from_cr(pred_cr1)
    pred_rank2 = rank_from_cr(pred_cr2)
    # Logistic win probability based on predicted CR difference
    scale = 5.0
    diff = pred_cr1 - pred_cr2
    prob_img1 = 1.0 / (1.0 + math.exp(-diff / scale))
    if pred_cr1 >= pred_cr2:
        predicted_winner_id = img1_id
        winner_pred_cr = pred_cr1
        winner_pred_rank = pred_rank1
        win_prob = prob_img1
    else:
        predicted_winner_id = img2_id
        winner_pred_cr = pred_cr2
        winner_pred_rank = pred_rank2
        win_prob = 1.0 - prob_img1
    # ---------------------------------------------------------------

    # Compute top percentile for image1
    top_percentile1 = None
    bounds = _cr_min_max()
    if bounds:
        min_cr, max_cr = bounds
        if cr1 >= max_cr:
            top_percentile1 = 100.0
        elif cr1 <= min_cr:
            top_percentile1 = 0.0
        else:
            count_below = sum(1 for r in ratings.values() if not is_unrated(r) and conservative_rating(r) < cr1)
            total_count = sum(1 for r in ratings.values() if not is_unrated(r))
            if total_count > 0:
                top_percentile1 = (count_below / total_count) * 100.0
                top_percentile1 = round(top_percentile1, 2)
                top_percentile1 = min(top_percentile1, 100.0)

    # compute top percentile for image2
    top_percentile2 = None
    if bounds:
        min_cr, max_cr = bounds
        if cr2 >= max_cr:
            top_percentile2 = 100.0
        elif cr2 <= min_cr:
            top_percentile2 = 0.0
        else:
            count_below = sum(1 for r in ratings.values() if not is_unrated(r) and conservative_rating(r) < cr2)
            total_count = sum(1 for r in ratings.values() if not is_unrated(r))
            if total_count > 0:
                top_percentile2 = (count_below / total_count) * 100.0
                top_percentile2 = round(top_percentile2, 2)
                top_percentile2 = min(top_percentile2, 100.0)
    

    return {
        "image1": {
            "id": img1_id,
            "Path": img1.get("Path") or img1.get("path"),
            "mu": r1.mu,
            "sigma": r1.sigma,
            "conservative_rating": cr1,
            "rank_tier": rank1["tier"],
            "rank_subrank": rank1["subrank"],
            "rank_label": rank1["label"],
            "top_percentile": top_percentile1
        },
        "image2": {
            "id": img2_id,
            "Path": img2.get("Path") or img2.get("path"),
            "mu": r2.mu,
            "sigma": r2.sigma,
            "conservative_rating": cr2,
            "rank_tier": rank2["tier"],
            "rank_subrank": rank2["subrank"],
            "rank_label": rank2["label"],
            "top_percentile": top_percentile2
        },
        "average_rank_tier": avg_rank["tier"],
        "average_rank_subrank": avg_rank["subrank"],
        "average_rank_label": avg_rank["label"],
        "predicted_winner": {
            "id": predicted_winner_id,
            "predicted_conservative_rating": winner_pred_cr,
            "predicted_rank_tier": winner_pred_rank["tier"],
            "predicted_rank_subrank": winner_pred_rank["subrank"],
            "predicted_rank_label": winner_pred_rank["label"],
            "win_probability": round(win_prob, 4),
        },
    }

@router.get("/leaderboard")
def get_leaderboard(limit: int = 100, include_unrated: bool = False):
    images = getattr(utils, "images_data", {}) or {}

    # Ensure every known image has a rating (creates default for unrated)
    for img_id in images.keys():
        _ = get_rating(img_id)

    items = []
    for img_id, r in ratings.items():
        if not include_unrated and is_unrated(r):
            continue  # skip unrated images

        img = images.get(img_id, {})
        path = img.get("Path") or img.get("path")
        cr = r.mu - 3 * r.sigma
        rinfo = rank_from_cr(cr)
        items.append({
            "id": img_id,
            "Path": path,
            "mu": r.mu,
            "sigma": r.sigma,
            "conservative_rating": cr,
            "rank_tier": rinfo["tier"],
            "rank_subrank": rinfo["subrank"],
            "rank_label": rinfo["label"],
        })

    # Sort by conservative rating, highest first
    items.sort(key=lambda x: x["conservative_rating"], reverse=True)
    return {"leaderboard": items[: max(0, min(limit, len(items)))]}


# ---------- Prediction helpers (Prompt + pHash) ----------

def _get_image_meta(image_id: int) -> Optional[dict]:
    _ensure_images_loaded()
    images = getattr(utils, "images_data", {}) or {}
    img = images.get(image_id)
    if not img:
        return None

    prompt = img.get("Prompt") or img.get("prompt") or ""
    phash = img.get("pHash") or img.get("phash") or img.get("hash") or ""
    return {"prompt": str(prompt), "phash": str(phash)}


def _tokenize(prompt: str) -> set[str]:
    # Simple, robust tokenization for tags/phrases
    s = (prompt or "").lower().replace(",", " ")
    tokens: list[str] = []
    for part in s.split():
        t = "".join(ch for ch in part if ch.isalnum() or ch in ("#", "+"))
        if t:
            tokens.append(t)
    return set(tokens)


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return (inter / union) if union else 0.0


def _phash_similarity(h1: str, h2: str) -> float:
    if not h1 or not h2:
        return 0.0
    try:
        i1 = int(h1, 16)
        i2 = int(h2, 16)
    except ValueError:
        return 0.0
    xor = i1 ^ i2
    # Estimate bit-length from hex length (4 bits per hex char)
    n_bits = max(len(h1), len(h2)) * 4
    if n_bits <= 0:
        return 0.0
    dist = xor.bit_count()
    dist = min(dist, n_bits)
    return 1.0 - (dist / n_bits)


def _predict_from_meta(prompt: str, phash: str, top_k: int = 20, alpha: float = 0.6) -> Optional[dict]:
    # Fast, scalable prediction using caches and token index
    _ensure_images_loaded()
    with _CACHE_LOCK:
        if not _RATED_IDS:
            _recompute_rated_cache()
        rated_ids = list(_RATED_IDS)

    if not rated_ids:
        return None  # nothing to compare to

    q_tokens = _tokenize(prompt or "")
    q_ph_int, q_ph_bits = _phash_to_int_bits(str(phash or ""))

    # If we have neither tokens nor a valid phash, fall back to mean
    if not q_tokens and q_ph_bits == 0:
        return {"predicted_conservative_rating": _MEAN_CR, "neighbors_used": 0}

    # Build candidate set via token index; if empty, fall back to all rated ids (sampled)
    candidates: set[int] = set()
    if q_tokens:
        with _CACHE_LOCK:
            for t in q_tokens:
                ids = _TOKEN_INDEX.get(t)
                if ids:
                    candidates.update(ids)
    if not candidates:
        # No token overlap; fallback to all rated ids
        candidates = set(rated_ids)

    # Limit candidate size for scalability
    if len(candidates) > _MAX_CANDIDATES:
        candidates = set(random.sample(list(candidates), _MAX_CANDIDATES))

    # Compute similarities, keep only top_k via a min-heap
    start = time.perf_counter()
    heap: list[tuple[float, float]] = []  # (similarity, conservative_rating)

    # Pre-calc for jaccard against many
    q_len = len(q_tokens)

    for cid in candidates:
        # Time budget check (soft)
        if (time.perf_counter() - start) * 1000.0 > _TIME_BUDGET_MS and len(heap) >= max(5, top_k):
            break

        # Ensure meta present
        tokens, ph_int, ph_bits = _ensure_meta_cached(cid)

        # Text similarity (Jaccard)
        if q_tokens and tokens:
            inter = len(q_tokens & tokens)
            if inter == 0:
                s_text = 0.0
            else:
                union = q_len + len(tokens) - inter
                s_text = (inter / union) if union else 0.0
        else:
            s_text = 0.0

        # pHash similarity
        if q_ph_bits and ph_bits and q_ph_int and ph_int:
            xor = q_ph_int ^ ph_int
            n_bits = max(q_ph_bits, ph_bits)
            dist = (xor.bit_count() if hasattr(int, "bit_count") else bin(xor).count("1"))
            if dist > n_bits:
                dist = n_bits
            s_hash = 1.0 - (dist / n_bits)
        else:
            s_hash = 0.0

        s = alpha * s_text + (1.0 - alpha) * s_hash
        if s <= 0.0:
            continue

        cr = conservative_rating(get_rating(cid))
        if len(heap) < max(1, top_k):
            heapq.heappush(heap, (s, cr))
        else:
            if s > heap[0][0]:
                heapq.heapreplace(heap, (s, cr))

    if not heap:
        # Fallback to mean of rated if no positive similarity found
        return {"predicted_conservative_rating": _MEAN_CR, "neighbors_used": 0}

    total_w = sum(s for s, _ in heap)
    if total_w <= 0.0:
        pred = sum(cr for _, cr in heap) / len(heap)
    else:
        pred = sum(s * cr for s, cr in heap) / total_w

    return {"predicted_conservative_rating": pred, "neighbors_used": len(heap)}


class PredictRequest(BaseModel):
    prompt: Optional[str] = None
    pHash: Optional[str] = None
    top_k: int = 20
    alpha: float = 0.6


@router.get("/predict/{image_id}")
def predict_score_for_image(image_id: int, top_k: int = 20, alpha: float = 0.6):
    meta = _get_image_meta(image_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Image not found")

    res = _predict_from_meta(meta["prompt"], meta["phash"], top_k=top_k, alpha=alpha)
    if res is None:
        raise HTTPException(status_code=400, detail="Not enough rated images to predict")

    pred_cr = res["predicted_conservative_rating"]
    pred_rinfo = rank_from_cr(pred_cr)
    
    result = {
        "id": image_id,
        "predicted_conservative_rating": pred_cr,
        "neighbors_used": res["neighbors_used"],
        "predicted_rank_tier": pred_rinfo["tier"],
        "predicted_rank_subrank": pred_rinfo["subrank"],
        "predicted_rank_label": pred_rinfo["label"],
        "label": pred_rinfo["label"],
        "tier": pred_rinfo["tier"],
        "unrated": True,
    }
    
    # Add actual rank if available
    if image_id in ratings:
        r = ratings[image_id]
        if not is_unrated(r):
            actual_cr = conservative_rating(r)
            actual_rinfo = rank_from_cr(actual_cr)
            result["actual_conservative_rating"] = actual_cr
            result["actual_rank_tier"] = actual_rinfo["tier"]
            result["actual_rank_subrank"] = actual_rinfo["subrank"]
            result["actual_rank_label"] = actual_rinfo["label"]
            result["label"] = actual_rinfo["label"]
            result["tier"] = actual_rinfo["tier"]
            result["unrated"] = False
            
    
    return result


@router.post("/predict")
def predict_score(req: PredictRequest):
    res = _predict_from_meta(req.prompt or "", req.pHash or "", top_k=req.top_k, alpha=req.alpha)
    if res is None:
        raise HTTPException(status_code=400, detail="Not enough rated images to predict")

    pred_cr = res["predicted_conservative_rating"]
    rinfo = rank_from_cr(pred_cr)
    return {
        "predicted_conservative_rating": pred_cr,
        "neighbors_used": res["neighbors_used"],
        "predicted_rank_tier": rinfo["tier"],
        "predicted_rank_subrank": rinfo["subrank"],
        "predicted_rank_label": rinfo["label"],
    }

