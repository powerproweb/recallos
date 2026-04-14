#!/usr/bin/env python3
"""
retrieval_engine.py — Semantic retrieval from the Data Vault.

Returns verbatim text — the actual words, never summaries.
"""

from pathlib import Path

import chromadb

from .exceptions import VaultNotFoundError, QueryError


def search(query: str, vault_path: str, domain: str = None, node: str = None, n_results: int = 5):
    """
    Query the Data Vault. Returns verbatim source record content.
    Optionally filter by domain (project) or node (topic).

    Raises:
        VaultNotFoundError: if the vault or collection is missing.
        QueryError: if the ChromaDB query fails.
    """
    try:
        client = chromadb.PersistentClient(path=vault_path)
        col = client.get_collection("recallos_records")
    except Exception as e:
        raise VaultNotFoundError(vault_path, str(e))

    # Build where filter
    where = {}
    if domain and node:
        where = {"$and": [{"domain": domain}, {"node": node}]}
    elif domain:
        where = {"domain": domain}
    elif node:
        where = {"node": node}

    try:
        kwargs = {
            "query_texts": [query],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        results = col.query(**kwargs)

    except Exception as e:
        raise QueryError(str(e))

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    if not docs:
        print(f'\n  No results found for: "{query}"')
        return

    print(f"\n{'=' * 60}")
    print(f'  Results for: "{query}"')
    if domain:
        print(f"  Domain: {domain}")
    if node:
        print(f"  Node: {node}")
    print(f"{'=' * 60}\n")

    for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists), 1):
        similarity = round(1 - dist, 3)
        source = Path(meta.get("source_file", "?")).name
        domain_name = meta.get("domain", "?")
        node_name = meta.get("node", "?")

        print(f"  [{i}] {domain_name} / {node_name}")
        print(f"      Source: {source}")
        print(f"      Match:  {similarity}")
        print()
        # Print the verbatim text, indented
        for line in doc.strip().split("\n"):
            print(f"      {line}")
        print()
        print(f"  {'─' * 56}")

    print()


def search_memories(
    query: str, vault_path: str, domain: str = None, node: str = None, n_results: int = 5
) -> dict:
    """
    Programmatic query — returns a dict instead of printing.
    Used by the MCP gateway and other callers that need data.
    """
    try:
        client = chromadb.PersistentClient(path=vault_path)
        col = client.get_collection("recallos_records")
    except Exception as e:
        return {"error": f"No Data Vault found at {vault_path}: {e}"}

    # Build where filter
    where = {}
    if domain and node:
        where = {"$and": [{"domain": domain}, {"node": node}]}
    elif domain:
        where = {"domain": domain}
    elif node:
        where = {"node": node}

    try:
        kwargs = {
            "query_texts": [query],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        results = col.query(**kwargs)
    except Exception as e:
        return {"error": f"Query error: {e}"}

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    hits = []
    for doc, meta, dist in zip(docs, metas, dists):
        hits.append(
            {
                "text": doc,
                "domain": meta.get("domain", "unknown"),
                "node": meta.get("node", "unknown"),
                "source_file": Path(meta.get("source_file", "?")).name,
                "similarity": round(1 - dist, 3),
            }
        )

    return {
        "query": query,
        "filters": {"domain": domain, "node": node},
        "results": hits,
    }
