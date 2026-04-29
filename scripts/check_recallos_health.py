"""Unified RecallOS health check: vault connectivity + MCP gateway round-trip.

This script is designed for automation (startup checks, scheduled tasks, CI).
It exits non-zero on any hard failure.

Checks:
  1. Warp MCP config exists and contains a `recallos` server.
  2. RecallOS vault is reachable via ChromaDB and collection metadata is readable.
  3. MCP gateway handles initialize/tools/list/recallos_status/recallos_query.
  4. MCP-reported total_records matches direct vault count.
  5. (optional) Auto-repair drifted/missing RecallOS MCP config before checks.

Examples:
  python scripts/check_recallos_health.py
  python scripts/check_recallos_health.py --query "auth decisions"
  python scripts/check_recallos_health.py --json
  python scripts/check_recallos_health.py --auto-repair-mcp
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_QUERY = "health check recallos memory"
PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"
RECALLOS_SERVER_NAME = "recallos"
RECALLOS_GATEWAY_ARGS = ["-m", "recallos.mcp_gateway"]
REQUIRED_MCP_ENV = {
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUTF8": "1",
}


def _line(status: str, label: str, detail: str = "") -> None:
    icon = {"PASS": "✔", "FAIL": "✗", "WARN": "⚠"}.get(status, "·")
    print(f"[{status}] {icon} {label}")
    if detail:
        print(f"       {detail}")


def _recognized_server_map(config: dict[str, Any]) -> dict[str, Any]:
    if isinstance(config.get("mcpServers"), dict):
        return config["mcpServers"]
    if isinstance(config.get("mcp_servers"), dict):
        return config["mcp_servers"]
    if isinstance(config.get("servers"), dict):
        return config["servers"]
    if isinstance(config.get("mcp"), dict) and isinstance(config["mcp"].get("servers"), dict):
        return config["mcp"]["servers"]
    # Flat map fallback
    return {
        k: v
        for k, v in config.items()
        if isinstance(v, dict) and ("command" in v or "url" in v or "args" in v or "warp_id" in v)
    }


def _load_json_file(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected object at root in {path}")
    return data


def _load_recallos_file_config() -> tuple[str, str]:
    config_path = Path.home() / ".recallos" / "config.json"
    vault_path = os.path.expanduser("~/.recallos/vault")
    collection_name = "recallos_records"
    if config_path.exists():
        try:
            cfg = _load_json_file(config_path)
            vault_path = cfg.get("vault_path", vault_path)
            collection_name = cfg.get("collection_name", collection_name)
        except Exception:
            # Keep resilient defaults if config is malformed.
            pass
    return vault_path, collection_name


def _resolve_vault_and_collection(server: dict[str, Any]) -> tuple[str, str]:
    file_vault, file_collection = _load_recallos_file_config()
    env = server.get("env", {})
    if isinstance(env, dict) and env.get("RECALLOS_VAULT_PATH"):
        return env["RECALLOS_VAULT_PATH"], file_collection
    return file_vault, file_collection


def _resolve_server_container_for_write(config: dict[str, Any]) -> tuple[dict[str, Any], str]:
    if isinstance(config.get("mcpServers"), dict):
        return config["mcpServers"], "mcpServers"
    if isinstance(config.get("mcp_servers"), dict):
        return config["mcp_servers"], "mcp_servers"
    if isinstance(config.get("servers"), dict):
        return config["servers"], "servers"
    if isinstance(config.get("mcp"), dict):
        mcp_block = config["mcp"]
        if isinstance(mcp_block.get("servers"), dict):
            return mcp_block["servers"], "mcp.servers"
    flat_servers = _recognized_server_map(config)
    if flat_servers:
        return config, "flat"
    config["mcpServers"] = {}
    return config["mcpServers"], "mcpServers"


def _canonicalize_recallos_server(
    existing_server: Any, fallback_python_command: str, vault_path: str
) -> dict[str, Any]:
    server = existing_server.copy() if isinstance(existing_server, dict) else {}
    command = server.get("command")
    if not isinstance(command, str) or not command.strip():
        command = fallback_python_command
    server["command"] = command
    server["args"] = list(RECALLOS_GATEWAY_ARGS)
    env_value = server.get("env")
    env: dict[str, str] = (
        {k: v for k, v in env_value.items() if isinstance(k, str) and isinstance(v, str)}
        if isinstance(env_value, dict)
        else {}
    )
    env.update(REQUIRED_MCP_ENV)
    env["RECALLOS_VAULT_PATH"] = vault_path
    server["env"] = env
    for conflict_key in ("url", "headers", "warp_id"):
        server.pop(conflict_key, None)
    return server


def _repair_warp_mcp_config(
    mcp_path: Path, fallback_python_command: str
) -> tuple[bool, str]:
    existed_before = mcp_path.exists()
    repair_notes: list[str] = []

    if existed_before:
        try:
            config = _load_json_file(mcp_path)
        except Exception as exc:
            broken_backup_path = mcp_path.with_name(
                f"{mcp_path.name}.broken-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.bak"
            )
            broken_backup_path.write_text(
                mcp_path.read_text(encoding="utf-8", errors="replace"),
                encoding="utf-8",
            )
            config = {}
            repair_notes.append(
                f"existing file was invalid JSON ({exc}); backup saved to {broken_backup_path}"
            )
    else:
        config = {}

    if not isinstance(config, dict):
        config = {}
        repair_notes.append("existing config root was not an object; reset to object")

    vault_path, _ = _load_recallos_file_config()
    server_container, wrapper_name = _resolve_server_container_for_write(config)
    previous_server = server_container.get(RECALLOS_SERVER_NAME)
    repaired_server = _canonicalize_recallos_server(
        previous_server, fallback_python_command, vault_path
    )

    changed = not existed_before or previous_server != repaired_server
    if changed:
        server_container[RECALLOS_SERVER_NAME] = repaired_server
        mcp_path.parent.mkdir(parents=True, exist_ok=True)
        mcp_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        detail = (
            f"repaired {mcp_path} using wrapper '{wrapper_name}'"
            if existed_before
            else f"created {mcp_path} with wrapper '{wrapper_name}'"
        )
    else:
        detail = f"recallos MCP entry already healthy in {mcp_path} (wrapper '{wrapper_name}')"

    if repair_notes:
        detail = f"{detail}; " + "; ".join(repair_notes)
    return changed, detail


def _check_vault(vault_path: str, collection_name: str) -> tuple[bool, dict[str, Any]]:
    try:
        import chromadb
    except Exception as exc:
        return False, {"error": f"chromadb import failed: {exc}"}

    try:
        client = chromadb.PersistentClient(path=vault_path)
        col = client.get_collection(collection_name)
        count = col.count()
        sample = col.get(limit=1, include=["metadatas"])
        metadatas = sample.get("metadatas", [])
        sample_keys = sorted((metadatas[0] or {}).keys()) if metadatas else []
        return True, {
            "vault_path": vault_path,
            "collection_name": collection_name,
            "count": count,
            "sample_metadata_keys": sample_keys,
        }
    except Exception as exc:
        return False, {"error": str(exc), "vault_path": vault_path, "collection_name": collection_name}


def _build_mcp_env(server: dict[str, Any]) -> dict[str, str]:
    env = os.environ.copy()
    server_env = server.get("env")
    if isinstance(server_env, dict):
        for k, v in server_env.items():
            if isinstance(k, str) and isinstance(v, str):
                env[k] = v
    for env_key, env_value in REQUIRED_MCP_ENV.items():
        env.setdefault(env_key, env_value)
    return env


def _run_mcp_roundtrip(
    command: str, args: list[str], env: dict[str, str], query: str, timeout: int
) -> tuple[bool, dict[str, Any]]:
    cmd = [command, *args]
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "recallos_status", "arguments": {}},
        },
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "recallos_query",
                "arguments": {"query": query, "limit": 1},
            },
        },
    ]
    input_text = "\n".join(json.dumps(r) for r in requests) + "\n"

    try:
        proc = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, {"error": f"MCP process timeout after {timeout}s", "command": cmd}
    except Exception as exc:
        return False, {"error": str(exc), "command": cmd}

    responses: dict[int, dict[str, Any]] = {}
    parse_errors: list[str] = []
    for raw in proc.stdout.splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict) and isinstance(obj.get("id"), int):
                responses[obj["id"]] = obj
        except Exception as exc:
            parse_errors.append(f"{exc}: {line[:120]}")

    if proc.returncode != 0:
        return False, {
            "error": f"MCP process exited with code {proc.returncode}",
            "command": cmd,
            "stderr": (proc.stderr or "").strip(),
        }

    missing = [rid for rid in (1, 2, 3, 4) if rid not in responses]
    if missing:
        return False, {
            "error": f"Missing MCP responses for ids: {missing}",
            "stderr": (proc.stderr or "").strip(),
            "parse_errors": parse_errors,
            "stdout": proc.stdout[-1000:],
        }

    init = responses[1].get("result", {})
    server_info = init.get("serverInfo", {}) if isinstance(init, dict) else {}
    tools_payload = responses[2].get("result", {})
    tools = tools_payload.get("tools", []) if isinstance(tools_payload, dict) else []
    tool_names = [t.get("name") for t in tools if isinstance(t, dict)]

    if "recallos_status" not in tool_names or "recallos_query" not in tool_names:
        return False, {
            "error": "MCP tool list missing required RecallOS tools",
            "tool_names": tool_names,
        }

    status_text = (
        responses[3]
        .get("result", {})
        .get("content", [{}])[0]
        .get("text", "")
    )
    query_text = (
        responses[4]
        .get("result", {})
        .get("content", [{}])[0]
        .get("text", "")
    )

    try:
        status_obj = json.loads(status_text) if status_text else {}
    except Exception as exc:
        return False, {"error": f"Could not parse recallos_status payload: {exc}"}
    try:
        query_obj = json.loads(query_text) if query_text else {}
    except Exception as exc:
        return False, {"error": f"Could not parse recallos_query payload: {exc}"}

    if isinstance(query_obj, dict):
        hits = query_obj.get("results") or query_obj.get("matches") or query_obj.get("hits") or []
    else:
        hits = query_obj if isinstance(query_obj, list) else []

    return True, {
        "command": cmd,
        "server_name": server_info.get("name"),
        "server_version": server_info.get("version"),
        "tool_count": len(tool_names),
        "status_total_records": status_obj.get("total_records"),
        "query_hits": len(hits),
        "stderr": (proc.stderr or "").strip(),
        "parse_errors": parse_errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check RecallOS vault + MCP health with strict pass/fail output."
    )
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Probe query for recallos_query")
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout in seconds for MCP process round-trip (default: 60)",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON summary")
    parser.add_argument(
        "--auto-repair-mcp",
        action="store_true",
        help="Create or repair the RecallOS entry in ~/.warp/.mcp.json before health checks",
    )
    args = parser.parse_args()

    summary: dict[str, Any] = {"checks": [], "overall": PASS}
    hard_fail = False

    mcp_path = Path.home() / ".warp" / ".mcp.json"
    if args.auto_repair_mcp:
        try:
            repaired, repair_detail = _repair_warp_mcp_config(mcp_path, sys.executable)
            repair_status = WARN if repaired else PASS
            _line(repair_status, "MCP auto-repair", repair_detail)
            summary["checks"].append(
                {"name": "mcp_auto_repair", "status": repair_status, "detail": repair_detail}
            )
        except Exception as exc:
            _line(FAIL, "MCP auto-repair", str(exc))
            summary["checks"].append(
                {"name": "mcp_auto_repair", "status": FAIL, "detail": str(exc)}
            )
            hard_fail = True

    if hard_fail:
        summary["overall"] = FAIL
        if args.json:
            print(json.dumps(summary, indent=2))
        return 1
    if not mcp_path.exists():
        _line(FAIL, "Warp MCP config", f"Missing file: {mcp_path}")
        summary["checks"].append(
            {"name": "warp_mcp_config", "status": FAIL, "detail": f"Missing file: {mcp_path}"}
        )
        hard_fail = True
        summary["overall"] = FAIL
        if args.json:
            print(json.dumps(summary, indent=2))
        return 1

    try:
        mcp_config = _load_json_file(mcp_path)
        server_map = _recognized_server_map(mcp_config)
        server = server_map.get(RECALLOS_SERVER_NAME)
        if not isinstance(server, dict):
            raise ValueError(f"No '{RECALLOS_SERVER_NAME}' entry found")
        _line(PASS, "Warp MCP config", f"Loaded recallos server from {mcp_path}")
        summary["checks"].append(
            {"name": "warp_mcp_config", "status": PASS, "detail": f"{mcp_path}"}
        )
    except Exception as exc:
        _line(FAIL, "Warp MCP config", str(exc))
        summary["checks"].append({"name": "warp_mcp_config", "status": FAIL, "detail": str(exc)})
        hard_fail = True
        summary["overall"] = FAIL
        if args.json:
            print(json.dumps(summary, indent=2))
        return 1

    command = server.get("command")
    cmd_args = server.get("args", [])
    if not isinstance(command, str) or not command.strip():
        _line(FAIL, "MCP command", "recallos server has no valid command")
        summary["checks"].append(
            {"name": "mcp_command", "status": FAIL, "detail": "recallos server has no valid command"}
        )
        hard_fail = True
    elif not isinstance(cmd_args, list) or not all(isinstance(a, str) for a in cmd_args):
        _line(FAIL, "MCP args", "recallos server args must be a list of strings")
        summary["checks"].append(
            {"name": "mcp_args", "status": FAIL, "detail": "recallos server args must be list[str]"}
        )
        hard_fail = True
    else:
        _line(PASS, "MCP command", f"{command} {' '.join(cmd_args)}")
        summary["checks"].append(
            {"name": "mcp_command", "status": PASS, "detail": [command, *cmd_args]}
        )

    vault_path, collection_name = _resolve_vault_and_collection(server)
    vault_ok, vault_detail = _check_vault(vault_path, collection_name)
    if vault_ok:
        _line(
            PASS,
            "Vault connectivity",
            (
                f"{vault_detail['collection_name']} count={vault_detail['count']} "
                f"at {vault_detail['vault_path']}"
            ),
        )
        summary["checks"].append(
            {
                "name": "vault_connectivity",
                "status": PASS,
                "detail": vault_detail,
            }
        )
    else:
        _line(FAIL, "Vault connectivity", vault_detail.get("error", "unknown error"))
        summary["checks"].append(
            {
                "name": "vault_connectivity",
                "status": FAIL,
                "detail": vault_detail,
            }
        )
        hard_fail = True

    if not hard_fail:
        env = _build_mcp_env(server)
        mcp_ok, mcp_detail = _run_mcp_roundtrip(command, cmd_args, env, args.query, args.timeout)
        if mcp_ok:
            _line(
                PASS,
                "MCP round-trip",
                (
                    f"server={mcp_detail.get('server_name')} "
                    f"v{mcp_detail.get('server_version')} "
                    f"tools={mcp_detail.get('tool_count')} "
                    f"query_hits={mcp_detail.get('query_hits')}"
                ),
            )
            summary["checks"].append({"name": "mcp_roundtrip", "status": PASS, "detail": mcp_detail})

            direct_count = vault_detail.get("count")
            status_count = mcp_detail.get("status_total_records")
            if isinstance(direct_count, int) and isinstance(status_count, int):
                if direct_count == status_count:
                    _line(PASS, "Record count match", f"direct={direct_count} mcp={status_count}")
                    summary["checks"].append(
                        {
                            "name": "count_match",
                            "status": PASS,
                            "detail": {"direct_count": direct_count, "mcp_count": status_count},
                        }
                    )
                else:
                    _line(FAIL, "Record count match", f"direct={direct_count} mcp={status_count}")
                    summary["checks"].append(
                        {
                            "name": "count_match",
                            "status": FAIL,
                            "detail": {"direct_count": direct_count, "mcp_count": status_count},
                        }
                    )
                    hard_fail = True
            else:
                _line(WARN, "Record count match", "Could not compare integer counts")
                summary["checks"].append(
                    {
                        "name": "count_match",
                        "status": WARN,
                        "detail": {"direct_count": direct_count, "mcp_count": status_count},
                    }
                )
        else:
            _line(FAIL, "MCP round-trip", mcp_detail.get("error", "unknown error"))
            summary["checks"].append({"name": "mcp_roundtrip", "status": FAIL, "detail": mcp_detail})
            hard_fail = True

    summary["overall"] = FAIL if hard_fail else PASS
    print()
    if summary["overall"] == PASS:
        print("[result] PASS — RecallOS vault + MCP are healthy.")
    else:
        print("[result] FAIL — RecallOS health check failed. Review details above.")

    if args.json:
        print(json.dumps(summary, indent=2))
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
