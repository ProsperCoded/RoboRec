# Robo-Rec

Windows desktop application for recovering damaged, incomplete, or disordered
BIP39 seed phrases. Wraps the [btcrecover](https://github.com/3rdIteration/btcrecover)
engine with a native GUI (PySide6), GPU-awareness, and offline wallet address
derivation/verification.

See `robo-rec-prd.md` for the full product requirements document.

## Development setup

```bash
git submodule update --init --recursive
uv sync
uv run python -m robo_rec.main
```

## Project layout

- `src/robo_rec/gui` — PySide6 views and windows
- `src/robo_rec/recovery` — btcrecover subprocess orchestration
- `src/robo_rec/derivation` — BIP32/39/44/49/84 address derivation & verification
- `src/robo_rec/gpu` — GPU/CUDA detection and diagnostics reporting
- `src/robo_rec/util` — shared helpers
- `vendor/btcrecover` — unmodified btcrecover engine (git submodule)
