"""
/api/search — Semantic search endpoint.

Bridges the desktop UI to recallos.retrieval_engine.search_memories().
Also exposes domain/node lists for the filter dropdowns.
"""

from fastapi import APIRouter
from pydantic import BaseModel

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
    """Semantic search across the Data Vault."""
    return search_memories(
        query=body.query,
        vault_path=_config.vault_path,
        domain=body.domain,
        node=body.node,
        n_results=body.limit,
    )


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
