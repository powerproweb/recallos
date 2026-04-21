"""
packaging/common.py — Shared PyInstaller configuration for all platforms.

Centralises hidden imports, data files, and excludes so the Windows,
macOS, and Linux specs stay in sync.
"""

import importlib
import os

# ---------------------------------------------------------------------------
# Data files
# ---------------------------------------------------------------------------

chromadb_pkg = os.path.dirname(importlib.import_module("chromadb").__file__)
CHROMADB_MIGRATIONS = (
    os.path.join(chromadb_pkg, "migrations"),
    os.path.join("chromadb", "migrations"),
)
STATIC_FILES = (
    os.path.join("desktop", "static"),
    os.path.join("desktop", "static"),
)

# ---------------------------------------------------------------------------
# Hidden imports
# ---------------------------------------------------------------------------

CHROMADB_HIDDEN = [
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

UVICORN_HIDDEN = [
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

APP_HIDDEN = [
    "desktop",
    "desktop.server",
    "desktop.auth",
    "desktop.crash",
    "desktop.db",
    "desktop.security",
    "desktop.tray",
    "desktop.routes",
    "desktop.routes.backups",
    "desktop.routes.download",
    "desktop.routes.graph",
    "desktop.routes.mcp",
    "desktop.routes.models",
    "desktop.routes.network",
    "desktop.routes.provenance",
    "desktop.routes.search",
    "desktop.routes.settings",
    "desktop.routes.status",
    "desktop.routes.support",
    "desktop.routes.updater",
    "desktop.routes.upload",
    "desktop.routes.vault_lock",
    "desktop.services",
    "desktop.services.backup_service",
    "desktop.services.crypto_service",
    "desktop.services.job_manager",
    "desktop.services.logging_service",
    "desktop.services.model_manager",
    "desktop.services.network_policy",
    "desktop.services.search_service",
    "desktop.services.secrets_store",
    "desktop.services.updater",
    "desktop.services.vault_lock",
    "recallos",
    "recallos.cli",
    "recallos.config",
    "recallos.diagnostics",
    "recallos.exceptions",
    "recallos.extractors",
    "recallos.retrieval_engine",
    "recallos.ingest_engine",
    "recallos.conversation_ingest",
    "recallos.recall_graph",
    "recallos.vault_graph",
    "recallos.recallscript",
    "recallos.bootstrap",
    "recallos.agent_log",
    "recallos.mcp_gateway",
    "recallos.entity_detector",
    "recallos.node_detector_local",
]

ALL_HIDDEN = CHROMADB_HIDDEN + UVICORN_HIDDEN + APP_HIDDEN

# ---------------------------------------------------------------------------
# Excludes
# ---------------------------------------------------------------------------

EXCLUDES = [
    "pytest",
    "ruff",
    "twine",
    "build",
    "pip",
    "setuptools",
]
