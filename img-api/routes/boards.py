from fastapi import APIRouter, HTTPException, Query, Body
import utils  # changed from "from .. import utils"
# Added import for the helper from images route.
from .images import add_boards_info
from concurrent.futures import ThreadPoolExecutor

router = APIRouter()

@router.post("/board")
def create_board(data: dict = Body(...)):
    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Board name is required")
    new_id = max(utils.boards_data.keys(), default=0) + 1
    utils.boards_data[new_id] = {"id": new_id, "name": name, "images": []}
    utils.save_boards()
    return utils.boards_data[new_id]

@router.delete("/board/{board_id}")
def delete_board(board_id: int):
    if board_id not in utils.boards_data:
        raise HTTPException(status_code=404, detail="Board not found")
    del utils.boards_data[board_id]
    utils.save_boards()
    return {"message": f"Board {board_id} deleted"}

@router.post("/board/{board_id}/pin")
def pin_image_to_board(board_id: int, image_id: int = Query(..., description="The image ID to pin to the board")):
    board = utils.boards_data.get(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    if image_id not in utils.images_data:
        raise HTTPException(status_code=404, detail="Image not found")
    if image_id not in board["images"]:
        board["images"].append(image_id)
    utils.save_boards()
    return {"message": f"Image {image_id} pinned to board {board_id}"}

@router.post("/board/{board_id}/unpin")
def unpin_image_from_board(board_id: int, image_id: int = Query(..., description="The image ID to unpin from the board")):
    board = utils.boards_data.get(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    if image_id in board["images"]:
        board["images"].remove(image_id)
        utils.save_boards()
        return {"message": f"Image {image_id} removed from board {board_id}"}
    raise HTTPException(status_code=404, detail="Image not pinned to this board")

@router.get("/board/{board_id}")
def get_board(board_id: int):
    board = utils.boards_data.get(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    full_images = []
    for img_id in board["images"]:
        img = utils.images_data.get(img_id)
        if img:
            copy_img = img.copy()
            copy_img.pop("tags_set", None)
            full_images.append(copy_img)
    result = board.copy()
    result["images"] = full_images
    return result

@router.get("/all-boards")
def get_all_boards():
    boards_list = []
    for board in utils.boards_data.values():
        cover_ids = board["images"][:3] if board["images"] else []
        cover_images = []
        for img_id in cover_ids:
            img = utils.images_data.get(img_id)
            if img:
                cover_images.append(img.get("Path"))
        boards_list.append({
            "id": board["id"],
            "name": board["name"],
            "pin_count": len(board["images"]),
            "cover_images": cover_images
        })
    return boards_list

@router.get("/board-suggestions")
def board_suggestions(board_id: int = Query(..., description="Board ID for which to suggest images"),
                      page: int = 1, per_page: int = 10):
    board = utils.boards_data.get(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    pinned_ids = set(board["images"])
    
    # Parse the board tags into a set for comparison
    board_tags_set = {t.lower() for t in board.get("tags", "").split(",") if t.strip()}

    if not board["images"]:
        recommendations = sorted(utils.all_images, key=lambda x: x.get("Likes", 0), reverse=True)
        output = []
        for img in recommendations:
            copy_img = img.copy()
            copy_img.pop("tags_set", None)
            copy_img["recommendation_score"] = None
            output.append(copy_img)
        return output[(page - 1) * per_page: page * per_page]

    pin_imgs = [img for img in (utils.images_data.get(pid) for pid in board["images"]) if img]

    def compute_score(candidate):
        if candidate["Id"] in pinned_ids:
            return None
        similarities = [utils.compute_full_similarity(pin, candidate) for pin in pin_imgs]
        avg_score = sum(similarities) / len(similarities) if similarities else 0
        # Compute tag similarity from board tags vs candidate tags
        candidate_tags_set = set()
        if "tags" in candidate:
            candidate_tags_set = {t.lower() for t in candidate.get("tags", "").split(",") if t.strip()}
        tag_similarity = 0
        if board_tags_set:
            tag_similarity = len(board_tags_set & candidate_tags_set) / len(board_tags_set)
        # Combine the computed similarity and tag similarity using weights
        combined_score = avg_score * 0.7 + tag_similarity * 0.3
        return (combined_score, candidate)

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(compute_score, utils.all_images))
    scored_candidates = [r for r in results if r is not None]
    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    recommendations = []
    for score, candidate in scored_candidates:
        candidate_copy = candidate.copy()
        candidate_copy.pop("tags_set", None)
        candidate_copy["recommendation_score"] = score
        recommendations.append(candidate_copy)

    return recommendations[(page - 1) * per_page: page * per_page]
