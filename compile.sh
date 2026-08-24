#!/usr/bin/env bash
set -euo pipefail

# Clean up previous build directories
echo "Cleaning up previous builds..."
rm -rf main.bin main.dist main.build main.onefile-build dist

echo "Compiling Robo-Rec with Nuitka..."
uv run python -m nuitka \
  --onefile \
  --windows-console-mode=disable \
  --enable-plugin=pyside6 \
  --main=src/robo_rec/main.py \
  --main=vendor/btcrecover/seedrecover.py \
  --include-data-dir=vendor/btcrecover/derivationpath-lists=vendor/btcrecover/derivationpath-lists \
  --include-data-dir=vendor/btcrecover/btcrecover/wordlists=btcrecover/wordlists \
  --include-data-dir=vendor/btcrecover/btcrecover/wordlists=vendor/btcrecover/btcrecover/wordlists \
  --output-dir=dist

echo "Done! The compiled executables are in the dist/ folder."
