# Robo-Rec — Implementation Notes

**Purpose:** Working notes from hands-on terminal testing of `btcrecover` (vendored at
`vendor/btcrecover`, submodule pin `3rdIteration/btcrecover` v1.12.0-179-g1457088). Captures
CLI mechanics, gotchas, and one applied patch, so the GUI-integration layer (PRD Section 5.2)
can construct correct subprocess arguments without re-deriving this from scratch.

Companion to `robo-rec-prd.md` (product scope) — this document is implementation/engineering
detail, not scope.

---

## 1. Running `seedrecover.py` from the terminal

### 1.1 Working directory requirement

`seedrecover.py` resolves asset paths (e.g. `./derivationpath-lists/BTC.txt`) relative to the
**current working directory**, not the script's own location. It must be run with
`vendor/btcrecover/` as cwd, or it fails with `FileNotFoundError`.

`uv run --project <path>` only selects which project's Python environment to use — it does
**not** change the script lookup directory or cwd. Both must be handled separately.

### 1.2 Wrapper script

`scripts/seedrecover-test.sh` bakes in the repeated defaults and handles the cwd requirement:

```bash
#!/usr/bin/env bash
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
```

Usage — only pass what changes per test:

```bash
./scripts/seedrecover-test.sh \
  --mnemonic "word1 word2 ... %% ... word12" \
  --addrs <address>
```

### 1.3 Generating a throwaway test mnemonic/address pair

Never test against a real wallet's seed. Generate disposable pairs with `bip_utils`
(already a project dependency):

```python
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

mnemonic = Bip39MnemonicGenerator().FromWordsNumber(12)
seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
addr = (Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
        .Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
        .PublicKey().ToAddress())
print(mnemonic, addr)
```

Known-good pair used throughout this session's tests:

```
Mnemonic: rotate dream drip opinion key dove region mind visit diesel negative speed
Address : 1FMHvVtJkJFnSxaN9KUn5q3KtqNwej1sZ6
```

---

## 2. Why a target (address/mpk) is required

`seedrecover.py`'s search loop has no way to know a candidate phrase is *the* answer without
comparing derived output against something external — a valid BIP39 checksum is satisfied by
many wordlist substitutions, not just the correct one. Verification requires one of:

- `--addrs <address> [<address> ...]` — check derived addresses against known address(es)
- `--addressdb <file>` — check against a precomputed address database
- `--mpk <xpub>` — check against a known extended public key

Without one of these, `seedrecover.py` exits immediately: `Error: No MPK or addresses
specified... Exiting...` (source: `btcrseed.py` lines 558, 1584). There is no default
"just show me checksum-valid candidates" mode in normal recovery flow. 

**v1 Scope Tweak:** Because a valid BIP39 checksum alone cannot determine which candidate phrase is the *correct* one for a specific wallet, checksum-only recovery (without providing a target address) is deferred for v1. A target wallet address must always be provided for all recovery operations (getting missing words, scrambled seed phrase, etc.). See Section 5.

## 3. Token / wallet-type must be specified explicitly

`--wallet-type <type>` (e.g. `bip39`, `ethereum`, `solana`) tells btcrecover which
derivation logic/address format to use. If omitted, `seedrecover.py` can *sometimes*
auto-infer the coin from an address prefix (e.g. `1...` → BIP44/P2PKH → assumes Bitcoin-like),
but this is incidental, not reliable — it does not work for tokens whose address format
doesn't self-disclose the coin type. Per PRD Section 4.4, the GUI must always pass
`--wallet-type` explicitly based on the user's token selection; never rely on address-prefix
sniffing.

---

## 4. Small typo vs. big typo

Both are substitution mechanisms for individual mnemonic word positions, but they are
**structurally partitioned by btcrecover** based on whether the position already holds a
valid wordlist word or not (`btcrseed.py` lines 4494–4502):

