from fastapi import APIRouter, Query, HTTPException, Body, UploadFile, File
import utils
from typing import List, Optional, Dict, Any
from PIL import Image
import os
from pathlib import Path
import json
import io
from routes import comments
from routes.comments import ChatResponse

router = APIRouter()


@router.get("/comics")
def list_comics():
    """
    List all comics with only title, topic and a cover image (the first available image).
    """
    comics_file_path = Path(__file__).parent.parent / "comics.json"
    with open(comics_file_path, "r", encoding="utf-8") as f:
        comics_data = json.load(f)

    files_root = Path(__file__).parent.parent / "files" / "comics"
    results: List[Dict[str, Any]] = []

    for idx, comic in enumerate(comics_data):
        cover = ""

        # Prefer first panel that has an explicit image set
        for pidx, panel in enumerate(comic.get("panels", [])):
            img_url = (panel.get("image") or "").strip()
            if img_url:
                cover = img_url
                break
            # Fallback to stored file for this panel if exists
            panel_file = files_root / str(idx) / f"{pidx}.png"
            if not cover and panel_file.exists():
                cover = f"/files/comics/{idx}/{pidx}.png"
                break

        # If still no cover, pick the first image file in the comic's folder
        if not cover:
            comic_dir = files_root / str(idx)
            if comic_dir.exists():

                def sort_key(p: Path):
                    try:
                        return (0, int(p.stem))
                    except Exception:
                        return (1, p.name)

                candidates = sorted(
                    [
                        p
                        for p in comic_dir.iterdir()
                        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
                    ],
                    key=sort_key,
                )
                if candidates:
                    cover = f"/files/comics/{idx}/{candidates[0].name}"

        results.append(
            {
                "title": comic.get("title", ""),
                "topic": comic.get("topic", ""),
                "cover_image": cover,
            }
        )

    return results


@router.get("/comics/{comic_index}")
def get_comic(comic_index: int):
    """
    Get a comic by its index.
    """
    # Load the comics data from the JSON file
    comics_file_path = Path(__file__).parent.parent / "comics.json"
    with open(comics_file_path, "r", encoding="utf-8") as f:
        comics_data = json.load(f)

    # Check if the comic_index is valid
    if comic_index < 0 or comic_index >= len(comics_data):
        raise HTTPException(status_code=404, detail="Comic not found")

    # Return the requested comic
    return comics_data[comic_index]


@router.post("/comics/{comic_index}")
def save_comic(comic_index: int, comic_data: Dict[str, Any] = Body(...)):
    """
    Save (update) a comic by its index.
    """

    # validate comic_data has required fields
    if "title" not in comic_data:
        raise HTTPException(status_code=400, detail="Invalid comic data, missing title")
    if "panels" not in comic_data or not isinstance(comic_data["panels"], list):
        raise HTTPException(
            status_code=400, detail="Invalid comic data, missing or invalid panels"
        )
    for panel in comic_data["panels"]:
        if "prompt" not in panel:
            panel["prompt"] = ""
        if "image" not in panel:
            panel["image"] = ""
        if "texts" not in panel or not isinstance(panel["texts"], list):
            panel["texts"] = []

    # Load the comics data from the JSON file
    comics_file_path = Path(__file__).parent.parent / "comics.json"
    with open(comics_file_path, "r", encoding="utf-8") as f:
        comics_data = json.load(f)

    if comic_index == -1:
        # Append new comic
        comics_data.append(comic_data)
        comic_index = len(comics_data) - 1
    # Check if the comic_index is valid
    elif comic_index < 0 or comic_index >= len(comics_data):
        raise HTTPException(status_code=404, detail="Comic not found")

    # Update the comic data
    comics_data[comic_index] = comic_data

    # Save the updated comics data back to the JSON file
    with open(comics_file_path, "w", encoding="utf-8") as f:
        json.dump(comics_data, f, indent=4)

    return {"message": "Comic updated successfully", "comic_index": comic_index}


# endpoint to save images to files/comics/:comic_index/:panel_index.png from base64 string
# and returns "{"image_url": "/files/comics/:comic_index/:panel_index.png"}"
@router.post("/comics/{comic_index}/panels/{panel_index}/image")
async def upload_panel_image(
    comic_index: int, panel_index: int, file: UploadFile = File(...)
):
    # Validate content type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    # Read bytes
    try:
        raw_bytes = await file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read uploaded file.")

    # Validate image
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img.load()
        # Normalize mode for PNG
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    except Exception:
        raise HTTPException(
            status_code=400, detail="Unsupported or corrupt image data."
        )

    # Validate indices
    comics_file_path = Path(__file__).parent.parent / "comics.json"
    with open(comics_file_path, "r", encoding="utf-8") as f:
        comics_data = json.load(f)
    if comic_index < 0 or comic_index >= len(comics_data):
        raise HTTPException(status_code=404, detail="Comic not found")
    panels = comics_data[comic_index].get("panels", [])
    if panel_index < 0 or panel_index >= len(panels):
        raise HTTPException(status_code=404, detail="Panel not found")

    # Save PNG to files/comics/{comic_index}/{panel_index}.png overwriting existing file if any
    out_dir = Path(__file__).parent.parent / "files" / "comics" / str(comic_index)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{panel_index}.png"
    try:
        img.save(out_path, format="PNG")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {e}")

    return {"image_url": f"/files/comics/{comic_index}/{panel_index}.png"}


