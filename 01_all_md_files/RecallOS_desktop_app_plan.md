# RecallOS Desktop App — Implementation Plan

Transform RecallOS from a CLI/library package (v4.0.0) into a shippable, installable desktop application with a local web UI, layered search, and proper desktop distribution.

## Current State

RecallOS is a Python CLI package (`recallos/`) with:
- CLI entry (`cli.py`), MCP gateway (`mcp_gateway.py`), retrieval/ingest engines
- ChromaDB for vector storage, SQLite-based Recall Graph
- Data Vault architecture (Domains, Nodes, Channels, Index Summaries, Source Records)
- RecallScript compression, agent logs, diagnostics
- Dependencies: `chromadb>=0.4.0`, `pyyaml>=6.0`, Python 3.9+
- No GUI, no desktop shell, no installer

## Target Architecture

- **Desktop shell** → pywebview (native window, app lifecycle)
- **Frontend** → React + Vite + TypeScript (bundled static assets; zero remote/CDN dependencies)
- **Service API** → FastAPI + Uvicorn (localhost-only; random port; per-session internal auth token)
- **Storage** → SQLite (settings, jobs, audit) + existing ChromaDB (vector search)
- **Search** → ripgrep (instant scan) + SQLite FTS5 (indexed retrieval) + ChromaDB semantic
- **Embeddings/runtime** → explicit offline embedding provider + model-pack manager (no implicit downloads)
- **Security** → OS keychain for secrets + optional “Vault Lock” (encryption at rest) + scoped filesystem roots
- **Packaging** → PyInstaller → signed installer + signed, verifiable updates (Windows first)

## Sovereignty Requirements (World-Class Bar)

A “sovereign” RecallOS desktop app must be provably user-owned, offline-capable, and verifiable.

Non-negotiables:
- **Offline-first after install:** ingest, query, export, diagnostics work with all network disabled; no implicit model downloads.
- **Network governance + transparency:** global “Disable all network” switch, per-feature toggles (updates, connectors, telemetry), and a visible network activity log. Frontend loads **zero** remote assets.
- **Encryption + local control:** secrets stored in OS secure storage; optional vault/database encryption; user-controlled storage locations.
- **Portability + recovery:** backup/restore, snapshots, and exports to open formats; rollback-safe upgrades.
- **Supply-chain integrity:** signed installers/updates, signature verification before applying, build provenance display, third-party licenses/SBOM in-app.
- **Safety boundaries:** localhost-only API, per-session auth token, least-privilege file access, and an audit log for privileged actions.

## Proposed Directory Structure

```
recallos/
├── recallos/                  # existing core package (unchanged)
├── desktop/                   # NEW — desktop app layer
│   ├── app.py                 # pywebview shell entry point
│   ├── server.py              # FastAPI app + Uvicorn launcher
│   ├── routes/                # API route modules
│   │   ├── api_connections.py
│   │   ├── upload.py
│   │   ├── download.py
│   │   ├── search.py
│   │   ├── graph.py
│   │   ├── backups.py
│   │   ├── network.py
│   │   ├── models.py
│   │   ├── support.py
│   │   └── settings.py
│   ├── services/              # business logic bridging routes → core
│   │   ├── search_service.py  # ripgrep + FTS5 + semantic unification
│   │   ├── job_manager.py     # background task queue
│   │   ├── secrets_store.py   # OS-native credential storage
│   │   ├── model_manager.py   # offline model packs + verification
│   │   ├── network_policy.py  # allow/deny + per-feature toggles + logging
│   │   ├── backup_service.py  # backup/restore/snapshots
│   │   └── crypto_service.py  # vault/db encryption helpers
│   ├── models/                # Pydantic models / DB schemas
│   ├── db.py                  # SQLite session (settings, jobs, audit)
│   ├── static/                # built React frontend assets
│   └── assets/                # bundled rg binary, model packs, icons
├── frontend/                  # NEW — React/Vite/TS source
│   ├── src/
│   │   ├── pages/             # Dashboard, APIConnections, Upload, Download, Search, Graph, Backups, Network, Models, Support, Settings
│   │   ├── components/
│   │   ├── hooks/
│   │   └── api/               # typed fetch wrappers
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── installer/                 # NEW — platform installer configs
│   └── windows/
│       └── recallos.iss       # Inno Setup script
├── recallos.spec              # NEW — PyInstaller spec
└── pyproject.toml             # updated with new deps
```

