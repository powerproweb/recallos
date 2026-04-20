"""
/api/export — Export vault data in various formats.
"""

import chromadb
from fastapi import APIRouter, Query

from recallos.config import RecallOSConfig

router = APIRouter(tags=["export"])
_config = RecallOSConfig()


@router.get("/export/vault")
def export_vault(domain: str = Query(default=None)):
    """Export all vault records as JSON."""
    try:
        client = chromadb.PersistentClient(path=_config.vault_path)
        col = client.get_collection("recallos_records")
    except Exception:
        return {"error": "No vault found", "records": []}

    kwargs = {"include": ["documents", "metadatas"]}
    if domain:
        kwargs["where"] = {"domain": domain}
    try:
        data = col.get(**kwargs)
    except Exception as e:
        return {"error": str(e), "records": []}

    records = []
    for doc_id, doc, meta in zip(data["ids"], data["documents"], data["metadatas"]):
        records.append({"id": doc_id, "text": doc, **meta})

    return {"count": len(records), "domain": domain, "records": records}


@router.get("/export/recallscript")
def export_recallscript(domain: str = Query(default=None)):
    """Export RecallScript-encoded records (if available)."""
    try:
        client = chromadb.PersistentClient(path=_config.vault_path)
        col = client.get_collection("recallos_encoded")
    except Exception:
        return {"error": "No encoded collection found", "records": []}

    kwargs = {"include": ["documents", "metadatas"]}
    if domain:
        kwargs["where"] = {"domain": domain}
    try:
        data = col.get(**kwargs)
    except Exception as e:
        return {"error": str(e), "records": []}

    records = []
    for doc_id, doc, meta in zip(data["ids"], data["documents"], data["metadatas"]):
        records.append({"id": doc_id, "recallscript": doc, **meta})

    return {"count": len(records), "domain": domain, "records": records}
