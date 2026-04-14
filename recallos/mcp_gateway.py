#!/usr/bin/env python3
"""
RecallOS MCP Gateway — read/write Data Vault access for Claude Code
====================================================================
Install: claude mcp add recallos -- python /path/to/mcp_gateway.py

Tools (read):
  recallos_status           — total records, domain/node breakdown
  recallos_list_domains     — all domains with record counts
  recallos_list_nodes       — nodes within a domain
  recallos_get_topology     — full domain → node → count tree
  recallos_query            — semantic search, optional domain/node filter
  recallos_check_duplicate  — check if content already exists before filing

Tools (write):
  recallos_add_record       — file verbatim content into a domain/node
  recallos_delete_record    — remove a record by ID
"""

import sys
import json
import logging
import hashlib
from datetime import datetime

from .config import RecallOSConfig
from .retrieval_engine import search_memories
from .vault_graph import traverse, find_links, graph_stats
import chromadb

from .agent_log import AgentLog
from .recall_graph import RecallGraph

_rg = RecallGraph()

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
logger = logging.getLogger("recallos_mcp")

_config = RecallOSConfig()


def _get_collection(create=False):
    """Return the ChromaDB collection, or None on failure."""
    try:
        client = chromadb.PersistentClient(path=_config.vault_path)
        if create:
            return client.get_or_create_collection(_config.collection_name)
        return client.get_collection(_config.collection_name)
    except Exception:
        return None


def _no_vault():
    return {
        "error": "No Data Vault found",
        "vault_path": _config.vault_path,
        "hint": "Run: recallos init <dir> && recallos ingest <dir>",
    }


# ==================== READ TOOLS ====================


def tool_status():
    col = _get_collection()
    if not col:
        return _no_vault()
    count = col.count()
    domains = {}
    nodes = {}
    try:
        all_meta = col.get(include=["metadatas"])["metadatas"]
        for m in all_meta:
            d = m.get("domain", "unknown")
            n = m.get("node", "unknown")
            domains[d] = domains.get(d, 0) + 1
            nodes[n] = nodes.get(n, 0) + 1
    except Exception:
        pass
    return {
        "total_records": count,
        "domains": domains,
        "nodes": nodes,
        "vault_path": _config.vault_path,
        "protocol": RECALL_PROTOCOL,
        "recallscript_spec": RECALLSCRIPT_SPEC,
    }


# ── RecallScript Spec ────────────────────────────────────────────────────────
# Included in status response so the AI learns it on first bootstrap call.
# Also available via recallos_get_recallscript_spec tool.

RECALL_PROTOCOL = """IMPORTANT — RecallOS Memory Protocol:
1. ON BOOTSTRAP: Call recallos_status to load vault overview + RecallScript spec.
2. BEFORE RESPONDING about any person, project, or past event: call recallos_graph_query or recallos_query FIRST. Never guess — verify.
3. IF UNSURE about a fact (name, gender, age, relationship): say "let me check" and query the vault. Wrong is worse than slow.
4. AFTER EACH SESSION: call recallos_log_write to record what happened, what you learned, what matters.
5. WHEN FACTS CHANGE: call recallos_graph_invalidate on the old fact, recallos_graph_add for the new one.

This protocol ensures the AI KNOWS before it speaks. Storage is not memory — but storage + this protocol = memory."""

RECALLSCRIPT_SPEC = """RecallScript is a compressed memory dialect that RecallOS uses for efficient storage.
It is designed to be readable by both humans and LLMs without decoding.

FORMAT:
  ENTITIES: 3-letter uppercase codes. ALC=Alice, JOR=Jordan, RIL=Riley, MAX=Max, BEN=Ben.
  EMOTIONS: *action markers* before/during text. *warm*=joy, *fierce*=determined, *raw*=vulnerable, *bloom*=tenderness.
  STRUCTURE: Pipe-separated fields. domain: project | node: topic | channel: memory type.
  DATES: ISO format (2026-03-31). COUNTS: Nx = N mentions (e.g., 570x).
  IMPORTANCE: ★ to ★★★★★ (1-5 scale).
  CHANNELS: channel_facts, channel_events, channel_discoveries, channel_preferences, channel_guidance.
  DOMAINS: domain_user, domain_agent, domain_team, domain_code, domain_myproject.
  NODES: Hyphenated slugs representing named ideas (e.g., chromadb-setup, gpu-pricing).

EXAMPLE:
  FAM: ALC→♡JOR | 2D(kids): RIL(18,sports) MAX(11,chess+swimming) | BEN(contributor)

Read RecallScript naturally — expand codes mentally, treat *markers* as emotional context.
When WRITING RecallScript: use entity codes, mark emotions, keep structure tight."""


