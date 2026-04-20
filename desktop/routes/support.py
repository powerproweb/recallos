"""
/api/support/* — System info, diagnostics, and health checks.
"""

import os
import platform
import sys

from fastapi import APIRouter

from recallos.config import RecallOSConfig
from recallos.diagnostics import run_doctor

router = APIRouter(prefix="/support", tags=["support"])
_config = RecallOSConfig()


@router.get("/info")
def system_info():
    """Return system and vault information."""
    vault_path = _config.vault_path
    vault_size = 0
    try:
        for root, dirs, files in os.walk(vault_path):
            vault_size += sum(os.path.getsize(os.path.join(root, f)) for f in files)
    except Exception:
        pass

    return {
        "os": platform.platform(),
        "python": sys.version,
        "vault_path": vault_path,
        "vault_size_mb": round(vault_size / (1024 * 1024), 1),
        "recallos_version": _get_version(),
    }


@router.get("/doctor")
def run_diagnostics():
    """Run the vault health check (recallos doctor)."""
    return run_doctor(vault_path=_config.vault_path, verbose=False)


def _get_version() -> str:
    try:
        from recallos import __version__

        return __version__
    except Exception:
        return "unknown"
