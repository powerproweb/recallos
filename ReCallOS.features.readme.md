# RecallOS v4.0.0 — Complete Feature List

> Local-first AI memory operating system. No API key required. No cloud. No subscription.
> Highest LongMemEval score ever published — free or paid.

---

## 1. Data Vault — Structured Memory Storage

### 1.1 Hierarchical Storage Architecture
- **Domains** — top-level containers for each project, person, or topic. Unlimited domains per vault.
- **Nodes** — named sub-topics within a domain (e.g. `auth-migration`, `billing`, `deploy`). Auto-detected from folder structure or file content. Fully customizable.
- **Channels** — five standardized memory-type routes present in every domain:
  - `channel_facts` — decisions made, choices locked in
  - `channel_events` — sessions, milestones, debugging runs
  - `channel_discoveries` — breakthroughs and new insights
  - `channel_preferences` — habits, likes, opinions
  - `channel_guidance` — recommendations and solutions
- **Index Summaries** — compressed retrieval layers that point to the original content. Fast for AI to read.
- **Source Records** — verbatim original content. Never summarized. Every word preserved.
- **Links** — automatic cross-domain connections when the same Node appears in multiple Domains.

### 1.2 Storage Backend
- Powered by **ChromaDB** (local vector database) — no server required, runs on the user's machine.
- Default vault location: `~/.recallos/vault`
- Configurable via `~/.recallos/config.json` or the `RECALLOS_VAULT_PATH` environment variable.
- Collection name: `recallos_records` (verbatim) + `recallos_encoded` (RecallScript compressed).

### 1.3 Retrieval Performance (Tested on 22,000+ memories)
- Search all summaries: **60.9% R@10**
- Search within domain: **73.1% R@10** (+12%)
- Search domain + channel: **84.8% R@10** (+24%)
- Search domain + node: **94.8% R@10** (+34%)
- Raw LongMemEval R@5: **96.6%** — zero API calls
- Hybrid LongMemEval R@5: **100%** (500/500) — optional Haiku rerank

---

## 2. Ingest Engine — Getting Data In

### 2.1 Project File Ingest (`recallos ingest <dir>`)
- Recursively scans a project directory for all readable files.
- Supported extensions: `.txt`, `.md`, `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.json`, `.yaml`, `.yml`, `.html`, `.css`, `.java`, `.go`, `.rs`, `.rb`, `.sh`, `.csv`, `.sql`, `.toml`
- Chunks files into 800-character records with paragraph-boundary awareness and 100-character overlap.
- Skips already-ingested files (deduplication by source file path).
- Automatically routes each file to the correct Node using a 3-priority detection system:
  1. Folder path contains Node name
  2. Filename matches Node name
  3. Keyword scoring with position weighting (3x for first 500 chars) and light stemming
- Dry-run mode: `--dry-run` previews what would be filed without writing anything.
- Domain override: `--domain <name>` tags all records with a custom domain name.
- File limit: `--limit N` caps the number of files processed.
- RecallScript encoding: `--encode` stores compressed versions simultaneously in `recallos_encoded`.

### 2.2 Conversation Ingest (`recallos ingest <dir> --mode convos`)
- **Exchange-pair chunking** (default): one user turn + AI response = one record unit. Preserves conversational context.
- **General extraction mode** (`--extract general`): auto-classifies chunks into decisions, preferences, milestones, problems, and emotional context.
- **Improved domain detection** using:
  - Bigram patterns (e.g. `pull request`, `stack trace`, `we decided`, `not working`)
  - 2x weight for matches in the first 500 characters (title/lead)
  - Text normalization before scoring (punctuation stripped, whitespace collapsed)
- Skips already-ingested files using pre-loaded source file set (one query, not N queries).
- Batch filing: all chunks per file written in sub-batches of 100 for memory efficiency.

### 2.3 Supported Import Formats (7 total via `normalize.py`)
| Format | Detection Method |
|--------|-----------------|
| Plain text with `>` markers | Passthrough |
| **Claude.ai JSON** | `{"role": "user/assistant", "content": "..."}` |
| **ChatGPT conversations.json** | Mapping tree traversal |
| **Claude Code JSONL** | Line-by-line `{"type": "human/assistant"}` |
| **Slack JSON export** | `[{"type": "message", "user": "...", "text": "..."}]` |
| **Discord JSON export** | Array or `{"messages": [...]}` wrapped schema |
| **Obsidian vault notes** | YAML frontmatter stripped + `[[wikilinks]]` converted |

