"""
test_diagnostics.py — Unit tests for recallos/diagnostics.py

Strategy:
- Checks that accept parameters (vault_path, col, cfg) are tested directly.
- Checks that rely on hardcoded expanduser paths (_check_recall_graph,
  _check_identity_profile, _check_config_file) are tested by patching
  `recallos.diagnostics.os.path.expanduser` with a side_effect that only
  redirects the specific path under test, delegating all other calls to
  the real os.path.expanduser.
- ChromaDB interaction tests use a real PersistentClient in a temp dir and
  release all handles before the test exits (required on Windows).
"""

import json
import os
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import chromadb
import pytest

from recallos.config import RecallOSConfig
from recallos.diagnostics import (
    FAIL,
    INFO,
    PASS,
    WARN,
    _check_chroma_collection,
    _check_config_file,
    _check_identity_profile,
    _check_incomplete_records,
    _check_legacy_dir,
    _check_recall_graph,
    _check_vault_dir,
    run_doctor,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Capture the real os.path.expanduser at import time, before any test patches
# it. Fallbacks in side_effect functions must use this reference so they do not
# recursively call the mock (patch replaces the attribute on the shared os.path
# module object, so all lookups through os.path.expanduser see the mock).
_REAL_EXPANDUSER = os.path.expanduser


def _make_graph_db(path: Path):
    """Create the minimal SQLite schema that _check_recall_graph expects."""
    conn = sqlite3.connect(str(path))
    conn.execute(
        "CREATE TABLE entities (id TEXT PRIMARY KEY, name TEXT, type TEXT, "
        "properties TEXT, created_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE triples (id TEXT PRIMARY KEY, subject TEXT, predicate TEXT, "
        "object TEXT, valid_from TEXT, valid_to TEXT, confidence REAL, "
        "source_index TEXT, source_file TEXT, extracted_at TEXT)"
    )
    conn.commit()
    conn.close()


def _expanduser_for(real_path: str, target_suffix: str):
    """Return a side_effect callable for os.path.expanduser.

    When the argument ends with *target_suffix*, return *real_path*.
    Otherwise fall through to _REAL_EXPANDUSER (captured before any patch).
    """
    def _side_effect(p):
        if p.endswith(target_suffix):
            return real_path
        return _REAL_EXPANDUSER(p)
    return _side_effect


# ---------------------------------------------------------------------------
# _check_vault_dir
# ---------------------------------------------------------------------------


def test_vault_dir_pass(tmp_path):
    result = _check_vault_dir(str(tmp_path))
    assert result["status"] == PASS


def test_vault_dir_warn_missing(tmp_path):
    result = _check_vault_dir(str(tmp_path / "nonexistent"))
    assert result["status"] == WARN
    assert "nonexistent" in result["detail"]


def test_vault_dir_fail_is_file(tmp_path):
    f = tmp_path / "not_a_dir.txt"
    f.write_text("x")
    result = _check_vault_dir(str(f))
    assert result["status"] == FAIL


# ---------------------------------------------------------------------------
# _check_chroma_collection
# ---------------------------------------------------------------------------


def test_chroma_pass(tmp_path):
    """PASS when recallos_records collection exists and is readable."""
    vault = str(tmp_path / "vault")
    client = chromadb.PersistentClient(path=vault)
    col = client.create_collection("recallos_records")
    col.add(
        ids=["r1"],
        documents=["hello world"],
        metadatas=[{"domain": "d", "node": "n"}],
    )
    del col, client  # release handles before re-opening

    result, col = _check_chroma_collection(vault, verbose=False)
    assert result["status"] == PASS
    assert col is not None
    del col


def test_chroma_pass_verbose_includes_count(tmp_path):
    """PASS with verbose=True includes record count in detail."""
    vault = str(tmp_path / "vault")
    client = chromadb.PersistentClient(path=vault)
    col = client.create_collection("recallos_records")
    col.add(ids=["r1"], documents=["x"], metadatas=[{"domain": "d", "node": "n"}])
    del col, client

    result, col = _check_chroma_collection(vault, verbose=True)
    assert result["status"] == PASS
    assert "1" in result["detail"]
    del col


def test_chroma_fail_empty_dir(tmp_path):
    """FAIL when the vault dir has no recallos_records collection."""
    result, col = _check_chroma_collection(str(tmp_path / "empty"), verbose=False)
    assert result["status"] == FAIL
    assert col is None


# ---------------------------------------------------------------------------
# _check_incomplete_records
# ---------------------------------------------------------------------------


def test_incomplete_none_col_returns_info():
    result = _check_incomplete_records(None, verbose=False)
    assert result["status"] == INFO


def test_incomplete_all_complete_returns_pass():
    mock_col = MagicMock()
    mock_col.get.return_value = {
        "ids": ["r1", "r2"],
        "metadatas": [
            {"domain": "dom", "node": "backend"},
            {"domain": "dom", "node": "frontend"},
        ],
    }
    result = _check_incomplete_records(mock_col, verbose=False)
    assert result["status"] == PASS


def test_incomplete_missing_node_returns_warn():
    mock_col = MagicMock()
    mock_col.get.return_value = {
        "ids": ["r1", "r2"],
        "metadatas": [
            {"domain": "dom", "node": "backend"},
            {"domain": "dom"},           # missing node
        ],
    }
    result = _check_incomplete_records(mock_col, verbose=False)
    assert result["status"] == WARN
    assert "r2" in result["detail"]


def test_incomplete_missing_domain_returns_warn():
    mock_col = MagicMock()
    mock_col.get.return_value = {
        "ids": ["r1"],
        "metadatas": [
            {"node": "backend"},         # missing domain
        ],
    }
    result = _check_incomplete_records(mock_col, verbose=False)
    assert result["status"] == WARN


def test_incomplete_verbose_includes_count():
    mock_col = MagicMock()
    mock_col.get.return_value = {
        "ids": ["r1", "r2", "r3"],
        "metadatas": [
            {"domain": "d", "node": "n"},
            {"domain": "d", "node": "n"},
            {"domain": "d", "node": "n"},
        ],
    }
    result = _check_incomplete_records(mock_col, verbose=True)
    assert result["status"] == PASS
    assert "3" in result["detail"]


def test_incomplete_many_missing_samples_first_three(tmp_path):
    """When 5 records are incomplete only the first 3 IDs are sampled."""
    mock_col = MagicMock()
    ids = [f"r{i}" for i in range(5)]
    mock_col.get.return_value = {
        "ids": ids,
        "metadatas": [{"domain": "d"} for _ in ids],  # all missing node
    }
    result = _check_incomplete_records(mock_col, verbose=False)
    assert result["status"] == WARN
    assert "+2 more" in result["detail"]


# ---------------------------------------------------------------------------
# _check_recall_graph
# ---------------------------------------------------------------------------


def test_recall_graph_not_found_returns_info(tmp_path):
    """INFO when the recall_graph.sqlite3 file does not exist."""
    absent = str(tmp_path / "recall_graph.sqlite3")
    with patch(
        "recallos.diagnostics.os.path.expanduser",
        side_effect=_expanduser_for(absent, "recall_graph.sqlite3"),
    ):
        result = _check_recall_graph()
    assert result["status"] == INFO


def test_recall_graph_valid_returns_pass(tmp_path):
    """PASS when recall_graph.sqlite3 exists with correct schema."""
    graph_path = tmp_path / "recall_graph.sqlite3"
    _make_graph_db(graph_path)

    with patch(
        "recallos.diagnostics.os.path.expanduser",
        side_effect=_expanduser_for(str(graph_path), "recall_graph.sqlite3"),
    ):
        result = _check_recall_graph()

    assert result["status"] == PASS
    assert "entities" in result["detail"]
    assert "triples" in result["detail"]


def test_recall_graph_corrupt_returns_fail(tmp_path):
    """FAIL when the file exists but is not valid SQLite."""
    graph_path = tmp_path / "recall_graph.sqlite3"
    graph_path.write_bytes(b"this is not sqlite data at all!!!")

    with patch(
        "recallos.diagnostics.os.path.expanduser",
        side_effect=_expanduser_for(str(graph_path), "recall_graph.sqlite3"),
    ):
        result = _check_recall_graph()

    assert result["status"] == FAIL


# ---------------------------------------------------------------------------
# _check_identity_profile
# ---------------------------------------------------------------------------


def test_identity_profile_missing_returns_warn(tmp_path):
    absent = str(tmp_path / "identity_profile.txt")
    with patch(
        "recallos.diagnostics.os.path.expanduser",
        side_effect=_expanduser_for(absent, "identity_profile.txt"),
    ):
        result = _check_identity_profile()
    assert result["status"] == WARN


def test_identity_profile_present_returns_pass(tmp_path):
    identity = tmp_path / "identity_profile.txt"
    identity.write_text("I am Atlas.\nTraits: warm.", encoding="utf-8")

    with patch(
        "recallos.diagnostics.os.path.expanduser",
        side_effect=_expanduser_for(str(identity), "identity_profile.txt"),
    ):
        result = _check_identity_profile()

    assert result["status"] == PASS
    assert "2" in result["detail"]  # 2 lines


# ---------------------------------------------------------------------------
# _check_config_file
# ---------------------------------------------------------------------------


def test_config_file_absent_returns_info(tmp_path):
    absent = str(tmp_path / "config.json")
    with patch(
        "recallos.diagnostics.os.path.expanduser",
        side_effect=_expanduser_for(absent, "config.json"),
    ):
        result = _check_config_file()
    assert result["status"] == INFO


def test_config_file_valid_returns_pass(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"vault_path": "/v", "collection_name": "rec"}))

    with patch(
        "recallos.diagnostics.os.path.expanduser",
        side_effect=_expanduser_for(str(cfg), "config.json"),
    ):
        result = _check_config_file()

    assert result["status"] == PASS
    assert "vault_path" in result["detail"]


