import pytest

from robo_rec.derivation import SupportedCoin, validate_address

BTC_P2PKH_VALID = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
BTC_P2SH_VALID = "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"
BTC_BECH32_VALID = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"  # BIP-173 spec example
BTC_TAPROOT_VALID = "bc1p5d7rjq7g6rdk2yhzks9smlaqtedr4dekq08ge8ztwac72sfr9rusxg3297"
ETH_CHECKSUMMED_VALID = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"


def test_empty_address_is_rejected_with_a_prompt():
    assert validate_address("", SupportedCoin.BITCOIN) is not None
    assert validate_address("   ", SupportedCoin.BITCOIN) is not None


@pytest.mark.parametrize(
    "address",
    [BTC_P2PKH_VALID, BTC_P2SH_VALID, BTC_BECH32_VALID, BTC_TAPROOT_VALID],
)
def test_valid_bitcoin_addresses_of_every_type_pass(address):
    assert validate_address(address, SupportedCoin.BITCOIN) is None


def test_bitcoin_bad_checksum_is_rejected_with_a_helpful_message():
    bad = BTC_P2PKH_VALID[:-1] + ("3" if BTC_P2PKH_VALID[-1] != "3" else "4")
    error = validate_address(bad, SupportedCoin.BITCOIN)
    assert error is not None
    assert "checksum" in error.lower()


def test_bitcoin_garbage_is_rejected():
    error = validate_address("not-an-address-at-all", SupportedCoin.BITCOIN)
    assert error is not None


def test_bitcoin_doubled_paste_is_caught_with_a_specific_message():
    # Reproduces a real incident: a clipboard paste silently duplicated the address.
    original = "15oM8RLMuMXLTJg7t7faFnLmn9APhAZrSw"
    doubled = original + original
    error = validate_address(doubled, SupportedCoin.BITCOIN)
    assert error is not None
    assert "twice" in error.lower() or "duplicat" in error.lower()


def test_bip173_spec_example_address_passes_format_validation():
    # This is a real, well-formed bech32 address (used across bech32 test suites) even
    # though it isn't derived from any real seed — format validation should accept it;
    # only the recovery search itself can determine it doesn't match a given phrase.
    assert validate_address(BTC_BECH32_VALID, SupportedCoin.BITCOIN) is None


def test_ethereum_checksummed_address_passes():
    assert validate_address(ETH_CHECKSUMMED_VALID, SupportedCoin.ETHEREUM) is None


def test_ethereum_all_lowercase_address_passes_unchecksummed():
    assert validate_address(ETH_CHECKSUMMED_VALID.lower(), SupportedCoin.ETHEREUM) is None


def test_ethereum_all_uppercase_hex_passes_unchecksummed():
    upper = "0x" + ETH_CHECKSUMMED_VALID[2:].upper()
    assert validate_address(upper, SupportedCoin.ETHEREUM) is None


def test_ethereum_mixed_case_with_wrong_checksum_is_rejected():
    # Flip the case of every letter -- still mixed-case, but no longer a valid EIP-55
    # checksum, so this must be rejected rather than silently accepted.
    flipped = "0x" + "".join(
        c.lower() if c.isupper() else c.upper() for c in ETH_CHECKSUMMED_VALID[2:]
    )
    error = validate_address(flipped, SupportedCoin.ETHEREUM)
    assert error is not None
    assert "checksum" in error.lower()


def test_ethereum_missing_0x_prefix_is_rejected():
    error = validate_address(ETH_CHECKSUMMED_VALID[2:], SupportedCoin.ETHEREUM)
    assert error is not None


def test_ethereum_wrong_length_is_rejected():
    error = validate_address("0x1234", SupportedCoin.ETHEREUM)
    assert error is not None


def test_solana_valid_address_passes():
    assert validate_address("5n9FVdLYELJG8QydhDbbLPSWK86UcaiE6U4u4VMVhWBu", SupportedCoin.SOLANA) is None


def test_solana_garbage_is_rejected():
    error = validate_address("not-a-valid-address", SupportedCoin.SOLANA)
    assert error is not None


def test_solana_wrong_length_base58_is_rejected():
    # A real Bitcoin address decodes to the wrong byte length for a Solana (32-byte) key.
    error = validate_address(BTC_P2PKH_VALID, SupportedCoin.SOLANA)
    assert error is not None
