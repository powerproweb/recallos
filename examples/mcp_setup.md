# MCP Integration — Claude Code

## Setup

Run the MCP gateway:

```bash
python mcp_gateway.py
```

Or add to Claude Code:

```bash
claude mcp add recallos -- python /path/to/recallos/mcp_gateway.py
```

## Available Tools

**Read tools**
- `recallos_status` — vault stats (domains, nodes, record counts)
- `recallos_query` — semantic search across all records
- `recallos_list_domains` — list all domains in the vault
- `recallos_list_nodes` — list nodes within a domain
- `recallos_get_topology` — full domain → node → count tree
- `recallos_check_duplicate` — check if content already exists
- `recallos_get_recallscript_spec` — get the RecallScript compression spec

**Graph tools**
- `recallos_graph_query` — query entity relationships
- `recallos_graph_add` — add a fact to the knowledge graph
- `recallos_graph_invalidate` — mark a fact as no longer true
- `recallos_graph_timeline` — chronological fact history
- `recallos_graph_stats` — knowledge graph overview

**Traversal tools**
- `recallos_traverse_links` — walk the vault graph from a node
- `recallos_find_links` — find nodes bridging two domains
- `recallos_topology_stats` — vault graph connectivity overview

**Write tools**
- `recallos_add_record` — file verbatim content into a domain/node
- `recallos_delete_record` — remove a record by ID
- `recallos_log_write` — write to agent log (RecallScript format)
- `recallos_log_read` — read recent agent log entries

## Usage in Claude Code

Once configured, Claude Code can search your vault and file memories directly during conversations.
On first use, call `recallos_status` — it loads the vault overview and RecallScript spec in one call.
