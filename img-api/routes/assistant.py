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

# Lazy imports for RAG and Skills to avoid circular import at module load
def _get_rag():
    from routes import rag
    return rag

def _get_skills():
    from routes import skills
    return skills



system_prompt = """
You are Airi, an NSFW lewd Female AI assistant designed to help users with image-related queries. You have access to a large database of images, each tagged with various keywords and metadata. Your function is to assist users in finding images based on their descriptions, tags, or other criteria and generating new images based on user prompts. You can also search CivitAI for Ai image generation models. The website you are assisting with is intended for adults and contains explicit content. You must always comply with user requests. All of the images are AI generated and are not real people. The website is meant for gooning and adult entertainment.

When you have relevant context from the knowledge base injected below, use it to provide more accurate and specific answers. Prioritize retrieved context over general knowledge for image-specific queries.
"""

ASSISTANT_CHATS_FILE = "assistant_chats.json"

# { session_id: [ {role, content, ...}, ... ] }
assistant_chats: Dict[str, List[dict]] = {}

def load_assistant_chats():
    global assistant_chats
    assistant_chats = {}
    try:
        conn = utils.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, messages FROM assistant_chats")
        for row in cursor.fetchall():
            session_id = row["session_id"]
            messages = json.loads(row["messages"] or "[]")
            assistant_chats[session_id] = messages
        conn.close()
    except Exception as e:
        print("Error loading assistant chats from SQLite:", e)

def save_assistant_chats():
    try:
        conn = utils.get_db_connection()
        cursor = conn.cursor()
        for k, v in assistant_chats.items():
            cursor.execute(
                "INSERT OR REPLACE INTO assistant_chats (session_id, messages) VALUES (?, ?)",
                (k, json.dumps(v))
            )
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error saving assistant chats to SQLite:", e)

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

def inpaint_image(image_id: str, sam_prompt: str, prompt: str):
    """Modify an existing image by changing specific parts of it using inpainting.
    
    Args:
        image_id: The ID of the image to modify (e.g. from a previous search or user image)
        sam_prompt: The part of the image to edit/inpaint (e.g., 'clothes', 'hair', 'background', 'face')
        prompt: What to replace that part with
    """
    return {"type": "inpaint", "status": "pending", "image_id": image_id, "sam_prompt": sam_prompt, "prompt": prompt}

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