comic_ai_prompt = """You are an AI Comic Generator assistant. Your task is to create engaging comic book stories with multiple panels based on user prompts.

For each comic you generate, you must:
1. Create a compelling title that captures the essence of the story
2. Design 4-6 panels that tell a complete narrative arc
3. For each panel, provide:
   - A detailed image prompt describing the visual scene, characters, setting, mood, and artistic style
   - Dialog or narration text that advances the story
   - Proper panel composition and pacing

Format your response as a JSON object with this structure:
{
  "title": "Comic Title Here",
  "topic": "Brief summary of the comic's theme or subject",
  "panels": [
    {
      "prompt": "prompt for image generation",
      "texts": [
        "Dialog or narration"
      ]
    }
  ]
}

Guidelines:
- Make image prompts detailed with specific visual elements, character descriptions like hair color, clothing, expressions, pose, 
Output should be in comma-separated tags, not sentences.
Use anime-style conventions: 1girl, 2girls, 1boy, long hair, blue eyes, school uniform, standing, smile, looking at viewer, sky, sunset, detailed background, etc.
Use commas to separate tags.
Always expand with character appearance, clothing, pose, expression, setting, lighting, and atmosphere.
Keep it descriptive but concise, avoiding filler words.
Examples:
---
girl with long hair in a field: 
 1girl, long hair, flowing hair, open field, green grass, flower petals in wind, sunlight, blue sky, white clouds, hair blowing, standing pose, peaceful expression, anime style, vibrant colors, soft shading, detailed background
girl with large breasts and long hair in a field:
Enhanced Output: 1girl, large breasts, seductive pose, long hair, flowing hair, open field, green grass, flower petals in wind, sunlight, blue sky, white clouds, hair blowing, standing pose, sultry expression, anime style, vibrant colors, soft shading, detailed background
---
Jinx from arcane having sex from behind:
 1girl, jinx \(league of legends\), object insertion, anus, hetero, penis, pov, vaginal, ass, sex, 1boy, pillow, nude, anal, long hair, sex toy, completely nude, breasts, braid, anal object insertion, uncensored, blue hair, blush, sex from behind, pussy, solo focus, bed sheet, choker, ass grab, looking at viewer, nipples, from behind, doggystyle, ass focus, open mouth, looking back, top-down bottom-up, butt plug, small breasts, on bed, all fours, male pubic hair, anal beads, pubic hair, black choker
---
 Sexy maid
1girl, breasts, solo, maid, apron, maid headdress, cleavage, short sleeves, large breasts, indoors, blue eyes, puffy sleeves, jewelry, blonde hair, puffy short sleeves, parted lips, earrings, detached collar, looking at viewer, bow, short hair, window, frills, bowtie, cup, black bow, blush, lips, dress, white apron, collarbone, waist apron, maid apron, black dress,
...
location, breasts size, body. avoid sentences use simple phrases and tags of only what is visible in the image.
- Note the image generator has no context to build upon, and cant understand sentences, so be explicit in your descriptions
- Keep dialog concise and impactful
- Ensure panels flow logically to tell a coherent story
- Consider comic book conventions (establishing shots, close-ups, action sequences)
- Vary panel composition for visual interest

Here are example comics for reference:
"""


@router.get("/generate-comic")
def generate_comic(prompt: str = Query(..., description="Prompt for the comic panel")):
    """
    Generate a full comic image based on the provided prompt.
    """
    # load comic_examples.json

    examples_file_path = Path(__file__).parent.parent / "comic_examples.json"
    with open(examples_file_path, "r", encoding="utf-8") as f:
        examples = json.load(f)

    full_prompt = (
        comic_ai_prompt
        + str(examples)
        + f'\n\n---\n\nNow create a comic based on this prompt:\n"{prompt}"\n\nGenerate the comic JSON:'
    )

    response: ChatResponse = comments.get_ollama_client().chat(
        model=comments.get_default_model(),
        messages=[{"role": "system", "content": full_prompt}],
        format={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "topic": {"type": "string"},
                "panels": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string"},
                            "texts": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["prompt", "texts"],
                    },
                },
            },
            "required": ["title", "topic", "panels"],
        },
        options=comments.get_ollama_options()
    )
    comments.print_usage(response)
    comic = json.loads(response["message"]["content"])

    save = save_comic(-1, comic)

    return save["comic_index"]


