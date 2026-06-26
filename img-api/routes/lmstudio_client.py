import os
import base64
import time
import requests
import inspect
import json

class Message:
    def __init__(self, role, content):
        self.role = role
        self.content = content
    def __getitem__(self, item):
        return getattr(self, item)
    def get(self, item, default=None):
        return getattr(self, item, default)

class ToolCallFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments  # Must be a dict

class ToolCall:
    def __init__(self, name, arguments):
        self.function = ToolCallFunction(name, arguments)

class MessageChunk:
    def __init__(self, content="", thinking="", tool_calls=None):
        self.content = content
        self.thinking = thinking
        self.tool_calls = tool_calls or []

class ChatResponseChunk:
    def __init__(self, content="", thinking="", tool_calls=None, prompt_eval_count=0, eval_count=0, eval_duration=0):
        self.message = MessageChunk(content, thinking, tool_calls)
        self.prompt_eval_count = prompt_eval_count
        self.eval_count = eval_count
        self.eval_duration = eval_duration

class CustomChatResponse(dict):
    def __init__(self, content, role="assistant", prompt_eval_count=0, eval_count=0, eval_duration=0, tool_calls=None, **kwargs):
        message = Message(role=role, content=content)
        # Add tool_calls attribute to the message object to match Ollama's structure
        message.tool_calls = tool_calls or []
        super().__init__(message=message, **kwargs)
        self._message = message
        self._prompt_eval_count = prompt_eval_count
        self._eval_count = eval_count
        self._eval_duration = eval_duration

    @property
    def message(self):
        return self._message

    @property
    def prompt_eval_count(self):
        return self._prompt_eval_count

    @property
    def eval_count(self):
        return self._eval_count

    @property
    def eval_duration(self):
        return self._eval_duration

def function_to_openai_tool(fn):
    """Convert a Python function into an OpenAI/LM Studio compatible tool definition."""
    name = fn.__name__
    doc = fn.__doc__ or ""
    description = doc.strip().split("\n")[0] if doc else f"Call {name}"
    
    # Custom high-fidelity schemas for our specific assistant tools
    if name == "search_images":
        return {
            "type": "function",
            "function": {
                "name": "search_images",
                "description": "Search for images in the database based on tags or query tokens.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Tag or space-separated keywords to search for."},
                        "max_results": {"type": "integer", "description": "Maximum number of results to return (default 10)."}
                    },
                    "required": ["query"]
                }
            }
        }
    elif name == "get_random_images":
        return {
            "type": "function",
            "function": {
                "name": "get_random_images",
                "description": "Get random images from the database.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "max_results": {"type": "integer", "description": "Maximum number of results to return (default 10)."}
                    }
                }
            }
        }
    elif name == "show_image":
        return {
            "type": "function",
            "function": {
                "name": "show_image",
                "description": "Show a specific image in the chat by its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_id": {"type": "string", "description": "The ID of the image to show."}
                    },
                    "required": ["image_id"]
                }
            }
        }
    elif name == "generate_new_image":
        return {
            "type": "function",
            "function": {
                "name": "generate_new_image",
                "description": "Request a new image generation (returns pending status).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "Prompt to generate."}
                    },
                    "required": ["prompt"]
                }
            }
        }
    elif name == "search_civitai_models":
        return {
            "type": "function",
            "function": {
                "name": "search_civitai_models",
                "description": "Search CivitAI for AI image generation models.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query for model name or tags."},
                        "max_results": {"type": "integer", "description": "Maximum number of results to return (default 10)."}
                    },
                    "required": ["query"]
                }
            }
        }
    elif name == "get_civitai_images":
        return {
            "type": "function",
            "function": {
                "name": "get_civitai_images",
                "description": "Fetch images from CivitAI with optional filters.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Limit results (default 24)."},
                        "modelId": {"type": "integer", "description": "Filter by model ID."},
                        "nsfw": {"type": "string", "description": "Filter NSFW level ('soft', 'mature', 'x', etc.)."},
                        "sort": {"type": "string", "description": "Sort order ('Highest Rated', 'Most Liked', etc.)."}
                    }
                }
            }
        }
    elif name == "show_prompt":
        return {
            "type": "function",
            "function": {
                "name": "show_prompt",
                "description": "Return a prompt string for copying.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "which": {"type": "string", "description": "Which prompt to show (default 'last_user')."}
                    }
                }
            }
        }

    # Fallback to automatic reflection
    sig = inspect.signature(fn)
    properties = {}
    required = []
    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue
        p_type = "string"
        if param.annotation == int:
            p_type = "integer"
        elif param.annotation == float:
            p_type = "number"
        elif param.annotation == bool:
            p_type = "boolean"
        properties[param_name] = {"type": p_type}
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
            
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }

