from fastapi import APIRouter, Query
import random
from difflib import SequenceMatcher
import math
import re
import utils  # changed from "from .. import utils"

router = APIRouter()

quality_tags = [
    "masterpiece",
    "best quality",
    "detailed",
    "score_9",
    "score_8",
    "score_7",
    "score_6",
    "score_5",
    "score_4",
    "score_3",
    "score_2",
    "score_1",
    "realistic",
    "amazing quality",
    "score_8_up",
    "score_7_up",
    "score_6_up",
    "score_5_up",
    "score_4_up",
    "highly detailed",
    "high contrast",
    "film grain",
    "Rim Lighting",
    "Long Exposure",
    "Soft Lighting",
    "Studio Lighting",
    "High Dynamic Range",
    "High Contrast",
    "Low Contrast",
    "Low Dynamic Range",
    "High Key",
    "Low Key",
    "Backlighting",
    "Overexposed",
    "Underexposed",
    "Natural Light",
    "Ambient Light",
    "Artificial Light",
    "Diffused Light",
    "Harsh Light",
    "DSLR",
    "highest quality",
    "soft lighting",
    "digital painting",
    "digital painting",
    "sharp focus",
    "by antonio j. manzanedo",
    "bloom",
    "by jeremy lipking",
    "[[chromatic aberration]]",
    "(backlighting)"
    "high quality",
    "4k",
    "(best quality)",
    "8k",
    "dslr",
    "8k uhd",
    "fujifilm xt3",
    "intricate",
    "hdr",
    "cinematic lighting",
    "<lora",
    "lens flare",
    "backlighting",
    "high quality",
    "raw photo",
    "nsfw",
]



@router.get("/autocomplete-tags")
def autocomplete_tags(
    query: str = Query(..., description="Tag search query"),
    limit: int = Query(10, description="Maximum number of tags to return"),
    min_score: float = Query(0.3, description="Minimum fuzzy match score (0-1)")
):
    def clean_tag(tag: str) -> str:
        if not tag:
            return ""
        t = tag.strip()
        t = t.replace("(", "").replace(")", "")
        t = re.sub(r":\d+(?:\.\d+)?$", "", t)
        return t.strip()

    if not query:
        return []
    q = clean_tag(query.lower().strip())

    # NEW: date: autocomplete (date:yyyy-mm-dd)
    if "date:" in q:
        prefix_after = q.split("date:", 1)[1]  # may be partial yyyy, yyyy-mm, etc.
        date_counts = {}
        for img in utils.all_images:
            ticks = img.get("CreatedDate")
            if not ticks:
                continue
            try:
                dt = utils.ticksToDatetime(int(ticks))
                date_str = dt.strftime("%Y-%m-%d")
                date_counts[date_str] = date_counts.get(date_str, 0) + 1
            except Exception:
                continue
        # Filter by partial after date:
        filtered = []
        for d, cnt in date_counts.items():
            if not prefix_after or d.startswith(prefix_after):
                filtered.append((d, cnt))
        # Sort by count desc then date desc
        filtered.sort(key=lambda x: (x[1], x[0]), reverse=True)
        # Build results
        results = []
        for i, (d, cnt) in enumerate(filtered[:limit]):
            # Simple fuzzy: full match =1, prefix match high, else lower
            if prefix_after and d.startswith(prefix_after):
                fuzz = min(1.0, 0.8 + 0.2 * (len(prefix_after) / len(d)))
            else:
                fuzz = 1.0 if not prefix_after else 0.5
            results.append({
                "index": i,
                "tag": f"date:{d}",
                "count": cnt,
                "fuzzy_score": round(fuzz, 4)
            })
        return results

    tag_counts = {}
    for img in utils.all_images:
        for raw_tag in img.get("tags_set", []):
            ct = clean_tag(raw_tag)
            if not ct:
                continue
            tag_counts[ct] = tag_counts.get(ct, 0) + 1

    def token_set_ratio(a: str, b: str) -> float:
        ta = set(a.split())
        tb = set(b.split())
        inter = ta & tb
        if not ta or not tb:
            return 0.0
        inter_str = " ".join(sorted(inter))
        diff_str_a = " ".join(sorted(ta - tb))
        diff_str_b = " ".join(sorted(tb - ta))
        combo1 = (inter_str + " " + diff_str_a).strip()
        combo2 = (inter_str + " " + diff_str_b).strip()
        if not combo1 or not combo2:
            return SequenceMatcher(None, a, b).ratio()
        return max(
            SequenceMatcher(None, inter_str, a).ratio(),
            SequenceMatcher(None, inter_str, b).ratio(),
            SequenceMatcher(None, combo1, combo2).ratio(),
        )

    def fuzzy_score(q: str, tag: str) -> float:
        t = tag.lower()
        seq_ratio = SequenceMatcher(None, q, t).ratio()
        tok_ratio = token_set_ratio(q, t)
        boost = 0.0
        if q in t:
            boost += 0.15
        if t.startswith(q):
            boost += 0.15
        length_diff = abs(len(t) - len(q))
        length_penalty = max(0.0, 0.08 * math.log10(length_diff + 1))
        raw = max(seq_ratio, tok_ratio) + boost - length_penalty
        return max(0.0, min(1.0, raw))

    scored = []
    for tag, count in tag_counts.items():
        score = fuzzy_score(q, tag)
        if score >= min_score:
            weighted = score * (1 + math.log10(count + 1) * 0.25)
            scored.append((tag, count, score, weighted))

    scored.sort(key=lambda x: (x[3], x[2], x[1]), reverse=True)
    return [
        {
            "index": i,
            "tag": tag,
            "count": count,
            "fuzzy_score": round(score, 4)
        }
        for i, (tag, count, score, _) in enumerate(scored[:limit])
    ]

