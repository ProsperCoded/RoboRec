from robo_rec.recovery.args import (
    build_missing_word_known_position_args,
    build_missing_word_unknown_position_args,
    build_rearrangement_args,
    build_typo_correction_args,
)
from robo_rec.recovery.models import (
    MissingWordKnownPositionSpec,
    MissingWordUnknownPositionSpec,
    RearrangementSpec,
    TypoCorrectionSpec,
)

WORDS_12 = [
    "rotate", "dream", "drip", "opinion", "key", "dove",
    "region", "mind", "visit", "diesel", "negative", "speed",
]
ADDR = "1FMHvVtJkJFnSxaN9KUn5q3KtqNwej1sZ6"


def test_missing_word_known_position_uses_placeholder():
    words = WORDS_12.copy()
    words[4] = None
    spec = MissingWordKnownPositionSpec(words=words, wallet_type="bip39", addrs=[ADDR])
    argv = build_missing_word_known_position_args(spec)

    assert "--mnemonic" in argv
    mnemonic = argv[argv.index("--mnemonic") + 1]
    assert mnemonic == "rotate dream drip opinion %% dove region mind visit diesel negative speed"
    assert "--mnemonic-length" in argv
    assert argv[argv.index("--mnemonic-length") + 1] == "12"
    assert "--wallet-type" in argv
    assert argv[argv.index("--wallet-type") + 1] == "bip39"
    assert "--addrs" in argv
    assert argv[argv.index("--addrs") + 1] == ADDR


def test_missing_word_known_position_omits_gpu_flag_by_default():
    words = WORDS_12.copy()
    words[4] = None
    spec = MissingWordKnownPositionSpec(words=words, wallet_type="bip39", addrs=[ADDR])
    argv = build_missing_word_known_position_args(spec)
    assert "--enable-opencl" not in argv


def test_missing_word_known_position_passes_enable_opencl_when_gpu_requested():
    """--enable-opencl, not --enable-gpu: the latter requires init_opencl_kernel(), which
    WalletBIP39 doesn't implement (only WalletBitcoinCore does) and would error_exit
    immediately in btcrpass.py. See the module docstring for the full trace."""
    words = WORDS_12.copy()
    words[4] = None
    spec = MissingWordKnownPositionSpec(words=words, wallet_type="bip39", addrs=[ADDR])
    argv = build_missing_word_known_position_args(spec, use_gpu=True)
    assert "--enable-opencl" in argv
    assert "--enable-gpu" not in argv


def test_rearrangement_passes_enable_opencl_when_gpu_requested():
    known = [None] * 12
    known[0], known[1] = "rotate", "dream"
    scrambled = WORDS_12[2:]
    spec = RearrangementSpec(
        known_words=known, scrambled_words=scrambled, wallet_type="bip39", addrs=[ADDR]
    )
    argv, tokenlist_path = build_rearrangement_args(spec, use_gpu=True)
    try:
        assert "--enable-opencl" in argv
    finally:
        tokenlist_path.unlink()


def test_typo_correction_passes_enable_opencl_when_gpu_requested():
    spec = TypoCorrectionSpec(
        best_guess_mnemonic=" ".join(WORDS_12), wallet_type="bip39", addrs=[ADDR]
    )
    argv = build_typo_correction_args(spec, use_gpu=True)
    assert "--enable-opencl" in argv


def test_missing_word_unknown_position_omits_word_and_sets_length():
    words = WORDS_12.copy()
    del words[4]  # omit "key" entirely — no placeholder
    spec = MissingWordUnknownPositionSpec(
        words=words, full_length=12, wallet_type="bip39", addrs=[ADDR]
    )
    argv = build_missing_word_unknown_position_args(spec)

    mnemonic = argv[argv.index("--mnemonic") + 1]
    assert mnemonic == "rotate dream drip opinion dove region mind visit diesel negative speed"
    assert "%%" not in mnemonic
    assert argv[argv.index("--mnemonic-length") + 1] == "12"


def test_missing_word_unknown_position_passes_enable_opencl_when_gpu_requested():
    words = WORDS_12.copy()
    del words[4]
    spec = MissingWordUnknownPositionSpec(
        words=words, full_length=12, wallet_type="bip39", addrs=[ADDR]
    )
    argv = build_missing_word_unknown_position_args(spec, use_gpu=True)
    assert "--enable-opencl" in argv


def test_typo_correction_passes_full_mnemonic_as_is():
    mnemonic = " ".join(WORDS_12)
    spec = TypoCorrectionSpec(best_guess_mnemonic=mnemonic, wallet_type="bip39", addrs=[ADDR])
    argv = build_typo_correction_args(spec)

    assert argv[argv.index("--mnemonic") + 1] == mnemonic
    assert "--mnemonic-length" not in argv
    assert "%%" not in mnemonic


def test_typo_correction_forwards_optional_tuning_flags():
    spec = TypoCorrectionSpec(
        best_guess_mnemonic=" ".join(WORDS_12),
        wallet_type="bip39",
        addrs=[ADDR],
        typos=2,
        big_typos=1,
        close_match=0.7,
    )
    argv = build_typo_correction_args(spec)

    assert argv[argv.index("--typos") + 1] == "2"
    assert argv[argv.index("--big-typos") + 1] == "1"
    assert argv[argv.index("--close-match") + 1] == "0.7"


def test_rearrangement_builds_tokenlist_and_argv():
    known = [None] * 12
    known[0], known[1] = "rotate", "dream"
    scrambled = WORDS_12[2:]
    spec = RearrangementSpec(
        known_words=known, scrambled_words=scrambled, wallet_type="bip39", addrs=[ADDR]
    )
    argv, tokenlist_path = build_rearrangement_args(spec)
    try:
        assert "--tokenlist" in argv
        assert argv[argv.index("--tokenlist") + 1] == str(tokenlist_path)
        assert "--keep-tokens-order" not in argv
        assert "--mnemonic" not in argv
        # --tokenlist mode requires both explicitly (seedrecover.py can't infer them from
        # the tokenlist file itself — confirmed by direct terminal testing).
        assert argv[argv.index("--mnemonic-length") + 1] == "12"
        assert argv[argv.index("--language") + 1] == "en"

        content = tokenlist_path.read_text()
        lines = content.splitlines()
        assert "^1^rotate" in lines
        assert "^2^dream" in lines
        for word in scrambled:
            assert word in lines
    finally:
        tokenlist_path.unlink()
