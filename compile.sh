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
  --standalone \
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
  --output-filename=Roborec \
  --jobs="$NUM_CORES" \
  --lto=auto \
  --output-dir=dist \
  src/robo_rec/main.py

EXECUTABLE=$(find dist -type f \( -name "Roborec.exe" -o -name "Roborec" \) | head -n 1)

if [ -z "$EXECUTABLE" ]; then
  echo "✗ Build failed - executable not found under dist/"
  exit 1
fi

FOLDER=$(dirname "$EXECUTABLE")
SIZE=$(du -sh "$FOLDER" | cut -f1)

echo ""
echo "✓ Build successful!"
echo "  Folder to copy: $FOLDER"
echo "  Executable:     $EXECUTABLE"
echo "  Total size:     $SIZE"
echo ""
echo "Copy the WHOLE folder above to the flash drive, not just the executable."
chmod +x "$EXECUTABLE"
