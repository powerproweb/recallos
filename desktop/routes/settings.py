"""
/api/settings — App settings endpoint (Phase 1.11).
"""

from fastapi import APIRouter

router = APIRouter(tags=["settings"])


@router.get("/settings")
def settings_placeholder():
    return {"status": "not_implemented", "message": "Settings routes coming in Phase 1.11"}
