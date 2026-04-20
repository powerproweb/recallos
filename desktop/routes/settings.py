"""
/api/settings — Read/write app settings (vault path, theme, etc.).
"""

from fastapi import APIRouter
from pydantic import BaseModel

from desktop.db import get_connection, init_db

router = APIRouter(tags=["settings"])


class SettingsUpdate(BaseModel):
    key: str
    value: str


@router.get("/settings")
def get_all_settings():
    """Return all settings as a key-value dict."""
    init_db()
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {"settings": {r[0]: r[1] for r in rows}}


@router.put("/settings")
def update_setting(body: SettingsUpdate):
    """Update a single setting."""
    init_db()
    conn = get_connection()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?)"
        " ON CONFLICT(key) DO UPDATE SET value = excluded.value,"
        " updated_at = datetime('now')",
        (body.key, body.value),
    )
    conn.commit()
    conn.close()
    return {"key": body.key, "value": body.value}
