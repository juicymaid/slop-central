from fastapi import APIRouter, Query, HTTPException, Body, WebSocket, WebSocketDisconnect
from PIL import Image
import os
import json
import utils
from sd_parsers import ParserManager
import asyncio
from fastapi import BackgroundTasks
import main
import httpx
from routes import models

router = APIRouter()

folders = [
    r"E:\unity\cache\_\ai\stable-diffusion-webui\outputs",
    r"H:\ent\ai\StabilityMatrix\Packages\ComfyUI\output",
]

scan_inprogress = False
retrieved_unscanned_images = False
images_to_scan = []
scanned_images = []
all_files = 0
files_found = 0
error = False
active_connections = []

@router.websocket("/ws/scan")
async def websocket_scan(websocket: WebSocket):
    global scan_inprogress, active_connections

    await websocket.accept()
    active_connections.append(websocket)

    try:
        if scan_inprogress:
            await websocket.send_json({
                "type": "error",
                "message": "Scan already in progress"
            })
            return

        scan_inprogress = True

        # Send initial status
        await websocket.send_json({
            "type": "status",
            "status": "starting",
            "message": "Starting scan process"
        })

        # Run the scan in a background thread so the websocket stays responsive
        await asyncio.to_thread(websocket_scan_images_sync, websocket)
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)

def websocket_scan_images_sync(websocket: WebSocket):
    # This function is now synchronous and will be run in a thread
    # Use asyncio.run to call async functions if needed
    asyncio.run(_websocket_scan_images_sync(websocket))

