#!/usr/bin/env python3
"""Build robo-rec using PyInstaller (alternative to Nuitka)."""
import shutil
import subprocess
import sys
from pathlib import Path


def build():
    repo_root = Path(__file__).parent
    dist = repo_root / "dist_pyinstaller"

    # Clean previous builds
    if dist.exists():
        shutil.rmtree(dist)

    # PyInstaller spec file approach
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=robo-rec",
        f"--distpath={dist / 'dist'}",
        f"--buildpath={dist / 'build'}",
        f"--specpath={dist}",
        "--hidden-import=coincurve._cffi_backend",
        "--hidden-import=bip_utils",
        "--hidden-import=robo_rec",
        "--collect-submodules=bip_utils",
        "--collect-submodules=coincurve",
        str(repo_root / "src" / "robo_rec" / "main.py"),
    ]

    print(f"Building with PyInstaller...")
    print(f"Command: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=repo_root)

    if result.returncode == 0:
        exe_path = dist / "dist" / "robo-rec.exe"
        if exe_path.exists():
            print(f"\n✓ Build successful: {exe_path}")
            print(f"  File size: {exe_path.stat().st_size / (1024**2):.1f} MB")

    sys.exit(result.returncode)


if __name__ == "__main__":
    build()
