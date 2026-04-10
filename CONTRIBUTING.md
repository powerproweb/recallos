# Contributing to RecallOS

Thanks for wanting to help. RecallOS is open source and we welcome contributions of all sizes — from typo fixes to new features.

## Getting Started

```bash
git clone https://github.com/milla-jovovich/recallos.git
cd recallos
pip install -e ".[dev]"    # installs with dev dependencies (pytest, build, twine)
```

## Running Tests

```bash
pytest tests/ -v
```

All tests must pass before submitting a PR. Tests run without API keys or network access — ChromaDB is the only I/O dependency and uses temporary directories.

## Running Benchmarks

```bash
# Quick test (20 questions, ~30 seconds)
python benchmarks/longmemeval_bench.py /path/to/longmemeval_s_cleaned.json --limit 20

# Full benchmark (500 questions, ~5 minutes)
python benchmarks/longmemeval_bench.py /path/to/longmemeval_s_cleaned.json
```

See [benchmarks/README.md](benchmarks/README.md) for data download instructions and reproduction guide.

## Project Structure

```
recallos/           ← core package
  cli.py            ← CLI entry point (all commands)
  config.py         ← configuration loading and defaults
  ingest_engine.py  ← project file ingest
  conversation_ingest.py  ← conversation ingest
  retrieval_engine.py     ← semantic retrieval (ChromaDB)
  memory_layers.py  ← 4-layer memory stack (L0–L3)
  recall_graph.py   ← temporal entity-relationship graph (SQLite)
  vault_graph.py    ← node navigation graph (built from ChromaDB metadata)
  recallscript.py   ← RecallScript compression dialect
  mcp_gateway.py    ← MCP server — 22 tools, RecallScript auto-teach
  bootstrap.py      ← guided vault setup
  normalize.py      ← converts 7 chat formats to standard transcript
  migration.py      ← migrate ~/.mempalace/ data to ~/.recallos/
  diagnostics.py    ← vault health checks (recallos doctor)
  agent_log.py      ← file-backed agent logs
  node_detector_local.py  ← detect nodes from folder structure
  entity_detector.py      ← auto-detect people and projects from content
  entity_registry.py      ← entity code registry
  transcript_splitter.py  ← split concatenated transcripts
benchmarks/         ← reproducible benchmark runners
hooks/              ← Claude Code auto-save hooks
examples/           ← usage examples
tests/              ← test suite (54 tests)
assets/             ← logo + brand
```

## PR Guidelines

1. Fork the repo and create a feature branch: `git checkout -b feat/my-thing`
2. Write your code
3. Add or update tests — `tests/` must continue to pass with `pytest tests/ -v`
4. Run `pytest tests/ -v` — all 54 tests must pass
5. Commit with a clear message following [conventional commits](https://www.conventionalcommits.org/):
   - `feat: add Notion export format`
   - `fix: handle empty transcript files`
   - `docs: update MCP tool descriptions`
   - `test: add coverage for agent_log.py`
   - `bench: add LoCoMo turn-level metrics`
6. Push to your fork and open a PR against `main`

## Code Style

- **Formatting**: [Ruff](https://docs.astral.sh/ruff/) with 100-char line limit (configured in `pyproject.toml`)
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes
- **Docstrings**: on all modules and public functions
- **Type hints**: where they improve readability
- **Dependencies**: minimize. ChromaDB + PyYAML only. Don't add new deps without discussion.

## Good First Issues

Check the [Issues](https://github.com/milla-jovovich/recallos/issues) tab. Great starting points:

- **New chat formats**: Add import support for Cursor, Copilot, Notion, or other AI tool exports (`normalize.py`)
- **Node detection**: Improve pattern matching in `node_detector_local.py`
- **Tests**: Increase coverage — `vault_graph.py`, `recall_graph.py`, `agent_log.py`, `normalize.py` new parsers
- **Entity detection**: Better name disambiguation in `entity_detector.py`
- **Graph visualization**: CLI export command wrapping `RecallGraph.export_dot()` / `export_json()`
- **Docs**: Improve examples, add tutorials

## Architecture Principles

If you're planning a significant change, open an issue first to discuss the approach. Key principles:

- **Verbatim first**: Never summarize user content. Store exact words.
- **Local first**: Everything runs on the user's machine. No cloud dependencies.
- **Zero API by default**: Core features must work without any API key.
- **Structure matters**: Domains, Channels, and Nodes aren't cosmetic — they drive a 34% retrieval improvement. Respect the hierarchy.
- **Backward compatible**: New features should not break existing vaults or config files.

## Community

- **Discord**: [Join us](https://discord.com/invite/ycTQQCu6kn)
- **Issues**: Bug reports and feature requests welcome
- **Discussions**: For questions and ideas

## License

MIT — your contributions will be released under the same license.