## Phase 0 — Discovery & Proof of Concept

Goal: Prove the desktop shell launches, serves the frontend, and communicates with the existing RecallOS core — while meeting the sovereignty non-negotiables.

### 0.0 Core API-readiness refactor (required)
- Remove `sys.exit()` and interactive prompts from core modules when called programmatically; replace with exceptions or structured `{ "error": ... }` returns.
- Keep CLI behavior identical by moving printing/exiting into CLI wrappers only.
- Add a small test slice proving core calls behave correctly in “service mode”.

### 0.1 Project scaffolding
- Create `desktop/` directory with `app.py`, `server.py`, `db.py`
- Add new dependencies to `pyproject.toml`: `fastapi`, `uvicorn`, `pywebview`, `aiosqlite`, `python-multipart`
- Create `frontend/` with Vite + React + TypeScript scaffold (no CDN assets)

### 0.2 Sovereignty guardrails (early)
- Add per-session internal auth token required on every `/api/*` call from the UI.
- Introduce a `network_policy` abstraction (allow/deny) that all update checks and connectors must use.
- Add a build-time check that the frontend bundle contains no external `http(s)://` asset references.

### 0.3 pywebview shell (`desktop/app.py`)
- Launch a pywebview window pointing at `http://127.0.0.1:{port}`
- Start Uvicorn in a background thread before opening the window
- Use a random available port; pass it to the frontend via query param or env
- Handle graceful shutdown: closing the window stops Uvicorn

### 0.4 FastAPI service layer (`desktop/server.py`)
- Mount the built React static assets at `/`
- Create a `/api/status` health endpoint that calls `recallos.diagnostics`
- Bind exclusively to `127.0.0.1`

### 0.5 Minimal React frontend
- Single-page app with sidebar navigation (placeholder pages)
- Dashboard page calling `/api/status` and rendering vault overview
- Vite build outputs to `desktop/static/`

### 0.6 Deterministic offline runtime spike
- Decide and implement an explicit offline embedding provider for ChromaDB (no implicit downloads).
- Add a “Model Manager” stub UI that shows embedding provider + model pack hash/path.
- Add an “offline mode” smoke test gate: run with network disabled and verify dashboard/status/search.

### 0.7 PyInstaller proof
- Create `recallos.spec` that bundles `desktop/`, `recallos/`, and `desktop/static/`
- Verify the resulting `.exe` opens the pywebview window on Windows

**Exit criteria:** App opens a native window showing the dashboard with live vault status, and passes the offline/no-egress smoke gate. PyInstaller exe works on a clean Windows VM.

## Phase 1 — MVP Features (Sovereign Windows v1)

Goal: Usable end-to-end on Windows with a polished UI and the core sovereignty guarantees in place.

### 1.1 SQLite local database (`desktop/db.py`)
- Schema: `settings`, `api_connections`, `jobs`, `job_events`, `audit_log`
- Use SQLite WAL mode for concurrent reads during indexing
- Store DB at `~/.recallos/desktop.db`
- Design DB with an encryption upgrade path (SQLCipher) and versioned migrations.

### 1.2 API Connections page
- CRUD for connector configs (name, type, auth_type, scopes, endpoint)
- Token test endpoint that validates credentials
- All outbound requests must go through `network_policy` (respects global “Disable all network”).
- Secrets stored via `desktop/services/secrets_store.py` (Windows Credential Manager via `keyring`; fallback to encrypted local storage)
- Show last sync time, failure reason, retry action per connector

### 1.3 Upload page
- Drag-and-drop + file picker (pywebview native file dialog)
- Queue view with progress, validation errors, duplicate detection
- Backend calls existing `recallos.ingest_engine` and `recallos.conversation_ingest`
- Background jobs via `desktop/services/job_manager.py` (threaded task queue with SQLite-backed state)
- Optional watched-folders mode (incremental ingest) with clear pause/resume controls
- Show accepted file types, size limits, processing result

