from ollama import ChatResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import os
import io
import time
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from PIL import Image as PILImage

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
    title:str
    image: Image
    image_url: str
    instructions_for_next_post:str
    created_at: float = 0.0

class Character(BaseModel):
    id:str
    name:str
    avatar:str
    description:str
    prompt_prefix:str
    posts: List[Post] = []

DATA_FILE = "storage/characters.json"

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
        # Use json.loads(char.json()) to handle enums/objects cleanly across Pydantic v1 and v2
        json.dump([json.loads(char.json()) if hasattr(char, 'json') else char.model_dump() for char in characters], f, indent=4)

@router.get("/characters", response_model=List[Character])
def get_characters():
    return load_characters()

@router.get("/characters/{char_id}", response_model=Character)
def get_character(char_id: str):
    characters = load_characters()
    for char in characters:
        if char.id == char_id:
            return char
    raise HTTPException(status_code=404, detail="Character not found")

@router.post("/characters", response_model=Character)
def create_character(char: Character):
    characters = load_characters()
    for existing in characters:
        if existing.id == char.id:
            raise HTTPException(status_code=400, detail="Character already exists")
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
            characters[i] = updated_char
            save_characters(characters)
            return updated_char
    raise HTTPException(status_code=404, detail="Character not found")

@router.get("/characters/{char_id}/posts", response_model=List[Post])
def get_posts(char_id: str):
    characters = load_characters()
    for char in characters:
        if char.id == char_id:
            return char.posts
    raise HTTPException(status_code=404, detail="Character not found")

@router.post("/characters/{char_id}/posts", response_model=Post)
def create_post(char_id: str, post: Post):
    characters = load_characters()
    for i, char in enumerate(characters):
        if char.id == char_id:
            if post.created_at == 0.0:
                post.created_at = time.time()
            char.posts.insert(0, post) # Add to the beginning like Twitter
            characters[i] = char
            save_characters(characters)
            return post
    raise HTTPException(status_code=404, detail="Character not found")

@router.get("/posts")
def get_post():
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
            }
            posts.append(post_data)
    
    # Sort newest first
    posts.sort(key=lambda x: x.get('created_at', 0.0), reverse=True)
    return posts

@router.post("/characters/{char_id}/posts/{post_index}/image")
async def upload_post_image(
    char_id: str, post_index: int, file: UploadFile = File(...)
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
    if post_index < 0 or post_index >= len(char.posts):
        raise HTTPException(status_code=404, detail="Post not found")

    # Save to files/posts/{char_id}/{post_index}.png
    out_dir = Path(__file__).parent.parent / "files" / "posts" / char_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{post_index}.png"
    try:
        img.save(out_path, format="PNG")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {e}")

    # Update the post's image_url
    image_url = f"/files/posts/{char_id}/{post_index}.png"
    char.posts[post_index].image_url = image_url
    save_characters(characters)

    return {"image_url": image_url}

from routes import comments
import random

use_thinking = False
use_laptop = True

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
    
    prompt = f"""You are {character.name}. {character.description}. \n\n You are posting a photo of yourself to your private nsfw instagram. Come up with a post to upload to your instagram.
    Include a title and details about the image you posted. Respond in json format. \n
    # Image data used to generate image with examples\n:
    every image element is a list of tags seperated by ","
class Image(BaseModel):
    rating: str # [safe, sensitive, questionable, explicit]
    appearance: str #Hair (length, color), eyes, etc, 
    body:str #chubby, pregnant, overweight, skinny, fat, muscular thick thighs, huge ass etc
    breast_size: str #small breasts (~AA to B cup size), medium breasts(~C to D cup size), large breasts (~E to K cup size), huge breasts (~L to zz cup size), gigantic breasts (~zzz cup size), (cup size is rough estimate) 
    clothing: str #specific outfits (e.g., school uniform, long hair, bikini, lingerie, nude, etc ).
    pose: str #explicit poses, standing, , looking at viewer, sitting
    expression: str #happy, sad, angry, seductive smile, etc.
    camera_angle: str #from above, close up, far away, ass focus, from behind, 
    setting: str #the environment where the image was taken (e.g., bedroom, beach, etc. classroom, forest, night, city).
    Most of the posts should be lewd, adult, questinable or explicit. This website is meant for jerking off
    """

    if(len(character.posts) > 0):
        #show last 2 posts
        last_2_posts = character.posts[:3]
        prompt += f"\n\nHere are the Latest posts from this character:\n{last_2_posts}"
        prompt += "\n\nCome up with a new post for this character."
        

    #Generate

    if(use_laptop):
        client = comments.laptopClient
    else:
        client = comments.OllamaClient

    response: ChatResponse = client.chat(
        model=comments.default_model,
        messages=[
            {
                "role": "system",
                "content":  prompt,
            }
        ],
        format=Post.model_json_schema(),
        think=use_thinking
    )

    #debug print
    json_response = json.loads(response.message.content)
    print(json_response)

    post = Post.model_validate_json(response.message.content)
    post.image_url = ""
    post.created_at = time.time()

    #Add to posts
    create_post(character.id,post)

    return post






    

    