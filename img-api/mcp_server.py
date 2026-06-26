import sys
import os
import json

# Add current directory to sys.path so we can import modules correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
import utils
from routes.assistant import (
    search_images,
    get_random_images,
    show_image,
    generate_new_image,
    search_civitai_models,
    get_civitai_images,
)

# Create FastMCP server
mcp = FastMCP("Slop Central MCP Server")

@mcp.tool()
def tool_search_images(query: str, max_results: int = 10) -> str:
    """Search for images in the database based on tags or query tokens.
    
    Args:
        query: Tag or space-separated keywords to search for.
        max_results: Maximum number of results to return (default 10).
    """
    res = search_images(query, max_results)
    return json.dumps(res)

@mcp.tool()
def tool_get_random_images(max_results: int = 10) -> str:
    """Get random images from the database.
    
    Args:
        max_results: Maximum number of results to return (default 10).
    """
    res = get_random_images(max_results)
    return json.dumps(res)

@mcp.tool()
def tool_show_image(image_id: str) -> str:
    """Show detailed information for a specific image by ID.
    
    Args:
        image_id: The ID of the image to show.
    """
    res = show_image(image_id)
    return json.dumps(res)

@mcp.tool()
def tool_generate_new_image(prompt: str) -> str:
    """Request a new image generation (returns pending status).
    
    Args:
        prompt: Prompt to generate.
    """
    res = generate_new_image(prompt)
    return json.dumps(res)

@mcp.tool()
def tool_search_civitai_models(query: str, max_results: int = 10) -> str:
    """Search CivitAI for AI image generation models.
    
    Args:
        query: Search query for the model name or tags.
        max_results: Maximum number of results to return (default 10).
    """
    res = search_civitai_models(query, max_results)
    return json.dumps(res)

@mcp.tool()
def tool_get_civitai_images(
    limit: int = 24,
    modelId: int = None,
    nsfw: str = None,
    sort: str = None,
) -> str:
    """Fetch images from CivitAI with optional filters.
    
    Args:
        limit: Max number of images to return (default 24).
        modelId: Filter by model ID.
        nsfw: Filter NSFW level ('soft', 'mature', 'x', etc.).
        sort: Sort order ('Highest Rated', 'Most Liked', etc.).
    """
    # Convert modelId to int if it's passed as a string or float
    if modelId is not None:
        try:
            modelId = int(modelId)
        except Exception:
            pass
    res = get_civitai_images(limit=limit, modelId=modelId, nsfw=nsfw, sort=sort)
    return json.dumps(res)

if __name__ == "__main__":
    mcp.run()
