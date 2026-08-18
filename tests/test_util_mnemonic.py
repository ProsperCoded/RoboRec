from robo_rec.util.mnemonic import close_words, english_wordlist, is_valid_mnemonic, is_valid_word

VALID_MNEMONIC = "rotate dream drip opinion key dove region mind visit diesel negative speed"


def test_english_wordlist_has_2048_words():
    assert len(english_wordlist()) == 2048


def test_is_valid_word():
    assert is_valid_word("rotate")
    assert not is_valid_word("notaword")


def test_is_valid_mnemonic_true_for_real_phrase():
    assert is_valid_mnemonic(VALID_MNEMONIC)


def test_is_valid_mnemonic_false_for_bad_checksum():
    tampered = VALID_MNEMONIC.replace("speed", "zebra")
    assert not is_valid_mnemonic(tampered)


def test_close_words_finds_spelling_neighbors():
    # Matches the exact case validated in robo-rec-implementation.md Section 4.
    matches = close_words("error", cutoff=0.5, limit=5)
    assert "error" in matches
    assert "horror" in matches
