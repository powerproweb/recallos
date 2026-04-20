"""
/api/updater/* — Update checking and offline bundle verification.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from desktop.services.updater import check_for_update, verify_bundle

router = APIRouter(prefix="/updater", tags=["updater"])


@router.get("/check")
def check_update():
    """Check GitHub for a newer version (governed by network policy)."""
    return check_for_update()


class BundleVerifyRequest(BaseModel):
    path: str
    expected_sha256: str


@router.post("/verify-bundle")
def verify_update_bundle(body: BundleVerifyRequest):
    """Verify an offline update bundle by SHA-256."""
    return verify_bundle(body.path, body.expected_sha256)
