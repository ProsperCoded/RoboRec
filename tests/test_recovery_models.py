import pytest

from robo_rec.recovery.exceptions import InvalidSpecError
from robo_rec.recovery.models import (
    MissingWordKnownPositionSpec,
    MissingWordUnknownPositionSpec,
    RearrangementSpec,
    TypoCorrectionSpec,
)

WORDS_12 = ["word"] * 12


def test_spec_requires_addrs_or_mpk():
    words = WORDS_12.copy()
    words[0] = None
    with pytest.raises(InvalidSpecError):
        MissingWordKnownPositionSpec(words=words, wallet_type="bip39")


def test_known_position_rejects_zero_missing():
    with pytest.raises(InvalidSpecError):
        MissingWordKnownPositionSpec(words=WORDS_12.copy(), wallet_type="bip39", addrs=["a"])


def test_known_position_rejects_five_missing():
    words = [None] * 5 + WORDS_12[5:]
    with pytest.raises(InvalidSpecError):
        MissingWordKnownPositionSpec(words=words, wallet_type="bip39", addrs=["a"])


def test_known_position_allows_four_missing():
    words = [None] * 4 + WORDS_12[4:]
    spec = MissingWordKnownPositionSpec(words=words, wallet_type="bip39", addrs=["a"])
    assert spec is not None


def test_unknown_position_rejects_three_missing():
    words = WORDS_12[:9]  # 12 - 9 = 3 missing
    with pytest.raises(InvalidSpecError):
        MissingWordUnknownPositionSpec(
            words=words, full_length=12, wallet_type="bip39", addrs=["a"]
        )


def test_unknown_position_allows_two_missing():
    words = WORDS_12[:10]  # 12 - 10 = 2 missing
    spec = MissingWordUnknownPositionSpec(
        words=words, full_length=12, wallet_type="bip39", addrs=["a"]
    )
    assert spec is not None


def test_rearrangement_requires_matching_blank_and_scrambled_counts():
    known = [None, None] + WORDS_12[2:]
    with pytest.raises(InvalidSpecError):
        RearrangementSpec(
            known_words=known, scrambled_words=["only_one"], wallet_type="bip39", addrs=["a"]
        )


def test_typo_correction_rejects_empty_mnemonic():
    with pytest.raises(InvalidSpecError):
        TypoCorrectionSpec(best_guess_mnemonic="   ", wallet_type="bip39", addrs=["a"])