### 2.4 Transcript Splitter (`recallos split <dir>`)
- Detects concatenated multi-session transcript mega-files.
- Splits into individual per-session files before ingest.
- `--dry-run` preview mode.
- `--min-sessions N` only splits files containing at least N sessions (default: 2).
- `--output-dir` writes split files to a separate directory.

### 2.5 Entity Detection (`recallos init <dir>`)
- Two-pass detection during `init`:
  1. Auto-detect people and projects from file content (entity detector)
  2. Detect nodes from folder structure and filename patterns
- 90+ folder keyword patterns mapped to canonical node names (frontend, backend, docs, design, costs, meetings, team, research, planning, testing, scripts, configuration, etc.)
- Interactive approval flow: accept all, remove, or add nodes manually.
- Saves `recallos.yaml` config and `entities.json` for downstream ingest use.

---

## 3. RecallScript — Compression Dialect

### 3.1 Core Compression
- **30x lossless compression** — same information, 30× fewer tokens.
- No decoder required — any LLM that reads text can interpret it.
- Works with Claude, GPT, Gemini, Llama, Mistral, and any text-reading model.
- Fully offline — no API calls for compression or decompression.

### 3.2 RecallScript Format
- **Entity codes**: 3-letter uppercase (e.g. `ALC=Alice`, `KAI=Kai`, `MAX=Max`)
- **Emotion markers**: `*warm*`, `*fierce*`, `*raw*`, `*bloom*` — emotional context preserved
- **Structure**: pipe-separated fields — `domain: project | node: topic | channel: memory type`
- **Dates**: ISO format (`2026-03-31`)
- **Importance**: ★ to ★★★★★ (1–5 scale)
- **Counts**: `Nx` notation (e.g. `570x` = 570 mentions)

### 3.3 RecallScript CLI (`recallos encode`)
- Encodes existing vault records on demand.
- `--domain <name>` encodes only one domain.
- `--dry-run` previews compression ratios without storing.
- `--config <entities.json>` loads entity code definitions.
- Reports total original vs. compressed token counts and ratio.

### 3.4 Inline Encoding During Ingest
- `recallos ingest --encode` stores both verbatim and RecallScript-compressed versions in the same ingest pass.
- Lazy-imports `Dialect` — zero performance cost when `--encode` is not used.
- Encoded records stored in separate `recallos_encoded` ChromaDB collection.

### 3.5 Auto-Teaching via MCP
- The `RECALL_PROTOCOL` and `RECALLSCRIPT_SPEC` are embedded in the `recallos_status` MCP response.
- AI models learn RecallScript automatically on the first bootstrap call — no manual setup.

---

## 4. Memory Stack — Layered Context Loading

### 4.1 Four-Layer Architecture
| Layer | Name | Size | When Loaded |
|-------|------|------|-------------|
| **L0** | Identity Layer | ~50 tokens | Always — "who is this AI?" |
| **L1** | Core Context Layer | ~120 tokens | Always — team, projects, preferences |
| **L2** | Node Recall Layer | ~200–500 tokens | On demand — when a topic comes up |
| **L3** | Deep Retrieval Layer | Unlimited | On demand — full semantic search |

### 4.2 Bootstrap (`recallos bootstrap`)
- Generates L0 + L1 context (~170 tokens total).
- L0 reads from `~/.recallos/identity_profile.txt` (plain text, user-written).
- L1 auto-generated from highest-importance/most-recent records in the vault. Groups by node, picks top 15 moments, hard cap at 3,200 characters.
- `--domain <name>` generates a project-specific bootstrap.
- Output can be piped into a local model's system prompt.

---

## 5. Recall Graph — Temporal Entity-Relationship Graph

### 5.1 Storage
- SQLite database at `~/.recallos/recall_graph.sqlite3` — local, zero dependencies.
- Two tables: `entities` (id, name, type, properties) and `triples` (subject, predicate, object, valid_from, valid_to, confidence, source_index, source_file).
- Four indexes for fast querying (subject, object, predicate, temporal validity).

