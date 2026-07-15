from fastapi import APIRouter, Query, HTTPException, Body, WebSocket, WebSocketDisconnect
from PIL import Image
import os
import json
import utils
from sd_parsers import ParserManager
import asyncio
from fastapi import BackgroundTasks
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

# Prompt update states
update_inprogress = False
update_total = 0
update_processed = 0
update_successful = 0
update_error = False
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

        # Load existing images once at start of scan
        utils.ensure_loaded()
        all_images = utils.raw_all_images.copy()

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
                    # Check if this image has been moved
                    was_moved = find_and_update_moved_image(metadata, all_images)
                    if not was_moved:
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
        if all_images:
            highest_id = max(image["Id"] for image in all_images)

        for index, metadata in enumerate(scanned_images):
            metadata["Id"] = highest_id + 1 + index

        await websocket.send_json({
            "type": "status",
            "status": "saving",
            "message": f"Saving new and updated images..."
        })

        start_id = highest_id
        all_images.extend(scanned_images)
        utils.raw_all_images = all_images
        utils.save_images()
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

        # Load existing images once at start of scan
        utils.ensure_loaded()
        all_images = utils.raw_all_images.copy()

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

        for metadata in results:
            if metadata:
                was_moved = find_and_update_moved_image(metadata, all_images)
                if not was_moved:
                    scanned_images.append(metadata)

        highest_id = 0
        if all_images:
            highest_id = max(image["Id"] for image in all_images)

        for index, metadata in enumerate(scanned_images):
            metadata["Id"] = highest_id + 1 + index
            print(f"[{index + 1}/{len(scanned_images)}] Prompt:  {metadata['Prompt']}")

        all_images.extend(scanned_images)
        utils.raw_all_images = all_images
        utils.save_images()

        print("Scan completed. Images saved to SQLite database")
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

def extract_comfy_prompts(prompt_json):
    if not isinstance(prompt_json, dict):
        return None, None
        
    sampler_nodes = []
    for node_id, node in prompt_json.items():
        class_type = node.get("class_type", "")
        if "KSampler" in class_type:
            sampler_nodes.append(node)
            
    if not sampler_nodes:
        clip_texts = []
        for node_id, node in prompt_json.items():
            if node.get("class_type") == "CLIPTextEncode":
                txt = node.get("inputs", {}).get("text")
                if txt and isinstance(txt, str):
                    clip_texts.append(txt)
        if len(clip_texts) >= 2:
            return clip_texts[0], clip_texts[1]
        elif len(clip_texts) == 1:
            return clip_texts[0], ""
        return None, None

    sampler = sampler_nodes[0]
    inputs = sampler.get("inputs", {})
    
    def trace_text(link_or_val):
        if isinstance(link_or_val, list) and len(link_or_val) >= 2:
            source_id = str(link_or_val[0])
            source_node = prompt_json.get(source_id)
            if not source_node:
                return ""
            class_type = source_node.get("class_type", "")
            if class_type == "ConditioningZeroOut":
                return ""
            node_inputs = source_node.get("inputs", {})
            if class_type == "CLIPTextEncode":
                txt = node_inputs.get("text", "")
                if isinstance(txt, list):
                    return trace_text(txt)
                return txt
            elif class_type in ("ConditioningSetMask", "ConditioningCombine"):
                for k, v in node_inputs.items():
                    if k in ("conditioning", "conditioning_to", "conditioning_from"):
                        res = trace_text(v)
                        if res:
                            return res
            if "text" in node_inputs:
                txt = node_inputs["text"]
                if isinstance(txt, list):
                    return trace_text(txt)
                return str(txt)
            for k, v in node_inputs.items():
                if isinstance(v, list) and len(v) >= 2:
                    res = trace_text(v)
                    if res:
                        return res
        elif isinstance(link_or_val, str):
            return link_or_val
        return ""

    pos_link = inputs.get("positive")
    neg_link = inputs.get("negative")
    
    pos_prompt = trace_text(pos_link) if pos_link else ""
    neg_prompt = trace_text(neg_link) if neg_link else ""
    
    return pos_prompt, neg_prompt


