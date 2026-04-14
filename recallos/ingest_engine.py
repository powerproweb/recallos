#!/usr/bin/env python3
"""
miner.py ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Files everything into the palace.

Reads recallos.yaml from the project directory to know the domain + nodes.
Routes each file to the right node based on content.
Stores verbatim chunks as source records. No summaries. Ever.
"""

import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import chromadb

READABLE_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".json",
    ".yaml",
    ".yml",
    ".html",
    ".css",
    ".java",
    ".go",
    ".rs",
    ".rb",
    ".sh",
    ".csv",
    ".sql",
    ".toml",
}

SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    ".next",
    "coverage",
    ".recallos",
}

CHUNK_SIZE = 800  # chars per record
CHUNK_OVERLAP = 100  # overlap between chunks
MIN_CHUNK_SIZE = 50  # skip tiny chunks


# =============================================================================
# CONFIG
# =============================================================================


def load_config(project_dir: str) -> dict:
    """Load recallos.yaml from project directory (falls back to mempal.yaml).

    Raises:
        ConfigNotFoundError: if neither recallos.yaml nor mempal.yaml exists.
    """
    import yaml
    from .exceptions import ConfigNotFoundError

    config_path = Path(project_dir).expanduser().resolve() / "recallos.yaml"
    if not config_path.exists():
        # Fallback to legacy name
        legacy_path = Path(project_dir).expanduser().resolve() / "mempal.yaml"
        if legacy_path.exists():
            config_path = legacy_path
        else:
            raise ConfigNotFoundError(project_dir)
    with open(config_path) as f:
        return yaml.safe_load(f)


# =============================================================================
# FILE ROUTING ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â which node does this file belong to?
# =============================================================================


