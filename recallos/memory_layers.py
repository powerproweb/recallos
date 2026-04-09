#!/usr/bin/env python3
"""
memory_layers.py — 4-Layer Memory Stack for RecallOS
=====================================================

Load only what you need, when you need it.

    Layer 0: Identity Layer      (~100 tokens)       — Always loaded. "Who am I?"
    Layer 1: Core Context Layer  (~500-800 tokens)   — Always loaded. Top moments from the vault.
    Layer 2: Node Recall Layer   (~200-500 each)     — Loaded when a topic/domain comes up.
    Layer 3: Deep Retrieval Layer (unlimited)         — Full ChromaDB semantic search.

Bootstrap cost: ~600-900 tokens (L0+L1). Leaves 95%+ of context free.

Reads directly from ChromaDB (recallos_records)
and ~/.recallos/identity_profile.txt.
"""

import os
import sys
from pathlib import Path
from collections import defaultdict

import chromadb

from .config import RecallOSConfig


# ---------------------------------------------------------------------------
# Layer 0 Ã¢â‚¬â€ Identity
# ---------------------------------------------------------------------------


class Layer0:
    """
    ~100 tokens. Always loaded.
    Reads from ~/.recallos/identity_profile.txt Ã¢â‚¬â€ a plain-text file the user writes.

    Example identity_profile.txt:
        I am Atlas, a personal AI assistant for Alice.
        Traits: warm, direct, remembers everything.
        People: Alice (creator), Bob (Alice's partner).
        Project: A journaling app that helps people process emotions.
    """

    def __init__(self, identity_path: str = None):
        if identity_path is None:
            identity_path = os.path.expanduser("~/.recallos/identity_profile.txt")
        self.path = identity_path
        self._text = None

    def render(self) -> str:
        """Return the identity text, or a sensible default."""
        if self._text is not None:
            return self._text

        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                self._text = f.read().strip()
        else:
            self._text = (
                "## L0 Ã¢â‚¬â€ IDENTITY\nNo identity configured. Create ~/.recallos/identity_profile.txt"
            )

        return self._text

    def token_estimate(self) -> int:
        return len(self.render()) // 4


# ---------------------------------------------------------------------------
# Layer 1 — Core Context (auto-generated from vault)
# ---------------------------------------------------------------------------


class Layer1:
    """
    ~500-800 tokens. Always loaded.
    Auto-generated from the highest-weight / most-recent records in the vault.
    Groups by node, picks the top N moments, compresses to a compact summary.
    """

    MAX_RECORDS = 15  # at most 15 moments in bootstrap
    MAX_CHARS = 3200  # hard cap on total L1 text (~800 tokens)

    def __init__(self, vault_path: str = None, domain: str = None):
        cfg = RecallOSConfig()
        self.vault_path = vault_path or cfg.vault_path
        self.domain = domain

    def generate(self) -> str:
        """Pull top records from ChromaDB and format as compact L1 text."""
        try:
            client = chromadb.PersistentClient(path=self.vault_path)
            col = client.get_collection("recallos_records")
        except Exception:
            return "## L1 Ã¢â‚¬â€ No Data Vault found. Run: recallos ingest <dir>"

        # Fetch all records (with optional domain filter)
        kwargs = {"include": ["documents", "metadatas"]}
        if self.domain:
            kwargs["where"] = {"domain": self.domain}

        try:
            results = col.get(**kwargs)
        except Exception:
            return "## L1 Ã¢â‚¬â€ No records found."

        docs = results.get("documents", [])
        metas = results.get("metadatas", [])

        if not docs:
            return "## L1 Ã¢â‚¬â€ No memories yet."

        # Score each record: prefer high importance, recent filing
        scored = []
        for doc, meta in zip(docs, metas):
            importance = 3
            # Try multiple metadata keys that might carry weight info
            for key in ("importance", "emotional_weight", "weight"):
                val = meta.get(key)
                if val is not None:
                    try:
                        importance = float(val)
                    except (ValueError, TypeError):
                        pass
                    break
            scored.append((importance, meta, doc))

        # Sort by importance descending, take top N
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[: self.MAX_RECORDS]

        # Group by node for readability
        by_node = defaultdict(list)
        for imp, meta, doc in top:
            node = meta.get("node", "general")
            by_node[node].append((imp, meta, doc))

        # Build compact text
        lines = ["## L1 Ã¢â‚¬â€ ESSENTIAL STORY"]

        total_len = 0
        for node, entries in sorted(by_node.items()):
            node_line = f"\n[{node}]"
            lines.append(node_line)
            total_len += len(node_line)

            for imp, meta, doc in entries:
                source = Path(meta.get("source_file", "")).name if meta.get("source_file") else ""

                # Truncate doc to keep L1 compact
                snippet = doc.strip().replace("\n", " ")
                if len(snippet) > 200:
                    snippet = snippet[:197] + "..."

                entry_line = f"  - {snippet}"
                if source:
                    entry_line += f"  ({source})"

                if total_len + len(entry_line) > self.MAX_CHARS:
                    lines.append("  ... (more in L3 retrieval)")
                    return "\n".join(lines)

                lines.append(entry_line)
                total_len += len(entry_line)

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Layer 2 Ã¢â‚¬â€ On-Demand (domain/node filtered retrieval)
# ---------------------------------------------------------------------------