### 5.2 Write Operations
- `add_entity(name, type, properties)` — add or update entity nodes with typed properties.
- `add_triple(subject, predicate, object, valid_from, valid_to, confidence, source_index)` — add typed relationships with temporal validity windows.
  - Auto-creates entities if they don't exist.
  - Deduplicates: adding the same active triple twice returns the existing ID.
  - Normalizes predicates (lowercase, underscores).
- `invalidate(subject, predicate, object, ended)` — marks a fact as no longer true by setting `valid_to`.
- `seed_from_entity_facts(entity_facts)` — bulk-seed from a known-facts dictionary.

### 5.3 Query Operations
- `query_entity(name, as_of, direction)` — get all relationships for an entity.
  - `direction`: `outgoing`, `incoming`, or `both`
  - `as_of`: date filter — only return facts valid at that point in time
  - Returns `current` flag (True if `valid_to IS NULL`)
- `query_relationship(predicate, as_of)` — get all triples with a given relationship type.
- `timeline(entity_name)` — chronological story of an entity (or all entities).
- `stats()` — entity count, triple count, current vs. expired facts, relationship types.

### 5.4 Path-Finding
- `find_path(entity_a, entity_b, max_depth, as_of)` — BFS shortest path between two entities.
  - Returns list of `{from, predicate, to}` steps.
  - Returns `[]` for same entity, `None` if no path within max_depth.
  - `max_depth` defaults to 4 hops.
  - Optional `as_of` date filtering.

### 5.5 Export
- `export_dot(current_only)` — Graphviz DOT string. Renders with `dot -Tpng graph.dot`. No graphviz library required — pure string generation.
- `export_json(current_only)` — D3/JS-ready adjacency JSON: `{"nodes": [...], "edges": [...]}`.

### 5.6 Contradiction Detection
- Facts are checked against the Recall Graph before AI responses.
- Ages, dates, and tenures calculated dynamically — not hardcoded.
- Attribution conflicts, wrong tenure, and stale dates are all detectable.

---

## 6. Vault Graph — Navigation Graph

### 6.1 Graph Construction (`build_graph`)
- Built from ChromaDB metadata — no separate storage required.
- Nodes = topic nodes (named ideas) that appear in the vault.
- Edges = nodes that span multiple domains (cross-domain links).
- Edge types = channels (memory type routes).
- Excludes `general` nodes and records with no domain.

### 6.2 Traversal (`traverse`)
- BFS traversal from a starting node across shared domains.
- Returns all connected nodes with hop distance, domains, channels, and count.
- `max_hops` parameter (default: 2).
- Fuzzy match suggestions when start node is not found.
- Capped at 50 results, sorted by hop distance then record count.

### 6.3 Link Discovery (`find_links`)
- Returns all nodes appearing in 2+ domains.
- Optional `domain_a` and `domain_b` filters.
- Shows the "bridges" between different areas of your vault.

### 6.4 Stats (`graph_stats`)
- Total nodes, link nodes (spanning 2+ domains), total edges.
- Nodes per domain breakdown.
- Top-10 most-connected link nodes.

---

## 7. MCP Gateway — 22 Tools for AI Integration

### 7.1 Setup
```bash
claude mcp add recallos -- python -m recallos.mcp_gateway
```
AI learns RecallScript and the memory protocol automatically from `recallos_status`.

### 7.2 Data Vault Read Tools (7)
| Tool | Description |
|------|-------------|
| `recallos_status` | Total records, domain/node counts, RecallScript spec, memory protocol |
| `recallos_list_domains` | All domains with record counts |
| `recallos_list_nodes` | Nodes within a domain (or all nodes) |
| `recallos_get_topology` | Full domain → node → count tree |
| `recallos_query` | Semantic search with domain/node filters, configurable result count |
| `recallos_check_duplicate` | Similarity check before filing (threshold configurable, default 0.9) |
| `recallos_get_recallscript_spec` | RecallScript dialect reference on demand |

### 7.3 Record Write Tools (2)
| Tool | Description |
|------|-------------|
| `recallos_add_record` | File verbatim content (auto-checks duplicates first) |
| `recallos_delete_record` | Remove a record by ID (irreversible) |

