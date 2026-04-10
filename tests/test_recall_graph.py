"""
test_recall_graph.py — Unit tests for recallos/recall_graph.py

Strategy: pass a temp SQLite path to RecallGraph() so tests never touch
the real ~/.recallos/recall_graph.sqlite3.
"""

import json

import pytest

from recallos.recall_graph import RecallGraph


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def rg(tmp_path):
    """Return a RecallGraph backed by a fresh temp SQLite database."""
    return RecallGraph(db_path=str(tmp_path / "test_graph.sqlite3"))


# ---------------------------------------------------------------------------
# add_entity
# ---------------------------------------------------------------------------


def test_add_entity_stores_and_returns_id(rg):
    eid = rg.add_entity("Alice", entity_type="person")
    assert eid == "alice"

    conn = rg._conn()
    row = conn.execute("SELECT name, type FROM entities WHERE id=?", ("alice",)).fetchone()
    conn.close()
    assert row[0] == "Alice"
    assert row[1] == "person"


def test_add_entity_with_properties(rg):
    rg.add_entity("Max", properties={"birthday": "2015-04-01"})
    conn = rg._conn()
    row = conn.execute("SELECT properties FROM entities WHERE id='max'").fetchone()
    conn.close()
    props = json.loads(row[0])
    assert props["birthday"] == "2015-04-01"


def test_add_entity_overwrites_on_duplicate(rg):
    rg.add_entity("Alice", entity_type="person")
    rg.add_entity("Alice", entity_type="project")  # overwrite
    conn = rg._conn()
    rows = conn.execute("SELECT type FROM entities WHERE id='alice'").fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0][0] == "project"


# ---------------------------------------------------------------------------
# add_triple
# ---------------------------------------------------------------------------


def test_add_triple_creates_entities_automatically(rg):
    rg.add_triple("Max", "child_of", "Alice")
    conn = rg._conn()
    max_exists = conn.execute("SELECT id FROM entities WHERE id='max'").fetchone()
    alice_exists = conn.execute("SELECT id FROM entities WHERE id='alice'").fetchone()
    conn.close()
    assert max_exists is not None
    assert alice_exists is not None


def test_add_triple_returns_triple_id(rg):
    tid = rg.add_triple("Max", "loves", "Chess")
    assert isinstance(tid, str)
    assert tid.startswith("t_")


def test_add_triple_deduplication_returns_same_id(rg):
    """Adding the same active triple twice returns the existing ID."""
    tid1 = rg.add_triple("Max", "loves", "Chess")
    tid2 = rg.add_triple("Max", "loves", "Chess")
    assert tid1 == tid2


def test_add_triple_normalizes_predicate(rg):
    rg.add_triple("Max", "Child Of", "Alice")
    conn = rg._conn()
    row = conn.execute("SELECT predicate FROM triples WHERE subject='max'").fetchone()
    conn.close()
    assert row[0] == "child_of"


def test_add_triple_stores_valid_from(rg):
    rg.add_triple("Max", "does", "swimming", valid_from="2025-01-01")
    conn = rg._conn()
    row = conn.execute(
        "SELECT valid_from FROM triples WHERE subject='max' AND predicate='does'"
    ).fetchone()
    conn.close()
    assert row[0] == "2025-01-01"


# ---------------------------------------------------------------------------
# invalidate
# ---------------------------------------------------------------------------


def test_invalidate_sets_valid_to(rg):
    rg.add_triple("Max", "has_issue", "ankle_injury")
    rg.invalidate("Max", "has_issue", "ankle_injury", ended="2026-02-15")

    conn = rg._conn()
    row = conn.execute(
        "SELECT valid_to FROM triples WHERE subject='max' AND predicate='has_issue'"
    ).fetchone()
    conn.close()
    assert row[0] == "2026-02-15"


def test_invalidate_only_affects_active_triples(rg):
    """invalidate only sets valid_to on rows that currently have valid_to IS NULL."""
    rg.add_triple("Max", "has_issue", "ankle_injury")
    rg.invalidate("Max", "has_issue", "ankle_injury", ended="2026-02-15")
    # Invalidate again — should be a no-op since valid_to is already set
    rg.invalidate("Max", "has_issue", "ankle_injury", ended="2026-03-01")

    conn = rg._conn()
    row = conn.execute(
        "SELECT valid_to FROM triples WHERE subject='max' AND predicate='has_issue'"
    ).fetchone()
    conn.close()
    # First invalidation wins
    assert row[0] == "2026-02-15"


# ---------------------------------------------------------------------------
# query_entity
# ---------------------------------------------------------------------------


