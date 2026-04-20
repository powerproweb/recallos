"""Read-only peek at Warp's local SQLite store.

Copies ~/AppData/Local/Warp/Warp/data/warp.sqlite (+ WAL/SHM) to a temp
location so we don't touch Warp's running DB, then lists tables and any
rows that look like agent conversations.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import sys
import tempfile

SRC = os.path.expanduser(r"~\AppData\Local\Warp\Warp\data\warp.sqlite")


def main() -> int:
    if not os.path.exists(SRC):
        print(f"Not found: {SRC}")
        return 1

    tmp_dir = tempfile.mkdtemp(prefix="warp_ro_")
    tmp = os.path.join(tmp_dir, "warp.sqlite")
    shutil.copy2(SRC, tmp)
    for ext in ("-shm", "-wal"):
        s = SRC + ext
        if os.path.exists(s):
            shutil.copy2(s, tmp + ext)

    conn = sqlite3.connect(tmp)
    try:
        tables = [
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        ]
        print(f"tables ({len(tables)}):")
        for t in tables:
            print(f"  - {t}")

        candidates = [
            t
            for t in tables
            if any(k in t.lower() for k in ("conversation", "agent", "message", "ai", "chat"))
        ]
        print()
        print(f"conversation-like tables: {candidates}")

        for t in candidates:
            try:
                cnt = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{t}")')]
                print(f"\n[{t}]  rows={cnt}  cols={cols}")
                if cnt:
                    sample = conn.execute(f'SELECT * FROM "{t}" LIMIT 1').fetchone()
                    preview = {}
                    for col, val in zip(cols, sample):
                        s = repr(val)
                        preview[col] = (s[:80] + "...") if len(s) > 80 else s
                    for k, v in preview.items():
                        print(f"    {k} = {v}")
            except Exception as e:
                print(f"[{t}] error: {e}")
    finally:
        conn.close()

    print(f"\n(tmp copy at: {tmp})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
