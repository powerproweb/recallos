"""
desktop/crash.py — Crash reporting and unclean-shutdown detection.

- ``write_crash_dump(exc)`` saves a JSON crash report to ~/.recallos/logs/
- ``mark_running()`` / ``clear_running()`` manage a lock file to detect
  unclean shutdowns on next launch
- ``check_unclean_shutdown()`` returns True if the app didn't exit cleanly
"""

from __future__ import annotations

import json
import logging
import os
import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(os.path.expanduser("~/.recallos/logs"))
LOCK_FILE = LOG_DIR / ".running"

logger = logging.getLogger("crash")


def write_crash_dump(exc: BaseException) -> Path | None:
    """Write a crash report JSON file.  Returns the path, or None on failure."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = LOG_DIR / f"crash_{ts}.json"
    try:
        dump = {
            "timestamp": datetime.now().isoformat(),
            "exception_type": type(exc).__qualname__,
            "message": str(exc),
            "traceback": traceback.format_exception(type(exc), exc, exc.__traceback__),
            "python": sys.version,
            "platform": platform.platform(),
        }
        path.write_text(json.dumps(dump, indent=2), encoding="utf-8")
        logger.critical("Crash dump written to %s", path)
        return path
    except Exception as e:
        logger.error("Failed to write crash dump: %s", e)
        return None


def mark_running() -> None:
    """Create a lock file indicating the app is running."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOCK_FILE.write_text(datetime.now().isoformat(), encoding="utf-8")


def clear_running() -> None:
    """Remove the lock file on clean shutdown."""
    try:
        LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def check_unclean_shutdown() -> bool:
    """Return True if the previous session did not exit cleanly."""
    return LOCK_FILE.exists()
