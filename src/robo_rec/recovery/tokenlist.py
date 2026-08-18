"""Builds --tokenlist files for seed phrase rearrangement (PRD 4.1).

Format validated against vendor/btcrecover/docs/tokenlist_file.md ("Positional Anchors")
and vendor/btcrecover/btcrecover/test/test-listfiles/SeedTokenListTest.txt: a known-correct
word at position N (1-indexed) becomes a line `^N^word`; a word known to be somewhere in the
scrambled segment, but not at a specific position, becomes a plain unanchored line. btcrecover
tries permutations of the unanchored tokens into the remaining slots by default (do not pass
--keep-tokens-order — see recovery/args.py).
"""

from __future__ import annotations

import tempfile
from pathlib import Path


def build_tokenlist_file(
    *,
    known_words: list[str | None],
    scrambled_words: list[str],
    dest_dir: Path | None = None,
) -> Path:
    """Writes a tokenlist file and returns its path.

    known_words is the full-length (12 or 24) word list with None at each position that's
    part of the scrambled segment. scrambled_words are the words known to belong somewhere
    in those blank slots (order irrelevant — that's what's being searched for). The caller
    (BtcrecoverRunner) owns cleanup of the returned path.
    """
    lines: list[str] = []
    for position, word in enumerate(known_words, start=1):
        if word is not None:
            lines.append(f"^{position}^{word}")
    lines.extend(scrambled_words)

    fd, raw_path = tempfile.mkstemp(
        prefix="robo-rec-tokenlist-", suffix=".txt", dir=str(dest_dir) if dest_dir else None
    )
    path = Path(raw_path)
    with open(fd, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path
