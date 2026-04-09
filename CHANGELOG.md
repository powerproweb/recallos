# RecallOS Changelog

> **Convention:** A `CHANGELOG.md` lives in the root of every project directory we build.
> It is updated at the end of every dev session — what changed, what was fixed, what's next.
> Format: newest entry at the top, grouped by version/session, tagged with phase.

---

## [4.0.0-dev] — 2026-04-09

### Rebuild: MemPalace → RecallOS (Phases 1–5 + Phase 4 bug fixes)

This session completed the structural and core-logic rename from MemPalace to RecallOS.
All phases follow the spec in `REBUILD_PLAN.md`.

---

### Phase 1 — Package & Module Rename ✅

- Renamed top-level package directory `mempalace/` → `recallos/`
- Deleted `mempalace.egg-info/`
- Renamed all internal modules:
  - `mcp_server.py` → `mcp_gateway.py`
  - `miner.py` → `ingest_engine.py`
  - `convo_miner.py` → `conversation_ingest.py`
  - `searcher.py` → `retrieval_engine.py`
  - `layers.py` → `memory_layers.py`
  - `dialect.py` → `recallscript.py`
  - `knowledge_graph.py` → `recall_graph.py`
  - `palace_graph.py` → `vault_graph.py`
  - `onboarding.py` → `bootstrap.py`
  - `split_mega_files.py` → `transcript_splitter.py`
  - `room_detector_local.py` → `node_detector_local.py`
- Kept as-is: `cli.py`, `config.py`, `normalize.py`, `entity_detector.py`,
  `entity_registry.py`, `general_extractor.py`, `spellcheck.py`, `__init__.py`, `__main__.py`

---

### Phase 2 — Config & Constants ✅

- `config.py`: `MempalaceConfig` → `RecallOSConfig`
- `DEFAULT_PALACE_PATH` → `DEFAULT_VAULT_PATH` (`~/.recallos/vault`)
- `DEFAULT_COLLECTION_NAME` → `"recallos_records"`
- `palace_path` → `vault_path`, `topic_wings` → `topic_domains`, `hall_keywords` → `channel_keywords`
- Config dir: `~/.mempalace` → `~/.recallos`
- Env var: `MEMPALACE_PALACE_PATH` → `RECALLOS_VAULT_PATH`

---

### Phase 3 — CLI Rewrite ✅

- Entry point: `mempalace` → `recallos`
- Commands: `mine` → `ingest`, `search` → `query`, `wake-up` → `bootstrap`, `compress` → `encode`
- Flags: `--palace` → `--vault`, `--wing` → `--domain`, `--room` → `--node`
- All imports updated to new module names
- All help text and docstrings updated

---

### Phase 4 — Core Module Internals ✅ (including bug fixes)

**`ingest_engine.py`**
- Fixed `detect_node()`: was iterating `rooms`/`room` (undefined variables) — renamed to `nodes`/`node`
- Fixed `status()`: was reading ChromaDB metadata with old `wing`/`room` keys — updated to `domain`/`node`
- Updated section comment `PALACE` → `DATA VAULT`
- Fixed inline comment `chars per drawer` → `chars per record`

**`conversation_ingest.py`**
- Fixed critical bug: batch filing referenced `drawer_id` (never assigned) — renamed to `record_id`
- Fixed critical bug: metadata used `"domain": wing` where `wing` was undefined — corrected to `"domain": domain`

**`retrieval_engine.py`**
- Collection name updated: `mempalace_drawers` → `recallos_records`
- Parameters updated: `wing`/`room` → `domain`/`node` throughout

**`recallscript.py`**
- `compress()` method: metadata lookup keys `wing`/`room` → `domain`/`node`
- CLI usage strings: `python dialect.py` → `python recallscript.py`

**`recall_graph.py`**
- `KnowledgeGraph` class → `RecallGraph`
- DB path: `~/.mempalace/knowledge_graph.sqlite3` → `~/.recallos/recall_graph.sqlite3`

**`vault_graph.py`**
- Fixed multiple syntax errors left from incomplete rename:
  - `if Node nd Node = "general" and wing:` → `if node and node != "general" and domain:`
  - `if Node n visited:` → `if node in visited:`
  - `_fuzzy_match()`: broken `any(word in Node or ...)` → `any(word in node for word in ...)`
- Fixed all `room`/`wing`/`hall` variable names → `node`/`domain`/`channel` throughout
  `build_graph()`, `traverse()`, `find_links()`, `graph_stats()`, `_fuzzy_match()`
- Return keys: `total_rooms` → `total_nodes`, `rooms_per_wing` → `nodes_per_domain`, `top_tunnels` → `top_links`
- Updated docstring: `palace_graph.py / MemPalace` → `vault_graph.py / RecallOS`