def extract_comfyui_metadata(file_path):
    from PIL import Image
    import json
    try:
        with Image.open(file_path) as img:
            info = img.info
            prompt_str = info.get("prompt")
            workflow_str = info.get("workflow")
            
            if not prompt_str:
                return None
                
            prompt_json = json.loads(prompt_str)
            
            pos_prompt, neg_prompt = extract_comfy_prompts(prompt_json)
            
            sampler_node = None
            for node_id, node in prompt_json.items():
                if "KSampler" in node.get("class_type", ""):
                    sampler_node = node
                    break
                    
            sampler_name = "unknown"
            steps = 0
            cfg = 0
            seed = 0
            model = None
            
            if sampler_node:
                inputs = sampler_node.get("inputs", {})
                sampler_name = inputs.get("sampler_name", "unknown")
                steps = int(inputs.get("steps", 0))
                cfg = float(inputs.get("cfg", 0))
                seed = float(inputs.get("seed") or inputs.get("noise_seed") or 0)
                model = inputs.get("model")
                
            return {
                "Prompt": pos_prompt or "",
                "NegativePrompt": neg_prompt or "",
                "Sampler": sampler_name,
                "Model": model,
                "CFGScale": cfg,
                "Steps": steps,
                "Seed": seed,
                "Workflow": workflow_str,
            }
    except Exception as e:
        print(f"Error in extract_comfyui_metadata for {file_path}: {e}")
        return None


def find_and_update_moved_image(metadata, all_images):
    file_hash = metadata.get("FileHash")
    new_path = metadata.get("Path")
    if not new_path:
        return False

    # 1. Search by FileHash
    if file_hash:
        for img in all_images:
            if img.get("FileHash") == file_hash:
                img["Path"] = new_path
                img["CreatedDate"] = metadata.get("CreatedDate", img.get("CreatedDate"))
                img["ModifiedDate"] = metadata.get("ModifiedDate", img.get("ModifiedDate"))
                if metadata.get("Prompt"):
                    img["Prompt"] = metadata["Prompt"]
                if metadata.get("NegativePrompt"):
                    img["NegativePrompt"] = metadata["NegativePrompt"]
                if metadata.get("Sampler"):
                    img["Sampler"] = metadata["Sampler"]
                if metadata.get("Model"):
                    img["Model"] = metadata["Model"]
                if metadata.get("ModelHash"):
                    img["ModelHash"] = metadata["ModelHash"]
                if metadata.get("Width"):
                    img["Width"] = metadata["Width"]
                if metadata.get("Height"):
                    img["Height"] = metadata["Height"]
                if metadata.get("Workflow"):
                    img["Workflow"] = metadata["Workflow"]
                return True

    # 2. Fallback: Search by same filename if the old path is broken (does not exist)
    new_filename = os.path.basename(new_path)
    for img in all_images:
        old_path = img.get("Path")
        if not old_path:
            continue
        
        old_abs = old_path
        if old_abs.startswith("/files/"):
            old_abs = old_abs.replace("/files", utils.api_file_root)
            
        if not os.path.exists(old_abs):
            old_filename = os.path.basename(old_path)
            if old_filename == new_filename:
                img["Path"] = new_path
                if file_hash:
                    img["FileHash"] = file_hash
                img["CreatedDate"] = metadata.get("CreatedDate", img.get("CreatedDate"))
                img["ModifiedDate"] = metadata.get("ModifiedDate", img.get("ModifiedDate"))
                if metadata.get("Prompt"):
                    img["Prompt"] = metadata["Prompt"]
                if metadata.get("NegativePrompt"):
                    img["NegativePrompt"] = metadata["NegativePrompt"]
                if metadata.get("Sampler"):
                    img["Sampler"] = metadata["Sampler"]
                if metadata.get("Model"):
                    img["Model"] = metadata["Model"]
                if metadata.get("ModelHash"):
                    img["ModelHash"] = metadata["ModelHash"]
                if metadata.get("Width"):
                    img["Width"] = metadata["Width"]
                if metadata.get("Height"):
                    img["Height"] = metadata["Height"]
                if metadata.get("Workflow"):
                    img["Workflow"] = metadata["Workflow"]
                return True

    return False

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

        # Parse ComfyUI metadata as a fallback or to override default behavior
        if not prompt_info or (hasattr(prompt_info, "raw_parameters") and "prompt" in prompt_info.raw_parameters):
            try:
                comfy_meta = extract_comfyui_metadata(file_path)
                if comfy_meta:
                    for k, v in comfy_meta.items():
                        if v is not None:
                            metadata[k] = v
            except Exception as comfy_err:
                print(f"Failed to extract ComfyUI metadata for {file_path}: {comfy_err}")

        # Compute FileHash
        import hashlib
        h = hashlib.sha256()
        try:
            with open(file_path, 'rb') as fh:
                while chunk := fh.read(8192):
                    h.update(chunk)
            metadata["FileHash"] = h.hexdigest()
        except Exception as hash_error:
            print(f"Error hashing file {file_path}: {hash_error}")
            metadata["FileHash"] = None

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
    utils.ensure_loaded()
    all_images = utils.raw_all_images.copy()

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

    utils.raw_all_images = all_images
    utils.save_images()

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

    utils.ensure_loaded()
    all_images = utils.raw_all_images.copy()
    print(f"Prune: loaded {len(all_images)} images from SQLite")
    
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

    utils.raw_all_images = all_images
    utils.save_images()

    utils.load_images()

    print(f"Prune: completed. Removed {files_removed} (missing: {missing_removed}, duplicates: {duplicates_removed}). Remaining: {len(all_images)}")
    print("Prune: images.json written and images reloaded.")

    return {
        "message": "Pruned images",
        "files_removed": files_removed,
        "remaining_images": len(all_images)
    }