### 1.4 Download / Export page
- Export vault data, RecallScript outputs, query results
- Destination picker (pywebview save dialog)
- Job history with re-download and open-folder actions
- Overwrite warning before replacing existing files
- Open-format exports (JSONL/CSV) for portability

### 1.5 Search page (v1 — hybrid MVP)
- **Layer 1 — ripgrep instant search:** shell out to bundled `rg` binary for filename/path/content scan
- **Layer 2 — SQLite FTS5:** create `search_index` FTS5 table; index vault records, filenames, and metadata on ingest
- **Layer 3 — ChromaDB semantic:** bridge to existing `recallos.retrieval_engine.search_memories()`
- Unified search box with filters and mode toggle (instant / indexed / semantic)
- Keyboard navigation, preview pane, source badges
- Recent and saved searches stored in SQLite
- Must not perform network calls during search/embedding (uses explicit offline model)

### 1.6 Graph page (trust + insight)
- Visualize Recall Graph using existing export functions (JSON/DOT).
- Visualize Vault Graph (cross-domain/node links).
- Provide safe filters and “export graph data” action.

### 1.7 Backups & Restore (portability)
- One-click backup of vault + desktop DB + config + model packs (encrypted option).
- Restore flow with verification (checksums, version compatibility).
- Snapshot support (manual at MVP; scheduling can move to Phase 2).

### 1.8 Network & Privacy (transparency)
- Settings UI:
  - Global “Disable all network”
  - Per-feature toggles: update checks, connectors, telemetry
  - Telemetry off by default
- Network Activity Log page (host, path, feature, timestamp, success/failure).

### 1.9 Model Manager (no implicit downloads)
- Show embedding provider, model pack path, and SHA256.
- Install/import model packs from local file (offline) and verify checksums.
- Provide “offline-ready” status gate in the dashboard.

### 1.10 Support page
- Links to docs and self-help resources (external links open outside the app window)
- System info display (OS, Python version, vault path, DB size, ChromaDB status)
- Self-test diagnostics calling `recallos.diagnostics.doctor()`
- Recent error log viewer
- One-click “Export Diagnostic Bundle” with preview + redaction controls (ensure no secrets)

### 1.11 Settings page
- Vault path, index location, indexing rules (include/exclude folders)
- Theme toggle (light/dark)
- Update channel selector (stable/beta)
- Privacy controls (telemetry opt-in/out)
- Diagnostic bundle content preview
- Third-party licenses + build info view

### 1.12 Dashboard
- Recent jobs with status
- Global search bar (routes to Search page)
- Indexing status indicators and alerts for failed jobs
- Offline-ready + network-policy status indicators
- Quick actions: New ingest, Run doctor, Export bundle, Backup now

### 1.13 Background mode (desktop feel)
- System tray icon (running/indexing state, quick actions)
- Background jobs continue when window is closed (configurable)

### 1.14 MCP Setup page (AI integration)
- Guided setup for MCP clients, with health check and “copy command” UX.
- Show available tools and last-call status.

**Exit criteria:** All primary screens functional. Upload → ingest → search round-trip works. Backup/restore works. Offline/no-egress gate passes. Installer installs/uninstalls cleanly on Windows.

## Phase 2 — Stabilization, Trust, and Sovereignty Hardening

Goal: Production-quality desktop experience with strong supportability, security boundaries, and verifiable supply chain.

### 2.1 Structured logging
- Python `logging` with JSON formatter writing to `~/.recallos/logs/`
- Log rotation (7 days retained)
- Frontend error boundary sends errors to `/api/log` endpoint

### 2.2 Crash reporting
- Global exception handler in `desktop/app.py` that writes crash dump
- Crash recovery: detect unclean shutdown on next launch, offer to re-index

### 2.3 Updater + offline update bundles
- Version check against a release endpoint on startup (configurable and governed by `network_policy`).
- Download updates only with explicit user confirmation.
- Verify update signatures before applying.
- Support importing an offline update bundle (air-gapped install) with the same signature verification.

### 2.4 Vault Lock + encryption at rest
- Optional passphrase unlock on launch (“Vault Lock”).
- Encrypt desktop SQLite DB (SQLCipher or equivalent) when Vault Lock is enabled.
- Define and implement approach for vault/Chroma at-rest protection (OS-encrypted directory vs app-level encryption), and document tradeoffs.

