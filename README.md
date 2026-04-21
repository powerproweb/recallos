<div align="center">

# RecallOS

### Persistent AI memory that lives on your machine.

[![][version-shield]][release-link]
[![][python-shield]][python-link]
[![][license-shield]][license-link]
[![][discord-shield]][discord-link]

<br>

**The highest-scoring local AI memory system ever benchmarked. Open source. Free forever.**

<table>
<tr>
<td align="center"><strong>96.6%</strong><br><sub>LongMemEval R@5<br>Zero API calls</sub></td>
<td align="center"><strong>100%</strong><br><sub>LongMemEval R@5<br>with Haiku rerank</sub></td>
<td align="center"><strong>+34%</strong><br><sub>Retrieval boost<br>from vault structure</sub></td>
<td align="center"><strong>$0</strong><br><sub>No subscription<br>No cloud. Local only.</sub></td>
</tr>
</table>

<sub>Reproducible — runners in <a href="benchmarks/">benchmarks/</a>. <a href="benchmarks/BENCHMARKS.md">Full results</a>.</sub>

<br>

[Quick Start](#quick-start) · [How It Works](#how-it-works) · [Benchmarks](#benchmarks) · [MCP Tools](#mcp-server) · [Website](https://recallos.com)

</div>

---

Every conversation you have with an AI — every decision, every debugging session, every architecture debate — disappears when the session ends. Six months of daily AI use produces **19.5 million tokens** of reasoning. Gone.

RecallOS stores everything, makes it retrievable, and gives your AI a memory that compounds over time. No cloud. No API key. No subscription.

- **The Data Vault** — Organizes long-term AI memory into Domains, Nodes, Channels, Index Summaries, and Source Records. Structure alone improves retrieval by 34%.
- **RecallScript** — A 30× lossless compression dialect readable by any LLM. Load months of context in ~120 tokens. Works with Claude, GPT, Gemini, Llama, Mistral — any model that reads text.
- **Local, open, adaptable** — Runs entirely on your machine. Tested on conversations, adaptable to any datastore. That's why it's open source.

---

## Quick Start

```bash
pip install recallos

# Set up your working world
recallos init ~/projects/myapp

# Ingest your data
recallos ingest ~/projects/myapp                            # projects — code, docs, notes
recallos ingest ~/chats/ --mode convos                     # convos — Claude, ChatGPT, Slack, Discord exports
recallos ingest ~/chats/ --mode convos --extract general   # classifies into decisions, milestones, problems
recallos ingest ~/projects/myapp --encode                  # store RecallScript-compressed versions

# Query anything you've ever discussed
recallos query "why did we switch to GraphQL"

# Health check
recallos status
recallos doctor
```

Three ingest modes: **projects** (code and docs), **convos** (conversation exports — Claude, ChatGPT, Slack, Discord, Obsidian), and **general** (auto-classifies into decisions, preferences, milestones, problems, and emotional context).

---

## How You Actually Use It

After setup, you rarely run RecallOS manually. Your AI uses it for you.

### With Claude, ChatGPT, Cursor (MCP-compatible tools)

```bash
claude mcp add recallos -- python -m recallos.mcp_gateway
```

Now your AI has RecallOS tools available through MCP:

> *"What did we decide about auth last month?"*

Claude calls `recallos_query` automatically, gets verbatim results, and answers you.

### With local models (Llama, Mistral, or any offline LLM)

```bash
# Load your world into the model's context
recallos bootstrap > context.txt

# Or query on demand
recallos query "auth decisions" > results.txt
```

Or use the Python API:

```python
from recallos.retrieval_engine import search_memories
results = search_memories("auth decisions", vault_path="~/.recallos/vault")
```

Either way, your entire memory stack runs offline. ChromaDB on your machine, your model on your machine, zero cloud calls.

---

## How It Works

### The Data Vault

```text
  ┌─────────────────────────────────────────────────────────────┐
  │  DOMAIN: Person                                            │
  │                                                            │
  │    ┌──────────┐  ─channel─  ┌──────────┐                   │
  │    │  Node A  │             │  Node B  │                   │
  │    └────┬─────┘             └──────────┘                   │
  │         │                                                  │
  │         ▼                                                  │
  │    ┌────────────────┐   ┌───────────────┐                  │
  │    │ Index Summary  │ ─▶│ Source Record │                  │
  │    └────────────────┘   └───────────────┘                  │
  └─────────┼──────────────────────────────────────────────────┘
            │
           link
            │
  ┌─────────┼──────────────────────────────────────────────────┐
  │  DOMAIN: Project                                           │
  │         │                                                  │
  │    ┌────┴─────┐  ─channel─  ┌──────────┐                   │
  │    │  Node A  │             │  Node C  │                   │
  │    └────┬─────┘             └──────────┘                   │
  │         │                                                  │
  │         ▼                                                  │
  │    ┌────────────────┐   ┌───────────────┐                  │
  │    │ Index Summary  │ ─▶│ Source Record │                  │
  │    └────────────────┘   └───────────────┘                  │
  └─────────────────────────────────────────────────────────────┘
```

**Domains** — a person, project, or topic. As many as you need.
**Nodes** — specific topics within a Domain. Auth, billing, deploy — unlimited Nodes.
**Channels** — structured memory pathways: `channel_facts`, `channel_events`, `channel_discoveries`, `channel_preferences`, `channel_guidance`.
**Links** — cross-domain connections between matching Nodes.
**Index Summaries** — compressed retrieval layers. Fast for AI to read.
**Source Records** — the original verbatim files. Never summarized away.

### Why Structure Matters

Tested on 22,000+ real conversation memories:

```text
Search all summaries:        60.9%  R@10
Search within domain:        73.1%  (+12%)
Search domain + channel:     84.8%  (+24%)
Search domain + node:        94.8%  (+34%)
```

### The Memory Stack

| Layer | What | Size | When |
|-------|------|------|------|
| **L0** | Identity Layer | ~50 tokens | Always loaded |
| **L1** | Core Context Layer | ~120 tokens (RecallScript) | Always loaded |
| **L2** | Node Recall Layer | On demand | When a topic comes up |
| **L3** | Deep Retrieval Layer | On demand | When explicitly asked |

Your AI bootstraps with L0 + L1 (~170 tokens) and knows your world.

### RecallScript Compression

30× lossless compression. Any LLM reads it. No decoder required.

**English (~1000 tokens):**
```text
Priya manages the Driftwood team: Kai (backend, 3 years), Soren (frontend),
Maya (infrastructure), and Leo (junior, started last month). They're building
a SaaS analytics platform. Current sprint: auth migration to Clerk.
Kai recommended Clerk over Auth0 based on pricing and DX.
```

**RecallScript (~120 tokens):**
```text
TEAM: PRI(lead) | KAI(backend,3yr) SOR(frontend) MAY(infra) LEO(junior,new)
PROJ: DRIFTWOOD(saas.analytics) | SPRINT: auth.migration→clerk
DECISION: KAI.rec:clerk>auth0(pricing+dx) | ★★★★
```

### Contradiction Detection

```text
Input:  "Soren finished the auth migration"
Output: 🔴 AUTH-MIGRATION: attribution conflict — Maya was assigned, not Soren

Input:  "Kai has been here 2 years"
Output: 🟡 KAI: wrong_tenure — records show 3 years (started 2023-04)
```

Facts checked against the Recall Graph. Ages and dates calculated dynamically.

---

## Recall Graph

Temporal entity-relationship triples — like Graphiti, but SQLite instead of Neo4j. Local and free.

```python
from recallos.recall_graph import RecallGraph

rg = RecallGraph()
rg.add_triple("Kai", "works_on", "Orion", valid_from="2025-06-01")
rg.query_entity("Kai")
rg.find_path("Kai", "Clerk")
rg.timeline("Orion")
rg.export_dot()    # Graphviz DOT string
rg.export_json()   # D3-ready adjacency JSON
```

| Feature | RecallOS | Zep (Graphiti) |
|---------|----------|----------------|
| Storage | SQLite (local) | Neo4j (cloud) |
| Cost | Free | $25/mo+ |
| Temporal validity | Yes | Yes |
| Self-hosted | Always | Enterprise only |

---

## Domain Agents

Specialist agents with their own memory. Each agent gets its own Domain and Agent Log in the Data Vault.

```text
~/.recallos/agents/
  ├── reviewer.json       # code quality, patterns, bugs
  ├── architect.json      # design decisions, tradeoffs
  └── ops.json            # deploys, incidents, infra
```

Agent logs are file-backed (`~/.recallos/agent_logs/<agent>/YYYY-MM-DD.jsonl`) and indexed in ChromaDB for semantic search. Files rotate automatically after 30 days.

---

## MCP Server

```bash
claude mcp add recallos -- python -m recallos.mcp_gateway
```

**22 tools** across 5 categories:

| Category | Tools |
|----------|-------|
| **Data Vault** (read) | `recallos_status`, `recallos_list_domains`, `recallos_list_nodes`, `recallos_get_topology`, `recallos_query`, `recallos_check_duplicate`, `recallos_get_recallscript_spec` |
| **Records** (write) | `recallos_add_record`, `recallos_delete_record` |
| **Recall Graph** | `recallos_graph_query`, `recallos_graph_add`, `recallos_graph_invalidate`, `recallos_graph_timeline`, `recallos_graph_stats`, `recallos_graph_path` |
| **Link Navigation** | `recallos_traverse_links`, `recallos_find_links`, `recallos_topology_stats` |
| **Agent Logs** | `recallos_log_write`, `recallos_log_read`, `recallos_log_search` |

The AI learns RecallScript and the memory protocol automatically from `recallos_status`.

---

## Benchmarks

| Benchmark | Mode | Score | API Calls |
|-----------|------|-------|-----------|
| **LongMemEval R@5** | Raw (ChromaDB only) | **96.6%** | Zero |
| **LongMemEval R@5** | Hybrid + Haiku rerank | **100%** (500/500) | ~500 |
| **LoCoMo R@10** | Raw, session level | **60.3%** | Zero |
| **Data Vault structure** | Domain+Node filtering | **+34%** R@10 | Zero |

### vs Published Systems

| System | LongMemEval R@5 | API Required | Cost |
|--------|----------------|--------------|------|
| **RecallOS (hybrid)** | **100%** | Optional | Free |
| Supermemory ASMR | ~99% | Yes | — |
| **RecallOS (raw)** | **96.6%** | **None** | **Free** |
| Mastra | 94.87% | Yes (GPT) | API costs |
| Mem0 | ~85% | Yes | $19–249/mo |
| Zep | ~85% | Yes | $25/mo+ |

---

## All Commands

```bash
recallos init <dir>                                  # guided onboarding
recallos migrate [--dry-run] [--force]               # migrate from ~/.mempalace/
recallos ingest <dir>                                # ingest project files
recallos ingest <dir> --mode convos                  # ingest conversations
recallos ingest <dir> --encode                       # also store RecallScript versions
recallos split <dir>                                 # split concatenated transcripts
recallos query "query"                               # semantic search
recallos query "query" --domain myapp                # scoped to a domain
recallos bootstrap                                   # load L0 + L1 context
recallos encode [--domain myapp]                     # RecallScript encode records
recallos status                                      # vault overview
recallos doctor [--verbose]                          # full health report
```

All commands accept `--vault <path>` to override the default vault location.

---

## Project Structure

```text
recallos/
├── README.md                     ← you are here
├── recallos/                     ← core package
│   ├── cli.py                    ← CLI entry point
│   ├── mcp_gateway.py            ← MCP gateway (22 tools)
│   ├── recall_graph.py           ← temporal entity graph
│   ├── vault_graph.py            ← node navigation graph
│   ├── recallscript.py           ← RecallScript compression
│   ├── ingest_engine.py          ← project file ingest
│   ├── conversation_ingest.py    ← conversation ingest
│   ├── retrieval_engine.py       ← semantic retrieval
│   ├── bootstrap.py              ← guided setup
│   ├── migration.py              ← migrate ~/.mempalace/ data
│   ├── diagnostics.py            ← vault health checks
│   ├── agent_log.py              ← file-backed agent logs
│   └── ...
├── site/                         ← landing page (recallos.com)
├── benchmarks/                   ← reproducible benchmark runners
├── hooks/                        ← Claude Code auto-save hooks
├── examples/                     ← usage examples
├── tests/                        ← test suite
├── 01_all_md_files/              ← supplementary documentation
│   ├── CHANGELOG.md
│   ├── CONTRIBUTING.md
│   ├── REBUILD_PLAN.md
│   ├── ReCallOS.features.readme.md
│   ├── ReCallOS.user-benefits.readme.md
│   └── ...
└── pyproject.toml                ← package config
```

---

## Requirements

- Python 3.9+
- `chromadb>=0.4.0`
- `pyyaml>=6.0`

No API key. No internet after install. Everything local.

```bash
pip install recallos
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Feature List](01_all_md_files/ReCallOS.features.readme.md) | Complete technical reference — every capability, flag, API method, and config option |
| [User Guide](01_all_md_files/ReCallOS.user-benefits.readme.md) | Plain-English guide — what RecallOS does for you, use cases, getting started |
| [Contributing](01_all_md_files/CONTRIBUTING.md) | Setup, PR guidelines, code style, good first issues |
| [Changelog](01_all_md_files/CHANGELOG.md) | Full development history across all build phases |
| [Rebuild Plan](01_all_md_files/REBUILD_PLAN.md) | Architecture decisions and naming conventions |
| [Web Roadmap](01_all_md_files/recallos.web.gui.build.md) | CLI → web service development plan |

---

## Contributing

PRs welcome. See [CONTRIBUTING.md](01_all_md_files/CONTRIBUTING.md) for setup and guidelines.

## License

MIT — see [LICENSE](LICENSE).

<!-- Link Definitions -->
[version-shield]: https://img.shields.io/badge/version-4.2.0-4dc9f6?style=flat-square&labelColor=0a0e14
[release-link]: https://github.com/powerproweb/recallos/releases
[python-shield]: https://img.shields.io/badge/python-3.9+-7dd8f8?style=flat-square&labelColor=0a0e14&logo=python&logoColor=7dd8f8
[python-link]: https://www.python.org/
[license-shield]: https://img.shields.io/badge/license-MIT-b0e8ff?style=flat-square&labelColor=0a0e14
[license-link]: https://github.com/powerproweb/recallos/blob/main/LICENSE
[discord-shield]: https://img.shields.io/badge/discord-join-5865F2?style=flat-square&labelColor=0a0e14&logo=discord&logoColor=5865F2
[discord-link]: https://discord.com/invite/ycTQQCu6kn
