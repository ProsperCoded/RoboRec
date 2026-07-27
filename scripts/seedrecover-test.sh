#!/usr/bin/env bash
# Thin wrapper around vendor/btcrecover/seedrecover.py for quick terminal testing.
# Usage: scripts/seedrecover-test.sh --mnemonic "..." --addrs <address> [extra seedrecover.py flags]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT/vendor/btcrecover"

exec uv run --project "$REPO_ROOT" python seedrecover.py \
  --mnemonic-length 12 \
  --addr-limit 5 \
  --wallet-type bip39 \
  --no-gui \
  --dsw \
  "$@"
