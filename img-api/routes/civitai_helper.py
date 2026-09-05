import asyncio
import hashlib
import io
import json
import os
import re
import time
from typing import Any, Dict, List, Optional
import urllib.parse

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel
from PIL import Image
import requests
import utils

router = APIRouter(prefix="/civitai-helper", tags=["Civitai Helper"])

# Supported file extensions for models
MODEL_EXTENSIONS = (".safetensors", ".ckpt", ".pt", ".bin")

# Global scan status and locks
_scan_state_lock = asyncio.Lock()
scan_state: Dict[str, Any] = {
    "status": "idle",  # idle, running, completed, error, cancelled
    "total": 0,
    "processed": 0,
    "successful": 0,
    "failed": 0,
    "skipped": 0,
    "percent": 0,
    "current_model": "",
    "current_type": "",
    "message": "System ready",
    "logs": [],
    "results": [],
    "start_time": None,
    "end_time": None,
}
_cancel_requested = False


def _append_log(msg: str, log_type: str = "info"):
    """Append a timestamped log entry to the scan state."""
    timestamp = time.strftime("%H:%M:%S")
    entry = {"time": timestamp, "type": log_type, "message": msg}
    scan_state["logs"].append(entry)
    # Keep last 200 logs
    if len(scan_state["logs"]) > 200:
        scan_state["logs"] = scan_state["logs"][-200:]
    print(f"[CivitaiHelper] [{log_type.upper()}] {msg}")


def get_model_folders() -> Dict[str, List[str]]:
    """Return dictionary of folders for each model type."""
    loras_dir = os.getenv("LORAS_DIR", "/mnt/SSD/ai/Data/Models/Lora")
    models_dir = os.getenv("MODELS_DIR", "/mnt/SSD/ai/Data/Models/StableDiffusion")

    # Also check WebUI / Forge directories if present
    forge_dir = os.getenv("FORGE_DIR", "/mnt/SSD/ai/Data/Packages/Stable Diffusion WebUI Forge - Neo")
    extra_loras = []
    extra_checkpoints = []

    if os.path.exists(forge_dir):
        forge_loras = os.path.join(forge_dir, "models", "Lora")
        if os.path.exists(forge_loras) and os.path.abspath(forge_loras) != os.path.abspath(loras_dir):
            extra_loras.append(forge_loras)
        forge_ckp = os.path.join(forge_dir, "models", "Stable-diffusion")
        if os.path.exists(forge_ckp) and os.path.abspath(forge_ckp) != os.path.abspath(models_dir):
            extra_checkpoints.append(forge_ckp)

    lora_folders = [loras_dir] + extra_loras
    checkpoint_folders = [models_dir] + extra_checkpoints

    return {
        "lora": [f for f in lora_folders if os.path.exists(f)],
        "checkpoint": [f for f in checkpoint_folders if os.path.exists(f)],
    }


def compute_sha256(filepath: str, blocksize: int = 1024 * 1024) -> str:
    """Compute SHA256 of file in 1MB chunks."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(blocksize):
            hasher.update(chunk)
    return hasher.hexdigest().upper()


def compute_autov2(sha256_hash: str) -> str:
    """Compute AutoV2 10-char hash from SHA256."""
    return sha256_hash[:10].upper()


def get_nsfw_score(img: Dict[str, Any]) -> int:
    """Calculate numeric NSFW score for an image.
    
    Civitai nsfwLevel bitfield:
    32 = Blocked
    16 = XXX
    8  = X
    4  = Mature / R
    2  = Soft / PG-13
    1  = None / PG
    """
    level = img.get("nsfwLevel")
    if isinstance(level, (int, float)):
        return int(level)

    nsfw_str = str(img.get("nsfw") or "").strip().lower()
    mapping = {
        "blocked": 32,
        "xxx": 16,
        "x": 8,
        "mature": 4,
        "soft": 2,
        "pg13": 2,
        "pg": 1,
        "none": 1,
        "true": 8,
        "false": 1,
    }
    return mapping.get(nsfw_str, 1)


def select_highest_nsfw_image(images: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Select the image with the highest NSFW level from a list of images."""
    if not images:
        return None
    # Sort images by NSFW score descending
    ranked = sorted(images, key=get_nsfw_score, reverse=True)
    return ranked[0]


