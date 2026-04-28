from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import random
from fastapi import APIRouter
import utils  
from sklearn.preprocessing import normalize

from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timezone
from routes import rate
from scipy.sparse import csr_matrix

def phash_to_bits(phash):
    return np.array([int(b) for h in phash for b in bin(int(h, 16))[2:].zfill(4)], dtype=np.uint8)

def average_phash(vectors):
    return (np.mean(vectors, axis=0) > 0.5).astype(np.uint8)

def hamming_similarity(a, b):
    return 1.0 - np.mean(np.bitwise_xor(a, b))

def get_recommended_images():
    
    # Helper: compute max similarity to a "seen" set in chunks (sparse-safe)
    def max_sim_to_seen(candidates_csr, seen_csr, batch_size=1024):
        n = candidates_csr.shape[0]
        out = np.zeros(n, dtype=np.float32)
        if seen_csr.shape[0] == 0 or n == 0:
            return out
        for start in range(0, n, batch_size):
            end = min(start + batch_size, n)
            block = candidates_csr[start:end] @ seen_csr.T
            block = block.toarray() if hasattr(block, "toarray") else block
            if block.size == 0:
                continue
            out[start:end] = block.max(axis=1).astype(np.float32)
        return out

    # Helper: simple MMR reranking using tag similarity (fast for small pools)
    def mmr_rerank(indices, base_scores, vectors_csr, top_pool=300, mmr_lambda=0.75):
        if len(indices) <= 2:
            return indices

        # Pool: take the top by base score
        pool = np.array(sorted(indices, key=lambda i: base_scores[i], reverse=True)[:min(top_pool, len(indices))])
        if pool.size < 3:
            return indices

        # Precompute tag similarity matrix for pool
        pool_vecs = vectors_csr[pool]
        sim = (pool_vecs @ pool_vecs.T)
        sim = sim.toarray() if hasattr(sim, "toarray") else sim
        np.fill_diagonal(sim, 0.0)
        sim = sim.astype(np.float32)

        # Normalize base scores in pool to [0,1]
        pool_scores = np.array([base_scores[i] for i in pool], dtype=np.float32)
        s_min, s_max = pool_scores.min(), pool_scores.max()
        if s_max - s_min < 1e-8:
            norm_scores = np.zeros_like(pool_scores, dtype=np.float32)
        else:
            norm_scores = (pool_scores - s_min) / (s_max - s_min)

        # Greedy MMR
        selected = [int(pool[np.argmax(norm_scores)])]
        remaining = set(pool.tolist()) - set(selected)

        # Maintain max-sim to selected for each candidate
        idx_to_pos = {int(idx): pos for pos, idx in enumerate(pool.tolist())}
        max_sim_selected = np.zeros(pool.size, dtype=np.float32)

        while remaining:
            # Update max similarity to any selected
            last_pos = idx_to_pos[selected[-1]]
            # Update only those in remaining for speed
            for idx in list(remaining):
                pos = idx_to_pos[idx]
                if sim[pos, last_pos] > max_sim_selected[pos]:
                    max_sim_selected[pos] = sim[pos, last_pos]

            # Compute MMR objective for remaining
            best_idx = None
            best_val = -1e9
            for idx in remaining:
                pos = idx_to_pos[idx]
                mmr_val = mmr_lambda * norm_scores[pos] - (1.0 - mmr_lambda) * max_sim_selected[pos]
                if mmr_val > best_val:
                    best_val = mmr_val
                    best_idx = idx

            selected.append(int(best_idx))
            remaining.remove(int(best_idx))

            # Small cap to keep it fast when pool is big
            if len(selected) >= top_pool:
                break

        # Merge reranked pool with the rest (preserve base-score order)
        pool_set = set(pool.tolist())
        tail = [i for i in sorted(indices, key=lambda i: base_scores[i], reverse=True) if i not in pool_set]
        return selected + tail

    # Ensure images are loaded and fetch from the most complete source
    try:
        utils.load_images()
    except Exception:
        pass

    src = getattr(utils, "images_data", {}) or {}
    if isinstance(src, dict) and src:
        images_raw = list(src.values())
    else:
        images_raw = getattr(utils, "all_images", [])

    # Keep items that have either a prompt or a pHash
    images = [
        img for img in images_raw
        if (img.get("Prompt") or img.get("prompt") or img.get("pHash") or img.get("phash") or img.get("hash"))
    ]
    if not images:
        return []

    prompts = [(img.get("Prompt") or img.get("prompt") or "") for img in images]
    clicks = np.array([img.get("Clicks", 0) for img in images], dtype=np.float32)
    # Sanitize legacy 1–5 ratings: None/'' -> 0.0
    ratings = np.array([float(img.get("Rating", 0) or 0) for img in images], dtype=np.float32)

    # ---- TrueSkill conservative ratings integration ----
    def _img_id(img):
        for k in ("Id", "id", "image_id", "imageId", "ID"):
            if k in img and img[k] is not None:
                try:
                    return int(img[k])
                except Exception:
                    return None
        return None

    ts_crs_list = []
    for img in images:
        iid = _img_id(img)
        if iid is None:
            ts_crs_list.append(0.0)
        else:
            try:
                ts_crs_list.append(float(rate.get_conservative_rating(iid)))
            except Exception:
                ts_crs_list.append(0.0)
    ts_crs = np.array(ts_crs_list, dtype=np.float32)

    rated_by_ts_mask = ts_crs > 0.01  # matches routes.rate.is_unrated
    ts_rated_vals = ts_crs[rated_by_ts_mask]
    
    # Exclude ALL images with legacy 1-5 star ratings from candidates
    has_star_rating_mask = ratings > 0  # any star rating (1-5)

    # Use TrueSkill for profile building, but exclude star-rated images from candidates
    if ts_rated_vals.size >= 5:
        p25 = float(np.percentile(ts_rated_vals, 25))
        p75 = float(np.percentile(ts_rated_vals, 75))
        high_rated_mask = rated_by_ts_mask & (ts_crs >= p75)
        low_rated_mask = rated_by_ts_mask & (ts_crs <= p25)
        # Candidates: TrueSkill unrated AND no star rating
        unrated_mask = ~rated_by_ts_mask & ~has_star_rating_mask
        seen_mask = (clicks > 0) | rated_by_ts_mask | has_star_rating_mask
    else:
        # Fallback: use star ratings for profiles but still exclude star-rated from candidates
        high_rated_mask = ratings >= 4
        low_rated_mask = ratings <= 2
        # Candidates: no star rating at all
        unrated_mask = ~has_star_rating_mask
        seen_mask = (clicks > 0) | has_star_rating_mask

    # Fast TF-IDF (with basic tuning)
    vectorizer = TfidfVectorizer(max_features=5000, stop_words="english", sublinear_tf=True, norm="l2")
    try:
        tag_matrix = vectorizer.fit_transform(prompts)  # csr, l2-normalized
    except ValueError:
        # empty vocabulary (e.g., all prompts missing) -> zero matrix fallback
        tag_matrix = csr_matrix((len(prompts), 1), dtype=np.float32)

    # Profiles (weighted)
    pos_profile = None
    if np.any(high_rated_mask):
        # TS-based weights if available
        if ts_rated_vals.size >= 2:
            # normalize across TS-rated to [0,1]
            ts_min = ts_rated_vals.min()
            ts_max = ts_rated_vals.max()
            denom = (ts_max - ts_min) if (ts_max - ts_min) > 1e-8 else 1.0
            ts_norm = np.zeros_like(ts_crs, dtype=np.float32)
            ts_norm[rated_by_ts_mask] = (ts_crs[rated_by_ts_mask] - ts_min) / denom
            w = ts_norm[high_rated_mask]
        else:
            # fallback to star ratings as before
            w = (ratings[high_rated_mask] - 3.0) / 2.0  # 4->0.5, 5->1.0

        if w.size > 0 and np.sum(w) > 0:
            pos_profile = tag_matrix[high_rated_mask].T.dot(w.astype(np.float32)).astype(np.float32)
            norm = np.linalg.norm(pos_profile)
            if norm > 1e-8:
                pos_profile /= norm

    neg_profile = None
    if np.any(low_rated_mask):
        if ts_rated_vals.size >= 2:
            ts_min = ts_rated_vals.min()
            ts_max = ts_rated_vals.max()
            denom = (ts_max - ts_min) if (ts_max - ts_min) > 1e-8 else 1.0
            ts_norm = np.zeros_like(ts_crs, dtype=np.float32)
            ts_norm[rated_by_ts_mask] = (ts_crs[rated_by_ts_mask] - ts_min) / denom
            # stronger weight for lower TS ratings
            w = (1.0 - ts_norm[low_rated_mask])
        else:
            w = (3.0 - ratings[low_rated_mask]) / 2.0  # 2->0.5, 1->1.0

        if w.size > 0 and np.sum(w) > 0:
            neg_profile = tag_matrix[low_rated_mask].T.dot(w.astype(np.float32)).astype(np.float32)
            norm = np.linalg.norm(neg_profile)
            if norm > 1e-8:
                neg_profile /= norm

    # Candidate vectors - these are the items we want to recommend (no star ratings)
    unrated_indices = np.where(unrated_mask)[0]
    unrated_vectors = tag_matrix[unrated_mask]
    seen_vectors = tag_matrix[seen_mask]

    # If no unrated candidates exist, return empty (don't recommend already-rated items)
    if unrated_indices.size == 0:
        return []

    # Tag-based relevance
    tag_score = np.zeros(unrated_vectors.shape[0], dtype=np.float32)
    if pos_profile is not None:
        tag_score += (unrated_vectors @ pos_profile).A1 if hasattr(unrated_vectors @ pos_profile, "A1") else (unrated_vectors @ pos_profile).ravel()
    if neg_profile is not None:
        tag_score -= (unrated_vectors @ neg_profile).A1 if hasattr(unrated_vectors @ neg_profile, "A1") else (unrated_vectors @ neg_profile).ravel()

    # Novelty: penalize only very-high similarity to seen (keep moderate similarity to capture taste)
    sim_to_seen = max_sim_to_seen(unrated_vectors, seen_vectors, batch_size=1024)
    NOVELTY_SIM_THRESH = 0.55
    seen_prompt_penalty = np.clip((sim_to_seen - NOVELTY_SIM_THRESH) / max(1e-6, 1.0 - NOVELTY_SIM_THRESH), 0.0, 1.0).astype(np.float32)

    # pHash preparation with per-image cache (robust to missing/invalid hashes)
    # Infer target bit length from available hashes; default to 64 bits
    phash_strs = [str(img.get("pHash") or img.get("phash") or img.get("hash") or "") for img in images]
    valid_hex = [h for h in phash_strs if h and all(c in "0123456789abcdefABCDEF" for c in h)]
    target_bits = (len(max(valid_hex, key=len)) * 4) if valid_hex else 64

    def _normalize_bits(b: np.ndarray, L: int) -> np.ndarray:
        if b.shape[0] == L:
            return b
        if b.shape[0] > L:
            return b[:L]
        pad = np.zeros(L - b.shape[0], dtype=np.uint8)
        return np.concatenate([b, pad], axis=0)

    phash_bits_list = []
    for img in images:
        bits = img.get("_phash_bits")
        if isinstance(bits, np.ndarray) and bits.dtype == np.uint8:
            phash_bits_list.append(_normalize_bits(bits, target_bits))
        else:
            p = img.get("pHash") or img.get("phash") or img.get("hash") or ""
            try:
                bits = phash_to_bits(p) if p else np.zeros(target_bits, dtype=np.uint8)
            except Exception:
                bits = np.zeros(target_bits, dtype=np.uint8)
            bits = _normalize_bits(bits, target_bits)
            img["_phash_bits"] = bits  # cache for future calls
            phash_bits_list.append(bits)
    phashes_bits = np.stack(phash_bits_list).astype(np.uint8)

    # pHash groups
    high_rated_phashes = phashes_bits[high_rated_mask] if np.any(high_rated_mask) else None
    low_rated_phashes = phashes_bits[low_rated_mask] if np.any(low_rated_mask) else None
    seen_phashes = phashes_bits[seen_mask] if np.any(seen_mask) else None
    unrated_phashes = phashes_bits[unrated_mask]

    # Mean pHashes
    mean_high_phash = average_phash(high_rated_phashes) if high_rated_phashes is not None and high_rated_phashes.shape[0] > 0 else None
    mean_low_phash = average_phash(low_rated_phashes) if low_rated_phashes is not None and low_rated_phashes.shape[0] > 0 else None
    mean_seen_phash = average_phash(seen_phashes) if seen_phashes is not None and seen_phashes.shape[0] > 0 else None

    # pHash similarities
    phash_pos = np.zeros(unrated_phashes.shape[0], dtype=np.float32)
    phash_neg = np.zeros(unrated_phashes.shape[0], dtype=np.float32)
    phash_seen_sim = np.zeros(unrated_phashes.shape[0], dtype=np.float32)

    if mean_high_phash is not None:
        phash_pos = 1.0 - np.mean(np.bitwise_xor(unrated_phashes, mean_high_phash), axis=1).astype(np.float32)
    if mean_low_phash is not None:
        phash_neg = 1.0 - np.mean(np.bitwise_xor(unrated_phashes, mean_low_phash), axis=1).astype(np.float32)
    if mean_seen_phash is not None:
        phash_seen_sim = 1.0 - np.mean(np.bitwise_xor(unrated_phashes, mean_seen_phash), axis=1).astype(np.float32)

    # Thresholded pHash novelty (only penalize near-duplicates)
    PHASH_SEEN_THRESH = 0.85
    phash_seen_penalty = np.clip((phash_seen_sim - PHASH_SEEN_THRESH) / max(1e-6, 1.0 - PHASH_SEEN_THRESH), 0.0, 1.0).astype(np.float32)

    # Click/seen penalty (prefer truly unseen)
    clicked_unrated = (clicks[unrated_mask] > 0).astype(np.float32)

    # Legacy 1–5 rating contribution for candidates (should be all zeros now since candidates have no star ratings)
    unrated_star = ratings[unrated_mask]  # should all be 0
    star_norm = np.where(unrated_star > 0.0, (unrated_star - 3.0) / 2.0, 0.0).astype(np.float32)
    star_norm = np.clip(star_norm, -1.0, 1.0)

    # Positive/negative neighbor similarity to liked/disliked sets (drives “similar to likes”)
    pos_tag_neighbor_sim = np.zeros(unrated_vectors.shape[0], dtype=np.float32)
    if np.any(high_rated_mask):
        pos_tag_neighbor_sim = max_sim_to_seen(unrated_vectors, tag_matrix[high_rated_mask], batch_size=1024)

    neg_tag_neighbor_sim = np.zeros(unrated_vectors.shape[0], dtype=np.float32)
    if np.any(low_rated_mask):
        neg_tag_neighbor_sim = max_sim_to_seen(unrated_vectors, tag_matrix[low_rated_mask], batch_size=1024)

    def phash_max_sim(cands_bits: np.ndarray, group_bits: np.ndarray | None, sample_cap: int = 256, batch_size: int = 1024) -> np.ndarray:
        if group_bits is None or getattr(group_bits, "shape", (0,))[0] == 0 or cands_bits.shape[0] == 0:
            return np.zeros(cands_bits.shape[0], dtype=np.float32)
        G = group_bits
        if G.shape[0] > sample_cap:
            idx = np.linspace(0, G.shape[0] - 1, num=sample_cap, dtype=int)
            G = G[idx]
        out = np.zeros(cands_bits.shape[0], dtype=np.float32)
        for s in range(0, cands_bits.shape[0], batch_size):
            e = min(s + batch_size, cands_bits.shape[0])
            block = np.bitwise_xor(cands_bits[s:e][:, None, :], G[None, :, :])  # (b, g, bits)
            sim = 1.0 - np.mean(block, axis=2).astype(np.float32)  # (b, g)
            out[s:e] = sim.max(axis=1).astype(np.float32)
        return out

    phash_pos_nn = phash_max_sim(unrated_phashes, high_rated_phashes) if np.any(high_rated_mask) else np.zeros(unrated_phashes.shape[0], dtype=np.float32)
    phash_neg_nn = phash_max_sim(unrated_phashes, low_rated_phashes) if np.any(low_rated_mask) else np.zeros(unrated_phashes.shape[0], dtype=np.float32)

    # Recency
    current_time = datetime.now(timezone.utc)
    timestamps = []
    for img in images:
        ts = img.get("timestamp")
        if ts:
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            ts = current_time
        timestamps.append(ts)
    ages_hours = np.array([(current_time - ts).total_seconds() / 3600.0 for ts in timestamps], dtype=np.float32)
    unrated_ages = ages_hours[unrated_mask]
    decay_rate = 0.2  # stronger preference for freshness
    recency_score = np.exp(-decay_rate * unrated_ages / 24.0).astype(np.float32)

    # Random jitter
    random_jitter = np.random.uniform(0.0, 1.0, size=tag_score.shape).astype(np.float32)

    # Weights (tuned for speed/quality/novelty)
    W_TAG_POS = 0.40
    W_TAG_NEG = 0.30
    W_SEEN_PROMPT = 0.35
    W_PHASH_POS = 0.25
    W_PHASH_NEG = 0.20
    W_PHASH_SEEN = 0.20
    W_CLICK_SEEN = 0.30
    W_RECENCY = 0.20
    W_JITTER = 0.05
    W_OLD_RATING = 0.20
    # New neighbor-sim weights (promote similarity to likes, demote similarity to dislikes)
    W_POS_NEIGHBOR_PROMPT = 0.25
    W_NEG_NEIGHBOR_PROMPT = 0.15
    W_PHASH_POS_NN = 0.15
    W_PHASH_NEG_NN = 0.10

    # Final base score (only for unrated)
    recommendation_score = (
        W_TAG_POS * tag_score
        - W_TAG_NEG * 0.0  # neg already subtracted in tag_score
        - W_SEEN_PROMPT * seen_prompt_penalty
        + W_PHASH_POS * phash_pos
        - W_PHASH_NEG * phash_neg
        - W_PHASH_SEEN * phash_seen_penalty
        - W_CLICK_SEEN * clicked_unrated
        + W_OLD_RATING * star_norm
        + W_POS_NEIGHBOR_PROMPT * pos_tag_neighbor_sim
        - W_NEG_NEIGHBOR_PROMPT * neg_tag_neighbor_sim
        + W_PHASH_POS_NN * phash_pos_nn
        - W_PHASH_NEG_NN * phash_neg_nn
        + W_RECENCY * recency_score
        + W_JITTER * random_jitter
    )

    # Apply MMR reranking on unrated to favor diversity and novelty
    if unrated_indices.size > 1:
        # Build a quick lookup array of base scores per absolute index
        base_scores = np.zeros(len(images), dtype=np.float32)
        base_scores[unrated_indices] = recommendation_score

        reranked_unrated = mmr_rerank(unrated_indices.tolist(), base_scores, tag_matrix, top_pool=300, mmr_lambda=0.75)

        # Small rank-based boost to enforce reranked order while preserving magnitude
        n = len(reranked_unrated)
        rank_boost = np.linspace(1.0, 0.0, num=n, dtype=np.float32) * 0.02  # up to +0.02
        for rank, idx in enumerate(reranked_unrated):
            # If idx is unrated, update its score
            pos = np.where(unrated_indices == idx)[0]
            if pos.size > 0:
                recommendation_score[pos[0]] += rank_boost[rank]

    # Write scores back (unrated get computed above; rated items are excluded)
    for i, idx in enumerate(unrated_indices):
        images[idx]["recommendation_score"] = float(recommendation_score[i])

    # Only return unrated items (no star ratings), sorted by recommendation score
    unrated_images = [images[idx] for idx in unrated_indices]
    sorted_images = sorted(unrated_images, key=lambda x: x.get("recommendation_score", -1e9), reverse=True)

    # Avoid returning non-JSON-serializable cache fields
    safe_images = []
    for img in sorted_images:
        clean = {}
        for k, v in img.items():
            if k.startswith("_"):
                continue
            if isinstance(v, np.ndarray):
                clean[k] = v.tolist()
            elif isinstance(v, (np.floating, np.integer)):
                clean[k] = v.item()
            else:
                clean[k] = v
        safe_images.append(clean)

    return safe_images
