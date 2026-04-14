#!/usr/bin/env python3
"""
build_exe.py — Build the RecallOS desktop .exe with PyInstaller.

Usage:
    python scripts/build_exe.py

Requires: pip install pyinstaller
Output:   dist/RecallOS/RecallOS.exe
"""

import subprocess
import sys
from pathlib import Path

SPEC_FILE = Path(__file__).resolve().parent.parent / "recallos_desktop.spec"
DIST_DIR = Path(__file__).resolve().parent.parent / "dist" / "RecallOS"


def ensure_pyinstaller():
    """Install PyInstaller if not already available."""
    try:
        import PyInstaller  # noqa: F401

        print(f"  PyInstaller {PyInstaller.__version__} found.")
    except ImportError:
        print("  Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def build():
    """Run PyInstaller with the spec file."""
    print(f"\n  Building from: {SPEC_FILE}")
    print(f"  Output dir:    {DIST_DIR}\n")

    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(SPEC_FILE), "--noconfirm"],
        cwd=str(SPEC_FILE.parent),
    )

    if result.returncode != 0:
        print(f"\n  BUILD FAILED (exit code {result.returncode})")
        sys.exit(result.returncode)

    exe_path = DIST_DIR / "RecallOS.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("\n  BUILD OK")
        print(f"  Executable: {exe_path}")
        print(f"  Size:       {size_mb:.1f} MB")
        total_mb = sum(f.stat().st_size for f in DIST_DIR.rglob("*") if f.is_file()) / (1024 * 1024)
        print(f"  Bundle:     {total_mb:.0f} MB total")
    else:
        print(f"\n  WARNING: Expected exe not found at {exe_path}")
        print("  Check dist/ for output.")


def main():
    print("=" * 55)
    print("  RecallOS Desktop — PyInstaller Build")
    print("=" * 55)

    ensure_pyinstaller()
    build()

    print("=" * 55)


if __name__ == "__main__":
    main()
