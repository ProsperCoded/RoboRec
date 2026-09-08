#!/usr/bin/env python3
"""Build robo-rec as a standalone folder using PyInstaller (alternative to Nuitka)."""
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
        "--onedir",
        "--windowed",
        "--name=Roborec",
        f"--icon={repo_root / 'src' / 'robo_rec' / 'gui' / 'assets' / 'app-icon.ico'}",
        f"--add-data={repo_root / 'src' / 'robo_rec' / 'gui' / 'assets'}{';' if sys.platform == 'win32' else ':'}robo_rec/gui/assets",
        f"--distpath={dist / 'dist'}",
        f"--buildpath={dist / 'build'}",
        f"--specpath={dist}",
        "--hidden-import=coincurve._cffi_backend",
        "--hidden-import=bip_utils",
        "--hidden-import=robo_rec",
        "--collect-submodules=bip_utils",
        "--collect-submodules=coincurve",
        "--collect-all=numpy",
        "--collect-all=pyopencl",
        str(repo_root / "src" / "robo_rec" / "main.py"),
    ]

    print("Building with PyInstaller...")
    print(f"Command: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=repo_root, check=False)

    if result.returncode == 0:
        exe_path = dist / "dist" / "Roborec" / "Roborec.exe"
        if exe_path.exists():
            folder = exe_path.parent
            total_size = sum(f.stat().st_size for f in folder.rglob("*") if f.is_file())
            print(f"\n✓ Build successful!")
            print(f"  Folder to copy: {folder}")
            print(f"  Executable:     {exe_path}")
            print(f"  Total size:     {total_size / (1024**2):.1f} MB")
            print("\nCopy the WHOLE folder above to the flash drive, not just the executable.")
        else:
            print(f"\n✗ Build completed but {exe_path} not found")

    sys.exit(result.returncode)


if __name__ == "__main__":
    build()
