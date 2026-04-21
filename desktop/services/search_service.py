"""
desktop/services/search_service.py — Advanced search ranking and snippets.

Applies post-retrieval enhancements to ChromaDB semantic results:
  - Recency boost (newer records rank higher)
  - Field weighting (domain/node match boosts relevance)
  - Deduplication (remove near-identical text hits)
  - Snippet highlighting (extract the most relevant fragment)
"""

from __future__ import annotations

import hashlib
from datetime import datetime


def rank_results(
    results: list[dict],
    query: str,
    domain_filter: str | None = None,
    node_filter: str | None = None,
) -> list[dict]:
    """Re-rank search results with recency boost, field weighting, and dedup."""
    scored = []
    seen_hashes: set[str] = set()

    for r in results:
        # --- Deduplication by content hash ---
        text = r.get("text", "")
        content_hash = hashlib.md5(text[:500].encode()).hexdigest()
        if content_hash in seen_hashes:
            continue
        seen_hashes.add(content_hash)

        # --- Base score from semantic similarity ---
        score = r.get("similarity", 0.0)

        # --- Field weighting ---
        if domain_filter and r.get("domain") == domain_filter:
            score += 0.05
        if node_filter and r.get("node") == node_filter:
            score += 0.03

        # --- Recency boost ---
        filed_at = r.get("filed_at", "")
        if filed_at:
            try:
                dt = datetime.fromisoformat(filed_at)
                days_ago = (datetime.now() - dt).days
                recency = max(0, 0.05 - days_ago * 0.0005)  # up to +0.05 for today
                score += recency
            except Exception:
                pass

        r["ranked_score"] = round(score, 4)
        r["snippet"] = highlight_snippet(text, query)
        scored.append(r)

    scored.sort(key=lambda x: -x["ranked_score"])
    return scored


def highlight_snippet(text: str, query: str, context_chars: int = 120) -> str:
    """Extract the most relevant snippet from text around the query match."""
    if not text or not query:
        return text[: context_chars * 2] if text else ""

    # Find the best match position
    lower_text = text.lower()
    query_words = query.lower().split()

    best_pos = -1
    for word in query_words:
        pos = lower_text.find(word)
        if pos >= 0:
            best_pos = pos
            break

    if best_pos < 0:
        return text[: context_chars * 2]

    # Extract context around the match
    start = max(0, best_pos - context_chars)
    end = min(len(text), best_pos + context_chars)

    snippet = text[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return snippet
