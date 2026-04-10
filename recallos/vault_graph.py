"""
vault_graph.py – Graph traversal layer for RecallOS
====================================================

Builds a navigable graph from the Data Vault structure:
  - Graph nodes = topic nodes (named ideas)
  - Edges = shared nodes across domains (links)
  - Edge types = channels (memory type routes)

Enables queries like:
  "Start at chromadb-setup in domain_code, walk to domain_myproject"
  "Find all nodes connected to riley-college-apps"
  "What topics bridge domain_hardware and domain_myproject?"

No external graph DB needed – built from ChromaDB metadata.
"""

from collections import defaultdict, Counter
from .config import RecallOSConfig

import chromadb


def _get_collection(config=None):
    config = config or RecallOSConfig()
    try:
        client = chromadb.PersistentClient(path=config.vault_path)
        return client.get_collection(config.collection_name)
    except Exception:
        return None


def build_graph(col=None, config=None):
    """
    Build the vault graph from ChromaDB metadata.

    Returns:
        nodes: dict of {node: {domains: set, channels: set, count: int}}
        edges: list of {node, domain_a, domain_b, channel} – one per link crossing
    """
    if col is None:
        col = _get_collection(config)
    if not col:
        return {}, []

    total = col.count()
    node_data = defaultdict(lambda: {"domains": set(), "channels": set(), "count": 0, "dates": set()})

    offset = 0
    while offset < total:
        batch = col.get(limit=1000, offset=offset, include=["metadatas"])
        for meta in batch["metadatas"]:
            node = meta.get("node", "")
            domain = meta.get("domain", "")
            channel = meta.get("channel", "")
            date = meta.get("date", "")
            if node and node != "general" and domain:
                node_data[node]["domains"].add(domain)
                if channel:
                    node_data[node]["channels"].add(channel)
                if date:
                    node_data[node]["dates"].add(date)
                node_data[node]["count"] += 1
        if not batch["ids"]:
            break
        offset += len(batch["ids"])

    # Build edges from nodes that span multiple domains
    edges = []
    for node, data in node_data.items():
        domains = sorted(data["domains"])
        if len(domains) >= 2:
            for i, da in enumerate(domains):
                for db in domains[i + 1 :]:
                    for ch in data["channels"]:
                        edges.append(
                            {
                                "node": node,
                                "domain_a": da,
                                "domain_b": db,
                                "channel": ch,
                                "count": data["count"],
                            }
                        )

    # Convert sets to lists for JSON serialization
    nodes = {}
    for node, data in node_data.items():
        nodes[node] = {
            "domains": sorted(data["domains"]),
            "channels": sorted(data["channels"]),
            "count": data["count"],
            "dates": sorted(data["dates"])[-5:] if data["dates"] else [],
        }

    return nodes, edges


def traverse(start_node: str, col=None, config=None, max_hops: int = 2):
    """
    Walk the graph from a starting room. Find connected rooms
    through shared wings.

    Returns list of paths: [{room, wing, hall, hop_distance}]
    """
    nodes, edges = build_graph(col, config)

    if start_node not in nodes:
        return {
            "error": f"Node {start_node}' not found",
            "suggestions": _fuzzy_match(start_node, nodes),
        }

    start = nodes[start_node]
    visited = {start_node}
    results = [
        {
            "node": start_node,
            "domains": start["domains"],
            "channels": start["channels"],
            "count": start["count"],
            "hop": 0,
        }
    ]

    # BFS traversal
    frontier = [(start_node, 0)]
    while frontier:
        current_node, depth = frontier.pop(0)
        if depth >= max_hops:
            continue

        current = nodes.get(current_node, {})
        current_domains = set(current.get("domains", []))

        # Find all nodes that share a domain with the current node
        for node, data in nodes.items():
            if node in visited:
                continue
            shared_domains = current_domains & set(data["domains"])
            if shared_domains:
                visited.add(node)
                results.append(
                    {
                        "node": node,
                        "domains": data["domains"],
                        "channels": data["channels"],
                        "count": data["count"],
                        "hop": depth + 1,
                        "connected_via": sorted(shared_domains),
                    }
                )
                if depth + 1 < max_hops:
                    frontier.append((node, depth + 1))

    # Sort by relevance (hop distance, then count)
    results.sort(key=lambda x: (x["hop"], -x["count"]))
    return results[:50]  # cap results


def find_links(domain_a: str = None, domain_b: str = None, col=None, config=None):
    """
    Find nodes that connect two domains (or all link nodes if no wings specified).
    These are the "hallways" â€” same named idea appearing in multiple domains.
    """
    nodes, edges = build_graph(col, config)

    links = []
    for node, data in nodes.items():
        domains = data["domains"]
        if len(domains) < 2:
            continue

        if domain_a and domain_a not in domains:
            continue
        if domain_b and domain_b not in domains:
            continue

        links.append(
            {
                "node": node,
                "domains": domains,
                "channels": data["channels"],
                "count": data["count"],
                "recent": data["dates"][-1] if data["dates"] else "",
            }
        )

    links.sort(key=lambda x: -x["count"])
    return links[:50]


def graph_stats(col=None, config=None):
    """Summary statistics about the vault graph."""
    nodes, edges = build_graph(col, config)

    link_nodes = sum(1 for n in nodes.values() if len(n["domains"]) >= 2)
    domain_counts = Counter()
    for data in nodes.values():
        for w in data["domains"]:
            domain_counts[w] += 1

    return {
        "total_nodes": len(nodes),
        "link_nodes": link_nodes,
        "total_edges": len(edges),
        "nodes_per_domain": dict(domain_counts.most_common()),
        "top_links": [
            {"node": n, "domains": d["domains"], "count": d["count"]}
            for n, d in sorted(nodes.items(), key=lambda x: -len(x[1]["domains"]))[:10]
            if len(d["domains"]) >= 2
        ],
    }


def _fuzzy_match(query: str, nodes: dict, n: int = 5):
    """Find nodes that approximately match a query string."""
    query_lower = query.lower()
    scored = []
    for node in nodes:
        # Simple substring matching
        if query_lower in node:
            scored.append((node, 1.0))
        elif any(word in node for word in query_lower.split("-")):
            scored.append((node, 0.5))
    scored.sort(key=lambda x: -x[1])
    return [n for n, _ in scored[:n]]
