# RecallOS Landing Page — BUILD Plan

### -<<<|||>>>--<<<|||>>>--<<<|||>>>- BEGIN - DESCRIPTIONS -<<<|||>>>--<<<|||>>>--<<<|||>>>- ###

# Prompt for Descriptions: I need these descriptions of this project... 
	* 290 Character - Github Description:
	* long complete description:
	* short & precise description:
	* About us page desc:
	* Homepage hero desc:
	* Polished promotional Desc:
	
	from the build.plan.features.benefits.md or something like this.
	
	After this create a GitHub.README.md also

# ChatGPT - BUILD_plan.md Description - Polished promotional description:
RecallOS transforms forgetful AI into a long-term thinking partner. It captures your conversations, project files, decisions, and knowledge in a structured local memory vault, then makes that history instantly retrievable for Claude, ChatGPT, and offline models. No cloud. No API key. No subscription. Just fast, private, persistent memory that compounds in value every time you use it. Whether you are building products, leading teams, researching ideas, or managing long-running AI workflows, RecallOS keeps the full context of your work alive and ready when you need it.

# ChatGPT - BUILD_plan.md Description - Homepage hero / intro version:
Your AI remembers everything.
RecallOS gives Claude, ChatGPT, and local models a private, local-first memory system for conversations, files, decisions, and facts, so you never have to repeat yourself again.

# ChatGPT - BUILD_plan.md Description - About Us Page:
We built RecallOS because modern AI forgets too much. Every new session starts cold, and valuable decisions, project history, and context disappear unless users manually repeat them. That wastes time, breaks continuity, and makes AI far less useful than it should be.

RecallOS solves that by giving AI a local-first memory system that stores conversations, files, notes, and structured facts in a searchable vault on your own machine. Our goal is to make AI feel continuous, reliable, and context-aware without sacrificing privacy, ownership, or control. No cloud lock-in. No recurring fees. No black-box memory service. Just durable, structured memory that helps AI work the way people expect it to: by remembering what matters.

# ChatGPT - BUILD_plan.md Description - Longest:
RecallOS is a local-first AI memory operating system built to give AI assistants durable, structured, retrievable memory across time. Instead of starting every session from zero, RecallOS lets Claude, ChatGPT, Cursor, local Llama models, and other text-based AI systems work with a persistent memory layer that remembers your projects, decisions, conversations, preferences, milestones, and facts. It is designed for people who rely on AI every day and are tired of losing context, repeating themselves, and watching valuable reasoning disappear from one session to the next.

At its core, RecallOS stores memory in a structured local vault on your machine using a hierarchical architecture built around domains, nodes, channels, index summaries, source records, and cross-domain links. Domains act as top-level containers for projects, people, or topics. Nodes organize subtopics within each domain. Channels standardize memory into categories such as facts, events, discoveries, preferences, and guidance. Index summaries make retrieval fast for AI, while source records preserve the original wording verbatim so nothing important gets abstracted away or lost in summarization. The system also creates automatic links across domains when shared nodes appear in multiple places, allowing memory to connect across projects and contexts.

RecallOS is powered by a fully local storage backend using ChromaDB, with no server requirement and no cloud dependency. By default, the vault lives in the user’s local environment and can be reconfigured by file path or environment variable. It stores both full verbatim records and optional compressed RecallScript records in separate collections, giving users a flexible balance between completeness and context efficiency. Everything is designed to run under the user’s control, on the user’s hardware, with the user’s data staying private.

The system is built to ingest large amounts of real working history. RecallOS can recursively scan project folders, chunk readable files into structured records, detect the right node for each file using folder paths, filenames, and weighted keyword scoring, and skip content that has already been ingested through deduplication. It supports dry runs, custom domain tagging, file limits, and simultaneous RecallScript encoding during ingest. It also supports conversation ingest, including exchange-pair chunking for user/AI interactions and extraction modes that classify material into decisions, preferences, milestones, problems, and emotional context. Conversation ingest uses improved domain detection through bigram patterns, normalized scoring, and batch filing for efficiency.

