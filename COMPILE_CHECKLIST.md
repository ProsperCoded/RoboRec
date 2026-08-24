# Nuitka Compilation Checklist for RoboRec

## Included Packages
- ✅ `robo_rec` — Main application package
- ✅ `bip_utils` — BIP39 mnemonics & crypto (includes wordlists in bip/bip39/wordlist/)
- ✅ `coincurve` — C extension for secp256k1 curve operations
- ✅ `PySide6` — Qt GUI framework
- ✅ `pycryptodome` — Cryptographic functions
- ✅ `py_crypto_hd_wallet` — HD wallet derivation

## Included Data Files
- ✅ `src/robo_rec/gui/assets/` — SVG icons (flag.svg, copy.svg, etc.)
- ✅ `bip_utils` wordlists — Auto-included via `--include-package`
- ✅ `PySide6` plugins — Auto-included via `--include-package`

## Build Optimizations
- ✅ Parallel compilation (`--jobs=NUM_CORES`)
- ✅ Link-time optimization (`--lto=auto`)
- ✅ Single binary output (`--onefile`)
- ✅ No console window on Windows (`--windows-console-mode=disable`)

## Known Dependencies
The following are required at runtime and are bundled:
- Python 3.13 runtime
- Qt libraries (via PySide6)
- OpenSSL/libcrypto (via coincurve, pycryptodome)
- System libraries (via C extensions)

## Scripts Available
- `./compile.sh` — Linux/Mac/WSL
- `.\compile.ps1` — PowerShell (Windows)
- `compile.bat` — Command Prompt (Windows)

## Expected Output
- Linux/Mac: `dist/main.bin` (executable)
- Windows: `dist/main.exe` (executable)

## Size Expectations
- ~150-200 MB single binary (PySide6 + dependencies are large)

## Troubleshooting
If still missing files:
1. Check error message for missing `FileNotFoundError: [Errno 2]` path
2. Add `--include-data-files` flag for that specific file pattern
3. For C extensions, add `--include-package=<package_name>`
