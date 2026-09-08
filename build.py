#!/usr/bin/env python3
"""Build robo-rec into a standalone folder using Nuitka."""
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
        "--standalone",
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
        "--output-filename=Roborec.exe",
        "--output-dir=dist",
        str(repo_root / "src" / "robo_rec" / "main.py"),
    ]

    print("Building with Nuitka...")
    print("This may take 10-20 minutes on first build...\n")
    result = subprocess.run(cmd, cwd=repo_root, check=False)

    if result.returncode == 0:
        matches = list(dist.rglob("Roborec.exe")) or list(dist.rglob("Roborec"))
        if matches:
            exe_path = matches[0]
            folder = exe_path.parent
            total_size = sum(f.stat().st_size for f in folder.rglob("*") if f.is_file())
            print(f"\n✓ Build successful!")
            print(f"  Folder to copy: {folder}")
            print(f"  Executable:     {exe_path}")
            print(f"  Total size:     {total_size / (1024**2):.1f} MB")
            print("\nCopy the WHOLE folder above to the flash drive, not just the executable.")
        else:
            print("\n✗ Build completed but Roborec.exe not found under dist/")

    sys.exit(result.returncode)


if __name__ == "__main__":
    build()
