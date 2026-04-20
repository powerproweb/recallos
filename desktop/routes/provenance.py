"""
/api/provenance/* — Build provenance and supply-chain transparency.
"""

import importlib.metadata
import platform
import sys

from fastapi import APIRouter, Query

from desktop.security import get_audit_log

router = APIRouter(prefix="/provenance", tags=["provenance"])


@router.get("/info")
def build_info():
    """Return build provenance: version, Python, platform."""
    try:
        from recallos import __version__
    except Exception:
        __version__ = "unknown"

    return {
        "recallos_version": __version__,
        "python_version": sys.version,
        "platform": platform.platform(),
    }


@router.get("/licenses")
def third_party_licenses():
    """List installed packages and their licenses."""
    packages = []
    for dist in importlib.metadata.distributions():
        meta = dist.metadata
        packages.append(
            {
                "name": meta["Name"],
                "version": meta["Version"],
                "license": meta.get("License", meta.get("Classifier", "Unknown")),
            }
        )
    # Deduplicate and sort
    seen = set()
    unique = []
    for p in packages:
        key = p["name"]
        if key not in seen:
            seen.add(key)
            unique.append(p)
    unique.sort(key=lambda x: x["name"].lower())
    return {"packages": unique[:200]}  # cap to avoid huge responses


@router.get("/audit")
def audit_log(limit: int = Query(default=100, ge=1, le=1000)):
    """Return recent audit log entries."""
    return {"entries": get_audit_log(limit=limit)}
