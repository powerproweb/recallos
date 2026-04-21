"""
/api/search — Semantic search endpoint.

Bridges the desktop UI to recallos.retrieval_engine.search_memories().
Also exposes domain/node lists for the filter dropdowns.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from desktop.db import get_connection, init_db
from desktop.services.search_service import rank_results
from recallos.config import RecallOSConfig
from recallos.retrieval_engine import search_memories

router = APIRouter(tags=["search"])

_config = RecallOSConfig()


class SearchRequest(BaseModel):
    query: str
    domain: str | None = None
    node: str | None = None
    limit: int = 10


@router.post("/search")
def search(body: SearchRequest):
    """Semantic search with advanced ranking, dedup, and snippets."""
    raw = search_memories(
        query=body.query,
        vault_path=_config.vault_path,
        domain=body.domain,
        node=body.node,
        n_results=body.limit,
    )
    if "error" in raw:
        return raw
    # Apply ranking, dedup, and snippet extraction
    raw["results"] = rank_results(
        raw.get("results", []),
        query=body.query,
        domain_filter=body.domain,
        node_filter=body.node,
    )
    return raw


@router.get("/search/filters")
def search_filters():
    """Return available domains and nodes for the filter dropdowns."""
    import chromadb

    try:
        client = chromadb.PersistentClient(path=_config.vault_path)
        col = client.get_collection("recallos_records")
    except Exception:
        return {"domains": {}, "nodes": {}}

    domains: dict[str, int] = {}
    nodes: dict[str, int] = {}
    try:
        all_meta = col.get(include=["metadatas"])["metadatas"]
        for m in all_meta:
            d = m.get("domain", "unknown")
            n = m.get("node", "unknown")
            domains[d] = domains.get(d, 0) + 1
            nodes[n] = nodes.get(n, 0) + 1
    except Exception:
        pass

    return {"domains": domains, "nodes": nodes}


# ---------------------------------------------------------------------------
# 3.3 Saved searches
# ---------------------------------------------------------------------------


class SaveSearchRequest(BaseModel):
    query: str
    domain: str | None = None
    node: str | None = None
    name: str | None = None


@router.post("/search/saved")
def save_search(body: SaveSearchRequest):
    """Save a search query for later re-use."""
    init_db()
    conn = get_connection()
    conn.execute(
        "INSERT INTO saved_searches (query, domain, node, name) VALUES (?, ?, ?, ?)",
        (body.query, body.domain, body.node, body.name or body.query[:50]),
    )
    conn.commit()
    conn.close()
    return {"status": "saved"}


@router.get("/search/saved")
def list_saved_searches(limit: int = Query(default=20, ge=1, le=100)):
    """List saved searches."""
    init_db()
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, query, domain, node, name, created_at FROM saved_searches ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return {
        "searches": [
            {
                "id": r[0],
                "query": r[1],
                "domain": r[2],
                "node": r[3],
                "name": r[4],
                "created_at": r[5],
            }
            for r in rows
        ]
    }


@router.delete("/search/saved/{search_id}")
def delete_saved_search(search_id: int):
    """Delete a saved search."""
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM saved_searches WHERE id = ?", (search_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}
