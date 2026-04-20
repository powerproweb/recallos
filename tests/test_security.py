"""
test_security.py — Tests for Phase 2 security hardening.

Covers: filesystem sandbox, audit logging, provenance endpoints.
"""

from desktop.security import (
    PathNotAllowedError,
    audit_action,
    get_audit_log,
    is_path_allowed,
    validate_path,
    _RECALLOS_HOME,
)


# ---------------------------------------------------------------------------
# Filesystem sandbox
# ---------------------------------------------------------------------------


def test_validate_path_allows_recallos_home():
    """Paths under ~/.recallos are allowed."""
    p = _RECALLOS_HOME / "vault" / "some_file.db"
    # Should not raise (even if file doesn't exist — we validate the path, not existence)
    result = validate_path(str(p))
    assert result.is_relative_to(_RECALLOS_HOME)


def test_validate_path_blocks_outside_sandbox():
    """Paths outside approved roots are blocked."""
    import pytest

    with pytest.raises(PathNotAllowedError):
        validate_path("/etc/passwd")


def test_validate_path_blocks_traversal():
    """Path traversal attempts are blocked."""
    import pytest

    traversal = str(_RECALLOS_HOME / ".." / ".." / "etc" / "passwd")
    with pytest.raises(PathNotAllowedError):
        validate_path(traversal)


def test_is_path_allowed_returns_bool():
    assert is_path_allowed(str(_RECALLOS_HOME / "test.txt")) is True
    assert is_path_allowed("/etc/shadow") is False


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------


def test_audit_action_writes_to_db():
    audit_action("test_action", "test detail 12345")
    log = get_audit_log(limit=5)
    assert len(log) >= 1
    latest = log[0]
    assert latest["action"] == "test_action"
    assert "12345" in latest["detail"]


def test_audit_log_returns_list():
    result = get_audit_log(limit=10)
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Provenance routes
# ---------------------------------------------------------------------------


def test_provenance_info():
    from desktop.routes.provenance import build_info

    result = build_info()
    assert "recallos_version" in result
    assert "python_version" in result
    assert "platform" in result


def test_provenance_licenses():
    from desktop.routes.provenance import third_party_licenses

    result = third_party_licenses()
    assert "packages" in result
    assert isinstance(result["packages"], list)
    assert len(result["packages"]) > 0
    assert "name" in result["packages"][0]


def test_provenance_audit():
    from desktop.routes.provenance import audit_log

    result = audit_log(limit=10)
    assert "entries" in result
    assert isinstance(result["entries"], list)
