#!/usr/bin/env python3
"""Build robo-rec into a single Windows executable using Nuitka."""
import shutil
import subprocess
import sys
from pathlib import Path


def build():
    repo_root = Path(__file__).parent
    dist = repo_root / "dist"

    # Clean previous builds
    if dist.exists():
        shutil.rmtree(dist)

    # Run Nuitka compilation with minimal but complete flags
    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--onefile",
        "--follow-imports",
        "--include-package=robo_rec",
        "--include-package=bip_utils",
        "--include-package=coincurve",
        "--include-package=PySide6",
        "--include-package=numpy",
        "--include-package=pyopencl",
        "--include-data-dir=src/robo_rec/gui/assets=robo_rec/gui/assets",
        "--windows-icon-from-ico=src/robo_rec/gui/assets/app-icon.ico",
        "--windows-console-mode=disable",
        "--output-dir=dist",
        str(repo_root / "src" / "robo_rec" / "main.py"),
    ]

    print("Building with Nuitka...")
    print("This may take 10-20 minutes on first build...\n")
    result = subprocess.run(cmd, cwd=repo_root, check=False)

    if result.returncode == 0:
        exe_path = dist / "main.exe"
        if exe_path.exists():
            print(f"\n✓ Build successful: {exe_path}")
            print(f"  File size: {exe_path.stat().st_size / (1024**2):.1f} MB")

    sys.exit(result.returncode)


if __name__ == "__main__":
    build()
