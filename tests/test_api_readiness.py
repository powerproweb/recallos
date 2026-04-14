"""
test_api_readiness.py — Verify core modules are safe to call from a service context.

Key guarantee: no function called by the desktop API layer should ever call
sys.exit() or input().  They must raise structured exceptions instead.
"""

import tempfile
import os

import pytest

from recallos.exceptions import (
    RecallOSError,
    VaultNotFoundError,
    ConfigNotFoundError,
    QueryError,
    DirectoryNotFoundError,
)


# ---------------------------------------------------------------------------
# retrieval_engine.search() — must raise, not sys.exit()
# ---------------------------------------------------------------------------


def test_search_raises_vault_not_found():
    """search() on a missing vault raises VaultNotFoundError."""
    from recallos.retrieval_engine import search

    with pytest.raises(VaultNotFoundError):
        search(query="test", vault_path="/nonexistent/vault")


def test_search_memories_returns_error_dict():
    """search_memories() returns an error dict (pre-existing behavior, still works)."""
    from recallos.retrieval_engine import search_memories

    result = search_memories(query="test", vault_path="/nonexistent/vault")
    assert "error" in result


# ---------------------------------------------------------------------------
# ingest_engine.load_config() — must raise, not sys.exit()
# ---------------------------------------------------------------------------


def test_load_config_raises_config_not_found():
    """load_config() on a directory without recallos.yaml raises ConfigNotFoundError."""
    from recallos.ingest_engine import load_config

    with pytest.raises(ConfigNotFoundError):
        load_config(tempfile.mkdtemp())


# ---------------------------------------------------------------------------
# node_detector_local — must raise, not sys.exit()
# ---------------------------------------------------------------------------


def test_detect_nodes_local_raises_directory_not_found():
    """detect_nodes_local() on a missing directory raises DirectoryNotFoundError."""
    from recallos.node_detector_local import detect_nodes_local

    with pytest.raises(DirectoryNotFoundError):
        detect_nodes_local("/nonexistent/dir/abc123", interactive=False)


def test_detect_nodes_local_non_interactive():
    """detect_nodes_local() with interactive=False completes without input()."""
    from recallos.node_detector_local import detect_nodes_local

    tmpdir = tempfile.mkdtemp()
    # Create a minimal file so scan finds something
    with open(os.path.join(tmpdir, "readme.md"), "w") as f:
        f.write("# Test project\n")

    # Should not prompt — just auto-accept nodes and write recallos.yaml
    detect_nodes_local(tmpdir, interactive=False)
    assert os.path.exists(os.path.join(tmpdir, "recallos.yaml"))


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


def test_all_errors_are_recallos_errors():
    """All custom exceptions inherit from RecallOSError."""
    assert issubclass(VaultNotFoundError, RecallOSError)
    assert issubclass(ConfigNotFoundError, RecallOSError)
    assert issubclass(QueryError, RecallOSError)
    assert issubclass(DirectoryNotFoundError, RecallOSError)


def test_vault_not_found_has_vault_path():
    err = VaultNotFoundError("/some/path")
    assert err.vault_path == "/some/path"
    assert "/some/path" in str(err)


def test_config_not_found_has_project_dir():
    err = ConfigNotFoundError("/some/project")
    assert err.project_dir == "/some/project"
    assert "recallos init" in str(err)
