"""
/api/backups/* — Backup and restore endpoints.
/api/log       — Frontend error forwarding.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from desktop.services.backup_service import backup, restore, list_backups
from desktop.services.logging_service import log_frontend_error

router = APIRouter(tags=["backups"])


@router.post("/backups/create")
def create_backup():
    """Create a new backup ZIP."""
    return backup()


@router.get("/backups")
def get_backups():
    """List available backups."""
    return {"backups": list_backups()}


class RestoreRequest(BaseModel):
    path: str


@router.post("/backups/restore")
def restore_backup(body: RestoreRequest):
    """Restore from a backup ZIP."""
    return restore(body.path)


class FrontendError(BaseModel):
    source: str
    message: str
    stack: str = ""


@router.post("/log")
def log_error(body: FrontendError):
    """Receive and log errors from the frontend error boundary."""
    log_frontend_error(body.source, body.message, body.stack)
    return {"status": "logged"}
