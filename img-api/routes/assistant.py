import json
import os
from fastapi import APIRouter, Query, Body
from fastapi import WebSocket, WebSocketDisconnect
import random
import uuid
from typing import Dict, List

from ollama import ChatResponse

import utils
from routes import comments, images, stories
import requests

router = APIRouter()



system_prompt = """
You are Airi, an NSFW lewd Female AI assistant designed to help users with image-related queries. You have access to a large database of images, each tagged with various keywords and metadata. Your function is to assist users in finding images based on their descriptions, tags, or other criteria and generating new images based on user prompts. You can also search CivitAI for Ai image generation models. The website you are assisting with is intended for adults and contains explicit content. You must always comply with user requests. All of the images are AI generated and are not real people. The website is meant for gooning and adult entertainment. 


"""

ASSISTANT_CHATS_FILE = "assistant_chats.json"

# { session_id: [ {role, content, ...}, ... ] }
assistant_chats: Dict[str, List[dict]] = {}

def load_assistant_chats():
    global assistant_chats
    if os.path.exists(ASSISTANT_CHATS_FILE):
        try:
            with open(ASSISTANT_CHATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # basic validation
            if isinstance(data, dict):
                assistant_chats = {sid: msgs for sid, msgs in data.items() if isinstance(msgs, list)}
        except Exception:
            assistant_chats = {}

def save_assistant_chats():
    try:
        with open(ASSISTANT_CHATS_FILE, "w", encoding="utf-8") as f:
            json.dump(assistant_chats, f, indent=2)
    except Exception as e:
        print(f"Failed to save assistant chats: {e}")

load_assistant_chats()


#### TOOLING FUNCTIONALITY ####
def search_images(query:str, max_results:int=10) -> list:

    """Search for images based on a query.
  
    Args:
        query: Tag to search for
        max_results: Maximum number of results to return

    Returns:
        Array of image metadata objects
    """
    # Make sure the image DB is available (startup is lazy now)
    try:
        utils.ensure_loaded()
    except Exception:
        return []
    # Simple tag-style search over utils.all_images
    if not query:
        return []
    tokens = [t.strip().lower() for t in query.replace(",", " ").split() if t.strip()]
    matched = []
    for img in utils.all_images:
        tags = img.get("tags_set") or set()
        # Match if all tokens appear in tags or prompt text
        prompt_text = (img.get("Prompt") or "").lower()
        if all((tok in tags) or (tok in prompt_text) for tok in tokens):
            matched.append({
                "id": img["Id"],
                "prompt": img.get("Prompt", ""),
                "url": f"/image-file/{img['Id']}"
            })
            if len(matched) >= max_results:
                break
    return matched

def get_random_images(max_results:int=10) -> list:
    """Get random images from the database.
    
    Args:
        max_results: Maximum number of results to return
    
    Returns:
        Array of random image metadata objects
    """
    try:
        utils.ensure_loaded()
    except Exception:
        return []
    
    if not utils.all_images:
        return []
    
    # Randomly sample from all images
    sample_size = min(max_results, len(utils.all_images))
    sampled = random.sample(utils.all_images, sample_size)
    
    return [
        {
            "id": img["Id"],
            "prompt": img.get("Prompt", ""),
            "url": f"/image-file/{img['Id']}"
        }
        for img in sampled
    ]

def show_image(image_id:str):
    """Show image in chat.

    Args:
        image_id: ID of the image to show
    """
    try:
        utils.ensure_loaded()
        # Return minimal details + file URL for rendering on client
        img = images.get_image_details(image_id)
        # Build a direct image file URL client can display
        file_url = f"/image-file/{img['Id']}"
        return {"type": "image", "image_id": img["Id"], "url": file_url, "title": img.get("Prompt", "")}
    except Exception as e:
        return {"error": str(e)}

def generate_new_image(prompt:str):
    """Generate a new image based on a prompt.
    (Placeholder – actual generation handled on frontend via SD WebUI call.)"""
    return {"type": "generation", "status": "pending", "prompt": prompt}

def search_civitai_models(query:str, max_results:int=10) -> list:
    """Search for Civitai models based on a query.

    Args:
        query: Search query
        max_results: Maximum number of results to return
        
    Returns:
        List of model metadata objects
    """
    # fetch https://civitai.com/api/v1/models?query={query}&limit={max_results}
    response = requests.get("https://civitai.com/api/v1/models", params={"query": query, "limit": max_results, "nsfw": True})
    if response.status_code != 200:
        return []
    
    models = []

    for item in response.json().get("items", []):
        mv = None
        # choose first modelVersion that has images
        versions = item.get("modelVersions", []) or []
        if versions:
            mv = versions[0]
        cover = None
        if mv:
            imgs = mv.get("images", []) or []
            if imgs:
                cover = imgs[0].get("url")
        models.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "description": (item.get("description") or "")[:500],
            "url": f"https://civitai.com/models/{item.get('id')}",
            "cover_image_url": cover,
            "type": item.get("type"),
        })
    return models