def fetch_civitai_model_version_by_hash(
    file_hash: str, domain: str = "civitai.com", api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Query Civitai API by model hash (SHA256 or AutoV2)."""
    url = f"https://{domain}/api/v1/model-versions/by-hash/{file_hash}"
    headers = {"User-Agent": "Pinthesis-CivitaiHelper/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 404:
            return None
        else:
            print(f"[CivitaiHelper] Civitai returned status {resp.status_code} for hash {file_hash}")
            return None
    except Exception as e:
        print(f"[CivitaiHelper] Error querying Civitai for hash {file_hash}: {e}")
        return None


def fetch_civitai_model_version_by_id(
    version_id: int, domain: str = "civitai.com", api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Query Civitai API by model version ID."""
    url = f"https://{domain}/api/v1/model-versions/{version_id}"
    headers = {"User-Agent": "Pinthesis-CivitaiHelper/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as e:
        print(f"[CivitaiHelper] Error querying model version {version_id}: {e}")
        return None


def fetch_civitai_model_by_id(
    model_id: int, domain: str = "civitai.com", api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Query Civitai API by model ID."""
    url = f"https://{domain}/api/v1/models/{model_id}"
    headers = {"User-Agent": "Pinthesis-CivitaiHelper/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as e:
        print(f"[CivitaiHelper] Error querying model {model_id}: {e}")
        return None


def parse_civitai_url_or_id(input_str: str) -> Dict[str, Optional[int]]:
    """Extract modelId and modelVersionId from URL or numeric ID."""
    input_str = input_str.strip()
    result = {"model_id": None, "version_id": None}

    if input_str.isdigit():
        result["model_id"] = int(input_str)
        return result

    # Check for modelVersionId query param
    parsed = urllib.parse.urlparse(input_str)
    if parsed.query:
        qs = urllib.parse.parse_qs(parsed.query)
        if "modelVersionId" in qs and qs["modelVersionId"][0].isdigit():
            result["version_id"] = int(qs["modelVersionId"][0])

    # Check for /models/12345 pattern
    model_match = re.search(r"/models/(\d+)", parsed.path)
    if model_match:
        result["model_id"] = int(model_match.group(1))

    # Check for /model-versions/12345 pattern
    version_match = re.search(r"/model-versions/(\d+)", parsed.path)
    if version_match:
        result["version_id"] = int(version_match.group(1))

    return result


def download_and_save_preview_image(
    image_url: str,
    target_path: str,
    max_size: bool = True,
    api_key: Optional[str] = None,
) -> bool:
    """Download preview image from URL and save as PNG."""
    headers = {"User-Agent": "Pinthesis-CivitaiHelper/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    url = image_url
    if max_size and "image.civitai.com" in url:
        # Request maximum quality / original image
        if "/width=" in url:
            url = re.sub(r"/width=\d+/", "/original=true/", url)
        elif "/original=false/" in url:
            url = url.replace("/original=false/", "/original=true/")

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code != 200:
            print(f"[CivitaiHelper] Failed to download preview image {url}: status {resp.status_code}")
            return False

        # Open with Pillow and convert to RGB PNG
        img = Image.open(io.BytesIO(resp.content))
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        img.convert("RGB").save(target_path, format="PNG")

        # Also save .preview.png for compatibility if target is .png
        if target_path.endswith(".png") and not target_path.endswith(".preview.png"):
            preview_alt = target_path.replace(".png", ".preview.png")
            try:
                img.convert("RGB").save(preview_alt, format="PNG")
            except Exception:
                pass

        return True
    except Exception as e:
        print(f"[CivitaiHelper] Error processing preview image {url}: {e}")
        return False


def save_model_metadata(
    model_path: str,
    version_data: Dict[str, Any],
    model_data: Optional[Dict[str, Any]] = None,
    sha256_hash: Optional[str] = None,
) -> str:
    """Save metadata to <model_name>.civitai.info."""
    base_path = os.path.splitext(model_path)[0]
    info_path = f"{base_path}.civitai.info"

    parent_model = version_data.get("model", {})
    if model_data:
        parent_model_info = {
            "name": model_data.get("name"),
            "type": model_data.get("type"),
            "nsfw": model_data.get("nsfw"),
            "poi": model_data.get("poi"),
            "description": model_data.get("description"),
            "tags": model_data.get("tags", []),
        }
    else:
        parent_model_info = {
            "name": parent_model.get("name") or version_data.get("name"),
            "type": parent_model.get("type"),
            "nsfw": parent_model.get("nsfw"),
            "poi": parent_model.get("poi"),
            "description": parent_model.get("description"),
            "tags": parent_model.get("tags", []),
        }

    civitai_info = {
        "id": version_data.get("id"),
        "modelId": version_data.get("modelId"),
        "name": version_data.get("name"),
        "trainedWords": version_data.get("trainedWords", []),
        "baseModel": version_data.get("baseModel"),
        "description": version_data.get("description"),
        "model": parent_model_info,
        "images": version_data.get("images", []),
        "files": version_data.get("files", []),
        "downloadUrl": version_data.get("downloadUrl"),
        "sha256": sha256_hash,
    }

    os.makedirs(os.path.dirname(os.path.abspath(info_path)), exist_ok=True)
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(civitai_info, f, indent=2, ensure_ascii=False)

    return info_path


# Request Models
class ScanRequest(BaseModel):
    model_types: List[str] = ["lora", "checkpoint"]
    skip_existing: bool = True
    download_preview: bool = True
    max_size_preview: bool = True
    civitai_domain: str = "civitai.com"
    api_key: Optional[str] = None


class FetchByUrlRequest(BaseModel):
    model_path: str
    url_or_id: str
    download_preview: bool = True
    max_size_preview: bool = True
    civitai_domain: str = "civitai.com"
    api_key: Optional[str] = None


class SaveConfigRequest(BaseModel):
    civitai_domain: str = "civitai.com"
    civitai_api_key: Optional[str] = ""
    max_size_preview: bool = True
    skip_existing: bool = True


# Endpoints
@router.get("/config")
def get_config():
    """Get Civitai Helper configuration and folder paths."""
    folders = get_model_folders()
    api_key = ""
    domain = "civitai.com"
    try:
        from utils import get_db_connection
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT key, value FROM settings WHERE key IN ('civitai_api_key', 'civitai_domain')")
        for row in c.fetchall():
            if row["key"] == "civitai_api_key":
                api_key = json.loads(row["value"])
            elif row["key"] == "civitai_domain":
                domain = json.loads(row["value"])
        conn.close()
    except Exception:
        pass

    return {
        "folders": folders,
        "civitai_domain": domain,
        "has_api_key": bool(api_key),
    }


@router.post("/save-config")
def save_config(req: SaveConfigRequest):
    """Save Civitai Helper configuration to settings table."""
    try:
        from utils import get_db_connection
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("civitai_domain", json.dumps(req.civitai_domain)),
        )
        if req.civitai_api_key is not None:
            c.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("civitai_api_key", json.dumps(req.civitai_api_key)),
            )
        conn.commit()
        conn.close()
        return {"message": "Config saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {e}")


@router.get("/status")
def get_status():
    """Get current scan status, progress, and logs."""
    return scan_state


@router.post("/cancel")
def cancel_scan():
    """Cancel any active Civitai scan."""
    global _cancel_requested
    if scan_state["status"] == "running":
        _cancel_requested = True
        _append_log("Cancellation requested by user", "warning")
        return {"message": "Scan cancellation requested"}
    return {"message": "No active scan to cancel"}


@router.get("/local-models")
def get_local_models(
    type: str = Query("all", description="Model type: all, lora, checkpoint"),
    missing_only: bool = Query(False, description="Only show models missing info or preview"),
):
    """List all local models with their Civitai metadata status."""
    folders = get_model_folders()
    types_to_scan = ["lora", "checkpoint"] if type == "all" else [type]
    results = []

    for m_type in types_to_scan:
        dir_list = folders.get(m_type, [])
        for base_dir in dir_list:
            if not os.path.exists(base_dir):
                continue
            for root, _, files in os.walk(base_dir):
                for file in files:
                    if file.lower().endswith(MODEL_EXTENSIONS):
                        full_path = os.path.join(root, file)
                        base_no_ext = os.path.splitext(full_path)[0]
                        info_file = f"{base_no_ext}.civitai.info"
                        preview_file_png = f"{base_no_ext}.png"
                        preview_file_alt = f"{base_no_ext}.preview.png"

                        has_info = os.path.isfile(info_file)
                        has_preview = os.path.isfile(preview_file_png) or os.path.isfile(preview_file_alt)

                        if missing_only and has_info and has_preview:
                            continue

                        civitai_name = None
                        trained_words = []
                        if has_info:
                            try:
                                with open(info_file, "r", encoding="utf-8") as f:
                                    c_info = json.load(f)
                                    civitai_name = c_info.get("model", {}).get("name") or c_info.get("name")
                                    trained_words = c_info.get("trainedWords", [])
                            except Exception:
                                pass

                        try:
                            size_mb = round(os.path.getsize(full_path) / (1024 * 1024), 1)
                            modified = int(os.path.getmtime(full_path))
                        except Exception:
                            size_mb = 0
                            modified = 0

                        rel_path = os.path.relpath(full_path, base_dir)

                        results.append({
                            "name": file,
                            "filename": file,
                            "path": full_path,
                            "rel_path": rel_path,
                            "type": m_type,
                            "has_info": has_info,
                            "has_preview": has_preview,
                            "civitai_name": civitai_name,
                            "trained_words": trained_words,
                            "size_mb": size_mb,
                            "modified": modified,
                        })

    # Sort alphabetically by name
    results.sort(key=lambda x: x["name"].lower())
    return {
        "total": len(results),
        "models": results,
    }


@router.post("/scan")
def start_scan(req: ScanRequest, background_tasks: BackgroundTasks):
    """Start scanning local models for Civitai info and highest NSFW cover art."""
    global _cancel_requested

    if scan_state["status"] == "running":
        raise HTTPException(status_code=400, detail="Scan already in progress")

    _cancel_requested = False
    background_tasks.add_task(_run_civitai_scan, req)
    return {"message": "Civitai model scan started in background"}


@router.post("/fetch-model-by-url")
def fetch_model_by_url(req: FetchByUrlRequest):
    """Fetch Civitai metadata and highest NSFW cover art for a specific local model."""
    if not os.path.isfile(req.model_path):
        raise HTTPException(status_code=404, detail=f"Model file not found: {req.model_path}")

    parsed = parse_civitai_url_or_id(req.url_or_id)
    version_data = None
    model_data = None

    if parsed["version_id"]:
        version_data = fetch_civitai_model_version_by_id(
            parsed["version_id"], domain=req.civitai_domain, api_key=req.api_key
        )
        if version_data and version_data.get("modelId"):
            model_data = fetch_civitai_model_by_id(
                version_data["modelId"], domain=req.civitai_domain, api_key=req.api_key
            )
    elif parsed["model_id"]:
        model_data = fetch_civitai_model_by_id(
            parsed["model_id"], domain=req.civitai_domain, api_key=req.api_key
        )
        if model_data and model_data.get("modelVersions"):
            # Use the first/latest model version
            version_data = model_data["modelVersions"][0]

    if not version_data:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find model on Civitai from input: {req.url_or_id}",
        )

    # Compute SHA256 for local reference
    sha256_hash = compute_sha256(req.model_path)

    # Save metadata
    info_path = save_model_metadata(
        req.model_path, version_data, model_data=model_data, sha256_hash=sha256_hash
    )

    # Download preview image with highest NSFW level
    preview_downloaded = False
    preview_path = f"{os.path.splitext(req.model_path)[0]}.png"
    selected_img_info = None

    if req.download_preview:
        images = version_data.get("images", [])
        if not images and model_data:
            images = model_data.get("images", [])

        best_img = select_highest_nsfw_image(images)
        if best_img and best_img.get("url"):
            selected_img_info = {
                "url": best_img.get("url"),
                "nsfw_level": get_nsfw_score(best_img),
            }
            preview_downloaded = download_and_save_preview_image(
                best_img["url"],
                preview_path,
                max_size=req.max_size_preview,
                api_key=req.api_key,
            )

    return {
        "message": "Successfully fetched model info and cover art",
        "model_name": version_data.get("name") or (model_data.get("name") if model_data else "Unknown"),
        "model_id": version_data.get("modelId"),
        "version_id": version_data.get("id"),
        "info_path": info_path,
        "preview_path": preview_path if preview_downloaded else None,
        "preview_downloaded": preview_downloaded,
        "selected_image": selected_img_info,
        "trained_words": version_data.get("trainedWords", []),
    }


def _run_civitai_scan(req: ScanRequest):
    """Background worker for scanning models and fetching Civitai info."""
    global scan_state, _cancel_requested

    scan_state["status"] = "running"
    scan_state["total"] = 0
    scan_state["processed"] = 0
    scan_state["successful"] = 0
    scan_state["failed"] = 0
    scan_state["skipped"] = 0
    scan_state["percent"] = 0
    scan_state["current_model"] = ""
    scan_state["current_type"] = ""
    scan_state["message"] = "Discovering local model files..."
    scan_state["logs"] = []
    scan_state["results"] = []
    scan_state["start_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    scan_state["end_time"] = None

    _append_log(f"Starting scan for model types: {', '.join(req.model_types)}")

    try:
        folders = get_model_folders()
        files_to_process: List[Dict[str, Any]] = []

        for m_type in req.model_types:
            dir_list = folders.get(m_type, [])
            for base_dir in dir_list:
                if not os.path.exists(base_dir):
                    _append_log(f"Directory not found: {base_dir}", "warning")
                    continue

                _append_log(f"Scanning folder ({m_type}): {base_dir}")
                for root, _, files in os.walk(base_dir):
                    for file in files:
                        if file.lower().endswith(MODEL_EXTENSIONS):
                            full_path = os.path.join(root, file)
                            base_no_ext = os.path.splitext(full_path)[0]
                            info_file = f"{base_no_ext}.civitai.info"
                            preview_file_png = f"{base_no_ext}.png"
                            preview_file_alt = f"{base_no_ext}.preview.png"

                            has_info = os.path.isfile(info_file)
                            has_preview = (
                                os.path.isfile(preview_file_png)
                                or os.path.isfile(preview_file_alt)
                            )

                            if req.skip_existing and has_info and has_preview:
                                continue

                            files_to_process.append({
                                "name": file,
                                "path": full_path,
                                "type": m_type,
                                "has_info": has_info,
                                "has_preview": has_preview,
                            })

        scan_state["total"] = len(files_to_process)
        _append_log(f"Found {len(files_to_process)} model files to check.")

        if not files_to_process:
            scan_state["status"] = "completed"
            scan_state["message"] = "No models needed scanning (all up to date or empty folders)."
            _append_log("No models to scan. Done.", "success")
            scan_state["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            return

        for idx, item in enumerate(files_to_process):
            if _cancel_requested:
                scan_state["status"] = "cancelled"
                scan_state["message"] = "Scan cancelled by user."
                _append_log("Scan cancelled by user.", "warning")
                break

            m_name = item["name"]
            m_path = item["path"]
            m_type = item["type"]

            scan_state["current_model"] = m_name
            scan_state["current_type"] = m_type
            scan_state["processed"] = idx + 1
            scan_state["percent"] = round(((idx + 1) / len(files_to_process)) * 100, 1)
            scan_state["message"] = f"Processing [{idx + 1}/{len(files_to_process)}]: {m_name}"

            _append_log(f"[{idx + 1}/{len(files_to_process)}] Calculating hash for {m_name}...")

            try:
                # 1. Calculate SHA256
                sha256_hash = compute_sha256(m_path)
                autov2_hash = compute_autov2(sha256_hash)

                # 2. Query Civitai API by SHA256
                version_data = fetch_civitai_model_version_by_hash(
                    sha256_hash, domain=req.civitai_domain, api_key=req.api_key
                )

                # Fallback to AutoV2 if not found
                if not version_data:
                    _append_log(f"SHA256 not found, trying AutoV2 ({autov2_hash}) for {m_name}...")
                    version_data = fetch_civitai_model_version_by_hash(
                        autov2_hash, domain=req.civitai_domain, api_key=req.api_key
                    )

                if not version_data:
                    scan_state["failed"] += 1
                    _append_log(f"No Civitai match for {m_name} (Hash: {autov2_hash})", "warning")
                    scan_state["results"].append({
                        "name": m_name,
                        "path": m_path,
                        "type": m_type,
                        "status": "not_found",
                        "hash": autov2_hash,
                    })
                    continue

                # 3. If version found, fetch parent model details if available
                model_id = version_data.get("modelId")
                model_data = None
                if model_id:
                    model_data = fetch_civitai_model_by_id(
                        model_id, domain=req.civitai_domain, api_key=req.api_key
                    )

                # 4. Save metadata .civitai.info
                save_model_metadata(
                    m_path, version_data, model_data=model_data, sha256_hash=sha256_hash
                )

                # 5. Pick highest NSFW cover art and download
                preview_status = "skipped"
                if req.download_preview:
                    images = version_data.get("images", [])
                    if not images and model_data:
                        images = model_data.get("images", [])

                    best_img = select_highest_nsfw_image(images)
                    if best_img and best_img.get("url"):
                        nsfw_level = get_nsfw_score(best_img)
                        preview_path = f"{os.path.splitext(m_path)[0]}.png"
                        dl_ok = download_and_save_preview_image(
                            best_img["url"],
                            preview_path,
                            max_size=req.max_size_preview,
                            api_key=req.api_key,
                        )
                        preview_status = f"downloaded (NSFW level {nsfw_level})" if dl_ok else "download_failed"
                        _append_log(
                            f"Downloaded cover art for {m_name} (Highest NSFW level: {nsfw_level})",
                            "success" if dl_ok else "warning",
                        )

                matched_name = (
                    version_data.get("name")
                    or (model_data.get("name") if model_data else None)
                    or m_name
                )
                scan_state["successful"] += 1
                _append_log(f"Successfully updated Civitai info for: {matched_name}", "success")

                scan_state["results"].append({
                    "name": m_name,
                    "civitai_name": matched_name,
                    "path": m_path,
                    "type": m_type,
                    "status": "success",
                    "model_id": model_id,
                    "version_id": version_data.get("id"),
                    "preview": preview_status,
                    "trained_words": version_data.get("trainedWords", []),
                })

                # Polite rate-limiting sleep between Civitai API calls
                time.sleep(0.3)

            except Exception as item_err:
                scan_state["failed"] += 1
                _append_log(f"Error processing {m_name}: {item_err}", "error")

        if not _cancel_requested:
            scan_state["status"] = "completed"
            scan_state["message"] = (
                f"Scan complete! Processed {scan_state['processed']} models: "
                f"{scan_state['successful']} updated, {scan_state['failed']} not found/failed."
            )
            _append_log(
                f"Scan finished: {scan_state['successful']} succeeded, {scan_state['failed']} failed.",
                "success",
            )

    except Exception as e:
        scan_state["status"] = "error"
        scan_state["message"] = f"Fatal scan error: {str(e)}"
        _append_log(f"Scan aborted due to error: {str(e)}", "error")
    finally:
        scan_state["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
