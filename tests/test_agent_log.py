"""
test_agent_log.py — Unit tests for recallos/agent_log.py

Strategy: patch module-level LOG_ROOT with a temp directory so no files
are written to the real ~/.recallos/agent_logs during tests.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

import recallos.agent_log as agent_log_module
from recallos.agent_log import AgentLog


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def log(tmp_path):
    """Return an AgentLog pointing at a temp directory."""
    with patch.object(agent_log_module, "LOG_ROOT", tmp_path):
        yield AgentLog("tester")


# ---------------------------------------------------------------------------
# write
# ---------------------------------------------------------------------------


def test_write_creates_jsonl_file(log, tmp_path):
    log.write("something happened")
    files = list((tmp_path / "tester").glob("*.jsonl"))
    assert len(files) == 1


def test_write_returns_metadata(log):
    result = log.write("test entry", topic="code")
    assert "entry_id" in result
    assert "timestamp" in result
    assert "file" in result
    assert result["entry_id"].startswith("log_tester_")


def test_write_appends_valid_json_lines(log, tmp_path):
    log.write("first")
    log.write("second")
    lines = (tmp_path / "tester" / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl") \
        .read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    for line in lines:
        entry = json.loads(line)
        assert "content" in entry
        assert "timestamp" in entry
        assert "topic" in entry


def test_write_stores_topic(log, tmp_path):
    log.write("PR reviewed", topic="code-review")
    today = datetime.now().strftime("%Y-%m-%d")
    line = (tmp_path / "tester" / f"{today}.jsonl").read_text(encoding="utf-8").strip()
    entry = json.loads(line)
    assert entry["topic"] == "code-review"


def test_write_stores_agent_name(log, tmp_path):
    log.write("hello")
    today = datetime.now().strftime("%Y-%m-%d")
    line = (tmp_path / "tester" / f"{today}.jsonl").read_text(encoding="utf-8").strip()
    entry = json.loads(line)
    assert entry["agent"] == "tester"


def test_write_unique_ids_per_entry(log):
    r1 = log.write("first entry")
    r2 = log.write("second entry")
    assert r1["entry_id"] != r2["entry_id"]


# ---------------------------------------------------------------------------
# read
# ---------------------------------------------------------------------------


def test_read_returns_entries(log):
    log.write("entry one")
    log.write("entry two")
    entries = log.read()
    assert len(entries) == 2


def test_read_newest_first(log):
    log.write("older")
    log.write("newer")
    entries = log.read()
    # Most recently written should appear first
    assert entries[0]["content"] == "newer"
    assert entries[1]["content"] == "older"


def test_read_respects_last_n(log):
    for i in range(5):
        log.write(f"entry {i}")
    entries = log.read(last_n=2)
    assert len(entries) == 2


def test_read_empty_log_returns_empty_list(log):
    entries = log.read()
    assert entries == []


def test_read_across_multiple_files(tmp_path):
    """read() collects entries across multiple day files (newest day first)."""
    with patch.object(agent_log_module, "LOG_ROOT", tmp_path):
        log_dir = tmp_path / "tester"
        log_dir.mkdir(parents=True)

        # Write to two different day files manually
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")

        (log_dir / f"{yesterday}.jsonl").write_text(
            json.dumps({"content": "old entry", "timestamp": f"{yesterday}T10:00:00",
                        "topic": "g", "agent": "tester", "date": yesterday,
                        "id": "old_id"}) + "\n",
            encoding="utf-8",
        )
        (log_dir / f"{today}.jsonl").write_text(
            json.dumps({"content": "new entry", "timestamp": f"{today}T10:00:00",
                        "topic": "g", "agent": "tester", "date": today,
                        "id": "new_id"}) + "\n",
            encoding="utf-8",
        )

        log = AgentLog("tester")
        entries = log.read(last_n=10)

    assert len(entries) == 2
    assert entries[0]["content"] == "new entry"  # newest day first
    assert entries[1]["content"] == "old entry"


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


def test_search_returns_matching_entries(log):
    log.write("auth migration completed")
    log.write("billing refactor started")
    log.write("auth token expiry bug fixed")

    matches = log.search("auth")
    contents = [m["content"] for m in matches]
    assert "auth migration completed" in contents
    assert "auth token expiry bug fixed" in contents
    assert "billing refactor started" not in contents


def test_search_case_insensitive(log):
    log.write("AUTH migration done")
    matches = log.search("auth")
    assert len(matches) == 1


def test_search_no_matches_returns_empty(log):
    log.write("billing refactor")
    matches = log.search("nonexistent-keyword-xyz")
    assert matches == []


def test_search_respects_max_results(log):
    for i in range(10):
        log.write(f"auth event {i}")
    matches = log.search("auth", max_results=3)
    assert len(matches) <= 3


def test_search_empty_log_returns_empty(log):
    matches = log.search("anything")
    assert matches == []


# ---------------------------------------------------------------------------
# rotate
# ---------------------------------------------------------------------------


def test_rotate_deletes_old_files(tmp_path):
    with patch.object(agent_log_module, "LOG_ROOT", tmp_path):
        log_dir = tmp_path / "tester"
        log_dir.mkdir(parents=True)

        # Write a file dated 60 days ago
        old_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        today_date = datetime.now().strftime("%Y-%m-%d")
        (log_dir / f"{old_date}.jsonl").write_text('{"content":"old"}\n')
        (log_dir / f"{today_date}.jsonl").write_text('{"content":"today"}\n')

        log = AgentLog("tester")
        result = log.rotate(keep_days=30)

    assert result["deleted"] == 1
    assert result["kept"] == 1
    assert old_date + ".jsonl" in result["deleted_files"]


def test_rotate_keeps_recent_files(tmp_path):
    with patch.object(agent_log_module, "LOG_ROOT", tmp_path):
        log_dir = tmp_path / "tester"
        log_dir.mkdir(parents=True)

        today_date = datetime.now().strftime("%Y-%m-%d")
        (log_dir / f"{today_date}.jsonl").write_text('{"content":"today"}\n')

        log = AgentLog("tester")
        result = log.rotate(keep_days=30)

    assert result["deleted"] == 0
    assert result["kept"] == 1


def test_rotate_keeps_unparseable_filenames(tmp_path):
    """Files with non-date names are never deleted."""
    with patch.object(agent_log_module, "LOG_ROOT", tmp_path):
        log_dir = tmp_path / "tester"
        log_dir.mkdir(parents=True)
        (log_dir / "notes.jsonl").write_text('{"content":"misc"}\n')

        log = AgentLog("tester")
        result = log.rotate(keep_days=1)

    assert result["deleted"] == 0
    assert (log_dir / "notes.jsonl").exists()


def test_rotate_returns_cutoff_date(log):
    result = log.rotate(keep_days=7)
    cutoff = datetime.now() - timedelta(days=7)
    assert result["cutoff_date"] == cutoff.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------


def test_stats_empty_log(log):
    s = log.stats()
    assert s["agent"] == "tester"
    assert s["log_files"] == 0
    assert s["total_entries"] == 0
    assert s["oldest"] is None
    assert s["newest"] is None


def test_stats_counts_entries(log):
    log.write("first")
    log.write("second")
    log.write("third")
    s = log.stats()
    assert s["total_entries"] == 3
    assert s["log_files"] == 1


def test_stats_oldest_newest(tmp_path):
    with patch.object(agent_log_module, "LOG_ROOT", tmp_path):
        log_dir = tmp_path / "tester"
        log_dir.mkdir(parents=True)
        (log_dir / "2026-01-01.jsonl").write_text('{"content":"old"}\n')
        (log_dir / "2026-03-15.jsonl").write_text('{"content":"new"}\n')

        log = AgentLog("tester")
        s = log.stats()

    assert s["newest"] == "2026-03-15"
    assert s["oldest"] == "2026-01-01"
