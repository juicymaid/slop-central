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
SHOWS_FILE = "shows.json"
BOARDS_FILE = "boards.json"
TRASH_FILE = "trash.json"

# Global data structures.
images_data = {}
all_images = []  # used as a list to support append
raw_all_images = []  # used to store original images without modifications
clicks_data = {}
shows_data = {}
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
    from routes.comments import get_embeddings
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
            vec = get_embeddings(model_name, text)
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

        # Initialize vote counts, clicks, and shows.
        if "Likes" not in image:
            image["Likes"] = 0
        if "Dislikes" not in image:
            image["Dislikes"] = 0
        image["Clicks"] = 0
        image["Shows"] = 0
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
    load_shows()

def save_images():

    if not raw_all_images:
        raise ValueError("No images to save.")

    _runtime_fields = {"tags_set", "pHash", "Likes", "Dislikes", "Rating", "Clicks", "Shows"}
    clean = [{k: v for k, v in img.items() if k not in _runtime_fields and not k.startswith("_")} for img in raw_all_images]

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

def load_shows():
    global shows_data
    if os.path.exists(SHOWS_FILE):
        try:
            with open(SHOWS_FILE, "r", encoding="utf-8") as f:
                shows_data = json.load(f)
        except Exception as e:
            print(f"Error loading {SHOWS_FILE}: {e}")
            shows_data = {}
        for img_id, show in shows_data.items():
            img = images_data.get(int(img_id))
            if img:
                img["Shows"] = show

def save_shows():
    shows = {}
    for img_id, img in images_data.items():
        shows[str(img_id)] = img.get("Shows", 0)
    try:
        with open(SHOWS_FILE, "w", encoding="utf-8") as f:
            json.dump(shows, f, indent=2)
    except Exception as e:
        print(f"Error saving {SHOWS_FILE}: {e}")

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

