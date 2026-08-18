"""BIP39 mnemonic validation and wordlist helpers, English only (PRD Non-Goals: no
non-English wordlists in the initial release)."""

from __future__ import annotations

import difflib
import importlib.resources
from functools import lru_cache

from bip_utils import Bip39MnemonicValidator

_CLOSE_MATCH_CUTOFF = 0.65  # matches btcrecover's own --close-match default


@lru_cache(maxsize=1)
def english_wordlist() -> tuple[str, ...]:
    """The 2048-word BIP39 English wordlist, bundled with bip_utils."""
    text = (
        importlib.resources.files("bip_utils.bip.bip39")
        .joinpath("wordlist", "english.txt")
        .read_text(encoding="utf-8")
    )
    return tuple(text.split())


def is_valid_word(word: str) -> bool:
    return word.lower() in english_wordlist()


def is_valid_mnemonic(mnemonic: str) -> bool:
    """Checksum-valid BIP39 mnemonic (12 or 24 words, correct checksum bits)."""
    return Bip39MnemonicValidator().IsValid(mnemonic)


def close_words(word: str, *, cutoff: float = _CLOSE_MATCH_CUTOFF, limit: int = 10) -> list[str]:
    """Spelling-neighbor wordlist words for `word`, using the same difflib mechanism
    btcrecover uses internally for small-typo correction (robo-rec-implementation.md
    Section 4). Useful for GUI-side "did you mean" hints before a search is even run."""
    return difflib.get_close_matches(word.lower(), english_wordlist(), limit, cutoff)
