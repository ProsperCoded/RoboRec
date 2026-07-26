# Robo-Rec — Technical Product Requirements Document

**Version:** 1.0
**Type:** Windows Desktop Application
**Status:** Approved for development

---

## 1. Overview

Robo-Rec is a Windows desktop application for recovering damaged, incomplete, or disordered BIP39 seed phrases (12-word and 24-word). It wraps the existing `btcrecover` engine, adds a native GUI, GPU-awareness, and wallet address derivation/verification — without checking live balances or requiring internet access.

---

## 2. Goals

- Provide a non-technical, GUI-driven front end for `btcrecover`'s CLI capabilities.
- Support the specific recovery scenarios the client has requested and that are mathematically feasible.
- Auto-detect and report GPU acceleration availability (NVIDIA/CUDA), falling back cleanly to CPU.
- Ship as a single Windows executable with minimal install friction.

## 3. Non-Goals (Explicitly Out of Scope)

- Cloud GPU rental / distributed compute integration.
- Recovering 4 or more missing words in any configuration.
- Full rearrangement of a 24-word phrase from completely unknown positions.
- Balance checking / blockchain API integration of any kind.
- wallet.dat password/passphrase recovery or file corruption repair (separate, unscoped feature — different client ask, not part of this build).
- Non-English wordlists (initial release).

---

## 4. Core Functional Requirements

### 4.1 Seed Phrase Rearrangement
- **12-word, fully scrambled:** Test all orderings. 12! ≈ 479M combinations. ~1-2 hrs on CPU.
- **24-word, partially scrambled:** If the user can identify a known-correct sub-segment (e.g., "words 1-12 are correct, 13-24 are scrambled"), only the unknown segment is permuted. Effective complexity reduces to that segment's factorial (e.g., a 12-word unknown segment = same cost as full 12-word case).
- **24-word, fully scrambled (all positions unknown):** Not supported. 24! is computationally infeasible under any realistic hardware budget.

### 4.2 Missing Word Recovery
- Supports 1, 2, or 3 missing words, for both 12-word and 24-word phrases.
- Known word positions required as input (unknown positions multiply search space and increase time significantly, particularly at 3 words).
- 4+ missing words: not supported at any GPU tier (local or cloud) — 2,048⁴ ≈ 17.6 trillion combinations is outside practical turnaround even on enterprise-grade GPUs.

### 4.3 Typo / Error Correction
- Support correcting individual mistyped words within an otherwise-complete phrase, using btcrecover's typo/pattern engine.

### 4.4 Wallet Address Derivation & Verification
- User specifies the target token (Bitcoin, Ethereum, or other BIP39-compatible token).
- App derives addresses by iterating standard derivation paths (BIP-44, BIP-49, BIP-84) covering common wallet software (MetaMask, Trust Wallet, Ledger, Trezor, etc.).
- **With target address provided:** app confirms match and reports which path/wallet type it corresponds to.
- **Without target address:** app still derives and displays the standard first address(es) for the recovered phrase, without a verification step.
- No balance, transaction history, or blockchain lookups of any kind — address derivation is purely local/offline math.

