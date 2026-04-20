"""
desktop/services/updater.py — Update checking and offline bundle import.

Version check hits the GitHub releases API (governed by network_policy).
Offline update bundles can be imported with SHA-256 verification.
Signature verification (cryptography lib) is documented as an upgrade path.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger("updater")

GITHUB_RELEASES_URL = "https://api.github.com/repos/powerproweb/recallos/releases/latest"


def _current_version() -> str:
    try:
        from recallos import __version__

        return __version__
    except Exception:
        return "0.0.0"


def compare_versions(current: str, latest: str) -> int:
    """Compare two semver strings.  Returns -1, 0, or 1."""

    def _parse(v: str) -> Tuple[int, ...]:
        return tuple(int(x) for x in v.strip().lstrip("v").split(".")[:3])

    try:
        c, la = _parse(current), _parse(latest)
        if c < la:
            return -1
        if c > la:
            return 1
        return 0
    except Exception:
        return 0


def check_for_update() -> dict:
    """Check GitHub releases for a newer version.

    Respects network_policy — will not make the call if updates are disabled.
    Returns dict with current, latest, and update_available.
    """
    from desktop.services.network_policy import NetworkPolicy

    policy = NetworkPolicy()
    if not policy.check("updates", "api.github.com", "/repos/powerproweb/recallos/releases/latest"):
        return {
            "current": _current_version(),
            "latest": None,
            "update_available": False,
            "blocked": True,
            "reason": "Network policy blocks update checks",
        }

    try:
        import urllib.request

        req = urllib.request.Request(GITHUB_RELEASES_URL, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        latest = data.get("tag_name", "").lstrip("v")
    except Exception as e:
        logger.warning("Update check failed: %s", e)
        return {
            "current": _current_version(),
            "latest": None,
            "update_available": False,
            "error": str(e),
        }

    current = _current_version()
    cmp = compare_versions(current, latest)

    return {
        "current": current,
        "latest": latest,
        "update_available": cmp < 0,
        "release_url": data.get("html_url", ""),
    }


def verify_bundle(path: str, expected_sha256: str) -> dict:
    """Verify an offline update bundle by SHA-256.

    Returns status dict.  Does NOT apply the update — just validates.
    Applying updates (replacing the installed package) is a separate
    step that will use pip or PyInstaller replacement logic.
    """
    p = Path(path)
    if not p.is_file():
        return {"status": "error", "message": f"File not found: {path}"}

    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    actual = h.hexdigest()

    if actual != expected_sha256:
        return {
            "status": "error",
            "message": "SHA-256 mismatch",
            "expected": expected_sha256,
            "actual": actual,
        }

    return {
        "status": "ok",
        "message": "Bundle integrity verified",
        "sha256": actual,
        "size_mb": round(p.stat().st_size / (1024 * 1024), 1),
    }
