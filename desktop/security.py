"""
desktop/security.py — Security primitives for RecallOS Desktop.

Filesystem sandbox:
  - validate_path() ensures all file operations stay within approved roots
  - Prevents path traversal attacks and arbitrary filesystem access

Audit logging:
  - audit_action() records privileged operations to the audit_log table
  - Used by export, restore, settings changes, credential operations
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

from desktop.db import get_connection, init_db

logger = logging.getLogger("security")

# ---------------------------------------------------------------------------
# Approved filesystem roots — all file operations must stay within these
# ---------------------------------------------------------------------------

_RECALLOS_HOME = Path(os.path.expanduser("~/.recallos")).resolve()

APPROVED_ROOTS: list[Path] = [
    _RECALLOS_HOME,  # vault, config, desktop.db, logs, backups, staging
]


def add_approved_root(path: str | Path) -> None:
    """Add an additional approved root (e.g. a user-configured vault path)."""
    resolved = Path(path).resolve()
    if resolved not in APPROVED_ROOTS:
        APPROVED_ROOTS.append(resolved)


# ---------------------------------------------------------------------------
# Path validation
# ---------------------------------------------------------------------------


class PathNotAllowedError(Exception):
    """Raised when a file path is outside all approved roots."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Path not allowed: {path}")


def validate_path(path: str | Path) -> Path:
    """Resolve *path* and verify it falls under an approved root.

    Returns the resolved Path if valid.
    Raises PathNotAllowedError if the path escapes the sandbox.
    """
    resolved = Path(path).resolve()

    for root in APPROVED_ROOTS:
        try:
            resolved.relative_to(root)
            return resolved
        except ValueError:
            continue

    logger.warning("Blocked path outside sandbox: %s", resolved)
    raise PathNotAllowedError(str(resolved))


def is_path_allowed(path: str | Path) -> bool:
    """Check without raising."""
    try:
        validate_path(path)
        return True
    except PathNotAllowedError:
        return False


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------


def audit_action(action: str, detail: str = "") -> None:
    """Record a privileged action in the audit log.

    Actions: export, restore, backup, settings_change, credential_change,
    upload, path_change, etc.
    """
    init_db()
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_log (action, detail, created_at) VALUES (?, ?, ?)",
        (action, detail, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    logger.info("AUDIT: %s — %s", action, detail)


def get_audit_log(limit: int = 100) -> list[dict]:
    """Return recent audit log entries."""
    init_db()
    conn = get_connection()
    rows = conn.execute(
        "SELECT action, detail, created_at FROM audit_log ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [{"action": r[0], "detail": r[1], "timestamp": r[2]} for r in rows]
