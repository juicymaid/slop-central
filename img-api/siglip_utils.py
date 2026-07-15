import os
import json
import time
import threading
import numpy as np
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModel
import utils

# Cached in-memory embeddings
siglip_vectors = None  # np.ndarray of shape (N, 768)
siglip_ids = []        # List[int]
siglip_id_to_index = {} # {image_id: index_in_matrix}

# Indexing status
siglip_indexing_status = {
    "status": "idle",
    "processed": 0,
    "total": 0,
    "message": ""
}
_status_lock = threading.Lock()

SIGLIP_EMBEDDINGS_FILE = "siglip_embeddings.npy"
SIGLIP_IDS_FILE = "siglip_embeddings_ids.json"
MODEL_NAME = "google/siglip2-base-patch16-224"
EMBEDDING_DIM = 768

def load_siglip_embeddings():
    """Load precomputed SigLIP embeddings and IDs from disk into memory."""
    global siglip_vectors, siglip_ids, siglip_id_to_index
    
    # Load IDs
    if os.path.exists(SIGLIP_IDS_FILE):
        try:
            with open(SIGLIP_IDS_FILE, "r", encoding="utf-8") as f:
                siglip_ids = json.load(f)
        except Exception as e:
            print(f"Error loading {SIGLIP_IDS_FILE}: {e}")
            siglip_ids = []
    else:
        siglip_ids = []

    # Load vectors matrix
    if os.path.exists(SIGLIP_EMBEDDINGS_FILE):
        try:
            siglip_vectors = np.load(SIGLIP_EMBEDDINGS_FILE).astype(np.float32)
        except Exception as e:
            print(f"Error loading {SIGLIP_EMBEDDINGS_FILE}: {e}")
            siglip_vectors = None
    else:
        siglip_vectors = None

    # Validate alignment
    if siglip_vectors is not None and (len(siglip_ids) != siglip_vectors.shape[0] or siglip_vectors.shape[1] != EMBEDDING_DIM):
        print(f"Warning: SigLIP embeddings ({siglip_vectors.shape if siglip_vectors is not None else None}) and IDs ({len(siglip_ids)}) mismatch! Resetting.")
        siglip_vectors = None
        siglip_ids = []

    # Build index map
    siglip_id_to_index = {iid: idx for idx, iid in enumerate(siglip_ids)}
    print(f"Loaded {len(siglip_ids)} SigLIP embeddings.")

def save_siglip_embeddings(ids, matrix):
    """Save embeddings and IDs to disk."""
    try:
        with open(SIGLIP_IDS_FILE, "w", encoding="utf-8") as f:
            json.dump(ids, f, indent=2)
        np.save(SIGLIP_EMBEDDINGS_FILE, matrix)
    except Exception as e:
        print(f"Error saving SigLIP embeddings: {e}")

def update_status(status=None, processed=None, total=None, message=None):
    with _status_lock:
        if status is not None:
            siglip_indexing_status["status"] = status
        if processed is not None:
            siglip_indexing_status["processed"] = processed
        if total is not None:
            siglip_indexing_status["total"] = total
        if message is not None:
            siglip_indexing_status["message"] = message

def get_local_path(path):
    """Resolve static Web path to local absolute file path."""
    if not path:
        return ""
    normalized = path.replace("\\", "/")
    if normalized.startswith("/files/"):
        return os.path.join(utils.api_file_root, normalized[7:])
    if normalized.startswith("files/"):
        return os.path.join(utils.api_file_root, normalized[6:])
    # Try as direct path or relative to files/ or api_root
    if os.path.exists(path):
        return path
    rel_files = os.path.join(utils.api_file_root, path)
    if os.path.exists(rel_files):
        return rel_files
    return path

