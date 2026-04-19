"""
test_search_api.py — Tests for the desktop search API route.

Verifies the search endpoint returns expected shapes and handles
missing vault gracefully (returns error dict, not crash).
"""

from recallos.retrieval_engine import search_memories


def test_search_memories_returns_dict_on_missing_vault():
    """search_memories returns an error dict when vault doesn't exist."""
    result = search_memories(query="test", vault_path="/nonexistent/vault")
    assert isinstance(result, dict)
    assert "error" in result


def test_search_memories_returns_expected_shape_on_missing_vault():
    """The error dict has a string error message."""
    result = search_memories(query="hello", vault_path="/nonexistent/vault")
    assert isinstance(result["error"], str)
    assert "No Data Vault" in result["error"]


def test_search_request_model():
    """SearchRequest Pydantic model validates correctly."""
    from desktop.routes.search import SearchRequest

    req = SearchRequest(query="auth decisions")
    assert req.query == "auth decisions"
    assert req.domain is None
    assert req.node is None
    assert req.limit == 10


def test_search_request_with_filters():
    from desktop.routes.search import SearchRequest

    req = SearchRequest(query="test", domain="myapp", node="backend", limit=5)
    assert req.domain == "myapp"
    assert req.node == "backend"
    assert req.limit == 5


def test_search_filters_returns_empty_on_missing_vault():
    """search_filters endpoint returns empty dicts when no vault exists."""
    from desktop.routes.search import search_filters

    result = search_filters()
    # Should return valid structure (may be empty if no vault)
    assert "domains" in result
    assert "nodes" in result
    assert isinstance(result["domains"], dict)
    assert isinstance(result["nodes"], dict)