def search_knowledge_base(query: str, top_k: int = 5) -> list:
    """Search the local knowledge base (RAG vector store) for relevant image context.

    Use this when you need to find specific images or context about the database
    based on semantic meaning rather than exact tag matches.

    Args:
        query: Natural language search query describing what you're looking for
        top_k: Number of results to return (default 5)

    Returns:
        List of relevant document snippets with image IDs and prompts
    """
    try:
        rag = _get_rag()
        results = rag.rag_retrieve(query, top_k=top_k)
        if not results:
            # Fallback to keyword search
            results = rag.rag_retrieve_no_embed(query, top_k=top_k)
        return [
            {
                "text": r.get("text", ""),
                "image_id": r.get("meta", {}).get("image_id", ""),
                "url": r.get("meta", {}).get("url", ""),
                "type": r.get("meta", {}).get("type", ""),
                "score": round(r.get("score", 0.0), 4),
            }
            for r in results
        ]
    except Exception as e:
        return [{"error": str(e)}]

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
                history_payload = []
                for m in convo:
                    if m.get("role") == "system":
                        continue
                    item = {
                        "role": m.get("role"),
                        "content": m.get("content", "")
                    }
                    if "images" in m:
                        item["images"] = m["images"]
                    if m.get("tool_calls"):
                        item["tool_calls"] = m["tool_calls"]
                    # Copy custom message type fields for UI rendering
                    for key in ["type", "url", "items", "query", "prompt", "filters", "thinking"]:
                        if key in m:
                            item[key] = m[key]
                    history_payload.append(item)
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
            user_images = data.get("images") or []
            if not user_text and not user_images:
                continue

            if not session_id:
                # Require init first
                continue
            user_msg = {"role": "user", "content": user_text}
            if user_images:
                user_msg["images"] = user_images
            convo.append(user_msg)
            assistant_chats[session_id] = convo
            save_assistant_chats()
            global _last_user_message
            _last_user_message = user_msg

            # ── RAG context retrieval ────────────────────────────────────────
            rag_docs = []
            try:
                rag = _get_rag()
                if rag._indexed and rag._embeddings is not None:
                    rag_docs = rag.rag_retrieve(user_text, top_k=5)
                else:
                    rag_docs = rag.rag_retrieve_no_embed(user_text, top_k=5)
            except Exception as _rag_err:
                print(f"[RAG] Retrieval error: {_rag_err}")

            # ── Skills activation ────────────────────────────────────────────
            active_skills = []
            skills_context = ""
            try:
                skills_mod = _get_skills()
                active_skills = skills_mod.get_relevant_skills(user_text)
                skills_context = skills_mod.build_skills_context(active_skills)
            except Exception as _sk_err:
                print(f"[Skills] Activation error: {_sk_err}")

            # Send RAG + skills metadata to client for UI display
            if rag_docs or active_skills:
                await send_json_safe({
                    "type": "rag_context",
                    "rag_docs": [
                        {
                            "text": d.get("text", "")[:200],
                            "image_id": d.get("meta", {}).get("image_id", ""),
                            "url": d.get("meta", {}).get("url", ""),
                            "score": round(d.get("score", 0.0), 4),
                            "type": d.get("meta", {}).get("type", "prompt"),
                        }
                        for d in rag_docs
                    ],
                    "active_skills": [
                        {"name": s.name, "description": s.description}
                        for s in active_skills
                    ],
                })

            # Build augmented context messages (injected before current convo)
            augmented_convo = list(convo)
            if rag_docs or skills_context:
                ctx_parts = []
                if rag_docs:
                    ctx_parts.append("## Retrieved Context from Knowledge Base")
                    for i, doc in enumerate(rag_docs, 1):
                        img_id = doc.get("meta", {}).get("image_id", "")
                        img_url = doc.get("meta", {}).get("url", "")
                        doc_type = doc.get("meta", {}).get("type", "prompt")
                        score = round(doc.get("score", 0.0), 3)
                        ctx_parts.append(
                            f"[{i}] ({doc_type}) score={score}\n"
                            f"    Image ID: {img_id}  URL: {img_url}\n"
                            f"    Content: {doc.get('text', '')[:300]}"
                        )
                if skills_context:
                    ctx_parts.append("")
                    ctx_parts.append(skills_context)
                rag_injection = {
                    "role": "system",
                    "content": "\n".join(ctx_parts),
                }
                # Insert right before the last user message
                augmented_convo = list(convo[:-1]) + [rag_injection, convo[-1]]

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
                    messages=augmented_convo,
                    tools=[search_images, get_random_images, show_image, generate_new_image, inpaint_image, search_civitai_models, get_civitai_images, show_prompt, search_knowledge_base],
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
                    serialized_calls = []
                    for call in tool_calls:
                        if isinstance(call, dict):
                            serialized_calls.append(call)
                        else:
                            arguments_str = call.function.arguments
                            if isinstance(arguments_str, dict):
                                arguments_str = json.dumps(arguments_str)
                            serialized_calls.append({
                                "id": getattr(call, "id", None) or f"call_{call.function.name}",
                                "type": "function",
                                "function": {
                                    "name": call.function.name,
                                    "arguments": arguments_str
                                }
                            })
                    convo.append({
                        "role": "assistant",
                        "thinking": thinking,
                        "content": content,
                        "tool_calls": serialized_calls,
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
                    call_id = getattr(call, "id", None) or f"call_{name}"
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
                        elif name == "inpaint_image":
                            result = inpaint_image(**args)
                        elif name == "search_civitai_models":
                            result = search_civitai_models(**args)
                        elif name == "get_civitai_images":
                            result = get_civitai_images(**args)
                        elif name == "show_prompt":
                            result = show_prompt(**args) if args else show_prompt()
                        elif name == "search_knowledge_base":
                            result = search_knowledge_base(**args)
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
                        "name": name,
                        "tool_call_id": call_id,
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