def run_siglip_indexing(force=False):
    """Background task to generate embeddings for all images missing them."""
    global siglip_vectors, siglip_ids, siglip_id_to_index
    
    try:
        update_status(status="running", processed=0, total=0, message="Initializing database...")
        utils.load_images()
        
        # Load existing embeddings first
        load_siglip_embeddings()
        
        # Exclude deleted images from the index
        active_ids = set(utils.images_data.keys())
        if siglip_ids and siglip_vectors is not None:
            keep_indices = [i for i, iid in enumerate(siglip_ids) if iid in active_ids]
            if len(keep_indices) < len(siglip_ids):
                siglip_ids = [siglip_ids[i] for i in keep_indices]
                siglip_vectors = siglip_vectors[keep_indices]
                save_siglip_embeddings(siglip_ids, siglip_vectors)
                siglip_id_to_index = {iid: idx for idx, iid in enumerate(siglip_ids)}
                print(f"Cleaned up deleted images from SigLIP cache. New count: {len(siglip_ids)}")
        
        # Determine which images need processing
        to_process = []
        for img in utils.all_images:
            iid = img["Id"]
            if force or iid not in siglip_id_to_index:
                to_process.append(img)
                
        # Sort by CreatedDate descending so newest images are processed first
        to_process.sort(key=lambda x: x.get("CreatedDate") or 0, reverse=True)
        
        total = len(to_process)
        if total == 0:
            update_status(status="idle", processed=0, total=0, message="All images already embedded.")
            return

        update_status(total=total, message=f"Loading SigLIP 2 model {MODEL_NAME}...")
        
        # Setup device & model (only when building to save VRAM)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"SigLIP Indexer running on device: {device}")
        
        model = AutoModel.from_pretrained(MODEL_NAME).to(device)
        processor = AutoProcessor.from_pretrained(MODEL_NAME)
        
        batch_size = 64
        processed_count = 0
        
        # Temporary lists for the current run
        run_ids = []
        run_vecs = []
        
        # Process in batches
        for i in range(0, total, batch_size):
            batch_images_meta = to_process[i:i+batch_size]
            batch_pil_images = []
            batch_valid_ids = []
            
            for img in batch_images_meta:
                local_path = get_local_path(img.get("Path"))
                if not local_path or not os.path.exists(local_path):
                    continue
                try:
                    pil_img = Image.open(local_path)
                    # Convert to RGB to ensure no alpha channel issues
                    if pil_img.mode != "RGB":
                        pil_img = pil_img.convert("RGB")
                    # Quick check to prevent memory issues with astronomical dimensions
                    if pil_img.width > 16384 or pil_img.height > 16384:
                        pil_img.thumbnail((2048, 2048))
                    batch_pil_images.append(pil_img)
                    batch_valid_ids.append(img["Id"])
                except Exception as ex:
                    print(f"Skipping corrupt image {local_path} (ID: {img['Id']}): {ex}")
                    continue
            
            if not batch_pil_images:
                processed_count += len(batch_images_meta)
                update_status(processed=processed_count)
                continue
                
            try:
                # Preprocess and forward pass
                inputs = processor(images=batch_pil_images, return_tensors="pt").to(device)
                with torch.no_grad():
                    features = model.get_image_features(**inputs)
                    # L2 Normalize the vectors
                    features = features / features.norm(dim=-1, keepdim=True)
                    features_np = features.cpu().numpy().astype(np.float32)
                
                run_ids.extend(batch_valid_ids)
                run_vecs.append(features_np)
                
            except Exception as ex:
                print(f"Error during SigLIP inference batch: {ex}")
                # Fallback to process singly to isolate faulty images
                for pil_img, iid in zip(batch_pil_images, batch_valid_ids):
                    try:
                        inputs = processor(images=[pil_img], return_tensors="pt").to(device)
                        with torch.no_grad():
                            feat = model.get_image_features(**inputs)
                            feat = feat / feat.norm(dim=-1, keepdim=True)
                            feat_np = feat.cpu().numpy().astype(np.float32)
                        run_ids.append(iid)
                        run_vecs.append(feat_np)
                    except Exception as sing_ex:
                        print(f"Failed on single image ID {iid}: {sing_ex}")
            
            processed_count += len(batch_images_meta)
            update_status(processed=processed_count, message=f"Processed {processed_count}/{total} images...")
            
            # Periodically write progress to disk (every 256 images)
            if len(run_ids) >= 256:
                # Merge new with existing
                new_matrix = np.vstack(run_vecs)
                if siglip_vectors is not None:
                    # Remove any duplicates in existing if they are somehow reprocessed
                    dupes = set(run_ids)
                    keep_idx = [idx for idx, iid in enumerate(siglip_ids) if iid not in dupes]
                    
                    if len(keep_idx) < len(siglip_ids):
                        filtered_ids = [siglip_ids[idx] for idx in keep_idx]
                        filtered_matrix = siglip_vectors[keep_idx]
                    else:
                        filtered_ids = siglip_ids
                        filtered_matrix = siglip_vectors
                        
                    siglip_ids = filtered_ids + run_ids
                    siglip_vectors = np.vstack([filtered_matrix, new_matrix])
                else:
                    siglip_ids = run_ids
                    siglip_vectors = new_matrix
                
                save_siglip_embeddings(siglip_ids, siglip_vectors)
                siglip_id_to_index = {iid: idx for idx, iid in enumerate(siglip_ids)}
                
                run_ids = []
                run_vecs = []
        
        # Final save for remaining
        if run_ids:
            new_matrix = np.vstack(run_vecs)
            if siglip_vectors is not None:
                dupes = set(run_ids)
                keep_idx = [idx for idx, iid in enumerate(siglip_ids) if iid not in dupes]
                filtered_ids = [siglip_ids[idx] for idx in keep_idx]
                filtered_matrix = siglip_vectors[keep_idx]
                
                siglip_ids = filtered_ids + run_ids
                siglip_vectors = np.vstack([filtered_matrix, new_matrix])
            else:
                siglip_ids = run_ids
                siglip_vectors = new_matrix
            
            save_siglip_embeddings(siglip_ids, siglip_vectors)
            siglip_id_to_index = {iid: idx for idx, iid in enumerate(siglip_ids)}

        # Trigger 2D coordinates map rebuilding
        try:
            update_status(message="Rebuilding 2D coordinates map...")
            rebuild_siglip_2d_coords()
        except Exception as map_ex:
            print(f"Failed to auto-rebuild 2D coords: {map_ex}")

        update_status(status="idle", message=f"Embedding process complete. Total: {len(siglip_ids)}")
        print(f"SigLIP Embedding database generation finished. Total count: {len(siglip_ids)}")

    except Exception as e:
        import traceback
        update_status(status="failed", message=f"Error: {str(e)}")
        print(f"SigLIP Indexing failed: {e}")
        traceback.print_exc()
        
    finally:
        # Crucial VRAM cleanup
        if 'model' in locals():
            del model
        if 'processor' in locals():
            del processor
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        # Force reload in-memory cache to ensure consistency
        load_siglip_embeddings()

