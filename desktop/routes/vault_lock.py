"""
/api/vault-lock/* — Vault Lock management.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from desktop.security import audit_action
from desktop.services.vault_lock import enable, disable, get_status, verify

router = APIRouter(prefix="/vault-lock", tags=["vault-lock"])


class PassphraseRequest(BaseModel):
    passphrase: str


@router.get("/status")
def lock_status():
    """Return whether Vault Lock is enabled."""
    return get_status()


@router.post("/enable")
def enable_lock(body: PassphraseRequest):
    """Enable Vault Lock with a passphrase."""
    result = enable(body.passphrase)
    if result["status"] == "ok":
        audit_action("vault_lock_enable", "Vault Lock enabled")
    return result


@router.post("/disable")
def disable_lock(body: PassphraseRequest):
    """Disable Vault Lock (requires current passphrase)."""
    result = disable(body.passphrase)
    if result["status"] == "ok":
        audit_action("vault_lock_disable", "Vault Lock disabled")
    return result


@router.post("/verify")
def verify_passphrase(body: PassphraseRequest):
    """Verify a passphrase without changing state."""
    return {"valid": verify(body.passphrase)}
