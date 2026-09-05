from routes.comments import ChatResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
import io
import time
import hashlib
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from PIL import Image as PILImage
import tiktoken

router = APIRouter()

#Image data used to generate image
class Image(BaseModel):
    rating: str = "" # [safe, sensitive, questionable, explicit]
    appearance: str = "" #Hair (length, color), eyes, body, etc, 
    body: str = "" #chubby, pregnant, overweight, skinny, fat, muscular thick thighs, huge ass etc
    breast_size: str = "" #small breasts, medium breasts, large breasts, huge breasts, gigantic breasts,
    clothing: str = "" #specific outfits (e.g., school uniform, long hair, bikini, lingerie, nude, etc ).
    pose: str = "" #explicit poses, standing, , looking at viewer, sitting
    expression: str = "" #happy, sad, angry, seductive smile, etc.
    camera_angle: str = "" #from above, close up, far away, ass focus, from behind, 
    setting: str = "" #the environment where the image was taken (e.g., bedroom, beach, etc. classroom, forest, night, city).
    other_tags: str = "" # other tags

class Post(BaseModel):
    title: str
    image: Image
    image_url: str
    instructions_for_next_post: str
    created_at: float = 0.0
    image_id: Optional[int] = None

class Character(BaseModel):
    id: str
    name: str
    avatar: str
    avatar_tags: Optional[str] = ""
    description: str
    prompt_prefix: str
    tags: Optional[str] = ""
    posts: List[Post] = []

class UpdateTagsPayload(BaseModel):
    tags: str

DATA_FILE = "storage/characters.json"

_img_md5_cache: Dict[str, str] = {}
_posts_link_cache: Dict[str, Any] = {
    "last_build": 0,
    "image_to_post": {},
    "post_to_image": {}
}

def _compute_file_md5(file_path: str) -> Optional[str]:
    try:
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return None
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None

def get_image_md5(file_path: str) -> Optional[str]:
    if file_path in _img_md5_cache:
        return _img_md5_cache[file_path]
    h = _compute_file_md5(file_path)
    if h:
        _img_md5_cache[file_path] = h
    return h

def find_image_id_for_post(post: Post) -> Optional[int]:
    import utils
    if not post.image_url:
        return None

    clean_url = post.image_url.split("?")[0]
    if clean_url.startswith("http://") or clean_url.startswith("https://"):
        clean_url = "/" + "/".join(clean_url.split("/")[3:])
    rel_path = clean_url.lstrip("/")
    base_name = os.path.basename(clean_url)

    # 1. Path or Basename matching
    for img_id, img in utils.images_data.items():
        img_path = img.get("Path", "")
        if img_path:
            img_clean = img_path.lstrip("/")
            if img_clean == rel_path or img_path == clean_url or img_clean.endswith(rel_path) or rel_path.endswith(img_clean):
                return int(img_id)
            if base_name and os.path.basename(img_path) == base_name:
                return int(img_id)

    # 2. File Hash (MD5) matching
    local_file_path = None
    if clean_url.startswith("/files") or clean_url.startswith("files"):
        local_file_path = str(Path(__file__).parent.parent / clean_url.lstrip("/"))
    elif os.path.exists(clean_url):
        local_file_path = clean_url

    post_md5 = None
    if local_file_path and os.path.exists(local_file_path):
        post_md5 = get_image_md5(local_file_path)

    if post_md5:
        for img_id, img in utils.images_data.items():
            img_path = img.get("Path", "")
            if not img_path:
                continue
            resolved = img_path if os.path.isabs(img_path) else str(Path(__file__).parent.parent / img_path.lstrip("/"))
            if os.path.exists(resolved):
                if get_image_md5(resolved) == post_md5:
                    return int(img_id)

    # 3. pHash matching
    if local_file_path and os.path.exists(local_file_path):
        try:
            post_phash = utils.compute_phash(local_file_path)
            if post_phash:
                for img_id, img in utils.images_data.items():
                    img_phash = img.get("pHash")
                    if img_phash:
                        try:
                            if utils.hamming_distance(post_phash, img_phash) <= 2:
                                return int(img_id)
                        except Exception:
                            pass
        except Exception:
            pass

    return None