@router.get("/tags")
def get_tags(limit: int = Query(10, description="Maximum number of tags to return")):
    # get top tags excluding quality tags
    tag_counts = {}
    tag_images = {}  # Dictionary to store image examples for each tag
    tag_metrics = {}  # Dictionary to store likes, views, and saves for each tag
    
    for img in utils.all_images:
        img_path = img.get("Path", "")
        likes = img.get("likes", 0)
        views = img.get("views", 0)
        saves = img.get("board_saves", 0)
        
        for tag in img.get("tags_set", []):
            # Clean tag by removing parentheses and ratio patterns like :1), :1.2)
            clean_tag = tag.replace("(", "").replace(")", "")
            clean_tag = clean_tag.split(":")[0].strip()  # Remove everything after colon
            if clean_tag not in quality_tags:  # Skip quality tags
                tag_counts[clean_tag] = tag_counts.get(clean_tag, 0) + 1
                # Store this image as a possible cover for this tag
                if clean_tag not in tag_images:
                    tag_images[clean_tag] = []
                tag_images[clean_tag].append(img_path)
                
                # Update metrics
                if clean_tag not in tag_metrics:
                    tag_metrics[clean_tag] = {"likes": 0, "views": 0, "saves": 0}
                tag_metrics[clean_tag]["likes"] += likes
                tag_metrics[clean_tag]["views"] += views
                tag_metrics[clean_tag]["saves"] += saves
    
    # Get top tags by occurrence
    sorted_tags = sorted(tag_counts.items(), key=lambda item: item[1], reverse=True)
    top_tags_result = []
    
    for tag, count in sorted_tags[:limit]:
        # Select a random image for this tag if available
        cover_image = None
        if tag in tag_images and tag_images[tag]:
            cover_image = random.choice(tag_images[tag])
        
        top_tags_result.append({
            "tag": tag, 
            "count": count,
            "cover_image": cover_image
        })
    
    # Calculate recommended tags based on engagement metrics
    engagement_score = {}
    for tag, metrics in tag_metrics.items():
        # Calculate an engagement score (weighted sum of likes, views, and saves)
        score = (2 * metrics["likes"]) + metrics["views"] + (3 * metrics["saves"])
        if tag_counts.get(tag, 0) > 0:  # Avoid division by zero
            # Normalize by tag count to find tags with high engagement per occurrence
            engagement_score[tag] = score / tag_counts[tag]
    
    # Get top tags by engagement
    sorted_recommended = sorted(engagement_score.items(), key=lambda item: item[1], reverse=True)
    recommended_tags = []
    
    for tag, score in sorted_recommended[:limit]:
        cover_image = None
        if tag in tag_images and tag_images[tag]:
            cover_image = random.choice(tag_images[tag])
        
        recommended_tags.append({
            "tag": tag,
            "engagement_score": score,
            "count": tag_counts.get(tag, 0),
            "cover_image": cover_image
        })
    
    return {
        "top_tags": top_tags_result,
        "recommended_tags": recommended_tags
    }
