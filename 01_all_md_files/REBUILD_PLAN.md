# RecallOS — Full Rebuild Plan

## Problem
Rebrand and rebuild "MemPalace" into **RecallOS** — a professional AI memory OS with platform-grade naming, cleaner architecture, and new features.

## Canonical Naming Map
- **MemPalace** → **RecallOS** | **Palace** → **Data Vault** | **Wing** → **Domain**
- **Room** → **Node** | **Hall** → **Channel** | **Tunnel** → **Link**
- **Closet** → **Index Summary** | **Drawer** → **Source Record**
- **AAAK** → **RecallScript** | **Knowledge Graph** → **Recall Graph**
- **Specialist Agents** → **Domain Agents** | **Agent Diary** → **Agent Log**

## Phase 1: Package & Module Rename
Rename `mempalace/` → `recallos/`. Delete `mempalace.egg-info/`.

File renames inside `recallos/`:
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
- Keep as-is: `cli.py`, `config.py`, `normalize.py`, `entity_detector.py`, `entity_registry.py`, `general_extractor.py`, `spellcheck.py`, `__init__.py`, `__main__.py`

## Phase 2: Config & Constants Rewrite
In `config.py`:
- `MempalaceConfig` → `RecallOSConfig`
- `DEFAULT_PALACE_PATH` → `DEFAULT_VAULT_PATH` (`~/.recallos/vault`)
- `DEFAULT_COLLECTION_NAME` → `"recallos_records"`
- `palace_path` → `vault_path`, `topic_wings` → `topic_domains`, `hall_keywords` → `channel_keywords`
- Config dir: `~/.mempalace` → `~/.recallos`
- Env vars: `MEMPALACE_PALACE_PATH` → `RECALLOS_VAULT_PATH`

## Phase 3: CLI Rewrite (`cli.py`)
- Entry point: `mempalace` → `recallos`
- `mine` → `ingest`, `search` → `query`, `wake-up` → `bootstrap`, `compress` → `encode`
- Flags: `--palace` → `--vault`, `--wing` → `--domain`, `--room` → `--node`
- Update all imports to new module names
- Update all help text and docstrings

## Phase 4: Core Module Internals
Rewrite internal terminology in every module:
- `retrieval_engine.py`: collection `mempalace_drawers` → `recallos_records`, wing/room params → domain/node
- `ingest_engine.py`: `detect_room()` → `detect_node()`, `SKIP_DIRS` add `.recallos`, config ref `mempalace.yaml` → `recallos.yaml`
- `conversation_ingest.py`: `detect_convo_room()` → `detect_convo_node()`, same collection rename
- `recallscript.py`: All AAAK references → RecallScript, hall refs → channel refs
- `recall_graph.py`: `KnowledgeGraph` → `RecallGraph`, db path `~/.mempalace/knowledge_graph.sqlite3` → `~/.recallos/recall_graph.sqlite3`
- `vault_graph.py`: palace_graph terminology → vault_graph, wing→domain, room→node, tunnel→link, hall→channel
- `memory_layers.py`: Layer class names stay (L0-L3), update wing→domain, room→node, drawer→record, palace→vault, identity path → `~/.recallos/identity_profile.txt`
- `bootstrap.py`: All MemPalace onboarding text → RecallOS, wing→domain
- `mcp_gateway.py`: All 19+ tools renamed `mempalace_*` → `recallos_*`, `PALACE_PROTOCOL` → `RECALL_PROTOCOL`, `AAAK_SPEC` → `RECALLSCRIPT_SPEC`, tool groups renamed
- `node_detector_local.py`: room detection → node detection

