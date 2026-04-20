"""
desktop/services/logging_service.py — Structured JSON logging for RecallOS Desktop.

Writes JSON-formatted log lines to ~/.recallos/logs/ with automatic 7-day rotation.
Call ``init_logging()`` once at app startup to configure the root logger.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

LOG_DIR = Path(os.path.expanduser("~/.recallos/logs"))
LOG_FILE = LOG_DIR / "recallos-desktop.log"
RETENTION_DAYS = 7


class JSONFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def init_logging(level: int = logging.INFO) -> None:
    """Configure the root logger with a JSON file handler + console handler."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers on repeated calls
    if any(isinstance(h, TimedRotatingFileHandler) for h in root.handlers):
        return

    # File handler — daily rotation, 7-day retention
    file_handler = TimedRotatingFileHandler(
        str(LOG_FILE),
        when="midnight",
        interval=1,
        backupCount=RETENTION_DAYS,
        encoding="utf-8",
    )
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(level)
    root.addHandler(file_handler)

    # Console handler — brief format for dev
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(levelname)-5s %(name)s: %(message)s"))
    console.setLevel(logging.WARNING)
    root.addHandler(console)


def log_frontend_error(source: str, message: str, stack: str = "") -> None:
    """Log an error forwarded from the frontend error boundary."""
    logger = logging.getLogger("frontend")
    logger.error("%s: %s\n%s", source, message, stack)
