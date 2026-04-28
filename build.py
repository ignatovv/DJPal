#!/usr/bin/env python3
"""
Build script for DJPal.
Installs PyInstaller if needed, then builds the standalone executable.

Usage:
    python build.py
"""

import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(result.returncode)


def main() -> None:
    print("=== DJPal build ===")

    # Ensure pyinstaller is available
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("Installing PyInstaller...")
        run([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Ensure all project dependencies are installed (needed for analysis)
    requirements = Path(__file__).parent / "requirements.txt"
    if requirements.exists():
        print("Installing project requirements...")
        run([sys.executable, "-m", "pip", "install", "-r", str(requirements)])

    # Build
    run(["pyinstaller", "--clean", "djpal.spec"])

    dist = Path("dist") / "DJPal"
    print(f"\n✓ Build complete → {dist}/")
    print(f"  Main binary:    {dist}/djpal")
    print(f"  Deemix runner:  {dist}/deemix_runner")
    print("\nTo zip for distribution:")
    print("  make zip     OR     zip -r DJPal-macOS.zip dist/DJPal/")
    print("\nFriend setup (macOS):")
    print("  unzip DJPal-macOS.zip")
    print("  cd DJPal")
    print("  xattr -cr djpal deemix_runner   # remove macOS quarantine")
    print("  ./djpal")


if __name__ == "__main__":
    main()