RecallOS also supports a wide set of import formats out of the box, making it possible to bring in the history users already have instead of forcing them to start fresh. Supported formats include plain text transcripts, Claude.ai JSON, ChatGPT conversations.json, Claude Code JSONL sessions, Slack JSON exports, Discord JSON exports, and Obsidian vault notes with frontmatter stripping and wikilink conversion. It also includes a transcript splitter for breaking apart concatenated multi-session files and an initialization flow that auto-detects people, projects, and topic nodes from file content, folder structure, and filename patterns. This initialization system includes interactive approval, manual adjustment, and downstream config saving for future ingest use.

One of RecallOS’s most distinctive features is RecallScript, a custom compression dialect designed to reduce memory size dramatically while preserving meaning. The system claims roughly 30x lossless compression, allowing the same information to fit into far fewer tokens without requiring a decoder. RecallScript uses entity codes, emotional markers, structured fields, ISO dates, importance ratings, and count notation so that modern language models can interpret compressed memory directly as text. It works offline, supports on-demand encoding through the CLI, can encode by domain or dry-run for previewing ratios, and can be applied inline during ingest so both full and compressed memory are stored at the same time. RecallScript and the broader recall protocol can also be auto-taught to models through MCP bootstrap responses.

To make persistent memory practical for everyday AI use, RecallOS includes a layered memory stack that separates always-loaded identity and core context from deeper topic recall and unlimited semantic retrieval. Its four-layer architecture includes an identity layer, a core context layer, a node recall layer, and a deep retrieval layer. The bootstrap system generates a compact startup context that includes who the AI is, how it should behave, current project state, important recent facts, and top moments from the vault. This lets an AI load meaningful context at the start of a session in roughly a few hundred tokens instead of requiring the user to re-explain months of work.

RecallOS also includes a Recall Graph, a local temporal entity-relationship graph stored in SQLite. This graph tracks people, projects, relationships, facts, time windows, confidence, and source attribution. It supports adding and updating typed entities, adding triples with validity windows, invalidating facts when they are no longer true, bulk seeding known facts, querying entities as of a point in time, retrieving timelines, querying relationships, running path-finding between entities, exporting to DOT or JSON, and detecting contradictions. This allows AI systems to check whether a fact is still current before answering and helps prevent errors involving wrong dates, outdated ownership, attribution conflicts, stale tenures, or invalid assumptions. In practical terms, it gives AI a way to verify instead of guess.

In addition to the Recall Graph, RecallOS includes a Vault Graph for navigating knowledge across domains. It builds graph structure directly from vault metadata rather than from a separate database, treats nodes as ideas that appear across the memory system, and identifies shared nodes that act as bridges across different projects or subject areas. Users can traverse the graph by hop distance, discover cross-domain links, inspect the most connected topics, and better understand how knowledge is distributed through the vault. This gives RecallOS not just retrieval, but navigable structure.

RecallOS is built for integration with AI workflows through an MCP gateway with 22 tools. These tools cover vault inspection, domain and node listing, semantic querying, duplicate checking, RecallScript specification access, record creation and deletion, graph querying and editing, timeline retrieval, relationship path-finding, topology statistics, link traversal, and agent log operations. The embedded RECALL_PROTOCOL instructs models to bootstrap first, query memory before answering, avoid guessing, write logs after sessions, and update facts when they change. This turns RecallOS into an operational memory substrate for MCP-compatible assistants rather than just a passive database.

The platform also supports persistent agent logs, allowing specialist agents to maintain their own daily journals of work history. These logs are file-backed, optionally indexed in ChromaDB for semantic search, organized by date and agent, readable in reverse chronology, searchable by keyword, and rotatable after a configured number of days. This makes RecallOS useful not just for human memory continuity, but also for long-running AI agent workflows where different assistants need to retain their own operating histories.

Operational reliability is built in through diagnostics, migration tools, configuration layers, and test coverage. RecallOS includes a doctor command that checks vault accessibility, collection health, incomplete records, SQLite integrity, identity profile presence, config validity, and legacy MemPalace traces. It includes migration tooling to move data from MemPalace into RecallOS, including old Chroma collections, a knowledge graph, identity profile, and config mappings, with dry-run and force options. Configuration follows a clear priority system of environment variables over config file over defaults, and supports identity profile files, domain lists, channel keyword maps, canonical people maps, and vault path overrides. The project is also packaged as a Python library, installable via pip, importable through a documented API surface, and supported by a sizeable automated test suite across core subsystems with CI/CD and pre-commit tooling in place.

