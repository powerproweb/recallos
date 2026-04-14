"""
/api/search — Hybrid search endpoint (Phase 1.5).
"""

from fastapi import APIRouter

router = APIRouter(tags=["search"])


@router.get("/search")
def search_placeholder():
    return {"status": "not_implemented", "message": "Search routes coming in Phase 1.5"}