class Layer2:
    """
    ~200-500 tokens per retrieval.
    Loaded when a specific topic or domain comes up in conversation.
    Queries ChromaDB with a domain/node filter.
    """

    def __init__(self, vault_path: str = None):
        cfg = RecallOSConfig()
        self.vault_path = vault_path or cfg.vault_path

    def retrieve(self, domain: str = None, node: str = None, n_results: int = 10) -> str:
        """Retrieve records filtered by domain and/or node."""
        try:
            client = chromadb.PersistentClient(path=self.vault_path)
            col = client.get_collection("recallos_records")
        except Exception:
            return "No Data Vault found."

        where = {}
        if domain and node:
            where = {"$and": [{"domain": domain}, {"node": node}]}
        elif domain:
            where = {"domain": domain}
        elif node:
            where = {"node": node}

        kwargs = {"include": ["documents", "metadatas"], "limit": n_results}
        if where:
            kwargs["where"] = where

        try:
            results = col.get(**kwargs)
        except Exception as e:
            return f"Retrieval error: {e}"

        docs = results.get("documents", [])
        metas = results.get("metadatas", [])

        if not docs:
            label = f"domain={domain}" if domain else ""
            if node:
                label += f" node={node}" if label else f"node={node}"
            return f"No records found for {label}."

        lines = [f"## L2 Ã¢â‚¬â€ ON-DEMAND ({len(docs)} records)"]
        for doc, meta in zip(docs[:n_results], metas[:n_results]):
            node_name = meta.get("node", "?")
            source = Path(meta.get("source_file", "")).name if meta.get("source_file") else ""
            snippet = doc.strip().replace("\n", " ")
            if len(snippet) > 300:
                snippet = snippet[:297] + "..."
            entry = f"  [{node_name}] {snippet}"
            if source:
                entry += f"  ({source})"
            lines.append(entry)

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Layer 3 — Deep Retrieval (full semantic search via ChromaDB)
# ---------------------------------------------------------------------------


