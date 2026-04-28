from fastapi import APIRouter, HTTPException, Body, Query
from pathlib import Path
import json, time
import utils
from typing import Dict, Any, List

router = APIRouter()

STORIES_FILE = Path(__file__).parent.parent / "stories.json"

def _load_stories() -> Dict[str, Any]:
    if STORIES_FILE.exists():
        with open(STORIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_stories(data: Dict[str, Any]):
    with open(STORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _json_safe(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (set, tuple, list)):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k == "tags_set":  # drop internal sets
                continue
            out[str(k)] = _json_safe(v)
        return out
    # fallback to string
    return str(value)


def _resolve_slide(slide):
    img = utils.images_data.get(slide["image_id"])
    if not img:
        return None
    # minimal subset or full sanitized dict
    safe_img = _json_safe(img)
    return {
        "image_id": img["Id"],
        "image": safe_img,
        "caption": slide.get("caption")
        or img.get("description")
        or (img.get("Prompt") or "").split(",")[0].strip(),
        "duration": slide.get("duration", 4.0),
    }


from routes import comments, tags, images


story_generator_system_prompt = f"""You are a highlight generator for google photos-like nsfw image application. You will generate a story consisting of a 5-10 images selected from a user's photo collection. 

The story should have a clear theme or narrative, such as best butts, biggest breasts, cute maids, completely naked, covered cum, beach, nurses, dildos, nuns, lingerie, tentacles etc. Those are just examples, you should come up with your own unique themes.

You will first come up with a theme and a search query to find relevant images from the user's collection. Then, you will select 5-10 images that best fit the theme of the story.

Search query should be one or two short tags to find images with said tag in the user's photo collection. Search query is not a sentence You are not generating new images only selecting from existing images. You do not need to copy the example prompts provided, they are only for reference to help you understand the user's photo collection and prompt format. DO NOT INCLUDE STYLE AND QUALITY TAGS IN THE SEARCH QUERY like masterpiece, best quality etc.

You may also use dates to create stories by using the query format "date:YYYY-MM-DD or date:YYYY-MM or date:YYYY" in your search query. For example, if the user has many photos from July 2023, you might use the query "date:2023-07" to find those images. For example best of April 2025. or remember this day January 1st 2024. etc. or one year ago today. Today's date is {time.strftime("%Y-%m-%d")}.
"""


@router.post("/stories/generate")
def generate_story():

    print("Generating story...")

    # get random prompts from user's photo collection
    random_prompts = comments.get_random_reference_prompts(10)

    dates = utils.get_image_count_per_day(10)

    create_based_on_dates = False

    #33% chance to create based on dates
    # import random
    # if random.random() < 0.33:
    #     create_based_on_dates = True
    #     print("Creating story based on dates.")

    messages = [
        {"role": "system", "content": story_generator_system_prompt},
        {
            "role": "user",
            "content": "Here are some example prompts from the user's photo collection to help you generate a story:"
            + "\n".join(random_prompts),
            "temp": True,
        },
        {
            "role": "user",
            "content": f"Here are some dates with image counts from the user's photo collection to help you generate a story based on these dates: {dates}",
            "temp": True,
        },
        {
            "role": "user",
            "content": create_based_on_dates and "Generate a highlight theme and search query date for a image story from a specific date. set search_query to date:xxxx etc" or "Generate a highlight theme and search query for a nsfw image story.",
        },
    ]

    print("Selecting story theme and search query...")
    response1 = comments.OllamaClient.chat(
        model=comments.default_model,
        messages=clean_messages(messages, False),
        format={
            "type": "object",
            "properties": {
                "theme": {"type": "string", "description": "The theme of the story"},
                "search_query": {
                    "type": "string",
                    "description": "The search query to find relevant images",
                },
            },
            "required": ["theme", "search_query"],
        },
    )

    response1 = json.loads(response1["message"]["content"])

    print("Generated story theme:", response1["theme"])
    print("Generated search query:", response1["search_query"])

    # clean temp messages
    messages = clean_messages(messages)

    search_count = 50

    _images = images.search_images(
        query=response1["search_query"],
        per_page=search_count,
        sort="random",
        can_return_empty=True,
    )

    search_query = response1["search_query"]

    attempts = 0

    while len(_images) == 0:

        if attempts >= 3:
            print(
                f"Failed to find images for search query '{search_query}' after {attempts} attempts. Aborting."
            )
            return messages

        attempts += 1

        _tags = tags.autocomplete_tags(query=search_query, limit=30, min_score=0.3)

        messages.append(
            {
                "role": "assistant",
                "content": str(response1),
                "temp": True,
            }
        )

        print(
            f"Search for '{search_query}' returned no images. Suggesting closest tags: {_tags}"
        )

        messages.append(
            {
                "role": "user",
                "content": f"Searching for '{search_query}' didn't return any images. Here are the closest tags found in the user's photo collection for your search query '{search_query}': {_tags}. Refine your search query to find images that fit your theme.",
                "temp": True,
            },
        )

        response2 = comments.OllamaClient.chat(
            model=comments.default_model,
            messages=clean_messages(messages, False),
            format={
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                    }
                },
                "required": ["search_query"],
            },
        )

        response2 = json.loads(response2["message"]["content"])
        selected_tag = response2["search_query"].replace("_", " ")
        search_query = selected_tag
        print(f"Refined search query to '{selected_tag}'")

        _images = images.search_images(
            query=selected_tag,
            per_page=search_count,
            sort="random",
            can_return_empty=True,
        )

        messages = clean_messages(messages)
    else:
        selected_tag = response1["search_query"]

    print(f"Found {_images.__len__()} images for search query '{selected_tag}'")

    messages.append(
        {
            "role": "assistant",
            "content": str(
                {
                    "theme": response1["theme"],
                    "search_query": selected_tag,
                }
            ),
        }
    )

    formatted_images = clean_search_images(_images)



    messages.append(
        {
            "role": "user",
            "content": f"Here are the images found for search query '{selected_tag}': {formatted_images}. Select 5-10 images that best fit the theme '{response1['theme']}' and provide their image_ids and come up with a caption for the images. if you wish to add more images with a different search query, set add_more_images to true.",
        }
    )
    print("Selecting images for the story...")
    response3 = comments.OllamaClient.chat(
        model=comments.default_model,
        messages=clean_messages(messages, False),
        format={
            "type": "object",
            "properties": {
                "selected_images": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "image_id": {"type": "integer"},
                            "caption": {"type": "string"},
                        },
                        "required": ["image_id", "caption"],
                    },
                    "description": "List of selected images for the story",
                },
                "add_more_images": {
                    "type": "boolean",
                    "description": "Whether to add more images to the story",
                },
            },
            "required": ["selected_images"],
        },
    )

    response3 = json.loads(response3["message"]["content"])
    selected = response3.get("selected_images", [])
    print("Selected images for story:", selected)
    if not selected:
        return messages

    # NEW: Handle add_more_images in a loop (max MAX_ADDITIONS iterations)
    selected_ids = {item["image_id"] for item in selected if "image_id" in item}
    additions = 0
    prev_queries = {selected_tag}

    MAX_ADDITIONS = 5

    while response3.get("add_more_images") and additions < MAX_ADDITIONS:
        additions += 1

        # Ask for a complementary search query not used before
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Theme: '{response1['theme']}'. Previously used queries: {sorted(list(prev_queries))}. "
                    f"Already selected image_ids: {sorted(list(selected_ids))}. "
                    "Propose a new complementary search_query (different from previous) to continue the story."
                ),
                "temp": True,
            }
        )
        next_query_resp = comments.OllamaClient.chat(
            model=comments.default_model,
            messages=clean_messages(messages, False),
            format={
                "type": "object",
                "properties": {"search_query": {"type": "string"}},
                "required": ["search_query"],
            },
        )
        next_query_obj = json.loads(next_query_resp["message"]["content"])
        next_query = next_query_obj.get("search_query", "").strip() or selected_tag
        # Avoid repeating same query; if repeated, break this cycle
        if next_query in prev_queries:
            print(f"Proposed query '{next_query}' already used. Stopping additions.")
            break
        prev_queries.add(next_query)

        # Search with the new query
        more_images = images.search_images(
            query=next_query, per_page=search_count, sort="random", can_return_empty=True
        )

        # If empty, try a simple refinement using closest tags once
        if not more_images:
            close_tags = tags.autocomplete_tags(query=next_query, limit=30, min_score=0.3)
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"No images found for '{next_query}'. Closest tags in user's collection: {close_tags}. "
                        "Refine the search_query."
                    ),
                    "temp": True,
                }
            )
            refine_resp = comments.OllamaClient.chat(
                model=comments.default_model,
                messages=clean_messages(messages, False),
                format={
                    "type": "object",
                    "properties": {"search_query": {"type": "string"}},
                    "required": ["search_query"],
                },
            )
            refine_obj = json.loads(refine_resp["message"]["content"])
            refined_query = refine_obj.get("search_query", "").replace("_", " ").strip() or next_query
            print(f"Refined additional search query to '{refined_query}'")
            prev_queries.add(refined_query)
            more_images = images.search_images(
                query=refined_query, per_page=search_count, sort="random", can_return_empty=True
            )

        # Filter out already selected images
        candidate_images = [
            img for img in more_images if img.get("Id") not in selected_ids
        ]
        formatted_more = [
            {
                "image_id": img["Id"],
                "caption": img.get("description") or (img.get("Prompt") or "").strip(),
            }
            for img in candidate_images
        ]

        if not formatted_more:
            print("No new candidates found for additional selection. Stopping additions.")
            break

        # Ask the model to pick 1-5 additional images and whether to continue
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Here are additional candidate images: {formatted_more}. "
                    f"Previously selected image_ids: {sorted(list(selected_ids))}. "
                    "Select 1-5 additional images that fit the theme and are not previously selected. "
                    "Return selected_images and set add_more_images if you want to continue."
                ),
                "temp": True,
            }
        )
        pick_more_resp = comments.OllamaClient.chat(
            model=comments.default_model,
            messages=clean_messages(messages, False),
            format={
                "type": "object",
                "properties": {
                    "selected_images": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "image_id": {"type": "integer"},
                                "caption": {"type": "string"},
                            },
                            "required": ["image_id", "caption"],
                        },
                    },
                    "add_more_images": {"type": "boolean"},
                },
                "required": ["selected_images"],
            },
        )
        response3 = json.loads(pick_more_resp["message"]["content"])
        additional = [
            item for item in response3.get("selected_images", [])
            if item.get("image_id") not in selected_ids
        ]
        if not additional:
            print("Model returned no valid additional selections. Stopping additions.")
            break

        # Merge additional selections
        selected.extend(additional)
        for it in additional:
            selected_ids.add(it["image_id"])

        # Clean temp messages to keep context small
        messages = clean_messages(messages)

    # save story
    data = _load_stories()
    story_id = max([int(k) for k in data.keys()], default=0)
    story_id += 1
    story_record = {
        "id": story_id,
        "title": response1["theme"],
        "cover_image_id": selected[0]["image_id"],
        "created_at": int(time.time()),
        "slides": [
            {
                "image_id": item["image_id"],
                "caption": item.get("caption"),
                "duration": 4.0,
            }
            for item in selected
        ],
    }
    data[str(story_id)] = story_record
    _save_stories(data)

    return story_record