### 7.4 Recall Graph Tools (6)
| Tool | Description |
|------|-------------|
| `recallos_graph_query` | Entity relationships with time filtering (direction: outgoing/incoming/both) |
| `recallos_graph_add` | Add a fact (subject → predicate → object + optional valid_from) |
| `recallos_graph_invalidate` | Mark a fact as ended (set valid_to) |
| `recallos_graph_timeline` | Chronological entity story |
| `recallos_graph_stats` | Entity/triple/relationship-type overview |
| `recallos_graph_path` | BFS shortest path between two entities |

### 7.5 Link Navigation Tools (3)
| Tool | Description |
|------|-------------|
| `recallos_traverse_links` | Walk the vault graph from a node across domains |
| `recallos_find_links` | Find nodes bridging two domains |
| `recallos_topology_stats` | Total nodes, link nodes, edges, domain connectivity |

### 7.6 Agent Log Tools (3)
| Tool | Description |
|------|-------------|
| `recallos_log_write` | Write RecallScript log entry (file-backed + ChromaDB) |
| `recallos_log_read` | Read recent entries (file-backed, newest first; ChromaDB fallback) |
| `recallos_log_search` | Keyword grep across full log history |

### 7.7 Memory Protocol (RECALL_PROTOCOL)
Embedded in every `recallos_status` response:
1. On bootstrap: call `recallos_status` to load overview + spec.
2. Before responding about any person/project/event: query vault first. Never guess.
3. If unsure about a fact: say "let me check" and query. Wrong is worse than slow.
4. After each session: call `recallos_log_write` to record what happened.
5. When facts change: invalidate old, add new.

---

## 8. Agent Logs — Persistent AI Journals

### 8.1 File-Backed Storage
- Each agent gets a per-day JSONL file at `~/.recallos/agent_logs/<agent>/YYYY-MM-DD.jsonl`.
- Entries: `{timestamp, date, topic, agent, content, id}`.
- Also writes to ChromaDB for semantic search (best-effort, non-fatal on failure).
- File logs are the primary store — survive vault resets.

### 8.2 Operations
- `write(content, topic)` — appends entry, returns `{entry_id, timestamp, file}`.
- `read(last_n)` — reads N most recent entries across all day files, newest first.
- `search(keyword, max_results)` — case-insensitive grep across all log history.
- `rotate(keep_days)` — deletes log files older than N days (default: 30). Skips files with non-date names.
- `stats()` — log file count, total entries, oldest and newest dates.

---

## 9. Diagnostics — Vault Health (`recallos doctor`)

### 9.1 Seven Health Checks
| Check | Pass | Warn | Fail |
|-------|------|------|------|
| Vault directory | Exists and is a directory | Not found | Exists but is a file |
| ChromaDB collection | `recallos_records` accessible | — | Cannot open |
| Incomplete records | All records have domain+node | Some missing domain/node | — |
| Recall graph SQLite | PRAGMA integrity_check passes | — | File corrupt or unreadable |
| Identity profile | `identity_profile.txt` exists | Not found | — |
| Config file | `config.json` valid JSON | — | Cannot parse |
| Legacy MemPalace | No `~/.mempalace/` | Legacy dir detected | — |

### 9.2 Output
- PASS ✔ / WARN ⚠ / FAIL ✗ / INFO · per check.
- `--verbose` shows detail on all checks, not just warnings/failures.
- Overall status: PASS, WARN, or FAIL.
- Summary line: `N passed · N warnings · N failures · N info`.

---

## 10. Migration — MemPalace → RecallOS (`recallos migrate`)

### 10.1 What Gets Migrated
- **ChromaDB collections**: `mempalace_drawers` → `recallos_records`, `mempalace_encoded` → `recallos_encoded`. Copied in 500-record batches.
- **Knowledge graph**: `~/.mempalace/knowledge_graph.sqlite3` → `~/.recallos/recall_graph.sqlite3`
- **Identity profile**: `~/.mempalace/identity_profile.txt` → `~/.recallos/identity_profile.txt` (skipped if already present)
- **Config**: Legacy key mapping (`palace_path` → `vault_path`, `topic_wings` → `topic_domains`, `hall_keywords` → `channel_keywords`). Never overwrites existing RecallOS config keys.

### 10.2 Flags
- `--dry-run` — preview all steps without making any changes.
- `--force` — overwrite existing RecallOS data.

### 10.3 Backward Compatibility
- `RecallOSConfig` detects `~/.mempalace/` on every init.
- CLI prints a one-time migration reminder before any command (suppressed during `migrate`).
- `ingest_engine` falls back to `mempal.yaml` if `recallos.yaml` is not found.

