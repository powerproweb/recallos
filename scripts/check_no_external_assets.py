#!/usr/bin/env python3
"""
check_no_external_assets.py — Sovereignty build gate.

Scans the built frontend bundle (desktop/static/) for any external
http:// or https:// references in HTML, JS, and CSS files.

Exits 0 if all assets are local.  Exits 1 if any external URLs are found.

Safe patterns (localhost, data URIs, source maps, protocol-relative
comments, etc.) are excluded.
"""

import re
import sys
from pathlib import Path

# Files to scan
EXTENSIONS = {".html", ".js", ".css"}

# Regex that matches http:// or https:// URLs
_URL_RE = re.compile(r"""https?://[^\s"'`)>]+""", re.IGNORECASE)

# Patterns that are safe / expected — NOT external assets
_SAFE_PATTERNS = [
    re.compile(r"^https?://(127\.0\.0\.1|localhost)(:\d+)?"),  # localhost
    re.compile(r"^https?://[^/]*\.map$"),  # source-map references
    re.compile(r"^https?://[^/]*#"),  # fragment-only
    re.compile(r"^https?://(www\.)?w3\.org/"),  # XML/SVG namespace URIs
    re.compile(r"^https?://schema\.org"),  # structured data schemas
    re.compile(r"^https?://react\.dev/"),  # React error documentation strings
    re.compile(r"^https?://reactrouter\.com/"),  # React Router docs in error strings
]


def scan_file(path: Path) -> list[tuple[int, str]]:
    """Return a list of (line_number, url) for external URLs found in *path*."""
    hits: list[tuple[int, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return hits

    for lineno, line in enumerate(text.splitlines(), 1):
        for match in _URL_RE.finditer(line):
            url = match.group(0)
            if any(pat.search(url) for pat in _SAFE_PATTERNS):
                continue
            hits.append((lineno, url))
    return hits


def main(static_dir: str | None = None) -> int:
    root = (
        Path(static_dir)
        if static_dir
        else Path(__file__).resolve().parent.parent / "desktop" / "static"
    )

    if not root.is_dir():
        print(f"SKIP  {root} does not exist (no build yet)")
        return 0

    violations: list[tuple[Path, int, str]] = []

    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in EXTENSIONS:
            continue
        for lineno, url in scan_file(path):
            violations.append((path.relative_to(root), lineno, url))

    if not violations:
        print(f"PASS  No external asset references in {root}")
        return 0

    print(f"FAIL  {len(violations)} external reference(s) found in {root}:\n")
    for relpath, lineno, url in violations:
        print(f"  {relpath}:{lineno}  {url}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
