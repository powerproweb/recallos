#!/usr/bin/env python3
"""
RecallOS — Local-first AI memory operating system. No API key required.

Two ways to ingest:
  Projects:      recallos ingest ~/projects/my_app          (code, docs, notes)
  Conversations: recallos ingest ~/chats/ --mode convos     (Claude, ChatGPT, Slack)

Same Data Vault. Same query. Different ingest strategies.

Commands:
    recallos init <dir>                   Detect nodes from folder structure
    recallos split <dir>                  Split concatenated mega-files into per-session files
    recallos ingest <dir>                 Ingest project files (default)
    recallos ingest <dir> --mode convos   Ingest conversation exports
    recallos query "query"                Find anything, exact words
    recallos bootstrap                    Show L0 + L1 bootstrap context
    recallos bootstrap --domain my_app    Bootstrap for a specific project
    recallos status                       Show what's been filed

Examples:
    recallos init ~/projects/my_app
    recallos ingest ~/projects/my_app
    recallos ingest ~/chats/claude-sessions --mode convos
    recallos query "why did we switch to GraphQL"
    recallos query "pricing discussion" --domain my_app --node costs
"""

import os
import sys
import argparse
from pathlib import Path

from .config import RecallOSConfig


def cmd_init(args):
    import json
    from pathlib import Path
    from .entity_detector import scan_for_detection, detect_entities, confirm_entities
    from .node_detector_local import detect_nodes_local

    # Pass 1: auto-detect people and projects from file content
    print(f"\n  Scanning for entities in: {args.dir}")
    files = scan_for_detection(args.dir)
    if files:
        print(f"  Reading {len(files)} files...")
        detected = detect_entities(files)
        total = len(detected["people"]) + len(detected["projects"]) + len(detected["uncertain"])
        if total > 0:
            confirmed = confirm_entities(detected, yes=getattr(args, "yes", False))
            # Save confirmed entities to <project>/entities.json for the miner
            if confirmed["people"] or confirmed["projects"]:
                entities_path = Path(args.dir).expanduser().resolve() / "entities.json"
                with open(entities_path, "w") as f:
                    json.dump(confirmed, f, indent=2)
                print(f"  Entities saved: {entities_path}")
        else:
            print("  No entities detected — proceeding with directory-based rooms.")

    # Pass 2: detect nodes from folder structure
    detect_nodes_local(project_dir=args.dir)
    RecallOSConfig().init()


def cmd_mine(args):
    vault_path = os.path.expanduser(args.vault) if args.vault else RecallOSConfig().vault_path

    if args.mode == "convos":
        from .conversation_ingest import mine_convos

        mine_convos(
            convo_dir=args.dir,
            vault_path=vault_path,
            domain=args.domain,
            agent=args.agent,
            limit=args.limit,
            dry_run=args.dry_run,
            extract_mode=args.extract,
            encode=getattr(args, "encode", False),
        )
    else:
        from .ingest_engine import mine

        mine(
            project_dir=args.dir,
            vault_path=vault_path,
            domain_override=args.domain,
            agent=args.agent,
            limit=args.limit,
            dry_run=args.dry_run,
            encode=getattr(args, "encode", False),
        )


def cmd_query(args):
    from .retrieval_engine import search

    vault_path = os.path.expanduser(args.vault) if args.vault else RecallOSConfig().vault_path
    search(
        query=args.query,
        vault_path=vault_path,
        domain=args.domain,
        node=args.node,
        n_results=args.results,
    )


def cmd_bootstrap(args):
    """Show L0 (Identity Layer) + L1 (Core Context Layer) — the bootstrap context."""
    from .memory_layers import MemoryStack

    vault_path = os.path.expanduser(args.vault) if args.vault else RecallOSConfig().vault_path
    stack = MemoryStack(vault_path=vault_path)

    text = stack.bootstrap(domain=args.domain)
    tokens = len(text) // 4
    print(f"Bootstrap context (~{tokens} tokens):")
    print("=" * 50)
    print(text)


def cmd_split(args):
    """Split concatenated transcript mega-files into per-session files."""
    from .transcript_splitter import main as split_main
    import sys

    # Rebuild argv for transcript_splitter argparse
    argv = [args.dir]
    if args.output_dir:
        argv += ["--output-dir", args.output_dir]
    if args.dry_run:
        argv.append("--dry-run")
    if args.min_sessions != 2:
        argv += ["--min-sessions", str(args.min_sessions)]

    old_argv = sys.argv
    sys.argv = ["recallos split"] + argv
    try:
        split_main()
    finally:
        sys.argv = old_argv


