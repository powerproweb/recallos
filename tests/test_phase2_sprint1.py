"""
test_phase2_sprint1.py — Tests for Phase 2 Sprint 1: logging, crash, backups.
"""

import json
import logging
import zipfile
from pathlib import Path

from desktop.crash import (
    check_unclean_shutdown,
    clear_running,
    mark_running,
    write_crash_dump,
)
from desktop.services.backup_service import backup, list_backups, restore
from desktop.services.logging_service import JSONFormatter, init_logging, log_frontend_error


# ---------------------------------------------------------------------------
# 2.1 Structured logging
# ---------------------------------------------------------------------------


def test_json_formatter_produces_valid_json():
    fmt = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    line = fmt.format(record)
    obj = json.loads(line)
    assert obj["level"] == "INFO"
    assert obj["message"] == "hello world"
    assert "ts" in obj


def test_json_formatter_includes_exception():
    fmt = JSONFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="fail",
            args=(),
            exc_info=sys.exc_info(),
        )
    line = fmt.format(record)
    obj = json.loads(line)
    assert "exception" in obj
    assert "boom" in obj["exception"]


def test_init_logging_creates_handlers():
    init_logging()
    root = logging.getLogger()
    # Should have at least a file handler + console handler
    assert len(root.handlers) >= 2


def test_log_frontend_error_does_not_raise():
    log_frontend_error("TestComponent", "something broke", "stack trace here")


# ---------------------------------------------------------------------------
# 2.2 Crash reporting
# ---------------------------------------------------------------------------


def test_crash_dump_writes_json(tmp_path, monkeypatch):
    monkeypatch.setattr("desktop.crash.LOG_DIR", tmp_path)
    try:
        raise RuntimeError("test crash")
    except RuntimeError as exc:
        path = write_crash_dump(exc)

    assert path is not None
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["exception_type"] == "RuntimeError"
    assert "test crash" in data["message"]
    assert "traceback" in data


def test_mark_and_clear_running(tmp_path, monkeypatch):
    lock = tmp_path / ".running"
    monkeypatch.setattr("desktop.crash.LOCK_FILE", lock)
    monkeypatch.setattr("desktop.crash.LOG_DIR", tmp_path)

    assert not check_unclean_shutdown()
    mark_running()
    assert lock.exists()

    monkeypatch.setattr("desktop.crash.LOCK_FILE", lock)
    assert check_unclean_shutdown()

    clear_running()
    assert not lock.exists()


# ---------------------------------------------------------------------------
# 1.7 Backups
# ---------------------------------------------------------------------------


def test_backup_creates_zip(tmp_path):
    result = backup(dest_dir=str(tmp_path))
    assert "path" in result
    assert result["files"] >= 0
    zip_path = Path(result["path"])
    assert zip_path.exists()
    assert zipfile.is_zipfile(str(zip_path))


def test_restore_rejects_nonexistent():
    result = restore("/nonexistent/backup.zip")
    assert result["status"] == "error"


def test_restore_rejects_invalid_zip(tmp_path):
    bad = tmp_path / "bad.zip"
    bad.write_bytes(b"not a zip")
    result = restore(str(bad))
    assert result["status"] == "error"
    assert "valid ZIP" in result["message"]


def test_list_backups_returns_list():
    result = list_backups()
    assert isinstance(result, list)


def test_backup_restore_round_trip(tmp_path):
    """Create a backup and restore it — should not crash."""
    result = backup(dest_dir=str(tmp_path))
    zip_path = result["path"]
    restore_result = restore(zip_path)
    assert restore_result["status"] == "ok"
    assert restore_result["restored_files"] >= 0
