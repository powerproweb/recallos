# -*- mode: python ; coding: utf-8 -*-
"""
macOS PyInstaller spec for RecallOS Desktop.

Build:  cd <project_root> && pyinstaller packaging/macos/recallos_macos.spec
Output: dist/RecallOS.app
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(SPECPATH), ".."))
from common import ALL_HIDDEN, CHROMADB_MIGRATIONS, STATIC_FILES, EXCLUDES

PROJECT_ROOT = os.path.join(SPECPATH, "..", "..")

a = Analysis(
    [os.path.join(PROJECT_ROOT, "desktop", "app.py")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=[STATIC_FILES, CHROMADB_MIGRATIONS],
    hiddenimports=ALL_HIDDEN,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    optimize=0,
    module_collection_mode={"chromadb": "py"},
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
    upx=False,  # UPX not recommended on macOS
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="RecallOS",
)

app = BUNDLE(
    coll,
    name="RecallOS.app",
    icon=None,  # TODO: add .icns icon
    bundle_identifier="com.powerproweb.recallos",
    info_plist={
        "CFBundleDisplayName": "RecallOS",
        "CFBundleShortVersionString": "4.1.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "13.0",
    },
)
