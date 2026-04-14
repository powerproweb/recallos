"""
/api/models/* — Embedding model management and offline status.

  GET   /api/models           — model info (name, installed, hash, size)
  POST  /api/models/download  — explicitly download the embedding model
  GET   /api/models/offline   — offline-readiness check
"""

from fastapi import APIRouter

from desktop.services.model_manager import ModelManager

router = APIRouter(prefix="/models", tags=["models"])


@router.get("")
def get_model_info():
    """Return embedding model metadata."""
    return ModelManager().get_info()


@router.post("/download")
def download_model():
    """Explicitly download the embedding model (user-initiated)."""
    return ModelManager().download()


@router.get("/offline")
def get_offline_status():
    """Report whether RecallOS can run fully offline."""
    return ModelManager().offline_status()