## Phase 5: MCP Tool Rename
- `mempalace_status` → `recallos_status`
- `mempalace_list_wings` → `recallos_list_domains`
- `mempalace_list_rooms` → `recallos_list_nodes`
- `mempalace_get_taxonomy` → `recallos_get_topology`
- `mempalace_search` → `recallos_query`
- `mempalace_check_duplicate` → `recallos_check_duplicate`
- `mempalace_get_aaak_spec` → `recallos_get_recallscript_spec`
- `mempalace_add_drawer` → `recallos_add_record`
- `mempalace_delete_drawer` → `recallos_delete_record`
- `mempalace_kg_query` → `recallos_graph_query`
- `mempalace_kg_add` → `recallos_graph_add`
- `mempalace_kg_invalidate` → `recallos_graph_invalidate`
- `mempalace_kg_timeline` → `recallos_graph_timeline`
- `mempalace_kg_stats` → `recallos_graph_stats`
- `mempalace_traverse` → `recallos_traverse_links`
- `mempalace_find_tunnels` → `recallos_find_links`
- `mempalace_graph_stats` → `recallos_topology_stats`
- `mempalace_diary_write` → `recallos_log_write`
- `mempalace_diary_read` → `recallos_log_read`

## Phase 6: Channel Rename
- `hall_facts` → `channel_facts`
- `hall_events` → `channel_events`
- `hall_discoveries` → `channel_discoveries`
- `hall_preferences` → `channel_preferences`
- `hall_advice` → `channel_guidance`

## Phase 7: Memory Stack Rename
- L0 Identity → **Identity Layer**
- L1 Critical Facts → **Core Context Layer**
- L2 Room Recall → **Node Recall Layer**
- L3 Deep Search → **Deep Retrieval Layer**

## Phase 8: Hooks & Examples
- `hooks/mempal_save_hook.sh` → `hooks/recallos_save_hook.sh`
- `hooks/mempal_precompact_hook.sh` → `hooks/recallos_precompact_hook.sh`
- Update all internal references in hook scripts
- `examples/basic_mining.py` → `examples/basic_ingest.py`
- Update example imports and API calls
- Update `examples/mcp_setup.md`

## Phase 9: Tests
Update all 4 test files:
- `test_config.py`: `MempalaceConfig` → `RecallOSConfig`, path refs
- `test_miner.py`: import from `recallos.ingest_engine`
- `test_convo_miner.py`: import from `recallos.conversation_ingest`
- `test_normalize.py`: import from `recallos.normalize`

## Phase 10: pyproject.toml & Package Metadata
- `name = "recallos"`, bump version to `4.0.0`
- Update description: "RecallOS — Local-first AI memory operating system"
- Update all URLs to new repo
- Entry point: `recallos = "recallos:main"`
- Update keywords

## Phase 11: Docs & Supporting Files
- Rewrite `README.md` using the full RecallOS README from `readme_new_rebuild_app.md` (lines 1462-2128)
- Update `CONTRIBUTING.md` references
- Update `benchmarks/README.md`, `benchmarks/BENCHMARKS.md`
- Update `.github/` templates
- Update `hooks/README.md`
- Update `.pre-commit-config.yaml` if it references mempalace
- Update `.gitignore` if needed

## Phase 12: New Features to Build Out
Beyond the rename, these improvements align with the RecallOS identity:
1. **Migration tool** — `recallos migrate` command to auto-migrate existing `~/.mempalace/` data to `~/.recallos/`, rename ChromaDB collections, and update SQLite paths
2. **Backward-compatible config loading** — detect old `~/.mempalace/` dir and warn users to migrate
3. **RecallScript deep integration** — integrate RecallScript encoding directly into Index Summaries during ingest (currently compression is a separate `compress` step)
4. **Improved Domain auto-detection** — smarter entity detection using NLP patterns rather than just keyword matching
5. **Richer Recall Graph queries** — add path-finding between entities, relationship type filtering, and graph visualization export
6. **Agent Log persistence** — file-backed agent logs with RecallScript compression, rotation, and search
7. **Multi-format ingest** — add native support for Slack JSON exports, Discord exports, and Obsidian vaults beyond the current 5 chat formats
8. **`recallos doctor`** — diagnostic command that validates vault integrity, checks for orphaned records, and reports collection health

## Execution Order
Phases 1-2 first (structural foundation), then 3-7 (core logic), then 8-11 (periphery), then 12 (new features). Each phase should be validated with tests before proceeding.
