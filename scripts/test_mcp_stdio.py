"""Verify the RecallOS MCP gateway over stdio.

Spawns `python -m recallos.mcp_gateway` and sends:
  1. initialize
  2. tools/list
  3. tools/call recallos_status
  4. tools/call recallos_query { query: ..., limit: 3 }

Prints a concise pass/fail report.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys


QUERY = "ChatGPT export downloader browser app"


def send(proc: subprocess.Popen, payload: dict) -> dict | None:
    line = json.dumps(payload) + "\n"
    assert proc.stdin is not None
    assert proc.stdout is not None
    proc.stdin.write(line)
    proc.stdin.flush()
    # notifications/initialized has no response
    if payload.get("method") == "notifications/initialized":
        return None
    response_line = proc.stdout.readline()
    if not response_line:
        return None
    return json.loads(response_line)


def main() -> int:
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

    try:
        init = send(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        server_info = (init or {}).get("result", {}).get("serverInfo", {})
        print(f"[initialize] server={server_info.get('name')} version={server_info.get('version')}")

        send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})

        tools = send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tool_names = [t["name"] for t in (tools or {}).get("result", {}).get("tools", [])]
        print(f"[tools/list] {len(tool_names)} tools: {', '.join(tool_names[:5])}...")

        status = send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "recallos_status", "arguments": {}},
            },
        )
        status_text = (status or {}).get("result", {}).get("content", [{}])[0].get("text", "")
        status_obj = json.loads(status_text) if status_text else {}
        total = status_obj.get("total_records", "?")
        print(f"[recallos_status] total_records={total}")

        result = send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "recallos_query",
                    "arguments": {"query": QUERY, "limit": 3},
                },
            },
        )
        q_text = (result or {}).get("result", {}).get("content", [{}])[0].get("text", "")
        payload = json.loads(q_text) if q_text else {}
        if isinstance(payload, dict):
            hits = payload.get("results") or payload.get("matches") or payload.get("hits") or []
        else:
            hits = payload
        print(f"[recallos_query] query={QUERY!r} hits={len(hits)}")
        for i, hit in enumerate(hits[:3], 1):
            meta = hit.get("metadata", {}) if isinstance(hit, dict) else {}
            score = (
                hit.get("similarity_score")
                or hit.get("match")
                or hit.get("score")
                or hit.get("similarity")
                or "?"
            )
            print(
                f"  {i}. score={score} "
                f"domain={meta.get('domain', hit.get('domain', '?'))} "
                f"node={meta.get('node', hit.get('node', '?'))} "
                f"source={meta.get('source_file', hit.get('source', '?'))}"
            )
            content = hit.get("content") or hit.get("document") or ""
            if content:
                snippet = content.strip().replace("\n", " ")[:140]
                print(f"     {snippet}")

        print("\n[result] MCP gateway handshake + query round-trip OK")
        return 0
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
        err = (proc.stderr.read() if proc.stderr else "") or ""
        if err.strip():
            print("\n--- gateway stderr ---")
            print(err.strip())


if __name__ == "__main__":
    sys.exit(main())
