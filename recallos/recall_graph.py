"""
recall_graph.py — Temporal Entity-Relationship Graph for RecallOS
=================================================================

Recall Graph with:
  - Entity nodes (people, projects, tools, concepts)
  - Typed relationship edges (daughter_of, does, loves, works_on, etc.)
  - Temporal validity (valid_from → valid_to — knows WHEN facts are true)
  - Index Summary references (links back to the verbatim memory)

Storage: SQLite (local, no dependencies, no subscriptions)
Query: entity-first traversal with time filtering

This is what competes with Zep's temporal knowledge graph.
Zep uses Neo4j in the cloud ($25/mo+). We use SQLite locally (free).

Usage:
    from recallos.recall_graph import RecallGraph

    rg = RecallGraph()
    rg.add_triple("Max", "child_of", "Alice", valid_from="2015-04-01")
    rg.add_triple("Max", "does", "swimming", valid_from="2025-01-01")
    rg.add_triple("Max", "loves", "chess", valid_from="2025-10-01")

    # Query: everything about Max
    rg.query_entity("Max")

    # Query: what was true about Max in January 2026?
    rg.query_entity("Max", as_of="2026-01-15")

    # Query: who is connected to Alice?
    rg.query_entity("Alice", direction="both")

    # Invalidate: Max's sports injury resolved
    rg.invalidate("Max", "has_issue", "sports_injury", ended="2026-02-15")
"""

import hashlib
import json
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path


DEFAULT_RG_PATH = os.path.expanduser("~/.recallos/recall_graph.sqlite3")


