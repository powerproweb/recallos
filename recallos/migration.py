#!/usr/bin/env python3
"""
migration.py — Migrate MemPalace data to RecallOS
==================================================

Moves everything from ~/.mempalace/ → ~/.recallos/:
  - ChromaDB records: mempalace_drawers → recallos_records
  - Knowledge graph SQLite: knowledge_graph.sqlite3 → recall_graph.sqlite3
  - Identity profile: identity_profile.txt (if not already present)
  - Config: vault_path and collection_name fields mapped to new names

Usage:
    recallos migrate             Run full migration
    recallos migrate --dry-run   Preview what would be moved
    recallos migrate --force     Overwrite existing RecallOS data
"""

import json
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

import chromadb


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LEGACY_DIR = Path(os.path.expanduser("~/.mempalace"))
NEW_DIR = Path(os.path.expanduser("~/.recallos"))

LEGACY_VAULT = LEGACY_DIR / "vault"
NEW_VAULT = NEW_DIR / "vault"

LEGACY_GRAPH = LEGACY_DIR / "knowledge_graph.sqlite3"
NEW_GRAPH = NEW_DIR / "recall_graph.sqlite3"

LEGACY_IDENTITY = LEGACY_DIR / "identity_profile.txt"
NEW_IDENTITY = NEW_DIR / "identity_profile.txt"

LEGACY_CONFIG = LEGACY_DIR / "config.json"
NEW_CONFIG = NEW_DIR / "config.json"

# Old collection name → new collection name
COLLECTION_MAP = {
    "mempalace_drawers": "recallos_records",
    "mempalace_encoded": "recallos_encoded",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _print_step(label: str, status: str, detail: str = ""):
    status_icons = {"ok": "✔", "skip": "–", "warn": "⚠", "dry": "○", "fail": "✗"}
    icon = status_icons.get(status, " ")
    line = f"  {icon}  {label}"
    if detail:
        line += f"  ({detail})"
    print(line)


def _record_count(collection) -> int:
    try:
        return collection.count()
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Step functions
# ---------------------------------------------------------------------------


def _migrate_chroma(dry_run: bool, force: bool) -> dict:
    """Copy ChromaDB records from legacy vault to new vault.

    Returns dict with per-collection migration counts.
    """
    results = {}

    if not LEGACY_VAULT.exists():
        _print_step("ChromaDB vault", "skip", "~/.mempalace/vault not found")
        return results

    try:
        src_client = chromadb.PersistentClient(path=str(LEGACY_VAULT))
    except Exception as e:
        _print_step("ChromaDB vault", "fail", f"Cannot open source vault: {e}")
        return results

    src_collections = src_client.list_collections()
    if not src_collections:
        _print_step("ChromaDB vault", "skip", "no collections in legacy vault")
        return results

    if dry_run:
        for col_meta in src_collections:
            col = src_client.get_collection(col_meta.name)
            count = _record_count(col)
            mapped = COLLECTION_MAP.get(col_meta.name, col_meta.name)
            _print_step(
                f"ChromaDB '{col_meta.name}' → '{mapped}'",
                "dry",
                f"{count} records would be copied",
            )
            results[col_meta.name] = count
        return results

    NEW_VAULT.mkdir(parents=True, exist_ok=True)
    dst_client = chromadb.PersistentClient(path=str(NEW_VAULT))

    for col_meta in src_collections:
        src_col = src_client.get_collection(col_meta.name)
        dst_name = COLLECTION_MAP.get(col_meta.name, col_meta.name)

        # Check existing destination collection
        existing_count = 0
        try:
            dst_col = dst_client.get_collection(dst_name)
            existing_count = _record_count(dst_col)
            if existing_count > 0 and not force:
                _print_step(
                    f"ChromaDB '{col_meta.name}' → '{dst_name}'",
                    "skip",
                    f"destination already has {existing_count} records (use --force to overwrite)",
                )
                results[col_meta.name] = 0
                continue
        except Exception:
            dst_col = dst_client.create_collection(dst_name)

        # Read all records from source in batches
        total = src_col.count()
        if total == 0:
            _print_step(f"ChromaDB '{col_meta.name}' → '{dst_name}'", "skip", "empty collection")
            results[col_meta.name] = 0
            continue

        copied = 0
        offset = 0
        BATCH = 500

        while offset < total:
            batch = src_col.get(
                limit=BATCH,
                offset=offset,
                include=["documents", "metadatas", "embeddings"],
            )
            ids = batch.get("ids", [])
            docs = batch.get("documents", [])
            metas = batch.get("metadatas", [])
            embeddings = batch.get("embeddings", [])

            if not ids:
                break

            try:
                if embeddings:
                    dst_col.upsert(
                        ids=ids,
                        documents=docs,
                        metadatas=metas,
                        embeddings=embeddings,
                    )
                else:
                    dst_col.upsert(ids=ids, documents=docs, metadatas=metas)
                copied += len(ids)
            except Exception as e:
                _print_step(
                    f"ChromaDB '{col_meta.name}' batch @{offset}",
                    "warn",
                    f"partial error: {e}",
                )

            offset += len(ids)
            if len(ids) < BATCH:
                break

        _print_step(
            f"ChromaDB '{col_meta.name}' → '{dst_name}'",
            "ok",
            f"{copied}/{total} records copied",
        )
        results[col_meta.name] = copied

    return results


def _migrate_graph(dry_run: bool, force: bool) -> bool:
    """Copy knowledge_graph.sqlite3 → recall_graph.sqlite3."""
    if not LEGACY_GRAPH.exists():
        _print_step("Knowledge graph SQLite", "skip", "not found in legacy dir")
        return False

    if NEW_GRAPH.exists() and not force:
        _print_step(
            "Knowledge graph SQLite",
            "skip",
            "recall_graph.sqlite3 already exists (use --force to overwrite)",
        )
        return False

    if dry_run:
        size_kb = LEGACY_GRAPH.stat().st_size // 1024
        _print_step("Knowledge graph SQLite", "dry", f"{size_kb} KB would be copied")
        return True

    NEW_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(LEGACY_GRAPH), str(NEW_GRAPH))
    size_kb = NEW_GRAPH.stat().st_size // 1024
    _print_step("Knowledge graph SQLite", "ok", f"{size_kb} KB copied")
    return True


