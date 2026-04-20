"""
desktop/server.py — FastAPI application for the RecallOS desktop layer.

Responsibilities:
  - Serve the built React frontend as static files at /
  - Expose /api/* routes for the frontend to consume
  - Bind exclusively to 127.0.0.1 (never 0.0.0.0)
"""

import sys
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from desktop.auth import require_session_token, TOKEN_HEADER
from desktop.routes import download as download_routes
from desktop.routes import graph as graph_routes
from desktop.routes import mcp as mcp_routes
from desktop.routes import models as models_routes
from desktop.routes import network as network_routes
from desktop.routes import search as search_routes
from desktop.routes import settings as settings_routes
from desktop.routes import status as status_routes
from desktop.routes import support as support_routes
from desktop.routes import backups as backups_routes
from desktop.routes import provenance as provenance_routes
from desktop.routes import updater as updater_routes
from desktop.routes import upload as upload_routes
from desktop.routes import vault_lock as vault_lock_routes

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

# In a PyInstaller bundle, data files live under sys._MEIPASS
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    STATIC_DIR = Path(sys._MEIPASS) / "desktop" / "static"
else:
    STATIC_DIR = Path(__file__).parent / "static"


# ---------------------------------------------------------------------------
# Route whitelist middleware
# ---------------------------------------------------------------------------

_ALLOWED_PREFIXES = ("/api/", "/api/docs", "/api/openapi.json")


class RouteWhitelistMiddleware(BaseHTTPMiddleware):
    """Reject requests to unknown paths — only /api/* and static assets pass."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Allow API routes
        if path.startswith(_ALLOWED_PREFIXES):
            return await call_next(request)
        # Allow static assets (handled by StaticFiles mount at /)
        if not path.startswith("/api"):
            return await call_next(request)
        # Block unregistered /api paths
        return JSONResponse(status_code=404, content={"detail": "Not found"})


def create_app() -> FastAPI:
    """Build and return the FastAPI application."""
    app = FastAPI(
        title="RecallOS Desktop",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
    )

    # Route whitelist — reject unknown paths before other middleware
    app.add_middleware(RouteWhitelistMiddleware)

    # CORS — restrict to localhost origins, expose session-token header
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1", "http://localhost"],
        allow_origin_regex=r"^http://(127\.0\.0\.1|localhost)(:\d+)?$",
        allow_methods=["*"],
        allow_headers=["*", TOKEN_HEADER],
    )

    # --- API routes (all require session token) -----------------------------
    api_deps = [Depends(require_session_token)]
    app.include_router(status_routes.router, prefix="/api", dependencies=api_deps)
    app.include_router(search_routes.router, prefix="/api", dependencies=api_deps)
    app.include_router(upload_routes.router, prefix="/api", dependencies=api_deps)
    app.include_router(download_routes.router, prefix="/api", dependencies=api_deps)
    app.include_router(graph_routes.router, prefix="/api", dependencies=api_deps)
    app.include_router(network_routes.router, prefix="/api", dependencies=api_deps)
    app.include_router(models_routes.router, prefix="/api", dependencies=api_deps)
    app.include_router(settings_routes.router, prefix="/api", dependencies=api_deps)
    app.include_router(support_routes.router, prefix="/api", dependencies=api_deps)
    app.include_router(backups_routes.router, prefix="/api", dependencies=api_deps)
    app.include_router(provenance_routes.router, prefix="/api", dependencies=api_deps)
    app.include_router(updater_routes.router, prefix="/api", dependencies=api_deps)
    app.include_router(vault_lock_routes.router, prefix="/api", dependencies=api_deps)
    app.include_router(mcp_routes.router, prefix="/api", dependencies=api_deps)

    # --- Static frontend ----------------------------------------------------
    if STATIC_DIR.is_dir():
        # SPA fallback: serve index.html for any non-API, non-file path
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app


# Singleton used by Uvicorn
app = create_app()
