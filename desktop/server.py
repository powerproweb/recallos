"""
desktop/server.py — FastAPI application for the RecallOS desktop layer.

Responsibilities:
  - Serve the built React frontend as static files at /
  - Expose /api/* routes for the frontend to consume
  - Bind exclusively to 127.0.0.1 (never 0.0.0.0)
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from desktop.routes import status as status_routes

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

    # CORS — only allow the local pywebview origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tightened in Phase 0.2 with session token
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- API routes ---------------------------------------------------------
    app.include_router(status_routes.router, prefix="/api")

    # --- Static frontend ----------------------------------------------------
    if STATIC_DIR.is_dir():
        # SPA fallback: serve index.html for any non-API, non-file path
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app


# Singleton used by Uvicorn
app = create_app()
