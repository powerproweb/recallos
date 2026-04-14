"""
test_sovereignty.py — Phase 0.2 sovereignty guardrails.

Tests for:
  1. Per-session auth token (generation, validation, rejection)
  2. Network policy (global switch, per-feature toggles, logging)
  3. External assets check (no remote URLs in static bundle)
"""

import os
import sqlite3

import pytest

from desktop.auth import (
    generate_session_token,
    get_session_token,
    require_session_token,
    TOKEN_HEADER,
)
from desktop.db import _SCHEMA
from scripts.check_no_external_assets import scan_file, main as check_main

# ---------------------------------------------------------------------------
# 1. Session auth
# ---------------------------------------------------------------------------


def test_generate_session_token_returns_string():
    token = generate_session_token()
    assert isinstance(token, str)
    assert len(token) > 20


def test_generate_sets_env_var():
    token = generate_session_token()
    assert os.environ.get("RECALLOS_SESSION_TOKEN") == token


def test_get_session_token_matches():
    token = generate_session_token()
    assert get_session_token() == token


def test_each_call_generates_unique_token():
    t1 = generate_session_token()
    t2 = generate_session_token()
    assert t1 != t2


class _FakeRequest:
    """Minimal request stub for testing the dependency."""

    def __init__(self, headers: dict | None = None):
        self.headers = headers or {}


@pytest.mark.asyncio
async def test_require_session_token_accepts_valid():
    token = generate_session_token()
    req = _FakeRequest(headers={TOKEN_HEADER: token})
    # Should not raise
    await require_session_token(req)


@pytest.mark.asyncio
async def test_require_session_token_rejects_missing():
    generate_session_token()
    req = _FakeRequest(headers={})
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await require_session_token(req)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_session_token_rejects_wrong():
    generate_session_token()
    req = _FakeRequest(headers={TOKEN_HEADER: "wrong-token"})
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await require_session_token(req)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_session_token_skips_when_no_token_configured():
    """When no token is set (dev mode), auth is skipped."""
    import desktop.auth as auth_mod

    # Clear all token state
    auth_mod._SESSION_TOKEN = None
    os.environ.pop("RECALLOS_SESSION_TOKEN", None)

    req = _FakeRequest(headers={})
    await require_session_token(req)  # should not raise


# ---------------------------------------------------------------------------
# 2. Network policy
# ---------------------------------------------------------------------------


def _make_db() -> sqlite3.Connection:
    """Create a fresh in-memory SQLite DB with the desktop schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def test_network_policy_defaults():
    from desktop.services.network_policy import NetworkPolicy

    policy = NetworkPolicy(conn=_make_db())
    state = policy.get_policy()
    assert state["enabled"] is True
    assert state["features"]["updates"] is True
    assert state["features"]["connectors"] is True
    assert state["features"]["telemetry"] is False  # off by default


def test_global_kill_switch():
    from desktop.services.network_policy import NetworkPolicy

    policy = NetworkPolicy(conn=_make_db())
    policy.enabled = False

    assert policy.enabled is False
    # All features should be denied when global is off
    assert policy.is_feature_allowed("updates") is False
    assert policy.is_feature_allowed("connectors") is False
    assert policy.is_feature_allowed("telemetry") is False


def test_per_feature_toggle():
    from desktop.services.network_policy import NetworkPolicy

    policy = NetworkPolicy(conn=_make_db())
    policy.set_feature_allowed("updates", False)

    assert policy.is_feature_allowed("updates") is False
    assert policy.is_feature_allowed("connectors") is True  # unchanged


def test_check_logs_activity():
    from desktop.services.network_policy import NetworkPolicy

    policy = NetworkPolicy(conn=_make_db())

    result = policy.check("updates", "releases.example.com", "/latest")
    assert result is True

    log = policy.get_log()
    assert len(log) == 1
    assert log[0]["feature"] == "updates"
    assert log[0]["host"] == "releases.example.com"
    assert log[0]["path"] == "/latest"
    assert log[0]["allowed"] is True


def test_check_logs_denied():
    from desktop.services.network_policy import NetworkPolicy

    policy = NetworkPolicy(conn=_make_db())
    policy.enabled = False

    result = policy.check("connectors", "api.example.com", "/sync")
    assert result is False

    log = policy.get_log()
    assert len(log) == 1
    assert log[0]["allowed"] is False


def test_set_policy_bulk_update():
    from desktop.services.network_policy import NetworkPolicy

    policy = NetworkPolicy(conn=_make_db())
    new_state = policy.set_policy(
        enabled=True,
        features={"telemetry": True, "updates": False},
    )

    assert new_state["enabled"] is True
    assert new_state["features"]["telemetry"] is True
    assert new_state["features"]["updates"] is False
    assert new_state["features"]["connectors"] is True  # unchanged


# ---------------------------------------------------------------------------
# 3. External assets check
# ---------------------------------------------------------------------------


def test_scan_file_detects_external_url(tmp_path):
    f = tmp_path / "bad.js"
    f.write_text('import "https://cdn.example.com/lib.js";\n', encoding="utf-8")

    hits = scan_file(f)
    assert len(hits) == 1
    assert "cdn.example.com" in hits[0][1]


def test_scan_file_allows_localhost(tmp_path):
    f = tmp_path / "ok.js"
    f.write_text('fetch("http://127.0.0.1:8000/api/status");\n', encoding="utf-8")

    hits = scan_file(f)
    assert len(hits) == 0


def test_scan_file_allows_w3_namespace(tmp_path):
    f = tmp_path / "ok.html"
    f.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>\n', encoding="utf-8")

    hits = scan_file(f)
    assert len(hits) == 0


def test_check_main_passes_clean_dir(tmp_path):
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    (tmp_path / "app.js").write_text("console.log('ok');", encoding="utf-8")

    result = check_main(str(tmp_path))
    assert result == 0


def test_check_main_fails_on_external_url(tmp_path):
    (tmp_path / "app.js").write_text(
        'loadScript("https://evil.example.com/track.js");\n',
        encoding="utf-8",
    )

    result = check_main(str(tmp_path))
    assert result == 1


def test_check_main_skips_nonexistent_dir():
    result = check_main("/nonexistent/path/abc123")
    assert result == 0
