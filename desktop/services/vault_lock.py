"""
desktop/services/vault_lock.py — Passphrase-based vault locking.

When Vault Lock is enabled, the user must enter a passphrase to access
the desktop app.  The passphrase hash (PBKDF2-HMAC-SHA256) is stored in
the settings table.

NOTE: This does NOT encrypt the SQLite database at rest (that requires
SQLCipher, tracked as a future upgrade).  What it provides is:
  - An app-level gate that prevents casual access
  - A passphrase hash that can later be used as the SQLCipher key

Upgrade path to full encryption:
  1. Install sqlcipher3 / pysqlcipher3
  2. Use the PBKDF2-derived key to open the DB via SQLCipher pragmas
  3. Migrate existing unencrypted DB to encrypted format
"""

from __future__ import annotations

import hashlib
import logging
import os

from desktop.db import get_connection, init_db

logger = logging.getLogger("vault_lock")

_SALT_KEY = "vault_lock.salt"
_HASH_KEY = "vault_lock.hash"
_ENABLED_KEY = "vault_lock.enabled"


def _pbkdf2(passphrase: str, salt: bytes) -> str:
    """Derive a key from the passphrase using PBKDF2-HMAC-SHA256."""
    dk = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, iterations=600_000)
    return dk.hex()


def is_enabled() -> bool:
    """Check if Vault Lock is enabled."""
    init_db()
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (_ENABLED_KEY,)).fetchone()
    conn.close()
    return row is not None and row[0] == "true"


def enable(passphrase: str) -> dict:
    """Enable Vault Lock with the given passphrase."""
    if not passphrase or len(passphrase) < 8:
        return {"status": "error", "message": "Passphrase must be at least 8 characters"}

    salt = os.urandom(32)
    pw_hash = _pbkdf2(passphrase, salt)

    init_db()
    conn = get_connection()
    for key, value in [
        (_SALT_KEY, salt.hex()),
        (_HASH_KEY, pw_hash),
        (_ENABLED_KEY, "true"),
    ]:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?)"
            " ON CONFLICT(key) DO UPDATE SET value = excluded.value,"
            " updated_at = datetime('now')",
            (key, value),
        )
    conn.commit()
    conn.close()

    logger.info("Vault Lock enabled")
    return {"status": "ok", "message": "Vault Lock enabled"}


def disable(passphrase: str) -> dict:
    """Disable Vault Lock (requires current passphrase)."""
    if not verify(passphrase):
        return {"status": "error", "message": "Incorrect passphrase"}

    init_db()
    conn = get_connection()
    for key in (_SALT_KEY, _HASH_KEY, _ENABLED_KEY):
        conn.execute("DELETE FROM settings WHERE key = ?", (key,))
    conn.commit()
    conn.close()

    logger.info("Vault Lock disabled")
    return {"status": "ok", "message": "Vault Lock disabled"}


def verify(passphrase: str) -> bool:
    """Verify a passphrase against the stored hash."""
    init_db()
    conn = get_connection()
    salt_row = conn.execute("SELECT value FROM settings WHERE key = ?", (_SALT_KEY,)).fetchone()
    hash_row = conn.execute("SELECT value FROM settings WHERE key = ?", (_HASH_KEY,)).fetchone()
    conn.close()

    if not salt_row or not hash_row:
        return False

    salt = bytes.fromhex(salt_row[0])
    expected = hash_row[0]
    return _pbkdf2(passphrase, salt) == expected


def get_status() -> dict:
    """Return Vault Lock status for the UI."""
    return {"enabled": is_enabled()}