def start_siglip_indexing(force=False, background_tasks=None):
    """Start indexing missing images in a background thread."""
    global siglip_indexing_status
    with _status_lock:
        if siglip_indexing_status["status"] == "running":
            return {"status": "already running", "processed": siglip_indexing_status["processed"], "total": siglip_indexing_status["total"]}
            
    if background_tasks:
        background_tasks.add_task(run_siglip_indexing, force)
    else:
        t = threading.Thread(target=run_siglip_indexing, kwargs={"force": force})
        t.daemon = True
        t.start()
        
    return {"status": "started", "message": "SigLIP embedding generation started in the background."}

def generate_image_embedding(image_id: int):
    """
    Generate a SigLIP embedding for a single image, append it to the cache and save it to disk.
    Returns True if successful, False otherwise.
    """
    global siglip_vectors, siglip_ids, siglip_id_to_index
    
    img = utils.images_data.get(image_id)
    if not img:
        return False
        
    local_path = get_local_path(img.get("Path"))
    if not local_path or not os.path.exists(local_path):
        return False
        
    try:
        pil_img = Image.open(local_path)
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
        if pil_img.width > 16384 or pil_img.height > 16384:
            pil_img.thumbnail((2048, 2048))
    except Exception as e:
        print(f"Failed to open image for single embedding generation: {e}")
        return False

    device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        model = AutoModel.from_pretrained(MODEL_NAME).to(device)
        processor = AutoProcessor.from_pretrained(MODEL_NAME)
        
        inputs = processor(images=[pil_img], return_tensors="pt").to(device)
        with torch.no_grad():
            features = model.get_image_features(**inputs)
            features = features / features.norm(dim=-1, keepdim=True)
            features_np = features.cpu().numpy().astype(np.float32)
            
        # Add to local cache and disk
        if siglip_vectors is None or len(siglip_ids) == 0:
            siglip_vectors = features_np
            siglip_ids = [image_id]
        else:
            # If it somehow already existed, remove old one first to prevent duplicates
            if image_id in siglip_id_to_index:
                idx = siglip_id_to_index[image_id]
                siglip_vectors = np.delete(siglip_vectors, idx, axis=0)
                siglip_ids.pop(idx)
            
            siglip_vectors = np.vstack([siglip_vectors, features_np])
            siglip_ids.append(image_id)
            
        save_siglip_embeddings(siglip_ids, siglip_vectors)
        siglip_id_to_index = {iid: idx for idx, iid in enumerate(siglip_ids)}
        return True
    except Exception as e:
        print(f"Failed to generate single embedding: {e}")
        return False
    finally:
        # VRAM cleanup
        if 'model' in locals():
            del model
        if 'processor' in locals():
            del processor
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

