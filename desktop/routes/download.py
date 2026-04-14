"""
/api/download — Export / download endpoint (Phase 1.4).
"""

from fastapi import APIRouter

router = APIRouter(tags=["download"])


@router.get("/download")
def download_placeholder():
    return {"status": "not_implemented", "message": "Download routes coming in Phase 1.4"}