def _refresh_posts_link_cache(force: bool = False):
    now = time.time()
    if not force and (now - _posts_link_cache["last_build"] < 30):
        return

    characters = load_characters()
    img_to_post = {}
    post_to_img = {}

    for char in characters:
        char_info = {
            "id": char.id,
            "name": char.name,
            "avatar": char.avatar,
            "prompt_prefix": char.prompt_prefix,
            "tags": char.tags or ""
        }
        for post in char.posts:
            matched_id = find_image_id_for_post(post)
            post_dict = post.model_dump() if hasattr(post, 'model_dump') else post.dict()
            if matched_id:
                post_dict["image_id"] = matched_id
                post_to_img[(char.id, post.created_at)] = matched_id
                img_to_post[matched_id] = {
                    "character": char_info,
                    "post": post_dict
                }

    _posts_link_cache["image_to_post"] = img_to_post
    _posts_link_cache["post_to_image"] = post_to_img
    _posts_link_cache["last_build"] = now

def get_post_info_for_image(image_id: int, image_dict: Optional[dict] = None) -> Optional[dict]:
    _refresh_posts_link_cache()
    if image_id in _posts_link_cache["image_to_post"]:
        return _posts_link_cache["image_to_post"][image_id]

    if image_dict:
        img_path = image_dict.get("Path", "")
        img_base = os.path.basename(img_path) if img_path else ""
        characters = load_characters()
        for char in characters:
            char_info = {
                "id": char.id,
                "name": char.name,
                "avatar": char.avatar,
                "prompt_prefix": char.prompt_prefix,
                "tags": char.tags or ""
            }
            for post in char.posts:
                if not post.image_url:
                    continue
                p_url = post.image_url.split("?")[0]
                p_base = os.path.basename(p_url)
                if (img_base and p_base and img_base == p_base) or (img_path and p_url and (p_url.endswith(img_path) or img_path.endswith(p_url))):
                    post_dict = post.model_dump() if hasattr(post, 'model_dump') else post.dict()
                    post_dict["image_id"] = image_id
                    res = {
                        "character": char_info,
                        "post": post_dict
                    }
                    _posts_link_cache["image_to_post"][image_id] = res
                    return res
    return None

def load_characters() -> List[Character]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Character(**char) for char in data]
    except Exception:
        return []

