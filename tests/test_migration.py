"""
test_migration.py — Unit tests for recallos/migration.py

Strategy: patch module-level Path constants (LEGACY_GRAPH, NEW_GRAPH, etc.)
so tests never touch the real ~/.mempalace or ~/.recallos directories.
"""

import json
import sqlite3
from pathlib import Path
from unittest.mock import patch


import recallos.migration as migration_module
from recallos.migration import (
    _migrate_config,
    _migrate_graph,
    _migrate_identity,
    migrate_from_mempalace,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_valid_sqlite(path: Path):
    """Create a minimal SQLite file that passes PRAGMA integrity_check."""
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# migrate_from_mempalace — top-level entry point
# ---------------------------------------------------------------------------


def test_nothing_to_migrate_when_legacy_absent(tmp_path):
    """Returns nothing_to_migrate when LEGACY_DIR does not exist."""
    fake_legacy = tmp_path / "nonexistent"  # never created
    with patch.object(migration_module, "LEGACY_DIR", fake_legacy):
        result = migrate_from_mempalace()
    assert result["status"] == "nothing_to_migrate"


def test_dry_run_creates_no_files(tmp_path):
    """A dry run with all legacy artefacts present must not create any new files."""
    legacy = tmp_path / "legacy"
    new = tmp_path / "new"
    legacy.mkdir()

    # Populate legacy dir with something for every step
    (legacy / "identity_profile.txt").write_text("I am Atlas.", encoding="utf-8")
    (legacy / "config.json").write_text(
        json.dumps({"palace_path": "/old/vault"}), encoding="utf-8"
    )

    with patch.multiple(
        migration_module,
        LEGACY_DIR=legacy,
        NEW_DIR=new,
        LEGACY_VAULT=legacy / "vault",       # no vault dir → Chroma step skips
        NEW_VAULT=new / "vault",
        LEGACY_GRAPH=legacy / "knowledge_graph.sqlite3",  # doesn't exist → graph step skips
        NEW_GRAPH=new / "recall_graph.sqlite3",
        LEGACY_IDENTITY=legacy / "identity_profile.txt",
        NEW_IDENTITY=new / "identity_profile.txt",
        LEGACY_CONFIG=legacy / "config.json",
        NEW_CONFIG=new / "config.json",
    ):
        result = migrate_from_mempalace(dry_run=True)

    assert result["dry_run"] is True
    # dry run must not create the new directory at all
    assert not new.exists(), "dry run must not create ~/.recallos"


def test_full_migration_creates_new_files(tmp_path):
    """A real migration copies identity + config when present."""
    legacy = tmp_path / "legacy"
    new = tmp_path / "new"
    legacy.mkdir()

    (legacy / "identity_profile.txt").write_text("I am Atlas.", encoding="utf-8")
    (legacy / "config.json").write_text(
        json.dumps({"palace_path": "/old/vault", "topic_wings": ["memory"]}),
        encoding="utf-8",
    )

    with patch.multiple(
        migration_module,
        LEGACY_DIR=legacy,
        NEW_DIR=new,
        LEGACY_VAULT=legacy / "vault",       # no vault dir → Chroma skips
        NEW_VAULT=new / "vault",
        LEGACY_GRAPH=legacy / "knowledge_graph.sqlite3",  # absent → graph skips
        NEW_GRAPH=new / "recall_graph.sqlite3",
        LEGACY_IDENTITY=legacy / "identity_profile.txt",
        NEW_IDENTITY=new / "identity_profile.txt",
        LEGACY_CONFIG=legacy / "config.json",
        NEW_CONFIG=new / "config.json",
    ):
        result = migrate_from_mempalace(dry_run=False)

    assert result["identity"] is True
    assert result["config"] is True
    assert (new / "identity_profile.txt").read_text(encoding="utf-8") == "I am Atlas."
    written = json.loads((new / "config.json").read_text(encoding="utf-8"))
    assert written["vault_path"] == "/old/vault"
    assert written["topic_domains"] == ["memory"]


# ---------------------------------------------------------------------------
# _migrate_graph
# ---------------------------------------------------------------------------


def test_graph_copies_sqlite(tmp_path):
    """_migrate_graph copies the SQLite file to the destination."""
    legacy_graph = tmp_path / "knowledge_graph.sqlite3"
    new_dir = tmp_path / "new"
    new_graph = new_dir / "recall_graph.sqlite3"
    _make_valid_sqlite(legacy_graph)

    with patch.multiple(
        migration_module,
        LEGACY_GRAPH=legacy_graph,
        NEW_GRAPH=new_graph,
        NEW_DIR=new_dir,
    ):
        result = _migrate_graph(dry_run=False, force=False)

    assert result is True
    assert new_graph.exists()
    assert new_graph.stat().st_size == legacy_graph.stat().st_size


def test_graph_skips_when_absent(tmp_path):
    """_migrate_graph returns False (skip) when source does not exist."""
    legacy_graph = tmp_path / "nonexistent.sqlite3"
    new_graph = tmp_path / "new" / "recall_graph.sqlite3"

    with patch.multiple(
        migration_module,
        LEGACY_GRAPH=legacy_graph,
        NEW_GRAPH=new_graph,
        NEW_DIR=tmp_path / "new",
    ):
        result = _migrate_graph(dry_run=False, force=False)

    assert result is False
    assert not new_graph.exists()


def test_graph_skips_existing_without_force(tmp_path):
    """_migrate_graph does not overwrite destination when force=False."""
    legacy_graph = tmp_path / "knowledge_graph.sqlite3"
    new_graph = tmp_path / "recall_graph.sqlite3"
    legacy_graph.write_bytes(b"new_data")
    new_graph.write_bytes(b"existing_data")

    with patch.multiple(
        migration_module,
        LEGACY_GRAPH=legacy_graph,
        NEW_GRAPH=new_graph,
        NEW_DIR=tmp_path,
    ):
        result = _migrate_graph(dry_run=False, force=False)

    assert result is False
    assert new_graph.read_bytes() == b"existing_data"  # untouched


def test_graph_force_overwrites(tmp_path):
    """_migrate_graph replaces destination when force=True."""
    legacy_graph = tmp_path / "knowledge_graph.sqlite3"
    new_graph = tmp_path / "recall_graph.sqlite3"
    legacy_graph.write_bytes(b"fresh_data")
    new_graph.write_bytes(b"stale_data")

    with patch.multiple(
        migration_module,
        LEGACY_GRAPH=legacy_graph,
        NEW_GRAPH=new_graph,
        NEW_DIR=tmp_path,
    ):
        result = _migrate_graph(dry_run=False, force=True)

    assert result is True
    assert new_graph.read_bytes() == b"fresh_data"


def test_graph_dry_run_no_copy(tmp_path):
    """_migrate_graph dry run returns True but does not copy anything."""
    legacy_graph = tmp_path / "knowledge_graph.sqlite3"
    new_graph = tmp_path / "new" / "recall_graph.sqlite3"
    _make_valid_sqlite(legacy_graph)

    with patch.multiple(
        migration_module,
        LEGACY_GRAPH=legacy_graph,
        NEW_GRAPH=new_graph,
        NEW_DIR=tmp_path / "new",
    ):
        result = _migrate_graph(dry_run=True, force=False)

    assert result is True
    assert not new_graph.exists()


# ---------------------------------------------------------------------------
# _migrate_identity
# ---------------------------------------------------------------------------


def test_identity_copies_file(tmp_path):
    """_migrate_identity copies identity_profile.txt to new location."""
    legacy_id = tmp_path / "identity_profile.txt"
    new_dir = tmp_path / "new"
    new_id = new_dir / "identity_profile.txt"
    legacy_id.write_text("I am Atlas.", encoding="utf-8")

    with patch.multiple(
        migration_module,
        LEGACY_IDENTITY=legacy_id,
        NEW_IDENTITY=new_id,
        NEW_DIR=new_dir,
    ):
        result = _migrate_identity(dry_run=False, force=False)

    assert result is True
    assert new_id.read_text(encoding="utf-8") == "I am Atlas."


def test_identity_skips_when_absent(tmp_path):
    """_migrate_identity returns False when source does not exist."""
    with patch.multiple(
        migration_module,
        LEGACY_IDENTITY=tmp_path / "nonexistent.txt",
        NEW_IDENTITY=tmp_path / "new" / "identity_profile.txt",
        NEW_DIR=tmp_path / "new",
    ):
        result = _migrate_identity(dry_run=False, force=False)

    assert result is False


def test_identity_skips_existing_without_force(tmp_path):
    """_migrate_identity does not overwrite when destination exists and force=False."""
    legacy_id = tmp_path / "legacy_id.txt"
    new_id = tmp_path / "new_id.txt"
    legacy_id.write_text("new content", encoding="utf-8")
    new_id.write_text("existing content", encoding="utf-8")

    with patch.multiple(
        migration_module,
        LEGACY_IDENTITY=legacy_id,
        NEW_IDENTITY=new_id,
        NEW_DIR=tmp_path,
    ):
        result = _migrate_identity(dry_run=False, force=False)

    assert result is False
    assert new_id.read_text(encoding="utf-8") == "existing content"


def test_identity_force_overwrites(tmp_path):
    """_migrate_identity overwrites destination when force=True."""
    legacy_id = tmp_path / "legacy_id.txt"
    new_id = tmp_path / "new_id.txt"
    legacy_id.write_text("updated identity", encoding="utf-8")
    new_id.write_text("old identity", encoding="utf-8")

    with patch.multiple(
        migration_module,
        LEGACY_IDENTITY=legacy_id,
        NEW_IDENTITY=new_id,
        NEW_DIR=tmp_path,
    ):
        result = _migrate_identity(dry_run=False, force=True)

    assert result is True
    assert new_id.read_text(encoding="utf-8") == "updated identity"


def test_identity_dry_run_no_copy(tmp_path):
    """_migrate_identity dry run returns True but does not copy."""
    legacy_id = tmp_path / "identity_profile.txt"
    new_id = tmp_path / "new" / "identity_profile.txt"
    legacy_id.write_text("dry content", encoding="utf-8")

    with patch.multiple(
        migration_module,
        LEGACY_IDENTITY=legacy_id,
        NEW_IDENTITY=new_id,
        NEW_DIR=tmp_path / "new",
    ):
        result = _migrate_identity(dry_run=True, force=False)

    assert result is True
    assert not new_id.exists()


# ---------------------------------------------------------------------------
# _migrate_config
# ---------------------------------------------------------------------------


def test_config_remaps_legacy_keys(tmp_path):
    """_migrate_config maps palace_path → vault_path, topic_wings → topic_domains, etc."""
    legacy_cfg = tmp_path / "legacy_config.json"
    new_cfg = tmp_path / "new_config.json"
    legacy_cfg.write_text(
        json.dumps({
            "palace_path": "/old/vault",
            "topic_wings": ["emotions", "memory"],
            "hall_keywords": {"emotions": ["sad"]},
        }),
        encoding="utf-8",
    )

    with patch.multiple(
        migration_module,
        LEGACY_CONFIG=legacy_cfg,
        NEW_CONFIG=new_cfg,
        NEW_DIR=tmp_path,
    ):
        result = _migrate_config(dry_run=False, force=False)

    assert result is True
    written = json.loads(new_cfg.read_text(encoding="utf-8"))
    assert written["vault_path"] == "/old/vault"
    assert written["topic_domains"] == ["emotions", "memory"]
    assert written["channel_keywords"] == {"emotions": ["sad"]}
    assert "palace_path" not in written
    assert "topic_wings" not in written


def test_config_preserves_existing_keys(tmp_path):
    """_migrate_config never overwrites keys already present in the RecallOS config."""
    legacy_cfg = tmp_path / "legacy_config.json"
    new_cfg = tmp_path / "new_config.json"
    legacy_cfg.write_text(json.dumps({"palace_path": "/old"}), encoding="utf-8")
    new_cfg.write_text(json.dumps({"vault_path": "/already/set"}), encoding="utf-8")

    with patch.multiple(
        migration_module,
        LEGACY_CONFIG=legacy_cfg,
        NEW_CONFIG=new_cfg,
        NEW_DIR=tmp_path,
    ):
        _migrate_config(dry_run=False, force=False)

    written = json.loads(new_cfg.read_text(encoding="utf-8"))
    assert written["vault_path"] == "/already/set"  # must not be overwritten


def test_config_skips_when_absent(tmp_path):
    """_migrate_config returns False when legacy config.json is missing."""
    with patch.multiple(
        migration_module,
        LEGACY_CONFIG=tmp_path / "nonexistent.json",
        NEW_CONFIG=tmp_path / "new_config.json",
        NEW_DIR=tmp_path,
    ):
        result = _migrate_config(dry_run=False, force=False)

    assert result is False


def test_config_dry_run_no_write(tmp_path):
    """_migrate_config dry run returns True but never writes the destination file."""
    legacy_cfg = tmp_path / "legacy_config.json"
    new_cfg = tmp_path / "new_config.json"
    legacy_cfg.write_text(json.dumps({"palace_path": "/old"}), encoding="utf-8")

    with patch.multiple(
        migration_module,
        LEGACY_CONFIG=legacy_cfg,
        NEW_CONFIG=new_cfg,
        NEW_DIR=tmp_path,
    ):
        result = _migrate_config(dry_run=True, force=False)

    assert result is True
    assert not new_cfg.exists()


def test_config_invalid_json_returns_false(tmp_path):
    """_migrate_config returns False gracefully when legacy config.json is malformed."""
    legacy_cfg = tmp_path / "legacy_config.json"
    new_cfg = tmp_path / "new_config.json"
    legacy_cfg.write_text("{ this is not valid json }", encoding="utf-8")

    with patch.multiple(
        migration_module,
        LEGACY_CONFIG=legacy_cfg,
        NEW_CONFIG=new_cfg,
        NEW_DIR=tmp_path,
    ):
        result = _migrate_config(dry_run=False, force=False)

    assert result is False
    assert not new_cfg.exists()
