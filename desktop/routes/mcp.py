"""
/api/mcp/* — MCP integration setup and status.
"""

import sys

from fastapi import APIRouter

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/status")
def mcp_status():
    """Return MCP gateway availability and setup instructions."""
    # Check if the mcp_gateway module is importable
    try:
        from recallos.mcp_gateway import TOOLS

        tool_count = len(TOOLS)
    except Exception:
        tool_count = 0

    python_path = sys.executable
    setup_command = f"claude mcp add recallos -- {python_path} -m recallos.mcp_gateway"

    return {
        "available": tool_count > 0,
        "tool_count": tool_count,
        "python_path": python_path,
        "setup_command": setup_command,
        "tools": _list_tools(),
    }


def _list_tools() -> list[dict]:
    try:
        from recallos.mcp_gateway import TOOLS

        return [{"name": name, "description": tool["description"]} for name, tool in TOOLS.items()]
    except Exception:
        return []
