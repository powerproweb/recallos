# -*- mode: python ; coding: utf-8 -*-
"""
Linux PyInstaller spec for RecallOS Desktop.

Build:  cd <project_root> && pyinstaller packaging/linux/recallos_linux.spec
Output: dist/RecallOS/RecallOS  (one-dir bundle)

To create an AppImage from this:
  1. Build with this spec
  2. Create AppDir structure: dist/RecallOS.AppDir/
  3. Add .desktop file + icon
  4. Run appimagetool dist/RecallOS.AppDir RecallOS-x86_64.AppImage
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
    strip=True,  # strip debug symbols on Linux for smaller binary
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name="RecallOS",
)