class LMStudioClient:
    def __init__(self, base_url="http://127.0.0.1:1234/v1"):
        self.base_url = base_url.rstrip("/")

    def chat(self, model, messages, format=None, options=None, keep_alive=None, think=None, **kwargs):
        start_time = time.perf_counter()

        # 1. Unload Stable Diffusion WebUI only if manage_vram is enabled
        try:
            import utils
            from routes.ai_settings import load_ai_settings
            if load_ai_settings().manage_vram:
                utils.unload_sd_models_sync()
            else:
                print("[VRAM] manage_vram=False — skipping SD model unload.")
        except Exception as e:
            print(f"[VRAM] Failed to unload SD models: {e}")

        # 2. Check if the model is loaded, if not load it explicitly and log
        try:
            root_url = self.base_url.rstrip("/")
            if root_url.endswith("/v1"):
                root_url = root_url[:-3]
            
            # Check if already loaded
            models_resp = requests.get(f"{root_url}/api/v1/models", timeout=5)
            if models_resp.status_code == 200:
                models_data = models_resp.json()
                loaded = False
                for m in models_data.get("models", []):
                    if m.get("key") == model:
                        loaded_instances = m.get("loaded_instances", [])
                        if loaded_instances:
                            loaded = True
                            break
                if not loaded:
                    print(f"[VRAM] Loading LM Studio model: {model}...")
                    load_resp = requests.post(
                        f"{root_url}/api/v1/models/load",
                        json={"model": model},
                        timeout=180
                    )
                    if load_resp.status_code == 200:
                        print(f"[VRAM] Loaded model: {model}")
                    else:
                        print(f"[VRAM] Failed to load model {model}: {load_resp.status_code}")
            else:
                print(f"[VRAM] Loading LM Studio model (JIT): {model}...")
        except Exception as e:
            print(f"[VRAM] Error checking/loading LM Studio model: {e}")

        
        # Convert messages and extract/convert images if any
        converted_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            images = msg.get("images")
            
            if not images:
                converted_messages.append({"role": role, "content": content})
                continue
                
            new_content = []
            if content:
                new_content.append({"type": "text", "text": content})
                
            for img in images:
                b64_data = None
                if isinstance(img, str):
                    if os.path.exists(img):
                        try:
                            with open(img, "rb") as f:
                                b64_data = base64.b64encode(f.read()).decode("utf-8")
                        except Exception as e:
                            print(f"[LMStudioClient] Error reading image file {img}: {e}")
                    else:
                        b64_data = img
                
                if b64_data:
                    if "," in b64_data:
                        b64_data = b64_data.split(",")[-1]
                    data_url = f"data:image/jpeg;base64,{b64_data}"
                    new_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": data_url
                        }
                    })
            
            converted_messages.append({
                "role": role,
                "content": new_content
            })

        payload = {
            "model": model,
            "messages": converted_messages,
        }

        # Apply options
        if options:
            if "temperature" in options:
                payload["temperature"] = options["temperature"]

        # Apply structured format
        if format:
            if isinstance(format, dict):
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "structured_output",
                        "schema": format
                    }
                }
            else:
                payload["response_format"] = {"type": "json_object"}

        # Convert and append tools if provided
        raw_tools = kwargs.get("tools")
        if raw_tools:
            payload["tools"] = [function_to_openai_tool(t) for t in raw_tools]

        url = f"{self.base_url}/chat/completions"

        # Check if streaming is requested
        is_streaming = kwargs.get("stream", False)
        if is_streaming:
            payload["stream"] = True
            
            def stream_generator():
                try:
                    resp = requests.post(url, json=payload, timeout=120, stream=True)
                    resp.raise_for_status()
                except Exception as e:
                    print(f"[LMStudioClient] Stream request error: {e}")
                    raise e

                # To accumulate tool calls
                # tool_calls_data: { index: { "id": "...", "name": "...", "arguments": "..." } }
                tool_calls_data = {}
                prompt_tokens = 0
                completion_tokens = 0
                
                for line in resp.iter_lines():
                    if not line:
                        continue
                    line_str = line.decode("utf-8").strip()
                    if line_str.startswith("data: "):
                        data_payload = line_str[6:]
                        if data_payload == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(data_payload)
                        except Exception:
                            continue
                        
                        # Extract usage stats if present in stream
                        if "usage" in chunk_data and chunk_data["usage"]:
                            usage = chunk_data["usage"]
                            prompt_tokens = usage.get("prompt_tokens", 0)
                            completion_tokens = usage.get("completion_tokens", 0)

                        choices = chunk_data.get("choices", [])
                        if not choices:
                            continue
                        choice = choices[0]
                        delta = choice.get("delta", {})
                        
                        # Extract thinking/reasoning (OpenAI/LM Studio compatible)
                        thinking = delta.get("reasoning_content") or delta.get("thinking") or ""
                        content = delta.get("content") or ""
                        
                        # Extract tool call deltas
                        raw_tool_calls = delta.get("tool_calls") or []
                        for tc in raw_tool_calls:
                            idx = tc.get("index", 0)
                            if idx not in tool_calls_data:
                                tool_calls_data[idx] = {"id": "", "name": "", "arguments": ""}
                            if tc.get("id"):
                                tool_calls_data[idx]["id"] = tc["id"]
                            if tc.get("function", {}).get("name"):
                                tool_calls_data[idx]["name"] = tc["function"]["name"]
                            if tc.get("function", {}).get("arguments"):
                                tool_calls_data[idx]["arguments"] += tc["function"]["arguments"]

                        if content or thinking:
                            yield ChatResponseChunk(content=content, thinking=thinking)

                # Stream ended, compile tool calls and yield final compatibility chunk
                parsed_tool_calls = []
                for idx, tc in sorted(tool_calls_data.items()):
                    tc_name = tc["name"]
                    tc_args_str = tc["arguments"]
                    tc_args = {}
                    if tc_args_str:
                        try:
                            tc_args = json.loads(tc_args_str)
                        except Exception as e:
                            print(f"[LMStudioClient] Failed to parse tool call args: {tc_args_str} - {e}")
                    parsed_tool_calls.append(ToolCall(tc_name, tc_args))
                
                duration_ns = int((time.perf_counter() - start_time) * 1e9)
                yield ChatResponseChunk(
                    tool_calls=parsed_tool_calls,
                    prompt_eval_count=prompt_tokens,
                    eval_count=completion_tokens,
                    eval_duration=duration_ns
                )

            return stream_generator()

        # Non-streaming implementation (original logic with tools parsing support added)
        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[LMStudioClient] Error during request to {url}: {e}")
            raise e

        choices = data.get("choices", [])
        if not choices:
            raise ValueError("No choices returned from LM Studio")
            
        choice = choices[0]
        content = choice.get("message", {}).get("content", "")
        role = choice.get("message", {}).get("role", "assistant")
        
        # Parse non-streaming tool calls if any
        raw_tool_calls = choice.get("message", {}).get("tool_calls") or []
        parsed_tool_calls = []
        for tc in raw_tool_calls:
            tc_fn = tc.get("function", {})
            tc_name = tc_fn.get("name")
            tc_args_str = tc_fn.get("arguments") or "{}"
            tc_args = {}
            if isinstance(tc_args_str, dict):
                tc_args = tc_args_str
            elif isinstance(tc_args_str, str):
                try:
                    tc_args = json.loads(tc_args_str)
                except Exception:
                    pass
            parsed_tool_calls.append(ToolCall(tc_name, tc_args))

        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        duration_ns = int((time.perf_counter() - start_time) * 1e9)

        return CustomChatResponse(
            content=content,
            role=role,
            prompt_eval_count=prompt_tokens,
            eval_count=completion_tokens,
            eval_duration=duration_ns,
            tool_calls=parsed_tool_calls
        )

    def embeddings(self, model, prompt):
        url = f"{self.base_url}/embeddings"
        payload = {
            "model": model,
            "input": prompt
        }
        try:
            resp = requests.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            embedding = data["data"][0]["embedding"]
            return {"embedding": embedding}
        except Exception as e:
            print(f"[LMStudioClient] Error during embeddings request to {url}: {e}")
            raise e
