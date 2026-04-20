"""
desktop/services/job_manager.py — Threaded background task queue with SQLite-backed state.

Jobs are created in the ``jobs`` table with status='pending', then executed
in a background thread.  Status transitions: pending → running → done | failed.
Each status change is recorded in ``job_events``.
"""

from __future__ import annotations

import json
import threading
import traceback
from datetime import datetime

from desktop.db import get_connection, init_db


def _now() -> str:
    return datetime.now().isoformat()


class JobManager:
    """Create and run background jobs persisted in SQLite."""

    def __init__(self):
        init_db()

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_job(self, job_type: str, params: dict | None = None) -> int:
        """Insert a new pending job and return its ID."""
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO jobs (type, status, params, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (job_type, "pending", json.dumps(params or {}), _now(), _now()),
        )
        conn.commit()
        job_id = cur.lastrowid
        conn.close()
        return job_id

    # ------------------------------------------------------------------
    # Status transitions
    # ------------------------------------------------------------------

    def _set_status(self, job_id: int, status: str, result: str | None = None) -> None:
        conn = get_connection()
        conn.execute(
            "UPDATE jobs SET status = ?, result = ?, updated_at = ? WHERE id = ?",
            (status, result, _now(), job_id),
        )
        conn.execute(
            "INSERT INTO job_events (job_id, event_type, detail, created_at) VALUES (?, ?, ?, ?)",
            (job_id, status, result, _now()),
        )
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run_in_background(self, job_id: int, fn, *args, **kwargs) -> None:
        """Execute *fn* in a daemon thread, updating job status."""

        def _worker():
            self._set_status(job_id, "running")
            try:
                result = fn(*args, **kwargs)
                self._set_status(job_id, "done", json.dumps(result) if result else None)
            except Exception:
                self._set_status(job_id, "failed", traceback.format_exc()[:2000])

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_job(self, job_id: int) -> dict | None:
        conn = get_connection()
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        conn.close()
        if not row:
            return None
        return dict(row)

    def list_jobs(self, limit: int = 20) -> list[dict]:
        conn = get_connection()
        rows = conn.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
