"""
desktop/services/network_policy.py — Network governance for RecallOS Desktop.

Provides a global "Disable all network" switch, per-feature toggles
(updates, connectors, telemetry), and a transparent activity log of every
outbound network attempt.

All code that wants to make an outbound request MUST call
``NetworkPolicy.check(feature, host, path)`` first.  The call is logged
regardless of whether access is allowed or denied.

Policy state is persisted in the desktop SQLite ``settings`` table.
Activity is logged to the ``network_log`` table.
"""

from __future__ import annotations

import sqlite3
from typing import Literal

from desktop.db import get_connection

Feature = Literal["updates", "connectors", "telemetry"]

FEATURES: tuple[Feature, ...] = ("updates", "connectors", "telemetry")

# Setting keys ---
_KEY_GLOBAL = "network.enabled"
_KEY_PREFIX = "network.feature."

# Defaults: network enabled, telemetry OFF, everything else ON
_DEFAULTS: dict[str, str] = {
    _KEY_GLOBAL: "true",
    **{f"{_KEY_PREFIX}{f}": "true" if f != "telemetry" else "false" for f in FEATURES},
}


class NetworkPolicy:
    """Read/write network governance policy backed by SQLite."""

    def __init__(self, conn: sqlite3.Connection | None = None):
        self._conn = conn or get_connection()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, key: str) -> str:
        row = self._conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if row is not None:
            return row[0]
        default = _DEFAULTS.get(key, "false")
        self._set(key, default)
        return default

    def _set(self, key: str, value: str) -> None:
        self._conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?)"
            " ON CONFLICT(key) DO UPDATE SET value = excluded.value,"
            " updated_at = datetime('now')",
            (key, value),
        )
        self._conn.commit()

    @staticmethod
    def _bool(value: str) -> bool:
        return value.lower() in ("true", "1", "yes")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def enabled(self) -> bool:
        """Global network switch.  When False, ALL outbound access is denied."""
        return self._bool(self._get(_KEY_GLOBAL))

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._set(_KEY_GLOBAL, str(value).lower())

    def is_feature_allowed(self, feature: Feature) -> bool:
        """Check whether *feature* is allowed to make outbound calls.

        Returns False if the global switch is off OR the per-feature
        toggle is off.
        """
        if not self.enabled:
            return False
        return self._bool(self._get(f"{_KEY_PREFIX}{feature}"))

    def set_feature_allowed(self, feature: Feature, allowed: bool) -> None:
        self._set(f"{_KEY_PREFIX}{feature}", str(allowed).lower())

    # ------------------------------------------------------------------
    # Check + log  (the call-site API)
    # ------------------------------------------------------------------

    def check(self, feature: Feature, host: str, path: str = "") -> bool:
        """Check access and log the attempt.  Returns True if allowed."""
        allowed = self.is_feature_allowed(feature)
        self._log(feature, host, path, allowed)
        return allowed

    def _log(self, feature: str, host: str, path: str, allowed: bool) -> None:
        self._conn.execute(
            "INSERT INTO network_log (feature, host, path, allowed) VALUES (?, ?, ?, ?)",
            (feature, host, path, int(allowed)),
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_log(self, limit: int = 100) -> list[dict]:
        """Return recent network activity log entries."""
        rows = self._conn.execute(
            "SELECT feature, host, path, allowed, created_at"
            " FROM network_log ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {
                "feature": r[0],
                "host": r[1],
                "path": r[2],
                "allowed": bool(r[3]),
                "timestamp": r[4],
            }
            for r in rows
        ]

    def get_policy(self) -> dict:
        """Return the full policy state as a serialisable dict."""
        return {
            "enabled": self.enabled,
            "features": {f: self.is_feature_allowed(f) for f in FEATURES},
        }

    def set_policy(self, enabled: bool | None, features: dict | None) -> dict:
        """Bulk-update policy.  Returns the new state."""
        if enabled is not None:
            self.enabled = enabled
        if features:
            for feat, allowed in features.items():
                if feat in FEATURES:
                    self.set_feature_allowed(feat, bool(allowed))
        return self.get_policy()
