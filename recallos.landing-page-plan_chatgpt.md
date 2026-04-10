# Landing Page Plan
> *Last updated: 4/10/2026, 7:48:00 AM*

**You** *(4/10/2026, 7:40:59 AM)*

read the files and give me a plan for a landing page that is easy to understand (5th grade level wording). I want it to have 2 long scrolling pages - one for the Features and the other for the User Benefits. Color palet is dark maroons and deep blues with gold and turquoise accents and trim - lets start there and improve as we go

---

**Deep Research** *(4/10/2026, 7:40:59 AM)*

Make sure to include fileciteturn0file0 in your response to cite this file, or to surface it as a link.
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

---

**Deep Research** *(4/10/2026, 7:40:59 AM)*

Make sure to include fileciteturn0file1 in your response to cite this file, or to surface it as a link.
# RecallOS — What It Does For You

> *Your AI remembers everything. You never repeat yourself. Nothing gets lost.*

---

## The Problem It Solves

Every time you start a new session with an AI — whether that's Claude, ChatGPT, Cursor, or a local Llama model — it has no memory of anything you've discussed before. Every decision, every reason, every "we tried X and it broke because Y" is gone. You spend the first 10 minutes of every session re-explaining your project, your team, your stack, and your preferences.

Six months of daily AI use generates roughly 19.5 million tokens of conversation. That's every architecture debate, every debugging session, every product decision — completely inaccessible the next day.

RecallOS fixes this. Permanently. Locally. For free.

---

## What RecallOS Does For You — In Plain English

### You Never Lose a Decision Again

Every conversation you've had, every project file you've written, every Slack export or chat transcript — RecallOS ingests it all and stores it in a structured, searchable vault on your machine. The original words are never summarized away. Six months from now, you can ask:

> *"Why did we choose Postgres over SQLite for this project?"*

And RecallOS will return the exact conversation where that decision was made, word for word, with the date and who said it.

---

### Your AI Starts Every Session Knowing Your World

Instead of re-explaining everything at the start of each session, RecallOS generates a tiny bootstrap context (~170 tokens) that tells your AI:
- Who you are and how this AI should behave
- Your current projects and team
- The most important recent decisions and facts

170 tokens is less than half a paragraph. Your AI loads your entire world before you type a single question.

---

### Your AI Gets Smarter Over Time — Without Any Cloud

RecallOS is not a cloud service. There is no subscription. There is no API key. Everything lives on your machine — your conversations, your code, your memories. You can run it entirely offline against a local Llama or Mistral model and it works identically.

As you use RecallOS more, it gets better — more data, more context, smarter retrieval. It compounds. The more you feed it, the more useful it becomes.

---

### You Can Import Everything You Already Have

RecallOS reads 7 different formats out of the box:
- **Claude.ai** conversation exports
- **ChatGPT** `conversations.json`
- **Claude Code** JSONL session files
- **Slack** JSON exports
- **Discord** JSON exports (from DiscordChatExporter)
- **Obsidian** vault notes (strips frontmatter, converts wikilinks)
- **Plain text** transcripts

You don't need to reformat anything. Point RecallOS at a folder, and it figures out what everything is.

---

### Your AI Can Verify Facts Before It Speaks

RecallOS includes a Recall Graph — a local database of facts about people, projects, and decisions, each with a time window showing when they were true. Your AI can check this graph before answering:

- *"Kai has been here 2 years"* → ⚠ Wrong. Records show 3 years (started 2023-04).
- *"Soren finished the migration"* → 🔴 Attribution conflict — Maya was assigned, not Soren.
- *"The sprint ends Friday"* → ⚠ Stale date — current sprint ends Thursday (updated 2 days ago).

Facts change. RecallOS tracks that. Your AI stops confidently saying wrong things.

---

### You Stop Paying Thousands Per Year for AI Memory