Performance is a major part of the project’s positioning. The feature doc cites retrieval metrics across a 22,000+ memory test set, with gains from global summary search to domain-scoped, channel-scoped, and node-scoped retrieval, culminating in a reported 94.8% R@10 for domain-plus-node search. It also cites 96.6% raw LongMemEval R@5 and 100% hybrid LongMemEval R@5 with optional reranking. The user-benefits doc frames this as proof that RecallOS is not just a storage system, but a retrieval system that can bring back the right memory at the right time while remaining local and low cost.

From the user’s perspective, RecallOS solves a simple but painful problem: AI forgets everything unless the user keeps re-teaching it. The project is explicitly designed so users no longer lose decisions, no longer waste time re-explaining projects, no longer pay for cloud memory layers they do not control, and no longer have to worry that six months of AI-assisted work has become inaccessible. Instead, RecallOS lets users search exact prior reasoning, resume dormant projects quickly, import existing AI and team history, bootstrap assistants with minimal context, verify facts before speaking, and run fully offline if needed. It is especially positioned for developers, team leads, researchers, privacy-conscious users, offline users, and heavy AI users who want continuity without cloud lock-in.

Economically, RecallOS presents itself as an alternative to expensive cloud memory products and token-heavy summary pipelines. The benefits doc contrasts local operation and extremely low annual cost against subscription-based tools and API-driven memory approaches. The broader value proposition is that RecallOS compounds in usefulness over time: the more files, transcripts, decisions, logs, and conversations you feed into it, the more context your AI has available, and the more useful that AI becomes.

Technically, philosophically, and operationally, RecallOS is built around a clear promise: your AI should remember your world without sending your world anywhere else. It does not summarize away the why. It does not require internet access. It does not depend on subscription infrastructure. It does not overwrite or modify your source files. It does not force a proprietary hosted service between the user and their own memory. Instead, it gives users a local operating system for AI memory: structured storage, semantic retrieval, compression, graph-based fact tracking, agent continuity, diagnostics, migration, and integration tooling in one open-source package.

Condensed polished version of that same long description

RecallOS is a local-first AI memory operating system that gives AI assistants persistent, structured memory across conversations, files, projects, and time. It ingests chat histories, project code, transcripts, notes, and exports from tools like ChatGPT, Claude, Slack, Discord, and Obsidian into a searchable local vault, preserving original source material while building fast retrieval layers on top. With domains, nodes, channels, semantic search, RecallScript compression, a temporal Recall Graph, a navigable Vault Graph, agent logs, diagnostics, migration tools, and a 22-tool MCP gateway, RecallOS turns forgetful AI into a context-aware system that can recall exact past reasoning, verify facts before speaking, and resume work with minimal bootstrap context. It runs locally, works offline, requires no API key or subscription, integrates with Claude, ChatGPT, Cursor, and local models, and is built for developers, researchers, team leads, and serious AI users who want private, durable, open-source memory that compounds in value over time.


# ChatGPT - BUILD_plan.md Description - Long:
RecallOS is a local-first AI memory operating system that gives AI assistants persistent, structured memory without relying on cloud storage, subscriptions, or API keys. It ingests conversations, project files, transcripts, notes, and exports from tools like ChatGPT, Claude, Slack, Discord, and Obsidian into a searchable memory vault on your machine.

Instead of forcing you to repeat yourself in every new session, RecallOS helps your AI remember decisions, project history, people, preferences, debugging steps, and important facts across time. It stores original source content, builds compressed retrieval layers, supports semantic search, generates lightweight bootstrap context for fast session startup, and includes a fact-aware Recall Graph so your AI can check what is true before responding. It also provides MCP tools, agent logging, migration utilities, diagnostics, and optional RecallScript compression for much smaller context footprints.

The result is simple: your AI starts with context, retrieves exact past reasoning when needed, and works more like a true long-term collaborator. Everything stays local, private, and under your control.

# ChatGPT - BUILD_plan.md Description - Short:
RecallOS gives AI persistent memory on your machine, so it can remember conversations, files, decisions, and facts across sessions without cloud storage or subscriptions.