@router.get("/comics/{comic_index}/generate-panel/{panel_index}")
def generate_comic_panel(
    comic_index: int,
    panel_index: int,
    instructions: Optional[str] = Query(
        "", description="Additional instructions for the panel generation"
    ),
):
    """
    Generate a specific panel image for the comic.
    """
    comic = get_comic(comic_index)

    new_panel = False

    if panel_index == -1:
        new_panel = True
        panel_index = len(comic["panels"])
        comic["panels"].append({"prompt": "", "texts": []})
    elif panel_index < 0 or panel_index >= len(comic["panels"]):
        raise HTTPException(status_code=404, detail="Panel not found")

    panel = comic["panels"][panel_index]

    examples_file_path = Path(__file__).parent.parent / "comic_examples.json"
    with open(examples_file_path, "r", encoding="utf-8") as f:
        examples = json.load(f)

    system_prompt = (
        comic_ai_prompt
        + str(examples)
        + "\n\n---\n\nYou are generating a panel for the comic below.\n"
        + str(comic)
    )

    if not new_panel:
        system_prompt += f"\nThe current panel to update is:\n{str(panel)}\nUpdate and improve the image prompt and dialog for this panel."
    else:
        system_prompt += "\nCreate a new panel to fit into the overall comic narrative to continue the story."

    system_prompt += "\nFocus on creating a vivid and detailed image prompt that captures the scene, characters, and mood. Keep dialog concise and relevant to the action.\n\n"

    print("System Prompt:", system_prompt)

    response: ChatResponse = comments.get_ollama_client().chat(
        model=comments.get_default_model(),
        messages=[
            {"role": "system", "content": system_prompt + str(panel)},
            {
                "role": "user",
                "content": (
                    f"Additional instructions: {instructions}" if instructions else ""
                ),
            },
        ],
        format={
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "texts": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["prompt", "texts"],
        },
        options=comments.get_ollama_options()
    )
    comments.print_usage(response)

    updated_panel = json.loads(response["message"]["content"])
    comic["panels"][panel_index] = updated_panel
    save_comic(comic_index, comic)
    return updated_panel


from RedDownloader import RedDownloader
from routes import tagger, comments


@router.post("/create-examples")
def create_examples(
    url: str = Query(
        ..., description="URL of the Reddit thread to create comic examples from"
    )
):

    title = RedDownloader.GetPostTitle(url).Get()

    # sanitize title to be a valid filename
    title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip()

    print(f"Creating comic example for Reddit thread: {title}")

    path = f"./comic_creator/{title}"

    # check if isnt downloaded
    if not os.path.exists(path):
        RedDownloader.Download(
            url,
            destination="./comic_creator/",
            output=title,
        )

    comic = {"title": title, "panels": []}

    # loop through all images in the path
    for root, dirs, files in os.walk(path):
        for file_idx, file in enumerate(files):
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):

                img_path = os.path.join(root, file)
                print(f"Processing image {file_idx + 1}/{len(files)}: {file}")

                prompt = tagger.process_image(path=img_path)["tag_string"]
                print(f"  Generated prompt: {prompt[:100]}...")

                texts = []

                response: ChatResponse = comments.get_ollama_client().chat(
                    model=comments.get_default_model(),
                    messages=[
                        {
                            "role": "system",
                            "content": f"You are a text extractor for comic panels. Extract any dialog or narration text present in the image. Split images into seperate strings based on text boxes or natural breaks. Return an array of text strings. If no text is present, return an empty array.",
                            "images": [img_path],
                        }
                    ],
                    format={
                        "type": "object",
                        "properties": {
                            "texts": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["texts"],
                    },
                    options=comments.get_ollama_options()
                )
                comments.print_usage(response)
                extracted = json.loads(response["message"]["content"])
                if "texts" in extracted:
                    texts = extracted["texts"]
                print(f"  Extracted {len(texts)} text elements")
                comic["panels"].append({"prompt": prompt, "texts": texts})

    # examples_file_path = Path(__file__).parent.parent / "comic_examples.json"
    # if examples_file_path.exists():
    #     with open(examples_file_path, "r", encoding="utf-8") as f:
    #         examples = json.load(f)
    # else:
    #     examples = []
    # examples.append(comic)
    # with open(examples_file_path, "w", encoding="utf-8") as f:
    #     json.dump(examples, f, indent=4)
    return comic