def _strip_suffix(word: str) -> str:
    """Light stemming: strip common English suffixes."""
    for suffix in ("ing", "tion", "tions", "ed", "er", "ers", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def detect_node(filepath: Path, content: str, nodes: list, project_path: Path) -> str:
    """
    Route a file to the right node.
    Priority:
    1. Folder path matches a node name
    2. Filename matches a node name or keyword
    3. Content keyword scoring with position weighting
    4. Fallback: "general"
    """
    import re as _re

    relative = str(filepath.relative_to(project_path)).lower()
    filename = filepath.stem.lower()

    # Priority 1: folder path contains node name
    path_parts = relative.replace("\\", "/").split("/")
    for part in path_parts[:-1]:  # skip filename itself
        for node in nodes:
            if node["name"].lower() in part or part in node["name"].lower():
                return node["name"]

    # Priority 2: filename matches node name
    for node in nodes:
        if node["name"].lower() in filename or filename in node["name"].lower():
            return node["name"]

    # Priority 3: position-weighted keyword scoring
    # Title/lead (first 500 chars) words get 3x weight
    lead = content[:500].lower()
    body = content[:2000].lower()
    lead_words = set(_re.findall(r"\w+", lead))
    lead_stems = {_strip_suffix(w) for w in lead_words}

    scores = defaultdict(int)
    for node in nodes:
        keywords = node.get("keywords", []) + [node["name"]]
        for kw in keywords:
            kw_lower = kw.lower()
            kw_stem = _strip_suffix(kw_lower)
            body_count = body.count(kw_lower)
            if body_count:
                scores[node["name"]] += body_count
            # 3x weight if keyword (or its stem) appears in the lead
            if kw_lower in lead or kw_stem in lead_stems:
                scores[node["name"]] += 3

    if scores:
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return best

    return "general"


# =============================================================================
# CHUNKING
# =============================================================================


def chunk_text(content: str, source_file: str) -> list:
    """
    Split content into record-sized chunks.
    Tries to split on paragraph/line boundaries.
    Returns list of {"content": str, "chunk_index": int}
    """
    # Clean up
    content = content.strip()
    if not content:
        return []

    chunks = []
    start = 0
    chunk_index = 0

    while start < len(content):
        end = min(start + CHUNK_SIZE, len(content))

        # Try to break at paragraph boundary
        if end < len(content):
            newline_pos = content.rfind("\n\n", start, end)
            if newline_pos > start + CHUNK_SIZE // 2:
                end = newline_pos
            else:
                newline_pos = content.rfind("\n", start, end)
                if newline_pos > start + CHUNK_SIZE // 2:
                    end = newline_pos

        chunk = content[start:end].strip()
        if len(chunk) >= MIN_CHUNK_SIZE:
            chunks.append(
                {
                    "content": chunk,
                    "chunk_index": chunk_index,
                }
            )
            chunk_index += 1

        start = end - CHUNK_OVERLAP if end < len(content) else end

    return chunks


# =============================================================================
# DATA VAULT Ã¢ÂÂ ChromaDB operations
# =============================================================================


def get_collection(vault_path: str):
    os.makedirs(vault_path, exist_ok=True)
    client = chromadb.PersistentClient(path=vault_path)
    try:
        return client.get_collection("recallos_records")
    except Exception:
        return client.create_collection("recallos_records")


def file_already_mined(collection, source_file: str) -> bool:
    """Fast check: has this file been filed before?"""
    try:
        results = collection.get(where={"source_file": source_file}, limit=1)
        return len(results.get("ids", [])) > 0
    except Exception:
        return False


def add_record(
    collection, domain: str, node: str, content: str, source_file: str, chunk_index: int, agent: str
):
    """Add one source record to the Data Vault."""
    record_id = f"record_{domain}_{node}_{hashlib.md5((source_file + str(chunk_index)).encode()).hexdigest()[:16]}"
    try:
        collection.add(
            documents=[content],
            ids=[record_id],
            metadatas=[
                {
                    "domain": domain,
                    "node": node,
                    "source_file": source_file,
                    "chunk_index": chunk_index,
                    "added_by": agent,
                    "filed_at": datetime.now().isoformat(),
                }
            ],
        )
        return True
    except Exception as e:
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            return False
        raise


# =============================================================================
# PROCESS ONE FILE
# =============================================================================


def process_file(
    filepath: Path,
    project_path: Path,
    collection,
    domain: str,
    nodes: list,
    agent: str,
    dry_run: bool,
    encode: bool = False,
    encoded_collection=None,
) -> int:
    """Read, chunk, route, and file one file. Returns record count."""

    # Skip if already filed
    source_file = str(filepath)
    if not dry_run and file_already_mined(collection, source_file):
        return 0

    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return 0

    content = content.strip()
    if len(content) < MIN_CHUNK_SIZE:
        return 0

    node = detect_node(filepath, content, nodes, project_path)
    chunks = chunk_text(content, source_file)

    if dry_run:
        encode_label = " +encode" if encode else ""
        print(f"    [DRY RUN] {filepath.name} → node:{node} ({len(chunks)} records{encode_label})")
        return len(chunks)

    # Lazy-load RecallScript encoder only if needed
    dialect = None
    if encode:
        try:
            from .recallscript import Dialect

            dialect = Dialect()
        except Exception:
            dialect = None

    records_added = 0
    for chunk in chunks:
        added = add_record(
            collection=collection,
            domain=domain,
            node=node,
            content=chunk["content"],
            source_file=source_file,
            chunk_index=chunk["chunk_index"],
            agent=agent,
        )
        if added:
            records_added += 1
            # Also store RecallScript-encoded version if requested
            if dialect and encoded_collection:
                meta = {
                    "domain": domain,
                    "node": node,
                    "source_file": source_file,
                    "chunk_index": chunk["chunk_index"],
                    "added_by": agent,
                    "filed_at": datetime.now().isoformat(),
                }
                try:
                    compressed = dialect.compress(chunk["content"], metadata=meta)
                    stats = dialect.compression_stats(chunk["content"], compressed)
                    enc_meta = dict(meta)
                    enc_meta["compression_ratio"] = round(stats["ratio"], 1)
                    record_id = f"record_{domain}_{node}_{hashlib.md5((source_file + str(chunk['chunk_index'])).encode()).hexdigest()[:16]}"
                    encoded_collection.upsert(
                        ids=[record_id],
                        documents=[compressed],
                        metadatas=[enc_meta],
                    )
                except Exception:
                    pass  # Non-fatal — verbatim record already stored

    return records_added


# =============================================================================
# SCAN PROJECT
# =============================================================================


def scan_project(project_dir: str) -> list:
    """Return list of all readable file paths."""
    project_path = Path(project_dir).expanduser().resolve()
    files = []
    for root, dirs, filenames in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for filename in filenames:
            filepath = Path(root) / filename
            if filepath.suffix.lower() in READABLE_EXTENSIONS:
                # Skip config files
                if filename in (
                    "recallos.yaml",
                    "recallos.yml",
                    "mempal.yaml",
                    "mempal.yml",
                    ".gitignore",
                    "package-lock.json",
                ):
                    continue
                files.append(filepath)
    return files


# =============================================================================
# MAIN: MINE
# =============================================================================


def mine(
    project_dir: str,
    vault_path: str,
    domain_override: str = None,
    agent: str = "recallos",
    limit: int = 0,
    dry_run: bool = False,
    encode: bool = False,
):
    """Ingest a project directory into the Data Vault."""

    project_path = Path(project_dir).expanduser().resolve()
    config = load_config(project_dir)

    domain = domain_override or config["domain"]
    nodes = config.get("nodes", [{"name": "general", "description": "All project files"}])

    files = scan_project(project_dir)
    if limit > 0:
        files = files[:limit]

    print(f"\n{'=' * 55}")
    print("  RecallOS Ingest")
    print(f"{'=' * 55}")
    print(f"  Domain:  {domain}")
    print(f"  Nodes:   {', '.join(r['name'] for r in nodes)}")
    print(f"  Files:   {len(files)}")
    print(f"  Vault:   {vault_path}")
    if dry_run:
        print("  DRY RUN ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â nothing will be filed")
    print(f"{'ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬' * 55}\n")

    if not dry_run:
        collection = get_collection(vault_path)
        encoded_collection = None
        if encode:
            client = chromadb.PersistentClient(path=vault_path)
            encoded_collection = client.get_or_create_collection("recallos_encoded")
            print("  Encode: ON (storing RecallScript versions in recallos_encoded)")
    else:
        collection = None
        encoded_collection = None

    total_records = 0
    files_skipped = 0
    node_counts = defaultdict(int)

    for i, filepath in enumerate(files, 1):
        records = process_file(
            filepath=filepath,
            project_path=project_path,
            collection=collection,
            domain=domain,
            nodes=nodes,
            agent=agent,
            dry_run=dry_run,
            encode=encode,
            encoded_collection=encoded_collection,
        )
        if records == 0 and not dry_run:
            files_skipped += 1
        else:
            total_records += records
            node = detect_node(filepath, "", nodes, project_path)
            node_counts[node] += 1
            if not dry_run:
                print(f"  ÃƒÂ¢Ã…â€œÃ¢â‚¬Å“ [{i:4}/{len(files)}] {filepath.name[:50]:50} +{records}")

    print(f"\n{'=' * 55}")
    print("  Done.")
    print(f"  Files processed: {len(files) - files_skipped}")
    print(f"  Files skipped (already filed): {files_skipped}")
    print(f"  Records filed: {total_records}")
    print("\n  By node:")
    for node, count in sorted(node_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    {node:20} {count} files")
    print('\n  Next: recallos query "what you\'re looking for"')
    print(f"{'=' * 55}\n")


# =============================================================================
# STATUS
# =============================================================================


def status(vault_path: str):
    """Show what's been filed in the Data Vault."""
    try:
        client = chromadb.PersistentClient(path=vault_path)
        col = client.get_collection("recallos_records")
    except Exception:
        print(f"\n  No Data Vault found at {vault_path}")
        print("  Run: recallos init <dir> then recallos ingest <dir>")
        return

    # Count by domain and node
    r = col.get(limit=10000, include=["metadatas"])
    metas = r["metadatas"]

    domain_nodes = defaultdict(lambda: defaultdict(int))
    for m in metas:
        domain_nodes[m.get("domain", "?")][m.get("node", "?")] += 1

    print(f"\n{'=' * 55}")
    print(f"  RecallOS Status ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â {len(metas)} records")
    print(f"{'=' * 55}\n")
    for domain, nodes in sorted(domain_nodes.items()):
        print(f"  DOMAIN: {domain}")
        for node, count in sorted(nodes.items(), key=lambda x: x[1], reverse=True):
            print(f"    NODE:   {node:20} {count:5} records")
        print()
    print(f"{'=' * 55}\n")
