# RecallOS Web — CLI to Web Service Roadmap

## Current Architecture

RecallOS is a Python package with a CLI entry point (`cli.py`), an MCP gateway (`mcp_gateway.py`), and a set of pure-Python core modules. All data lives locally in ChromaDB (`~/.recallos/vault`) and SQLite (`recall_graph.sqlite3`).

The key architectural fact: **the MCP tool functions already return plain dicts**, and `search_memories()` already returns a dict. The API layer is mostly already written — it just has no HTTP server in front of it.

---

## What Needs Changing Before a Web Layer Can Sit On Top

Three things in the current codebase are not web-safe:

- `retrieval_engine.search()` calls `sys.exit()` on error — needs to raise exceptions
- `ingest_engine.mine()` / `conversation_ingest.mine_convos()` read from local file paths — web ingest needs file upload + temp dir
- Several CLI functions print to stdout rather than returning data — fine for CLI, irrelevant for API callers who already use the programmatic variants

---

## Phases

### Phase W1 — API-Readiness Refactor (1–2 days)

Target: make every core function safe to call from a web context.

**`retrieval_engine.py`**: replace `sys.exit()` calls with `raise` or `return {"error": ...}`. The programmatic `search_memories()` already does this correctly — the `search()` CLI wrapper just needs cleaning.

**`ingest_engine.py`** and **`conversation_ingest.py`**: extract a `mine_from_content(content, filename, domain, node, vault_path)` variant that accepts pre-read content instead of a file path. The existing `mine()` / `mine_convos()` stay intact for CLI use.

**`bootstrap.py`**: `get_user_approval()` uses `input()` — make interactive prompts optional (already has a `--yes` flag path; just needs an `interactive=False` parameter).

No new dependencies. No new files. Pure refactor.

---

### Phase W2 — FastAPI Backend (3–5 days)

New directory: `recallos/api/`

```
recallos/api/
  __init__.py
  app.py          ← FastAPI app, CORS, startup
  routes/
    vault.py      ← status, query, topology, domains, nodes
    ingest.py     ← file upload → temp dir → mine()
    graph.py      ← add_triple, query_entity, find_path, timeline, export
    logs.py       ← write, read, search, rotate
    health.py     ← doctor checks
  auth.py         ← API key middleware (single key for self-hosted)
  deps.py         ← shared FastAPI dependencies (config, vault path)
```

**Key design decisions:**

- **Every MCP tool function becomes a route** — `tool_status()` → `GET /api/status`, `tool_query()` → `POST /api/query`, etc. Minimal new logic.
- **Ingest via file upload**: `POST /api/ingest` accepts multipart/form-data. Files saved to a temp dir, processed by `mine_from_content()`, temp dir deleted on completion.
- **Background tasks for ingest**: FastAPI's `BackgroundTasks` so large ingests don't block the HTTP response. Returns a job ID; poll `GET /api/ingest/{job_id}` for status.
- **Single API key auth** for self-hosted: `X-API-Key` header checked by middleware. Key stored in `~/.recallos/config.json` or an environment variable.

New dependencies: `fastapi>=0.100`, `uvicorn>=0.22`, `python-multipart` (for file uploads).

---

### Phase W3 — Web Frontend (3–5 days)

New directory: `recallos/web/` (static files served by FastAPI)

Stack: **HTML + Alpine.js + Tailwind CDN** — no build step, no Node.js required, deployable as static files.

```
recallos/web/
  index.html      ← dashboard (vault status, recent records)
  query.html      ← search interface
  ingest.html     ← file upload + progress indicator
  graph.html      ← D3.js graph visualization (uses export_json())
  logs.html       ← agent log viewer + keyword search
  health.html     ← doctor report
```

The graph page uses `RecallGraph.export_json()` — already built — fed into a D3.js force-directed layout. This is the highest-value visual page and requires no new backend work.

No build pipeline. FastAPI serves the static files via `StaticFiles`.

---

### Phase W4 — Docker + Deployment (1–2 days)

**`Dockerfile`:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e ".[web]"
VOLUME /root/.recallos
EXPOSE 8000
CMD ["uvicorn", "recallos.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`docker-compose.yml`**: mounts `~/.recallos` as a volume so the vault persists across container restarts.

**nginx config**: reverse proxy on port 443, SSL termination via Let's Encrypt (`certbot`). Point the domain DNS A record at the server IP, run `certbot --nginx`, done.

New optional dependency group `[web]` in `pyproject.toml`: `fastapi`, `uvicorn`, `python-multipart`.

---

### Phase W5 — Optional: Multi-User SaaS (separate product decision)

If RecallOS ever becomes a hosted service rather than a self-hosted tool, this phase adds:

- User registration and JWT auth
- Per-user vault isolation (`~/.recallos/users/<user_id>/vault`)
- Admin panel
- Usage metering and billing hooks

This contradicts the current "local-first, free, no subscription" identity and should be treated as a separate product decision, not an upgrade to the existing tool.

---

## Dependency Map

```
Phase W1 (refactor) ──→ Phase W2 (API) ──→ Phase W3 (frontend)
                                         └──→ Phase W4 (Docker)

Phase W5 is independent and optional
```

---

## What Does NOT Change

- All existing CLI commands continue to work identically
- All 154 tests continue to pass
- ChromaDB storage format is unchanged
- The MCP gateway is unchanged — AI agents can still use it in parallel with the web UI
- `pip install recallos` installs only the CLI by default; `pip install recallos[web]` adds FastAPI

---

## Estimated Total Effort

- **W1 + W2 + W3 + W4**: ~2 weeks for a working self-hosted web UI
- The graph visualization page (W3, D3.js) is the most open-ended piece — everything else is mechanical wrapping of existing code
- **W5 (multi-user SaaS)**: 2–3 months minimum, separate product decision