# ChatGPT - GitHub.README.md Description: 
RecallOS is a local-first AI memory operating system that gives AI assistants persistent, structured memory across sessions, projects, files, and time. Instead of losing context every time a chat ends, RecallOS stores conversations, project files, notes, transcripts, and decisions in a searchable local vault on your machine, so your AI can recall what happened, why it happened, and what changed. It works with Claude, ChatGPT, Cursor, and local models, and it runs without a cloud backend, API key, or subscription.

RecallOS combines structured memory storage, semantic retrieval, RecallScript compression, a temporal fact graph, a vault navigation graph, persistent agent logs, and an MCP gateway with 22 tools into one system. It can ingest project directories, AI chat exports, Slack and Discord exports, Obsidian notes, and plain-text transcripts, then organize them into domains, nodes, and channels for high-precision retrieval. The original source material is preserved verbatim, while compressed and indexed layers make memory fast and practical for AI use.

The goal is simple: stop repeating yourself to AI. With RecallOS, your assistant can bootstrap with lightweight context, retrieve exact past decisions, verify facts before answering, track changes over time, and keep long-running work coherent across sessions. It is designed for developers, researchers, team leads, privacy-conscious users, and anyone building serious workflows around AI who wants memory that is private, durable, open source, and fully under local control.

Here is a slightly more punchy README opener too:

README Opener Version

RecallOS is a local-first AI memory operating system for Claude, ChatGPT, Cursor, and local models. It gives AI persistent memory for conversations, files, decisions, and facts, so you never have to re-explain your work again. No cloud. No API key. No subscription. Just private, structured, searchable memory that stays on your machine.

And an even tighter version for the very top of the repo:

Short README Header Version

RecallOS gives AI persistent local memory across chats, files, projects, and time, with structured storage, semantic retrieval, fact tracking, and MCP integration. Fully offline. Open source. No subscription.

# ChatGPT - GitHub.README.md Description2: 

RecallOS

Private AI memory that actually lasts.

RecallOS is a local-first AI memory operating system for Claude, ChatGPT, Cursor, and local models. It gives AI persistent memory across chats, files, decisions, people, and projects, so you never have to re-explain your work from scratch.

Store conversations, project files, transcripts, notes, and facts in a structured local vault. Retrieve exact past reasoning. Bootstrap new sessions with context. Verify facts before your AI responds. Keep everything offline and fully under your control.

No cloud. No API key. No subscription.

Features
Local-first structured memory vault
Semantic search across conversations and files
Verbatim source preservation
RecallScript compression
Temporal fact graph
Vault navigation graph
Persistent agent logs
MCP tools for AI integration
Offline operation
Open-source Python package and CLI


# Get Started - terminal command
----------
pip install recallos
recallos init ~/projects/myapp
recallos ingest ~/chats --mode convos
recallos query "what did we decide about auth"

Built For

Developers, researchers, team leads, and serious AI users who want private, durable, searchable memory that compounds in value over time.

And here is a very tight README top block for a modern repo:

RecallOS

Local-first AI memory OS for Claude, ChatGPT, Cursor, and local models.

Persistent memory for conversations, files, decisions, and facts. Structured, searchable, private, and fully offline.

# terminal command
----------
pip install recallos

No cloud. No API key. No subscription.

# ChatGPT - 290 Character - Github Description: 
RecallOS is a local-first AI memory operating system that helps Claude, ChatGPT, and local models remember conversations, files, decisions, and facts across time. No cloud, no API key, no subscription. Fast retrieval, structured memory, and fully offline control.

### -<<<|||>>>--<<<|||>>>--<<<|||>>>- END - DESCRIPTIONS -<<<|||>>>--<<<|||>>>--<<<|||>>>- ###

## Overview
Build a 2-page long-scrolling landing site for RecallOS v4.0.0. Page 1 covers **Features**, Page 2 covers **User Benefits**. All copy at a 5th-grade reading level. Color palette: dark maroon, deep blue, gold accents, turquoise trim.

## Color Palette & Design System

### Core Colors
- **Background base:** deep navy (`#0a0f1e` range) with maroon glow zones (`#4a0e1e` range)
- **Card surfaces:** dark maroon overlays, deep navy blocks
- **Primary accent:** gold — buttons, dividers, trim lines
- **Secondary accent:** turquoise — icons, hover states, glow
- **Text:** soft white, light gray

### Cards
- Soft dark surfaces, thin gold border, turquoise icon glow, large rounded corners

