#!/usr/bin/env python3
"""
conversation_ingest.py Ã¢â‚¬â€ Mine conversations into the palace.

Ingests chat exports (Claude Code, ChatGPT, Slack, plain text transcripts).
Normalizes format, chunks by exchange pair (Q+A = one unit), files to Data Vault.

Same Data Vault as project ingest. Different ingest strategy.
"""

import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import re as _re

import chromadb

from .normalize import normalize


# File types that might contain conversations
CONVO_EXTENSIONS = {
    ".txt",
    ".md",
    ".json",
    ".jsonl",
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
    ".recallos",
}

MIN_CHUNK_SIZE = 30


# =============================================================================
# CHUNKING Ã¢â‚¬â€ exchange pairs for conversations
# =============================================================================


def chunk_exchanges(content: str) -> list:
    """
    Chunk by exchange pair: one > turn + AI response = one unit.
    Falls back to paragraph chunking if no > markers.
    """
    lines = content.split("\n")
    quote_lines = sum(1 for line in lines if line.strip().startswith(">"))

    if quote_lines >= 3:
        return _chunk_by_exchange(lines)
    else:
        return _chunk_by_paragraph(content)


def _chunk_by_exchange(lines: list) -> list:
    """One user turn (>) + the AI response that follows = one chunk."""
    chunks = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if line.strip().startswith(">"):
            user_turn = line.strip()
            i += 1

            ai_lines = []
            while i < len(lines):
                next_line = lines[i]
                if next_line.strip().startswith(">") or next_line.strip().startswith("---"):
                    break
                if next_line.strip():
                    ai_lines.append(next_line.strip())
                i += 1

            ai_response = " ".join(ai_lines[:8])
            content = f"{user_turn}\n{ai_response}" if ai_response else user_turn

            if len(content.strip()) > MIN_CHUNK_SIZE:
                chunks.append(
                    {
                        "content": content,
                        "chunk_index": len(chunks),
                    }
                )
        else:
            i += 1

    return chunks


def _chunk_by_paragraph(content: str) -> list:
    """Fallback: chunk by paragraph breaks."""
    chunks = []
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

    # If no paragraph breaks and long content, chunk by line groups
    if len(paragraphs) <= 1 and content.count("\n") > 20:
        lines = content.split("\n")
        for i in range(0, len(lines), 25):
            group = "\n".join(lines[i : i + 25]).strip()
            if len(group) > MIN_CHUNK_SIZE:
                chunks.append({"content": group, "chunk_index": len(chunks)})
        return chunks

    for para in paragraphs:
        if len(para) > MIN_CHUNK_SIZE:
            chunks.append({"content": para, "chunk_index": len(chunks)})

    return chunks


# =============================================================================
# NODE DETECTION Ã¢â‚¬â€ topic-based for conversations
# =============================================================================

TOPIC_KEYWORDS = {
    "technical": [
        "code",
        "python",
        "function",
        "bug",
        "error",
        "api",
        "database",
        "server",
        "deploy",
        "git",
        "test",
        "debug",
        "refactor",
    ],
    "architecture": [
        "architecture",
        "design",
        "pattern",
        "structure",
        "schema",
        "interface",
        "module",
        "component",
        "service",
        "layer",
    ],
    "planning": [
        "plan",
        "roadmap",
        "milestone",
        "deadline",
        "priority",
        "sprint",
        "backlog",
        "scope",
        "requirement",
        "spec",
    ],
    "decisions": [
        "decided",
        "chose",
        "picked",
        "switched",
        "migrated",
        "replaced",
        "trade-off",
        "alternative",
        "option",
        "approach",
    ],
    "problems": [
        "problem",
        "issue",
        "broken",
        "failed",
        "crash",
        "stuck",
        "workaround",
        "fix",
        "solved",
        "resolved",
    ],
}

# Bigram patterns — multi-word signals that strongly indicate a topic
TOPIC_BIGRAMS = {
    "technical": [
        "pull request",
        "stack trace",
        "type error",
        "import error",
        "runtime error",
        "unit test",
        "end to end",
        "rest api",
        "async await",
        "npm install",
        "pip install",
        "docker compose",
    ],
    "architecture": [
        "data model",
        "design pattern",
        "system design",
        "domain model",
        "event driven",
        "micro service",
        "api gateway",
    ],
    "planning": [
        "next steps",
        "action item",
        "release date",
        "launch date",
        "project plan",
        "quarterly goal",
        "user story",
    ],
    "decisions": [
        "we decided",
        "final decision",
        "going with",
        "trade off",
        "chose to",
        "switched to",
        "moved to",
    ],
    "problems": [
        "not working",
        "keeps failing",
        "root cause",
        "known issue",
        "temporary fix",
        "workaround for",
    ],
}