| Approach | Annual Cost |
|----------|-------------|
| Paste everything into context | Impossible (doesn't fit) |
| LLM-generated summaries | ~$507/yr |
| **RecallOS** | **~$0.70–$10/yr** |
| Mem0 (cloud) | $19–$249/mo |
| Zep (cloud) | $25+/mo |

RecallOS costs almost nothing because it doesn't call any API to compress, store, or retrieve your memories. Everything runs locally.

---

## Specific Things You Can Do With RecallOS

### As a Solo Developer

**Remember why you made every decision across every project.**
```
recallos query "why did we switch to GraphQL" --domain orion
→ "We switched because REST API versioning was becoming unmaintainable.
   Decided 2025-11-15. See session orion-2025-11-15.md."
```

**Ask cross-project questions.**
```
recallos query "how did I handle rate limiting"
→ finds your solution in three different projects, shows the differences
```

**Resume any project instantly, even after months away.**
```
recallos bootstrap --domain helios
→ "L0: I am your dev assistant for Helios...
   L1: [auth-migration, billing refactor, deploy pipeline — all current states]"
```

---

### As a Team Lead

**Know what every team member worked on without asking them.**
```
recallos query "Soren sprint work" --domain driftwood
→ 14 summaries: OAuth refactor, dark mode, component library migration
```

**Onboard new team members instantly.**
Give them a `recallos bootstrap` dump and they have months of project context in seconds.

**Never lose a meeting decision.**
Import your Slack exports, and every decision your team made in Slack is searchable forever.

---

### With Claude Code or Any MCP-Compatible AI

Connect RecallOS once:
```bash
claude mcp add recallos -- python -m recallos.mcp_gateway
```

Then just talk to your AI normally. When you ask about a past decision, Claude calls `recallos_query` automatically and gets the answer. You never type `recallos` manually again — the AI handles it.

Your AI also:
- Writes a session log after every conversation (`recallos_log_write`)
- Reads its own history at the start of each session (`recallos_log_read`)
- Updates the Recall Graph when facts change (`recallos_graph_add`, `recallos_graph_invalidate`)
- Checks for duplicates before filing anything new (`recallos_check_duplicate`)

---

### With Local Models (Llama, Mistral, Any Offline LLM)

Generate a bootstrap context and paste it into your model's system prompt:
```bash
recallos bootstrap > context.txt
```

Or query on demand and include results in your prompt:
```bash
recallos query "auth decisions" > results.txt
```

Everything stays on your machine. No API calls, no data leaving your computer.

---

### For Managing Long-Running AI Agents

Create specialist agents that remember their entire work history:

```
reviewer agent  — remembers every bug pattern it has ever found
architect agent — remembers every design decision it has made
ops agent       — remembers every incident and how it was resolved
```

Each agent has its own daily log file at `~/.recallos/agent_logs/<agent>/`. These logs persist across sessions, are searchable by keyword, and automatically rotate after 30 days.

---

## The "Set It and Forget It" Workflow

Once RecallOS is set up, you largely stop thinking about it:

1. **One-time setup** (`recallos init <dir>`) — 2 minutes
2. **One-time ingest** (`recallos ingest <dir>`) — runs in the background
3. **One-time MCP connection** (`claude mcp add recallos ...`) — one command
4. **That's it** — your AI queries RecallOS automatically from that point on

For new conversations, new projects, or new chat exports — run `recallos ingest` again. New data goes into the same vault. Old data stays intact.

For Claude Code users, the save hooks run automatically every 15 messages and before context compression — you never need to manually save anything.

---

## What RecallOS Does NOT Do

Being clear about limitations is important:

- **It does not summarize your data.** It stores everything verbatim. This is intentional — summaries lose the *why*.
- **It does not modify your files.** It reads and indexes; your original files are untouched.
- **It does not require internet access.** It works entirely offline.
- **It does not decide what matters.** Structure (domains + nodes) drives retrieval — no AI curation of what gets kept.
- **It does not sync between machines.** The vault is local. If you want multi-machine sync, copy `~/.recallos/` yourself.
- **It is not a general-purpose database.** It is optimized specifically for AI memory workloads.

---

## Health and Safety of Your Data

### `recallos doctor`
Run at any time to check your vault:
- Is the vault directory accessible?
- Is ChromaDB healthy?
- Do any records have missing metadata?
- Is the Recall Graph database intact?
- Does your identity profile exist?

### `recallos migrate`
Coming from a previous MemPalace installation? One command moves everything:
```bash
recallos migrate --dry-run   # see exactly what would move
recallos migrate             # do it
```

### Your Data Stays Yours
- Everything lives at `~/.recallos/` on your machine.
- No telemetry, no usage tracking, no cloud uploads.
- MIT license — you can read every line of code.
- Open source at github.com/powerproweb/recallos.

---

## Getting Started — 3 Minutes

```bash
# Install
pip install recallos

# Set up a project
recallos init ~/projects/myapp

# Ingest your conversations
recallos ingest ~/chats/ --mode convos

# Check your vault
recallos status

# Connect to Claude (if you use it)
claude mcp add recallos -- python -m recallos.mcp_gateway

# Ask anything
recallos query "why did we pick this database"
```

That's it. From this point on, nothing gets lost.

---

## Who This Is For

RecallOS is most valuable for:

- **Developers** who use AI assistants daily and work across multiple long-running projects
- **Team leads** who need to track decisions, people, and projects across Slack, meetings, and AI sessions
- **Researchers** who accumulate months of AI-assisted analysis and need it to be retrievable
- **Power users of Claude, ChatGPT, or Cursor** who are frustrated by the lack of persistent memory
- **Privacy-conscious users** who want AI memory without their data going to any external service
- **Offline users** who need a full AI memory stack with no internet dependency
- **Builders** who want to extend AI memory with a Python API and MCP integration

If you have ever said *"I know we discussed this before but I can't find it"* — RecallOS is for you.

---

**Deep Research** *(4/10/2026, 7:40:59 AM)*

All the files uploaded by the user have been fully loaded. You can still search connectors to find additional information.

---

**ChatGPT** *(4/10/2026, 7:40:59 AM)*

I’m reading both files now and mapping them into a simple landing-page structure with the two long-scroll sections you want. Next I’m turning the product details into plain, easy wording and a clear visual flow.

---

**ChatGPT** *(4/10/2026, 7:40:59 AM)*

Here is a strong starting plan for the landing page, using simple wording and your color direction.

**What the landing page should do**

The page should help a new visitor understand 3 things fast:

1. **What RecallOS is**
2. **What it can do**
3. **Why that helps them**

The files make it clear that RecallOS is a **local-first AI memory system** that helps people keep project knowledge, decisions, chats, and facts from getting lost. It works offline, stores data on the user’s own machine, and helps AI remember past work across sessions. fileciteturn0file0 fileciteturn0file1

## Best page direction

Use **1 landing page** with **2 long scrolling sections/pages**:

- **Page 1: Features**
- **Page 2: User Benefits**

This is smart because the files naturally split that way:
- the feature file explains **what exists in the product** fileciteturn0file0
- the benefits file explains **why users care** fileciteturn0file1

## Tone and reading level

Use **5th grade wording**:
- short sentences
- common words
- one idea at a time
- very little tech talk on the main screen
- deeper details only in expandable sections or small “learn more” areas

Example style:
- Instead of “structured memory retrieval,” say: **“Find old answers fast.”**
- Instead of “local vector database,” say: **“Your data stays on your computer.”**
- Instead of “bootstrap context,” say: **“Your AI starts with the right background.”**

## Visual style direction

Your palette is good for a premium, powerful, futuristic feel.

### Core palette
- **Dark maroon** for richness and depth
- **Deep blue** for trust and intelligence
- **Gold** for premium trim, highlights, buttons, dividers
- **Turquoise** for active accents, hover states, icons, glow details

### Suggested role usage
- **Background:** deep blue-black gradient with maroon areas
- **Section panels/cards:** dark maroon overlays and deep navy blocks
- **Primary accent:** gold
- **Secondary accent:** turquoise
- **Text:** soft white and light gray
- **Small trim lines / icons / glowing dots:** gold and turquoise

### Mood
Think:
- elegant
- powerful
- mysterious
- high-value
- easy to read

## Structure recommendation

# PAGE 1 — FEATURES

This page answers:

**“What is inside RecallOS?”**

## 1. Hero section
Goal: explain the product in one clean message.

**Headline ideas**
- **Your AI remembers what matters**
- **Stop losing ideas, chats, and decisions**
- **Give your AI a real memory**

**Subheadline**
- **RecallOS saves your chats, files, and decisions on your own computer, so your AI can remember them later.**

**Primary buttons**
- See Features
- See User Benefits
- Get Started

**Small trust line**
- Local-first. Offline-ready. No cloud required. fileciteturn0file0 fileciteturn0file1

## 2. “What RecallOS does” strip
Use 3 to 4 simple blocks:

- **Saves your important work**
- **Helps your AI remember**
- **Finds old answers fast**
- **Keeps your data private**

These are strongly supported by both files. fileciteturn0file0 fileciteturn0file1

## 3. Main features in long-scroll story blocks
Do not show all 16 technical sections from the feature file at once. Group them into simple buckets.

### Feature group A — Save everything in one place
Based on Data Vault + ingest capabilities. fileciteturn0file0

Simple bullets:
- Save chats, notes, project files, and exports
- Keep original words, not just summaries
- Organize by project, topic, and memory type

### Feature group B — Bring in what you already have
Based on supported import formats. fileciteturn0file0 fileciteturn0file1

Simple bullets:
- Import ChatGPT chats
- Import Claude chats
- Import Slack and Discord exports
- Import plain text and notes

### Feature group C — Help your AI start smarter
Based on Memory Stack / bootstrap. fileciteturn0file0 fileciteturn0file1

Simple bullets:
- Give your AI the right background fast
- Load key facts at the start of a session
- Cut down on repeated explaining

### Feature group D — Check facts before your AI answers
Based on Recall Graph. fileciteturn0file0 fileciteturn0file1

Simple bullets:
- Track facts over time
- Catch old or wrong information
- Keep people, projects, and dates straight

### Feature group E — Works with your tools
Based on MCP Gateway, CLI, API, local model support. fileciteturn0file0 fileciteturn0file1

Simple bullets:
- Use with Claude Code
- Use with local models
- Use with command line tools
- Build on it with Python

### Feature group F — Stays local and in your control
Based on offline/local-first positioning. fileciteturn0file0 fileciteturn0file1

Simple bullets:
- No cloud required
- No subscription needed
- Your data stays on your machine

## 4. Feature detail layout style
For each feature block:
- left: simple icon or small illustration
- right: one plain headline, short paragraph, 3 bullets
- alternate sides as the user scrolls

This keeps a long page from feeling heavy.

## 5. Feature proof band
A slim section with fast proof points:
- Local-first
- Offline-ready
- Open source
- No API key required
- Built for long-term AI memory fileciteturn0file0 fileciteturn0file1

## 6. CTA at bottom of Features page
- **See how this helps users**
Button goes to Page 2.

---

# PAGE 2 — USER BENEFITS

This page answers:

**“Why should I care?”**

This page should feel more emotional, more human, and less technical.

## 1. Benefits hero
**Headline ideas**
- **Nothing important gets lost**
- **Stop repeating yourself to AI**
- **Pick up where you left off**

**Subheadline**
- **RecallOS helps your AI remember old chats, decisions, and project work, so you can move faster with less stress.** fileciteturn0file1

## 2. The problem section
Use plain pain points from the benefits file. fileciteturn0file1

Suggested cards:
- **You repeat the same things again and again**
- **Old decisions are hard to find**
- **Project knowledge gets buried**
- **AI forgets what happened last time**

## 3. “What gets better” long-scroll sections

### Benefit A — You stop repeating yourself
From the benefits file’s core message. fileciteturn0file1

Simple copy:
- Your AI starts with context
- You spend less time explaining
- You get to real work faster

### Benefit B — You can find old answers
From searchable vault and verbatim storage. fileciteturn0file0 fileciteturn0file1

Simple copy:
- Find past choices
- Find who said what
- Find why a decision was made

### Benefit C — Your AI becomes more useful over time
From cumulative value described in the benefits file. fileciteturn0file1

Simple copy:
- More history means better help
- Your context grows with your work
- You build a real memory over time

### Benefit D — Your data stays private
From local-only positioning. fileciteturn0file0 fileciteturn0file1

Simple copy:
- No cloud needed
- No forced sharing
- Works on your machine

### Benefit E — It saves money
The benefits file makes a cost argument. fileciteturn0file1

Simple copy:
- No costly memory service
- Lower yearly cost
- More control, less lock-in

### Benefit F — It helps many types of users
Based on “Who this is for.” fileciteturn0file1

Break into user rows:
- Solo developers
- Team leads
- Researchers
- Privacy-focused users
- Local AI users

## 4. Use-case storytelling section
This should be one of the strongest areas on the page.

Show 3 simple before/after stories:

### Story 1 — Solo builder
**Before:** “Where did I write that?”  
**After:** “I found the answer in seconds.”

### Story 2 — Team lead
**Before:** “I know we talked about this.”  
**After:** “Now the team can look it up.”

### Story 3 — Privacy-first user
**Before:** “I do not want my work in the cloud.”  
**After:** “Now it stays on my computer.”

These are directly aligned with the benefits file. fileciteturn0file1

## 5. Final trust + getting started
Finish with easy steps:
- Install it
- Set up your project
- Import your chats
- Ask your AI better questions

The benefits doc has a clean getting-started sequence you can simplify for this area. fileciteturn0file1

## 6. Final CTA
- **Start building your AI memory**
- **See how RecallOS works**
- **Keep every important decision**

---

# Recommended information hierarchy

This is the order I would use across both pages:

1. Big promise
2. One-line explanation
3. Main problem
4. Core solution
5. Key features
6. Real user benefits
7. Proof / trust points
8. Simple getting started
9. Final call to action

That order will make the product easier to understand.

# Best feature groups to highlight first

From all the material, these are the most valuable “top shelf” ideas:

1. **Your AI remembers across sessions**
2. **Your data stays on your computer**
3. **You can search old chats and decisions**
4. **You can import the tools you already use**
5. **Your AI can check facts before answering**
6. **It works offline and without subscriptions**

These are the clearest hooks from the docs. fileciteturn0file0 fileciteturn0file1

# Simple copy examples for the page

## Hero
**Your AI remembers what matters**  
Save chats, files, and decisions on your own computer so nothing important gets lost.

## Features intro
**Built to remember your work**  
RecallOS saves your project history in a smart way so your AI can find it later.

## Benefits intro
**Less repeating. Less searching. More building.**  
RecallOS helps you get back to work faster because your AI starts with the right context.

# Design notes for the long-scroll feel

To make the two pages feel rich and premium:

- use tall sections with lots of breathing room
- add thin gold divider lines
- use turquoise glow for active icons and hover states
- put dark maroon gradients behind important content blocks
- use deep navy as the base so white text stays readable
- use large headlines and short body text
- avoid crowded grids early on
- save denser content for lower sections

# What I would avoid

Do not lead with:
- test counts
- raw recall metrics
- CLI command overload
- database names
- table-heavy technical detail

Those belong lower on the page or in expandable details, because they are harder for a new visitor at a 5th-grade reading level. The docs contain strong technical depth, but the first pass should stay simple. fileciteturn0file0

# Strong next step

The best next move is to build:
1. a **site map / wireframe** for both long pages, then
2. the **actual homepage copy** in very simple wording, section by section.

I can draft the full wireframe and all homepage text next.

---

**You** *(4/10/2026, 7:46:23 AM)*

procede with step 1

---

**ChatGPT** *(4/10/2026, 7:46:24 AM)*

Great. Here is **Step 1: the site map + wireframe plan** for the two long scrolling pages, written for clarity and easy understanding.

This structure is based on the uploaded feature and benefit files, especially the ideas of local-first memory, searchable past decisions, imports, AI startup context, fact-checking, offline use, and user outcomes. fileciteturn0file0 fileciteturn0file1

# Overall site structure

## Main navigation
Keep the top nav very simple:

- Logo
- Features
- Benefits
- How It Works
- Get Started
- GitHub or Download

Optional right-side button:
- **Try RecallOS**
- or **Get Started**

---

# PAGE 1 — FEATURES

## Goal of this page
Help a new visitor quickly understand:

- what RecallOS is
- what it saves
- how it works
- why it is different

This page should feel like:
**“Here is what the product does.”**

---

## Wireframe for Page 1

### Section 1 — Hero
**Purpose:** explain RecallOS in one glance

**Layout**
- Left: headline, short paragraph, 2 buttons
- Right: product mockup / glowing vault-memory illustration / layered panel graphic

**Content blocks**
- Small label: **Local-First AI Memory**
- Headline: **Your AI remembers what matters**
- Subheadline:  
  **RecallOS saves chats, files, and decisions on your own computer so your AI can find them later.**
- Buttons:
  - **See Features**
  - **See Benefits**

**Micro-trust row below**
- Offline-ready
- No cloud needed
- No subscription
- Open source

This matches the local-first, offline, no-cloud, no-subscription positioning in the files. fileciteturn0file0 fileciteturn0file1

---

### Section 2 — “What RecallOS does”
**Purpose:** simplify the whole product into 4 easy ideas

**Layout**
- 4 large icon cards in a row or 2x2 grid

**Cards**
1. **Saves your work**
2. **Helps AI remember**
3. **Finds old answers**
4. **Keeps data private**

**Short support line under grid**
- **Everything stays on your machine and is easy to search later.**

This section acts as the plain-English summary of the feature file. fileciteturn0file0

---

### Section 3 — Save everything in one place
**Purpose:** explain the Data Vault without using heavy technical language

**Layout**
- Left: illustration of folders, nodes, and memory routes
- Right: text

**Headline**
- **Keep chats, files, and ideas in one smart place**

**Text**
- RecallOS stores your work in a clear structure so your AI can find the right thing later.

**3 bullet points**
- Sort by project or topic
- Keep original words
- Connect related ideas

This is based on Domains, Nodes, Channels, Source Records, and Links. fileciteturn0file0

---

### Section 4 — Bring in what you already have
**Purpose:** show import power

**Layout**
- Right: logos or file-type cards
- Left: text

**Headline**
- **Import the tools you already use**

**Visual cards**
- ChatGPT
- Claude
- Slack
- Discord
- Notes
- Plain text
- Project files

**Text**
- You do not need to start over. Point RecallOS to your files and chats, and it pulls them in.

This comes from the ingest engine and supported format list. fileciteturn0file0 fileciteturn0file1

---

### Section 5 — Start each session with context
**Purpose:** explain bootstrap / memory stack in simple words

**Layout**
- Full-width story section with layered “AI memory loading” visual

**Headline**
- **Help your AI start with the right background**

**Text**
- Instead of explaining everything again, RecallOS gives your AI the key facts it needs at the start.

**Mini 3-step flow**
1. Load who you are
2. Load current project facts
3. Load what matters most now

This is based on L0, L1, L2, L3 and bootstrap behavior. fileciteturn0file0 fileciteturn0file1

---

### Section 6 — Find old decisions fast
**Purpose:** highlight searchable memory

**Layout**
- Left: query box UI mockup
- Right: text + example result

**Headline**
- **Find the reason behind past decisions**

**Example UI**
Search:
- “Why did we switch databases?”
Result:
- old session found
- date shown
- exact wording shown

This directly reflects searchable past conversations and verbatim storage. fileciteturn0file0 fileciteturn0file1

---

### Section 7 — Check facts before AI answers
**Purpose:** explain Recall Graph simply

**Layout**
- Right: relationship map / graph lines / timeline UI
- Left: text

**Headline**
- **Help your AI avoid old or wrong facts**

**Text**
- RecallOS tracks facts over time so your AI can check what is true now.

**3 small examples**
- who worked on what
- when a change happened
- what is still current

This is grounded in the recall graph and contradiction detection. fileciteturn0file0 fileciteturn0file1

---

### Section 8 — Works with your setup
**Purpose:** show compatibility without too much tech detail

**Layout**
- 3 horizontal cards

**Cards**
1. **Use it with Claude Code**
2. **Use it with local AI**
3. **Use it with Python tools**

This reflects MCP tools, local models, CLI, and Python API support. fileciteturn0file0 fileciteturn0file1

---

### Section 9 — Private by design
**Purpose:** close the feature story with trust

**Layout**
- Dark premium band with gold trim

**Headline**
- **Your data stays yours**

**Trust bullets**
- Runs locally
- Works offline
- No cloud storage required
- No subscription required

This message is repeated across both files and should be a major trust anchor. fileciteturn0file0 fileciteturn0file1

---

### Section 10 — CTA at bottom of Features page
**Purpose:** move people to the benefits page

**Headline**
- **Now see what this means for you**

**Buttons**
- **See User Benefits**
- **Get Started**

---

# PAGE 2 — USER BENEFITS

## Goal of this page
Help visitors feel:

- “this solves my problem”
- “this will save me time”
- “this will make AI more useful for me”

This page should feel like:
**“Here is how life gets better.”**

---

## Wireframe for Page 2

### Section 1 — Benefits hero
**Purpose:** emotional hook

**Layout**
- Centered text with strong headline
- Background art: memory threads, glowing archive, or calm futuristic dashboard

**Headline**
- **Stop repeating yourself to AI**
- or
- **Nothing important gets lost**

**Subheadline**
- **RecallOS helps your AI remember past work, so you can get back to building faster.**

This is strongly supported by the benefits file’s core promise. fileciteturn0file1

---

### Section 2 — The problem
**Purpose:** make the pain feel familiar

**Layout**
- 4 pain-point cards

**Cards**
1. **You explain the same thing again**
2. **Old choices are hard to find**
3. **Team knowledge gets buried**
4. **AI forgets last time**

This comes straight from the user problem framing in the benefits file. fileciteturn0file1

---

### Section 3 — Main benefit story
**Purpose:** show the transformation

**Layout**
- Tall split section
- Left: “before”
- Right: “after”

**Headline**
- **From lost context to clear memory**

**Before / after examples**
- Before: “I know we talked about this before.”
- After: “Found it. Here is the exact reason.”

This fits the “never lose a decision again” message. fileciteturn0file1

---

### Section 4 — Benefit 1: save time
**Layout**
- left icon + right text

**Headline**
- **Spend less time re-explaining**
- Your AI starts with background context instead of a blank slate.

---

### Section 5 — Benefit 2: find old answers
**Headline**
- **Find past choices in seconds**
- Search old chats, notes, and project files when you need them.

---

### Section 6 — Benefit 3: keep momentum
**Headline**
- **Jump back into any project fast**
- Even after weeks or months away, your AI can help you pick up where you left off.

This reflects resume-any-project and bootstrap benefits. fileciteturn0file1

---

### Section 7 — Benefit 4: improve over time
**Headline**
- **Your AI gets more useful as you use it**
- More saved history means better help later.

This is directly from the benefits file. fileciteturn0file1

---

### Section 8 — Benefit 5: protect privacy
**Headline**
- **Keep your work on your own computer**
- Good for users who want control, privacy, and offline use.

This is central to both files. fileciteturn0file0 fileciteturn0file1

---

### Section 9 — Benefit 6: spend less money
**Purpose:** show practical value

**Layout**
- simple comparison strip, not a complex pricing table

**Headline**
- **Avoid costly memory tools**
- RecallOS keeps costs low by running locally.

This comes from the annual cost comparison in the benefits file. fileciteturn0file1

---

### Section 10 — “Who this helps”
**Purpose:** let people see themselves in the product

**Layout**
- 5 profile cards

**Cards**
1. **Solo developers**
2. **Team leads**
3. **Researchers**
4. **Privacy-first users**
5. **Local AI builders**

This is based directly on the “Who This Is For” section. fileciteturn0file1

---

### Section 11 — 3 use-case stories
**Purpose:** make it real

**Layout**
- 3 stacked story blocks

**Story 1**
- **For solo builders**
- You remember why you made a choice months ago.

**Story 2**
- **For teams**
- Decisions from chats and meetings do not disappear.

**Story 3**
- **For private workflows**
- Your memory system stays local and under your control.

These map well to the benefits examples. fileciteturn0file1

---

### Section 12 — Easy getting started
**Purpose:** reduce fear

**Layout**
- 3 or 4 simple steps with numbers

**Headline**
- **Start in a few simple steps**

**Steps**
1. Install RecallOS
2. Connect your project or chats
3. Let it organize your memory
4. Ask better questions later

This is based on the getting-started flow in the benefits file and CLI steps in the feature file. fileciteturn0file0 fileciteturn0file1

---

### Section 13 — Final CTA
**Purpose:** close with confidence

**Headline**
- **Give your AI a memory that lasts**

**Buttons**
- **Get Started**
- **View Features Again**
- **See the Code**

---

# Recommended visual rhythm

To keep both long pages easy to follow:

## Repeat this pattern
- big headline
- short paragraph
- 3 bullets or 1 example
- illustration or UI mockup
- lots of spacing

## Alternate layouts
- text left / visual right
- visual left / text right
- full-width center section
- cards row
- story block

That will make the page feel alive instead of repetitive.

---

# Design system guidance for this wireframe

## Background treatment
Use layered gradients:
- deep navy base
- maroon glow zones
- subtle gold lines
- turquoise light accents for active elements

## Cards
- soft dark surfaces
- thin gold border or trim line
- turquoise icon glow
- large rounded corners

## Buttons
Primary:
- gold fill or gold outline

Secondary:
- turquoise outline or dark fill with turquoise text

## Typography
- large bold hero headlines
- short simple body copy
- generous line spacing
- no dense paragraphs above the fold

---

# Best order of message across both pages

## Features page message order
1. What it is
2. What it saves
3. What it imports
4. How it helps AI remember
5. How it finds answers
6. How it checks facts
7. Why it is private
8. CTA

## Benefits page message order
1. What pain it solves
2. What gets easier
3. How it saves time
4. How it protects privacy
5. How it helps different users
6. How to start
7. CTA

---

# Recommendation for next build step

The smartest next step is:

**Step 2: write the full section-by-section copy for Page 1 (Features) in 5th-grade-level wording**

That will give you real text to place into the layout right away.

---