### Buttons
- Primary: gold fill or gold outline
- Secondary: turquoise outline or dark fill with turquoise text

### Typography
- Large bold hero headlines
- Short simple body copy
- Generous line spacing
- No dense paragraphs above the fold

### Visual Rhythm (repeat per section)
- Big headline → short paragraph → 3 bullets or 1 example → illustration/mockup → spacing
- Alternate layouts: text-left/visual-right, visual-left/text-right, full-width center, card row, story block

## Navigation
- Logo | Features | Benefits | How It Works | Get Started | GitHub
- Right-side CTA button: **Get Started**

---

## PAGE 1 — FEATURES

Goal: answer **"What is inside RecallOS?"**

### Section 1 — Hero
- Label: `Local-First AI Memory`
- Headline: **Your AI remembers what matters**
- Subheadline: **RecallOS saves chats, files, and decisions on your own computer so your AI can find them later.**
- Buttons: `See Features` | `See Benefits`
- Micro-trust row: Offline-ready · No cloud needed · No subscription · Open source
- Right side: product mockup / glowing vault illustration

### Section 2 — "What RecallOS Does" (4-card grid)
1. **Saves your work**
2. **Helps AI remember**
3. **Finds old answers**
4. **Keeps data private**

Support line: *Everything stays on your machine and is easy to search later.*

### Section 3 — Save Everything in One Place
*(Data Vault: Domains, Nodes, Channels, Source Records, Links)*
- Layout: left illustration / right text
- Headline: **Keep chats, files, and ideas in one smart place**
- Bullets: Sort by project or topic · Keep original words · Connect related ideas

### Section 4 — Bring In What You Already Have
*(Ingest Engine: 7 import formats)*
- Layout: left text / right logo/file-type cards
- Headline: **Import the tools you already use**
- Cards: ChatGPT · Claude · Slack · Discord · Notes · Plain text · Project files
- Copy: *You do not need to start over. Point RecallOS to your files and chats, and it pulls them in.*

### Section 5 — Start Each Session With Context
*(Memory Stack: L0–L3, Bootstrap)*
- Layout: full-width story section with layered "AI memory loading" visual
- Headline: **Help your AI start with the right background**
- 3-step flow: 1. Load who you are → 2. Load current project facts → 3. Load what matters most now

### Section 6 — Find Old Decisions Fast
*(Retrieval Engine, verbatim storage)*
- Layout: left query-box UI mockup / right text + example result
- Headline: **Find the reason behind past decisions**
- Example: search "Why did we switch databases?" → old session found, date shown, exact wording shown

### Section 7 — Check Facts Before AI Answers
*(Recall Graph, contradiction detection)*
- Layout: left text / right relationship map or timeline UI
- Headline: **Help your AI avoid old or wrong facts**
- Examples: who worked on what · when a change happened · what is still current

### Section 8 — Works With Your Setup
*(MCP Gateway, CLI, Python API, local models)*
- Layout: 3 horizontal cards
1. **Use it with Claude Code**
2. **Use it with local AI**
3. **Use it with Python tools**

### Section 9 — Private by Design
- Layout: dark premium band with gold trim
- Headline: **Your data stays yours**
- Trust bullets: Runs locally · Works offline · No cloud storage required · No subscription required

### Section 10 — CTA
- Headline: **Now see what this means for you**
- Buttons: `See User Benefits` | `Get Started`

---

## PAGE 2 — USER BENEFITS

Goal: answer **"Why should I care?"** — more emotional, more human, less technical.

### Section 1 — Benefits Hero
- Headline: **Stop repeating yourself to AI** (alt: **Nothing important gets lost**)
- Subheadline: **RecallOS helps your AI remember past work, so you can get back to building faster.**
- Background art: memory threads / glowing archive / calm futuristic dashboard

### Section 2 — The Problem (4 pain-point cards)
1. **You explain the same thing again**
2. **Old choices are hard to find**
3. **Team knowledge gets buried**
4. **AI forgets last time**

### Section 3 — Before / After Transformation
- Layout: tall split — left "before" / right "after"
- Headline: **From lost context to clear memory**
- Before: *"I know we talked about this before."*
- After: *"Found it. Here is the exact reason."*

### Section 4 — Benefit: Save Time
- Headline: **Spend less time re-explaining**
- Copy: Your AI starts with background context instead of a blank slate.

