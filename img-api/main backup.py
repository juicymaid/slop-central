import json
import os
import random
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

IMAGES_FILE = "images.json"
LIKES_FILE = "likes.json"  # new constant for votes file
CLICKS_FILE = "clicks.json"  # new constant for clicks file

# New constant and global variable for boards
BOARDS_FILE = "boards.json"
boards_data = {}  # { board_id: { "id": int, "name": str, "images": [int, ...] } }

images_data = {}
all_images = []  # changed from {} to [] to support append()
clicks_data = {}  # global variable to track image clicks


def load_images():
    global images_data, all_images
    if not os.path.exists(IMAGES_FILE):
        raise FileNotFoundError(f"{IMAGES_FILE} not found.")

    with open(IMAGES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for image in data:
        # Check for required keys.
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
        all_images.append(image)
    # End of image load.

def load_votes():
    # Load likes/dislikes from LIKES_FILE and update images_data accordingly.
    if os.path.exists(LIKES_FILE):
        with open(LIKES_FILE, "r", encoding="utf-8") as f:
            votes = json.load(f)
        for img_id, vote in votes.items():
            img = images_data.get(int(img_id))
            if img:
                img["Likes"] = vote.get("Likes", img.get("Likes", 0))
                img["Dislikes"] = vote.get("Dislikes", img.get("Dislikes", 0))

def save_votes():
    # Save current likes/dislikes for all images to LIKES_FILE.
    votes = {}
    for img_id, img in images_data.items():
        votes[str(img_id)] = {
            "Likes": img.get("Likes", 0),
            "Dislikes": img.get("Dislikes", 0)
        }
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
        # convert keys to int if needed
        boards_data = {int(k):v for k,v in boards_data.items()}

def save_boards():
    with open(BOARDS_FILE, "w", encoding="utf-8") as f:
        json.dump(boards_data, f, indent=2)

# Load images, votes, and boards at startup.
load_images()
load_votes()
load_clicks()  # load clicks data
load_boards()


@app.get("/")
def read_root():
    return {"message": "Welcome to the Pinterest-style image API!"}



@app.get("/image/{image_id}")
def get_image_details(image_id: int):
    image = images_data.get(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Increment click count every time the image is fetched.
    image["Clicks"] = image.get("Clicks", 0) + 1
    save_clicks()
    
    copy_img = image.copy()
    if "tags_set" in copy_img:
        del copy_img["tags_set"]

    identical_images = []
    variation_images = []
    for img in all_images:
        if img["Id"] == image_id:
            continue
        if (
            img.get("CFGScale") == image.get("CFGScale")
            and img.get("ModelHash") == image.get("ModelHash")
            and img.get("NegativePrompt") == image.get("NegativePrompt")
            and img.get("Prompt") == image.get("Prompt")
            and img.get("Sampler") == image.get("Sampler")
            and img.get("Steps") == image.get("Steps")
        ):
            copy_candidate = img.copy()
            if "tags_set" in copy_candidate:
                del copy_candidate["tags_set"]
            if img.get("Seed") == image.get("Seed"):
                identical_images.append(copy_candidate)
            else:
                variation_images.append(copy_candidate)
    copy_img["identical_images"] = identical_images
    copy_img["variations"] = variation_images

    # Determine the recommended boards based on similarity and sort them by score.
    recommended_boards = []
    for board in boards_data.values():
        pinned_ids = board.get("images", [])
        total_score = 0
        valid_count = 0
        for pid in pinned_ids:
            pinned_image = images_data.get(pid)
            if pinned_image:
                total_score += compute_full_similarity(image, pinned_image)
                valid_count += 1
        avg_score = total_score / valid_count if valid_count else 0
        recommended_boards.append({
            "id": board["id"],
            "name": board["name"],
            "pin_count": len(pinned_ids),
            "recommendation_score": avg_score
        })
    recommended_boards.sort(key=lambda x: x["recommendation_score"], reverse=True)
    copy_img["recommended_boards"] = recommended_boards

    # Add in_board details if image is in any board.
    in_boards = []
    for board in boards_data.values():
        if image_id in board.get("images", []):
            in_boards.append({
                "id": board["id"],
                "name": board["name"],
                "pin_count": len(board.get("images", []))
            })
    copy_img["in_boards"] = in_boards

    return copy_img


@app.get("/all-images")
def get_all_images(
    page: int = 1, 
    per_page: int = 10, 
    sort: str = Query("new", description="Sort order: old, new, top, random, home")
):
    start = (page - 1) * per_page
    end = start + per_page

    if sort == "home":
        # Home recommendations logic operating on original objects.
        liked_images = [img for img in all_images if img.get("Likes", 0) > 0]
        disliked_images = [img for img in all_images if img.get("Dislikes", 0) > 0]
        candidates = [img for img in all_images if img.get("Likes", 0) == 0 and img.get("Dislikes", 0) == 0]
        if not candidates or (not liked_images and not disliked_images):
            recommendations = all_images[:] if len(all_images) <= per_page else random.sample(all_images, per_page)
        else:
            scored_candidates = []
            for candidate in candidates:
                base_score = compute_custom_score(candidate, liked_images, disliked_images)
                score = (base_score * random.uniform(0.8, 1.2)) + random.uniform(0, 3)
                scored_candidates.append((score, candidate))
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            ranked = [img for _, img in scored_candidates]
            random_candidates = random.sample(all_images, k=min(5, len(all_images)))
            seen = set()
            merged = []
            for candidate in ranked:
                if candidate["Id"] not in seen:
                    merged.append(candidate)
                    seen.add(candidate["Id"])
            for candidate in random_candidates:
                if candidate["Id"] not in seen:
                    merged.append(candidate)
                    seen.add(candidate["Id"])
            recommendations = merged
        selected = recommendations[start:end]
    else:
        # For other sort orders, sort on the original list reference.
        if sort == "old":
            selected = sorted(all_images, key=lambda x: x.get("Id", 0))[start:end]
        elif sort == "new":
            selected = sorted(all_images, key=lambda x: x.get("Id", 0), reverse=True)[start:end]
        elif sort == "top":
            liked_images = [img for img in all_images if img.get("Likes", 0) > 0]
            selected = sorted(
                all_images, 
                key=lambda x: (x.get("Likes", 0), compute_custom_score(images_data[x["Id"]], liked_images, [])),
                reverse=True
            )[start:end]
        elif sort == "random":
            lst = all_images[:]  # shallow copy
            random.shuffle(lst)
            selected = lst[start:end]
        else:
            selected = sorted(all_images, key=lambda x: x.get("Id", 0), reverse=True)[start:end]

    # Now copy only the selected images and remove 'tags_set'
    result = []
    for img in selected:
        copy_img = img.copy()
        if "tags_set" in copy_img:
            del copy_img["tags_set"]
        # In home branch, also compute boards info if needed.
        if sort == "home":
            recommended_boards = []
            for board in boards_data.values():
                pinned_ids = board.get("images", [])
                total_score = 0
                valid_count = 0
                for pid in pinned_ids:
                    pinned_image = images_data.get(pid)
                    if pinned_image:
                        total_score += compute_full_similarity(img, pinned_image)
                        valid_count += 1
                avg_score = total_score / valid_count if valid_count else 0
                recommended_boards.append({
                    "id": board["id"],
                    "name": board["name"],
                    "pin_count": len(pinned_ids),
                    "recommendation_score": avg_score
                })
            recommended_boards.sort(key=lambda x: x["recommendation_score"], reverse=True)
            copy_img["recommended_boards"] = recommended_boards

            in_boards = []
            for board in boards_data.values():
                if img["Id"] in board.get("images", []):
                    in_boards.append({
                        "id": board["id"],
                        "name": board["name"],
                        "pin_count": len(board.get("images", []))
                    })
            copy_img["in_boards"] = in_boards
        result.append(copy_img)
    return result


ignore_tags = ["score_9","score_8","score_7", "score_6", "score_5", "score_4", "score_3", "score_2", "score_1", "masterpiece", "best quality","amazing quality","absurdres"]

def compute_full_similarity(image_a, image_b):
    """
    Computes similarity between two images based on prompt tags,
    ModelHash (bonus), NegativePrompt and Sampler (minor bonus).
    """
    #ignore tags
    image_a_tags = image_a["tags_set"].difference(ignore_tags)
    image_b_tags = image_b["tags_set"].difference(ignore_tags)
    
    tag_similarity = len(image_a["tags_set"].intersection(image_b["tags_set"]))
    model_bonus = (
        2
        if image_a.get("ModelHash")
        and image_b.get("ModelHash")
        and image_a["ModelHash"] == image_b["ModelHash"]
        else 0
    )
    negative_prompt_bonus = (
        0.5
        if image_a.get("NegativePrompt")
        and image_b.get("NegativePrompt")
        and image_a["NegativePrompt"] == image_b["NegativePrompt"]
        else 0
    )
    sampler_bonus = (
        0.5
        if image_a.get("Sampler")
        and image_b.get("Sampler")
        and image_a["Sampler"] == image_b["Sampler"]
        else 0
    )
    return tag_similarity + model_bonus + negative_prompt_bonus + sampler_bonus


def compute_custom_score(candidate, liked_images, disliked_images):
    """
    Compute a recommendation score for a candidate image based on similarity
    to liked/disliked images considering prompt, ModelHash, NegativePrompt, and Sampler.
    """
    score = 0
    for liked in liked_images:
        sim = compute_full_similarity(candidate, liked)
        score += sim
    for disliked in disliked_images:
        sim = compute_full_similarity(candidate, disliked)
        score -= sim
    return score


@app.get("/similar-images/{image_id}")
def get_similar_images(image_id: int, page: int = 1, per_page: int = 5):
    target_image = images_data.get(image_id)
    if not target_image:
        raise HTTPException(status_code=404, detail="Target image not found")

    candidates = []
    for img in all_images:
        if img["Id"] == image_id:
            continue
        score = compute_full_similarity(target_image, img)
        if score > 0:
            candidates.append((score, img))

    candidates.sort(key=lambda x: x[0], reverse=True)
    similar_images = []
    for score, img in candidates:
        copy_img = img.copy()
        if "tags_set" in copy_img:
            del copy_img["tags_set"]
        copy_img["similarity_score"] = score
        similar_images.append(copy_img)
    start = (page - 1) * per_page
    end = start + per_page
    return similar_images[start:end]



    """
    Returns images for the home page based on user votes with extra random images.
    Adds recommended boards and in_boards information for each image.
    """
    # Separate images that have been voted on.
    liked_images = [img for img in all_images if img.get("Likes", 0) > 0]
    disliked_images = [img for img in all_images if img.get("Dislikes", 0) > 0]

    # Consider only candidates that the user hasn't interacted with.
    candidates = [
        img for img in all_images
        if img.get("Likes", 0) == 0 and img.get("Dislikes", 0) == 0
    ]

    if not candidates or (not liked_images and not disliked_images):
        recommendations = (
            all_images.copy()
            if len(all_images) <= per_page
            else random.sample(all_images, per_page)
        )
    else:
        scored_candidates = []
        for candidate in candidates:
            base_score = compute_custom_score(candidate, liked_images, disliked_images)
            # existing random multiplier for some noise
            score = (base_score * random.uniform(0.8, 1.2)) + random.uniform(0, 3)
            scored_candidates.append((score, candidate))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        ranked = [img for _, img in scored_candidates]
        # Select additional random images from all images (toss in some variety)
        random_candidates = random.sample(all_images, k=min(5, len(all_images)))
        # Merge ranked recommendations and random candidates without duplicates.
        seen = set()
        merged = []
        for candidate in ranked:
            if candidate["Id"] not in seen:
                merged.append(candidate)
                seen.add(candidate["Id"])
        for candidate in random_candidates:
            if candidate["Id"] not in seen:
                merged.append(candidate)
                seen.add(candidate["Id"])
        recommendations = merged

    start = (page - 1) * per_page
    end = start + per_page
    response = []
    for img in recommendations[start:end]:
        copy_img = img.copy()
        if "tags_set" in copy_img:
            del copy_img["tags_set"]

        # Compute recommended boards similar to get_image_details.
        recommended_boards = []
        for board in boards_data.values():
            pinned_ids = board.get("images", [])
            total_score = 0
            valid_count = 0
            for pid in pinned_ids:
                pinned_image = images_data.get(pid)
                if pinned_image:
                    total_score += compute_full_similarity(img, pinned_image)
                    valid_count += 1
            avg_score = total_score / valid_count if valid_count else 0
            recommended_boards.append({
                "id": board["id"],
                "name": board["name"],
                "pin_count": len(pinned_ids),
                "recommendation_score": avg_score
            })
        recommended_boards.sort(key=lambda x: x["recommendation_score"], reverse=True)
        copy_img["recommended_boards"] = recommended_boards

        # Compute in_boards.
        in_boards = []
        for board in boards_data.values():
            if img["Id"] in board.get("images", []):
                in_boards.append({
                    "id": board["id"],
                    "name": board["name"],
                    "pin_count": len(board.get("images", []))
                })
        copy_img["in_boards"] = in_boards

        response.append(copy_img)
    return response


@app.get("/search")
def search_images(
    query: str = Query(..., description="Search query"),
    page: int = 1,
    per_page: int = 10,
    sort: str = Query("new", description="Sort order: old, new, top, random")
):
    """
    Searches for images whose prompt contains the query (case-insensitive)
    or whose tags match the query.
    """
    query_lower = query.lower().strip()
    results = []
    for img in all_images:
        prompt = img.get("Prompt") or ""
        if query_lower in prompt.lower() or query_lower in img["tags_set"]:
            copy_img = img.copy()
            if "tags_set" in copy_img:
                del copy_img["tags_set"]
            results.append(copy_img)
    if not results:
        raise HTTPException(status_code=404, detail="No images match your search query")
    # Apply sort order.
    if sort == "old":
        results.sort(key=lambda x: x.get("Id", 0))
    elif sort == "new":
        results.sort(key=lambda x: x.get("Id", 0), reverse=True)
    elif sort == "top":
        liked_images = [img for img in all_images if img.get("Likes", 0) > 0]
        results.sort(
            key=lambda x: (
                x.get("Likes", 0), 
                compute_custom_score(images_data[x["Id"]], liked_images, [])
            ),
            reverse=True,
        )
    elif sort == "random":
        random.shuffle(results)
    else:
        results.sort(key=lambda x: x.get("Id", 0), reverse=True)
    start = (page - 1) * per_page
    end = start + per_page
    return results[start:end]


@app.post("/like/{image_id}")
def like_image(image_id: int):
    """
    Increments the like count for the specified image.
    """
    image = images_data.get(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    image["Likes"] = image.get("Likes", 0) + 1
    save_votes()  # persist vote change
    return {"message": f"Image {image_id} liked", "Likes": image["Likes"]}


@app.post("/dislike/{image_id}")
def dislike_image(image_id: int):
    """
    Increments the dislike count for the specified image.
    """
    image = images_data.get(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    image["Dislikes"] = image.get("Dislikes", 0) + 1
    save_votes()  # persist vote change
    return {"message": f"Image {image_id} disliked", "Dislikes": image["Dislikes"]}


@app.get("/autocomplete-tags")
def autocomplete_tags(
    query: str = Query(..., description="Tag search query"),
    limit: int = Query(10, description="Maximum number of tags to return")
):
    # Collect tag counts from all images.
    tag_counts = {}
    for img in all_images:
        for tag in img.get("tags_set", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    # Filter tags by search string.
    query_lower = query.lower().strip()
    filtered_tags = {tag: count for tag, count in tag_counts.items() if query_lower in tag.lower()}
    # Sort tags by count descending.
    sorted_tags = sorted(filtered_tags.items(), key=lambda item: item[1], reverse=True)
    # Return the tag names along with their counts, limited to the specified number.
    return [{"tag": tag, "count": count} for tag, count in sorted_tags[:limit]]

@app.post("/board")
def create_board(data: dict = Body(...)):
    """
    Create a new board.
    Required:
      - name (in body): string (board name)
    """
    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Board name is required")
    new_id = max(boards_data.keys(), default=0) + 1
    boards_data[new_id] = {"id": new_id, "name": name, "images": []}
    save_boards()
    return boards_data[new_id]

@app.delete("/board/{board_id}")
def delete_board(board_id: int):
    """
    Delete an existing board.
    Path Parameter:
      - board_id: integer (ID of the board)
    """
    if board_id not in boards_data:
        raise HTTPException(status_code=404, detail="Board not found")
    del boards_data[board_id]
    save_boards()
    return {"message": f"Board {board_id} deleted"}

@app.post("/board/{board_id}/pin")
def pin_image_to_board(board_id: int, image_id: int = Query(..., description="The image ID to pin to the board")):
    """
    Pin an image to a board.
    Parameters:
      - board_id (path): board identifier.
      - image_id (query): image identifier to pin.
    """
    board = boards_data.get(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    if image_id not in images_data:
        raise HTTPException(status_code=404, detail="Image not found")
    if image_id not in board["images"]:
        board["images"].append(image_id)
    save_boards()
    return {"message": f"Image {image_id} pinned to board {board_id}"}

@app.post("/board/{board_id}/unpin")
def unpin_image_from_board(board_id: int, image_id: int = Query(..., description="The image ID to unpin from the board")):
    """
    Unpin an image from a board.
    Parameters:
      - board_id (path): board identifier.
      - image_id (query): image identifier to unpin.
    """
    board = boards_data.get(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    if image_id in board["images"]:
        board["images"].remove(image_id)
        save_boards()
        return {"message": f"Image {image_id} removed from board {board_id}"}
    raise HTTPException(status_code=404, detail="Image not pinned to this board")

@app.get("/board/{board_id}")
def get_board(board_id: int):
    board = boards_data.get(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    full_images = []
    for img_id in board["images"]:
        img = images_data.get(img_id)
        if img:
            copy_img = img.copy()
            if "tags_set" in copy_img:
                del copy_img["tags_set"]
            full_images.append(copy_img)
    result = board.copy()
    result["images"] = full_images
    return result

@app.get("/all-boards")
def get_all_boards():
    boards_list = []
    for board in boards_data.values():
        cover_images = board["images"][:3] if board["images"] else []
        boards_list.append({
            "id": board["id"],
            "name": board["name"],
            "pin_count": len(board["images"]),
            "cover_images": cover_images
        })
    return boards_list

@app.get("/board-suggestions")
def board_suggestions(
    board_id: int = Query(..., description="Board ID for which to suggest images"),
    page: int = 1,
    per_page: int = 10
):
    board = boards_data.get(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    
    pinned_ids = set(board["images"])
    
    # If the board is empty, return a default list (e.g., top liked images)
    if not board["images"]:
        recommendations = sorted(
            all_images, key=lambda x: x.get("Likes", 0), reverse=True
        )
        output = []
        for img in recommendations:
            copy_img = img.copy()
            if "tags_set" in copy_img:
                del copy_img["tags_set"]
            copy_img["recommendation_score"] = None
            output.append(copy_img)
        start = (page - 1) * per_page
        end = start + per_page
        return output[start:end]

    scored_candidates = []
    for candidate in all_images:
        if candidate["Id"] in pinned_ids:
            continue
        total_score = 0
        count = 0
        # Compute similarity from each pinned image to this candidate
        for pin_id in board["images"]:
            pin_img = images_data.get(pin_id)
            if pin_img:
                total_score += compute_full_similarity(pin_img, candidate)
                count += 1
        avg_score = total_score / count if count else 0
        scored_candidates.append((avg_score, candidate))
    
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    
    recommendations = []
    # Return recommendations with their score
    for score, candidate in scored_candidates:
        candidate_copy = candidate.copy()
        if "tags_set" in candidate_copy:
            del candidate_copy["tags_set"]
        candidate_copy["recommendation_score"] = score
        recommendations.append(candidate_copy)
    
    start = (page - 1) * per_page
    end = start + per_page
    return recommendations[start:end]

@app.get("/liked-images")
def get_liked_images(page: int = 1, per_page: int = 10):
    liked_images = [img for img in all_images if img.get("Likes", 0) > 0]
    start = (page - 1) * per_page
    end = start + per_page
    response = []
    for img in liked_images:
        copy_img = img.copy()
        if "tags_set" in copy_img:
            del copy_img["tags_set"]
        response.append(copy_img)
    return response[start:end]

@app.get("/image-file/{image_id}")
def get_image_file(image_id: int):
    image = images_data.get(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image_path = image.get("Path")
    if not image_path:
        raise HTTPException(status_code=404, detail="Image file not found")
    return FileResponse(image_path)