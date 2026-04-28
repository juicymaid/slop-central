from datetime import datetime
import json
import os
import random
import threading
import time
from fastapi import HTTPException, APIRouter

import GPUtil


router = APIRouter()

# Data file constants.
IMAGES_FILE = "images.json"
LIKES_FILE = "likes.json"
CLICKS_FILE = "clicks.json"
BOARDS_FILE = "boards.json"
TRASH_FILE = "trash.json"

# Global data structures.
images_data = {}
all_images = []  # used as a list to support append
raw_all_images = []  # used to store original images without modifications
clicks_data = {}
boards_data = {}  # { board_id: { "id": int, "name": str, "images": [int, ...] } }
trash_data = {}  # { image_id: { "TrashedAt": unix_timestamp } }

# Lazy-load state (startup can be made fast by deferring heavy JSON reads)
_data_loaded = False
_data_loading = False
_data_error = None
_data_lock = threading.Lock()

ignore_tags = ["score_9", "score_8", "score_7", "score_6", "score_5", "score_4", "score_3", "score_2", "score_1","score_8_up","score_7_up", "score_6_up"
                "masterpiece", "best quality", "amazing quality", "absurdres"
]

api_file_root = os.path.abspath("files")
api_root = os.path.abspath("")


image_embeddings = {}  # { image_id: { "vec": List[float], "norm": float } }
EMBEDDINGS_FILE = "embeddings.json"

def _embedding_text(img):
    parts = [
        img.get("Prompt") or "",
        img.get("taggerPrompt") or "",
        img.get("description") or "",
        ",".join(img.get("tags_set") or []),
    ]
    return " \n ".join(p for p in parts if p).strip()