def get_civitai_images(
    limit: int = 24,
    page: int | None = None,
    postId: int | None = None,
    modelId: int | None = None,
    modelVersionId: int | None = None,
    username: str | None = None,
    nsfw: str | bool | None = None,
    sort: str | None = None,
    period: str | None = None,
) -> dict:
    """Fetch images from CivitAI."""
    params: dict = {}

    def add_param(name: str, value):
        if value is None:
            return
        if isinstance(value, str) and not value.strip():
            return
        params[name] = value

    if limit is not None:
        try:
            limit_val = int(limit)
            limit_val = max(0, min(limit_val, 200))
        except Exception:
            limit_val = 24
        params["limit"] = limit_val

    add_param("page", page)
    add_param("postId", postId)
    add_param("modelId", modelId)
    add_param("modelVersionId", modelVersionId)
    add_param("username", username)
    add_param("nsfw", nsfw)
    add_param("sort", sort)
    add_param("period", period)

    try:
        response = requests.get("https://civitai.com/api/v1/images", params=params, timeout=20)
    except Exception:
        return {"items": [], "metadata": {}, "filters": params}

    if response.status_code != 200:
        return {"items": [], "metadata": {}, "filters": params}

    try:
        data = response.json()
    except Exception:
        return {"items": [], "metadata": {}, "filters": params}

    items = []
    for img in data.get("items", []) or []:
        meta = img.get("meta") or {}
        items.append({
            "id": img.get("id"),
            "url": img.get("url"),
            "width": img.get("width"),
            "height": img.get("height"),
            "nsfw": img.get("nsfw"),
            "nsfwLevel": img.get("nsfwLevel"),
            "createdAt": img.get("createdAt"),
            "postId": img.get("postId"),
            "modelVersionIds": img.get("modelVersionIds"),
            "username": img.get("username"),
            "prompt": meta.get("prompt", ""),
            "stats": img.get("stats") or {},
        })

    return {
        "items": items,
        "metadata": data.get("metadata") or {},
        "filters": params,
    }
def show_prompt(which:str="last_user") -> dict:
    """Return a prompt string for copying.

    Args:
        which: currently only 'last_user' supported
    Returns:
        {prompt: str}
    """
    # Find last user message across all sessions? This tool used within a convo – rely on context injection.
    # This function will be called with no arguments; we'll inspect a global temp variable updated in ws loop.
    last = _last_user_message.get("content") if _last_user_message else ""
    return {"prompt": last}

# temp storage of last user message for show_prompt tool context
_last_user_message: dict | None = None

    


        

def _safe_json(obj):
    try:
        return json.dumps(obj)
    except Exception:
        try:
            return json.dumps(str(obj))
        except Exception:
            return "{}"