def test_query_entity_outgoing(rg):
    rg.add_triple("Max", "child_of", "Alice")
    rg.add_triple("Max", "loves", "Chess")

    results = rg.query_entity("Max", direction="outgoing")
    predicates = {r["predicate"] for r in results}
    assert "child_of" in predicates
    assert "loves" in predicates


def test_query_entity_incoming(rg):
    rg.add_triple("Max", "child_of", "Alice")

    results = rg.query_entity("Alice", direction="incoming")
    assert len(results) == 1
    assert results[0]["subject"] == "Max"
    assert results[0]["predicate"] == "child_of"


def test_query_entity_both_directions(rg):
    rg.add_triple("Max", "child_of", "Alice")
    rg.add_triple("Alice", "partner_of", "Bob")

    alice_results = rg.query_entity("Alice", direction="both")
    directions = {r["direction"] for r in alice_results}
    assert "outgoing" in directions   # Alice → partner_of → Bob
    assert "incoming" in directions   # Max → child_of → Alice


def test_query_entity_as_of_filters_by_date(rg):
    rg.add_triple("Max", "attends", "Primary School", valid_from="2021-09-01", valid_to="2026-06-30")
    rg.add_triple("Max", "attends", "Secondary School", valid_from="2026-09-01")

    # In 2023, only Primary School is valid
    results_2023 = rg.query_entity("Max", as_of="2023-01-01")
    names = [r["object"] for r in results_2023]
    assert "Primary School" in names
    assert "Secondary School" not in names

    # In 2027, only Secondary School is valid (Primary has ended)
    results_2027 = rg.query_entity("Max", as_of="2027-01-01")
    names_2027 = [r["object"] for r in results_2027]
    assert "Secondary School" in names_2027
    assert "Primary School" not in names_2027


def test_query_entity_current_flag(rg):
    """current=True for triples with no valid_to, False otherwise."""
    rg.add_triple("Max", "likes", "pizza")
    rg.add_triple("Max", "liked", "sushi", valid_to="2025-01-01")

    results = rg.query_entity("Max", direction="outgoing")
    current_map = {r["predicate"]: r["current"] for r in results}
    assert current_map["likes"] is True
    assert current_map["liked"] is False


# ---------------------------------------------------------------------------
# query_relationship
# ---------------------------------------------------------------------------


def test_query_relationship_returns_matching_triples(rg):
    rg.add_triple("Max", "loves", "Chess")
    rg.add_triple("Alice", "loves", "Gardening")
    rg.add_triple("Max", "does", "swimming")

    results = rg.query_relationship("loves")
    subjects = {r["subject"] for r in results}
    assert "Max" in subjects
    assert "Alice" in subjects
    assert all(r["predicate"] == "loves" for r in results)


def test_query_relationship_as_of_filter(rg):
    rg.add_triple("Max", "loves", "Chess", valid_from="2025-01-01")
    rg.add_triple("Max", "loves", "Piano", valid_from="2027-01-01")

    results = rg.query_relationship("loves", as_of="2026-01-01")
    objects = [r["object"] for r in results]
    assert "Chess" in objects
    assert "Piano" not in objects


# ---------------------------------------------------------------------------
# timeline
# ---------------------------------------------------------------------------


def test_timeline_all_facts_in_order(rg):
    rg.add_triple("Max", "does", "swimming", valid_from="2024-01-01")
    rg.add_triple("Max", "loves", "chess",   valid_from="2025-06-01")

    tl = rg.timeline()
    assert len(tl) >= 2
    # Should be chronological (swimming before chess)
    dates = [r["valid_from"] for r in tl if r["valid_from"]]
    assert dates == sorted(dates)


def test_timeline_entity_filter(rg):
    rg.add_triple("Max",   "loves", "chess",   valid_from="2025-01-01")
    rg.add_triple("Alice", "loves", "painting", valid_from="2025-03-01")

    tl = rg.timeline("Max")
    subjects_objects = {r["subject"] for r in tl} | {r["object"] for r in tl}
    # Only Max-related triples
    assert "Max" in subjects_objects
    # Alice's facts are about Alice→painting; Alice appears as subject only
    # painting should not appear if we filter for Max
    assert "Painting" not in subjects_objects


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------


def test_stats_empty_graph(rg):
    s = rg.stats()
    assert s["entities"] == 0
    assert s["triples"] == 0
    assert s["current_facts"] == 0
    assert s["expired_facts"] == 0
    assert s["relationship_types"] == []