def get_vram_process_breakdown():
    """Use Windows Performance Counters or nvidia-smi to get per-process VRAM usage, categorized by app.
    Returns dict: { 'stable_diffusion': MB, 'lm_studio': MB, 'system': MB }
    """
    import subprocess
    import sys
    import psutil

    breakdown = {"stable_diffusion": 0.0, "lm_studio": 0.0, "system": 0.0}

    # ── Windows specific fast performance counter method ────────────────────
    if sys.platform == "win32":
        try:
            # Query the local GPU process memory counters using PowerShell
            cmd = [
                "powershell", "-NoProfile", "-Command",
                '(Get-Counter -Counter "\\GPU Process Memory(*)\\Local Usage" -ErrorAction SilentlyContinue).CounterSamples | Where-Object { $_.CookedValue -gt 0 } | ForEach-Object { $pidVal = 0; if ($_.InstanceName -match "pid_(\\d+)") { $pidVal = [int]$Matches[1] }; Write-Output ("{0};{1}" -f $pidVal, ($_.CookedValue / 1MB)) }'
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                pid_map = {}
                for line in res.stdout.strip().splitlines():
                    parts = line.split(";")
                    if len(parts) == 2:
                        try:
                            pid = int(parts[0])
                            mem_mb = float(parts[1].replace(",", "."))
                            if pid > 0:
                                pid_map[pid] = pid_map.get(pid, 0.0) + mem_mb
                        except ValueError:
                            continue

                # Categorize processes using fast psutil lookup
                for pid, mem_mb in pid_map.items():
                    proc_name = ""
                    try:
                        proc_name = psutil.Process(pid).name().lower()
                    except Exception:
                        pass

                    # Categorize based on process name keywords
                    if any(k in proc_name for k in ("python", "forge", "stable", "webui", "sd")):
                        breakdown["stable_diffusion"] += mem_mb
                    elif any(k in proc_name for k in ("lms", "lm studio", "lmstudio")):
                        breakdown["lm_studio"] += mem_mb
                    else:
                        breakdown["system"] += mem_mb

                # Round values for nice display
                for k in breakdown:
                    breakdown[k] = round(breakdown[k], 1)
                return breakdown
        except Exception as e:
            print(f"[VRAM] Windows performance counter query failed: {e}. Falling back to nvidia-smi...")

    # ── Fallback / non-Windows: nvidia-smi method ───────────────────────────
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,used_gpu_memory", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().splitlines()
            for line in lines:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 2:
                    continue
                try:
                    pid = int(parts[0])
                    mem_str = parts[1]
                    if "[n/a]" in mem_str.lower() or "n/a" in mem_str.lower():
                        continue
                    mem_mb = float(mem_str)
                except ValueError:
                    continue

                proc_name = ""
                try:
                    proc_name = psutil.Process(pid).name().lower()
                except Exception:
                    pass

                if any(k in proc_name for k in ("python", "forge", "stable", "webui", "sd")):
                    breakdown["stable_diffusion"] += mem_mb
                elif any(k in proc_name for k in ("lms", "lm studio", "lmstudio")):
                    breakdown["lm_studio"] += mem_mb
                else:
                    breakdown["system"] += mem_mb

            for k in breakdown:
                breakdown[k] = round(breakdown[k], 1)
            return breakdown
    except Exception as e:
        print(f"[VRAM] Fallback nvidia-smi breakdown failed: {e}")

    return None



def get_vram_usage():
    try:
        gpus = GPUtil.getGPUs()
        if not gpus:
            return {"error": "No GPUs found"}
        
        gpu_info = []
        for gpu in gpus:
            # Compute memory_util directly — GPUtil's memoryUtil can return 0 on Windows
            mem_total = gpu.memoryTotal or 1
            mem_used = gpu.memoryUsed or 0
            computed_util = mem_used / mem_total

            gpu_data = {
                "id": gpu.id,
                "name": gpu.name,
                "memory_total": mem_total,
                "memory_used": mem_used,
                "memory_free": gpu.memoryFree,
                "memory_util": computed_util,
                "load": gpu.load,
                "temperature": getattr(gpu, 'temperature', None),
                "breakdown": get_vram_process_breakdown(),
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


def is_vram_high_enough_to_unload(threshold=0.40):
    try:
        gpus = GPUtil.getGPUs()
        if not gpus:
            print("[VRAM] No GPUs found. Assuming we need to unload.")
            return True
        for gpu in gpus:
            util = gpu.memoryUtil
            # Double check with direct calculation
            if gpu.memoryTotal > 0:
                calc_util = gpu.memoryUsed / gpu.memoryTotal
            else:
                calc_util = util
            print(f"[VRAM] GPU {gpu.id} ({gpu.name}): VRAM usage = {calc_util * 100:.1f}%, used = {gpu.memoryUsed}MB, total = {gpu.memoryTotal}MB")
            if calc_util >= threshold:
                return True
        return False
    except Exception as e:
        print(f"[VRAM] Error checking VRAM usage: {e}")
        return True


def unload_sd_models_sync(url="http://127.0.0.1:7860/"):
    import requests
    try:
        # Check VRAM first
        if not is_vram_high_enough_to_unload():
            print("[VRAM] VRAM usage is under 40%. Skipping Stable Diffusion WebUI unload.")
            return False

        print("[VRAM] Unloading Stable Diffusion WebUI models...")
        # Get current model for debug logging before unloading
        current_model = "Unknown"
        try:
            opt_resp = requests.get(url.rstrip("/") + "/sdapi/v1/options", timeout=3)
            if opt_resp.status_code == 200:
                current_model = opt_resp.json().get("sd_model_checkpoint", "Unknown")
        except Exception:
            pass

        resp = requests.post(url.rstrip("/") + "/sdapi/v1/unload-checkpoint", timeout=10)
        if resp.status_code == 200:
            print(f"[VRAM] Unloaded SD model: {current_model}")
            return True
        else:
            print(f"[VRAM] Failed to unload SD models: {resp.status_code}")
            return False
    except Exception as e:
        print(f"[VRAM] Error unloading SD models: {e}")
        return False


def unload_lm_studio_models_sync(base_url="http://127.0.0.1:1234"):
    import requests
    try:
        # Check VRAM first
        if not is_vram_high_enough_to_unload():
            print("[VRAM] VRAM usage is under 40%. Skipping LM Studio unload.")
            return False

        root_url = base_url.rstrip("/")
        if root_url.endswith("/v1"):
            root_url = root_url[:-3]
        
        url = f"{root_url}/api/v1/models"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            models = data.get("models", [])
            unloaded_any = False
            for m in models:
                loaded_instances = m.get("loaded_instances", [])
                for inst in loaded_instances:
                    inst_id = inst.get("instance_id")
                    if inst_id:
                        print(f"[VRAM] Unloading LM Studio model instance: {inst_id}...")
                        unload_url = f"{root_url}/api/v1/models/unload"
                        unload_resp = requests.post(unload_url, json={"instance_id": inst_id}, timeout=15)
                        if unload_resp.status_code == 200:
                            print(f"[VRAM] Unloaded model {inst_id}")
                            unloaded_any = True
                        else:
                            print(f"[VRAM] Failed to unload model {inst_id}: {unload_resp.status_code}")
            if not unloaded_any:
                print("[VRAM] No loaded LM Studio models found to unload.")
            return unloaded_any
        else:
            print(f"[VRAM] Failed to get LM Studio models: {resp.status_code}")
            return False
    except Exception as e:
        print(f"[VRAM] Error unloading LM Studio models: {e}")
        return False

_hashing_thread_started = False
_hashing_thread_lock = threading.Lock()

def start_background_file_hashing():
    global _hashing_thread_started
    with _hashing_thread_lock:
        if _hashing_thread_started:
            return
        _hashing_thread_started = True

    def _run_hashing():
        import hashlib
        print("[Hash Engine] Starting background file hashing...")
        images_to_hash = []
        with _data_lock:
            images_to_hash = list(raw_all_images)

        updated_any = False
        count = 0
        for img in images_to_hash:
            if "FileHash" not in img:
                path = img.get("Path")
                if not path:
                    continue
                abs_path = path
                if abs_path.startswith("/files/"):
                    abs_path = abs_path.replace("/files", api_file_root)
                if os.path.exists(abs_path):
                    h = hashlib.sha256()
                    try:
                        with open(abs_path, 'rb') as file:
                            while chunk := file.read(8192):
                                h.update(chunk)
                        file_hash = h.hexdigest()
                        img["FileHash"] = file_hash
                        updated_any = True
                        count += 1
                    except Exception:
                        pass
                time.sleep(0.005)

                if count > 0 and count % 500 == 0:
                    print(f"[Hash Engine] Populated {count} file hashes, writing database...")
                    try:
                        save_images()
                    except Exception as se:
                        print(f"[Hash Engine] Error saving images during background hash: {se}")

        if updated_any:
            print(f"[Hash Engine] Background hashing complete. Populated {count} hashes. Saving database...")
            try:
                save_images()
            except Exception as se:
                print(f"[Hash Engine] Error saving database at completion: {se}")
        else:
            print("[Hash Engine] No missing hashes to populate.")

        global _hashing_thread_started
        with _hashing_thread_lock:
            _hashing_thread_started = False

    threading.Thread(target=_run_hashing, daemon=True, name="bg-file-hashing").start()
