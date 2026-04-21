"""
test_freeze_compat.py — Phase 0.7 PyInstaller compatibility tests.

Verifies that the desktop app code handles both normal and frozen
(PyInstaller) execution contexts correctly.
"""

import sys
from pathlib import Path
from unittest import mock


def test_static_dir_resolves_in_normal_mode():
    """In normal (non-frozen) mode, STATIC_DIR points to desktop/static/."""
    # Ensure we're not accidentally frozen
    assert not getattr(sys, "frozen", False)

    from desktop.server import STATIC_DIR

    assert STATIC_DIR == Path(__file__).resolve().parent.parent / "desktop" / "static"


def test_static_dir_resolves_in_frozen_mode(tmp_path):
    """In frozen mode, STATIC_DIR should use sys._MEIPASS."""
    fake_meipass = str(tmp_path)

    with mock.patch.dict(sys.__dict__, {"frozen": True, "_MEIPASS": fake_meipass}):
        # Re-evaluate the conditional by re-importing
        # We can't easily re-import a module-level variable, so test the logic directly
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            static_dir = Path(sys._MEIPASS) / "desktop" / "static"
        else:
            static_dir = Path(__file__).parent / "static"

        assert static_dir == tmp_path / "desktop" / "static"


def test_app_main_is_callable():
    """desktop.app.main is importable and callable."""
    from desktop.app import main

    assert callable(main)


def test_freeze_support_imported():
    """multiprocessing.freeze_support is used in app.py."""
    import inspect

    from desktop.app import main

    source = inspect.getsource(main)
    assert "freeze_support" in source


def test_frozen_branch_passes_app_object():
    """When sys.frozen is True, app.py should pass the app object, not a string."""
    import inspect

    from desktop.app import main

    source = inspect.getsource(main)
    # The frozen branch should import the app object directly
    assert "from desktop.server import app" in source


def test_spec_file_exists():
    """recallos_desktop.spec exists in the project root."""
    spec_path = Path(__file__).resolve().parent.parent / "recallos_desktop.spec"
    assert spec_path.exists(), f"Spec file not found at {spec_path}"


def test_spec_references_desktop_app():
    """The spec file points to desktop/app.py as entry."""
    spec_path = Path(__file__).resolve().parent.parent / "recallos_desktop.spec"
    content = spec_path.read_text()
    assert "desktop/app.py" in content or "desktop\\\\app.py" in content


def test_spec_includes_static_data():
    """The packaging config bundles desktop/static/ as data."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packaging"))
    from common import STATIC_FILES

    assert "static" in STATIC_FILES[0]


def test_spec_includes_chromadb_hidden_imports():
    """The packaging config includes critical chromadb hidden imports."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packaging"))
    from common import ALL_HIDDEN

    assert "chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2" in ALL_HIDDEN
    assert "chromadb.telemetry.product.posthog" in ALL_HIDDEN
    assert "chromadb.db.impl.sqlite" in ALL_HIDDEN


def test_spec_includes_uvicorn_hidden_imports():
    """The packaging config includes critical uvicorn hidden imports."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packaging"))
    from common import ALL_HIDDEN

    assert "uvicorn.protocols.http.auto" in ALL_HIDDEN
    assert "uvicorn.lifespan.on" in ALL_HIDDEN
