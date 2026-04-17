# -*- mode: python ; coding: utf-8 -*-
"""
recallos_desktop.spec — PyInstaller spec for the RecallOS desktop app.

Build:  pyinstaller recallos_desktop.spec
Output: dist/RecallOS/RecallOS.exe  (one-dir bundle)

Produces a folder-based bundle (not one-file) so the resulting layout
is suitable for wrapping with an Inno Setup installer in Phase 1.
"""

import os
import importlib

# ---------------------------------------------------------------------------
# Locate package data that PyInstaller can't auto-discover
# ---------------------------------------------------------------------------

# ChromaDB migrations — required at runtime for DB initialisation
chromadb_pkg = os.path.dirname(importlib.import_module("chromadb").__file__)
chromadb_migrations = os.path.join(chromadb_pkg, "migrations")

# Built React frontend served by FastAPI
static_dir = os.path.join("desktop", "static")

# ---------------------------------------------------------------------------
# Hidden imports — modules loaded via dynamic import / plugin discovery
# ---------------------------------------------------------------------------

chromadb_hidden = [
    "chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2",
    "chromadb.telemetry.product.posthog",
    "chromadb.api.segment",
    "chromadb.db.impl",
    "chromadb.db.impl.sqlite",
    "chromadb.migrations",
    "chromadb.migrations.embeddings_queue",
    "chromadb.migrations.metadb",
    "chromadb.migrations.sysdb",
    "chromadb.segment.impl.manager",
    "chromadb.segment.impl.manager.local",
    "chromadb.segment.impl.metadata",
    "chromadb.segment.impl.metadata.sqlite",
    "chromadb.segment.impl.vector",
    "chromadb.execution.executor.local",
    "chromadb.quota.simple_quota_enforcer",
    "chromadb.rate_limit.simple_rate_limit",
]

uvicorn_hidden = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
]

app_hidden = [
    # Our own packages — uvicorn string import won't be traced
    "desktop",
    "desktop.server",
    "desktop.auth",
    "desktop.db",
    "desktop.routes",
    "desktop.routes.status",
    "desktop.routes.network",
    "desktop.routes.models",
    "desktop.routes.search",
    "desktop.routes.upload",
    "desktop.routes.download",
    "desktop.routes.settings",
    "desktop.services",
    "desktop.services.network_policy",
    "desktop.services.model_manager",
    "desktop.services.search_service",
    "desktop.services.job_manager",
    "desktop.services.secrets_store",
    "desktop.services.backup_service",
    "desktop.services.crypto_service",
    "recallos",
    "recallos.cli",
    "recallos.config",
    "recallos.diagnostics",
    "recallos.retrieval_engine",
    "recallos.ingest_engine",
    "recallos.conversation_ingest",
    "recallos.recall_graph",
    "recallos.vault_graph",
    "recallos.recallscript",
    "recallos.bootstrap",
    "recallos.agent_log",
    "recallos.mcp_gateway",
    "recallos.exceptions",
    "recallos.entity_detector",
    "recallos.node_detector_local",
]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

a = Analysis(
    ["desktop/app.py"],
    pathex=["."],
    binaries=[],
    datas=[
        (static_dir, os.path.join("desktop", "static")),
        (chromadb_migrations, os.path.join("chromadb", "migrations")),
    ],
    hiddenimports=chromadb_hidden + uvicorn_hidden + app_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test / dev-only packages to keep bundle smaller
        "pytest",
        "ruff",
        "twine",
        "build",
        "pip",
        "setuptools",
    ],
    noarchive=False,
    optimize=0,
    module_collection_mode={
        "chromadb": "py",  # force pure-python collection for chromadb
    },
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RecallOS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # no console window — pywebview provides the UI
    icon=None,  # TODO: add app icon in Phase 1
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="RecallOS",
)