def _normalize_text(text: str) -> str:
    """Lowercase, collapse whitespace, strip leading punctuation."""
    text = text.lower()
    text = _re.sub(r"[^\w\s]", " ", text)  # replace punctuation with spaces
    text = _re.sub(r"\s+", " ", text).strip()
    return text


def detect_convo_node(content: str) -> str:
    """Score conversation content against topic keywords and bigrams.

    Matches in the first 500 chars (title/lead) receive 2x weight.
    Bigram matches count as 2 keyword matches each.
    """
    lead = _normalize_text(content[:500])
    body = _normalize_text(content[:3000])

    scores: dict = {}
    for node_name, keywords in TOPIC_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in body:
                score += 1
            if kw in lead:
                score += 1  # extra weight for lead matches
        for bigram in TOPIC_BIGRAMS.get(node_name, []):
            if bigram in body:
                score += 2
            if bigram in lead:
                score += 2  # extra weight for lead bigram matches
        if score > 0:
            scores[node_name] = score

    if scores:
        return max(scores, key=scores.get)
    return "general"


# =============================================================================
# DATA VAULT OPERATIONS
# =============================================================================


def get_collection(vault_path: str):
    os.makedirs(vault_path, exist_ok=True)
    client = chromadb.PersistentClient(path=vault_path)
    try:
        return client.get_collection("recallos_records")
    except Exception:
        return client.create_collection("recallos_records")


def get_mined_files(collection, domain: str) -> set:
    """Pre-load all already-mined source files for a wing in one query."""
    try:
        results = collection.get(where={"domain": domain}, include=["metadatas"])
        return {m.get("source_file", "") for m in results.get("metadatas", [])}
    except Exception:
        return set()


# =============================================================================
# SCAN FOR CONVERSATION FILES
# =============================================================================


