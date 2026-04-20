"""
test_vault_graph.py — Unit tests for recallos/vault_graph.py

Strategy: build real ChromaDB collections in temp dirs, pass them directly
to build_graph / traverse / find_links / graph_stats via the col= parameter
so no real vault path is read.
"""

import shutil
import tempfile

import chromadb

from recallos.vault_graph import (
    _fuzzy_match,
    build_graph,
    find_links,
    graph_stats,
    traverse,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_col(records: list) -> chromadb.Collection:
    """
    Create an in-memory-style ChromaDB collection with the given records.
    Each record is a dict with at least 'id', 'doc', and 'meta' keys.
    Returns (client, collection) — caller must del both when done.
    """
    tmpdir = tempfile.mkdtemp()
    client = chromadb.PersistentClient(path=tmpdir)
    col = client.create_collection("recallos_records")
    if records:
        col.add(
            ids=[r["id"] for r in records],
            documents=[r.get("doc", "text") for r in records],
            metadatas=[r["meta"] for r in records],
        )
    return client, col, tmpdir


def _cleanup(client, tmpdir):
    del client
    shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# build_graph
# ---------------------------------------------------------------------------


def test_build_graph_empty_collection():
    client, col, tmpdir = _make_col([])
    nodes, edges = build_graph(col=col)
    assert nodes == {}
    assert edges == []
    _cleanup(client, tmpdir)


def test_build_graph_single_domain_no_edges():
    """A node appearing in only one domain creates a node entry but no edge."""
    client, col, tmpdir = _make_col(
        [
            {
                "id": "r1",
                "doc": "x",
                "meta": {"node": "auth", "domain": "proj_a", "channel": "channel_facts"},
            },
            {
                "id": "r2",
                "doc": "y",
                "meta": {"node": "auth", "domain": "proj_a", "channel": "channel_facts"},
            },
        ]
    )
    nodes, edges = build_graph(col=col)
    assert "auth" in nodes
    assert nodes["auth"]["count"] == 2
    assert nodes["auth"]["domains"] == ["proj_a"]
    assert edges == []
    _cleanup(client, tmpdir)


def test_build_graph_multi_domain_creates_edge():
    """The same node in two domains → one edge per channel."""
    client, col, tmpdir = _make_col(
        [
            {
                "id": "r1",
                "doc": "x",
                "meta": {"node": "auth", "domain": "proj_a", "channel": "channel_facts"},
            },
            {
                "id": "r2",
                "doc": "y",
                "meta": {"node": "auth", "domain": "proj_b", "channel": "channel_facts"},
            },
        ]
    )
    nodes, edges = build_graph(col=col)
    assert "auth" in nodes
    assert set(nodes["auth"]["domains"]) == {"proj_a", "proj_b"}
    assert len(edges) == 1
    assert edges[0]["node"] == "auth"
    assert edges[0]["domain_a"] == "proj_a"
    assert edges[0]["domain_b"] == "proj_b"
    _cleanup(client, tmpdir)


def test_build_graph_general_node_excluded():
    """Records with node='general' must not appear in the graph."""
    client, col, tmpdir = _make_col(
        [
            {
                "id": "r1",
                "doc": "x",
                "meta": {"node": "general", "domain": "proj_a", "channel": ""},
            },
        ]
    )
    nodes, edges = build_graph(col=col)
    assert "general" not in nodes
    _cleanup(client, tmpdir)


def test_build_graph_missing_domain_excluded():
    """Records with no domain set must not appear in the graph."""
    client, col, tmpdir = _make_col(
        [
            {"id": "r1", "doc": "x", "meta": {"node": "auth", "domain": "", "channel": ""}},
        ]
    )
    nodes, edges = build_graph(col=col)
    assert "auth" not in nodes
    _cleanup(client, tmpdir)


def test_build_graph_no_collection_returns_empty():
    # Use an explicit empty collection instead of relying on _get_collection
    # fallback which reads the user's real vault and is non-deterministic.
    client, col, tmpdir = _make_col([])
    nodes, edges = build_graph(col=col)
    assert nodes == {}
    assert edges == []
    _cleanup(client, tmpdir)


def test_build_graph_multiple_channels_multiple_edges():
    """Same node in two domains, two channels → two edges."""
    client, col, tmpdir = _make_col(
        [
            {
                "id": "r1",
                "doc": "x",
                "meta": {"node": "db", "domain": "proj_a", "channel": "channel_facts"},
            },
            {
                "id": "r2",
                "doc": "y",
                "meta": {"node": "db", "domain": "proj_a", "channel": "channel_events"},
            },
            {
                "id": "r3",
                "doc": "z",
                "meta": {"node": "db", "domain": "proj_b", "channel": "channel_facts"},
            },
            {
                "id": "r4",
                "doc": "w",
                "meta": {"node": "db", "domain": "proj_b", "channel": "channel_events"},
            },
        ]
    )
    nodes, edges = build_graph(col=col)
    # 2 channels × 1 domain pair = 2 edges
    assert len(edges) == 2
    _cleanup(client, tmpdir)


# ---------------------------------------------------------------------------
# traverse
# ---------------------------------------------------------------------------


def test_traverse_node_not_found():
    """Traversing a non-existent node returns an error dict with suggestions."""
    client, col, tmpdir = _make_col(
        [
            {
                "id": "r1",
                "doc": "x",
                "meta": {"node": "auth-setup", "domain": "proj_a", "channel": "channel_facts"},
            },
        ]
    )
    result = traverse("nonexistent", col=col)
    assert isinstance(result, dict)
    assert "error" in result
    assert "suggestions" in result
    _cleanup(client, tmpdir)


def test_traverse_node_not_found_suggests_partial_match():
    """Fuzzy suggestions include partial matches for the query."""
    client, col, tmpdir = _make_col(
        [
            {
                "id": "r1",
                "doc": "x",
                "meta": {"node": "auth-setup", "domain": "proj_a", "channel": "channel_facts"},
            },
        ]
    )
    result = traverse("auth", col=col)
    assert isinstance(result, dict)
    assert "auth-setup" in result["suggestions"]
    _cleanup(client, tmpdir)


def test_traverse_returns_start_node():
    """Traversal always includes the start node at hop=0."""
    client, col, tmpdir = _make_col(
        [
            {
                "id": "r1",
                "doc": "x",
                "meta": {"node": "auth", "domain": "proj_a", "channel": "channel_facts"},
            },
        ]
    )
    result = traverse("auth", col=col)
    assert isinstance(result, list)
    assert result[0]["node"] == "auth"
    assert result[0]["hop"] == 0
    _cleanup(client, tmpdir)


def test_traverse_finds_connected_node():
    """Nodes sharing a domain appear in traversal results at hop=1."""
    client, col, tmpdir = _make_col(
        [
            {
                "id": "r1",
                "doc": "x",
                "meta": {"node": "auth", "domain": "proj_a", "channel": "channel_facts"},
            },
            {
                "id": "r2",
                "doc": "y",
                "meta": {"node": "billing", "domain": "proj_a", "channel": "channel_facts"},
            },
        ]
    )
    result = traverse("auth", col=col)
    nodes_found = [r["node"] for r in result]
    assert "auth" in nodes_found
    assert "billing" in nodes_found
    hop_billing = next(r["hop"] for r in result if r["node"] == "billing")
    assert hop_billing == 1
    _cleanup(client, tmpdir)


def test_traverse_max_hops_1_limits_results():
    """max_hops=1 stops after direct connections; 2-hop nodes are excluded."""
    client, col, tmpdir = _make_col(
        [
            {
                "id": "r1",
                "doc": "x",
                "meta": {"node": "auth", "domain": "proj_a", "channel": "channel_facts"},
            },
            {
                "id": "r2",
                "doc": "y",
                "meta": {"node": "billing", "domain": "proj_a", "channel": "channel_facts"},
            },
            {
                "id": "r3",
                "doc": "z",
                "meta": {"node": "billing", "domain": "proj_b", "channel": "channel_facts"},
            },
            {
                "id": "r4",
                "doc": "w",
                "meta": {"node": "deploy", "domain": "proj_b", "channel": "channel_facts"},
            },
        ]
    )
    # auth → proj_a → billing → proj_b → deploy  (2 hops from auth)
    result_1 = traverse("auth", col=col, max_hops=1)
    result_2 = traverse("auth", col=col, max_hops=2)

    hops_1 = {r["node"] for r in result_1}
    hops_2 = {r["node"] for r in result_2}

    assert "billing" in hops_1
    assert "deploy" not in hops_1  # 2 hops away
    assert "deploy" in hops_2  # reachable at max_hops=2
    _cleanup(client, tmpdir)


# ---------------------------------------------------------------------------
# find_links
# ---------------------------------------------------------------------------


def test_find_links_returns_multi_domain_nodes():
    """find_links only returns nodes appearing in 2+ domains."""
    client, col, tmpdir = _make_col(
        [
            {"id": "r1", "doc": "x", "meta": {"node": "auth", "domain": "proj_a", "channel": ""}},
            {"id": "r2", "doc": "y", "meta": {"node": "auth", "domain": "proj_b", "channel": ""}},
            {
                "id": "r3",
                "doc": "z",
                "meta": {"node": "billing", "domain": "proj_a", "channel": ""},
            },
        ]
    )
    links = find_links(col=col)
    link_nodes = [lnk["node"] for lnk in links]
    assert "auth" in link_nodes
    assert "billing" not in link_nodes
    _cleanup(client, tmpdir)


def test_find_links_domain_filter():
    """domain_a filter returns only links containing that domain."""
    client, col, tmpdir = _make_col(
        [
            {"id": "r1", "doc": "x", "meta": {"node": "auth", "domain": "proj_a", "channel": ""}},
            {"id": "r2", "doc": "y", "meta": {"node": "auth", "domain": "proj_b", "channel": ""}},
            {"id": "r3", "doc": "z", "meta": {"node": "cache", "domain": "proj_b", "channel": ""}},
            {"id": "r4", "doc": "w", "meta": {"node": "cache", "domain": "proj_c", "channel": ""}},
        ]
    )
    links_a = find_links(domain_a="proj_a", col=col)
    link_nodes_a = [lnk["node"] for lnk in links_a]
    assert "auth" in link_nodes_a
    assert "cache" not in link_nodes_a  # proj_c, not proj_a
    _cleanup(client, tmpdir)


def test_find_links_both_domain_filter():
    """Both domain_a and domain_b filter returns only nodes in both."""
    client, col, tmpdir = _make_col(
        [
            {"id": "r1", "doc": "x", "meta": {"node": "auth", "domain": "proj_a", "channel": ""}},
            {"id": "r2", "doc": "y", "meta": {"node": "auth", "domain": "proj_b", "channel": ""}},
            {"id": "r3", "doc": "z", "meta": {"node": "cache", "domain": "proj_a", "channel": ""}},
            {"id": "r4", "doc": "w", "meta": {"node": "cache", "domain": "proj_c", "channel": ""}},
        ]
    )
    links = find_links(domain_a="proj_a", domain_b="proj_b", col=col)
    link_nodes = [lnk["node"] for lnk in links]
    assert "auth" in link_nodes  # in both proj_a and proj_b
    assert "cache" not in link_nodes  # proj_a + proj_c, not proj_b
    _cleanup(client, tmpdir)


def test_find_links_empty_when_no_links():
    client, col, tmpdir = _make_col(
        [
            {"id": "r1", "doc": "x", "meta": {"node": "auth", "domain": "proj_a", "channel": ""}},
        ]
    )
    links = find_links(col=col)
    assert links == []
    _cleanup(client, tmpdir)


# ---------------------------------------------------------------------------
# graph_stats
# ---------------------------------------------------------------------------


def test_graph_stats_structure():
    """graph_stats always returns the expected keys."""
    client, col, tmpdir = _make_col(
        [
            {
                "id": "r1",
                "doc": "x",
                "meta": {"node": "auth", "domain": "proj_a", "channel": "channel_facts"},
            },
        ]
    )
    stats = graph_stats(col=col)
    assert "total_nodes" in stats
    assert "link_nodes" in stats
    assert "total_edges" in stats
    assert "nodes_per_domain" in stats
    assert "top_links" in stats
    _cleanup(client, tmpdir)


def test_graph_stats_counts():
    """graph_stats correctly counts nodes and link_nodes."""
    client, col, tmpdir = _make_col(
        [
            {"id": "r1", "doc": "x", "meta": {"node": "auth", "domain": "proj_a", "channel": ""}},
            {"id": "r2", "doc": "y", "meta": {"node": "auth", "domain": "proj_b", "channel": ""}},
            {
                "id": "r3",
                "doc": "z",
                "meta": {"node": "billing", "domain": "proj_a", "channel": ""},
            },
        ]
    )
    stats = graph_stats(col=col)
    assert stats["total_nodes"] == 2  # auth, billing
    assert stats["link_nodes"] == 1  # only auth spans 2 domains
    assert stats["nodes_per_domain"]["proj_a"] == 2
    assert stats["nodes_per_domain"]["proj_b"] == 1
    _cleanup(client, tmpdir)


def test_graph_stats_empty_collection():
    client, col, tmpdir = _make_col([])
    stats = graph_stats(col=col)
    assert stats["total_nodes"] == 0
    assert stats["link_nodes"] == 0
    assert stats["total_edges"] == 0
    _cleanup(client, tmpdir)


# ---------------------------------------------------------------------------
# _fuzzy_match
# ---------------------------------------------------------------------------


def test_fuzzy_match_exact_substring():
    nodes = {"auth-setup": {}, "billing-setup": {}, "deploy": {}}
    matches = _fuzzy_match("auth", nodes)
    assert "auth-setup" in matches


def test_fuzzy_match_hyphen_word():
    """A word split by hyphen matches the fragment."""
    nodes = {"auth-setup": {}, "billing-setup": {}, "deploy": {}}
    matches = _fuzzy_match("setup", nodes)
    assert "auth-setup" in matches
    assert "billing-setup" in matches


def test_fuzzy_match_no_match_returns_empty():
    nodes = {"auth": {}, "billing": {}}
    matches = _fuzzy_match("nonexistent", nodes)
    assert matches == []


def test_fuzzy_match_respects_n_limit():
    nodes = {f"auth-{i}": {} for i in range(10)}
    matches = _fuzzy_match("auth", nodes, n=3)
    assert len(matches) <= 3
