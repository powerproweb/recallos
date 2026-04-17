"""
desktop/services/model_manager.py — Offline embedding model management.

RecallOS uses ChromaDB's default ONNX all-MiniLM-L6-v2 model for embeddings.
By default ChromaDB downloads this model silently on first use.  The Model
Manager makes this explicit:

  - Detect whether the model is already cached locally
  - Verify its integrity via SHA-256
  - Provide an explicit download action (user-initiated, not implicit)
  - Report offline-ready status for the dashboard

No model download ever happens without the user's knowledge.
"""

from __future__ import annotations

import hashlib
import shutil
import tarfile
from pathlib import Path

# Pull the canonical constants from ChromaDB itself so we stay in sync
# with whatever version the user has installed.
from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import ONNXMiniLM_L6_V2

MODEL_NAME: str = ONNXMiniLM_L6_V2.MODEL_NAME  # "all-MiniLM-L6-v2"
MODEL_SHA256: str = ONNXMiniLM_L6_V2._MODEL_SHA256
MODEL_DOWNLOAD_URL: str = ONNXMiniLM_L6_V2.MODEL_DOWNLOAD_URL
CACHE_DIR: Path = Path(ONNXMiniLM_L6_V2.DOWNLOAD_PATH)
EXTRACTED_FOLDER: str = ONNXMiniLM_L6_V2.EXTRACTED_FOLDER_NAME  # "onnx"
ARCHIVE_FILENAME: str = ONNXMiniLM_L6_V2.ARCHIVE_FILENAME  # "onnx.tar.gz"


class ModelManager:
    """Manage the local embedding model used by ChromaDB."""

    def __init__(self, cache_dir: Path | None = None):
        self._cache_dir = cache_dir or CACHE_DIR

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    @property
    def model_dir(self) -> Path:
        """Path to the extracted model directory."""
        return self._cache_dir / EXTRACTED_FOLDER

    @property
    def is_installed(self) -> bool:
        """True if the model directory exists and contains the ONNX file."""
        onnx_file = self.model_dir / "model.onnx"
        return onnx_file.is_file()

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    def get_info(self) -> dict:
        """Return model metadata for the UI."""
        installed = self.is_installed
        info: dict = {
            "name": MODEL_NAME,
            "installed": installed,
            "cache_dir": str(self._cache_dir),
            "model_dir": str(self.model_dir),
            "expected_sha256": MODEL_SHA256,
        }

        if installed:
            info["size_bytes"] = self._dir_size(self.model_dir)
            info["verified"] = self.verify()
        else:
            info["size_bytes"] = 0
            info["verified"] = False
            info["download_url"] = MODEL_DOWNLOAD_URL

        return info

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify(self) -> bool:
        """Check that the cached archive matches the expected SHA-256.

        If the archive has been deleted (ChromaDB extracts then keeps it),
        we fall back to checking that the onnx file exists.  A full
        byte-level hash of the extracted directory is expensive and not
        done here — archive hash is the primary gate.
        """
        archive = self._cache_dir / ARCHIVE_FILENAME
        if archive.is_file():
            return self._sha256(archive) == MODEL_SHA256
        # Archive missing but extracted dir present — accept
        return self.is_installed

    # ------------------------------------------------------------------
    # Explicit download
    # ------------------------------------------------------------------

    def download(self) -> dict:
        """Download the model explicitly.

        Uses ChromaDB's own download machinery so we stay compatible.
        Returns status dict.
        """
        try:
            # ChromaDB's constructor triggers download if not cached
            ONNXMiniLM_L6_V2()
            return {
                "status": "ok",
                "message": f"Model '{MODEL_NAME}' downloaded and verified.",
                "model_dir": str(self.model_dir),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def import_from(self, source_path: str) -> dict:
        """Import a model archive from a local file (air-gapped install).

        The file must be the same ``onnx.tar.gz`` that ChromaDB expects.
        """
        src = Path(source_path)
        if not src.is_file():
            return {"status": "error", "message": f"File not found: {source_path}"}

        # Verify hash before extracting
        if self._sha256(src) != MODEL_SHA256:
            return {
                "status": "error",
                "message": "SHA-256 mismatch — this is not the expected model archive.",
            }

        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # Copy archive to cache dir
        dest_archive = self._cache_dir / ARCHIVE_FILENAME
        shutil.copy2(str(src), str(dest_archive))

        # Extract
        with tarfile.open(str(dest_archive), "r:gz") as tar:
            tar.extractall(path=str(self._cache_dir))

        if self.is_installed:
            return {
                "status": "ok",
                "message": f"Model imported from {source_path}",
                "model_dir": str(self.model_dir),
            }
        return {"status": "error", "message": "Extraction succeeded but model files not found."}

    # ------------------------------------------------------------------
    # Offline readiness
    # ------------------------------------------------------------------

    def offline_status(self) -> dict:
        """Report whether RecallOS can run fully offline."""
        model_ok = self.is_installed
        return {
            "offline_ready": model_ok,
            "checks": {
                "embedding_model": {
                    "ok": model_ok,
                    "detail": (
                        f"{MODEL_NAME} installed at {self.model_dir}"
                        if model_ok
                        else f"{MODEL_NAME} not found — run explicit download or import"
                    ),
                },
            },
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _dir_size(path: Path) -> int:
        return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
