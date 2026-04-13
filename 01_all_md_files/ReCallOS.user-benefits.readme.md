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