def tool_list_domains():
    col = _get_collection()
    if not col:
        return _no_vault()
    domains = {}
    try:
        all_meta = col.get(include=["metadatas"])["metadatas"]
        for m in all_meta:
            d = m.get("domain", "unknown")
            domains[d] = domains.get(d, 0) + 1
    except Exception:
        pass
    return {"domains": domains}


def tool_list_nodes(domain: str = None):
    col = _get_collection()
    if not col:
        return _no_vault()
    nodes = {}
    try:
        kwargs = {"include": ["metadatas"]}
        if domain:
            kwargs["where"] = {"domain": domain}
        all_meta = col.get(**kwargs)["metadatas"]
        for m in all_meta:
            n = m.get("node", "unknown")
            nodes[n] = nodes.get(n, 0) + 1
    except Exception:
        pass
    return {"domain": domain or "all", "nodes": nodes}


def tool_get_topology():
    col = _get_collection()
    if not col:
        return _no_vault()
    topology = {}
    try:
        all_meta = col.get(include=["metadatas"])["metadatas"]
        for m in all_meta:
            d = m.get("domain", "unknown")
            n = m.get("node", "unknown")
            if d not in topology:
                topology[d] = {}
            topology[d][n] = topology[d].get(n, 0) + 1
    except Exception:
        pass
    return {"topology": topology}


def tool_query(query: str, limit: int = 5, domain: str = None, node: str = None):
    return search_memories(
        query,
        vault_path=_config.vault_path,
        domain=domain,
        node=node,
        n_results=limit,
    )


def tool_check_duplicate(content: str, threshold: float = 0.9):
    col = _get_collection()
    if not col:
        return _no_vault()
    try:
        results = col.query(
            query_texts=[content],
            n_results=5,
            include=["metadatas", "documents", "distances"],
        )
        duplicates = []
        if results["ids"] and results["ids"][0]:
            for i, record_id in enumerate(results["ids"][0]):
                dist = results["distances"][0][i]
                similarity = round(1 - dist, 3)
                if similarity >= threshold:
                    meta = results["metadatas"][0][i]
                    doc = results["documents"][0][i]
                    duplicates.append(
                        {
                            "id": record_id,
                            "domain": meta.get("domain", "?"),
                            "node": meta.get("node", "?"),
                            "similarity": similarity,
                            "content": doc[:200] + "..." if len(doc) > 200 else doc,
                        }
                    )
        return {
            "is_duplicate": len(duplicates) > 0,
            "matches": duplicates,
        }
    except Exception as e:
        return {"error": str(e)}


def tool_get_recallscript_spec():
    """Return the RecallScript dialect specification."""
    return {"recallscript_spec": RECALLSCRIPT_SPEC}


def tool_traverse_links(start_node: str, max_hops: int = 2):
    """Walk the vault graph from a node. Find connected ideas across domains."""
    col = _get_collection()
    if not col:
        return _no_vault()
    return traverse(start_node, col=col, max_hops=max_hops)


def tool_find_links(domain_a: str = None, domain_b: str = None):
    """Find nodes that bridge two domains — the connections between different areas."""
    col = _get_collection()
    if not col:
        return _no_vault()
    return find_links(domain_a, domain_b, col=col)


def tool_topology_stats():
    """Vault graph overview: nodes, links, edges, connectivity."""
    col = _get_collection()
    if not col:
        return _no_vault()
    return graph_stats(col=col)


# ==================== WRITE TOOLS ====================


