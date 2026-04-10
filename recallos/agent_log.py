#!/usr/bin/env python3
"""
agent_log.py — File-backed Agent Log for RecallOS
===================================================

Each agent gets a directory of per-day JSONL log files:
    ~/.recallos/agent_logs/<agent_name>/YYYY-MM-DD.jsonl

Features:
  - write()  — append an entry (also writes to ChromaDB for semantic search)
  - read()   — read last N entries from files (most recent first)
  - search() — grep across log files for a keyword
  - rotate() — delete log files older than keep_days

Log entries are plain JSONL:
    {"timestamp": "...", "topic": "...", "content": "..."}
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path


LOG_ROOT = Path(os.path.expanduser("~/.recallos/agent_logs"))


class AgentLog:
    """File-backed log for a named agent.

    Writes entries to ~/.recallos/agent_logs/<agent>/YYYY-MM-DD.jsonl
    and also stores them in ChromaDB for semantic search via the vault.
    """

    def __init__(self, agent_name: str, vault_path: str = None):
        self.agent_name = agent_name
        self._agent_slug = agent_name.lower().replace(" ", "_")
        self._log_dir = LOG_ROOT / self._agent_slug
        self._vault_path = vault_path  # optional ChromaDB vault path
        self._log_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _today_file(self) -> Path:
        return self._log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"

    def _all_log_files(self, newest_first: bool = True) -> list:
        """Return all .jsonl files sorted by date."""
        files = sorted(self._log_dir.glob("*.jsonl"), reverse=newest_first)
        return files

    def _entry_id(self, timestamp: str, content: str) -> str:
        import hashlib

        return f"log_{self._agent_slug}_{timestamp[:10].replace('-', '')}_{hashlib.md5((timestamp + content[:30]).encode()).hexdigest()[:8]}"

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def write(self, content: str, topic: str = "general") -> dict:
        """Append a log entry to today's JSONL file and optionally ChromaDB.

        Returns entry metadata dict.
        """
        now = datetime.now()
        entry = {
            "timestamp": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "topic": topic,
            "agent": self.agent_name,
            "content": content,
        }
        entry_id = self._entry_id(entry["timestamp"], content)
        entry["id"] = entry_id

        # Append to JSONL file
        with open(self._today_file(), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        # Also write to ChromaDB if vault is configured
        if self._vault_path:
            self._write_to_chroma(entry_id, content, entry)

        return {
            "entry_id": entry_id,
            "timestamp": entry["timestamp"],
            "file": str(self._today_file()),
        }

    def _write_to_chroma(self, entry_id: str, content: str, meta: dict):
        """Best-effort ChromaDB write — silently skips if vault not available."""
        try:
            import chromadb

            client = chromadb.PersistentClient(path=self._vault_path)
            col = client.get_or_create_collection("recallos_records")
            domain = f"domain_{self._agent_slug}"
            col.upsert(
                ids=[entry_id],
                documents=[content],
                metadatas=[
                    {
                        "domain": domain,
                        "node": "agent_log",
                        "channel": "channel_facts",
                        "topic": meta.get("topic", "general"),
                        "type": "agent_log_entry",
                        "agent": self.agent_name,
                        "filed_at": meta.get("timestamp", ""),
                        "date": meta.get("date", ""),
                    }
                ],
            )
        except Exception:
            pass  # Non-fatal — file log is the primary store

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read(self, last_n: int = 10) -> list:
        """Read the most recent N entries across all log files.

        Returns list of entry dicts, newest first.
        """
        entries = []
        for log_file in self._all_log_files(newest_first=True):
            if len(entries) >= last_n:
                break
            try:
                lines = log_file.read_text(encoding="utf-8", errors="replace").strip().splitlines()
                for line in reversed(lines):
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                        if len(entries) >= last_n:
                            break
                    except json.JSONDecodeError:
                        continue
            except OSError:
                continue

        return entries

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, keyword: str, max_results: int = 20) -> list:
        """Case-insensitive keyword search across all log files.

        Returns matching entries sorted newest first.
        """
        keyword_lower = keyword.lower()
        matches = []

        for log_file in self._all_log_files(newest_first=True):
            if len(matches) >= max_results:
                break
            try:
                lines = log_file.read_text(encoding="utf-8", errors="replace").strip().splitlines()
                for line in reversed(lines):
                    if not line.strip():
                        continue
                    if keyword_lower not in line.lower():
                        continue
                    try:
                        entry = json.loads(line)
                        matches.append(entry)
                        if len(matches) >= max_results:
                            break
                    except json.JSONDecodeError:
                        continue
            except OSError:
                continue

        return matches

    # ------------------------------------------------------------------
    # Rotate
    # ------------------------------------------------------------------

    def rotate(self, keep_days: int = 30) -> dict:
        """Delete log files older than keep_days.

        Returns dict with count of files deleted and kept.
        """
        cutoff = datetime.now() - timedelta(days=keep_days)
        deleted = []
        kept = []

        for log_file in self._all_log_files():
            try:
                date_str = log_file.stem  # "YYYY-MM-DD"
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date < cutoff:
                    log_file.unlink()
                    deleted.append(log_file.name)
                else:
                    kept.append(log_file.name)
            except (ValueError, OSError):
                kept.append(log_file.name)  # Can't parse date — keep it

        return {
            "deleted": len(deleted),
            "kept": len(kept),
            "cutoff_date": cutoff.strftime("%Y-%m-%d"),
            "deleted_files": deleted,
        }

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """Return summary stats for this agent's log."""
        files = self._all_log_files()
        total_entries = 0
        for log_file in files:
            try:
                lines = log_file.read_text(encoding="utf-8", errors="replace").strip().splitlines()
                total_entries += sum(1 for line in lines if line.strip())
            except OSError:
                pass
        return {
            "agent": self.agent_name,
            "log_dir": str(self._log_dir),
            "log_files": len(files),
            "total_entries": total_entries,
            "oldest": files[-1].stem if files else None,
            "newest": files[0].stem if files else None,
        }
