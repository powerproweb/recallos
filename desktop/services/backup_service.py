"""
desktop/services/backup_service.py — Backup and restore for RecallOS Desktop.

Backup creates a ZIP of the vault directory, desktop.db, and config.
Restore verifies the ZIP and extracts to the original locations.
"""

from __future__ import annotations

import logging
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from recallos.config import RecallOSConfig
from desktop.db import DB_PATH

logger = logging.getLogger("backup")

BACKUP_DIR = Path(os.path.expanduser("~/.recallos/backups"))


def backup(dest_dir: str | None = None) -> dict:
    """Create a ZIP backup of vault + desktop DB + config.

    Returns dict with path, size, and contents summary.
    """
    config = RecallOSConfig()
    vault_path = Path(config.vault_path)
    dest = Path(dest_dir) if dest_dir else BACKUP_DIR
    dest.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = dest / f"recallos-backup-{ts}.zip"

    files_added = 0
    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
        # Vault
        if vault_path.is_dir():
            for root, dirs, files in os.walk(vault_path):
                for fname in files:
                    fpath = Path(root) / fname
                    arcname = f"vault/{fpath.relative_to(vault_path)}"
                    zf.write(str(fpath), arcname)
                    files_added += 1

        # Desktop DB
        if DB_PATH.exists():
            zf.write(str(DB_PATH), "desktop.db")
            files_added += 1

        # Config
        config_path = Path(os.path.expanduser("~/.recallos/config.json"))
        if config_path.exists():
            zf.write(str(config_path), "config.json")
            files_added += 1

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    logger.info("Backup created: %s (%.1f MB, %d files)", zip_path, size_mb, files_added)

    return {
        "path": str(zip_path),
        "size_mb": round(size_mb, 1),
        "files": files_added,
        "timestamp": ts,
    }


def restore(zip_path: str) -> dict:
    """Restore from a backup ZIP.  Returns summary."""
    zp = Path(zip_path)
    if not zp.is_file():
        return {"status": "error", "message": f"File not found: {zip_path}"}

    if not zipfile.is_zipfile(str(zp)):
        return {"status": "error", "message": "Not a valid ZIP file"}

    config = RecallOSConfig()
    vault_path = Path(config.vault_path)

    with zipfile.ZipFile(str(zp), "r") as zf:
        names = zf.namelist()

        # Restore vault
        vault_files = [n for n in names if n.startswith("vault/")]
        for name in vault_files:
            target = vault_path / name.removeprefix("vault/")
            target.parent.mkdir(parents=True, exist_ok=True)
            if not name.endswith("/"):
                with zf.open(name) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)

        # Restore desktop DB
        if "desktop.db" in names:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            with zf.open("desktop.db") as src, open(DB_PATH, "wb") as dst:
                shutil.copyfileobj(src, dst)

        # Restore config
        if "config.json" in names:
            config_path = Path(os.path.expanduser("~/.recallos/config.json"))
            with zf.open("config.json") as src, open(config_path, "wb") as dst:
                shutil.copyfileobj(src, dst)

    logger.info("Restored from %s (%d entries)", zp, len(names))
    return {"status": "ok", "restored_files": len(names), "source": str(zp)}


def list_backups() -> list[dict]:
    """List available backups in the default backup directory."""
    if not BACKUP_DIR.is_dir():
        return []
    backups = []
    for f in sorted(BACKUP_DIR.glob("recallos-backup-*.zip"), reverse=True):
        backups.append(
            {
                "path": str(f),
                "name": f.name,
                "size_mb": round(f.stat().st_size / (1024 * 1024), 1),
            }
        )
    return backups
