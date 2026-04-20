"""
/api/graph/* — Recall Graph and Vault Graph endpoints.
"""

from fastapi import APIRouter, Query

from recallos.config import RecallOSConfig
from recallos.recall_graph import RecallGraph
from recallos.vault_graph import graph_stats as vault_graph_stats

router = APIRouter(prefix="/graph", tags=["graph"])
_config = RecallOSConfig()


@router.get("/vault")
def get_vault_graph():
    """Return Vault Graph statistics (nodes, edges, domain breakdown)."""
    return vault_graph_stats()


@router.get("/recall/entities")
def get_recall_entities(limit: int = Query(default=100, ge=1, le=1000)):
    """List entities in the Recall Graph."""
    rg = RecallGraph()
    conn = rg._conn()
    rows = conn.execute(
        "SELECT id, name, type, properties FROM entities ORDER BY name LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return {
        "entities": [{"id": r[0], "name": r[1], "type": r[2], "properties": r[3]} for r in rows]
    }


@router.get("/recall/triples")
def get_recall_triples(
    entity: str = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """List triples in the Recall Graph, optionally filtered by entity."""
    rg = RecallGraph()
    if entity:
        results = rg.query_entity(entity, direction="both")
        return {"triples": results[:limit]}
    conn = rg._conn()
    rows = conn.execute(
        "SELECT t.subject, t.predicate, t.object, t.valid_from, t.valid_to, "
        "s.name as subject_name, o.name as object_name "
        "FROM triples t "
        "JOIN entities s ON t.subject = s.id "
        "JOIN entities o ON t.object = o.id "
        "ORDER BY t.extracted_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return {
        "triples": [
            {
                "subject": r[5],
                "predicate": r[1],
                "object": r[6],
                "valid_from": r[3],
                "valid_to": r[4],
            }
            for r in rows
        ]
    }
