"""
MCP (Model Context Protocol) server endpoints — integrated into the FastAPI app.

Exposes assistant tools over a simple JSON-RPC style HTTP API so any MCP-compatible
client can call them without needing a separate process.

Endpoint: POST /mcp
Body:  { "method": "tool_name", "params": { ...args } }
"""
from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
import json

router = APIRouter(prefix="/mcp", tags=["mcp"])

# ── Tool imports (reuse existing implementations) ──────────────────────────
from routes.assistant import (
    search_images,
    get_random_images,
    show_image,
    generate_new_image,
    search_civitai_models,
    get_civitai_images,
)


# ── Tool registry ───────────────────────────────────────────────────────────
TOOLS = {
    "search_images": {
        "fn": search_images,
        "description": "Search for images based on tags/query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Tag or keyword to search for"},
                "max_results": {"type": "integer", "description": "Max number of results (default 10)"},
            },
            "required": ["query"],
        },
    },
    "get_random_images": {
        "fn": get_random_images,
        "description": "Get random images from the database.",
        "parameters": {
            "type": "object",
            "properties": {
                "max_results": {"type": "integer", "description": "Max number of results (default 10)"},
            },
        },
    },
    "show_image": {
        "fn": show_image,
        "description": "Get details and URL for a specific image by ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "image_id": {"type": "string", "description": "ID of the image"},
            },
            "required": ["image_id"],
        },
    },
    "generate_new_image": {
        "fn": generate_new_image,
        "description": "Request a new image generation (returns pending status).",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Prompt to generate"},
            },
            "required": ["prompt"],
        },
    },
    "search_civitai_models": {
        "fn": search_civitai_models,
        "description": "Search CivitAI for AI image generation models.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max number of results (default 10)"},
            },
            "required": ["query"],
        },
    },
    "get_civitai_images": {
        "fn": get_civitai_images,
        "description": "Fetch images from CivitAI with optional filters.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer"},
                "modelId": {"type": "integer"},
                "nsfw": {"type": "string"},
                "sort": {"type": "string"},
            },
        },
    },
}


# ── MCP protocol helpers ────────────────────────────────────────────────────
def mcp_success(result, id=None):
    return {"jsonrpc": "2.0", "id": id, "result": result}


def mcp_error(code, message, id=None):
    return JSONResponse(
        status_code=400,
        content={"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}},
    )


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/tools")
def list_tools():
    """Return the list of available MCP tools and their schemas."""
    return [
        {
            "name": name,
            "description": info["description"],
            "parameters": info["parameters"],
        }
        for name, info in TOOLS.items()
    ]


@router.post("")
async def call_tool(body: dict = Body(...)):
    """
    Call an MCP tool.

    Request body:
      { "method": "tool_name", "params": { ...args }, "id": optional_id }
    """
    method = body.get("method")
    params = body.get("params") or {}
    req_id = body.get("id")

    if not method:
        return mcp_error(-32600, "Missing 'method'", id=req_id)

    if method == "tools/list":
        return mcp_success(list_tools(), id=req_id)

    tool = TOOLS.get(method)
    if not tool:
        return mcp_error(-32601, f"Unknown method: {method}", id=req_id)

    try:
        result = tool["fn"](**params)
        return mcp_success(result, id=req_id)
    except TypeError as e:
        return mcp_error(-32602, f"Invalid params: {e}", id=req_id)
    except Exception as e:
        return mcp_error(-32603, f"Internal error: {e}", id=req_id)
