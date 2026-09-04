#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "🔨 Building RoboRec with Nuitka..."
echo "This will take 10-20 minutes on first build"
echo ""

rm -rf dist

# Get number of CPU cores for parallel compilation
NUM_CORES=$(nproc 2>/dev/null || echo 4)

.venv/bin/python -m nuitka \
  --onefile \
  --follow-imports \
  --enable-plugin=pyside6 \
  --include-package=robo_rec \
  --include-package=bip_utils \
  --include-package=coincurve \
  --include-package=PySide6 \
  --include-package=Crypto \
  --include-package=py_crypto_hd_wallet \
  --include-package=numpy \
  --include-package=pyopencl \
  --include-data-dir="src/robo_rec/gui/assets=robo_rec/gui/assets" \
  --include-data-dir="vendor=vendor" \
  --windows-icon-from-ico="src/robo_rec/gui/assets/app-icon.ico" \
  --windows-console-mode=disable \
  --jobs="$NUM_CORES" \
  --lto=auto \
  --output-dir=dist \
  src/robo_rec/main.py

if [ -f "dist/main.exe" ]; then
  EXECUTABLE="dist/main.exe"
  SIZE=$(du -h dist/main.exe | cut -f1)
elif [ -f "dist/main.bin" ]; then
  EXECUTABLE="dist/main.bin"
  SIZE=$(du -h dist/main.bin | cut -f1)
else
  echo "✗ Build failed - executable not found"
  exit 1
fi

echo ""
echo "✓ Build successful!"
echo "  Executable: $EXECUTABLE"
echo "  Size: $SIZE"
chmod +x "$EXECUTABLE"
