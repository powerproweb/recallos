# RecallOS Landing Page — BUILD Plan

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