async def _websocket_scan_images_sync(websocket: WebSocket):
    global images_to_scan, scan_inprogress, scanned_images, retrieved_unscanned_images, error

    # Reset scan state
    retrieved_unscanned_images = False
    scanned_images = []
    error = False

    try:
        await websocket.send_json({
            "type": "status",
            "status": "retrieving_files",
            "message": "Retrieving unscanned images..."
        })

        images_to_scan = await get_all_unscanned_images()
        retrieved_unscanned_images = True

        await websocket.send_json({
            "type": "status",
            "status": "files_found",
            "message": f"Found {len(images_to_scan)} unscanned images",
            "total_files": len(images_to_scan)
        })

        processed_count = 0
        success_count = 0

        batch_size = 10
        total_batches = (len(images_to_scan) + batch_size - 1) // batch_size

        for batch_index in range(total_batches):
            start_idx = batch_index * batch_size
            end_idx = min(start_idx + batch_size, len(images_to_scan))
            batch = images_to_scan[start_idx:end_idx]

            # Run get_metadata in threads to avoid blocking
            tasks = [asyncio.to_thread(get_metadata_sync, image_path) for image_path in batch]
            batch_results = await asyncio.gather(*tasks)

            for metadata in batch_results:
                processed_count += 1

                if metadata:
                    success_count += 1
                    scanned_images.append(metadata)

                    await websocket.send_json({
                        "type": "image_discovered",
                        "processed": processed_count,
                        "successful": success_count,
                        "total": len(images_to_scan),
                        "percent": round(processed_count / len(images_to_scan) * 100, 1),
                        "image_path": metadata.get("Path", "Unknown")
                    })
                else:
                    await websocket.send_json({
                        "type": "image_failed",
                        "processed": processed_count,
                        "successful": success_count,
                        "total": len(images_to_scan),
                        "percent": round(processed_count / len(images_to_scan) * 100, 1)
                    })

                if processed_count % 5 == 0 or processed_count == len(images_to_scan):
                    await websocket.send_json({
                        "type": "progress",
                        "processed": processed_count,
                        "successful": success_count,
                        "total": len(images_to_scan),
                        "percent": round(processed_count / len(images_to_scan) * 100, 1),
                        "latest_file": metadata.get("Path", "Unknown") if metadata else "Unknown"
                    })

        highest_id = 0
        if utils.all_images:
            highest_id = max(image["Id"] for image in utils.all_images)

        for index, metadata in enumerate(scanned_images):
            metadata["Id"] = highest_id + 1 + index

        await websocket.send_json({
            "type": "status",
            "status": "saving",
            "message": f"Saving {len(scanned_images)} new images..."
        })

        all_images = []
        if os.path.exists(utils.IMAGES_FILE):
            with open(utils.IMAGES_FILE, "r", encoding="utf-8") as f:
                all_images = json.load(f)

        start_id = 0
        if all_images:
            start_id = max(image["Id"] for image in all_images)

        all_images.extend(scanned_images)
        with open(utils.IMAGES_FILE, "w", encoding="utf-8") as f:
            json.dump(all_images, f, indent=2)

        utils.load_images()

        await websocket.send_json({
            "type": "complete",
            "status": "completed",
            "message": "Scan completed successfully",
            "total_processed": processed_count,
            "total_added": len(scanned_images),
            "start_id": start_id,
        })

    except Exception as e:
        error = True
        print(f"Error during scan: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        scan_inprogress = False

def get_metadata_sync(file_path):
    # Synchronous wrapper for get_metadata
    return asyncio.run(get_metadata(file_path))

@router.post("/start-scan")
def start_scan(background_tasks: BackgroundTasks):
    global scan_inprogress, retrieved_unscanned_images, error
    
    if scan_inprogress:
        raise HTTPException(status_code=400, detail="Scan already in progress")
    
    scan_inprogress = True
    retrieved_unscanned_images = False
    error = False
    
    # Run the scanning process in the background
    background_tasks.add_task(background_scan_images)
    return {"message": "Scan started in background"}

async def background_scan_images():
    global images_to_scan, scan_inprogress, scanned_images, retrieved_unscanned_images, error
    try:
        print("Retrieving unscanned images...")
        images_to_scan = await get_all_unscanned_images()
        retrieved_unscanned_images = True
        print(f"Found {len(images_to_scan)} unscanned images")

        async def scan_single_image(image_path):
            try:
                print(f"[{len(scanned_images)}/{len(images_to_scan)}] Scanning image:", image_path)
                metadata = await get_metadata(image_path)
                if metadata:
                    return metadata
                return None
            except Exception as img_error:
                print(f"Error processing image {image_path}: {img_error}")
                return None

        tasks = [asyncio.create_task(scan_single_image(image_path)) for image_path in images_to_scan]
        results = await asyncio.gather(*tasks)

        highest_id = 0
        if utils.all_images:
            highest_id = max(image["Id"] for image in utils.all_images)

        for metadata in results:
            if metadata:
                metadata["Id"] = highest_id + 1
                highest_id += 1
                scanned_images.append(metadata)
                print(f"[{len(scanned_images)}/{len(images_to_scan)}] Prompt:  {metadata['Prompt']}")

        all_images = []
        if os.path.exists(utils.IMAGES_FILE):
            with open(utils.IMAGES_FILE, "r", encoding="utf-8") as f:
                all_images = json.load(f)

        all_images.extend(scanned_images)
        with open(utils.IMAGES_FILE, "w", encoding="utf-8") as f:
            json.dump(all_images, f, indent=2)

        print("Scan completed. Images saved to images.json")
        utils.load_images()
        print("Images reloaded into memory")

    except Exception as e:
        print("Error occurred during scanning:", e)
        error = True
    finally:
        scan_inprogress = False

@router.get("/scan-status")
def get_scan_status():
    return{
        "scan_inprogress": scan_inprogress,
        "retrieved_unscanned_images": retrieved_unscanned_images,
        "images_to_scan": len(images_to_scan) if retrieved_unscanned_images else 0,
        "scanned_images": len(scanned_images) if retrieved_unscanned_images else 0,
        "new_images": [img["Path"] for img in scanned_images] if retrieved_unscanned_images else [],
        "all_files": all_files,
        "files_checked": files_found,
        "error": error,
    }

@router.get("/unscanned")
async def get_all_unscanned_images():
    global all_files, files_found
    files_found = 0
    all_files = 0
    
    def scan_folder(folder):
        global files_found, all_files
        images = []
        valid_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".gif")
        
        for root, _, files in os.walk(folder):
            all_files += len(files)
            for file in files:
                files_found += 1
                if file.lower().endswith(valid_extensions):
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, start=folder)
                    rel_path_unix = os.path.join(os.path.basename(folder), rel_path).replace(os.sep, "/")
                    full_relative = f"/files/{rel_path_unix}"
                    full_relative = full_relative.replace("/outputs/","/automatic/").replace("/output/","/comfyui/")
                    images.append(full_relative)

        return images

    tasks = [asyncio.to_thread(scan_folder, folder) for folder in folders]
    results = await asyncio.gather(*tasks)
    all_images = [img for sublist in results for img in sublist]

    scanned_images = utils.all_images
    scanned_paths = {img["Path"] for img in scanned_images}
    unscanned_images = [img for img in all_images if img not in scanned_paths]

    return unscanned_images

