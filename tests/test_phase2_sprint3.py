"""
test_phase2_sprint3.py — Tests for Phase 2 Sprint 3: updater, vault lock, tray.
"""

from desktop.services.updater import compare_versions, verify_bundle
from desktop.services.vault_lock import enable, disable, verify, is_enabled, get_status
from desktop.tray import _has_pystray


# ---------------------------------------------------------------------------
# 2.3 Updater
# ---------------------------------------------------------------------------


def test_compare_versions_equal():
    assert compare_versions("4.1.0", "4.1.0") == 0


def test_compare_versions_older():
    assert compare_versions("4.0.0", "4.1.0") == -1


def test_compare_versions_newer():
    assert compare_versions("4.2.0", "4.1.0") == 1


def test_compare_versions_with_v_prefix():
    assert compare_versions("4.1.0", "v4.2.0") == -1


def test_verify_bundle_nonexistent():
    result = verify_bundle("/nonexistent/file.whl", "abc123")
    assert result["status"] == "error"
    assert "not found" in result["message"].lower()


def test_verify_bundle_wrong_hash(tmp_path):
    f = tmp_path / "fake.whl"
    f.write_bytes(b"fake content")
    result = verify_bundle(str(f), "0" * 64)
    assert result["status"] == "error"
    assert "mismatch" in result["message"].lower()


def test_verify_bundle_correct_hash(tmp_path):
    import hashlib

    content = b"test bundle content"
    f = tmp_path / "bundle.whl"
    f.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    result = verify_bundle(str(f), expected)
    assert result["status"] == "ok"


# ---------------------------------------------------------------------------
# 2.4 Vault Lock
# ---------------------------------------------------------------------------


def test_vault_lock_disabled_by_default():
    assert is_enabled() is False


def test_vault_lock_status():
    status = get_status()
    assert "enabled" in status


def test_vault_lock_enable_requires_min_length():
    result = enable("short")
    assert result["status"] == "error"
    assert "8 characters" in result["message"]


def test_vault_lock_enable_disable_cycle():
    pw = "test-passphrase-123"
    result = enable(pw)
    assert result["status"] == "ok"
    assert is_enabled() is True

    assert verify(pw) is True
    assert verify("wrong") is False

    result = disable(pw)
    assert result["status"] == "ok"
    assert is_enabled() is False


def test_vault_lock_disable_wrong_passphrase():
    pw = "another-passphrase-456"
    enable(pw)
    result = disable("wrong-passphrase")
    assert result["status"] == "error"
    # Clean up
    disable(pw)


# ---------------------------------------------------------------------------
# 1.13 System tray
# ---------------------------------------------------------------------------


def test_has_pystray_returns_bool():
    result = _has_pystray()
    assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Route availability
# ---------------------------------------------------------------------------


def test_updater_check_route_importable():
    from desktop.routes.updater import check_update

    assert callable(check_update)


def test_vault_lock_routes_importable():
    from desktop.routes.vault_lock import lock_status, enable_lock, disable_lock

    assert callable(lock_status)
    assert callable(enable_lock)
    assert callable(disable_lock)
