"""
test_phase4.py — Tests for Phase 4: cross-platform packaging configuration.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Packaging common module
# ---------------------------------------------------------------------------


def test_common_module_importable():
    import sys

    sys.path.insert(0, str(PROJECT_ROOT / "packaging"))
    from common import ALL_HIDDEN, CHROMADB_MIGRATIONS, STATIC_FILES, EXCLUDES

    assert len(ALL_HIDDEN) > 30  # should have 40+ hidden imports
    assert isinstance(CHROMADB_MIGRATIONS, tuple)
    assert isinstance(STATIC_FILES, tuple)
    assert "pytest" in EXCLUDES


def test_common_includes_all_routes():
    import sys

    sys.path.insert(0, str(PROJECT_ROOT / "packaging"))
    from common import APP_HIDDEN

    expected_routes = [
        "desktop.routes.backups",
        "desktop.routes.download",
        "desktop.routes.graph",
        "desktop.routes.mcp",
        "desktop.routes.models",
        "desktop.routes.network",
        "desktop.routes.provenance",
        "desktop.routes.search",
        "desktop.routes.settings",
        "desktop.routes.status",
        "desktop.routes.support",
        "desktop.routes.updater",
        "desktop.routes.upload",
        "desktop.routes.vault_lock",
    ]
    for route in expected_routes:
        assert route in APP_HIDDEN, f"Missing route in common: {route}"


def test_common_includes_all_services():
    import sys

    sys.path.insert(0, str(PROJECT_ROOT / "packaging"))
    from common import APP_HIDDEN

    expected_services = [
        "desktop.services.backup_service",
        "desktop.services.job_manager",
        "desktop.services.logging_service",
        "desktop.services.model_manager",
        "desktop.services.network_policy",
        "desktop.services.search_service",
        "desktop.services.updater",
        "desktop.services.vault_lock",
    ]
    for svc in expected_services:
        assert svc in APP_HIDDEN, f"Missing service in common: {svc}"


# ---------------------------------------------------------------------------
# Spec files exist
# ---------------------------------------------------------------------------


def test_windows_spec_exists():
    assert (PROJECT_ROOT / "recallos_desktop.spec").exists()


def test_macos_spec_exists():
    assert (PROJECT_ROOT / "packaging" / "macos" / "recallos_macos.spec").exists()


def test_linux_spec_exists():
    assert (PROJECT_ROOT / "packaging" / "linux" / "recallos_linux.spec").exists()


def test_linux_desktop_file_exists():
    assert (PROJECT_ROOT / "packaging" / "linux" / "RecallOS.desktop").exists()


# ---------------------------------------------------------------------------
# Release workflow
# ---------------------------------------------------------------------------


def test_release_workflow_exists():
    wf = PROJECT_ROOT / ".github" / "workflows" / "release.yml"
    assert wf.exists()
    content = wf.read_text()
    assert "windows-latest" in content
    assert "macos-latest" in content
    assert "ubuntu-latest" in content


# ---------------------------------------------------------------------------
# Build script
# ---------------------------------------------------------------------------


def test_build_script_exists():
    assert (PROJECT_ROOT / "scripts" / "build.py").exists()


def test_build_script_has_all_platforms():
    content = (PROJECT_ROOT / "scripts" / "build.py").read_text()
    assert "windows" in content
    assert "macos" in content
    assert "linux" in content
