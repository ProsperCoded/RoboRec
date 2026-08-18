"""End-to-end tests against the real vendored seedrecover.py, using disposable mnemonic/
address pairs generated on the fly (never a real wallet's seed — see
robo-rec-implementation.md Section 1.3). Only fast (<10s) scenarios run by default; anything
slower is marked `slow` and excluded from the default test run (see pyproject.toml addopts).
"""

from __future__ import annotations

import pytest
from bip_utils import Bip39MnemonicGenerator

from robo_rec.derivation import SupportedCoin, derive_addresses
from robo_rec.recovery.models import (
    MissingWordKnownPositionSpec,
    MissingWordUnknownPositionSpec,
    RearrangementSpec,
    TypoCorrectionSpec,
)
from robo_rec.recovery.runner import BtcrecoverRunner


def _fresh_pair(num_words: int = 12) -> tuple[list[str], str]:
    mnemonic = str(Bip39MnemonicGenerator().FromWordsNumber(num_words))
    bip44_address = next(
        a
        for a in derive_addresses(mnemonic, coin=SupportedCoin.BITCOIN, path_types=("bip44",))
    )
    return mnemonic.split(), bip44_address.address


def _run_to_completion(runner: BtcrecoverRunner):
    events = list(runner.run_iter())
    assert events[-1].kind == "finished"
    return events, events[-1].result


def test_missing_word_known_position_end_to_end():
    words, address = _fresh_pair()
    spec_words = words.copy()
    spec_words[4] = None
    spec = MissingWordKnownPositionSpec(words=spec_words, wallet_type="bip39", addrs=[address])
    runner = BtcrecoverRunner(spec)

    events, result = _run_to_completion(runner)

    assert result.succeeded is True
    assert result.mnemonic == " ".join(words)
    assert any(e.kind == "phase" for e in events)
    assert any(e.kind == "eta" for e in events)


def test_missing_word_unknown_position_end_to_end():
    words, address = _fresh_pair()
    spec_words = words.copy()
    del spec_words[4]
    spec = MissingWordUnknownPositionSpec(
        words=spec_words, full_length=12, wallet_type="bip39", addrs=[address]
    )
    runner = BtcrecoverRunner(spec)

    _, result = _run_to_completion(runner)

    assert result.succeeded is True
    assert result.mnemonic == " ".join(words)


def test_typo_correction_end_to_end():
    words, address = _fresh_pair()
    from robo_rec.util.mnemonic import close_words

    # Find a word in this phrase with at least one spelling-neighbor to swap in as the "typo".
    typo_index = None
    substitute = None
    for i, word in enumerate(words):
        neighbors = [w for w in close_words(word, cutoff=0.5, limit=5) if w != word]
        if neighbors:
            typo_index, substitute = i, neighbors[0]
            break
    if typo_index is None:
        pytest.skip("No spelling-neighbor found for this randomly generated phrase")

    typed = words.copy()
    typed[typo_index] = substitute
    spec = TypoCorrectionSpec(
        best_guess_mnemonic=" ".join(typed), wallet_type="bip39", addrs=[address]
    )
    runner = BtcrecoverRunner(spec)

    _, result = _run_to_completion(runner)

    assert result.succeeded is True
    assert result.mnemonic == " ".join(words)


def test_cancel_stops_a_running_search():
    # A 2-missing-word unknown-position search is slow enough to reliably cancel mid-run.
    words, address = _fresh_pair()
    spec_words = words.copy()
    del spec_words[4]
    del spec_words[7]
    spec = MissingWordUnknownPositionSpec(
        words=spec_words, full_length=12, wallet_type="bip39", addrs=[address]
    )
    runner = BtcrecoverRunner(spec)

    event_iter = runner.run_iter()
    next(event_iter)  # "started"
    runner.cancel()
    # Draining the rest should terminate promptly without hanging the test.
    for _ in event_iter:
        pass
    assert runner.is_running is False


@pytest.mark.slow
def test_rearrangement_end_to_end():
    words, address = _fresh_pair()
    known = [None] * 12
    known[0], known[1] = words[0], words[1]
    scrambled = words[2:]
    spec = RearrangementSpec(
        known_words=known, scrambled_words=scrambled, wallet_type="bip39", addrs=[address]
    )
    runner = BtcrecoverRunner(spec)

    _, result = _run_to_completion(runner)

    assert result.succeeded is True