---

## 11. CLI — Full Command Reference

```
recallos init <dir>                         Detect nodes from folder structure
recallos migrate [--dry-run] [--force]      Migrate from ~/.mempalace/
recallos ingest <dir>                       Ingest project files
recallos ingest <dir> --mode convos         Ingest conversation exports
recallos ingest <dir> --encode              Also store RecallScript versions
recallos ingest <dir> --dry-run             Preview without filing
recallos split <dir> [--dry-run]            Split concatenated transcripts
recallos query "query"                      Semantic search
recallos query "query" --domain <name>      Scoped to one domain
recallos query "query" --node <name>        Scoped to one node
recallos bootstrap                          Load L0 + L1 context (~170 tokens)
recallos bootstrap --domain <name>          Project-specific bootstrap
recallos encode [--domain <name>]           RecallScript encode existing records
recallos encode --dry-run                   Preview compression ratios
recallos status                             Data Vault overview
recallos doctor [--verbose]                 Full vault health report
```
All commands accept `--vault <path>` to override default vault location.

---

## 12. Auto-Save Hooks (Claude Code Integration)

### 12.1 Save Hook (`recallos_save_hook.sh`)
- Fires every 15 messages via Claude Code's `Stop` hook.
- Triggers structured save: topics, decisions, quotes, code changes.
- Regenerates the critical facts layer.

### 12.2 PreCompact Hook (`recallos_precompact_hook.sh`)
- Fires before Claude Code's context compression.
- Emergency save before the context window shrinks.

---

## 13. Configuration System

### 13.1 Load Priority
`env vars > config file > defaults`

### 13.2 Config File (`~/.recallos/config.json`)
- `vault_path` — ChromaDB vault location
- `collection_name` — ChromaDB collection name (default: `recallos_records`)
- `topic_domains` — list of domain names
- `channel_keywords` — keyword lists per channel
- `people_map` — name variant → canonical name mapping

### 13.3 Environment Variables
- `RECALLOS_VAULT_PATH` — overrides vault path

### 13.4 Identity Profile (`~/.recallos/identity_profile.txt`)
- Plain text file. Becomes Layer 0 — loaded every session.
- Describes who the AI is, its traits, the people it works with, and the projects it knows.

---

## 14. Python API

RecallOS is fully importable as a Python package (`pip install recallos`):

```python
from recallos.retrieval_engine import search_memories
from recallos.recall_graph import RecallGraph
from recallos.memory_layers import MemoryStack
from recallos.agent_log import AgentLog
from recallos.vault_graph import build_graph, traverse, find_links
from recallos.recallscript import Dialect
from recallos.normalize import normalize
from recallos.config import RecallOSConfig
```

---

## 15. Quality & Reliability

### 15.1 Test Suite
- **154 tests** across 9 test files, all passing.
- Coverage: `config`, `ingest_engine`, `conversation_ingest`, `normalize` (all 7 parsers), `vault_graph`, `recall_graph`, `agent_log`, `migration`, `diagnostics`.
- Tests never touch real `~/.recallos/` or `~/.mempalace/` directories.
- Windows file-handle cleanup handled explicitly (ChromaDB on Windows requires `del col, client` before `shutil.rmtree`).

### 15.2 CI/CD
- GitHub Actions: Python 3.10, 3.11, 3.12 on ubuntu-latest.
- Lint job: `ruff check .` + `ruff format --check .`
- Both jobs use `pip install -e ".[dev]"` — package installed in editable mode.
- `fail-fast: false` — one version failing doesn't cancel others.

### 15.3 Pre-commit Hooks
- Ruff lint (`--fix`) + Ruff format.
- Trailing whitespace, end-of-file-fixer, YAML/JSON check, merge conflict check, large file guard (500 KB).

---

## 16. Deployment & Distribution

- **Package name**: `recallos` on PyPI
- **Version**: 4.0.0
- **License**: MIT
- **Python**: ≥ 3.9
- **Dependencies**: `chromadb>=0.4.0`, `pyyaml>=6.0`
- **Entry point**: `recallos` CLI
- **Install**: `pip install recallos`
- **PyPI**: https://pypi.org/project/recallos/4.0.0/
- **GitHub**: https://github.com/powerproweb/recallos
