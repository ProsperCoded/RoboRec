from robo_rec.derivation import SupportedCoin, derive_addresses, verify_address

MNEMONIC = "rotate dream drip opinion key dove region mind visit diesel negative speed"
BTC_ADDRESS = "1FMHvVtJkJFnSxaN9KUn5q3KtqNwej1sZ6"  # verified against real seedrecover.py runs


def test_derive_addresses_btc_matches_known_good_pair():
    addresses = derive_addresses(MNEMONIC, coin=SupportedCoin.BITCOIN)
    bip44 = next(a for a in addresses if a.path_type == "bip44")
    assert bip44.address == BTC_ADDRESS
    assert bip44.derivation_path == "m/44'/0'/0'/0/0"


def test_derive_addresses_returns_all_three_path_types_for_bitcoin():
    addresses = derive_addresses(MNEMONIC, coin=SupportedCoin.BITCOIN)
    path_types = {a.path_type for a in addresses}
    assert path_types == {"bip44", "bip49", "bip84"}


def test_derive_addresses_ethereum_only_has_bip44():
    addresses = derive_addresses(MNEMONIC, coin=SupportedCoin.ETHEREUM)
    path_types = {a.path_type for a in addresses}
    assert path_types == {"bip44"}


def test_verify_address_finds_known_match():
    match = verify_address(MNEMONIC, BTC_ADDRESS, coin=SupportedCoin.BITCOIN)
    assert match is not None
    assert match.address == BTC_ADDRESS
    assert match.path_type == "bip44"


def test_verify_address_returns_none_for_wrong_address():
    match = verify_address(MNEMONIC, "1FMHvVtJkJFnSxaN9KUn5q3KtqNwej1sZX", coin=SupportedCoin.BITCOIN)
    assert match is None


def test_verify_address_is_case_insensitive_for_eth():
    addresses = derive_addresses(MNEMONIC, coin=SupportedCoin.ETHEREUM)
    eth_address = addresses[0].address
    match = verify_address(MNEMONIC, eth_address.upper(), coin=SupportedCoin.ETHEREUM)
    assert match is not None


def test_derive_addresses_solana_matches_btcrecover_verification_path():
    # Matches py_crypto_hd_wallet's HdWalletBip44Coins.SOLANA output, which is the exact
    # library/path vendor/btcrecover's WalletSolana._verify_seed() uses internally — this
    # is deliberately NOT bip_utils' own shallower DeriveDefaultPath() output (a different,
    # incompatible address), confirmed by direct comparison in this session.
    addresses = derive_addresses(MNEMONIC, coin=SupportedCoin.SOLANA)
    assert len(addresses) == 1
    solana = addresses[0]
    assert solana.path_type == "solana"
    assert solana.derivation_path == "m/44'/501'/0'/0'/0'"
    assert solana.address == "D1V72D3pMJRVW5w7G6TTdST6ZtnE2e8gaMeihQU7zoW1"


def test_verify_address_finds_solana_match():
    addresses = derive_addresses(MNEMONIC, coin=SupportedCoin.SOLANA)
    match = verify_address(MNEMONIC, addresses[0].address, coin=SupportedCoin.SOLANA)
    assert match is not None
    assert match.path_type == "solana"