class Layer3:
    """
    Unlimited depth. Semantic search against the full Data Vault.
    Reuses retrieval_engine.py logic against recallos_records.
    """

    def __init__(self, vault_path: str = None):
        cfg = RecallOSConfig()
        self.vault_path = vault_path or cfg.vault_path

    def search(self, query: str, domain: str = None, node: str = None, n_results: int = 5) -> str:
        """Semantic search, returns compact result text."""
        try:
            client = chromadb.PersistentClient(path=self.vault_path)
            col = client.get_collection("recallos_records")
        except Exception:
            return "No Data Vault found."

        where = {}
        if domain and node:
            where = {"$and": [{"domain": domain}, {"node": node}]}
        elif domain:
            where = {"domain": domain}
        elif node:
            where = {"node": node}

        kwargs = {
            "query_texts": [query],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        try:
            results = col.query(**kwargs)
        except Exception as e:
            return f"Search error: {e}"

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        if not docs:
            return "No results found."

        lines = [f'## L3 Ã¢â‚¬â€ SEARCH RESULTS for "{query}"']
        for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists), 1):
            similarity = round(1 - dist, 3)
            domain_name = meta.get("domain", "?")
            node_name = meta.get("node", "?")
            source = Path(meta.get("source_file", "")).name if meta.get("source_file") else ""

            snippet = doc.strip().replace("\n", " ")
            if len(snippet) > 300:
                snippet = snippet[:297] + "..."

            lines.append(f"  [{i}] {domain_name}/{node_name} (sim={similarity})")
            lines.append(f"      {snippet}")
            if source:
                lines.append(f"      src: {source}")

        return "\n".join(lines)

    def search_raw(
        self, query: str, domain: str = None, node: str = None, n_results: int = 5
    ) -> list:
        """Return raw dicts instead of formatted text."""
        try:
            client = chromadb.PersistentClient(path=self.vault_path)
            col = client.get_collection("recallos_records")
        except Exception:
            return []

        where = {}
        if domain and node:
            where = {"$and": [{"domain": domain}, {"node": node}]}
        elif domain:
            where = {"domain": domain}
        elif node:
            where = {"node": node}

        kwargs = {
            "query_texts": [query],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        try:
            results = col.query(**kwargs)
        except Exception:
            return []

        hits = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            hits.append(
                {
                    "text": doc,
                    "domain": meta.get("domain", "unknown"),
                    "node": meta.get("node", "unknown"),
                    "source_file": Path(meta.get("source_file", "?")).name,
                    "similarity": round(1 - dist, 3),
                    "metadata": meta,
                }
            )
        return hits


# ---------------------------------------------------------------------------
# MemoryStack Ã¢â‚¬â€ unified interface
# ---------------------------------------------------------------------------


class MemoryStack:
    """
    The full 4-layer stack. One class, one vault, everything works.

        stack = MemoryStack()
        print(stack.bootstrap())                 # L0 + L1 (~600-900 tokens)
        print(stack.recall(domain="my_app"))     # L2 on-demand
        print(stack.search("pricing change"))    # L3 deep retrieval
    """

    def __init__(self, vault_path: str = None, identity_path: str = None):
        cfg = RecallOSConfig()
        self.vault_path = vault_path or cfg.vault_path
        self.identity_path = identity_path or os.path.expanduser("~/.recallos/identity_profile.txt")

        self.l0 = Layer0(self.identity_path)
        self.l1 = Layer1(self.vault_path)
        self.l2 = Layer2(self.vault_path)
        self.l3 = Layer3(self.vault_path)

    def bootstrap(self, domain: str = None) -> str:
        """
        Generate wake-up text: L0 (identity) + L1 (essential story).
        Typically ~600-900 tokens. Inject into system prompt or first message.

        Args:
            domain: Optional domain filter for L1 (project-specific wake-up).
        """
        parts = []

        # L0: Identity
        parts.append(self.l0.render())
        parts.append("")

        # L1: Essential Story
        if domain:
            self.l1.domain = domain
        parts.append(self.l1.generate())

        return "\n".join(parts)

    def recall(self, domain: str = None, node: str = None, n_results: int = 10) -> str:
        """On-demand L2 retrieval filtered by domain/node."""
        return self.l2.retrieve(domain=domain, node=node, n_results=n_results)

    def search(self, query: str, domain: str = None, node: str = None, n_results: int = 5) -> str:
        """Deep L3 semantic search."""
        return self.l3.search(query, domain=domain, node=node, n_results=n_results)

    def status(self) -> dict:
        """Status of all layers."""
        result = {
            "vault_path": self.vault_path,
            "L0_identity": {
                "path": self.identity_path,
                "exists": os.path.exists(self.identity_path),
                "tokens": self.l0.token_estimate(),
            },
            "L1_essential": {
                "description": "Auto-generated from top vault records",
            },
            "L2_on_demand": {
                "description": "domain/node filtered retrieval",
            },
            "L3_deep_search": {
                "description": "Full semantic search via ChromaDB",
            },
        }

        # Count records
        try:
            client = chromadb.PersistentClient(path=self.vault_path)
            col = client.get_collection("recallos_records")
            count = col.count()
            result["total_records"] = count
        except Exception:
            result["total_records"] = 0

        return result


# ---------------------------------------------------------------------------
# CLI (standalone)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    def usage():
        print("memory_layers.py — 4-Layer Memory Stack")
        print()
        print("Usage:")
        print("  python memory_layers.py bootstrap              Show L0 + L1")
        print("  python memory_layers.py bootstrap --domain=NAME  Bootstrap for a specific project")
        print("  python memory_layers.py recall --domain=NAME      On-demand L2 retrieval")
        print("  python memory_layers.py search <query>            Deep L3 retrieval")
        print("  python memory_layers.py status                    Show layer status")
        sys.exit(0)

    if len(sys.argv) < 2:
        usage()

    cmd = sys.argv[1]

    # Parse flags
    flags = {}
    positional = []
    for arg in sys.argv[2:]:
        if arg.startswith("--") and "=" in arg:
            key, val = arg.split("=", 1)
            flags[key.lstrip("-")] = val
        elif not arg.startswith("--"):
            positional.append(arg)

    vault_path = flags.get("vault")
    stack = MemoryStack(vault_path=vault_path)

    if cmd in ("bootstrap", "wake-up", "wakeup"):
        domain = flags.get("domain")
        text = stack.bootstrap(domain=domain)
        tokens = len(text) // 4
        print(f"Wake-up text (~{tokens} tokens):")
        print("=" * 50)
        print(text)

    elif cmd == "recall":
        domain = flags.get("domain")
        node = flags.get("node")
        text = stack.recall(domain=domain, node=node)
        print(text)

    elif cmd == "search":
        query = " ".join(positional) if positional else ""
        if not query:
            print("Usage: python layers.py search <query>")
            sys.exit(1)
        domain = flags.get("domain")
        node = flags.get("node")
        text = stack.search(query, domain=domain, node=node)
        print(text)

    elif cmd == "status":
        s = stack.status()
        print(json.dumps(s, indent=2))

    else:
        usage()