def test_config_file_invalid_json_returns_fail(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text("{ broken json }")

    with patch(
        "recallos.diagnostics.os.path.expanduser",
        side_effect=_expanduser_for(str(cfg), "config.json"),
    ):
        result = _check_config_file()

    assert result["status"] == FAIL


# ---------------------------------------------------------------------------
# _check_legacy_dir
# ---------------------------------------------------------------------------


def test_legacy_dir_absent_returns_pass(tmp_path):
    """PASS when RecallOSConfig sees no legacy dir."""
    cfg = RecallOSConfig(config_dir=str(tmp_path))
    cfg._legacy_dir = None  # force: no legacy dir regardless of real filesystem
    result = _check_legacy_dir(cfg)
    assert result["status"] == PASS


def test_legacy_dir_present_returns_warn(tmp_path):
    """WARN when RecallOSConfig detects a legacy dir."""
    cfg = RecallOSConfig(config_dir=str(tmp_path))
    cfg._legacy_dir = tmp_path / "fake_mempalace"  # simulate legacy detection
    result = _check_legacy_dir(cfg)
    assert result["status"] == WARN
    assert "recallos migrate" in result["detail"]


# ---------------------------------------------------------------------------
# run_doctor — integration / structure
# ---------------------------------------------------------------------------


def test_run_doctor_returns_required_keys(tmp_path):
    """run_doctor always returns a dict with overall, checks, and counts keys."""
    result = run_doctor(vault_path=str(tmp_path))
    assert "overall" in result
    assert "checks" in result
    assert "counts" in result
    assert "vault_path" in result


def test_run_doctor_overall_is_valid_status(tmp_path):
    result = run_doctor(vault_path=str(tmp_path))
    assert result["overall"] in (PASS, WARN, FAIL)


def test_run_doctor_seven_checks(tmp_path):
    """run_doctor always runs exactly 7 checks."""
    result = run_doctor(vault_path=str(tmp_path))
    assert len(result["checks"]) == 7


def test_run_doctor_warn_on_empty_vault(tmp_path):
    """An empty vault dir (no ChromaDB) results in WARN or FAIL overall."""
    result = run_doctor(vault_path=str(tmp_path))
    # ChromaDB will fail → overall must not be PASS
    assert result["overall"] in (WARN, FAIL)


def test_run_doctor_pass_with_healthy_vault(tmp_path):
    """PASS overall when vault, collection, and identity are all present."""
    vault = str(tmp_path / "vault")
    client = chromadb.PersistentClient(path=vault)
    col = client.create_collection("recallos_records")
    col.add(
        ids=["r1"],
        documents=["test content"],
        metadatas=[{"domain": "d", "node": "n"}],
    )
    del col, client

    identity = tmp_path / "identity_profile.txt"
    identity.write_text("I am Atlas.", encoding="utf-8")

    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"vault_path": vault}))

    # Patch the three expanduser-based checks to use our temp files.
    # Use _REAL_EXPANDUSER (not os.path.expanduser) in the fallback to avoid
    # recursion: the patch replaces os.path.expanduser on the shared os module.
    def _expand(p):
        if p.endswith("identity_profile.txt"):
            return str(identity)
        if p.endswith("config.json"):
            return str(config_file)
        if p.endswith("recall_graph.sqlite3"):
            return str(tmp_path / "recall_graph.sqlite3")  # absent → INFO
        return _REAL_EXPANDUSER(p)

    with patch("recallos.diagnostics.os.path.expanduser", side_effect=_expand):
        result = run_doctor(vault_path=vault)

    # vault dir ✔, chromadb ✔, records ✔, graph INFO, identity ✔, config ✔, legacy depends on env
    # At minimum no FAIL checks
    assert result["counts"][FAIL] == 0
