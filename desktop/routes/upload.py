"""
/api/upload — File upload / ingest endpoint (Phase 1.3).
"""

from fastapi import APIRouter

router = APIRouter(tags=["upload"])


@router.post("/upload")
def upload_placeholder():
    return {"status": "not_implemented", "message": "Upload routes coming in Phase 1.3"}
