"""
desktop/server.py — FastAPI application for the RecallOS desktop layer.

Responsibilities:
  - Serve the built React frontend as static files at /
  - Expose /api/* routes for the frontend to consume
  - Bind exclusively to 127.0.0.1 (never 0.0.0.0)
"""

from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from desktop.auth import require_session_token, TOKEN_HEADER
from desktop.routes import status as status_routes
from desktop.routes import network as network_routes

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> FastAPI:
    """Build and return the FastAPI application."""
    app = FastAPI(
        title="RecallOS Desktop",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
    )

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
    app.include_router(network_routes.router, prefix="/api", dependencies=api_deps)

    # --- Static frontend ----------------------------------------------------
    if STATIC_DIR.is_dir():
        # SPA fallback: serve index.html for any non-API, non-file path
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app


# Singleton used by Uvicorn
app = create_app()
