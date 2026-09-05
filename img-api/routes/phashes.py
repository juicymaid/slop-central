from fastapi import APIRouter, BackgroundTasks, HTTPException
import os
import json
import utils
from utils import images_data, compute_phash

router = APIRouter()

phash_status = {
    "status": "idle",  # idle, running, completed, error
    "processed": 0,
    "total": 0,
    "percent": 0,
    "message": "Ready to calculate pHashes",
}


@router.get("/phash-status")
def get_phash_status():
    """Get the current status and progress of pHash calculation."""
    return phash_status


@router.post("/calculate-phashes")
def calculate_phashes(background_tasks: BackgroundTasks):
    """Start calculating perceptual hashes in the background."""
    global phash_status
    if phash_status["status"] == "running":
        raise HTTPException(status_code=400, detail="pHash calculation already in progress")

    phash_status["status"] = "running"
    phash_status["processed"] = 0
    phash_status["total"] = 0
    phash_status["percent"] = 0
    phash_status["message"] = "Scanning for images needing pHash..."

    background_tasks.add_task(background_calculate_phashes)
    return {"message": "pHash calculation started in background", "status": phash_status}


def background_calculate_phashes():
    """Background worker to calculate pHash for all images."""
    global phash_status
    try:
        utils.ensure_loaded()
        phashes = {}

        # Load existing from hashes.json if it exists
        if os.path.exists("hashes.json"):
            try:
                with open("hashes.json", "r", encoding="utf-8") as f:
                    phashes = json.load(f)
            except Exception:
                phashes = {}

        images_without_phash = []
        for img_id, img in images_data.items():
            if img.get("pHash") is None and str(img_id) not in phashes and img_id not in phashes:
                images_without_phash.append(img)

        total = len(images_without_phash)
        phash_status["total"] = total

        if total == 0:
            phash_status["status"] = "completed"
            phash_status["percent"] = 100
            phash_status["message"] = "All images already have pHash calculated."
            print("[pHash] All images already have pHash.")
            return

        print(f"[pHash] Found {total} images needing pHash calculation.")
        images_processed = 0

        for idx, image in enumerate(images_without_phash):
            path = image.get("Path")
            if path and path.startswith("/files"):
                path = path.replace("/files", utils.api_file_root)

            img_id = image.get("Id")
            if path and os.path.exists(path):
                try:
                    ph = compute_phash(path)
                    phashes[str(img_id)] = ph
                    image["pHash"] = ph
                except Exception as e:
                    print(f"[pHash] Error computing pHash for {path}: {e}")
                    phashes[str(img_id)] = None
            else:
                phashes[str(img_id)] = None

            images_processed += 1
            percent = int((images_processed / total) * 100)
            phash_status["processed"] = images_processed
            phash_status["percent"] = percent
            phash_status["message"] = f"Calculating pHash: {images_processed} / {total} ({percent}%)"

            # Periodically write to file
            if images_processed % 50 == 0 or images_processed == total:
                try:
                    with open("hashes.json", "w", encoding="utf-8") as f:
                        json.dump(phashes, f, indent=2)
                except Exception as save_err:
                    print(f"[pHash] Error saving hashes.json: {save_err}")

        # Final save
        with open("hashes.json", "w", encoding="utf-8") as f:
            json.dump(phashes, f, indent=2)

        phash_status["status"] = "completed"
        phash_status["percent"] = 100
        phash_status["message"] = f"Finished! Calculated pHashes for {images_processed} images."
        print(f"[pHash] Complete: {images_processed} images processed.")

    except Exception as e:
        phash_status["status"] = "error"
        phash_status["message"] = f"Error during pHash calculation: {str(e)}"
        print(f"[pHash] Fatal error: {e}")