parser_manager = ParserManager()

def convert_metadata(automatic_metadata):
    if(not automatic_metadata):
        return {
            "Prompt": "",
            "NegativePrompt": "",
            "Sampler": "unknown",
            "ModelHash": "None",
            "Model": None,
            "CFGScale": 0,
            "Steps": 0,
            "Seed": 0,
            "Width": 0,
            "Height": 0,
            "Workflow": None,
        }

    size = automatic_metadata.metadata.get("size", "0x0")
    width = size.split("x")[0]
    height = size.split("x")[1]

    if(size == "0x0"):
        width = automatic_metadata.metadata.get("EmptyLatentImage", [{}])[0].get("width", 0)
        height = automatic_metadata.metadata.get("EmptyLatentImage", [{}])[0].get("height", 0)

    sampler = (
        automatic_metadata.samplers[0]
        if automatic_metadata.samplers and len(automatic_metadata.samplers) > 0
        else None
    )
    return {
        "Prompt": automatic_metadata.full_prompt,
        "NegativePrompt": automatic_metadata.full_negative_prompt,
        "Sampler": sampler.name if sampler else None,
        "ModelHash": sampler.model.hash if sampler and sampler.model else None,
        "Model": sampler.model.name if sampler and sampler.model else None,
        "CFGScale": float(sampler.parameters.get("cfg_scale", 0)) if sampler else 0,
        "Steps": int(sampler.parameters.get("steps", 0)) if sampler else 0,
        "Seed": float(sampler.parameters.get("seed", 0)) if sampler else 0,
        "Width": int(width),
        "Height": int(height),
        "Workflow": automatic_metadata.raw_parameters.get("workflow", None),
    }

async def get_metadata(file_path):
    try:
        file_path = file_path.replace("\\", "/")
        if(file_path.startswith("/files/")):
            file_path = file_path.replace("/files", utils.api_file_root)

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None

        prompt_info = None
        try:
            prompt_info = parser_manager.parse(file_path)
        except Exception as parse_error:
            print(f"Error parsing file {file_path}: {parse_error}")

        api_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)).replace("\\", "/")
        relative_path = file_path.replace("\\", "/").replace(api_root, "")
        metadata = convert_metadata(prompt_info)
        metadata["Path"] = relative_path

        if os.path.exists(file_path):
            created_time_unix = os.path.getctime(file_path)
            modified_time_unix = os.path.getmtime(file_path)

            created_time_ticks = int((created_time_unix + 62135596800) * 10000000)
            modified_time_ticks = int((modified_time_unix + 62135596800) * 10000000)

            metadata["CreatedDate"] = created_time_ticks
            metadata["ModifiedDate"] = modified_time_ticks

            if metadata["Width"] == 0 or metadata["Height"] == 0:
                try:
                    with Image.open(file_path) as img:
                        metadata["Width"], metadata["Height"] = img.size
                except Exception as img_error:
                    print(f"Error getting image size for {file_path}: {img_error}")

        return metadata
    except Exception as e:
        print(f"Error retrieving metadata for file {file_path}: {e}")
        return None