def _migrate_identity(dry_run: bool, force: bool) -> bool:
    """Copy identity_profile.txt if not already present."""
    if not LEGACY_IDENTITY.exists():
        _print_step("Identity profile", "skip", "not found in legacy dir")
        return False

    if NEW_IDENTITY.exists() and not force:
        _print_step(
            "Identity profile",
            "skip",
            "already exists at ~/.recallos/identity_profile.txt",
        )
        return False

    if dry_run:
        lines = LEGACY_IDENTITY.read_text(encoding="utf-8", errors="replace").count("\n") + 1
        _print_step("Identity profile", "dry", f"{lines} lines would be copied")
        return True

    NEW_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(LEGACY_IDENTITY), str(NEW_IDENTITY))
    _print_step("Identity profile", "ok", "copied to ~/.recallos/identity_profile.txt")
    return True


def _migrate_config(dry_run: bool, force: bool) -> bool:
    """Map legacy config fields into RecallOS config.json."""
    if not LEGACY_CONFIG.exists():
        _print_step("Config", "skip", "no ~/.mempalace/config.json found")
        return False

    try:
        legacy = json.loads(LEGACY_CONFIG.read_text(encoding="utf-8"))
    except Exception:
        _print_step("Config", "warn", "could not parse legacy config.json")
        return False

    if dry_run:
        _print_step("Config", "dry", "would map legacy fields to RecallOS config")
        return True

    NEW_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing RecallOS config if present
    existing = {}
    if NEW_CONFIG.exists():
        try:
            existing = json.loads(NEW_CONFIG.read_text(encoding="utf-8"))
        except Exception:
            existing = {}

    # Map old keys → new keys (only fill in missing values)
    key_map = {
        "palace_path": "vault_path",
        "topic_wings": "topic_domains",
        "hall_keywords": "channel_keywords",
        "collection_name": "collection_name",
        "people_map": "people_map",
    }
    updated = 0
    for old_key, new_key in key_map.items():
        if old_key in legacy and new_key not in existing:
            existing[new_key] = legacy[old_key]
            updated += 1

    NEW_CONFIG.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    _print_step("Config", "ok", f"{updated} fields merged into ~/.recallos/config.json")
    return True


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def migrate_from_mempalace(dry_run: bool = False, force: bool = False) -> dict:
    """
    Migrate data from ~/.mempalace/ to ~/.recallos/.

    Args:
        dry_run: If True, print what would happen but make no changes.
        force:   If True, overwrite existing RecallOS data.

    Returns:
        Summary dict with migration results.
    """
    print()
    print("=" * 55)
    print("  RecallOS Migration")
    print(f"  Source: {LEGACY_DIR}")
    print(f"  Target: {NEW_DIR}")
    if dry_run:
        print("  DRY RUN — no changes will be made")
    print("=" * 55)
    print()

    if not LEGACY_DIR.exists():
        print(f"  No legacy MemPalace installation found at {LEGACY_DIR}")
        print("  Nothing to migrate.")
        print()
        return {"status": "nothing_to_migrate"}

    summary = {
        "dry_run": dry_run,
        "started_at": datetime.now().isoformat(),
        "chroma": {},
        "graph": False,
        "identity": False,
        "config": False,
    }

    summary["chroma"] = _migrate_chroma(dry_run, force)
    summary["graph"] = _migrate_graph(dry_run, force)
    summary["identity"] = _migrate_identity(dry_run, force)
    summary["config"] = _migrate_config(dry_run, force)

    print()
    print("─" * 55)
    total_records = sum(summary["chroma"].values())
    if dry_run:
        print(f"  Would migrate ~{total_records} records.")
        print("  Run without --dry-run to apply changes.")
    else:
        print(f"  Migration complete. {total_records} records moved.")
        print()
        print("  Next steps:")
        print("    recallos status       — verify your vault")
        print("    recallos doctor       — run health checks")
    print("=" * 55)
    print()

    return summary