def cmd_doctor(args):
    """Run vault health diagnostics."""
    from .diagnostics import run_doctor

    vault_path = os.path.expanduser(args.vault) if args.vault else None
    run_doctor(vault_path=vault_path, verbose=args.verbose)


def cmd_migrate(args):
    """Migrate legacy ~/.mempalace/ data to ~/.recallos/."""
    from .migration import migrate_from_mempalace

    migrate_from_mempalace(dry_run=args.dry_run, force=args.force)


def cmd_status(args):
    from .ingest_engine import status

    vault_path = os.path.expanduser(args.vault) if args.vault else RecallOSConfig().vault_path
    status(vault_path=vault_path)


def cmd_encode(args):
    """Encode source records in a domain using RecallScript."""
    import chromadb
    from .recallscript import Dialect

    vault_path = os.path.expanduser(args.vault) if args.vault else RecallOSConfig().vault_path

    # Load dialect (with optional entity config)
    config_path = args.config
    if not config_path:
        for candidate in ["entities.json", os.path.join(vault_path, "entities.json")]:
            if os.path.exists(candidate):
                config_path = candidate
                break

    if config_path and os.path.exists(config_path):
        dialect = Dialect.from_config(config_path)
        print(f"  Loaded entity config: {config_path}")
    else:
        dialect = Dialect()

    # Connect to Data Vault
    try:
        client = chromadb.PersistentClient(path=vault_path)
        col = client.get_collection("recallos_records")
    except Exception:
        print(f"\n  No Data Vault found at {vault_path}")
        print("  Run: recallos init <dir> then recallos ingest <dir>")
        sys.exit(1)

    # Query records in the domain
    where = {"domain": args.domain} if args.domain else None
    try:
        kwargs = {"include": ["documents", "metadatas"]}
        if where:
            kwargs["where"] = where
        results = col.get(**kwargs)
    except Exception as e:
        print(f"\n  Error reading records: {e}")
        sys.exit(1)

    docs = results["documents"]
    metas = results["metadatas"]
    ids = results["ids"]

    if not docs:
        domain_label = f" in domain '{args.domain}'" if args.domain else ""
        print(f"\n  No records found{domain_label}.")
        return

    print(
        f"\n  Encoding {len(docs)} records"
        + (f" in domain '{args.domain}'" if args.domain else "")
        + "..."
    )
    print()

    total_original = 0
    total_compressed = 0
    compressed_entries = []

    for doc, meta, doc_id in zip(docs, metas, ids):
        compressed = dialect.compress(doc, metadata=meta)
        stats = dialect.compression_stats(doc, compressed)

        total_original += stats["original_chars"]
        total_compressed += stats["compressed_chars"]

        compressed_entries.append((doc_id, compressed, meta, stats))

        if args.dry_run:
            domain_name = meta.get("domain", "?")
            node_name = meta.get("node", "?")
            source = Path(meta.get("source_file", "?")).name
            print(f"  [{domain_name}/{node_name}] {source}")
            print(
                f"    {stats['original_tokens']}t -> {stats['compressed_tokens']}t ({stats['ratio']:.1f}x)"
            )
            print(f"    {compressed}")
            print()

    # Store encoded versions (unless dry-run)
    if not args.dry_run:
        try:
            comp_col = client.get_or_create_collection("recallos_encoded")
            for doc_id, compressed, meta, stats in compressed_entries:
                comp_meta = dict(meta)
                comp_meta["compression_ratio"] = round(stats["ratio"], 1)
                comp_meta["original_tokens"] = stats["original_tokens"]
                comp_col.upsert(
                    ids=[doc_id],
                    documents=[compressed],
                    metadatas=[comp_meta],
                )
            print(
                f"  Stored {len(compressed_entries)} encoded records in 'recallos_encoded' collection."
            )
        except Exception as e:
            print(f"  Error storing encoded records: {e}")
            sys.exit(1)

    # Summary
    ratio = total_original / max(total_compressed, 1)
    orig_tokens = Dialect.count_tokens("x" * total_original)
    comp_tokens = Dialect.count_tokens("x" * total_compressed)
    print(f"  Total: {orig_tokens:,}t -> {comp_tokens:,}t ({ratio:.1f}x compression)")
    if args.dry_run:
        print("  (dry run -- nothing stored)")