### 4.5 GPU Detection & Reporting
- App detects NVIDIA GPU presence, driver version, CUDA toolkit availability, and PyCUDA accessibility at runtime.
- Results shown in a dedicated GPU Status view within the app.
- Exportable JSON report so the client can send diagnostics back to the developer (developer's own hardware has no discrete GPU, so real-world GPU validation depends on client-side testing).
- If GPU acceleration is unavailable or fails, recovery automatically falls back to CPU — no manual switch required.

### 4.6 Progress & Feedback
- Real-time progress indicator and estimated time remaining during any recovery job.
- Clear success/failure state at job completion, with the recovered phrase (and derived address, if applicable) displayed and copyable.

---

## 5. Technical Architecture

### 5.1 Stack Summary

| Layer | Technology | Notes |
|---|---|---|
| GUI | PySide6 (Qt for Python) | Native Windows look, cross-platform for dev/testing |
| Recovery Engine | `btcrecover` (unmodified, used as-is) | Invoked as a subprocess with constructed CLI arguments — no internal refactor |
| GPU Acceleration | btcrecover's built-in NVIDIA CUDA support | No custom kernel work required |
| Packaging | Nuitka (compiled) | Preferred over PyInstaller for smaller binary size and fewer AV false positives |
| Installer | NSIS | Handles GPU/driver detection messaging during install |

### 5.2 Integration Approach
- btcrecover remains untouched — no forking or internal refactor of its codebase.
- App constructs and issues CLI calls to btcrecover (`seedrecover.py` / `btcrecover.py`) as a subprocess, passing parameters derived from GUI input (missing word count, known positions, wallet type, target address, GPU flag, etc.).
- Subprocess output is streamed back into the GUI for live progress display.

### 5.3 Offline Operation
- Application requires no internet connection at any stage — recovery, derivation, and verification are all local computations.

---

## 6. Development & Testing Environment

### 6.1 Developer Environment Constraints
- Primary development machine: Linux, embedded GPU only (no discrete NVIDIA hardware).
- All CPU-path logic (BIP39 derivation, rearrangement, missing-word combinatorics, address derivation, UI/threading) is developed and tested directly on Linux — PySide6 code is cross-platform and functionally identical across OSes (only native theming differs).

### 6.2 Windows Test Environment
- Windows test VM (via VirtualBox) hosted on an external drive to avoid consuming primary disk space.
- VirtualBox itself installs on the primary drive (lightweight); VM disk images are stored and run entirely from the external drive.

### 6.3 GPU Validation
- Since the developer has no discrete GPU, real GPU-path validation (CUDA detection, accelerated recovery performance) is performed by the client on their own NVIDIA hardware.
- The GPU Status export report (Section 4.5) is the mechanism for the client to confirm and report back GPU functionality.

### 6.4 CI / Build Pipeline
- GitHub Actions used for:
  - Running automated tests on a Windows runner (`windows-latest`) across supported Python versions.
  - Building the final Windows `.exe` via Nuitka on the Windows runner (cross-compiling from Linux is avoided entirely).

---

## 7. Distribution & Antivirus Considerations

- Executable should be code-signed to reduce "Unknown Publisher" warnings and AV false-positive rates.
- Documentation (plain-language) to be included with the installer explaining:
  - Why AV/Defender may flag the app (binary packing, GPU memory access, cryptographic operations).
  - That the app makes no network calls and sends no data anywhere.
  - Steps to whitelist the app if flagged.
- Optional: submit the built binary to major AV vendors' false-positive review processes ahead of client rollout.

---

## 8. Supported Tokens

- Bitcoin (BTC)
- Ethereum (ETH)
- Other standard BIP39-compatible tokens supported by btcrecover's derivation logic

---

## 9. Feasibility Reference Table

| Scenario | Feasible? | Approx. Time (local GPU/CPU) |
|---|---|---|
| 12-word, fully scrambled | Yes | 1–2 hrs (CPU) |
| 24-word, known-correct segment + scrambled remainder | Yes | Depends on scrambled segment size (e.g., 12-word segment ≈ 1–2 hrs) |
| 24-word, fully scrambled (unknown positions) | No | Infeasible (24! combinations) |
| 1 missing word | Yes | Minutes |
| 2 missing words (known positions) | Yes | Up to a few hours |
| 3 missing words (known positions) | Yes | Hours, faster with GPU |
| 3 missing words (unknown positions) | Marginal | GPU strongly recommended |
| 4 missing words (any hardware tier) | No | Infeasible even with enterprise cloud GPUs (~trillions of combinations) |
| Typo correction (complete phrase) | Yes | Fast |

---

## 10. Open Items / Future Considerations (Not Committed)

- wallet.dat password/passphrase recovery — raised by a separate client contact (Peter); not part of current scope, would require distinct tooling and a separate scoping conversation if pursued.
- Cloud GPU rental integration — technically possible via a remote job-dispatch architecture, but explicitly excluded from current build due to added complexity, cost management, and security surface.
- Non-English BIP39 wordlist support.

---

## 11. Deliverables

- `Robo-Rec.exe` (Windows 10/11, Nuitka-compiled, code-signed)
- Installation guide
- User manual with worked examples per scenario in Section 9
- GPU/AV troubleshooting documentation
- GitHub Actions CI/CD pipeline (test + build)
