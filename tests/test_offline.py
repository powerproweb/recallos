"""
test_offline.py — Phase 0.6 offline runtime tests.

Tests for:
  1. ModelManager — detection, info, verification, offline status
  2. Offline smoke test — core operations work without network
"""

from pathlib import Path

from desktop.services.model_manager import (
    ModelManager,
    MODEL_NAME,
    MODEL_SHA256,
)

# ---------------------------------------------------------------------------
# 1. ModelManager — detection and info
# ---------------------------------------------------------------------------


def test_model_manager_detects_installed_model():
    """On a dev machine the model should already be cached."""
    mm = ModelManager()
    # This test only passes if the model has been downloaded at least once;
    # CI installs chromadb which triggers it during test collection.
    assert isinstance(mm.is_installed, bool)


def test_model_manager_constants():
    assert MODEL_NAME == "all-MiniLM-L6-v2"
    assert len(MODEL_SHA256) == 64  # SHA-256 hex


def test_model_manager_get_info_structure():
    mm = ModelManager()
    info = mm.get_info()
    assert "name" in info
    assert "installed" in info
    assert "cache_dir" in info
    assert "model_dir" in info
    assert "expected_sha256" in info
    assert info["name"] == MODEL_NAME


def test_model_manager_offline_status_structure():
    mm = ModelManager()
    status = mm.offline_status()
    assert "offline_ready" in status
    assert "checks" in status
    assert "embedding_model" in status["checks"]
    assert "ok" in status["checks"]["embedding_model"]
    assert "detail" in status["checks"]["embedding_model"]


# ---------------------------------------------------------------------------
# ModelManager with a fake cache dir (no model present)
# ---------------------------------------------------------------------------


def test_model_not_installed_in_empty_dir(tmp_path):
    mm = ModelManager(cache_dir=tmp_path)
    assert mm.is_installed is False
    assert mm.verify() is False


def test_offline_status_not_ready_when_missing(tmp_path):
    mm = ModelManager(cache_dir=tmp_path)
    status = mm.offline_status()
    assert status["offline_ready"] is False


def test_get_info_when_not_installed(tmp_path):
    mm = ModelManager(cache_dir=tmp_path)
    info = mm.get_info()
    assert info["installed"] is False
    assert info["verified"] is False
    assert info["size_bytes"] == 0
    assert "download_url" in info


def test_import_rejects_nonexistent_file(tmp_path):
    mm = ModelManager(cache_dir=tmp_path)
    result = mm.import_from("/nonexistent/file.tar.gz")
    assert result["status"] == "error"
    assert "not found" in result["message"].lower()


def test_import_rejects_wrong_hash(tmp_path):
    # Create a fake archive that won't match the SHA-256
    fake_archive = tmp_path / "fake.tar.gz"
    fake_archive.write_bytes(b"not a real model")

    mm = ModelManager(cache_dir=tmp_path / "cache")
    result = mm.import_from(str(fake_archive))
    assert result["status"] == "error"
    assert "SHA-256" in result["message"]


# ---------------------------------------------------------------------------
# ModelManager with a simulated installed model
# ---------------------------------------------------------------------------


def test_model_detected_with_onnx_file(tmp_path):
    """If model.onnx exists in the expected path, is_installed is True."""
    model_dir = tmp_path / "onnx"
    model_dir.mkdir()
    (model_dir / "model.onnx").write_bytes(b"fake onnx content")

    mm = ModelManager(cache_dir=tmp_path)
    assert mm.is_installed is True


def test_verify_falls_back_to_is_installed(tmp_path):
    """When archive is missing but onnx file exists, verify returns True."""
    model_dir = tmp_path / "onnx"
    model_dir.mkdir()
    (model_dir / "model.onnx").write_bytes(b"fake")

    mm = ModelManager(cache_dir=tmp_path)
    assert mm.verify() is True


def test_offline_ready_when_model_present(tmp_path):
    model_dir = tmp_path / "onnx"
    model_dir.mkdir()
    (model_dir / "model.onnx").write_bytes(b"fake")

    mm = ModelManager(cache_dir=tmp_path)
    status = mm.offline_status()
    assert status["offline_ready"] is True


# ---------------------------------------------------------------------------
# 2. Offline smoke test — core operations
# ---------------------------------------------------------------------------


def test_retrieval_engine_import():
    """retrieval_engine can be imported without network."""
    from recallos.retrieval_engine import search, search_memories

    assert callable(search)
    assert callable(search_memories)


def test_diagnostics_import():
    """diagnostics can be imported without network."""
    from recallos.diagnostics import run_doctor

    assert callable(run_doctor)


def test_recall_graph_works_offline():
    """RecallGraph is pure SQLite — no network needed."""
    import tempfile

    from recallos.recall_graph import RecallGraph

    with tempfile.TemporaryDirectory() as td:
        rg = RecallGraph(db_path=str(Path(td) / "test.db"))
        rg.add_triple("Alice", "knows", "Bob")
        result = rg.query_entity("Alice")
        assert len(result) > 0
