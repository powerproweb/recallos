# -*- mode: python ; coding: utf-8 -*-
"""
recallos_desktop.spec — Windows PyInstaller spec for RecallOS Desktop.

Build:  pyinstaller recallos_desktop.spec
Output: dist/RecallOS/RecallOS.exe  (one-dir bundle)
"""

import sys
import os

sys.path.insert(0, os.path.join(".", "packaging"))
from common import ALL_HIDDEN, CHROMADB_MIGRATIONS, STATIC_FILES, EXCLUDES

a = Analysis(
    ["desktop/app.py"],
    pathex=["."],
    binaries=[],
    datas=[STATIC_FILES, CHROMADB_MIGRATIONS],
    hiddenimports=ALL_HIDDEN,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    optimize=0,
    module_collection_mode={
        "chromadb": "py",
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
