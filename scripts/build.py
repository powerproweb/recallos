#!/usr/bin/env python3
"""
build.py — Cross-platform build script for RecallOS Desktop.

Detects the current OS and runs the appropriate PyInstaller spec file.

Usage:
    python scripts/build.py           # auto-detect platform
    python scripts/build.py --windows
    python scripts/build.py --macos
    python scripts/build.py --linux
"""

import argparse
import platform
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SPECS = {
    "windows": PROJECT_ROOT / "recallos_desktop.spec",
    "macos": PROJECT_ROOT / "packaging" / "macos" / "recallos_macos.spec",
    "linux": PROJECT_ROOT / "packaging" / "linux" / "recallos_linux.spec",
}

DIST_NAMES = {
    "windows": "RecallOS.exe",
    "macos": "RecallOS.app",
    "linux": "RecallOS",
}


def detect_platform() -> str:
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    else:
        print(f"  Unknown platform: {system}")
        sys.exit(1)


def ensure_pyinstaller():
    try:
        import PyInstaller

        print(f"  PyInstaller {PyInstaller.__version__} found.")
    except ImportError:
        print("  Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def build(plat: str):
    spec = SPECS[plat]
    if not spec.exists():
        print(f"  Spec file not found: {spec}")
        sys.exit(1)

    print(f"\n  Platform:  {plat}")
    print(f"  Spec:      {spec}")
    print(f"  Output:    dist/{DIST_NAMES[plat]}\n")

    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(spec), "--noconfirm"],
        cwd=str(PROJECT_ROOT),
    )

    if result.returncode != 0:
        print(f"\n  BUILD FAILED (exit code {result.returncode})")
        sys.exit(result.returncode)

    dist_dir = PROJECT_ROOT / "dist" / "RecallOS"
    if dist_dir.exists():
        total_mb = sum(f.stat().st_size for f in dist_dir.rglob("*") if f.is_file()) / (1024 * 1024)
        print(f"\n  BUILD OK — {total_mb:.0f} MB total")
    else:
        print("\n  BUILD OK — check dist/ for output")


def main():
    parser = argparse.ArgumentParser(description="Build RecallOS Desktop")
    parser.add_argument("--windows", action="store_true")
    parser.add_argument("--macos", action="store_true")
    parser.add_argument("--linux", action="store_true")
    args = parser.parse_args()

    if args.windows:
        plat = "windows"
    elif args.macos:
        plat = "macos"
    elif args.linux:
        plat = "linux"
    else:
        plat = detect_platform()

    print("=" * 55)
    print("  RecallOS Desktop — Cross-Platform Build")
    print("=" * 55)

    ensure_pyinstaller()
    build(plat)

    print("=" * 55)


if __name__ == "__main__":
    main()