def save_characters(characters: List[Character]):
    os.makedirs("storage", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([json.loads(char.json()) if hasattr(char, 'json') else char.model_dump() for char in characters], f, indent=4)
    _refresh_posts_link_cache(force=True)

@router.get("/characters", response_model=List[Character])
def get_characters():
    _refresh_posts_link_cache()
    chars = load_characters()
    for char in chars:
        for p in char.posts:
            p.image_id = _posts_link_cache["post_to_image"].get((char.id, p.created_at))
            if not p.image_id and p.image_url:
                p.image_id = find_image_id_for_post(p)
    return chars

@router.get("/characters/{char_id}", response_model=Character)
def get_character(char_id: str):
    _refresh_posts_link_cache()
    characters = load_characters()
    for char in characters:
        if char.id == char_id:
            for p in char.posts:
                p.image_id = _posts_link_cache["post_to_image"].get((char.id, p.created_at))
                if not p.image_id and p.image_url:
                    p.image_id = find_image_id_for_post(p)
            return char
    raise HTTPException(status_code=404, detail="Character not found")

def update_avatar_tags(char: Character):
    if not char.avatar:
        return
    
    from routes import tagger
    try:
        path = None
        url = None
        if char.avatar.startswith("/files"):
            file_path = Path(__file__).parent.parent / char.avatar.lstrip("/")
            path = str(file_path)
            if not os.path.exists(path):
                print(f"Avatar file not found: {path}")
                return
        elif char.avatar.startswith("http"):
            url = char.avatar
        else:
            return

        print(f"Generating tags for {char.name}'s avatar...")
        result = tagger.interrogate_image(
            path=path, 
            url=url, 
            threshold=0.35, 
            model_name="wd14-convnextv2.v1", 
            exclude_tags=None, 
            use_cpu=False, 
            raw_tag=False
        )
        if result and "tag_string" in result:
            char.avatar_tags = result["tag_string"]
            print(f"Successfully generated tags: {char.avatar_tags[:50]}...")
    except Exception as e:
        print(f"Error getting avatar tags for {char.name}: {e}")

@router.post("/characters", response_model=Character)
def create_character(char: Character):
    characters = load_characters()
    for existing in characters:
        if existing.id == char.id:
            raise HTTPException(status_code=400, detail="Character already exists")
    
    if not char.avatar_tags:
        update_avatar_tags(char)
        
    characters.append(char)
    save_characters(characters)
    return char

@router.put("/characters/{char_id}", response_model=Character)
def edit_character(char_id: str, updated_char: Character):
    characters = load_characters()
    for i, char in enumerate(characters):
        if char.id == char_id:
            # Keep existing posts if not provided in the update
            if not updated_char.posts and char.posts:
                updated_char.posts = char.posts
            
            if (updated_char.avatar != char.avatar) or (not updated_char.avatar_tags and updated_char.avatar):
                update_avatar_tags(updated_char)
                
            characters[i] = updated_char
            save_characters(characters)
            return updated_char
    raise HTTPException(status_code=404, detail="Character not found")

@router.put("/characters/{char_id}/tags", response_model=Character)
def update_character_tags(char_id: str, payload: UpdateTagsPayload):
    characters = load_characters()
    for i, char in enumerate(characters):
        if char.id == char_id:
            char.tags = payload.tags
            characters[i] = char
            save_characters(characters)
            return char
    raise HTTPException(status_code=404, detail="Character not found")

@router.get("/characters/{char_id}/posts", response_model=List[Post])
def get_posts(char_id: str):
    _refresh_posts_link_cache()
    characters = load_characters()
    for char in characters:
        if char.id == char_id:
            for p in char.posts:
                p.image_id = _posts_link_cache["post_to_image"].get((char.id, p.created_at))
                if not p.image_id and p.image_url:
                    p.image_id = find_image_id_for_post(p)
            return char.posts
    raise HTTPException(status_code=404, detail="Character not found")

@router.post("/characters/{char_id}/posts", response_model=Post)
def create_post(char_id: str, post: Post):
    characters = load_characters()
    for i, char in enumerate(characters):
        if char.id == char_id:
            if post.created_at == 0.0:
                post.created_at = time.time()
            post.image_id = find_image_id_for_post(post)
            char.posts.insert(0, post) # Add to the beginning like Twitter
            characters[i] = char
            save_characters(characters)
            return post
    raise HTTPException(status_code=404, detail="Character not found")

@router.get("/characters/{char_id}/media")
def get_character_media(
    char_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    sort: str = Query("new")
):
    char = get_character(char_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    query_tags = (char.tags or "").strip()
    if not query_tags:
        query_tags = (char.prompt_prefix or char.name).strip()

    from routes import images as img_routes
    try:
        matched_images = img_routes.search_images(
            query=query_tags,
            page=page,
            per_page=per_page,
            sort=sort,
            can_return_empty=True
        )
    except Exception as e:
        matched_images = []

    enriched = []
    for img in matched_images:
        img_dict = dict(img) if isinstance(img, dict) else img.dict() if hasattr(img, 'dict') else {}
        post_info = get_post_info_for_image(img_dict.get("Id", -1), img_dict)
        if post_info:
            img_dict["post_info"] = post_info
        enriched.append(img_dict)

    return {
        "character_id": char.id,
        "query_tags": query_tags,
        "page": page,
        "per_page": per_page,
        "images": enriched
    }

@router.get("/posts")
def get_post():
    _refresh_posts_link_cache()
    posts = []
    characters = load_characters()
    for char in characters:
        for p in char.posts:
            post_data = p.dict() if hasattr(p, 'dict') else p.model_dump()
            post_data['character'] = {
                'id': char.id,
                'name': char.name,
                'avatar': char.avatar,
                'prompt_prefix': char.prompt_prefix,
                'tags': char.tags or '',
            }
            matched_id = _posts_link_cache["post_to_image"].get((char.id, p.created_at))
            if not matched_id and p.image_url:
                matched_id = find_image_id_for_post(p)
            post_data['image_id'] = matched_id
            posts.append(post_data)
    
    # Sort newest first
    posts.sort(key=lambda x: x.get('created_at', 0.0), reverse=True)
    return posts

@router.post("/characters/{char_id}/posts/{post_id}/image")
async def upload_post_image(
    char_id: str, post_id: str, file: UploadFile = File(...)
):
    """Upload a generated image for a specific post."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    try:
        raw_bytes = await file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read uploaded file.")

    try:
        img = PILImage.open(io.BytesIO(raw_bytes))
        img.load()
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Unsupported or corrupt image data.")

    characters = load_characters()
    char = None
    for c in characters:
        if c.id == char_id:
            char = c
            break
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
        
    post_index = -1
    try:
        target_time = float(post_id)
        for i, p in enumerate(char.posts):
            if abs(p.created_at - target_time) < 0.001:
                post_index = i
                break
    except ValueError:
        pass

    if post_index < 0:
        try:
            idx = int(post_id)
            if 0 <= idx < len(char.posts):
                post_index = idx
        except ValueError:
            pass

    if post_index < 0:
        raise HTTPException(status_code=404, detail="Post not found")

    post_obj = char.posts[post_index]
    safe_ts = str(post_obj.created_at).replace('.', '_')

    # Save to files/posts/{char_id}/{safe_ts}.png
    out_dir = Path(__file__).parent.parent / "files" / "posts" / char_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{safe_ts}.png"
    try:
        img.save(out_path, format="PNG")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {e}")

    # Update the post's image_url
    image_url = f"/files/posts/{char_id}/{safe_ts}.png"
    char.posts[post_index].image_url = image_url
    save_characters(characters)

    return {"image_url": image_url}

from routes import comments
from routes.ai_settings import load_ai_settings
import random

@router.post("/generate-post")
def generate_post(character_id: Optional[str] = None):
    if not character_id:
            # select random character among those with the fewest posts
            characters = load_characters()
            if not characters:
                raise HTTPException(status_code=404, detail="No characters found")
            
            min_posts = min(len(c.posts) for c in characters)
            candidates = [c for c in characters if len(c.posts) == min_posts]
            character_id = random.choice(candidates).id
        
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    print(f"Creating post for {character.name}")
    
    prompt = f"""You are {character.name}. {character.description.replace('{{char}}', character.name)}. \n\n\n\n Your goal is to populate the private Instagram account of {character.name} with realistic, lewd posts that drive massive engagement from her followers that fit {character.name}'s character.\n\nYou are posting a photo of yourself to your private nsfw instagram. Come up with a post to upload to your instagram.
    Include a title and details about the image you posted. Respond in json format. \n
    # Image data used to generate image (with examples)\n:
    every image element is a list of danbooru tags seperated by ",". the tags will be combined to an prompt and then used to generate an image with stable diffusion 
class Image(BaseModel):
    rating: str # [safe, sensitive, questionable, explicit]
    appearance: str #Hair (length, color), eyes, etc, coverd in cum,
    body:str #chubby, pregnant, overweight, skinny, fat, muscular thick thighs, huge ass etc
    breast_size: str # "small breasts" = (~AA to B cup size), "medium breasts" = (~C to D cup size), "large breasts" = (~E to K cup size), "huge breasts" = (~L to zz cup size), "gigantic breasts" = (~zzz cup size), (cup size is rough estimate dont include (cup sizes) in the tags only include size "description" ) 
    clothing: str #specific outfits (e.g., school uniform, long hair, bikini, lingerie, nude, etc ).
    pose: str #explicit poses, standing, , looking at viewer, sitting, female masturbation, sex, etc
    expression: str #happy, sad, angry, seductive smile, blush, tongue out
    camera_angle: str #from above, close up, far away, ass focus, from behind, or empty string for automatic angle
    setting: str #the environment where the image was taken (e.g., bedroom, beach, etc. classroom, forest, night, city).
    Most of the posts should be lewd, adult, questinable or explicit. This website is meant for jerking off. 
    """
    if character.avatar_tags:
        prompt += f"\n\nHere is the tags of your profile picture <avatar_tags_start>\n{character.avatar_tags}\n</avatar_tags_start> [USE THESE FOR REFERENCE]"

    if(len(character.posts) > 0):
        #show last 2 posts
        last_2_posts = character.posts[:3]
        prompt += f"\n\nHere are the Latest posts from this character: <previous_posts_start>\n{last_2_posts}\n<previous_posts_end> [DO NOT REPEAT PREVIOUS POSTS]"
        prompt += "\n\nCome up with a NEW post for this character. "
        

    #Generate
    try:
        tokenizer = tiktoken.get_encoding("cl100k_base")
        print("Prompt token count:", len(tokenizer.encode(prompt)))
    except Exception as e:
        print("Prompt token count:", len(prompt.split()))

    # Use centralized AI settings
    settings = load_ai_settings()

    client = comments.laptopClient

    options = {}
    if settings.override_temperature:
        options["temperature"] = settings.temperature

    response: ChatResponse = client.chat(
        model=settings.default_model,
        messages=[
            {
                "role": "system",
                "content":  prompt,
            }
        ],
        format=Post.model_json_schema(),
        options=options,
        think=settings.use_thinking
    )

    #debug print
    json_response = json.loads(response.message.content)
    print(json_response)

    # Usage prints
    input_tokens = getattr(response, "prompt_eval_count", 0)
    output_tokens = getattr(response, "eval_count", 0)
    eval_duration_ns = getattr(response, "eval_duration", 0)
    
    tokens_per_sec = 0
    if eval_duration_ns and eval_duration_ns > 0:
        tokens_per_sec = output_tokens / (eval_duration_ns / 1e9)
        
    print(f"Usage stats: {input_tokens} input tokens | {output_tokens} output tokens | {tokens_per_sec:.2f} tokens/s")

    post = Post.model_validate_json(response.message.content)
    post.image_url = ""
    post.created_at = time.time()

    #Add to posts
    create_post(character.id,post)

    return post






    

    