def scan_convos(convo_dir: str) -> list:
    """Find all potential conversation files."""
    convo_path = Path(convo_dir).expanduser().resolve()
    files = []
    for root, dirs, filenames in os.walk(convo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for filename in filenames:
            filepath = Path(root) / filename
            if filepath.suffix.lower() in CONVO_EXTENSIONS:
                files.append(filepath)
    return files


# =============================================================================
# MINE CONVERSATIONS
# =============================================================================


def mine_convos(
    convo_dir: str,
    vault_path: str,
    domain: str = None,
    agent: str = "recallos",
    limit: int = 0,
    dry_run: bool = False,
    extract_mode: str = "exchange",
    encode: bool = False,
):
    """Ingest a directory of conversation files into the Data Vault.

    extract_mode:
        "exchange" Ã¢â‚¬â€ default exchange-pair chunking (Q+A = one unit)
        "general"  Ã¢â‚¬â€ general extractor: decisions, preferences, milestones, problems, emotions
    """

    convo_path = Path(convo_dir).expanduser().resolve()
    if not domain:
        domain = convo_path.name.lower().replace(" ", "_").replace("-", "_")

    files = scan_convos(convo_dir)
    if limit > 0:
        files = files[:limit]

    print(f"\n{'=' * 55}")
    print("  RecallOS Ingest Ã¢â‚¬â€ Conversations")
    print(f"{'=' * 55}")
    print(f"  Domain:  {domain}")
    print(f"  Source:  {convo_path}")
    print(f"  Files:   {len(files)}")
    print(f"  Vault:   {vault_path}")
    if dry_run:
        print("  DRY RUN Ã¢â‚¬â€ nothing will be filed")
    print(f"{'Ã¢â€â‚¬' * 55}\n")

    collection = get_collection(vault_path) if not dry_run else None
    encoded_collection = None
    dialect = None
    if encode and not dry_run:
        import chromadb as _chromadb
        _enc_client = _chromadb.PersistentClient(path=vault_path)
        encoded_collection = _enc_client.get_or_create_collection("recallos_encoded")
        try:
            from .recallscript import Dialect
            dialect = Dialect()
        except Exception:
            dialect = None

    # Pre-load already-mined files in one query (avoids O(n) scan per file)
    mined_files = get_mined_files(collection, domain) if not dry_run else set()

    total_records = 0
    files_skipped = 0
    node_counts = defaultdict(int)

    for i, filepath in enumerate(files, 1):
        source_file = str(filepath)

        # Skip if already filed
        if source_file in mined_files:
            files_skipped += 1
            continue

        # Normalize format
        try:
            content = normalize(str(filepath))
        except Exception:
            continue

        if not content or len(content.strip()) < MIN_CHUNK_SIZE:
            continue

        # Chunk Ã¢â‚¬â€ either exchange pairs or general extraction
        if extract_mode == "general":
            from .general_extractor import extract_memories

            chunks = extract_memories(content)
            # Each chunk already has memory_type; use it as the room name
        else:
            chunks = chunk_exchanges(content)

        if not chunks:
            continue

        # Detect room from content (general mode uses memory_type instead)
        if extract_mode != "general":
            node = detect_convo_node(content)
        else:
            node = None  # set per-chunk below

        if dry_run:
            if extract_mode == "general":
                from collections import Counter

                type_counts = Counter(c.get("memory_type", "general") for c in chunks)
                types_str = ", ".join(f"{t}:{n}" for t, n in type_counts.most_common())
                print(f"    [DRY RUN] {filepath.name} Ã¢â€ â€™ {len(chunks)} memories ({types_str})")
            else:
                print(f"    [DRY RUN] {filepath.name} Ã¢â€ â€™ node:{node} ({len(chunks)} records)")
            total_records += len(chunks)
            # Track room counts
            if extract_mode == "general":
                for c in chunks:
                    node_counts[c.get("memory_type", "general")] += 1
            else:
                node_counts[node] += 1
            continue

        if extract_mode != "general":
            node_counts[node] += 1

        # Batch all chunks for this file into one collection.add() call
        batch_docs, batch_ids, batch_metas = [], [], []
        filed_at = datetime.now().isoformat()
        for chunk in chunks:
            chunk_node = chunk.get("memory_type", node) if extract_mode == "general" else node
            if extract_mode == "general":
                node_counts[chunk_node] += 1
            record_id = f"record_{domain}_{chunk_node}_{hashlib.md5((source_file + str(chunk['chunk_index'])).encode()).hexdigest()[:16]}"
            if record_id not in mined_files:  # skip already-stored chunks
                batch_docs.append(chunk["content"])
                batch_ids.append(record_id)
                batch_metas.append({
                    "domain": domain,
                    "node": chunk_node,
                    "source_file": source_file,
                    "chunk_index": chunk["chunk_index"],
                    "added_by": agent,
                    "filed_at": filed_at,
                    "ingest_mode": "convos",
                    "extract_mode": extract_mode,
                })

        records_added = 0
        if batch_docs:
            # Add in sub-batches of 100 to avoid memory pressure on large files
            BATCH_SIZE = 100
            for b in range(0, len(batch_docs), BATCH_SIZE):
                try:
                    collection.add(
                        documents=batch_docs[b:b+BATCH_SIZE],
                        ids=batch_ids[b:b+BATCH_SIZE],
                        metadatas=batch_metas[b:b+BATCH_SIZE],
                    )
                    records_added += len(batch_docs[b:b+BATCH_SIZE])
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        raise

        # Also store RecallScript-encoded versions if requested
        if dialect and encoded_collection and batch_docs:
            enc_batch_docs, enc_batch_ids, enc_batch_metas = [], [], []
            for doc, rec_id, meta in zip(batch_docs, batch_ids, batch_metas):
                try:
                    compressed = dialect.compress(doc, metadata=meta)
                    stats = dialect.compression_stats(doc, compressed)
                    enc_meta = dict(meta)
                    enc_meta["compression_ratio"] = round(stats["ratio"], 1)
                    enc_batch_docs.append(compressed)
                    enc_batch_ids.append(rec_id)
                    enc_batch_metas.append(enc_meta)
                except Exception:
                    pass
            if enc_batch_docs:
                try:
                    encoded_collection.upsert(
                        ids=enc_batch_ids,
                        documents=enc_batch_docs,
                        metadatas=enc_batch_metas,
                    )
                except Exception:
                    pass

        total_records += records_added
        print(f"  ✔ [{i:4}/{len(files)}] {filepath.name[:50]:50} +{records_added}")

    print(f"\n{'=' * 55}")
    print("  Done.")
    print(f"  Files processed: {len(files) - files_skipped}")
    print(f"  Files skipped (already filed): {files_skipped}")
    print(f"  Records filed: {total_records}")
    if node_counts:
        print("\n  By node:")
        for node, count in sorted(node_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"    {node:20} {count} files")
    print('\n  Next: recallos query "what you\'re looking for"')
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python conversation_ingest.py <convo_dir> [--palace PATH] [--limit N] [--dry-run]")
        sys.exit(1)
    from .config import RecallOSConfig

    mine_convos(sys.argv[1], vault_path=RecallOSConfig().vault_path)