### Section 5 — Benefit: Find Old Answers
- Headline: **Find past choices in seconds**
- Copy: Search old chats, notes, and project files when you need them.

### Section 6 — Benefit: Keep Momentum
- Headline: **Jump back into any project fast**
- Copy: Even after weeks or months away, your AI can help you pick up where you left off.

### Section 7 — Benefit: Improve Over Time
- Headline: **Your AI gets more useful as you use it**
- Copy: More saved history means better help later.

### Section 8 — Benefit: Protect Privacy
- Headline: **Keep your work on your own computer**
- Copy: Good for users who want control, privacy, and offline use.

### Section 9 — Benefit: Spend Less Money
- Layout: simple comparison strip (not a complex pricing table)
- Headline: **Avoid costly memory tools**
- Copy: RecallOS keeps costs low by running locally.

### Section 10 — "Who This Helps" (5 profile cards)
1. Solo developers
2. Team leads
3. Researchers
4. Privacy-first users
5. Local AI builders

### Section 11 — 3 Use-Case Stories
- **Solo builders:** You remember why you made a choice months ago.
- **Teams:** Decisions from chats and meetings do not disappear.
- **Private workflows:** Your memory system stays local and under your control.

### Section 12 — Easy Getting Started
- Headline: **Start in a few simple steps**
1. Install RecallOS
2. Connect your project or chats
3. Let it organize your memory
4. Ask better questions later

### Section 13 — Final CTA
- Headline: **Give your AI a memory that lasts**
- Buttons: `Get Started` | `View Features Again` | `See the Code`

---

## Message Order Summary

### Features page
1. What it is → 2. What it saves → 3. What it imports → 4. How it helps AI remember → 5. How it finds answers → 6. How it checks facts → 7. Why it is private → 8. CTA

### Benefits page
1. What pain it solves → 2. What gets easier → 3. How it saves time → 4. How it protects privacy → 5. How it helps different users → 6. How to start → 7. CTA

---
## Tech Stack
- **Static site** — plain HTML + CSS + vanilla JS (no framework, no build step)
- CSS: custom properties for the palette, no Tailwind (keep it dependency-free to match RecallOS philosophy)
- JS: IntersectionObserver for scroll animations, smooth-scroll polyfill, sticky nav highlight
- Hosting: Apache (shared or VPS) — `.htaccess` included for hardening, caching, compression
- Alternative deploy targets: GitHub Pages, Netlify, Vercel (all work with static HTML)

## Finalized Color Palette (hex values)
- `--bg-base: #080c1a` — deepest navy, main background
- `--bg-maroon: #1a0a12` — dark maroon panel backgrounds
- `--bg-card: #0f1225` — card / section surface
- `--accent-gold: #d4a843` — primary accent (buttons, dividers, trim)
- `--accent-gold-hover: #e6be5a` — gold hover / active state
- `--accent-turquoise: #2ec4b6` — secondary accent (icons, glow, hover)
- `--accent-turquoise-hover: #3dd9ca` — turquoise hover
- `--text-primary: #f0ede8` — soft white for body text
- `--text-secondary: #a8a4a0` — light gray for support copy
- `--text-muted: #6b6662` — muted labels
- `--border-gold: rgba(212, 168, 67, 0.25)` — subtle gold card borders
- `--glow-turquoise: rgba(46, 196, 182, 0.15)` — icon glow behind turquoise elements

## Font Stack
- **Headlines:** `'Inter', 'Segoe UI', system-ui, sans-serif` — weight 700/800
- **Body:** same family, weight 400
- **Mono (code snippets):** `'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace`
- Load via Google Fonts `<link>` with `display=swap`; subset to `latin`

## Responsive Design
- **Desktop:** ≥1200 px — full alternating layouts
- **Tablet:** 768–1199 px — stack to single-column, shrink card grids to 2-col
- **Mobile:** <768 px — single column, hamburger nav, full-width cards, larger tap targets (≥48 px)
- Hero illustration hides on mobile; replaced with a smaller inline badge graphic
- All images use `srcset` / `<picture>` for 1× and 2× density

