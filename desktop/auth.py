"""
desktop/auth.py — Per-session authentication for the desktop API.

Every desktop session generates a cryptographically random token at startup.
The pywebview frontend receives this token via the URL query string and sends
it back on every ``/api/*`` request as an ``X-Session-Token`` header.

This prevents other localhost processes from calling the API.
"""

import os
import secrets

from fastapi import Request, HTTPException

_SESSION_TOKEN: str | None = None

TOKEN_HEADER = "X-Session-Token"
TOKEN_QUERY = "token"


def generate_session_token() -> str:
    """Create a new session token and store it for this process."""
    global _SESSION_TOKEN
    _SESSION_TOKEN = secrets.token_urlsafe(32)
    os.environ["RECALLOS_SESSION_TOKEN"] = _SESSION_TOKEN
    return _SESSION_TOKEN


def get_session_token() -> str | None:
    """Return the current session token (if any)."""
    return _SESSION_TOKEN or os.environ.get("RECALLOS_SESSION_TOKEN")


async def require_session_token(request: Request) -> None:
    """FastAPI dependency — reject requests without a valid session token.

    When no token has been configured (e.g. running the server standalone
    in dev mode without ``app.py``) auth is skipped so the dev workflow
    is not blocked.
    """
    expected = get_session_token()
    if expected is None:
        return  # no token configured — dev/test mode

    provided = request.headers.get(TOKEN_HEADER)
    if provided == expected:
        return

    raise HTTPException(status_code=403, detail="Invalid or missing session token")
