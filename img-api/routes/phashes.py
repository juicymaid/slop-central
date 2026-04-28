from fastapi import APIRouter
import os
import json
from utils import images_data, compute_phash  # Changed import from main to utils

router = APIRouter()


@router.post("/calculate-phashes")
def calculate_phashes():
    # Calculate pHash for each image and save to hashes.json.
    phashes = {}

    #get list of images without pHash
    calculated_phashes = {}
    #load from hashes.json if it exists
    if os.path.exists("hashes.json"):
        with open("hashes.json", "r", encoding="utf-8") as f:
            calculated_phashes = json.load(f)
            
    images_without_phash = []
    for img_id, img in images_data.items():
        if img.get("pHash") is None and img_id not in calculated_phashes:
            images_without_phash.append(img)
        

    images_processed = 0
    last_percentage = -1
    for image in images_without_phash:
        path = image.get("Path")
        if(path.startswith("/files/")):
            path = path.replace("/files/", "H:/ent/ai/NewFolder/img-api/files/")
            
        if path and os.path.exists(path):
            ph = compute_phash(path)
            percentage = int(images_processed / len(images_without_phash) * 100)
            if percentage != last_percentage:
                print(f"Progress: [{percentage:3d}%]")
                last_percentage = percentage
            images_processed += 1
            phashes[image["Id"]] = ph
        else:
            phashes[image["Id"]] = None
    with open("hashes.json", "w", encoding="utf-8") as f:
        json.dump(phashes, f, indent=2)
    return {"message": "Phashes calculated and saved", "phashes": phashes}