def get_similar_images_by_siglip(image_id: int, top_k: int = 20):
    """Return a list of (image_id, similarity_score) sorted by highest similarity."""
    global siglip_vectors, siglip_ids, siglip_id_to_index
    
    # Force load embeddings if not loaded yet
    if siglip_vectors is None or len(siglip_ids) == 0:
        load_siglip_embeddings()
        
    if image_id not in siglip_id_to_index:
        # Try to generate it on the fly
        print(f"Embedding not found for image {image_id}. Generating on the fly...")
        generate_image_embedding(image_id)
        
    if siglip_vectors is None or len(siglip_ids) == 0 or image_id not in siglip_id_to_index:
        return []
        
    idx = siglip_id_to_index[image_id]
    target_vec = siglip_vectors[idx]
    
    # Compute dot product (which is cosine similarity since vectors are normalized)
    similarities = siglip_vectors @ target_vec
    
    # Sort and exclude the target image itself
    sorted_indices = np.argsort(similarities)[::-1]
    
    results = []
    for s_idx in sorted_indices:
        iid = siglip_ids[s_idx]
        if iid == image_id:
            continue
        results.append((iid, float(similarities[s_idx])))
        if len(results) >= top_k:
            break
            
    return results

def get_aligned_siglip_matrix(images_list):
    """
    Returns a normalized numpy matrix representing SigLIP embeddings aligned with images_list.
    Row i of the returned matrix corresponds to images_list[i].
    If an image does not have a SigLIP embedding, returns a zero vector for it.
    """
    global siglip_vectors, siglip_id_to_index
    
    matrix = np.zeros((len(images_list), EMBEDDING_DIM), dtype=np.float32)
    if siglip_vectors is None or len(siglip_ids) == 0:
        return matrix
        
    for i, img in enumerate(images_list):
        iid = img.get("Id")
        if iid in siglip_id_to_index:
            matrix[i] = siglip_vectors[siglip_id_to_index[iid]]
            
    return matrix

def rebuild_siglip_2d_coords():
    """Reduce SigLIP embeddings to 2D coordinates using UMAP (or PCA fallback) and save to disk."""
    global siglip_vectors, siglip_ids
    
    if siglip_vectors is None or len(siglip_ids) == 0:
        print("rebuild_siglip_2d_coords: No embeddings found to project.")
        return {"status": "error", "message": "No embeddings to reduce."}
        
    try:
        try:
            from umap import UMAP
            print("Running UMAP dimensionality reduction on embeddings...")
            reducer = UMAP(n_components=2, n_neighbors=15, min_dist=0.1, random_state=42)
            coords = reducer.fit_transform(siglip_vectors)
            mode_used = "umap"
        except ImportError:
            from sklearn.decomposition import PCA
            print("UMAP not available. Falling back to PCA...")
            reducer = PCA(n_components=2)
            coords = reducer.fit_transform(siglip_vectors)
            mode_used = "pca"
            
        # Normalize coordinates to [0, 1] range for easy plotting
        c_min = coords.min(axis=0)
        c_max = coords.max(axis=0)
        denom = c_max - c_min
        denom[denom == 0] = 1.0
        normalized_coords = (coords - c_min) / denom
        
        # Build coordinates map mapping image_id to [x, y]
        coords_map = {}
        for i, iid in enumerate(siglip_ids):
            coords_map[int(iid)] = [float(normalized_coords[i, 0]), float(normalized_coords[i, 1])]
            
        # Save to file
        with open("siglip_2d_coords.json", "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in coords_map.items()}, f)
            
        print(f"Successfully generated 2D coords using {mode_used} for {len(siglip_ids)} images.")
        return {"status": "success", "mode": mode_used, "count": len(siglip_ids)}
        
    except Exception as e:
        print(f"Error running dimensionality reduction: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