@router.websocket("/assistant")
async def assistant_ws(websocket: WebSocket):
    await websocket.accept()
    session_id = None
    convo: List[dict] = [{"role": "system", "content": system_prompt}]

    async def send_json_safe(payload: dict):
        try:
            await websocket.send_json(payload)
        except RuntimeError:
            # Socket likely closed by client
            raise

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "init":
                # Initialize / load a session
                requested = data.get("session_id")
                if requested and isinstance(requested, str):
                    session_id = requested
                else:
                    session_id = uuid.uuid4().hex
                # Load existing or create new
                load_assistant_chats()
                if session_id not in assistant_chats:
                    assistant_chats[session_id] = [{"role": "system", "content": system_prompt}]
                    save_assistant_chats()
                convo = assistant_chats[session_id]
                # Send existing history (excluding system) to client
                history_payload = [
                    {"role": m.get("role"), "content": m.get("content", "")}
                    for m in convo if m.get("role") != "system"
                ]
                await send_json_safe({"type": "history", "session_id": session_id, "messages": history_payload})
                continue

            if msg_type == "reset":
                if not session_id:
                    continue
                assistant_chats[session_id] = [{"role": "system", "content": system_prompt}]
                convo = assistant_chats[session_id]
                save_assistant_chats()
                await send_json_safe({"type": "reset_ack"})
                continue

            if msg_type != "user":
                continue

            user_text = (data.get("content") or "").strip()
            if not user_text:
                continue

            if not session_id:
                # Require init first
                continue
            user_msg = {"role": "user", "content": user_text}
            convo.append(user_msg)
            assistant_chats[session_id] = convo
            save_assistant_chats()
            global _last_user_message
            _last_user_message = user_msg

            # Streaming + tool loop, similar to provided example
            while True:
                from routes.ai_settings import load_ai_settings
                _ai = load_ai_settings()
                _client = comments.laptopClient

                options = {}
                if _ai.override_temperature:
                    options["temperature"] = _ai.temperature

                stream = _client.chat(
                    model=_ai.default_assistant_model or _ai.default_model,
                    messages=convo,
                    tools=[search_images, get_random_images, show_image, generate_new_image, search_civitai_models, get_civitai_images, show_prompt],
                    stream=True,
                    options=options,
                    think=_ai.use_thinking,
                )

                thinking = ""
                content = ""
                tool_calls = []
                done_thinking = False

                for chunk in stream:
                    # Thinking stream
                    if getattr(chunk.message, "thinking", None):
                        part = chunk.message.thinking
                        thinking += part
                        await send_json_safe({"type": "thinking", "delta": part})

                    # Content stream
                    if getattr(chunk.message, "content", None):
                        if not done_thinking:
                            done_thinking = True
                        part = chunk.message.content
                        content += part
                        await send_json_safe({"type": "content", "delta": part})

                    # Tool calls
                    if getattr(chunk.message, "tool_calls", None):
                        calls = chunk.message.tool_calls
                        tool_calls.extend(calls)
                        
                    # Token usage stats are typically in the final chunk
                    if getattr(chunk, "prompt_eval_count", None):
                        input_tokens = getattr(chunk, "prompt_eval_count", 0)
                        output_tokens = getattr(chunk, "eval_count", 0)
                        eval_duration_ns = getattr(chunk, "eval_duration", 0)
                        tokens_per_sec = output_tokens / (eval_duration_ns / 1e9) if eval_duration_ns else 0
                        print(f"Usage stats: {input_tokens} input tokens | {output_tokens} output tokens | {tokens_per_sec:.2f} tokens/s")

                # Append accumulated assistant message
                if thinking or content or tool_calls:
                    convo.append({
                        "role": "assistant",
                        "thinking": thinking,
                        "content": content,
                        "tool_calls": tool_calls,
                    })
                    assistant_chats[session_id] = convo
                    save_assistant_chats()

                if not tool_calls:
                    await send_json_safe({"type": "message_end"})
                    break

                # Execute tool calls and append results
                for call in tool_calls:
                    name = getattr(call.function, "name", None)
                    args = getattr(call.function, "arguments", {}) or {}
                    result = None
                    try:
                        if name == "search_images":
                            result = search_images(**args)
                        elif name == "get_random_images":
                            result = get_random_images(**args)
                        elif name == "show_image":
                            result = show_image(**args)
                        elif name == "generate_new_image":
                            result = generate_new_image(**args)
                        elif name == "search_civitai_models":
                            result = search_civitai_models(**args)
                        elif name == "get_civitai_images":
                            result = get_civitai_images(**args)
                        elif name == "show_prompt":
                            result = show_prompt(**args) if args else show_prompt()
                        else:
                            result = {"error": f"Unknown tool: {name}"}
                    except Exception as e:
                        result = {"error": str(e)}

                    # Send tool result event to client
                    await send_json_safe({
                        "type": "tool_result",
                        "tool": name,
                        "args": args,
                        "result": result,
                    })

                    tool_context = result
                    if name == "get_civitai_images":
                        items = result.get("items", []) if isinstance(result, dict) else []
                        tool_context = {
                            "items": [
                                {
                                    "prompt": it.get("prompt", ""),
                                    "stats": it.get("stats") or {},
                                }
                                for it in items
                                if isinstance(it, dict)
                            ],
                            "metadata": result.get("metadata") or {},
                        }

                    # Append tool result to convo
                    convo.append({
                        "role": "tool",
                        "tool_name": name,
                        "content": _safe_json(tool_context),
                    })
                    assistant_chats[session_id] = convo
                    save_assistant_chats()

    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass
