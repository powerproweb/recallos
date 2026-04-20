"""Export Warp agent conversations from the local SQLite database and ingest
them into the RecallOS vault via the RecallOS MCP server.

Reads (read-only, via a temp copy) ~/AppData/Local/Warp/Warp/data/warp.sqlite:
  - ai_queries          — user prompts (Query / Followup / UserInput entries)
  - agent_tasks         — task blobs (best-effort printable text extraction)
  - agent_conversations — session metadata (tokens, tool usage)

Writes one Markdown file per conversation into --out (default
~/recallos_inbox/warp_convos), then calls `recallos_add_record` over stdio MCP
to store each exported conversation in the RecallOS vault.

Safe to run repeatedly:
  - export step overwrites the per-conversation Markdown file
  - MCP ingest step skips duplicates via RecallOS duplicate detection

Usage:
    python scripts/export_warp_convos.py
    python scripts/export_warp_convos.py --skip-ingest
    python scripts/export_warp_convos.py --limit 5 --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

WARP_DB = os.path.expanduser(r"~\AppData\Local\Warp\Warp\data\warp.sqlite")
DEFAULT_OUT = os.path.expanduser(r"~\recallos_inbox\warp_convos")
DEFAULT_DOMAIN = "warp_agent_conversations"

# Ignore Warp context noise; we only want human-written content
_NOISE_PREFIXES = (
    "Here is some context about",
    "<system-reminder>",
    "I ran the following command",
    "I ran the following commands",
    "Command ID:",
    "Command input:",
    "Exit Code:",
    "Command output:",
)

_UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
_BASE64ISH_RE = re.compile(r"[A-Za-z0-9+/]{16,}={0,2}$")


def _copy_db_readonly() -> str:
    if not os.path.exists(WARP_DB):
        raise SystemExit(f"Warp DB not found: {WARP_DB}")
    tmp_dir = tempfile.mkdtemp(prefix="warp_export_")
    tmp = os.path.join(tmp_dir, "warp.sqlite")
    shutil.copy2(WARP_DB, tmp)
    for ext in ("-shm", "-wal"):
        src = WARP_DB + ext
        if os.path.exists(src):
            shutil.copy2(src, tmp + ext)
    return tmp


def _strip_noise(text: str) -> str:
    """Drop lines that are Warp context-injection boilerplate."""
    if not text:
        return ""
    lines = text.splitlines()
    out: list[str] = []
    skip_block = False
    for ln in lines:
        s = ln.strip()
        if not s:
            if out:
                out.append("")
            continue
        if s.startswith("{") and ('"directory_state"' in s or '"operating_system"' in s):
            skip_block = True
            continue
        if skip_block:
            if s == "}":
                skip_block = False
            continue
        if any(s.startswith(p) for p in _NOISE_PREFIXES):
            continue
        out.append(ln)
    cleaned = "\n".join(out).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def _extract_text_items(raw: str) -> list[str]:
    """Pull user-authored text out of ai_queries.input JSON."""
    if not raw:
        return []
    try:
        items = json.loads(raw)
    except Exception:
        return []
    if not isinstance(items, list):
        return []

    texts: list[str] = []
    for entry in items:
        if not isinstance(entry, dict):
            continue
        for _kind, payload in entry.items():
            if not isinstance(payload, dict):
                continue
            text = payload.get("text")
            if isinstance(text, str) and text.strip():
                texts.append(text.strip())
    return texts


def _extract_task_titles(blob: bytes) -> list[str]:
    """Best-effort extraction of human-readable assistant/task snippets from
    protobuf task blobs. This is intentionally conservative to avoid ingesting
    protobuf/base64 noise as false content.
    """
    if not blob:
        return []
    titles: list[str] = []
    for run in re.findall(rb"[\x20-\x7e\t]{20,500}", blob):
        s = run.decode(errors="replace").strip()
        if not s:
            continue
        s = s.lstrip("\"'`*$#@!:;,.|()[]{}<>-_=+").rstrip("\"'`*").strip()
        s = re.sub(r"\s+", " ", s)
        if len(s) < 24 or len(s) > 300:
            continue
        if " " not in s:
            continue
        if _UUID_RE.search(s) or _BASE64ISH_RE.search(s):
            continue
        if "=Z$" in s or s.startswith(("Z$", "$")):
            continue
        if not s[:1].isalpha():
            continue
        alpha_ratio = sum(1 for c in s if c.isalpha()) / max(1, len(s))
        if alpha_ratio < 0.58:
            continue
        if len(s.split()) < 4:
            continue
        lowered = s.lower()
        if (
            lowered.startswith("use this skill")
            or lowered.startswith("a powerful and fast search")
            or lowered.startswith("creates a new file")
            or lowered.startswith("reads the contents")
            or "warp's rest api" in lowered
            or "bundledskillid" in lowered
        ):
            continue
        titles.append(s)

    seen = set()
    uniq = []
    for t in titles:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def _safe_slug(text: str, maxlen: int = 60) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", text or "").strip("-").lower()
    return (s[:maxlen] or "untitled").rstrip("-")


def _suggested_node(cid: str, data: dict) -> str:
    first_text = data["exchanges"][0]["text"] if data["exchanges"] else "conversation"
    root = _safe_slug(first_text[:48], maxlen=48)
    short = cid.split("-")[0]
    return f"{root}-{short}"[:70]


def collect(db_path: str) -> dict[str, dict]:
    """Return mapping conversation_id -> aggregated record."""
    conn = sqlite3.connect(db_path)
    try:
        convos: dict[str, dict] = defaultdict(
            lambda: {
                "exchanges": [],
                "assistant_snippets": [],
                "first_ts": None,
                "last_ts": None,
                "working_dirs": set(),
                "models": set(),
                "metadata": None,
            }
        )

        for row in conn.execute(
            "SELECT conversation_id, start_ts, input, working_directory, model_id "
            "FROM ai_queries ORDER BY start_ts ASC"
        ):
            cid, ts, raw_input, wd, model = row
            if not cid:
                continue
            texts = _extract_text_items(raw_input)
            if not texts:
                continue
            c = convos[cid]
            for text in texts:
                cleaned = _strip_noise(text)
                if not cleaned or len(cleaned) < 3:
                    continue
                c["exchanges"].append(
                    {"ts": ts, "dir": wd or "", "text": cleaned, "model": model or ""}
                )
            c["first_ts"] = min(c["first_ts"], ts) if c["first_ts"] else ts
            c["last_ts"] = max(c["last_ts"], ts) if c["last_ts"] else ts
            if wd:
                c["working_dirs"].add(wd)
            if model:
                c["models"].add(model)

        for row in conn.execute(
            "SELECT conversation_id, task FROM agent_tasks ORDER BY last_modified_at ASC"
        ):
            cid, blob = row
            if not cid or cid not in convos:
                continue
            snippets = _extract_task_titles(blob)
            if snippets:
                convos[cid]["assistant_snippets"].extend(snippets)

        for row in conn.execute(
            "SELECT conversation_id, conversation_data, last_modified_at FROM agent_conversations"
        ):
            cid, cdata, lma = row
            if cid not in convos:
                continue
            try:
                parsed = json.loads(cdata) if cdata else {}
                convos[cid]["metadata"] = parsed.get("conversation_usage_metadata")
            except Exception:
                pass
            if lma and (not convos[cid]["last_ts"] or lma > convos[cid]["last_ts"]):
                convos[cid]["last_ts"] = lma

        for c in convos.values():
            seen = set()
            uniq = []
            for t in c["assistant_snippets"]:
                if t not in seen:
                    seen.add(t)
                    uniq.append(t)
            c["assistant_snippets"] = uniq[:25]

        return dict(convos)
    finally:
        conn.close()


def render_markdown(cid: str, data: dict) -> str:
    exchanges = data["exchanges"]
    if not exchanges:
        return ""

    first = data["first_ts"] or ""
    last = data["last_ts"] or ""
    dirs = sorted(data["working_dirs"])
    models = sorted(data["models"])
    title = _safe_slug(exchanges[0]["text"][:80])

    lines: list[str] = []
    lines.append(f"# Warp conversation - {title}")
    lines.append("")
    lines.append("## Metadata")
    lines.append(f"- conversation_id: `{cid}`")
    lines.append(f"- first_ts: {first}")
    lines.append(f"- last_ts: {last}")
    lines.append(f"- exchanges: {len(exchanges)}")
    if dirs:
        lines.append("- working_directories:")
        for d in dirs:
            lines.append(f"  - `{d}`")
    if models:
        lines.append(f"- models: {', '.join(models)}")
    meta = data.get("metadata") or {}
    if meta:
        tok = meta.get("token_usage") or []
        if tok:
            toks = ", ".join(f"{t.get('model_id', '?')}={t.get('warp_tokens', 0)}" for t in tok)
            lines.append(f"- token_usage: {toks}")
        tu = meta.get("tool_usage_metadata") or {}
        rc = tu.get("run_command_stats", {}).get("count")
        if rc is not None:
            lines.append(f"- run_command_count: {rc}")
    lines.append("")

    snippets = data["assistant_snippets"]
    if snippets:
        lines.append("## Assistant/task snippets (best-effort from local task blobs)")
        for t in snippets:
            lines.append(f"- {t}")
        lines.append("")

    lines.append("## Transcript (user turns)")
    lines.append("")
    for ex in exchanges:
        ts = ex.get("ts", "")
        dir_ = ex.get("dir", "")
        header = f"> **[{ts}]** _{dir_}_" if dir_ else f"> **[{ts}]**"
        lines.append(header)
        for line in ex["text"].splitlines():
            lines.append(f"> {line}")
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _mcp_send(proc: subprocess.Popen, payload: dict) -> dict | None:
    assert proc.stdin is not None
    assert proc.stdout is not None
    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()
    if payload.get("method") == "notifications/initialized":
        return None
    line = proc.stdout.readline()
    if not line:
        raise RuntimeError("MCP server closed the connection")
    response = json.loads(line)
    if "error" in response:
        raise RuntimeError(response["error"].get("message", "Unknown MCP error"))
    return response


def _ingest_via_mcp(
    records: list[tuple[str, dict, Path]], domain: str
) -> tuple[int, int, int, str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    proc = subprocess.Popen(
        [sys.executable, "-m", "recallos.mcp_gateway"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env=env,
    )

    added = 0
    skipped = 0
    failed = 0
    try:
        _mcp_send(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        _mcp_send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        for idx, (cid, data, path) in enumerate(records, start=1):
            node = _suggested_node(cid, data)
            content = path.read_text(encoding="utf-8")
            response = _mcp_send(
                proc,
                {
                    "jsonrpc": "2.0",
                    "id": idx + 1,
                    "method": "tools/call",
                    "params": {
                        "name": "recallos_add_record",
                        "arguments": {
                            "domain": domain,
                            "node": node,
                            "content": content,
                            "source_file": str(path),
                            "added_by": "warp_export_mcp",
                        },
                    },
                },
            )
            text = (response or {}).get("result", {}).get("content", [{}])[0].get("text", "")
            result = json.loads(text) if text else {}
            if result.get("success"):
                added += 1
            elif result.get("reason") == "duplicate":
                skipped += 1
            else:
                failed += 1

        _mcp_send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": len(records) + 100,
                "method": "tools/call",
                "params": {
                    "name": "recallos_log_write",
                    "arguments": {
                        "agent_name": "warp_importer",
                        "topic": "warp_import",
                        "entry": (
                            f"WARP-IMPORT | domain:{domain} | conversations:{len(records)} "
                            f"| added:{added} | duplicate:{skipped} | failed:{failed}"
                        ),
                    },
                },
            },
        )
    finally:
        try:
            if proc.stdin:
                proc.stdin.close()
        except Exception:
            pass
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        stderr_text = (proc.stderr.read() if proc.stderr else "") or ""

    return added, skipped, failed, stderr_text.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=DEFAULT_OUT, help="Output directory (default %(default)s)")
    parser.add_argument("--domain", default=DEFAULT_DOMAIN, help="RecallOS domain name")
    parser.add_argument("--limit", type=int, default=0, help="Max conversations to export (0=all)")
    parser.add_argument("--skip-ingest", action="store_true", help="Only export Markdown files")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print summary without writing files"
    )
    args = parser.parse_args(argv)

    tmp = _copy_db_readonly()
    convos = collect(tmp)

    usable = {cid: d for cid, d in convos.items() if d["exchanges"]}
    ordered = sorted(usable.items(), key=lambda kv: kv[1]["first_ts"] or "")
    if args.limit:
        ordered = ordered[: args.limit]

    print(
        f"Found {len(convos)} conversations in ai_queries; "
        f"{len(usable)} with user text; processing {len(ordered)}."
    )

    if args.dry_run:
        for cid, d in ordered[:10]:
            print(
                f"  {cid}  {d['first_ts']} -> {d['last_ts']}  "
                f"exchanges={len(d['exchanges'])}  snippets={len(d['assistant_snippets'])}"
            )
        return 0

    out_dir = Path(os.path.expanduser(args.out))
    out_dir.mkdir(parents=True, exist_ok=True)

    written_records: list[tuple[str, dict, Path]] = []
    for cid, d in ordered:
        md = render_markdown(cid, d)
        if not md:
            continue
        date_stamp = (d["first_ts"] or "")[:10].replace("-", "") or "00000000"
        short = cid.split("-")[0]
        path = out_dir / f"warp_{date_stamp}_{short}.md"
        path.write_text(md, encoding="utf-8")
        written_records.append((cid, d, path))

    print(f"Wrote {len(written_records)} files into {out_dir}")

    if args.skip_ingest:
        return 0

    added, skipped, failed, stderr_text = _ingest_via_mcp(written_records, args.domain)
    print(
        f"MCP ingest complete: added={added} duplicate={skipped} failed={failed} "
        f"domain={args.domain}"
    )
    if stderr_text:
        print("--- mcp stderr ---")
        print(stderr_text)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