@router.post("/update-missing-prompts")
def start_update_missing_prompts(background_tasks: BackgroundTasks):
    global update_inprogress
    if update_inprogress:
        raise HTTPException(status_code=400, detail="Prompt update already in progress")
    background_tasks.add_task(background_update_missing_prompts)
    return {"message": "Prompt update started in background"}

@router.get("/prompt-update-status")
def get_prompt_update_status():
    return {
        "update_inprogress": update_inprogress,
        "update_total": update_total,
        "update_processed": update_processed,
        "update_successful": update_successful,
        "update_error": update_error
    }

async def background_update_missing_prompts():
    global update_inprogress, update_total, update_processed, update_successful, update_error
    update_inprogress = True
    update_error = False
    update_total = 0
    update_processed = 0
    update_successful = 0
    
    try:
        utils.ensure_loaded()
        all_images = utils.raw_all_images.copy()
                
        # Filter images needing update
        target_images = []
        for img in all_images:
            if not img.get("Prompt") or img.get("GeneratedPrompt") == True:
                target_images.append(img)
                
        update_total = len(target_images)
        print(f"[Prompt Update] Found {update_total} images to update.")
        
        batch_size = 10
        total_batches = (update_total + batch_size - 1) // batch_size
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, update_total)
            batch = target_images[start_idx:end_idx]
            
            async def process_one(img):
                path = img.get("Path")
                if not path:
                    return False
                abs_path = path
                if abs_path.startswith("/files/"):
                    abs_path = abs_path.replace("/files", utils.api_file_root)
                if not os.path.exists(abs_path):
                    return False
                    
                try:
                    # Parse metadata
                    meta = extract_comfyui_metadata(abs_path)
                    if not meta:
                        try:
                            prompt_info = parser_manager.parse(abs_path)
                            if prompt_info:
                                meta = convert_metadata(prompt_info)
                        except Exception as pe:
                            print(f"[Prompt Update] Error parsing {abs_path}: {pe}")
                            
                    if meta and meta.get("Prompt"):
                        img["Prompt"] = meta["Prompt"]
                        if meta.get("NegativePrompt"):
                            img["NegativePrompt"] = meta["NegativePrompt"]
                        if meta.get("Sampler"):
                            img["Sampler"] = meta["Sampler"]
                        if meta.get("Model"):
                            img["Model"] = meta["Model"]
                        if meta.get("ModelHash"):
                            img["ModelHash"] = meta["ModelHash"]
                        if meta.get("CFGScale"):
                            img["CFGScale"] = meta["CFGScale"]
                        if meta.get("Steps"):
                            img["Steps"] = meta["Steps"]
                        if meta.get("Seed"):
                            img["Seed"] = meta["Seed"]
                        if meta.get("Workflow"):
                            img["Workflow"] = meta["Workflow"]
                        
                        if "GeneratedPrompt" in img:
                            del img["GeneratedPrompt"]
                        return True
                except Exception as ex:
                    print(f"[Prompt Update] Failed processing {abs_path}: {ex}")
                return False
                
            tasks = [process_one(img) for img in batch]
            results = await asyncio.gather(*tasks)
            
            update_processed += len(batch)
            update_successful += sum(1 for r in results if r)
            
            print(f"[Prompt Update] Progress: {update_processed}/{update_total} (successful={update_successful})")
            
            if update_processed % 50 == 0 or update_processed == update_total:
                utils.raw_all_images = all_images
                utils.save_images()
                utils.load_images()
                
        utils.raw_all_images = all_images
        utils.save_images()
        utils.load_images()
        print(f"[Prompt Update] Completed! Successfully updated {update_successful} images.")
        
    except Exception as e:
        update_error = True
        print(f"[Prompt Update] Error: {e}")
    finally:
        update_inprogress = False
