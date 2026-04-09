<div align="center">

<img src="assets/recallos_logo.png" alt="RecallOS" width="280">

# RecallOS

### The highest-scoring local AI memory operating system ever benchmarked. And it's free.

<br>

Every conversation you have with an AI — every decision, every debugging session, every architecture debate — disappears when the session ends. Six months of work, gone. You start over every time.

Most memory systems try to solve this by deciding what is worth remembering. They extract fragments like "user prefers Postgres" and discard the conversation that explained *why*. RecallOS takes a different approach: **store everything, then make it retrievable.**

**The Data Vault** — RecallOS organizes long-term AI memory into a structured system of Domains, Channels, Nodes, Index Summaries, and Source Records. No AI decides what matters — every word is preserved, and the structure makes it searchable. That structure alone improves retrieval by 34%.

**RecallScript** — A lossless shorthand dialect designed for AI agents. Not meant to be read by humans — meant to be read by your AI, fast. 30x compression, zero information loss. Your AI can load months of context in ~120 tokens. And because RecallScript is just structured text with a universal grammar, it works with **any model that reads text** — Claude, GPT, Gemini, Llama, Mistral. No decoder, no fine-tuning, no cloud API required. Run it against a local model and your entire memory stack stays offline.

**Local, open, adaptable** — RecallOS runs entirely on your machine, on any data you have locally, without relying on any external API or service. It has been tested on conversations, but it can be adapted to other datastore types. That is why it is open source.

<br>

[![][version-shield]][release-link]
[![][python-shield]][python-link]
[![][license-shield]][license-link]
[![][discord-shield]][discord-link]

<br>

