"""Pure argv-builder functions, one per PRD recovery scenario. No subprocess involved here —
these just construct the seedrecover.py CLI argument list, so they're independently testable
against the exact strings already validated by hand (robo-rec-implementation.md).

All builders always pass --wallet-type explicitly (never rely on address-prefix
auto-detection — robo-rec-implementation.md Section 3) and --no-gui/--dsw so the subprocess
never blocks on a Tk dialog or security-warning prompt.
"""

from __future__ import annotations

from pathlib import Path

from robo_rec.recovery.models import (
    MissingWordKnownPositionSpec,
    MissingWordUnknownPositionSpec,
    RearrangementSpec,
    TypoCorrectionSpec,
)
from robo_rec.recovery.tokenlist import build_tokenlist_file

_COMMON_FLAGS = ["--no-gui", "--dsw"]


def _target_flags(addrs: list[str] | None, mpk: str | None, addr_limit: int) -> list[str]:
    flags: list[str] = []
    if addrs:
        flags += ["--addrs", *addrs]
    if mpk:
        flags += ["--mpk", mpk]
    flags += ["--addr-limit", str(addr_limit)]
    return flags


def build_rearrangement_args(spec: RearrangementSpec) -> tuple[list[str], Path]:
    """Returns (argv, tokenlist_path). The caller owns deleting tokenlist_path once the
    subprocess has exited."""
    tokenlist_path = build_tokenlist_file(
        known_words=spec.known_words, scrambled_words=spec.scrambled_words
    )
    argv = [
        *_COMMON_FLAGS,
        "--wallet-type",
        spec.wallet_type,
        "--tokenlist",
        str(tokenlist_path),
        *_target_flags(spec.addrs, spec.mpk, spec.addr_limit),
        # Deliberately NOT passing --keep-tokens-order: permutation of the unanchored
        # (scrambled) tokens is the whole point of this scenario.
    ]
    return argv, tokenlist_path


def build_missing_word_known_position_args(spec: MissingWordKnownPositionSpec) -> list[str]:
    mnemonic = " ".join(word if word is not None else "%%" for word in spec.words)
    return [
        *_COMMON_FLAGS,
        "--wallet-type",
        spec.wallet_type,
        "--mnemonic",
        mnemonic,
        "--mnemonic-length",
        str(len(spec.words)),
        *_target_flags(spec.addrs, spec.mpk, spec.addr_limit),
    ]


def build_missing_word_unknown_position_args(
    spec: MissingWordUnknownPositionSpec,
) -> list[str]:
    """words is intentionally SHORTER than full_length (missing word(s) simply omitted, not
    '%%') — this is what makes btcrecover search over position as well as word (see
    robo-rec-implementation.md Section 6.2)."""
    mnemonic = " ".join(spec.words)
    return [
        *_COMMON_FLAGS,
        "--wallet-type",
        spec.wallet_type,
        "--mnemonic",
        mnemonic,
        "--mnemonic-length",
        str(spec.full_length),
        *_target_flags(spec.addrs, spec.mpk, spec.addr_limit),
    ]


def build_typo_correction_args(spec: TypoCorrectionSpec) -> list[str]:
    argv = [
        *_COMMON_FLAGS,
        "--wallet-type",
        spec.wallet_type,
        "--mnemonic",
        spec.best_guess_mnemonic,
        *_target_flags(spec.addrs, spec.mpk, spec.addr_limit),
    ]
    if spec.typos is not None:
        argv += ["--typos", str(spec.typos)]
    if spec.big_typos is not None:
        argv += ["--big-typos", str(spec.big_typos)]
    if spec.close_match is not None:
        argv += ["--close-match", str(spec.close_match)]
    return argv
