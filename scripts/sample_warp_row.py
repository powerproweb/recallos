"""Dump one full sample row from agent_conversations and ai_queries
so we can see the JSON shape before writing the real exporter."""

from __future__ import annotations
import json
import os
import shutil
import sqlite3
import sys
import tempfile

SRC = os.path.expanduser(r"~\AppData\Local\Warp\Warp\data\warp.sqlite")


def main() -> int:
    tmp_dir = tempfile.mkdtemp(prefix="warp_ro_")
    tmp = os.path.join(tmp_dir, "warp.sqlite")
    shutil.copy2(SRC, tmp)
    for ext in ("-shm", "-wal"):
        s = SRC + ext
        if os.path.exists(s):
            shutil.copy2(s, tmp + ext)

    conn = sqlite3.connect(tmp)
    try:
        print("=== agent_conversations sample ===")
        row = conn.execute(
            "SELECT conversation_id, conversation_data, last_modified_at "
            "FROM agent_conversations ORDER BY last_modified_at DESC LIMIT 1"
        ).fetchone()
        if row:
            cid, cdata, lma = row
            print(f"conversation_id: {cid}")
            print(f"last_modified_at: {lma}")
            try:
                parsed = json.loads(cdata)
                print("top-level keys:", list(parsed.keys())[:20])
                # Try to find message-like arrays
                for k, v in parsed.items():
                    if isinstance(v, list) and v:
                        print(
                            f"  list key '{k}' len={len(v)} first item keys: "
                            f"{list(v[0].keys()) if isinstance(v[0], dict) else type(v[0]).__name__}"
                        )
                # Print first ~3000 chars of JSON for structure
                print("--- first 3000 chars ---")
                print(json.dumps(parsed, indent=2)[:3000])
            except Exception as e:
                print("non-JSON or parse error:", e)
                print(cdata[:1500])

        print()
        print("=== ai_queries sample ===")
        row = conn.execute(
            "SELECT id, exchange_id, conversation_id, start_ts, input, "
            "working_directory, output_status, model_id "
            "FROM ai_queries ORDER BY start_ts DESC LIMIT 1"
        ).fetchone()
        if row:
            cols = [
                "id",
                "exchange_id",
                "conversation_id",
                "start_ts",
                "input",
                "working_directory",
                "output_status",
                "model_id",
            ]
            for c, v in zip(cols, row):
                if c == "input":
                    try:
                        parsed = json.loads(v)
                        print(f"{c} (parsed, first 2000 chars):")
                        print(json.dumps(parsed, indent=2)[:2000])
                    except Exception:
                        print(f"{c} (raw 500):", repr(v)[:500])
                else:
                    print(f"{c}: {v}")

        print()
        print("=== ai_queries columns (all) ===")
        cols = [r[1] for r in conn.execute("PRAGMA table_info(ai_queries)")]
        print(cols)

        print()
        print("=== ai_queries count grouped by conversation ===")
        for cid, cnt in conn.execute(
            "SELECT conversation_id, COUNT(*) c FROM ai_queries "
            "GROUP BY conversation_id ORDER BY c DESC LIMIT 5"
        ):
            print(f"  {cid}: {cnt} exchanges")

        print()
        print("=== ai_queries with non-empty input (3 samples) ===")
        rows = conn.execute(
            "SELECT id, conversation_id, start_ts, input FROM ai_queries "
            "WHERE length(input) > 10 ORDER BY start_ts LIMIT 3"
        ).fetchall()
        for r in rows:
            print(f"\n-- id={r[0]} conv={r[1]} ts={r[2]} --")
            print(r[3][:1500])

        print()
        print("=== agent_tasks sample (text fields) ===")
        cols = [r[1] for r in conn.execute("PRAGMA table_info(agent_tasks)")]
        print("cols:", cols)
        row = conn.execute(
            "SELECT id, conversation_id, task_id, task FROM agent_tasks "
            "ORDER BY last_modified_at LIMIT 1"
        ).fetchone()
        if row:
            print(f"task bytes length: {len(row[3]) if row[3] else 0}")
            if row[3]:
                try:
                    # Protobuf; just pull out printable ASCII runs
                    import re

                    printable = re.findall(rb"[\x20-\x7e\n\t]{8,}", row[3])
                    for p in printable[:20]:
                        print("  ", p.decode(errors="replace")[:200])
                except Exception as e:
                    print("err:", e)

        print()
        print("=== blocks table columns (maybe holds command output) ===")
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(blocks)")]
            print("cols:", cols)
            cnt = conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
            print("rows:", cnt)
        except Exception as e:
            print("err:", e)

        print()
        print("=== ai_queries output columns - is there a response column I missed? ===")
        # Full row dump
        row = conn.execute(
            "SELECT * FROM ai_queries WHERE length(input)>10 ORDER BY start_ts LIMIT 1"
        ).fetchone()
        cols = [r[1] for r in conn.execute("PRAGMA table_info(ai_queries)")]
        for c, v in zip(cols, row or []):
            preview = repr(v)[:400] if v is not None else "NULL"
            print(f"  {c}: {preview}")

    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