@router.post("/fix-image-resolutions")
def fix_resolutions():
    global all_images
    if not os.path.exists(utils.IMAGES_FILE):
        raise HTTPException(status_code=404, detail="images.json not found")

    with open(utils.IMAGES_FILE, "r", encoding="utf-8") as f:
        all_images = json.load(f)

    for image in all_images:
        if image["Width"] == 0 or image["Height"] == 0 or image["Width"] == 1 or image["Height"] == 1:
            try:
                path = image["Path"]

                if(path.startswith("/files/")):
                    path = path.replace("/files", utils.api_file_root)

                with Image.open(path) as img:
                    image["Width"], image["Height"] = img.size
            except Exception as img_error:
                print(f"Error getting image size for {image['Path']}: {img_error}")
                image["Width"] = 1  
                image["Height"] = 1

    with open(utils.IMAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(all_images, f, indent=2)

    utils.load_images()

    return {"message": "Resolutions fixed", "fixed_images": len(all_images)}

model_hash = {}

@router.post("/update-models")
def update_models(refresh_cache: bool = Query(False)):
    global model_hash

    if refresh_cache:
        model_hash = {}
        
    images = [image for image in utils.all_images if not image.get("Model") and image.get("ModelHash")]

    model_count = 0
    for image in images:
        if image["ModelHash"] not in model_hash:
            model_hash[image["ModelHash"]] = image["Model"]
            model_count += 1

    print(f"Found {len(images)} images without model with {model_count} unique hashes")

    models_found = 0

    for image in images:
        if image["ModelHash"] in model_hash:
            image["Model"] = model_hash[image["ModelHash"]]
        else:
            hash = image["ModelHash"]
            url = f"https://civitai.com/api/v1/model-versions/by-hash/{hash}"
            try:
                print(f"Fetching model name for hash {hash}...")
                with httpx.Client() as client:
                    response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("error"):
                        print(f"Error fetching model name for hash {hash}: {data['error']}")
                        model_hash[hash] = None
                        image["Model"] = None
                        continue

                    name = data.get("model","") + data.get("name", "")
                    
                    model_hash[hash] = name
                    image["Model"] = name
                    print(f"Fetched model name for hash {hash}: {name}")
                    models_found += 1
                else:
                    print(f"Error fetching model name for hash {hash}: {response.status_code}")
                    model_hash[hash] = None
                    image["Model"] = None
            except Exception as e:
                print(f"Error fetching model name for hash {hash}: {e}")
                model_hash[hash] = None
                image["Model"] = None

    return {"message": "Models updated", "updated_images": len(images), "models_found": models_found}


@router.post("/convert-videos-to-gifs")
async def convert_videos_to_gifs():
    base_dir = utils.api_file_root
    if not os.path.exists(base_dir):
        return {"error": f"Base directory {base_dir} not found"}

    video_files = []
    valid_extensions = (".mp4", ".avi", ".mov", ".mkv", ".webm")
    
    print(f"Searching for video files in {base_dir}...")
    
    for folder_path in folders:
        if os.path.exists(folder_path):
            print(f"Searching in {folder_path}...")
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(valid_extensions):
                        abs_path = os.path.join(root, file)
                        print(f"Found video: {abs_path}")
                        video_files.append(abs_path)
    
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith(valid_extensions):
                abs_path = os.path.join(root, file)
                print(f"Found video: {abs_path}")
                video_files.append(abs_path)

    video_files = list(set(video_files))
    
    print(f"Found {len(video_files)} video files")
    
    conversion_results = {
        "total": len(video_files),
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "errors": [],
        "converted_files": []
    }
    
    for video_path in video_files:
        try:
            output_path = os.path.splitext(video_path)[0] + ".gif"
            
            if os.path.exists(output_path):
                conversion_results["skipped"] += 1
                continue
                
            import subprocess
            
            palette_path = os.path.splitext(output_path)[0] + "_palette.png"
            
            palette_cmd = [
                "ffmpeg", "-y", "-i", video_path, 
                "-vf", "fps=10,scale=320:-1:flags=lanczos,palettegen", 
                palette_path
            ]
            
            convert_cmd = [
                "ffmpeg", "-y", "-i", video_path, "-i", palette_path,
                "-filter_complex", "fps=10,scale=320:-1:flags=lanczos[x];[x][1:v]paletteuse",
                output_path
            ]
            
            subprocess.run(palette_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(convert_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if os.path.exists(palette_path):
                os.remove(palette_path)
                
            conversion_results["successful"] += 1
            conversion_results["converted_files"].append({
                "input": video_path,
                "output": output_path
            })
            
        except Exception as e:
            conversion_results["failed"] += 1
            error_details = {
                "file": video_path,
                "error": str(e)
            }
            conversion_results["errors"].append(error_details)
            print(f"Failed to convert {video_path}: {e}")
    
    return {
        "message": f"Converted {conversion_results['successful']} videos to GIFs, "
                   f"skipped {conversion_results['skipped']}, "
                   f"failed {conversion_results['failed']}",
        "details": conversion_results
    }

@router.post("/prune-images")
async def prune_images():
    print("Prune: loading models...")
    _models = models.load_models()
    print(f"Prune: loaded {len(_models)} models")

    all_images = []
    if os.path.exists(utils.IMAGES_FILE):
        print(f"Prune: loading images from {utils.IMAGES_FILE} ...")
        with open(utils.IMAGES_FILE, "r", encoding="utf-8") as f:
            all_images = json.load(f)
        print(f"Prune: loaded {len(all_images)} images")
    else:
        raise HTTPException(status_code=404, detail="images.json not found")
    
    files_removed = 0
    missing_removed = 0
    models_filled = 0

    total = len(all_images)
    step = max(1, total // 20)  # ~5% progress updates

    print("Prune: checking file existence and filling model names...")
    for i, image in enumerate(list(all_images), start=1):  # iterate over a copy; we may remove from original
        path = image["Path"]
        if path.startswith("/files/"):
            path = path.replace("/files", utils.api_file_root)

        if not os.path.exists(path):
            print(f"Prune: missing file -> {path}")
            all_images.remove(image)
            files_removed += 1
            missing_removed += 1
        elif image.get("Model") is None or image.get("Model") == "None":
            if image.get("ModelHash") in _models:
                image["Model"] = _models[image["ModelHash"]]["Name"]
                models_filled += 1
            else:
                image["Model"] = None

        if i % step == 0 or i == total:
            pct = round(i / max(1, total) * 100, 1)
            print(f"Prune: pass 1 {i}/{total} ({pct}%) - missing removed {missing_removed}, models filled {models_filled}")

    print("Prune: removing duplicate entries by Path...")
    unique_images = {}
    duplicates_removed = 0
    total2 = len(all_images)
    step2 = max(1, total2 // 20)

    for j, image in enumerate(list(all_images), start=1):
        if image["Path"] not in unique_images:
            unique_images[image["Path"]] = image
        else:
            print(f"Prune: duplicate -> Id {image.get('Id')} Path {image['Path']}")
            all_images.remove(image)
            files_removed += 1
            duplicates_removed += 1

        if j % step2 == 0 or j == total2:
            pct = round(j / max(1, total2) * 100, 1)
            print(f"Prune: pass 2 {j}/{total2} ({pct}%) - duplicates removed {duplicates_removed}")

    all_images = list(unique_images.values())

    with open(utils.IMAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(all_images, f, indent=2)

    utils.load_images()

    print(f"Prune: completed. Removed {files_removed} (missing: {missing_removed}, duplicates: {duplicates_removed}). Remaining: {len(all_images)}")
    print("Prune: images.json written and images reloaded.")

    return {
        "message": "Pruned images",
        "files_removed": files_removed,
        "remaining_images": len(all_images)
    }