## Accessibility
- Contrast: all text/background combos must pass **WCAG AA** (4.5:1 body, 3:1 large text)
  - `#f0ede8` on `#080c1a` = 15.3:1 ✔
  - `#d4a843` on `#080c1a` = 8.2:1 ✔
  - `#2ec4b6` on `#080c1a` = 7.9:1 ✔
- All images get descriptive `alt` text
- Buttons and nav links have visible `:focus-visible` ring (turquoise outline)
- Skip-to-content link at top of page
- Semantic HTML: `<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`, `<article>`
- `prefers-reduced-motion` media query disables scroll animations
- `prefers-color-scheme` — not needed (site is dark-only by design)

## SEO & Meta
- `<title>`: RecallOS — Local-First AI Memory. No Cloud. No Subscription.
- `<meta name="description">`: Your AI remembers what matters. Save chats, files, and decisions on your own computer.
- Open Graph: `og:title`, `og:description`, `og:image` (1200×630 share card), `og:url`, `og:type=website`
- Twitter Card: `twitter:card=summary_large_image`, same image
- Favicon: 32×32 `.ico` + 180×180 Apple touch icon + 192×192 Android icon
- `<link rel="canonical">` on every page
- Structured data: `Organization` + `SoftwareApplication` JSON-LD
- `robots.txt` allowing all crawlers
- `sitemap.xml` with both pages

## Scroll UX & Animations
- **Sticky nav:** becomes opaque on scroll (`backdrop-filter: blur`) with gold bottom-border
- **Active section highlighting:** IntersectionObserver marks current nav link with turquoise underline
- **Smooth scroll:** `scroll-behavior: smooth` on `html`; polyfill for older browsers
- **Back-to-top button:** appears after scrolling past hero, gold circle with arrow, bottom-right fixed
- **Section entrance animations:** fade-up (translateY 30px → 0, opacity 0 → 1) triggered at 15% viewport intersection
- **Card hover:** subtle lift (`translateY(-4px)`) + turquoise glow intensifies
- **Hero:** slight parallax on background illustration (CSS `transform` on scroll, no heavy library)
- **All animations** respect `prefers-reduced-motion: reduce`

## Proof Metrics Band
Place this as a slim full-width strip **between Hero and the 4-card grid** on Page 1. These are RecallOS's strongest differentiators and should not be buried.
- **96.6%** — LongMemEval R@5, zero API calls
- **100%** — LongMemEval R@5 with optional Haiku rerank
- **30×** — RecallScript lossless compression ratio
- **$0.70/yr** — total memory cost vs $507/yr for LLM summaries
- Small subtext: *Highest LongMemEval score ever published — free or paid.*