def main():
    parser = argparse.ArgumentParser(
        description="RecallOS — Local-first AI memory operating system. No API key required.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--vault",
        default=None,
        help="Where the Data Vault lives (default: from ~/.recallos/config.json or ~/.recallos/vault)",
    )

    sub = parser.add_subparsers(dest="command")

    # init
    p_init = sub.add_parser("init", help="Detect nodes from your folder structure")
    p_init.add_argument("dir", help="Project directory to set up")
    p_init.add_argument(
        "--yes", action="store_true", help="Auto-accept all detected entities (non-interactive)"
    )

    # ingest
    p_ingest = sub.add_parser("ingest", help="Ingest files into the Data Vault")
    p_ingest.add_argument("dir", help="Directory to ingest")
    p_ingest.add_argument(
        "--mode",
        choices=["projects", "convos"],
        default="projects",
        help="Ingest mode: 'projects' for code/docs (default), 'convos' for chat exports",
    )
    p_ingest.add_argument("--domain", default=None, help="Domain name (default: directory name)")
    p_ingest.add_argument(
        "--agent",
        default="recallos",
        help="Your name — recorded on every source record (default: recallos)",
    )
    p_ingest.add_argument("--limit", type=int, default=0, help="Max files to process (0 = all)")
    p_ingest.add_argument(
        "--dry-run", action="store_true", help="Show what would be filed without filing"
    )
    p_ingest.add_argument(
        "--extract",
        choices=["exchange", "general"],
        default="exchange",
        help="Extraction strategy for convos mode: 'exchange' (default) or 'general' (5 memory types)",
    )
    p_ingest.add_argument(
        "--encode",
        action="store_true",
        help="Also store RecallScript-encoded versions in recallos_encoded collection (~30x compression)",
    )

    # query
    p_query = sub.add_parser("query", help="Semantic retrieval from the Data Vault")
    p_query.add_argument("query", help="What to search for")
    p_query.add_argument("--domain", default=None, help="Limit to one domain")
    p_query.add_argument("--node", default=None, help="Limit to one node")
    p_query.add_argument("--results", type=int, default=5, help="Number of results")

    # encode
    p_encode = sub.add_parser(
        "encode", help="Encode records using RecallScript (~30x compression)"
    )
    p_encode.add_argument("--domain", default=None, help="Domain to encode (default: all domains)")
    p_encode.add_argument(
        "--dry-run", action="store_true", help="Preview encoding without storing"
    )
    p_encode.add_argument(
        "--config", default=None, help="Entity config JSON (e.g. entities.json)"
    )

    # bootstrap
    p_bootstrap = sub.add_parser("bootstrap", help="Show L0 + L1 bootstrap context (~600-900 tokens)")
    p_bootstrap.add_argument("--domain", default=None, help="Bootstrap for a specific project/domain")

    # split
    p_split = sub.add_parser(
        "split",
        help="Split concatenated transcript mega-files into per-session files (run before ingest)",
    )
    p_split.add_argument("dir", help="Directory containing transcript files")
    p_split.add_argument(
        "--output-dir",
        default=None,
        help="Write split files here (default: same directory as source files)",
    )
    p_split.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be split without writing files",
    )
    p_split.add_argument(
        "--min-sessions",
        type=int,
        default=2,
        help="Only split files containing at least N sessions (default: 2)",
    )

    # status
    sub.add_parser("status", help="Show Data Vault overview")

    # doctor
    p_doctor = sub.add_parser(
        "doctor",
        help="Run vault health checks (integrity, orphans, legacy data)",
    )
    p_doctor.add_argument(
        "--verbose",
        action="store_true",
        help="Show detail for all checks, not just warnings/failures",
    )

    # migrate
    p_migrate = sub.add_parser(
        "migrate",
        help="Migrate legacy ~/.mempalace/ data to ~/.recallos/",
    )
    p_migrate.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be migrated without making changes",
    )
    p_migrate.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing RecallOS data if present",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Warn once if a legacy ~/.mempalace directory is detected
    _cfg = RecallOSConfig()
    _warn = _cfg.legacy_warning
    if _warn and args.command != "migrate":
        print(_warn)
        print()

    dispatch = {
        "init": cmd_init,
        "ingest": cmd_mine,
        "split": cmd_split,
        "query": cmd_query,
        "encode": cmd_encode,
        "bootstrap": cmd_bootstrap,
        "status": cmd_status,
        "migrate": cmd_migrate,
        "doctor": cmd_doctor,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