def load_embeddings():
    global image_embeddings
    if os.path.exists(EMBEDDINGS_FILE):
        try:
            with open(EMBEDDINGS_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # restore {id: {"vec": [...], "norm": float}}
            image_embeddings = {
                int(k): {"vec": v["vec"], "norm": v.get("norm", (sum(x*x for x in v["vec"])) ** 0.5)}
                for k, v in raw.items()
            }
        except Exception:
            image_embeddings = {}

def save_embeddings():
    out = {str(k): v for k, v in image_embeddings.items()}
    with open(EMBEDDINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f)

def build_image_embeddings(
    model_name="nomic-embed-text",
    force=False,
    limit=None,
    save_every=25,
    progress_every=25,
):
    """
    Build (or refresh) embeddings for images missing them.
    force=True recomputes all.
    limit=N only processes first N (for debugging).
    save_every=N saves embeddings every N successful updates.
    progress_every=N logs progress every N items.
    """
    import ollama
    load_embeddings()
    to_process = []
    for img in all_images:
        iid = img["Id"]
        if force or iid not in image_embeddings:
            to_process.append(img)
    if limit:
        to_process = to_process[:limit]
    if not to_process:
        return {"processed": 0, "total": len(image_embeddings)}
    processed = 0
    saved_processed = 0
    total = len(to_process)
    started = time.perf_counter()
    for idx, img in enumerate(to_process, start=1):
        try:
            text = _embedding_text(img)
            if not text:
                continue
            resp = ollama.embeddings(model=model_name, prompt=text)
            vec = resp.get("embedding")
            if not vec:
                continue
            # store vector + precomputed norm
            norm = (sum(x*x for x in vec)) ** 0.5
            image_embeddings[img["Id"]] = {"vec": vec, "norm": norm}
            processed += 1
            if save_every and (processed - saved_processed) >= save_every:
                save_embeddings()
                saved_processed = processed
        except Exception:
            continue
        if progress_every and (idx % progress_every == 0 or idx == total):
            elapsed = time.perf_counter() - started
            pct = (idx / total) * 100
            print(
                f"Embedding progress {idx}/{total} ({pct:.1f}%) "
                f"processed={processed} elapsed={elapsed:.1f}s"
            )
    if processed != saved_processed:
        save_embeddings()
    return {"processed": processed, "total": len(image_embeddings)}


def load_trash():
    global trash_data
    trash_data = {}
    if os.path.exists(TRASH_FILE):
        with open(TRASH_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        trash_data = {int(k): v for k, v in raw.items()}


def save_trash():
    out = {str(k): v for k, v in trash_data.items()}
    with open(TRASH_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)


def load_images():
    global images_data, all_images, raw_all_images
    # Make reload safe/idempotent
    images_data = {}
    all_images = []
    raw_all_images = []
    if not os.path.exists(IMAGES_FILE):
        raise FileNotFoundError(f"{IMAGES_FILE} not found.")

    # Load trash first so we can exclude trashed images from all_images
    load_trash()

    with open(IMAGES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_all_images = data.copy()  # Store the original data before modifications

    for image in data:
        if "Id" not in image or "Path" not in image:
            continue

        # Default to empty string if "Prompt" is None.
        prompt = image.get("Prompt") or ""
        tags_set = {tag.strip().lower() for tag in prompt.split(",") if tag.strip()}
        image["tags_set"] = tags_set

        # Initialize vote counts if they don't exist.
        if "Likes" not in image:
            image["Likes"] = 0
        if "Dislikes" not in image:
            image["Dislikes"] = 0

        images_data[image["Id"]] = image
        # Exclude trashed images from the active list
        if image["Id"] not in trash_data:
            all_images.append(image)
    # 
    #load phashes from hashes.json if it exists
    if os.path.exists("hashes.json"):
        with open("hashes.json", "r", encoding="utf-8") as f:
            phashes = json.load(f)
        for img_id, phash in phashes.items():
            img = images_data.get(int(img_id))
            if img:
                img["pHash"] = phash

    load_votes()
    load_clicks()

def save_images():

    if not raw_all_images:
        raise ValueError("No images to save.")

    _runtime_fields = {"tags_set", "pHash", "Likes", "Dislikes", "Rating", "Clicks"}
    clean = [{k: v for k, v in img.items() if k not in _runtime_fields} for img in raw_all_images]

    with open(IMAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2)

def load_votes():
    if os.path.exists(LIKES_FILE):
        with open(LIKES_FILE, "r", encoding="utf-8") as f:
            votes = json.load(f)
        for img_id, vote in votes.items():
            img = images_data.get(int(img_id))
            if img:
                img["Likes"] = vote.get("Likes", img.get("Likes", 0))
                img["Dislikes"] = vote.get("Dislikes", img.get("Dislikes", 0))
                img["Rating"] = vote.get("Rating", img.get("Rating", 0))
def save_votes():
    votes = {}
    for img_id, img in images_data.items():
        votes[str(img_id)] = {"Likes": img.get("Likes", 0), "Dislikes": img.get("Dislikes", 0), "Rating": img.get("Rating", 0)}
    with open(LIKES_FILE, "w", encoding="utf-8") as f:
        json.dump(votes, f, indent=2)

def load_clicks():
    global clicks_data
    if os.path.exists(CLICKS_FILE):
        with open(CLICKS_FILE, "r", encoding="utf-8") as f:
            clicks_data = json.load(f)
        for img_id, click in clicks_data.items():
            img = images_data.get(int(img_id))
            if img:
                img["Clicks"] = click

def save_clicks():
    clicks = {}
    for img_id, img in images_data.items():
        clicks[str(img_id)] = img.get("Clicks", 0)
    with open(CLICKS_FILE, "w", encoding="utf-8") as f:
        json.dump(clicks, f, indent=2)

def load_boards():
    global boards_data
    if os.path.exists(BOARDS_FILE):
        with open(BOARDS_FILE, "r", encoding="utf-8") as f:
            boards_data = json.load(f)
        boards_data = {int(k): v for k, v in boards_data.items()}


def ensure_loaded(block: bool = True) -> bool:
    """Ensure images/boards are loaded into memory.

    If block=False, kicks off a background load (if needed) and returns immediately.
    """
    global _data_loaded, _data_loading, _data_error

    if _data_loaded:
        return True
    if _data_error is not None:
        # Keep error sticky so callers see the failure.
        raise RuntimeError(f"Data load failed: {_data_error}")

    if not block:
        with _data_lock:
            if _data_loaded or _data_loading:
                return False
            _data_loading = True

        def _bg_load():
            global _data_loaded, _data_loading, _data_error
            started = time.perf_counter()
            try:
                load_images()
                load_boards()
                _data_loaded = True
                _data_error = None
                elapsed = time.perf_counter() - started
                print(f"Data loaded in {elapsed:.2f}s (images={len(all_images)})")
            except Exception as e:
                _data_error = str(e)
                print(f"Data load failed: {e}")
            finally:
                _data_loading = False

        threading.Thread(target=_bg_load, daemon=True).start()
        return False

    # block=True: perform (or wait for) load
    with _data_lock:
        if _data_loaded:
            return True
        if _data_error is not None:
            raise RuntimeError(f"Data load failed: {_data_error}")
        if not _data_loading:
            _data_loading = True

    started = time.perf_counter()
    try:
        load_images()
        load_boards()
        _data_loaded = True
        _data_error = None
        elapsed = time.perf_counter() - started
        print(f"Data loaded in {elapsed:.2f}s (images={len(all_images)})")
        return True
    except Exception as e:
        _data_error = str(e)
        raise
    finally:
        _data_loading = False


def is_loaded() -> bool:
    return _data_loaded


def get_load_state() -> dict:
    return {
        "loaded": _data_loaded,
        "loading": _data_loading,
        "error": _data_error,
        "images": len(all_images),
        "boards": len(boards_data),
    }

def save_boards():
    with open(BOARDS_FILE, "w", encoding="utf-8") as f:
        json.dump(boards_data, f, indent=2)

def hamming_distance(hash1: str, hash2: str) -> int:
    if(not hash1 or not hash2):
        return float('inf')

    # Ensure both hashes are the same length.
    if len(hash1) != len(hash2):
        return float('inf')  # Return infinity if lengths differ.
    
    # Calculate Hamming distance between two hex strings.
    return sum(bin(int(a, 16) ^ int(b, 16)).count('1') for a, b in zip(hash1, hash2))

def compute_full_similarity(image_a, image_b, mode: str = "full"):
    # Get lowercase tag sets
    def parse_tags(image):
        if image.get("tags_set") is None:
            image["tags_set"] = {tag.strip().lower() for tag in (image.get("Prompt") or "").split(",") if tag.strip()}
        return image["tags_set"]

    tags_a = parse_tags(image_a)
    tags_b = parse_tags(image_b)

    # Tag similarity (Jaccard index)
    intersection = tags_a & tags_b
    union = tags_a | tags_b
    tag_score = len(intersection) / len(union) if union else 0

    if mode == "prompt":
        return tag_score


    # Visual similarity (pHash)
    phash_a = image_a.get("pHash")
    phash_b = image_b.get("pHash")
    phash_score = 0
    if phash_a and phash_b:
        dist = hamming_distance(phash_a, phash_b)
        phash_score = 1.0 - (dist / 64.0)  # normalized

    if mode == "hash":
        return phash_score

    # Optional metadata bonuses
    model_bonus = 0.15 if image_a.get("ModelHash") == image_b.get("ModelHash") else 0
    negative_prompt_bonus = 0.1 if image_a.get("NegativePrompt") == image_b.get("NegativePrompt") else 0
    sampler_bonus = 0.1 if image_a.get("Sampler") == image_b.get("Sampler") else 0

    # Final weighted score
    return (
        0.45 * tag_score +
        0.35 * phash_score +
        model_bonus +
        negative_prompt_bonus +
        sampler_bonus
    )


def get_current_timestamp():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def compute_custom_score(candidate, liked_images, disliked_images):
    score = 0
    for liked in liked_images:
        score += compute_full_similarity(candidate, liked)
    for disliked in disliked_images:
        score -= compute_full_similarity(candidate, disliked)
    return score

def compute_phash(image_path: str) -> str:
    from PIL import Image
    import imagehash
    try:
        img = Image.open(image_path)
        return str(imagehash.phash(img))
    except Exception as e:
        return None

def get_vram_usage():
    try:
        gpus = GPUtil.getGPUs()
        if not gpus:
            return {"error": "No GPUs found"}
        
        gpu_info = []
        for gpu in gpus:
            gpu_data = {
                "id": gpu.id,
                "name": gpu.name,
                "memory_total": gpu.memoryTotal,
                "memory_used": gpu.memoryUsed,
                "memory_free": gpu.memoryFree,
                "memory_util": gpu.memoryUtil,
                "load": gpu.load,
                "temperature": getattr(gpu, 'temperature', None)
            }
            gpu_info.append(gpu_data)
        
        return {"gpus": gpu_info}
    except Exception as e:
        return {"error": f"Failed to get GPU info: {str(e)}"}


@router.get("/image_count_per_day")
def get_image_count_per_day(min_images: int = 0):
    ensure_loaded()
    # Returns a dictionary with date strings as keys and counts as values.
    # example format "CreatedDate": 638020749362214946 (these are .NET ticks since 0001-01-01)
    from datetime import datetime, timedelta
    counts = {}
    base = datetime(1, 1, 1)
    for img in all_images:
        ts = img.get("CreatedDate")
        if not ts:
            continue
        try:
            ticks = int(ts)
            if ticks <= 0:
                continue
            # .NET tick = 100 nanoseconds = 0.1 microseconds
            dt = base + timedelta(microseconds=ticks // 10)
            # Guard against impossible far future dates
            if dt.year > 2100 or dt.year < 1900:
                continue

            date_str = dt.strftime("%Y-%m-%d")
            counts[date_str] = counts.get(date_str, 0) + 1
        except Exception:
            continue

    # Filter by min_images
    counts = {date: count for date, count in counts.items() if count >= min_images}

    return counts

def ticksToDatetime(ticks: int):
    # Converts .NET ticks to Python datetime.
    from datetime import datetime, timedelta
    base = datetime(1, 1, 1)
    return base + timedelta(microseconds=ticks // 10)

def datetimeToTicks(dt: datetime) -> int:
    # Converts Python datetime to .NET ticks.
    base = datetime(1, 1, 1)
    delta = dt - base
    ticks = int(delta.total_seconds() * 10**7)  # 10 million ticks per second
    return ticks


@router.get("/status")
def status():
    # Lightweight health/status endpoint for startup debugging.
    return get_load_state()

wildcard_path = r"H:\ent\ai\StabilityMatrix\Packages\forge\webui\extensions\sd-dynamic-prompts\wildcards"
@router.get("/wildcards")
def get_wildcards():
    """Returns a list of the txt files in the wildcards directory. (without .txt extension)"""
    try:
        files = os.listdir(wildcard_path)
        wildcards = [f[:-4] for f in files if f.endswith(".txt")]
        return {"wildcards": wildcards}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list wildcards: {str(e)}")

def get_dir_size(path):
    total = 0
    if not os.path.exists(path):
        return 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    return total

@router.get("/get_cost")
def get_cost():
    ensure_loaded()
    
    sampler_cost = {
        "Euler a" : 0.8,
        "Euler" : 0.8,
        "LMS" : 0.9,
        "DDIM" : 0.8,
        "DPM++ 2M": 1.2,
        "DPM++ 2M SDE": 1.2,
    }

    total_cost = 0
    
    for img in all_images:
        width = img.get("Width", 512)
        height = img.get("Height", 512)
        sampler = img.get("Sampler", "")
        
        # Ensure sampler is a hashable string, some json artifacts might parse as lists
        if isinstance(sampler, list):
            sampler = sampler[0] if sampler else ""
        elif not isinstance(sampler, str):
            sampler = str(sampler)

        steps = img.get("Steps", 30)
        
        base_resolution = 512 * 512
        base_sampler_cost = sampler_cost.get(sampler, 1)
        base_steps = 30
        
        res_mult = round((width * height) / base_resolution)
        image_cost = 1 * res_mult * base_sampler_cost * (steps / base_steps)
        
        prompt = img.get("Prompt") or ""
        lora_count = prompt.count("<lora:")
        
        add_cost_val = round(0.5636713 - 0.01146222 * lora_count + 0.07849689 * lora_count * lora_count)
        image_cost += add_cost_val
        
        total_cost += max(1, round(image_cost))

    return {"total_cost": total_cost}


def image_to_base64(image_path):
    import base64
    try:
        with open(image_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
        return encoded_string
    except Exception as e:
        print(f"Failed to encode image {image_path} to base64: {e}")
        return None