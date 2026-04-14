"""
/api/status — Health and vault overview endpoint.

Bridges to recallos.diagnostics and recallos.ingest_engine.status
so the dashboard can show live vault state.
"""

from fastapi import APIRouter

from recallos.config import RecallOSConfig
from recallos.diagnostics import run_doctor

router = APIRouter(tags=["status"])


@router.get("/status")
def get_status():
    """Return vault health summary + basic metadata."""
    cfg = RecallOSConfig()
    vault_path = cfg.vault_path

    # run_doctor prints to stdout (legacy) — we only need the returned dict
    report = run_doctor(vault_path=vault_path, verbose=False)

    return {
        "vault_path": report["vault_path"],
        "overall": report["overall"],
        "checks": report["checks"],
        "counts": report["counts"],
    }