def test_stats_counts_correctly(rg):
    rg.add_triple("Max", "child_of", "Alice")
    rg.add_triple("Max", "loves", "Chess")
    rg.invalidate("Max", "loves", "Chess", ended="2026-01-01")

    s = rg.stats()
    assert s["entities"] == 3   # Max, Alice, Chess
    assert s["triples"] == 2
    assert s["current_facts"] == 1    # child_of (loves was invalidated)
    assert s["expired_facts"] == 1
    assert "loves" in s["relationship_types"]
    assert "child_of" in s["relationship_types"]


# ---------------------------------------------------------------------------
# find_path
# ---------------------------------------------------------------------------


def test_find_path_same_entity_returns_empty(rg):
    rg.add_entity("Max")
    result = rg.find_path("Max", "Max")
    assert result == []


def test_find_path_direct_connection(rg):
    rg.add_triple("Max", "child_of", "Alice")
    path = rg.find_path("Max", "Alice")
    assert path is not None
    assert len(path) == 1
    assert path[0]["from"] == "Max"
    assert path[0]["predicate"] == "child_of"
    assert path[0]["to"] == "Alice"


def test_find_path_two_hops(rg):
    rg.add_triple("Max", "child_of", "Alice")
    rg.add_triple("Alice", "partner_of", "Bob")
    path = rg.find_path("Max", "Bob")
    assert path is not None
    assert len(path) == 2


def test_find_path_no_connection_returns_none(rg):
    rg.add_entity("Max")
    rg.add_entity("Bob")  # no edge
    path = rg.find_path("Max", "Bob")
    assert path is None


def test_find_path_respects_max_depth(rg):
    # Chain: A → B → C → D (3 hops)
    rg.add_triple("A", "connects", "B")
    rg.add_triple("B", "connects", "C")
    rg.add_triple("C", "connects", "D")

    # max_depth=2 cannot reach D from A
    assert rg.find_path("A", "D", max_depth=2) is None
    # max_depth=3 can
    assert rg.find_path("A", "D", max_depth=3) is not None


# ---------------------------------------------------------------------------
# export_dot
# ---------------------------------------------------------------------------


def test_export_dot_valid_format(rg):
    rg.add_triple("Max", "loves", "Chess")
    dot = rg.export_dot()
    assert dot.startswith("digraph RecallGraph {")
    assert dot.endswith("}")
    assert "Max" in dot
    assert "Chess" in dot
    assert "loves" in dot


def test_export_dot_excludes_expired_by_default(rg):
    rg.add_triple("Max", "liked", "Sushi", valid_from="2024-01-01")
    rg.invalidate("Max", "liked", "Sushi", ended="2025-01-01")
    rg.add_triple("Max", "loves", "Chess")  # current

    dot = rg.export_dot(current_only=True)
    assert "Chess" in dot
    assert "Sushi" not in dot


def test_export_dot_includes_all_when_current_only_false(rg):
    rg.add_triple("Max", "liked", "Sushi")
    rg.invalidate("Max", "liked", "Sushi", ended="2025-01-01")

    dot = rg.export_dot(current_only=False)
    assert "Sushi" in dot


def test_export_dot_empty_graph(rg):
    dot = rg.export_dot()
    assert "digraph RecallGraph {" in dot


# ---------------------------------------------------------------------------
# export_json
# ---------------------------------------------------------------------------


def test_export_json_structure(rg):
    rg.add_triple("Max", "loves", "Chess")
    result = rg.export_json()
    assert "nodes" in result
    assert "edges" in result
    assert isinstance(result["nodes"], list)
    assert isinstance(result["edges"], list)


def test_export_json_nodes_have_required_keys(rg):
    rg.add_entity("Max", "person")
    result = rg.export_json()
    node = next(n for n in result["nodes"] if n["name"] == "Max")
    assert "id" in node
    assert "name" in node
    assert "type" in node


def test_export_json_edges_have_required_keys(rg):
    rg.add_triple("Max", "loves", "Chess")
    result = rg.export_json()
    assert len(result["edges"]) >= 1
    edge = result["edges"][0]
    assert "source" in edge
    assert "target" in edge
    assert "predicate" in edge


def test_export_json_current_only_excludes_expired(rg):
    rg.add_triple("Max", "liked", "Sushi")
    rg.invalidate("Max", "liked", "Sushi", ended="2025-01-01")
    rg.add_triple("Max", "loves", "Chess")

    result = rg.export_json(current_only=True)
    predicates = [e["predicate"] for e in result["edges"]]
    assert "loves" in predicates
    assert "liked" not in predicates


def test_export_json_empty_graph(rg):
    result = rg.export_json()
    assert result["nodes"] == []
    assert result["edges"] == []
