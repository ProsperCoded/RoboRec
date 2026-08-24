#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "🔨 Building RoboRec with Nuitka..."
echo "This will take 10-20 minutes on first build"
echo ""

rm -rf dist

.venv/bin/python -m nuitka \
  --onefile \
  --follow-imports \
  --include-package=robo_rec \
  --include-package=bip_utils \
  --include-package=coincurve \
  --include-package=PySide6 \
  --windows-console-mode=disable \
  --output-dir=dist \
  src/robo_rec/main.py

if [ -f "dist/main.exe" ]; then
  SIZE=$(du -h dist/main.exe | cut -f1)
  echo ""
  echo "✓ Build successful!"
  echo "  Executable: dist/main.exe"
  echo "  Size: $SIZE"
else
  echo "✗ Build failed - main.exe not found"
  exit 1
fi
