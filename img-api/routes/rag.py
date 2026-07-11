"""
RAG (Retrieval-Augmented Generation) system for Airi assistant.

Indexes image prompts, comments, and tags into an in-memory vector store
using LM Studio embeddings. Provides similarity search to inject relevant
context into the AI's system prompt before responding.
"""
import os
import json
import time
import threading
import numpy as np
from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()

# ── Configuration ─────────────────────────────────────────────────────────────
LM_STUDIO_BASE = "http://127.0.0.1:1234"
EMBEDDING_MODEL = "nomic-embed-text"   # Default; configurable via env var
EMBEDDING_MODEL = os.environ.get("RAG_EMBED_MODEL", EMBEDDING_MODEL)

RAG_INDEX_FILE = "storage/rag_index.npz"   # Persisted embeddings cache

# ── In-memory store ────────────────────────────────────────────────────────────
_lock = threading.Lock()

# Each entry: { "id": str, "text": str, "meta": dict }
_documents: list[dict] = []
_embeddings: Optional[np.ndarray] = None   # shape (N, D)
_indexed = False
_indexing = False


# ── Embedding helper ───────────────────────────────────────────────────────────
def _embed_texts(texts: list[str]) -> Optional[np.ndarray]:
    """Call LM Studio /v1/embeddings and return a (N, D) numpy array."""
    import requests

    if not texts:
        return None

    try:
        resp = requests.post(
            f"{LM_STUDIO_BASE}/v1/embeddings",
            json={"model": EMBEDDING_MODEL, "input": texts},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        vecs = [item["embedding"] for item in data.get("data", [])]
        if not vecs:
            return None
        arr = np.array(vecs, dtype=np.float32)
        # L2-normalise for cosine similarity via dot product
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        return arr / norms
    except Exception as e:
        print(f"[RAG] Embedding error: {e}")
        return None


def _cosine_search(query_vec: np.ndarray, top_k: int = 5) -> list[dict]:
    """Return top-k documents by cosine similarity."""
    global _embeddings, _documents
    if _embeddings is None or len(_documents) == 0:
        return []

    scores = _embeddings @ query_vec.reshape(-1)    # (N,)
    indices = np.argsort(scores)[::-1][:top_k]
    results = []
    for idx in indices:
        doc = _documents[int(idx)].copy()
        doc["score"] = float(scores[idx])
        results.append(doc)
    return results


# ── Index building ─────────────────────────────────────────────────────────────
def _build_index_from_images():
    """Index all image prompts + comments into the vector store."""
    global _documents, _embeddings, _indexed, _indexing

    with _lock:
        if _indexed or _indexing:
            return
        _indexing = True

    try:
        import utils
        try:
            utils.ensure_loaded()
        except Exception:
            pass

        docs = []
        for img in utils.all_images:
            prompt = img.get("Prompt", "").strip()
            img_id = img.get("Id", "")
            tags = img.get("tags", []) or []
            if prompt:
                docs.append({
                    "id": img_id,
                    "text": prompt[:512],
                    "meta": {
                        "type": "prompt",
                        "image_id": img_id,
                        "url": f"/image-file/{img_id}",
                        "tags": tags[:10],
                    },
                })

        # Also load comments
        comments_file = "comments.json"
        if os.path.exists(comments_file):
            try:
                with open(comments_file, "r", encoding="utf-8") as f:
                    raw_comments = json.load(f)
                for img_id, cdata in raw_comments.items():
                    if isinstance(cdata, dict):
                        desc = cdata.get("description", "").strip()
                        if desc:
                            docs.append({
                                "id": f"comment_{img_id}",
                                "text": desc[:512],
                                "meta": {
                                    "type": "description",
                                    "image_id": img_id,
                                    "url": f"/image-file/{img_id}",
                                },
                            })
            except Exception as e:
                print(f"[RAG] Failed to load comments for indexing: {e}")

        if not docs:
            print("[RAG] No documents to index.")
            with _lock:
                _indexed = True
                _indexing = False
            return

        print(f"[RAG] Building embeddings for {len(docs)} documents…")

        # Batch embed (256 at a time to avoid huge payloads)
        batch_size = 256
        all_vecs = []
        for i in range(0, len(docs), batch_size):
            batch = docs[i : i + batch_size]
            texts = [d["text"] for d in batch]
            vecs = _embed_texts(texts)
            if vecs is not None:
                all_vecs.append(vecs)
            else:
                print(f"[RAG] Batch {i}–{i+len(batch)} embedding failed; skipping.")

        if all_vecs:
            arr = np.concatenate(all_vecs, axis=0)
            # Trim docs to match successfully embedded count
            docs = docs[: arr.shape[0]]
            with _lock:
                _documents = docs
                _embeddings = arr
            print(f"[RAG] Indexed {arr.shape[0]} documents. Embedding dim={arr.shape[1]}")
        else:
            print("[RAG] No embeddings produced.")

    except Exception as e:
        print(f"[RAG] Index build failed: {e}")
    finally:
        with _lock:
            _indexed = True
            _indexing = False


def start_background_indexing():
    """Launch index build in a background thread (non-blocking)."""
    t = threading.Thread(target=_build_index_from_images, daemon=True, name="rag-indexer")
    t.start()


# ── Public retrieval function (used by assistant.py) ─────────────────────────
def rag_retrieve(query: str, top_k: int = 5) -> list[dict]:
    """
    Retrieve top_k relevant documents for a query.
    Returns list of { id, text, score, meta } dicts.
    """
    if not query.strip():
        return []
    
    with _lock:
        if not _indexed:
            return []
        if _embeddings is None:
            return []

    q_vec = _embed_texts([query])
    if q_vec is None:
        return []

    with _lock:
        results = _cosine_search(q_vec[0], top_k=top_k)

    return results


def rag_retrieve_no_embed(query: str, top_k: int = 5) -> list[dict]:
    """
    Keyword fallback retrieval when embeddings are unavailable.
    Token-overlap scoring, no external calls needed.
    """
    global _documents
    if not _documents:
        return []

    tokens = set(query.lower().split())
    scored = []
    for doc in _documents:
        doc_tokens = set(doc["text"].lower().split())
        overlap = len(tokens & doc_tokens)
        if overlap > 0:
            scored.append((overlap, doc))
    scored.sort(key=lambda x: -x[0])
    return [d for _, d in scored[:top_k]]


# ── REST endpoints ─────────────────────────────────────────────────────────────
class RAGStatusResponse(BaseModel):
    indexed: bool
    indexing: bool
    document_count: int
    embedding_model: str


@router.get("/rag/status", response_model=RAGStatusResponse)
def rag_status():
    with _lock:
        return RAGStatusResponse(
            indexed=_indexed,
            indexing=_indexing,
            document_count=len(_documents),
            embedding_model=EMBEDDING_MODEL,
        )


@router.post("/rag/reindex")
def rag_reindex():
    """Trigger a full re-index of all images + comments."""
    global _indexed, _indexing, _documents, _embeddings
    with _lock:
        _indexed = False
        _indexing = False
        _documents = []
        _embeddings = None
    start_background_indexing()
    return {"status": "reindexing started"}


class RAGSearchRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("/rag/search")
def rag_search(body: RAGSearchRequest):
    """Search the RAG index for relevant documents."""
    with _lock:
        ready = _indexed and _embeddings is not None

    if ready:
        results = rag_retrieve(body.query, body.top_k)
    else:
        results = rag_retrieve_no_embed(body.query, body.top_k)

    return {
        "query": body.query,
        "results": results,
        "mode": "embedding" if ready else "keyword",
    }