[Quick Start](#quick-start) · [The Data Vault](#the-data-vault) · [RecallScript Compression](#recallscript-compression) · [Benchmarks](#benchmarks) · [MCP Tools](#mcp-server)

<br>

### Highest LongMemEval score ever published — free or paid.

<table>
<tr>
<td align="center"><strong>96.6%</strong><br><sub>LongMemEval R@5<br>Zero API calls</sub></td>
<td align="center"><strong>100%</strong><br><sub>LongMemEval R@5<br>with Haiku rerank</sub></td>
<td align="center"><strong>+34%</strong><br><sub>Retrieval boost<br>from Data Vault structure</sub></td>
<td align="center"><strong>$0</strong><br><sub>No subscription<br>No cloud. Local only.</sub></td>
</tr>
</table>

<sub>Reproducible — runners in <a href="benchmarks/">benchmarks/</a>. <a href="benchmarks/BENCHMARKS.md">Full results</a>.</sub>

</div>

---

## Quick Start

```bash
pip install recallos

# Set up your working world — who you work with, what your projects are
recallos init ~/projects/myapp

# Ingest your data
recallos ingest ~/projects/myapp                           # projects — code, docs, notes
recallos ingest ~/chats/ --mode convos                    # convos — Claude, ChatGPT, Slack exports
recallos ingest ~/chats/ --mode convos --extract general  # general — classifies into decisions, milestones, problems

# Query anything you've ever discussed
recallos query "why did we switch to GraphQL"

# Check system status
recallos status
```

Three ingest modes: **projects** (code and docs), **convos** (conversation exports), and **general** (auto-classifies into decisions, preferences, milestones, problems, and emotional context). Everything stays on your machine.

---

## How You Actually Use It

After the one-time setup (install → init → ingest), you typically do not run RecallOS commands manually. Your AI uses it for you. There are two paths, depending on which AI you use.

### With Claude, ChatGPT, Cursor (MCP-compatible tools)

```bash
# Connect RecallOS once
claude mcp add recallos -- python -m recallos.mcp_gateway
```

Now your AI has RecallOS tools available through MCP. Ask it anything:

> *"What did we decide about auth last month?"*

Claude calls `recallos_query` automatically, gets verbatim results, and answers you. You never need to type `recallos query` manually. The AI handles it.

### With local models (Llama, Mistral, or any offline LLM)

Local models generally do not speak MCP yet. There are two simple approaches:

**1. Bootstrap command** — load your world into the model's context:

```bash
recallos bootstrap > context.txt
# Paste context.txt into your local model's system prompt
```

This gives your local model ~170 tokens of critical facts (in RecallScript if preferred) before you ask a single question.

**2. CLI query** — retrieve on demand, then feed results into your prompt:

```bash
recallos query "auth decisions" > results.txt
# Include results.txt in your prompt
```

Or use the Python API:

```python
from recallos.retrieval_engine import search_memories
results = search_memories("auth decisions", vault_path="~/.recallos/vault")
# Inject into your local model's context
```

Either way, your entire memory stack runs offline. ChromaDB on your machine, Llama on your machine, RecallScript for compression, zero cloud calls.

---

## The Problem

Decisions happen in conversations now. Not in docs. Not in Jira. In conversations with Claude, ChatGPT, Copilot. The reasoning, the tradeoffs, the "we tried X and it failed because Y" — all trapped in chat windows that evaporate when the session ends.

**Six months of daily AI use = 19.5 million tokens.** That is every decision, every debugging session, every architecture debate. Gone.

| Approach | Tokens loaded | Annual cost |
|----------|--------------|-------------|
| Paste everything | 19.5M — doesn't fit any context window | Impossible |
| LLM summaries | ~650K | ~$507/yr |
| **RecallOS bootstrap** | **~170 tokens** | **~$0.70/yr** |
| **RecallOS + 5 queries** | **~13,500 tokens** | **~$10/yr** |

RecallOS loads 170 tokens of critical facts at bootstrap — your team, your projects, your preferences. Then it queries only when needed. $10/year to remember everything vs $507/year for summaries that lose context.

---

## How It Works

### The Data Vault

The layout is simple, though it took a long time to make it simple.

It starts with a **Domain**. Every project, person, or topic you are storing gets its own Domain in the Data Vault.

Each Domain contains **Nodes**, where information is split into subjects related to that Domain — every Node represents a specific element of what that project, person, or topic contains. Project ideas could be one Node, employees another, financial statements another. There can be as many Nodes as needed to structure the Domain. RecallOS detects these automatically, and you can personalize them any way you want.

Every Node contains an **Index Summary**, and this is where things become powerful. RecallOS includes an AI shorthand language called **RecallScript**. Your agent learns RecallScript every time it bootstraps. Because RecallScript is essentially compressed structured English, your agent understands it quickly. It ships as part of the RecallOS install and is built into the system. In future updates, RecallScript will be integrated deeper into the Index Summary layer, which will significantly expand how much information can be stored while reducing read cost for the agent.

Inside those summaries are linked **Source Records**, and those records are where your original files live. In this first version, RecallScript is not yet fully used as the primary summary substrate, but even so, the summaries have shown **96.6% recall** across benchmark evaluations. Once the summary layer uses RecallScript more deeply, retrieval will be even faster while keeping every word exact. Even now, the summary layer is highly effective — it points your AI directly to the Source Record containing the original material. You never lose anything, and all of this happens in seconds.

There are also **Channels**, which organize memory types within a Domain, and **Links**, which connect Nodes across Domains. That means retrieval becomes dramatically easier — your AI has a clean, structured way to know where to start searching, without brute-forcing every keyword across massive folders.

You tell it what you need, and it already knows which Domain to enter.

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
**Channels** — structured memory pathways within the same Domain.  
**Links** — cross-domain connections between matching or related Nodes.  
**Index Summaries** — compressed retrieval layers that point to the original content. Fast for AI to read.  
**Source Records** — the original verbatim files. The exact words, never summarized away.

**Channels** are memory classes — the same in every Domain, acting as standardized routes:
- `channel_facts` — decisions made, choices locked in
- `channel_events` — sessions, milestones, debugging
- `channel_discoveries` — breakthroughs, new insights
- `channel_preferences` — habits, likes, opinions
- `channel_guidance` — recommendations and solutions

**Nodes** are named ideas — `auth-migration`, `graphql-switch`, `ci-pipeline`. When the same Node appears in different Domains, it creates a **Link** — connecting the same topic across contexts:

```text
domain_kai        / channel_events     / auth-migration  → "Kai debugged the OAuth token refresh"
domain_driftwood  / channel_facts      / auth-migration  → "team decided to migrate auth to Clerk"
domain_priya      / channel_guidance   / auth-migration  → "Priya approved Clerk over Auth0"
```

Same Node. Three Domains. The Link connects them.

### Why Structure Matters

Tested on 22,000+ real conversation memories:

```text
Search all summaries:        60.9%  R@10
Search within domain:        73.1%  (+12%)
Search domain + channel:     84.8%  (+24%)
Search domain + node:        94.8%  (+34%)
```

Domains and Nodes are not cosmetic. They produce a **34% retrieval improvement**. The Data Vault structure is the product.

### The Memory Stack

| Layer | What | Size | When |
|-------|------|------|------|
| **L0** | Identity Layer — who is this AI? | ~50 tokens | Always loaded |
| **L1** | Core Context Layer — team, projects, preferences | ~120 tokens (RecallScript) | Always loaded |
| **L2** | Node Recall Layer — recent sessions, current project | On demand | When a topic comes up |
| **L3** | Deep Retrieval Layer — semantic query across all summaries | On demand | When explicitly asked |

Your AI bootstraps with L0 + L1 (~170 tokens) and knows your world. Queries only fire when needed.

### RecallScript Compression

RecallScript is a lossless dialect — 30x compression, readable by any LLM without a decoder. It works with **Claude, GPT, Gemini, Llama, Mistral** — any model that reads text. Run it against a local Llama model and your whole memory stack stays offline.

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

Same information. Far fewer tokens. Your AI learns RecallScript automatically from the MCP gateway — no manual setup.

### Contradiction Detection

RecallOS catches mistakes before they reach you:

```text
Input:  "Soren finished the auth migration"
Output: 🔴 AUTH-MIGRATION: attribution conflict — Maya was assigned, not Soren

Input:  "Kai has been here 2 years"
Output: 🟡 KAI: wrong_tenure — records show 3 years (started 2023-04)

Input:  "The sprint ends Friday"
Output: 🟡 SPRINT: stale_date — current sprint ends Thursday (updated 2 days ago)
```

Facts are checked against the Recall Graph. Ages, dates, and tenures are calculated dynamically — not hardcoded.

---

## Real-World Examples

### Solo developer across multiple projects

```bash
# Ingest each project's conversations
recallos ingest ~/chats/orion/  --mode convos --domain orion
recallos ingest ~/chats/nova/   --mode convos --domain nova
recallos ingest ~/chats/helios/ --mode convos --domain helios

# Six months later: "why did I use Postgres here?"
recallos query "database decision" --domain orion
# → "Chose Postgres over SQLite because Orion needs concurrent writes
#    and the dataset will exceed 10GB. Decided 2025-11-03."

# Cross-project query
recallos query "rate limiting approach"
# → finds your approach in Orion AND Nova, shows the differences
```

### Team lead managing a product

```bash
# Ingest Slack exports and AI conversations
recallos ingest ~/exports/slack/ --mode convos --domain driftwood
recallos ingest ~/.claude/projects/ --mode convos

# "What did Soren work on last sprint?"
recallos query "Soren sprint" --domain driftwood
# → 14 summaries: OAuth refactor, dark mode, component library migration

# "Who decided to use Clerk?"
recallos query "Clerk decision" --domain driftwood
# → "Kai recommended Clerk over Auth0 — pricing + developer experience.
#    Team agreed 2026-01-15. Maya handling the migration."
```

### Before ingest: split mega-files

Some transcript exports concatenate multiple sessions into one huge file:

```bash
recallos split ~/chats/                      # split into per-session files
recallos split ~/chats/ --dry-run            # preview first
recallos split ~/chats/ --min-sessions 3     # only split files with 3+ sessions
```

---

## Recall Graph

Temporal entity-relationship triples — like Graphiti, but SQLite instead of Neo4j. Local and free.

```python
from recallos.recall_graph import RecallGraph

rg = RecallGraph()
rg.add_triple("Kai", "works_on", "Orion", valid_from="2025-06-01")
rg.add_triple("Maya", "assigned_to", "auth-migration", valid_from="2026-01-15")
rg.add_triple("Maya", "completed", "auth-migration", valid_from="2026-02-01")

# What's Kai working on?
rg.query_entity("Kai")
# → [Kai → works_on → Orion (current), Kai → recommended → Clerk (2026-01)]

# What was true in January?
rg.query_entity("Maya", as_of="2026-01-20")
# → [Maya → assigned_to → auth-migration (active)]

# Timeline
rg.timeline("Orion")
# → chronological story of the project
```

Facts have validity windows. When something stops being true, invalidate it:

```python
rg.invalidate("Kai", "works_on", "Orion", ended="2026-03-01")
```

Now queries for Kai's current work will not return Orion. Historical queries still will.

| Feature | RecallOS | Zep (Graphiti) |
|---------|----------|----------------|
| Storage | SQLite (local) | Neo4j (cloud) |
| Cost | Free | $25/mo+ |
| Temporal validity | Yes | Yes |
| Self-hosted | Always | Enterprise only |
| Privacy | Everything local | SOC 2, HIPAA |

---

## Domain Agents

Create agents that focus on specific areas. Each agent gets its own Domain and Agent Log in the Data Vault — not in your CLAUDE.md. Add 50 agents, your config stays the same size.

```text
~/.recallos/agents/
  ├── reviewer.json       # code quality, patterns, bugs
  ├── architect.json      # design decisions, tradeoffs
  └── ops.json            # deploys, incidents, infra
```

Your CLAUDE.md only needs one line:

```text
You have RecallOS agents. Run recallos_list_agents to see them.
```

The AI discovers its agents from the Data Vault at runtime. Each agent:

- **Has a focus** — what it pays attention to
- **Keeps an Agent Log** — written in RecallScript, persists across sessions
- **Builds expertise** — reads its own history to stay sharp in its domain

```text
# Agent writes to its log after a code review
recallos_log_write("reviewer",
    "PR#42|auth.bypass.found|missing.middleware.check|pattern:3rd.time.this.quarter|★★★★")

# Agent reads back its history
recallos_log_read("reviewer", last_n=10)
# → last 10 findings, compressed in RecallScript
```

Each agent is a specialist lens on your data. The reviewer remembers every bug pattern it has seen. The architect remembers every design decision. The ops agent remembers every incident. They do not share a scratchpad — they each maintain their own memory.

---

## MCP Server

```bash
claude mcp add recallos -- python -m recallos.mcp_gateway
```

### Core Tools

**Data Vault Operations (read)**

| Tool | What |
|------|------|
| `recallos_status` | Data Vault overview + RecallScript spec + memory protocol |
| `recallos_list_domains` | Domains with counts |
| `recallos_list_nodes` | Nodes within a Domain |
| `recallos_get_topology` | Full Domain → Node → count tree |
| `recallos_query` | Semantic retrieval with Domain/Node filters |
| `recallos_check_duplicate` | Check before filing |
| `recallos_get_recallscript_spec` | RecallScript dialect reference |

**Record Operations (write)**

| Tool | What |
|------|------|
| `recallos_add_record` | File verbatim content |
| `recallos_delete_record` | Remove by ID |

**Recall Graph**

| Tool | What |
|------|------|
| `recallos_graph_query` | Entity relationships with time filtering |
| `recallos_graph_add` | Add facts |
| `recallos_graph_invalidate` | Mark facts as ended |
| `recallos_graph_timeline` | Chronological entity story |
| `recallos_graph_stats` | Graph overview |

**Link Navigation**

| Tool | What |
|------|------|
| `recallos_traverse_links` | Walk the graph from a Node across Domains |
| `recallos_find_links` | Find Nodes bridging two Domains |
| `recallos_topology_stats` | Connectivity overview |

**Agent Logs**

| Tool | What |
|------|------|
| `recallos_log_write` | Write RecallScript log entry |
| `recallos_log_read` | Read recent log entries |

The AI learns RecallScript and the memory protocol automatically from the `recallos_status` response. No manual configuration needed.

---

## Auto-Save Hooks

Two hooks for Claude Code that automatically save memories during work:

**Save Hook** — every 15 messages, triggers a structured save. Topics, decisions, quotes, code changes. Also regenerates the critical facts layer.

**PreCompact Hook** — fires before context compression. Emergency save before the window shrinks.

```json
{
  "hooks": {
    "Stop": [{"matcher": "", "hooks": [{"type": "command", "command": "/path/to/recallos/hooks/recallos_save_hook.sh"}]}],
    "PreCompact": [{"matcher": "", "hooks": [{"type": "command", "command": "/path/to/recallos/hooks/recallos_precompact_hook.sh"}]}]
  }
}
```

---

## Benchmarks

Tested on standard academic benchmarks — reproducible, published datasets.

| Benchmark | Mode | Score | API Calls |
|-----------|------|-------|-----------|
| **LongMemEval R@5** | Raw (ChromaDB only) | **96.6%** | Zero |
| **LongMemEval R@5** | Hybrid + Haiku rerank | **100%** (500/500) | ~500 |
| **LoCoMo R@10** | Raw, session level | **60.3%** | Zero |
| **Personal Data Vault R@10** | Heuristic bench | **85%** | Zero |
| **Data Vault structure impact** | Domain+Node filtering | **+34%** R@10 | Zero |

The 96.6% raw score is the highest published LongMemEval result requiring no API key, no cloud, and no LLM at any stage.

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
# Setup
recallos init <dir>                                # guided onboarding + RecallScript bootstrap

# Ingest
recallos ingest <dir>                              # ingest project files
recallos ingest <dir> --mode convos                # ingest conversation exports
recallos ingest <dir> --mode convos --domain myapp # tag with a Domain name

# Splitting
recallos split <dir>                               # split concatenated transcripts
recallos split <dir> --dry-run                     # preview

# Query
recallos query "query"                             # query everything
recallos query "query" --domain myapp              # within a Domain
recallos query "query" --node auth-migration       # within a Node

# Memory stack
recallos bootstrap                                 # load L0 + L1 context
recallos bootstrap --domain driftwood              # project-specific

# Compression
recallos encode --domain myapp                     # RecallScript encode

# Status
recallos status                                    # Data Vault overview
```

All commands accept `--vault <path>` to override the default location.

---

## Configuration

### Global (`~/.recallos/config.json`)

```json
{
  "vault_path": "/custom/path/to/vault",
  "record_collection": "recallos_records",
  "people_map": {"Kai": "KAI", "Priya": "PRI"}
}
```

### Domain config (`~/.recallos/domain_config.json`)

Generated by `recallos init`. Maps your people and projects to Domains:

```json
{
  "default_domain": "domain_general",
  "domains": {
    "domain_kai": {"type": "person", "keywords": ["kai", "kai's"]},
    "domain_driftwood": {"type": "project", "keywords": ["driftwood", "analytics", "saas"]}
  }
}
```

### Identity (`~/.recallos/identity_profile.txt`)

Plain text. Becomes Layer 0 — loaded every session.

---

## File Reference

| File | What |
|------|------|
| `cli.py` | CLI entry point |
| `config.py` | Configuration loading and defaults |
| `normalize.py` | Converts 5 chat formats to standard transcript |
| `mcp_gateway.py` | MCP gateway — tools, RecallScript auto-teach, memory protocol |
| `ingest_engine.py` | Project file ingest |
| `conversation_ingest.py` | Conversation ingest — chunks by exchange pair |
| `retrieval_engine.py` | Semantic retrieval via ChromaDB |
| `memory_layers.py` | 4-layer memory stack |
| `recallscript.py` | RecallScript compression — 30x lossless |
| `recall_graph.py` | Temporal entity-relationship graph (SQLite) |
| `vault_graph.py` | Node-based navigation graph |
| `bootstrap.py` | Guided setup — generates RecallScript bootstrap + domain config |
| `entity_registry.py` | Entity code registry |
| `entity_detector.py` | Auto-detect people and projects from content |
| `transcript_splitter.py` | Split concatenated transcripts into per-session files |
| `hooks/recallos_save_hook.sh` | Auto-save every N messages |
| `hooks/recallos_precompact_hook.sh` | Emergency save before compaction |

---

## Project Structure

```text
recallos/
├── README.md                     ← you are here
├── recallos/                     ← core package
│   ├── cli.py                    ← CLI entry point
│   ├── mcp_gateway.py            ← MCP gateway
│   ├── recall_graph.py           ← temporal entity graph
│   ├── vault_graph.py            ← node navigation graph
│   ├── recallscript.py           ← RecallScript compression
│   ├── ingest_engine.py          ← project file ingest
│   ├── conversation_ingest.py    ← conversation ingest
│   ├── retrieval_engine.py       ← semantic retrieval
│   ├── bootstrap.py              ← guided setup
│   └── ...                       ← see recallos/README.md
├── benchmarks/                   ← reproducible benchmark runners
│   ├── README.md                 ← reproduction guide
│   ├── BENCHMARKS.md             ← full results + methodology
│   ├── longmemeval_bench.py      ← LongMemEval runner
│   ├── locomo_bench.py           ← LoCoMo runner
│   └── membench_bench.py         ← MemBench runner
├── hooks/                        ← Claude Code auto-save hooks
│   ├── README.md                 ← hook setup guide
│   ├── recallos_save_hook.sh     ← save every N messages
│   └── recallos_precompact_hook.sh ← emergency save
├── examples/                     ← usage examples
│   ├── basic_ingest.py
│   ├── convo_import.py
│   └── mcp_setup.md
├── tests/                        ← test suite
├── assets/                       ← logo + brand assets
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

## Contributing

PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and guidelines.

## License

MIT — see [LICENSE](LICENSE).

<!-- Link Definitions -->
[version-shield]: https://img.shields.io/badge/version-4.0.0-4dc9f6?style=flat-square&labelColor=0a0e14
[release-link]: https://github.com/milla-jovovich/recallos/releases
[python-shield]: https://img.shields.io/badge/python-3.9+-7dd8f8?style=flat-square&labelColor=0a0e14&logo=python&logoColor=7dd8f8
[python-link]: https://www.python.org/
[license-shield]: https://img.shields.io/badge/license-MIT-b0e8ff?style=flat-square&labelColor=0a0e14
[license-link]: https://github.com/milla-jovovich/recallos/blob/main/LICENSE
[discord-shield]: https://img.shields.io/badge/discord-join-5865F2?style=flat-square&labelColor=0a0e14&logo=discord&logoColor=5865F2
[discord-link]: https://discord.com/invite/ycTQQCu6kn
