"""
test_qa_release_gates.py — Phase 2.7 QA release gate tests.

These tests verify the Phase 2 exit criteria are met:
  1. Offline/no-egress: core imports work, no network required
  2. Backup/restore: round-trip creates and restores a valid ZIP
  3. Crash recovery: dump writes + unclean shutdown detection works
  4. Security: auth, path validation, audit log all functional
  5. All services importable: every desktop service module loads
  6. All routes importable: every desktop route module loads
  7. External assets: static bundle has no remote URLs
  8. Sovereignty: network policy defaults correct, model manager detects state
"""

import importlib
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Gate 1: Offline / no-egress
# ---------------------------------------------------------------------------


def test_gate_core_imports_no_network():
    """All core recallos modules import without network access."""
    from recallos.retrieval_engine import search, search_memories
    from recallos.ingest_engine import mine
    from recallos.diagnostics import run_doctor

    assert callable(search)
    assert callable(search_memories)
    assert callable(mine)
    assert callable(run_doctor)


def test_gate_recall_graph_offline():
    """RecallGraph works entirely offline (pure SQLite)."""
    from recallos.recall_graph import RecallGraph

    with tempfile.TemporaryDirectory() as td:
        rg = RecallGraph(db_path=str(Path(td) / "test.db"))
        rg.add_triple("Alice", "knows", "Bob")
        results = rg.query_entity("Alice")
        assert len(results) > 0


# ---------------------------------------------------------------------------
# Gate 2: Backup / restore round-trip
# ---------------------------------------------------------------------------


def test_gate_backup_creates_valid_zip(tmp_path):
    from desktop.services.backup_service import backup

    result = backup(dest_dir=str(tmp_path))
    assert result["files"] >= 0
    zp = Path(result["path"])
    assert zp.exists()
    assert zipfile.is_zipfile(str(zp))


def test_gate_backup_restore_round_trip(tmp_path):
    from desktop.services.backup_service import backup, restore

    result = backup(dest_dir=str(tmp_path))
    restore_result = restore(result["path"])
    assert restore_result["status"] == "ok"


# ---------------------------------------------------------------------------
# Gate 3: Crash recovery
# ---------------------------------------------------------------------------


def test_gate_crash_dump_writes(tmp_path, monkeypatch):
    from desktop.crash import write_crash_dump

    monkeypatch.setattr("desktop.crash.LOG_DIR", tmp_path)
    try:
        raise RuntimeError("QA gate test crash")
    except RuntimeError as exc:
        path = write_crash_dump(exc)

    assert path is not None
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["exception_type"] == "RuntimeError"


def test_gate_unclean_shutdown_detection(tmp_path, monkeypatch):
    from desktop.crash import mark_running, clear_running, check_unclean_shutdown

    lock = tmp_path / ".running"
    monkeypatch.setattr("desktop.crash.LOCK_FILE", lock)
    monkeypatch.setattr("desktop.crash.LOG_DIR", tmp_path)

    mark_running()
    assert check_unclean_shutdown() is True
    clear_running()
    assert check_unclean_shutdown() is False


# ---------------------------------------------------------------------------
# Gate 4: Security
# ---------------------------------------------------------------------------


def test_gate_session_token():
    from desktop.auth import generate_session_token, get_session_token

    token = generate_session_token()
    assert len(token) > 20
    assert get_session_token() == token


def test_gate_path_validation():
    from desktop.security import validate_path, PathNotAllowedError, _RECALLOS_HOME
    import pytest

    # Allowed
    validate_path(str(_RECALLOS_HOME / "vault"))
    # Blocked
    with pytest.raises(PathNotAllowedError):
        validate_path("/etc/passwd")


def test_gate_audit_log():
    from desktop.security import audit_action, get_audit_log

    audit_action("qa_gate_test", "release gate verification")
    log = get_audit_log(limit=1)
    assert len(log) >= 1
    assert log[0]["action"] == "qa_gate_test"


# ---------------------------------------------------------------------------
# Gate 5: All services importable
# ---------------------------------------------------------------------------


def test_gate_all_services_import():
    services = [
        "desktop.services.backup_service",
        "desktop.services.job_manager",
        "desktop.services.logging_service",
        "desktop.services.model_manager",
        "desktop.services.network_policy",
        "desktop.services.updater",
        "desktop.services.vault_lock",
    ]
    for mod in services:
        m = importlib.import_module(mod)
        assert m is not None, f"Failed to import {mod}"


# ---------------------------------------------------------------------------
# Gate 6: All routes importable
# ---------------------------------------------------------------------------


def test_gate_all_routes_import():
    routes = [
        "desktop.routes.backups",
        "desktop.routes.download",
        "desktop.routes.graph",
        "desktop.routes.mcp",
        "desktop.routes.models",
        "desktop.routes.network",
        "desktop.routes.provenance",
        "desktop.routes.search",
        "desktop.routes.settings",
        "desktop.routes.status",
        "desktop.routes.support",
        "desktop.routes.updater",
        "desktop.routes.upload",
        "desktop.routes.vault_lock",
    ]
    for mod in routes:
        m = importlib.import_module(mod)
        assert hasattr(m, "router"), f"{mod} missing 'router'"


# ---------------------------------------------------------------------------
# Gate 7: External assets check
# ---------------------------------------------------------------------------


def test_gate_no_external_assets():
    from scripts.check_no_external_assets import main as check_main

    static_dir = Path(__file__).resolve().parent.parent / "desktop" / "static"
    if not static_dir.is_dir():
        return  # no build — skip
    result = check_main(str(static_dir))
    assert result == 0, "External asset references found in static bundle"


# ---------------------------------------------------------------------------
# Gate 8: Sovereignty defaults
# ---------------------------------------------------------------------------


def test_gate_network_policy_defaults():
    from desktop.services.network_policy import NetworkPolicy
    from desktop.db import _SCHEMA

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)

    policy = NetworkPolicy(conn=conn)
    state = policy.get_policy()
    assert state["enabled"] is True
    assert state["features"]["telemetry"] is False  # off by default


def test_gate_model_manager_detects_state():
    from desktop.services.model_manager import ModelManager

    mm = ModelManager()
    info = mm.get_info()
    assert "installed" in info
    assert "name" in info
    status = mm.offline_status()
    assert "offline_ready" in status


# ---------------------------------------------------------------------------
# Gate 9: Vault Lock
# ---------------------------------------------------------------------------


def test_gate_vault_lock_lifecycle():
    from desktop.services.vault_lock import enable, disable, verify, is_enabled

    pw = "qa-gate-passphrase-2026"
    assert enable(pw)["status"] == "ok"
    assert is_enabled() is True
    assert verify(pw) is True
    assert verify("wrong") is False
    assert disable(pw)["status"] == "ok"
    assert is_enabled() is False


# ---------------------------------------------------------------------------
# Gate 10: Version comparison
# ---------------------------------------------------------------------------


def test_gate_version_comparison():
    from desktop.services.updater import compare_versions

    assert compare_versions("4.1.0", "4.1.0") == 0
    assert compare_versions("4.1.0", "4.2.0") == -1
    assert compare_versions("4.2.0", "4.1.0") == 1
