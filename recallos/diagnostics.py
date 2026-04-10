#!/usr/bin/env python3
"""
diagnostics.py — Vault health checks for RecallOS
===================================================

Run with:
    recallos doctor
    recallos doctor --verbose

Checks performed:
  1. Vault directory exists and is reachable
  2. recallos_records ChromaDB collection is accessible
  3. Records with missing domain or node metadata (incomplete records)
  4. recall_graph.sqlite3 PRAGMA integrity_check
  5. identity_profile.txt exists
  6. Legacy ~/.mempalace/ directory detected (migration reminder)
"""

import json
import os
import sqlite3
from pathlib import Path

from .config import RecallOSConfig

# Result constants
PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
INFO = "INFO"

_ICONS = {PASS: "✔", WARN: "⚠", FAIL: "✗", INFO: "·"}


def _result(status: str, label: str, detail: str = "") -> dict:
    return {"status": status, "label": label, "detail": detail}


def _print_result(r: dict, verbose: bool = False):
    icon = _ICONS.get(r["status"], " ")
    line = f"  {icon}  [{r['status']:4}]  {r['label']}"
    if r["detail"] and (verbose or r["status"] in (WARN, FAIL)):
        line += f"\n           {r['detail']}"
    print(line)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def _check_vault_dir(vault_path: str) -> dict:
    p = Path(vault_path)
    if not p.exists():
        return _result(WARN, "Vault directory", f"Not found: {vault_path}  (run: recallos init <dir>)")
    if not p.is_dir():
        return _result(FAIL, "Vault directory", f"{vault_path} exists but is not a directory")
    return _result(PASS, "Vault directory", str(vault_path))


def _check_chroma_collection(vault_path: str, verbose: bool) -> tuple:
    """Returns (result_dict, collection_or_None)."""
    try:
        import chromadb

        client = chromadb.PersistentClient(path=vault_path)
        col = client.get_collection("recallos_records")
        count = col.count()
        detail = f"{count:,} records" if verbose else ""
        return _result(PASS, "ChromaDB collection", detail), col
    except Exception as e:
        return _result(FAIL, "ChromaDB collection", str(e)), None


def _check_incomplete_records(col, verbose: bool) -> dict:
    """Scan for records missing domain or node metadata."""
    if col is None:
        return _result(INFO, "Incomplete records", "skipped — collection unavailable")
    try:
        results = col.get(include=["metadatas"])
        metas = results.get("metadatas", [])
        ids = results.get("ids", [])
        missing = [
            ids[i]
            for i, m in enumerate(metas)
            if not m.get("domain") or not m.get("node")
        ]
        if not missing:
            detail = f"{len(metas):,} records checked" if verbose else ""
            return _result(PASS, "Incomplete records", detail)
        sample = ", ".join(missing[:3])
        extra = f" (+{len(missing)-3} more)" if len(missing) > 3 else ""
        return _result(
            WARN,
            "Incomplete records",
            f"{len(missing)} records missing domain/node: {sample}{extra}",
        )
    except Exception as e:
        return _result(WARN, "Incomplete records", f"Could not scan: {e}")


def _check_recall_graph() -> dict:
    """Run SQLite PRAGMA integrity_check on recall_graph.sqlite3."""
    graph_path = Path(os.path.expanduser("~/.recallos/recall_graph.sqlite3"))
    if not graph_path.exists():
        return _result(INFO, "Recall graph SQLite", "Not found — graph is empty (no triples added yet)")
    try:
        conn = sqlite3.connect(str(graph_path), timeout=5)
        rows = conn.execute("PRAGMA integrity_check").fetchall()
        conn.close()
        if rows and rows[0][0] == "ok":
            # Count entities and triples
            conn2 = sqlite3.connect(str(graph_path), timeout=5)
            entities = conn2.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            triples = conn2.execute("SELECT COUNT(*) FROM triples").fetchone()[0]
            conn2.close()
            return _result(PASS, "Recall graph SQLite", f"{entities} entities, {triples} triples")
        else:
            issues = "; ".join(r[0] for r in rows[:3])
            return _result(FAIL, "Recall graph SQLite", f"Integrity issues: {issues}")
    except Exception as e:
        return _result(FAIL, "Recall graph SQLite", str(e))


def _check_identity_profile() -> dict:
    p = Path(os.path.expanduser("~/.recallos/identity_profile.txt"))
    if p.exists():
        lines = p.read_text(encoding="utf-8", errors="replace").strip().count("\n") + 1
        return _result(PASS, "Identity profile", f"{lines} lines at {p}")
    return _result(
        WARN,
        "Identity profile",
        f"Not found at {p} — create it to enable L0 bootstrap",
    )


def _check_legacy_dir(cfg: RecallOSConfig) -> dict:
    warn = cfg.legacy_warning
    if warn:
        return _result(
            WARN,
            "Legacy MemPalace",
            f"Found at {cfg.legacy_dir} — run: recallos migrate",
        )
    return _result(PASS, "Legacy MemPalace", "No legacy ~/.mempalace directory detected")


def _check_config_file() -> dict:
    config_path = Path(os.path.expanduser("~/.recallos/config.json"))
    if not config_path.exists():
        return _result(
            INFO,
            "Config file",
            "~/.recallos/config.json not found — using defaults (run: recallos init <dir>)",
        )
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        keys = ", ".join(sorted(data.keys()))
        return _result(PASS, "Config file", keys)
    except Exception as e:
        return _result(FAIL, "Config file", f"Cannot parse config.json: {e}")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_doctor(vault_path: str = None, verbose: bool = False) -> dict:
    """
    Run all vault health checks and print a report.

    Args:
        vault_path: Override vault path (default: from config).
        verbose:    Print detail for passing checks too.

    Returns:
        Dict with check results and overall status.
    """
    cfg = RecallOSConfig()
    vault_path = vault_path or cfg.vault_path

    print()
    print("=" * 55)
    print("  RecallOS Doctor — Vault Health Report")
    print(f"  Vault: {vault_path}")
    print("=" * 55)
    print()

    checks = []

    # Run all checks
    checks.append(_check_vault_dir(vault_path))
    col_result, col = _check_chroma_collection(vault_path, verbose)
    checks.append(col_result)
    checks.append(_check_incomplete_records(col, verbose))
    checks.append(_check_recall_graph())
    checks.append(_check_identity_profile())
    checks.append(_check_config_file())
    checks.append(_check_legacy_dir(cfg))

    for r in checks:
        _print_result(r, verbose)

    # Summary
    counts = {PASS: 0, WARN: 0, FAIL: 0, INFO: 0}
    for r in checks:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    overall = PASS
    if counts[FAIL] > 0:
        overall = FAIL
    elif counts[WARN] > 0:
        overall = WARN

    print()
    print("─" * 55)
    print(
        f"  {counts[PASS]} passed · {counts[WARN]} warnings · "
        f"{counts[FAIL]} failures · {counts[INFO]} info"
    )
    if overall == PASS:
        print("  ✔  Vault looks healthy.")
    elif overall == WARN:
        print("  ⚠  Vault has warnings — review items above.")
    else:
        print("  ✗  Vault has failures — action required.")
    print("=" * 55)
    print()

    return {
        "vault_path": vault_path,
        "overall": overall,
        "checks": checks,
        "counts": counts,
    }