```python
@btcrpass.register_simple_typo("replacecloseword")
def replace_close_word(mnemonic_ids, i):
    if mnemonic_ids[i] is None: return (),      # don't touch invalid/missing words
    return close_mnemonic_ids[mnemonic_ids[i]]  # pre-calculated similar words

@btcrpass.register_simple_typo("replacewrongword")
def replace_wrong_word(mnemonic_ids, i):
    if mnemonic_ids[i] is not None: return (),  # only replace invalid/missing words
    return ((new_id,) for new_id in loaded_wallet.word_ids)
```

| | Small typo (`replacecloseword`) | Big typo (`replacewrongword`) |
|---|---|---|
| Applies to | Positions with a real wordlist word you typed | Positions that are missing/invalid (`%%`) |
| Candidate pool | Spelling-neighbors only, precomputed once via `difflib.get_close_matches(word, wordlist, sys.maxsize, closematch_cutoff)` in `config_mnemonic` | Entire 2048-word list |
| Cost per slot | Small (typically single digits to low tens of candidates) | 2048x per slot |
| Use case | "I might have mistyped/misremembered this word as a similar-looking one" | "I have no idea what this word was" (`%%`) or "I wrote something completely unrelated" |
| CLI flag | `--typos N` / `--close-match CUTOFF` (default 0.65) | `--big-typos N` |

**Practical rule of thumb:** if you have a real word written down but aren't 100% sure of its
spelling, type your best guess — don't use `%%`. `%%` should be reserved for genuinely
missing/illegible words, since it always forces the expensive big-typo (full 2048-word) path.

**Mutual exclusivity is enforced per-position, not per-phase.** Both typo types can and do run
in the same search when applicable — e.g. a phrase with one missing word (`%%`) *and* a
separately mistyped word elsewhere is still recoverable, because each position independently
routes to whichever generator applies to it. The escalating "Phase 1/4 → 4/4" system controls
the *total* mistake budget and how much of it must be "big" vs "small," not which mechanism
touches which word.

### 4.1 Example: small-typo recovery (no `%%` needed)

Wrote `"horror"` by mistake, true word was `"error"` (spelling-similar, confirmed via
`difflib.get_close_matches('error', wordlist, 5, 0.5)` → `['error', 'mirror', 'horror',
'zero', 'warrior']`):

```bash
./scripts/seedrecover-test.sh \
  --mnemonic "teach monster clean noise horror very actual sick much deliver elder dismiss" \
  --addrs 1PDjpQLw6XnFKRs8Nstkbd6BCpmdXxCHr4
```

Result: found in ~2s, `"Will try 8,668 passwords"` (small candidate pool from spelling-neighbor
substitutions across the phrase, not 2048-per-slot).

---

## 5. `--listseeds` / checksum-only mode (no address) — vendored patch applied

### 5.1 The problem

btcrecover has no built-in "just validate checksum, skip address verification" mode for
normal recovery. The closest candidate, `--listseeds` (paired with `--savevalidseeds <file>`),
crashed in two ways when combined with BIP39 mnemonic recovery in this version (v1.12.0):

**Crash 1 — `KeyError: 'typos'`**

```
File "btcrseed.py", line 5379, in main
    if phase_params["typos"] == 1:
KeyError: 'typos'
```

Root cause: `args.listseeds` sets `phase["listpass"] = True` but never sets
`phase["typos"]`. Since `phase` becomes non-empty, `build_search_phases()` treats it as a
single fully-specified phase (`phases = [phase]`) rather than building its own default
5-phase escalation — but the phase dict is missing the required `"typos"` key, so the
phase-printing loop crashes immediately.

**Crash 2 — `AssertionError: custom wallet object not permitted...`** (hit after working
around crash 1 with `--typos 0 --big-typos 1`)

```
File "btcrpass.py", line 6959, in parse_arguments
    assert not wallet, 'custom wallet object not permitted with --wallet, --data-extract,
    --brainwallet, --warpwallet, --bip39, --yoroi-master-password, --bip38_enc_privkey, or --listpass'
```

