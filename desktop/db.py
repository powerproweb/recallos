"""
desktop/db.py — Local SQLite database for the RecallOS desktop layer.

Stores settings, API connections, background jobs, and audit events.
File location: ~/.recallos/desktop.db

Design notes:
  - WAL mode for concurrent reads during indexing
  - Schema versioned via ``schema_version`` table for future migrations
  - Encryption upgrade path (SQLCipher) planned for Phase 2
"""

import os
import sqlite3
from pathlib import Path

DB_DIR = Path(os.path.expanduser("~/.recallos"))
DB_PATH = DB_DIR / "desktop.db"

SCHEMA_VERSION = 2

# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

_SCHEMA = """
-- Track schema version for future migrations
CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER NOT NULL,
    applied_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- App-level key/value settings
CREATE TABLE IF NOT EXISTS settings (
    key         TEXT PRIMARY KEY,
    value       TEXT,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- External API / connector configurations
CREATE TABLE IF NOT EXISTS api_connections (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    type        TEXT    NOT NULL,
    auth_type   TEXT,
    endpoint    TEXT,
    scopes      TEXT,
    enabled     INTEGER NOT NULL DEFAULT 1,
    last_sync   TEXT,
    last_error  TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Background jobs (ingest, export, index, etc.)
CREATE TABLE IF NOT EXISTS jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'pending',
    params      TEXT,
    result      TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Granular events within a job (progress, errors, retries)
CREATE TABLE IF NOT EXISTS job_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id      INTEGER NOT NULL REFERENCES jobs(id),
    event_type  TEXT    NOT NULL,
    detail      TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Audit log for privileged actions (credential changes, exports, etc.)
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    action      TEXT    NOT NULL,
    detail      TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Network activity log (Phase 0.2 — sovereignty guardrails)
CREATE TABLE IF NOT EXISTS network_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    feature     TEXT    NOT NULL,
    host        TEXT    NOT NULL,
    path        TEXT    NOT NULL DEFAULT '',
    allowed     INTEGER NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_connection() -> sqlite3.Connection:
    """Open (or create) the desktop database with WAL mode enabled."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create tables if they don't exist and stamp the schema version."""
    conn = get_connection()
    conn.executescript(_SCHEMA)

    # Stamp version if table is empty
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    if row[0] is None:
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
        conn.commit()
    conn.close()


def current_version() -> int:
    """Return the current schema version (0 if DB doesn't exist)."""
    if not DB_PATH.exists():
        return 0
    conn = get_connection()
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return row[0] or 0
    except Exception:
        return 0
    finally:
        conn.close()