### 2.5 Security hardening
- Bind FastAPI to `127.0.0.1` only
- Enforce per-session internal API auth token
- Whitelist frontend-to-backend routes; reject unknown paths
- Constrain file-system operations to approved roots
- Enforce `network_policy` for every outbound-capable feature
- Audit log for privileged actions (credential changes, exports, path changes, restore operations)

### 2.6 Supply-chain transparency
- Build provenance panel (version, build time, commit hash, signing certificate fingerprint).
- Third-party licenses screen.
- Generate an SBOM as part of release artifacts.

### 2.7 QA + release gates
- Installer/uninstaller test on clean virtual machines.
- Upgrade + rollback test from at least two prior versions.
- Offline/no-egress test (core features still work).
- Backup/restore test (restore must be verifiable).
- Crash recovery test during indexing and downloads.
- Large corpus search performance test.

**Exit criteria:** Signed installer and verifiable updates. Support bundles and backups enable real field triage and recovery. Offline/no-egress gate passes reliably.

## Phase 3 — Search Depth

Goal: Search becomes flagship quality.

### 3.1 Document extraction pipeline
- PDF text extraction via `pdfplumber` or `pymupdf`
- DOCX extraction via `python-docx`
- Pluggable extractor interface for future formats
- Extracted text indexed into FTS5 and ChromaDB

### 3.2 Advanced ranking
- Recency boost, field weighting (title > body > path)
- Result deduplication across search layers
- Snippet highlighting in preview pane

### 3.3 Saved searches & notifications
- Save search queries with filters
- Optional background re-run with change detection

**Exit criteria:** Search covers PDF/DOCX content. Ranking produces noticeably better results on large corpora.

## Phase 4 — Cross-Platform

Goal: macOS and Linux packaging maturity.

### 4.1 macOS
- PyInstaller app bundle
- Signed + notarized DMG via `create-dmg`
- Keychain integration for secrets

### 4.2 Linux
- AppImage and `.deb` packaging
- `secret-tool` / `libsecret` for credential storage

**Exit criteria:** Installer works on macOS 13+ and Ubuntu 22.04+.

## New Dependencies (added to pyproject.toml)

Python (desktop/service layer):
- `fastapi` — local API layer
- `uvicorn[standard]` — ASGI server
- `python-multipart` — file uploads from the UI
- `pywebview` — native desktop window
- `aiosqlite` — async SQLite access
- `keyring` — OS-native secret storage
- `cryptography` — signature verification + encryption utilities
- `watchdog` — watched folders / file change detection
- `pystray` — system tray integration
- (TBD per platform) SQLCipher binding — encrypted SQLite when Vault Lock is enabled
- (TBD) offline embedding provider/runtime — model packs must be explicit and checksummed

Search/extraction (Phase 3):
- `pdfplumber` — PDF extraction
- `python-docx` — DOCX extraction

Frontend (separate `package.json`):
- `react`, `react-dom`, `react-router-dom`
- `vite`, `typescript`
- `@tanstack/react-query` — data fetching
- `tailwindcss` — styling

## Key Design Decisions

1. **pywebview over Electron** — Keeps Python as center of gravity, smaller footprint, direct JS-Python bridge. Tauri sidecar is the upgrade path if needed.
2. **Existing `recallos/` package untouched** — Desktop layer wraps and calls into the core package. CLI and MCP gateway continue to work independently.
3. **Hybrid search (ripgrep + FTS5 + ChromaDB)** — Instant scan + indexed retrieval + semantic search in layers. No external search server.
4. **Explicit offline embeddings + model packs** — No implicit downloads. Models are installed/imported deliberately and verified.
5. **Network governance + zero-remote-assets UI** — Global network kill switch, per-feature toggles, network activity log, and a frontend bundle that ships fully locally.
6. **Portability + recovery as product features** — Backup/restore/snapshots and open-format exports are first-class.
7. **Strong local boundaries** — Localhost-only API, per-session auth token, least-privilege filesystem access, and auditable privileged actions.
8. **Signed installers + verifiable updates** — Signature verification before apply, with build provenance and SBOM/license transparency.
9. **Windows first** — Primary target. macOS/Linux follow in Phase 4.