**`memory_layers.py`**
- Fixed typo: `MAX_recordS` → `MAX_RECORDS` (caused AttributeError at runtime)
- Fixed CLI: `stack.wake_up()` → `stack.bootstrap()` (method didn't exist under old name)
- Fixed CLI flag: `flags.get("palace")` → `flags.get("vault")`
- Updated comment: `full palace` → `full Data Vault`
- Updated identity path: `~/.recallos/identity_profile.txt`

**`bootstrap.py`**
- Renamed `_ask_wings()` → `_ask_domains()`, updated all UI text
- Renamed `_generate_aaak_bootstrap()` → `_generate_recallscript_bootstrap()`
- Updated generated file name: `aaak_entities.md` → `recallscript_entities.md`
- Updated generated section: `## AAAK Quick Reference` → `## RecallScript Quick Reference`
- Updated generated section: `## Palace / Wings:` → `## Data Vault / Domains:`
- Updated `run_onboarding()` call sites and print messages

**`node_detector_local.py`**
- Fixed `detect_nodes_from_folders()`: built `rooms` list but returned `nodes` (NameError) — fixed throughout
- Fixed `detect_nodes_from_files()`: same `rooms`/`nodes` mismatch + `room`/`node_name` loop variable inconsistency
- Fixed `get_user_approval()`: `room` → `node` in enumerate loop
- Fixed `save_config()`: `for r in rooms` → `for n in nodes`
- Fixed `detect_nodes_local()`: all `rooms` references → `nodes`

---

### Phase 5 — MCP Tool Rename ✅

All 19 MCP tool names renamed in `mcp_gateway.py`:

| Old | New |
|---|---|
| `mempalace_status` | `recallos_status` |
| `mempalace_list_wings` | `recallos_list_domains` |
| `mempalace_list_rooms` | `recallos_list_nodes` |
| `mempalace_get_taxonomy` | `recallos_get_topology` |
| `mempalace_search` | `recallos_query` |
| `mempalace_check_duplicate` | `recallos_check_duplicate` |
| `mempalace_get_aaak_spec` | `recallos_get_recallscript_spec` |
| `mempalace_add_drawer` | `recallos_add_record` |
| `mempalace_delete_drawer` | `recallos_delete_record` |
| `mempalace_kg_query` | `recallos_graph_query` |
| `mempalace_kg_add` | `recallos_graph_add` |
| `mempalace_kg_invalidate` | `recallos_graph_invalidate` |
| `mempalace_kg_timeline` | `recallos_graph_timeline` |
| `mempalace_kg_stats` | `recallos_graph_stats` |
| `mempalace_traverse` | `recallos_traverse_links` |
| `mempalace_find_tunnels` | `recallos_find_links` |
| `mempalace_graph_stats` | `recallos_topology_stats` |
| `mempalace_diary_write` | `recallos_log_write` |
| `mempalace_diary_read` | `recallos_log_read` |

Additional `mcp_gateway.py` changes:
- `PALACE_PROTOCOL` → `RECALL_PROTOCOL` (updated all tool name references inside the string)
- `AAAK_SPEC` → `RECALLSCRIPT_SPEC` (updated all AAAK → RecallScript language)
- `_kg` variable → `_rg` (was referencing undefined `_kg`; actual variable is `_rg = RecallGraph()`)
- All metadata: `wing`/`room`/`hall` → `domain`/`node`/`channel`
- IDs: `drawer_*` prefix → `record_*`
- Agent Diary → Agent Log: `tool_diary_write/read` → `tool_log_write/read`
- Server info: `name: "mempalace"`, `version: "2.0.0"` → `name: "recallos"`, `version: "4.0.0"`
- Startup log: `"MemPalace MCP Server starting..."` → `"RecallOS MCP Gateway starting..."`
- Tool parameter renames: `wing/room` → `domain/node`, `start_room` → `start_node`, `wing_a/b` → `domain_a/b`, `drawer_id` → `record_id`, `source_closet` → `source_record`

---

---

## [4.0.0-dev] — 2026-04-09 (session 2)

### Phase 6 — Channel Rename ✅ (verified clean)

- Audited all `.py` files: zero `hall_facts`, `hall_events`, `hall_discoveries`, `hall_preferences`, `hall_advice`, or `hall_diary` references remain.
- Channel rename was fully completed as part of Phase 4/5 work.

---

### Phase 7 — Memory Stack Rename ✅

`memory_layers.py` remaining items fixed:
- Module docstring: `layers.py` → `memory_layers.py`, layer descriptions updated to canonical names:
  - L0 → **Identity Layer**, L1 → **Core Context Layer**, L2 → **Node Recall Layer**, L3 → **Deep Retrieval Layer**
- L1 section comment: `Essential Story (auto-generated from palace)` → `Core Context (auto-generated from vault)`
- L1 docstring: `records in the palace` → `records in the vault`
- L3 section comment: `Deep Search` → `Deep Retrieval`
- L3 class docstring: `full palace` → `full Data Vault`
- `MemoryStack` docstring: `one palace` → `one vault`, `stack.wake_up()` → `stack.bootstrap()`
- `MemoryStack.status()`: `top palace records` → `top vault records`
- CLI usage block: `layers.py` → `memory_layers.py`, `wake-up` → `bootstrap`, `Deep L3 search` → `Deep L3 retrieval`

---

### Phase 8 — Hooks & Examples ✅

**Hook scripts renamed:**
- `mempal_save_hook.sh` → `recallos_save_hook.sh`
- `mempal_precompact_hook.sh` → `recallos_precompact_hook.sh`

**Hook script content updated (`recallos_save_hook.sh`):**
- Header: `MEMPALACE SAVE HOOK` → `RECALLOS SAVE HOOK`
- `diary + palace entries` → `log + vault entries`
- `wing/hall/closet` → `domain/node`
- `STATE_DIR`: `~/.mempalace/hook_state` → `~/.recallos/hook_state`
- `MEMPAL_DIR` var → `RECALLOS_DIR`
- `python3 -m mempalace mine` → `python3 -m recallos ingest`
- All path references to old filename updated

**Hook script content updated (`recallos_precompact_hook.sh`):**
- Same changes as save hook above
- `python3 -m mempalace mine` (synchronous) → `python3 -m recallos ingest`

**`hooks/README.md`:** Full rewrite — all MemPalace/mempal/palace/wings references replaced with RecallOS/recallos/vault/domains

**Examples renamed and updated:**
- `basic_mining.py` → `basic_ingest.py`: `mempalace init/mine/search` → `recallos init/ingest/query`, `rooms` → `nodes`
- `convo_import.py`: `mempalace mine ... --wing` → `recallos ingest ... --domain`
- `mcp_setup.md`: Full rewrite — `mcp_server.py` → `mcp_gateway.py`, all 19 tool names listed with new `recallos_*` names, grouped by category

---

---

## [4.0.0-dev] — 2026-04-09 (session 3)

### Phase 9 — Tests ✅

**`test_config.py`**
- Import: `from mempalace.config import MempalaceConfig` → `from recallos.config import RecallOSConfig`
- All `MempalaceConfig` → `RecallOSConfig`
- Assertions: `cfg.palace_path` → `cfg.vault_path`, `"palace"` → `"vault"`, `"mempalace_drawers"` → `"recallos_records"`
- Config file key: `palace_path` → `vault_path`, value `/custom/palace` → `/custom/vault`
- Env var: `MEMPALACE_PALACE_PATH` / `/env/palace` → `RECALLOS_VAULT_PATH` / `/env/vault`

**`test_miner.py`** (renamed test function: `test_project_mining` → `test_project_ingest`)
- Import: `from mempalace.miner import mine` → `from recallos.ingest_engine import mine`
- Config file: `mempalace.yaml` → `recallos.yaml`
- YAML keys: `wing` → `domain`, `rooms` → `nodes`
- Variables: `palace_path` → `vault_path`
- Collection: `mempalace_drawers` → `recallos_records`
- Added `del col, client` before `shutil.rmtree(ignore_errors=True)` — fixes Windows file-lock issue with ChromaDB

**`test_convo_miner.py`** (renamed test function: `test_convo_mining` → `test_convo_ingest`)
- Import: `from mempalace.convo_miner import mine_convos` → `from recallos.conversation_ingest import mine_convos`
- Kwarg: `wing="test_convos"` → `domain="test_convos"`
- Variables: `palace_path` → `vault_path`
- Collection: `mempalace_drawers` → `recallos_records`
- Added same `del col, client` + `ignore_errors=True` fix

**`test_normalize.py`**
- Import: `from mempalace.normalize import normalize` → `from recallos.normalize import normalize`

**Result: 9/9 tests pass** (`pytest 9.0.3`, Python 3.12.10, Windows)

---

---

## [4.0.0-dev] — 2026-04-09 (session 4)

### Phase 10 — pyproject.toml ✅

- `name`: `"mempalace"` → `"recallos"`
- `version`: `"3.0.0"` → `"4.0.0"`
- `description`: updated to `"RecallOS — Local-first AI memory operating system. No API key required."`
- `keywords`: added `"recallos"`, `"recall-os"`, `"memory-os"`, `"agent-memory"`
- `[project.urls]`: all three URLs updated from `milla-jovovich/mempalace` → `milla-jovovich/recallos`
- `[tool.setuptools.packages.find]`: `include = ["mempalace*"]` → `include = ["recallos*"]`
- `[project.scripts]`: `mempalace = "mempalace:main"` → `recallos = "recallos:main"`
- Verified: `import recallos`, `from recallos.config import RecallOSConfig`, and `from recallos import main` all resolve correctly
- Verified: 9/9 tests still pass after change

---

## Remaining Work

| Phase | Status | Description |
|---|---|---|
| 11 | ❌ Not started | Docs (README rewrite from readme_new_rebuild_app.md) |
| 12 | ❌ Not started | New Features (migration tool, doctor command, multi-format ingest, etc.) |
