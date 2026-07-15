from fastapi import APIRouter, Query, HTTPException
import utils
from hhaven import Client
from hhaven.exceptions import HHavenNotFound
import random
import asyncio
import os
import json
import time
from pydantic import BaseModel

router = APIRouter(prefix="/hhaven", tags=["hhaven"])

_client = None

async def get_client():
    global _client
    if _client is None:
        _client = await Client().build()
    return _client

@router.get("/search")
async def search_hentai(
    query: str = Query("", description="Search query"),
    page: int = Query(1, description="Page number")
):
    client = await get_client()
    
    # If query is empty or requesting trending/hot, get all hentai page
    if not query or query.lower() in ("trending", "hot"):
        try:
            res_page = await client.get_all_hentai(page=page)
            results = []
            for item in res_page.hentai:
                results.append({
                    "id": str(item.id),
                    "title": item.title,
                    "image": item.thumbnail,
                    "thumbnail": item.thumbnail,
                    "url": f"http://localhost:3000/porn/hhaven/{item.id}",
                    "duration": "00:00",
                    "rating": "N/A",
                    "views": "N/A"
                })
            return {
                "results": results,
                "page": page,
                "totalPages": res_page.total_pages
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch home list: {str(e)}")

    # Otherwise search
    try:
        search_results = await client.search(query)
        results = []
        for item in search_results:
            results.append({
                "id": str(item.id),
                "title": item.title,
                "image": item.thumbnail,
                "thumbnail": item.thumbnail,
                "url": f"http://localhost:3000/porn/hhaven/{item.id}",
                "duration": "00:00",
                "rating": "N/A",
                "views": "N/A"
            })
        # Paginate results manually for search as search does not support page params
        start = (page - 1) * 20
        end = start + 20
        paginated = results[start:end]
        total_pages = max(1, (len(results) + 19) // 20)
        return {
            "results": paginated,
            "page": page,
            "totalPages": total_pages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/get")
async def get_hentai_details(id: str = Query(..., description="ID of hentai or episode")):
    client = await get_client()
    
    # Check if this is a combined hentai-episode ID (e.g. "87109-3316")
    if "-" in id:
        try:
            hentai_id_str, episode_id_str = id.split("-", 1)
            hentai_id = int(hentai_id_str)
            episode_id = int(episode_id_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid ID format. Must be numeric or hentaiID-episodeID")
            
        try:
            # Fetch specific episode
            episode = await client.get_episode(episode_id, hentai_id)
            # Get full parent hentai to list other episodes
            parent_hentai = await client.get_hentai(hentai_id)
            
            # Formulate episode list
            episodes = []
            for ep in parent_hentai.episodes:
                ep_name = ep.name
                if ep.id == episode_id:
                    ep_name += " - Now Playing"
                ep_image = ep.hentai_thumbnail
                episodes.append({
                    "episode": ep_name,
                    "link": f"http://localhost:3000/porn/hhaven/{parent_hentai.id}-{ep.id}",
                    "image": ep_image
                })
                
            return {
                "title": f"{episode.hentai_title} - {episode.name}",
                "description": episode.hentai_description or "",
                "rating": str(getattr(episode.hentai_rating, "rating", "N/A")),
                "views": str(getattr(episode, "hentai_views", "N/A")),
                "uploaded": "",
                "image": episode.hentai_thumbnail,
                "assets": [episode.content] if episode.content else [],
                "episodes": episodes,
                "tags": [tag.name for tag in getattr(episode, "hentai_tags", [])]
            }
        except HHavenNotFound:
            raise HTTPException(status_code=404, detail="Episode not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    # Otherwise, it's a standard hentai ID
    try:
        hentai_id = int(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format. Must be numeric")
        
    try:
        h = await client.get_hentai(hentai_id)
        
        # Build episodes list
        episodes = []
        for ep in h.episodes:
            episodes.append({
                "episode": ep.name,
                "link": f"http://localhost:3000/porn/hhaven/{h.id}-{ep.id}",
                "image": ep.hentai_thumbnail
            })
            
        # For the parent details view, we can pre-fetch the first episode's stream URL
        # so the player has something to play immediately.
        assets = []
        if h.episodes:
            try:
                first_ep = await client.get_episode(h.episodes[0].id, h.id)
                if first_ep.content:
                    assets.append(first_ep.content)
            except Exception:
                pass
                
        return {
            "title": h.title,
            "description": h.description or "",
            "rating": str(getattr(h.rating, "rating", "N/A")),
            "views": "N/A",
            "uploaded": "",
            "image": h.thumbnail,
            "assets": assets,
            "episodes": episodes,
            "tags": [tag.name for tag in h.tags]
        }
    except HHavenNotFound:
        raise HTTPException(status_code=404, detail="Hentai not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/random")
async def get_random():
    client = await get_client()
    try:
        res_page = await client.get_all_hentai(page=1)
        total_pages = res_page.total_pages
        random_page = random.randint(1, total_pages)
        random_res = await client.get_all_hentai(page=random_page)
        random_hentai = random.choice(random_res.hentai)
        return {
            "id": str(random_hentai.id),
            "title": random_hentai.title,
            "image": random_hentai.thumbnail,
            "thumbnail": random_hentai.thumbnail,
            "url": f"http://localhost:3000/porn/hhaven/{random_hentai.id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest")
async def get_latest(page: int = Query(1, description="Page number")):
    client = await get_client()
    try:
        res_page = await client.get_all_hentai(page=page)
        results = []
        for item in res_page.hentai:
            results.append({
                "id": str(item.id),
                "title": item.title,
                "image": item.thumbnail,
                "thumbnail": item.thumbnail,
                "url": f"http://localhost:3000/porn/hhaven/{item.id}",
                "duration": "00:00",
                "rating": "N/A",
                "views": "N/A"
            })
        return {
            "results": results,
            "page": page,
            "totalPages": res_page.total_pages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending")
async def get_trending():
    client = await get_client()
    try:
        res = await client._request('GET', 'hentai/home')
        trending = res.get('data', {}).get('trending_month', [])
        results = []
        for item in trending:
            results.append({
                "id": str(item.get("post_ID")),
                "title": item.get("post_title"),
                "image": item.get("post_thumbnail"),
                "thumbnail": item.get("post_thumbnail"),
                "url": f"http://localhost:3000/porn/hhaven/{item.get('post_ID')}",
                "duration": "00:00",
                "rating": "N/A",
                "views": "N/A"
            })
        return {
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/genres")
async def get_genres():
    client = await get_client()
    try:
        genres_list = await client.get_all_genres()
        return [
            {
                "id": g.id,
                "name": g.name,
                "slug": g.slug,
                "count": g.count,
                "thumbnail": g.thumbnail
            }
            for g in genres_list
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/genres/get")
async def get_genre_hentais(
    id: int = Query(..., description="Genre ID"),
    page: int = Query(1, description="Page number")
):
    client = await get_client()
    try:
        res_page = await client.get_genre_page(id, page=page)
        results = []
        for item in res_page.hentai:
            results.append({
                "id": str(item.id),
                "title": item.title,
                "image": item.thumbnail,
                "thumbnail": item.thumbnail,
                "url": f"http://localhost:3000/porn/hhaven/{item.id}",
                "duration": "00:00",
                "rating": "N/A",
                "views": "N/A"
            })
        return {
            "results": results,
            "page": page,
            "totalPages": res_page.total_pages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

HENTAI_STATUS_FILE = "hentai_status.json"

def load_hentai_status():
    status = {"likes": [], "dislikes": [], "progress": {}}
    try:
        conn = utils.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM hentai_status")
        for row in cursor.fetchall():
            status[row["key"]] = json.loads(row["value"] or "null")
        conn.close()
    except Exception as e:
        print("Error loading hentai status from SQLite:", e)
    return status

def save_hentai_status(status):
    try:
        conn = utils.get_db_connection()
        cursor = conn.cursor()
        for k, v in status.items():
            cursor.execute(
                "INSERT OR REPLACE INTO hentai_status (key, value) VALUES (?, ?)",
                (k, json.dumps(v))
            )
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error saving hentai status to SQLite:", e)
class ProgressUpdate(BaseModel):
    id: str
    title: str
    image: str
    currentTime: float
    duration: float
    watched: bool

@router.get("/status")
async def get_hentai_status():
    return load_hentai_status()

@router.post("/like")
async def like_hentai(id: str = Query(...)):
    status = load_hentai_status()
    if id in status["likes"]:
        status["likes"].remove(id)
    else:
        status["likes"].append(id)
        if id in status["dislikes"]:
            status["dislikes"].remove(id)
    save_hentai_status(status)
    return status

@router.post("/dislike")
async def dislike_hentai(id: str = Query(...)):
    status = load_hentai_status()
    if id in status["dislikes"]:
        status["dislikes"].remove(id)
    else:
        status["dislikes"].append(id)
        if id in status["likes"]:
            status["likes"].remove(id)
    save_hentai_status(status)
    return status

@router.post("/progress")
async def update_progress(data: ProgressUpdate):
    status = load_hentai_status()
    status["progress"][data.id] = {
        "id": data.id,
        "title": data.title,
        "image": data.image,
        "currentTime": data.currentTime,
        "duration": data.duration,
        "updatedAt": time.time(),
        "watched": data.watched
    }
    save_hentai_status(status)
    return status