class RecallGraph:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_RG_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = self._conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT DEFAULT 'unknown',
                properties TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS triples (
                id TEXT PRIMARY KEY,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                valid_from TEXT,
                valid_to TEXT,
                confidence REAL DEFAULT 1.0,
                source_index TEXT,
                source_file TEXT,
                extracted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject) REFERENCES entities(id),
                FOREIGN KEY (object) REFERENCES entities(id)
            );

            CREATE INDEX IF NOT EXISTS idx_triples_subject ON triples(subject);
            CREATE INDEX IF NOT EXISTS idx_triples_object ON triples(object);
            CREATE INDEX IF NOT EXISTS idx_triples_predicate ON triples(predicate);
            CREATE INDEX IF NOT EXISTS idx_triples_valid ON triples(valid_from, valid_to);
        """)
        conn.commit()
        conn.close()

    def _conn(self):
        return sqlite3.connect(self.db_path, timeout=10)

    def _entity_id(self, name: str) -> str:
        return name.lower().replace(" ", "_").replace("'", "")

    # ── Write operations ──────────────────────────────────────────────────

    def add_entity(self, name: str, entity_type: str = "unknown", properties: dict = None):
        """Add or update an entity node."""
        eid = self._entity_id(name)
        props = json.dumps(properties or {})
        conn = self._conn()
        conn.execute(
            "INSERT OR REPLACE INTO entities (id, name, type, properties) VALUES (?, ?, ?, ?)",
            (eid, name, entity_type, props),
        )
        conn.commit()
        conn.close()
        return eid

    def add_triple(
        self,
        subject: str,
        predicate: str,
        obj: str,
        valid_from: str = None,
        valid_to: str = None,
        confidence: float = 1.0,
        source_index: str = None,
        source_file: str = None,
    ):
        """
        Add a relationship triple: subject → predicate → object.

        Examples:
            add_triple("Max", "child_of", "Alice", valid_from="2015-04-01")
            add_triple("Max", "does", "swimming", valid_from="2025-01-01")
            add_triple("Alice", "worried_about", "Max injury", valid_from="2026-01", valid_to="2026-02")
        """
        sub_id = self._entity_id(subject)
        obj_id = self._entity_id(obj)
        pred = predicate.lower().replace(" ", "_")

        # Auto-create entities if they don't exist
        conn = self._conn()
        conn.execute("INSERT OR IGNORE INTO entities (id, name) VALUES (?, ?)", (sub_id, subject))
        conn.execute("INSERT OR IGNORE INTO entities (id, name) VALUES (?, ?)", (obj_id, obj))

        # Check for existing identical triple
        existing = conn.execute(
            "SELECT id FROM triples WHERE subject=? AND predicate=? AND object=? AND valid_to IS NULL",
            (sub_id, pred, obj_id),
        ).fetchone()

        if existing:
            conn.close()
            return existing[0]  # Already exists and still valid

        triple_id = f"t_{sub_id}_{pred}_{obj_id}_{hashlib.md5(f'{valid_from}{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}"

        conn.execute(
            """INSERT INTO triples (id, subject, predicate, object, valid_from, valid_to, confidence, source_index, source_file)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                triple_id,
                sub_id,
                pred,
                obj_id,
                valid_from,
                valid_to,
                confidence,
                source_index,
                source_file,
            ),
        )
        conn.commit()
        conn.close()
        return triple_id

    def invalidate(self, subject: str, predicate: str, obj: str, ended: str = None):
        """Mark a relationship as no longer valid (set valid_to date)."""
        sub_id = self._entity_id(subject)
        obj_id = self._entity_id(obj)
        pred = predicate.lower().replace(" ", "_")
        ended = ended or date.today().isoformat()

        conn = self._conn()
        conn.execute(
            "UPDATE triples SET valid_to=? WHERE subject=? AND predicate=? AND object=? AND valid_to IS NULL",
            (ended, sub_id, pred, obj_id),
        )
        conn.commit()
        conn.close()

    # ── Query operations ──────────────────────────────────────────────────

    def query_entity(self, name: str, as_of: str = None, direction: str = "outgoing"):
        """
        Get all relationships for an entity.

        direction: "outgoing" (entity → ?), "incoming" (? → entity), "both"
        as_of: date string — only return facts valid at that time
        """
        eid = self._entity_id(name)
        conn = self._conn()

        results = []

        if direction in ("outgoing", "both"):
            query = "SELECT t.*, e.name as obj_name FROM triples t JOIN entities e ON t.object = e.id WHERE t.subject = ?"
            params = [eid]
            if as_of:
                query += " AND (t.valid_from IS NULL OR t.valid_from <= ?) AND (t.valid_to IS NULL OR t.valid_to >= ?)"
                params.extend([as_of, as_of])
            for row in conn.execute(query, params).fetchall():
                results.append(
                    {
                        "direction": "outgoing",
                        "subject": name,
                        "predicate": row[2],
                        "object": row[10],  # obj_name
                        "valid_from": row[4],
                        "valid_to": row[5],
                        "confidence": row[6],
                        "source_index": row[7],
                        "current": row[5] is None,
                    }
                )

        if direction in ("incoming", "both"):
            query = "SELECT t.*, e.name as sub_name FROM triples t JOIN entities e ON t.subject = e.id WHERE t.object = ?"
            params = [eid]
            if as_of:
                query += " AND (t.valid_from IS NULL OR t.valid_from <= ?) AND (t.valid_to IS NULL OR t.valid_to >= ?)"
                params.extend([as_of, as_of])
            for row in conn.execute(query, params).fetchall():
                results.append(
                    {
                        "direction": "incoming",
                        "subject": row[10],  # sub_name
                        "predicate": row[2],
                        "object": name,
                        "valid_from": row[4],
                        "valid_to": row[5],
                        "confidence": row[6],
                        "source_index": row[7],
                        "current": row[5] is None,
                    }
                )

        conn.close()
        return results

    def query_relationship(self, predicate: str, as_of: str = None):
        """Get all triples with a given relationship type."""
        pred = predicate.lower().replace(" ", "_")
        conn = self._conn()
        query = """
            SELECT t.*, s.name as sub_name, o.name as obj_name
            FROM triples t
            JOIN entities s ON t.subject = s.id
            JOIN entities o ON t.object = o.id
            WHERE t.predicate = ?
        """
        params = [pred]
        if as_of:
            query += " AND (t.valid_from IS NULL OR t.valid_from <= ?) AND (t.valid_to IS NULL OR t.valid_to >= ?)"
            params.extend([as_of, as_of])

        results = []
        for row in conn.execute(query, params).fetchall():
            results.append(
                {
                    "subject": row[10],
                    "predicate": pred,
                    "object": row[11],
                    "valid_from": row[4],
                    "valid_to": row[5],
                    "current": row[5] is None,
                }
            )
        conn.close()
        return results

    def timeline(self, entity_name: str = None):
        """Get all facts in chronological order, optionally filtered by entity."""
        conn = self._conn()
        if entity_name:
            eid = self._entity_id(entity_name)
            rows = conn.execute(
                """
                SELECT t.*, s.name as sub_name, o.name as obj_name
                FROM triples t
                JOIN entities s ON t.subject = s.id
                JOIN entities o ON t.object = o.id
                WHERE (t.subject = ? OR t.object = ?)
                ORDER BY t.valid_from ASC NULLS LAST
            """,
                (eid, eid),
            ).fetchall()
        else:
            rows = conn.execute("""
                SELECT t.*, s.name as sub_name, o.name as obj_name
                FROM triples t
                JOIN entities s ON t.subject = s.id
                JOIN entities o ON t.object = o.id
                ORDER BY t.valid_from ASC NULLS LAST
                LIMIT 100
            """).fetchall()

        conn.close()
        return [
            {
                "subject": r[10],
                "predicate": r[2],
                "object": r[11],
                "valid_from": r[4],
                "valid_to": r[5],
                "current": r[5] is None,
            }
            for r in rows
        ]

    # ── Stats ─────────────────────────────────────────────────────────────

    def stats(self):
        conn = self._conn()
        entities = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        triples = conn.execute("SELECT COUNT(*) FROM triples").fetchone()[0]
        current = conn.execute("SELECT COUNT(*) FROM triples WHERE valid_to IS NULL").fetchone()[0]
        expired = triples - current
        predicates = [
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT predicate FROM triples ORDER BY predicate"
            ).fetchall()
        ]
        conn.close()
        return {
            "entities": entities,
            "triples": triples,
            "current_facts": current,
            "expired_facts": expired,
            "relationship_types": predicates,
        }

    # ── Path-finding ─────────────────────────────────────────────────────

    def find_path(
        self,
        entity_a: str,
        entity_b: str,
        max_depth: int = 4,
        as_of: str = None,
    ):
        """
        Find the shortest relationship path between two entities using BFS.

        Returns a list of steps:
            [{"from": str, "predicate": str, "to": str}, ...]
        or None if no path exists within max_depth hops.
        """
        a_id = self._entity_id(entity_a)
        b_id = self._entity_id(entity_b)

        if a_id == b_id:
            return []  # same entity

        conn = self._conn()

        def neighbors(eid):
            """Return all entity IDs directly reachable from eid (both directions)."""
            q = "SELECT subject, predicate, object FROM triples WHERE (subject=? OR object=?)"
            params = [eid, eid]
            if as_of:
                q += " AND (valid_from IS NULL OR valid_from <= ?) AND (valid_to IS NULL OR valid_to >= ?)"
                params.extend([as_of, as_of])
            else:
                q += " AND valid_to IS NULL"
            rows = conn.execute(q, params).fetchall()
            result = []
            for sub, pred, obj in rows:
                if sub == eid:
                    result.append((obj, pred, "outgoing"))
                else:
                    result.append((sub, pred, "incoming"))
            return result

        # BFS
        # Each queue entry: (current_eid, path_so_far)
        # path_so_far: list of (from_id, predicate, to_id)
        from collections import deque

        queue = deque([(a_id, [])])
        visited = {a_id}

        while queue:
            current, path = queue.popleft()
            if len(path) >= max_depth:
                continue
            for neighbor_id, pred, direction in neighbors(current):
                if neighbor_id in visited:
                    continue
                step = (
                    {"from": current, "predicate": pred, "to": neighbor_id}
                    if direction == "outgoing"
                    else {"from": neighbor_id, "predicate": pred, "to": current}
                )
                new_path = path + [step]
                if neighbor_id == b_id:
                    conn.close()
                    # Resolve entity IDs back to names
                    all_ids = (
                        {a_id, b_id} | {s["from"] for s in new_path} | {s["to"] for s in new_path}
                    )
                    name_map = {}
                    conn3 = sqlite3.connect(self.db_path, timeout=10)
                    for eid in all_ids:
                        r = conn3.execute("SELECT name FROM entities WHERE id=?", (eid,)).fetchone()
                        name_map[eid] = r[0] if r else eid
                    conn3.close()
                    return [
                        {
                            "from": name_map.get(s["from"], s["from"]),
                            "predicate": s["predicate"],
                            "to": name_map.get(s["to"], s["to"]),
                        }
                        for s in new_path
                    ]
                visited.add(neighbor_id)
                queue.append((neighbor_id, new_path))

        conn.close()
        return None  # no path found

    # ── Export ───────────────────────────────────────────────────────────────

    def export_dot(self, current_only: bool = True) -> str:
        """
        Export the graph as a Graphviz DOT string.

        Args:
            current_only: If True (default), only include non-expired triples.

        Returns:
            A DOT-format string renderable with `dot -Tpng graph.dot > graph.png`.
        """
        conn = self._conn()
        q = """
            SELECT s.name, t.predicate, o.name
            FROM triples t
            JOIN entities s ON t.subject = s.id
            JOIN entities o ON t.object = o.id
        """
        if current_only:
            q += " WHERE t.valid_to IS NULL"
        rows = conn.execute(q).fetchall()
        conn.close()

        lines = ["digraph RecallGraph {"]
        lines.append("  rankdir=LR;")
        lines.append('  node [shape=box fontname="Helvetica" fontsize=10];')
        lines.append("")
        seen_nodes = set()
        for sub, pred, obj in rows:
            for name in (sub, obj):
                if name not in seen_nodes:
                    safe = name.replace('"', "'")
                    lines.append(f'  "{safe}";')
                    seen_nodes.add(name)
        lines.append("")
        for sub, pred, obj in rows:
            s = sub.replace('"', "'")
            p = pred.replace('"', "'")
            o = obj.replace('"', "'")
            lines.append(f'  "{s}" -> "{o}" [label="{p}"];')
        lines.append("}")
        return "\n".join(lines)

    def export_json(self, current_only: bool = True) -> dict:
        """
        Export the graph as a JSON adjacency structure for D3/JS visualization.

        Returns:
            {"nodes": [{"id": str, "name": str, "type": str}],
             "edges": [{"source": str, "target": str, "predicate": str,
                        "valid_from": str, "valid_to": str}]}
        """
        conn = self._conn()

        entity_rows = conn.execute("SELECT id, name, type FROM entities").fetchall()
        nodes = [{"id": row[0], "name": row[1], "type": row[2]} for row in entity_rows]

        q = "SELECT subject, predicate, object, valid_from, valid_to FROM triples"
        if current_only:
            q += " WHERE valid_to IS NULL"
        triple_rows = conn.execute(q).fetchall()
        edges = [
            {
                "source": row[0],
                "target": row[2],
                "predicate": row[1],
                "valid_from": row[3],
                "valid_to": row[4],
            }
            for row in triple_rows
        ]

        conn.close()
        return {"nodes": nodes, "edges": edges}

    # ── Seed from known facts ─────────────────────────────────────────────

    def seed_from_entity_facts(self, entity_facts: dict):
        """
        Seed the knowledge graph from fact_checker.py ENTITY_FACTS.
        This bootstraps the graph with known ground truth.
        """
        for key, facts in entity_facts.items():
            name = facts.get("full_name", key.capitalize())
            etype = facts.get("type", "person")
            self.add_entity(
                name,
                etype,
                {
                    "gender": facts.get("gender", ""),
                    "birthday": facts.get("birthday", ""),
                },
            )

            # Relationships
            parent = facts.get("parent")
            if parent:
                self.add_triple(
                    name, "child_of", parent.capitalize(), valid_from=facts.get("birthday")
                )

            partner = facts.get("partner")
            if partner:
                self.add_triple(name, "married_to", partner.capitalize())

            relationship = facts.get("relationship", "")
            if relationship == "daughter":
                self.add_triple(
                    name,
                    "is_child_of",
                    facts.get("parent", "").capitalize() or name,
                    valid_from=facts.get("birthday"),
                )
            elif relationship == "husband":
                self.add_triple(name, "is_partner_of", facts.get("partner", name).capitalize())
            elif relationship == "brother":
                self.add_triple(name, "is_sibling_of", facts.get("sibling", name).capitalize())
            elif relationship == "dog":
                self.add_triple(name, "is_pet_of", facts.get("owner", name).capitalize())
                self.add_entity(name, "animal")

            # Interests
            for interest in facts.get("interests", []):
                self.add_triple(name, "loves", interest.capitalize(), valid_from="2025-01-01")