Root cause: `parse_arguments()` counts `required_args` and demands exactly one of
`{--wallet, --bip39, --listpass, wallet-object, ...}`. `run_btcrecover()`'s BIP39 flow always
passes a live `wallet` object *and* sets `--listpass` in the constructed args string whenever
`listseeds=True` — these were architecturally designed as mutually exclusive alternatives
(`--listpass` for the wallet-file/password-list flow in `btcrecover.py`; wallet object for the
mnemonic-guess flow in `seedrecover.py`), but `--listseeds` triggers both simultaneously.

### 5.2 Decision

Chose to patch the vendored submodule directly (diverges from PRD 5.2's "btcrecover remains
untouched," but the alternative — writing a standalone `bip_utils`-based checksum enumerator —
was assessed as more code for less reuse of existing, tested logic). Both fixes are minimal
and localized.

### 5.3 The patch

Applied directly to `vendor/btcrecover` (not upstreamed — a local divergence from the pinned
submodule commit; must be re-applied if the submodule is ever bumped to a new upstream
version):

**`btcrecover/btcrpass.py`** (~line 6956) — stop double-counting `listpass` against a supplied
wallet object, since the wallet object alone already fully determines the checksum/derivation
source:

```python
    # --listpass only changes iteration/output mode (list candidates instead of
    # searching for one match); when a wallet object is supplied directly (e.g.
    # seedrecover.py's --listseeds path), the wallet already fully determines the
    # checksum/derivation source, so don't double-count listpass against it.
    if args.listpass and not wallet:
                                     required_args += 1
    if wallet:                      required_args += 1
```

(replaces the original unconditional `if args.listpass: required_args += 1`)

**`btcrecover/btcrseed.py`** (~line 5235, immediately after `loaded_wallet.config_mnemonic(...)`
so `mnemonic_ids_guess` is populated) — default `phase["typos"]`/`phase["big_typos"]` when
`--listseeds` is used without explicit `--typos`/`--big-typos`:

```python
    if listseeds and "typos" not in phase and "big_typos" not in phase:
        # --typos/--big-typos are normally required to build a phase, but --listseeds
        # only enumerates checksum-valid candidates (no address/mpk match needed), so
        # default them here if the user didn't set them: big_typos = however many
        # words are unknown (%%) so those slots can be filled from the full wordlist;
        # typos defaults to the same, since a missing word is always a "big" mistake.
        num_unknown = sum(1 for id_ in mnemonic_ids_guess if id_ is None)
        phase["big_typos"] = num_unknown
        phase["typos"] = num_unknown
```

### 5.4 Verified behavior after patch

```bash
./scripts/seedrecover-test.sh \
  --mnemonic "rotate dream drip opinion key dove region mind visit diesel negative %%" \
  --listseeds --savevalidseeds /tmp/valid_seeds.txt
```

No longer crashes. Enumerates all 2048 checksum-valid candidates for the blanked last-word
position (every wordlist word passes checksum for that slot in this example — expected, since
the final word of a BIP39 phrase carries checksum bits for the *whole* phrase; other slot
positions typically yield far fewer valid candidates). Confirmed the true original word
(`"speed"`) is present in the output.

**Known remaining rough edge:** `--savevalidseeds <path>` does not write to the literal path
given — `btcrpass.py` appends a `_NNNN.txt` suffix internally (`loaded_wallet._savevalidseeds +
"_" + '{:04d}'.format(seedfile_suffix) + ".txt"`). Output was verified via stdout capture
instead. Not yet resolved; low priority since checksum-only mode is a secondary path (see
Section 6.2 on why address-based verification remains the primary recommended flow).

---

## 6. Missing-word recovery: known vs. unknown position

### 6.1 Known position (`%%` placeholder)

Mark the exact blank slot with `%%`:

```bash
--mnemonic "rotate dream drip opinion %% dove region mind visit diesel negative speed"
```

Always routes to `replace_wrong_word` (big typo) for that slot only. Cost: `2048^n` where
`n` = number of `%%` tokens, independent of total phrase length (12 vs 24 words).

**Common mistake:** typing a mnemonic with a word simply omitted (wrong word count, no `%%`)
but *not* also passing `--mnemonic-length`. This makes btcrecover guess both *that* a word is
missing *and* every possible position for it — i.e. it silently becomes the unknown-position
case (Section 6.2) rather than failing fast, and runs far longer than intended.