def clean_search_images(images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    formatted_images = []
    for img in images:
        formatted_images.append(
            {
                "image_id": img["Id"],
                "caption": img.get("description") or (img.get("Prompt") or "").strip(),
            }
        )
    return formatted_images


@router.get("/stories")
def list_stories():
    data = _load_stories()
    stories = []
    for sid, s in data.items():
        cover = utils.images_data.get(s.get("cover_image_id"))
        cover_img = None
        if cover:
            cover_img = {"Id": cover["Id"], "Path": cover["Path"]}
        stories.append(
            {
                "id": s["id"],
                "title": s["title"],
                "cover_image_id": s["cover_image_id"],
                "cover": cover_img,
                "created_at": s.get("created_at"),
                "slides_count": len(s.get("slides", [])),
            }
        )
    # newest first
    stories.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return stories


@router.get("/stories/{story_id}")
def get_story(story_id: int):
    data = _load_stories()
    story = data.get(str(story_id))
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    slides = []
    for slide in story.get("slides", []):
        resolved = _resolve_slide(slide)
        if resolved:
            slides.append(resolved)
    return {
        "id": story["id"],
        "title": story["title"],
        "cover_image_id": story["cover_image_id"],
        "created_at": story.get("created_at"),
        "slides": slides,
    }


@router.post("/stories")
def upsert_story(payload: Dict[str, Any] = Body(...)):
    """
    { id?: int, title: str, slides: [{ image_id:int, caption?:str, duration?:number }], cover_image_id?:int }
    """
    if "title" not in payload or "slides" not in payload:
        raise HTTPException(status_code=400, detail="Missing title or slides")
    slides = payload["slides"]
    if not isinstance(slides, list) or len(slides) == 0:
        raise HTTPException(status_code=400, detail="Slides must be a non-empty array")

    # validate images exist
    for s in slides:
        if s.get("image_id") not in utils.images_data:
            raise HTTPException(
                status_code=404, detail=f"Image {s.get('image_id')} not found"
            )

    data = _load_stories()
    story_id = payload.get("id") or (max([int(k) for k in data.keys()], default=0) + 1)
    cover_id = payload.get("cover_image_id") or slides[0]["image_id"]

    story = {
        "id": story_id,
        "title": payload["title"],
        "cover_image_id": cover_id,
        "created_at": payload.get("created_at") or int(time.time()),
        "slides": [
            {
                "image_id": s["image_id"],
                "caption": s.get("caption"),
                "duration": s.get("duration", 4.0),
            }
            for s in slides
        ],
    }
    data[str(story_id)] = story
    _save_stories(data)
    return {"id": story_id}


@router.post("/stories/from-board/{board_id}")
def create_story_from_board(
    board_id: int, title: str = Query(None), duration: float = Query(4.0)
):
    board = utils.boards_data.get(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    image_ids: List[int] = [
        i for i in board.get("images", []) if i in utils.images_data
    ]
    if not image_ids:
        raise HTTPException(status_code=400, detail="Board has no images")

    slides = [{"image_id": i, "duration": duration} for i in image_ids]
    data = _load_stories()
    story_id = max([int(k) for k in data.keys()], default=0) + 1
    story = {
        "id": story_id,
        "title": title or board.get("name", f"Board {board_id}"),
        "cover_image_id": image_ids[0],
        "created_at": int(time.time()),
        "slides": slides,
    }
    data[str(story_id)] = story
    _save_stories(data)
    return {"id": story_id}


def clean_messages(messages, remove_temp=True):
    # remove messages with temp true and remove temp field
    formatted = []
    for m in messages:
        if remove_temp and m.get("temp"):
            continue
        fm = {k: v for k, v in m.items() if k != "temp"}
        formatted.append(fm)
    return formatted