### Cost Comparison (for Benefits Page Section 9)
Use these actual numbers in the comparison strip:
- Paste everything into context → **Impossible** (doesn't fit)
- LLM-generated summaries → **~$507/yr**
- Cloud memory services (Mem0, Zep) → **$228–$2,988/yr**
- **RecallOS → ~$0.70–$10/yr**

## Social Proof & Trust Signals
Place in the footer and/or as a slim band before the final CTA on each page:
- GitHub stars badge (live via `shields.io`)
- PyPI version badge
- Discord community link (existing server)
- `154 tests passing` badge
- MIT License badge
- `Python 3.9–3.12` badge

## Footer (both pages)
- Left: RecallOS logo + one-line tagline
- Center columns: Features | Benefits | Docs | GitHub | PyPI | Discord
- Right: `pip install recallos` copy-to-clipboard snippet
- Bottom bar: MIT License · © 2026 RecallOS · Privacy (minimal, no tracking)
- Gold top-border line

## "How It Works" Mini-Section
The nav references "How It Works" — place it as a **bridge between Page 1 Section 9 (Private by Design) and Section 10 (CTA)**:
1. Install → `pip install recallos`
2. Set up → `recallos init ~/projects/myapp`
3. Import → `recallos ingest ~/chats/ --mode convos`
4. Connect → `claude mcp add recallos -- python -m recallos.mcp_gateway`
5. Done → your AI handles the rest
Keep code snippets small, inside styled terminal-window mockups.

## Asset Requirements
- **Logo:** exists at `assets/recallos_logo.png` — create SVG version for web
- **OG share card:** 1200×630 branded image
- **Favicon set:** .ico + apple-touch-icon + android-chrome
- **Section illustrations:** 6–8 simple vector/SVG illustrations (vault, import logos, memory layers, graph, query mockup, privacy shield, terminal window)
- **Platform logos:** ChatGPT, Claude, Slack, Discord, Obsidian — use official marks or simple styled icons
- **Terminal mockup component:** CSS-only styled `<pre>` block with title bar dots

## Hosting & Deployment
- **Live URL:** https://quantumstoryforge.io/recallos/
- Hosted on Apache shared hosting with `.htaccess` hardening
- `.htaccess` includes: HTTPS redirect, security headers, gzip/brotli, browser caching, hotlink protection, bot blocking, error pages, clean URLs
- All 6 core files verified live (HTTP 200, sizes match local build)

---

## Things to Avoid Above the Fold
- Test counts / raw recall metrics
- CLI command overload
- Database names (ChromaDB, SQLite)
- Table-heavy technical detail
- Dense paragraphs

These belong in expandable "learn more" areas lower on each page.

---

## Project Status — Deployed 2026-04-10

### Delivered Files (13 files under `site/`)
- `index.html` (23 KB) — Features page with hero, proof metrics band, 7 feature sections, How It Works, CTA
- `benefits.html` (20 KB) — Benefits page with problem cards, before/after, 6 benefit sections, cost comparison, user profiles, stories, getting started
- `css/styles.css` (25 KB) — Full design system: 12 CSS custom properties, responsive breakpoints (desktop/tablet/mobile), cards, buttons, terminal mockup, scroll animations, accessibility
- `js/main.js` (5 KB) — IntersectionObserver fade-ups, sticky nav with blur, active section highlighting, hamburger toggle, back-to-top, pip-copy clipboard
- `.htaccess` (14 KB) — HTTPS redirect, security headers (HSTS, CSP, X-Frame), gzip/brotli, browser caching, clean URLs, hotlink protection, bot blocking, exploit prevention
- `robots.txt` — allows all crawlers, points to sitemap
- `sitemap.xml` — both pages with lastmod dates
- `errors/400.html`, `401.html`, `403.html`, `404.html`, `500.html`, `503.html` — branded error pages matching site design

### Implemented from Plan
- All Page 1 sections (hero through CTA): done
- All Page 2 sections (hero through final CTA): done
- Color palette with exact hex values: done (CSS custom properties)
- Font stack (Inter + JetBrains Mono via Google Fonts): done
- Responsive design (3 breakpoints, hamburger nav): done
- Accessibility (WCAG AA contrast, skip-link, focus-visible, prefers-reduced-motion, semantic HTML): done
- SEO (OG tags, Twitter Card, JSON-LD, canonical, robots.txt, sitemap.xml): done
- Scroll UX (sticky nav, fade-up animations, back-to-top, active nav highlighting): done
- Proof metrics band (96.6%, 100%, 30x, $0.70/yr): done
- Cost comparison strip with actual dollar figures: done
- Social proof badges (shields.io): done
- Footer with pip-copy clipboard: done
- "How It Works" 5-step section with terminal mockup: done
- All navigation verified with relative paths (works via file:// and on server): done

### Deployment Verified
- **Live URL:** https://quantumstoryforge.io/recallos/
- `index.html` — 200 OK, 22,746 bytes ✔
- `benefits.html` — 200 OK, 20,203 bytes ✔
- `css/styles.css` — 200 OK, 25,281 bytes ✔
- `js/main.js` — 200 OK, 5,203 bytes ✔
- `robots.txt` — 200 OK, 70 bytes ✔
- `sitemap.xml` — 200 OK, 441 bytes ✔
- PR #1 merged into `master` — all CI checks passed (Lint, Python 3.10/3.11/3.12)

### Remaining Polish Items
- **Assets to create:** `assets/og-card.png` (1200x630), `assets/favicon.ico`, `assets/apple-touch-icon.png` — referenced in HTML but not yet created
- **Replace illustration placeholders:** 8 sections have `[ illustration ]` placeholder divs — replace with SVGs or graphics
- **Discord link:** footer link is `href="#"` — update when Discord URL is available
- **Canonical URLs:** `sitemap.xml` and `<link rel="canonical">` reference `recallos.dev` — update to `quantumstoryforge.io/recallos` or final domain
- **`.htaccess` hotlink rules:** reference `recallos.(dev|io|com)` — add `quantumstoryforge.io` to the allowlist