def tool_add_record(
    domain: str, node: str, content: str, source_file: str = None, added_by: str = "mcp"
):
    """File verbatim content into a domain/node. Checks for duplicates first."""
    col = _get_collection(create=True)
    if not col:
        return _no_vault()

    # Duplicate check
    dup = tool_check_duplicate(content, threshold=0.9)
    if dup.get("is_duplicate"):
        return {
            "success": False,
            "reason": "duplicate",
            "matches": dup["matches"],
        }

    record_id = f"record_{domain}_{node}_{hashlib.md5((content[:100] + datetime.now().isoformat()).encode()).hexdigest()[:16]}"

    try:
        col.add(
            ids=[record_id],
            documents=[content],
            metadatas=[
                {
                    "domain": domain,
                    "node": node,
                    "source_file": source_file or "",
                    "chunk_index": 0,
                    "added_by": added_by,
                    "filed_at": datetime.now().isoformat(),
                }
            ],
        )
        logger.info(f"Filed record: {record_id} → {domain}/{node}")
        return {"success": True, "record_id": record_id, "domain": domain, "node": node}
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_delete_record(record_id: str):
    """Delete a single record by ID."""
    col = _get_collection()
    if not col:
        return _no_vault()
    existing = col.get(ids=[record_id])
    if not existing["ids"]:
        return {"success": False, "error": f"Record not found: {record_id}"}
    try:
        col.delete(ids=[record_id])
        logger.info(f"Deleted record: {record_id}")
        return {"success": True, "record_id": record_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== KNOWLEDGE GRAPH ====================


def tool_graph_query(entity: str, as_of: str = None, direction: str = "both"):
    """Query the knowledge graph for an entity's relationships."""
    results = _rg.query_entity(entity, as_of=as_of, direction=direction)
    return {"entity": entity, "as_of": as_of, "facts": results, "count": len(results)}


def tool_graph_add(
    subject: str, predicate: str, object: str, valid_from: str = None, source_record: str = None
):
    """Add a relationship to the knowledge graph."""
    triple_id = _rg.add_triple(
        subject, predicate, object, valid_from=valid_from, source_index=source_record
    )
    return {"success": True, "triple_id": triple_id, "fact": f"{subject} → {predicate} → {object}"}


def tool_graph_path(entity_a: str, entity_b: str, max_depth: int = 4):
    """Find the shortest relationship path between two entities in the knowledge graph."""
    path = _rg.find_path(entity_a, entity_b, max_depth=max_depth)
    if path is None:
        return {
            "entity_a": entity_a,
            "entity_b": entity_b,
            "path": None,
            "message": f"No path found between '{entity_a}' and '{entity_b}' within {max_depth} hops.",
        }
    if path == []:
        return {
            "entity_a": entity_a,
            "entity_b": entity_b,
            "path": [],
            "message": "Same entity.",
        }
    return {
        "entity_a": entity_a,
        "entity_b": entity_b,
        "hops": len(path),
        "path": path,
    }


def tool_graph_invalidate(subject: str, predicate: str, object: str, ended: str = None):
    """Mark a fact as no longer true (set end date)."""
    _rg.invalidate(subject, predicate, object, ended=ended)
    return {
        "success": True,
        "fact": f"{subject} → {predicate} → {object}",
        "ended": ended or "today",
    }


def tool_graph_timeline(entity: str = None):
    """Get chronological timeline of facts, optionally for one entity."""
    results = _rg.timeline(entity)
    return {"entity": entity or "all", "timeline": results, "count": len(results)}


def tool_graph_stats():
    """Knowledge graph overview: entities, triples, relationship types."""
    return _rg.stats()


# ==================== AGENT LOG ====================


def tool_log_write(agent_name: str, entry: str, topic: str = "general"):
    """
    Write an agent log entry. Persisted to file (~/.recallos/agent_logs/)
    and ChromaDB. This is the agent's personal journal.
    """
    log = AgentLog(agent_name, vault_path=_config.vault_path)
    result = log.write(content=entry, topic=topic)
    logger.info(f"Log entry: {result['entry_id']} (file: {result['file']})")
    return {
        "success": True,
        "entry_id": result["entry_id"],
        "agent": agent_name,
        "topic": topic,
        "timestamp": result["timestamp"],
        "file": result["file"],
    }


def tool_log_read(agent_name: str, last_n: int = 10):
    """
    Read an agent's recent log entries (file-backed, newest first).
    Falls back to ChromaDB if no file logs exist.
    """
    log = AgentLog(agent_name, vault_path=_config.vault_path)
    entries = log.read(last_n=last_n)

    # Fall back to ChromaDB if no file entries exist
    if not entries:
        col = _get_collection()
        if col:
            domain = f"domain_{agent_name.lower().replace(' ', '_')}"
            try:
                results = col.get(
                    where={"$and": [{"domain": domain}, {"node": "agent_log"}]},
                    include=["documents", "metadatas"],
                )
                for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
                    entries.append(
                        {
                            "date": meta.get("date", ""),
                            "timestamp": meta.get("filed_at", ""),
                            "topic": meta.get("topic", ""),
                            "content": doc,
                        }
                    )
                entries.sort(key=lambda x: x["timestamp"], reverse=True)
                entries = entries[:last_n]
            except Exception:
                pass

    if not entries:
        return {"agent": agent_name, "entries": [], "message": "No log entries yet."}

    stats = log.stats()
    return {
        "agent": agent_name,
        "entries": entries,
        "total_on_file": stats["total_entries"],
        "showing": len(entries),
    }


def tool_log_search(agent_name: str, keyword: str, max_results: int = 20):
    """
    Keyword search across an agent's file-backed log entries.
    Case-insensitive. Searches all days of logs.
    """
    log = AgentLog(agent_name)
    matches = log.search(keyword, max_results=max_results)
    return {
        "agent": agent_name,
        "keyword": keyword,
        "matches": matches,
        "count": len(matches),
    }


# ==================== MCP PROTOCOL ====================

TOOLS = {
    "recallos_status": {
        "description": "Vault overview — total records, domain and node counts",
        "input_schema": {"type": "object", "properties": {}},
        "handler": tool_status,
    },
    "recallos_list_domains": {
        "description": "List all domains with record counts",
        "input_schema": {"type": "object", "properties": {}},
        "handler": tool_list_domains,
    },
    "recallos_list_nodes": {
        "description": "List nodes within a domain (or all nodes if no domain given)",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain to list nodes for (optional)"},
            },
        },
        "handler": tool_list_nodes,
    },
    "recallos_get_topology": {
        "description": "Full topology: domain → node → record count",
        "input_schema": {"type": "object", "properties": {}},
        "handler": tool_get_topology,
    },
    "recallos_get_recallscript_spec": {
        "description": "Get the RecallScript dialect specification — the compressed memory format RecallOS uses. Call this if you need to read or write RecallScript-compressed memories.",
        "input_schema": {"type": "object", "properties": {}},
        "handler": tool_get_recallscript_spec,
    },
    "recallos_graph_query": {
        "description": "Query the knowledge graph for an entity's relationships. Returns typed facts with temporal validity. E.g. 'Max' → child_of Alice, loves chess, does swimming. Filter by date with as_of to see what was true at a point in time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity": {
                    "type": "string",
                    "description": "Entity to query (e.g. 'Max', 'MyProject', 'Alice')",
                },
                "as_of": {
                    "type": "string",
                    "description": "Date filter — only facts valid at this date (YYYY-MM-DD, optional)",
                },
                "direction": {
                    "type": "string",
                    "description": "outgoing (entity→?), incoming (?→entity), or both (default: both)",
                },
            },
            "required": ["entity"],
        },
        "handler": tool_graph_query,
    },
    "recallos_graph_add": {
        "description": "Add a fact to the knowledge graph. Subject → predicate → object with optional time window. E.g. ('Max', 'started_school', 'Year 7', valid_from='2026-09-01').",
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "The entity doing/being something"},
                "predicate": {
                    "type": "string",
                    "description": "The relationship type (e.g. 'loves', 'works_on', 'daughter_of')",
                },
                "object": {"type": "string", "description": "The entity being connected to"},
                "valid_from": {
                    "type": "string",
                    "description": "When this became true (YYYY-MM-DD, optional)",
                },
                "source_record": {
                    "type": "string",
                    "description": "Record ID where this fact appears (optional)",
                },
            },
            "required": ["subject", "predicate", "object"],
        },
        "handler": tool_graph_add,
    },
    "recallos_graph_invalidate": {
        "description": "Mark a fact as no longer true. E.g. ankle injury resolved, job ended, moved house.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "Entity"},
                "predicate": {"type": "string", "description": "Relationship"},
                "object": {"type": "string", "description": "Connected entity"},
                "ended": {
                    "type": "string",
                    "description": "When it stopped being true (YYYY-MM-DD, default: today)",
                },
            },
            "required": ["subject", "predicate", "object"],
        },
        "handler": tool_graph_invalidate,
    },
    "recallos_graph_timeline": {
        "description": "Chronological timeline of facts. Shows the story of an entity (or everything) in order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity": {
                    "type": "string",
                    "description": "Entity to get timeline for (optional — omit for full timeline)",
                },
            },
        },
        "handler": tool_graph_timeline,
    },
    "recallos_graph_stats": {
        "description": "Knowledge graph overview: entities, triples, current vs expired facts, relationship types.",
        "input_schema": {"type": "object", "properties": {}},
        "handler": tool_graph_stats,
    },
    "recallos_graph_path": {
        "description": "Find the shortest relationship path between two entities in the knowledge graph. E.g. how is 'Max' connected to 'Chess'? Returns each hop as subject → predicate → object.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_a": {"type": "string", "description": "Starting entity"},
                "entity_b": {"type": "string", "description": "Target entity"},
                "max_depth": {
                    "type": "integer",
                    "description": "Max hops to search (default: 4)",
                },
            },
            "required": ["entity_a", "entity_b"],
        },
        "handler": tool_graph_path,
    },
    "recallos_traverse_links": {
        "description": "Walk the vault graph from a node. Shows connected ideas across domains — the links. Like following a thread: start at 'chromadb-setup' in domain_code, discover it connects to domain_myproject (planning) and domain_user (feelings about it).",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_node": {
                    "type": "string",
                    "description": "Node to start from (e.g. 'chromadb-setup', 'riley-school')",
                },
                "max_hops": {
                    "type": "integer",
                    "description": "How many connections to follow (default: 2)",
                },
            },
            "required": ["start_node"],
        },
        "handler": tool_traverse_links,
    },
    "recallos_find_links": {
        "description": "Find nodes that bridge two domains. E.g. what topics connect domain_code to domain_team?",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain_a": {"type": "string", "description": "First domain (optional)"},
                "domain_b": {"type": "string", "description": "Second domain (optional)"},
            },
        },
        "handler": tool_find_links,
    },
    "recallos_topology_stats": {
        "description": "Vault graph overview: total nodes, link connections, edges between domains.",
        "input_schema": {"type": "object", "properties": {}},
        "handler": tool_topology_stats,
    },
    "recallos_query": {
        "description": "Semantic search. Returns verbatim record content with similarity scores.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for"},
                "limit": {"type": "integer", "description": "Max results (default 5)"},
                "domain": {"type": "string", "description": "Filter by domain (optional)"},
                "node": {"type": "string", "description": "Filter by node (optional)"},
            },
            "required": ["query"],
        },
        "handler": tool_query,
    },
    "recallos_check_duplicate": {
        "description": "Check if content already exists in the vault before filing",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Content to check"},
                "threshold": {
                    "type": "number",
                    "description": "Similarity threshold 0-1 (default 0.9)",
                },
            },
            "required": ["content"],
        },
        "handler": tool_check_duplicate,
    },
    "recallos_add_record": {
        "description": "File verbatim content into the vault. Checks for duplicates first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain (project name)"},
                "node": {
                    "type": "string",
                    "description": "Node (aspect: backend, decisions, meetings...)",
                },
                "content": {
                    "type": "string",
                    "description": "Verbatim content to store — exact words, never summarized",
                },
                "source_file": {"type": "string", "description": "Where this came from (optional)"},
                "added_by": {"type": "string", "description": "Who is filing this (default: mcp)"},
            },
            "required": ["domain", "node", "content"],
        },
        "handler": tool_add_record,
    },
    "recallos_delete_record": {
        "description": "Delete a record by ID. Irreversible.",
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "description": "ID of the record to delete"},
            },
            "required": ["record_id"],
        },
        "handler": tool_delete_record,
    },
    "recallos_log_write": {
        "description": "Write to your personal agent log in RecallScript format. Your observations, thoughts, what you worked on, what matters. Each agent has their own log with full history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "Your name — each agent gets their own log domain",
                },
                "entry": {
                    "type": "string",
                    "description": "Your log entry in RecallScript format — compressed, entity-coded, emotion-marked",
                },
                "topic": {
                    "type": "string",
                    "description": "Topic tag (optional, default: general)",
                },
            },
            "required": ["agent_name", "entry"],
        },
        "handler": tool_log_write,
    },
    "recallos_log_read": {
        "description": "Read your recent agent log entries (in RecallScript). See what past versions of yourself recorded — your journal across sessions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "Your name — each agent gets their own log domain",
                },
                "last_n": {
                    "type": "integer",
                    "description": "Number of recent entries to read (default: 10)",
                },
            },
            "required": ["agent_name"],
        },
        "handler": tool_log_read,
    },
    "recallos_log_search": {
        "description": "Keyword search across your agent log history. Case-insensitive grep across all days of recorded entries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "Your name",
                },
                "keyword": {
                    "type": "string",
                    "description": "Word or phrase to search for in your log history",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Max matching entries to return (default: 20)",
                },
            },
            "required": ["agent_name", "keyword"],
        },
        "handler": tool_log_search,
    },
}


def handle_request(request):
    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "recallos", "version": "4.1.0"},
            },
        }
    elif method == "notifications/initialized":
        return None
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {"name": n, "description": t["description"], "inputSchema": t["input_schema"]}
                    for n, t in TOOLS.items()
                ]
            },
        }
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        if tool_name not in TOOLS:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
            }
        try:
            result = TOOLS[tool_name]["handler"](**tool_args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]},
            }
        except Exception as e:
            logger.error(f"Tool error in {tool_name}: {e}")
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": str(e)}}

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }


def main():
    logger.info("RecallOS MCP Gateway starting...")
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            request = json.loads(line)
            response = handle_request(request)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Server error: {e}")


if __name__ == "__main__":
    main()