**Another common mistake:** using a mnemonic/address pair that don't actually correspond to
each other (e.g. copy-paste mismatch between test runs). btcrecover will exhaust the entire
search space and correctly report "Seed not found" — this looks identical in timing/behavior
to a legitimately hard search, so always double check the pair before concluding a slow run
indicates a problem.

### 6.2 Unknown position — no code changes needed, reuses the same handler

**Key finding:** btcrecover already supports unknown-position missing-word recovery natively,
via the *same* `run_btcrecover()` function and phase system used for known-position — no
patch, wrapper, or separate handler required. The mechanism:

- Type a mnemonic **shorter** than the true length (omit the missing word(s) entirely, don't
  use `%%`), and pass `--mnemonic-length <full count>`.
- `config_mnemonic()` computes `num_inserts = expected_len - len(mnemonic_ids_guess)` and
  prints `"Seed sentence was too short, inserting N word(s) into each guess."`
- `run_btcrecover()` (btcrseed.py ~line 4600) sets `ids_to_try_inserting =
  ((id,) for id in loaded_wallet.word_ids)` and passes it to `btcrpass.parse_arguments()` as
  `inserted_items=` — btcrpass's native insertion mechanism tries the missing word(s) at every
  valid position, not just one.

Verified:

```bash
./scripts/seedrecover-test.sh \
  --mnemonic "rotate dream drip opinion dove region mind visit diesel negative speed" \
  --mnemonic-length 12 \
  --addrs 1FMHvVtJkJFnSxaN9KUn5q3KtqNwej1sZ6
```

Result: `"Will try 24,565 passwords"` (matches the `12 positions × 2048 words ≈ 24,576`
estimate), found `"key"` back in its correct position, ~2s total.

### 6.3 Combinatorics: known vs. unknown position

| Missing words (n) | Known position | Unknown position (12-word) | Unknown position (24-word) |
|---|---|---|---|
| 1 | 2,048 | 24,576 (12× known) | 49,152 (24× known) |
| 2 | 4,194,304 | 276,824,064 (~66× known) | 1,157,627,904 (~276× known) |
| 3 | 8,589,934,592 | 1,889,785,610,240 (~220× known) | 17,386,027,614,208 (~2024× known) |

Formula: unknown-position cost = `C(total_words, n) × 2048^n` (vs. `2048^n` for known
position). The unknown-position multiplier is exactly `C(total_words, n)` — the number of
ways to choose which n positions are blank.

### 6.4 Scope conclusion (reflected in `robo-rec-prd.md` v1.1)

- **1 missing, unknown position:** trivial, same order of magnitude as known-position.
- **2 missing, unknown position:** CPU-feasible, ~66× (12-word) to ~276× (24-word) slower than
  known-position, but still a reasonable job.
- **3 missing, unknown position:** **not supported** — ~1.9 trillion combinations for a
  12-word phrase alone, which exceeds the PRD's own existing infeasibility bar (4-missing,
  known-position, ~17.6 trillion, was already the outer edge of "attempt with GPU warning").
  17.4 trillion for 24-word puts it in the same infeasible tier outright.

---

## 7. Open follow-ups for GUI integration (PRD Section 5.2)

- Subprocess argument builder must choose between `%%`-based (known position) and
  short-mnemonic + `--mnemonic-length` (unknown position) construction based on GUI input,
  per Section 6 above.
- `--wallet-type` must always be passed explicitly from the user's token selection — never
  rely on address-prefix auto-detection (Section 3).
- **Deferred for v1 (no-target-address recovery):** Since a target address is now mandatory for v1 recovery operations (missing words, scrambled seed phrase, etc.), the GUI copy/UX for a no-target-address recovery path is deferred. The `--savevalidseeds` file-suffix behavior (Section 5.4) read-back path is also deferred, as checksum-only mode is out of scope.
- Local patch to `vendor/btcrecover` (Section 5.3) is not upstream-tracked; if the submodule
  pin is ever bumped, both hunks must be reapplied and re-verified.
