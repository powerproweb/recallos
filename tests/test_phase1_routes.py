"""
test_phase1_routes.py — Tests for all Phase 1 MVP backend routes.

Covers: export, graph, settings, support, and MCP endpoints.
"""


# ---------------------------------------------------------------------------
# Export routes
# ---------------------------------------------------------------------------


def test_export_vault_returns_structure():
    from desktop.routes.download import export_vault

    result = export_vault(domain=None)
    assert "records" in result
    assert isinstance(result["records"], list)


def test_export_recallscript_returns_structure():
    from desktop.routes.download import export_recallscript

    result = export_recallscript(domain=None)
    assert "records" in result
    assert isinstance(result["records"], list)


# ---------------------------------------------------------------------------
# Graph routes
# ---------------------------------------------------------------------------


def test_vault_graph_returns_structure():
    from desktop.routes.graph import get_vault_graph

    result = get_vault_graph()
    assert "total_nodes" in result
    assert "total_edges" in result


def test_recall_entities_returns_structure():
    from desktop.routes.graph import get_recall_entities

    result = get_recall_entities(limit=10)
    assert "entities" in result
    assert isinstance(result["entities"], list)


def test_recall_triples_returns_structure():
    from desktop.routes.graph import get_recall_triples

    result = get_recall_triples(entity=None, limit=10)
    assert "triples" in result
    assert isinstance(result["triples"], list)


# ---------------------------------------------------------------------------
# Settings routes
# ---------------------------------------------------------------------------


def test_get_settings_returns_dict():
    from desktop.routes.settings import get_all_settings

    result = get_all_settings()
    assert "settings" in result
    assert isinstance(result["settings"], dict)


def test_update_setting_persists():
    from desktop.routes.settings import get_all_settings, update_setting, SettingsUpdate

    body = SettingsUpdate(key="test_key_abc", value="test_value")
    update_setting(body)

    result = get_all_settings()
    assert result["settings"].get("test_key_abc") == "test_value"


# ---------------------------------------------------------------------------
# Support routes
# ---------------------------------------------------------------------------


def test_support_info_returns_system_data():
    from desktop.routes.support import system_info

    result = system_info()
    assert "os" in result
    assert "python" in result
    assert "vault_path" in result
    assert "recallos_version" in result


def test_support_doctor_returns_report():
    from desktop.routes.support import run_diagnostics

    result = run_diagnostics()
    assert "vault_path" in result
    assert "overall" in result
    assert "checks" in result


# ---------------------------------------------------------------------------
# MCP routes
# ---------------------------------------------------------------------------


def test_mcp_status_returns_structure():
    from desktop.routes.mcp import mcp_status

    result = mcp_status()
    assert "available" in result
    assert "tool_count" in result
    assert "setup_command" in result
    assert "tools" in result
    assert isinstance(result["tools"], list)


def test_mcp_tools_have_names():
    from desktop.routes.mcp import mcp_status

    result = mcp_status()
    if result["tools"]:
        assert "name" in result["tools"][0]
        assert "description" in result["tools"][0]
