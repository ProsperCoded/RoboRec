"""Standalone address derivation and verification (PRD 4.4).

Pure, offline, synchronous, sub-second — uses bip_utils directly rather than btcrecover's own
WalletBIP32/WalletBIP39 classes, which are architected around the search/checksum-matching
loop and require a live search target or GUI/exit() fallback (confirmed by reading
vendor/btcrecover/btcrecover/btcrseed.py — no clean standalone "just derive" API exists
there). Safe to call directly on the Qt main thread; no subprocess involved.

Solana is the one exception: it uses py_crypto_hd_wallet (already a project dependency)
instead of bip_utils, deliberately matching the exact library and derivation path that
vendor/btcrecover/btcrecover/btcrseed.py's WalletSolana._verify_seed() uses internally
(py_crypto_hd_wallet.HdWalletBip44Coins.SOLANA, full m/44'/501'/account'/change'/0' path).
bip_utils' own Bip44Coins.SOLANA follows a shallower default path (m/44'/501'/account', no
change/index levels) that produces a DIFFERENT address for the same mnemonic — confirmed by
direct comparison in this session. Using bip_utils for Solana would silently disagree with
what btcrecover's own recovery search verifies against, breaking round-trip consistency
between the Missing Words/Rearrange panels (btcrecover-backed) and the Derive Wallet panel.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import py_crypto_hd_wallet as hd_wallet
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Changes, Bip49, Bip84

from robo_rec.derivation.paths import (
    PathType,
    SupportedCoin,
    coin_config,
    derivation_path_str,
    path_types_for_coin,
    wallet_label,
)

_CONTEXT_CLASS_BY_PATH_TYPE = {"bip44": Bip44, "bip49": Bip49, "bip84": Bip84}


@dataclass(frozen=True)
class DerivedAddress:
    coin: str
    path_type: PathType
    derivation_path: str
    address: str
    wallet_software_label: str


def _derive_solana(
    mnemonic: str, passphrase: str, *, account: int, address_index: int
) -> DerivedAddress:
    wallet = hd_wallet.HdWalletBipFactory(hd_wallet.HdWalletBip44Coins.SOLANA).CreateFromMnemonic(
        "solana", mnemonic=mnemonic, passphrase=passphrase
    )
    wallet.Generate(
        addr_num=1,
        addr_off=address_index,
        acc_idx=account,
        change_idx=hd_wallet.HdWalletBipChanges.CHAIN_EXT,
    )
    address = wallet.ToDict()["change_key"]["address"]
    return DerivedAddress(
        coin=SupportedCoin.SOLANA.value,
        path_type="solana",
        derivation_path=derivation_path_str(
            SupportedCoin.SOLANA, "solana", account=account, change=0, address_index=address_index
        ),
        address=address,
        wallet_software_label=wallet_label(SupportedCoin.SOLANA, "solana"),
    )


def _derive_bip_utils(
    seed_bytes: bytes,
    coin: SupportedCoin,
    path_type: PathType,
    *,
    account: int,
    address_index: int,
) -> DerivedAddress:
    config = coin_config(coin)
    coin_enum = getattr(config, path_type)
    context_cls = _CONTEXT_CLASS_BY_PATH_TYPE[path_type]
    ctx = (
        context_cls.FromSeed(seed_bytes, coin_enum)
        .Purpose()
        .Coin()
        .Account(account)
        .Change(Bip44Changes.CHAIN_EXT)
        .AddressIndex(address_index)
    )
    return DerivedAddress(
        coin=coin.value,
        path_type=path_type,
        derivation_path=derivation_path_str(
            coin, path_type, account=account, change=0, address_index=address_index
        ),
        address=ctx.PublicKey().ToAddress(),
        wallet_software_label=wallet_label(coin, path_type),
    )


def _derive_one(
    mnemonic: str,
    seed_bytes: bytes,
    passphrase: str,
    coin: SupportedCoin,
    path_type: PathType,
    *,
    account: int,
    address_index: int,
) -> DerivedAddress:
    if path_type == "solana":
        return _derive_solana(mnemonic, passphrase, account=account, address_index=address_index)
    return _derive_bip_utils(
        seed_bytes, coin, path_type, account=account, address_index=address_index
    )


def derive_addresses(
    mnemonic: str,
    *,
    coin: SupportedCoin,
    passphrase: str = "",
    account: int = 0,
    address_index: int = 0,
    path_types: Sequence[PathType] | None = None,
) -> list[DerivedAddress]:
    """Powers PRD 4.4's 'without target address' path: derives and returns the standard
    first address(es) for the recovered phrase across the requested path types (default:
    every path type valid for this coin)."""
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate(passphrase)
    types = path_types if path_types is not None else path_types_for_coin(coin)
    return [
        _derive_one(
            mnemonic, seed_bytes, passphrase, coin, pt, account=account, address_index=address_index
        )
        for pt in types
    ]


def verify_address(
    mnemonic: str,
    target_address: str,
    *,
    coin: SupportedCoin,
    passphrase: str = "",
    search_accounts: int = 1,
    search_indices: int = 5,
) -> DerivedAddress | None:
    """Powers PRD 4.4's 'with target address' path: iterates path types x a small
    account/index range and returns the first DerivedAddress match (with path/wallet-label),
    or None if no match is found in the searched range."""
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate(passphrase)
    target_lower = target_address.strip().lower()
    for path_type in path_types_for_coin(coin):
        for account in range(search_accounts):
            for address_index in range(search_indices):
                candidate = _derive_one(
                    mnemonic,
                    seed_bytes,
                    passphrase,
                    coin,
                    path_type,
                    account=account,
                    address_index=address_index,
                )
                if candidate.address.lower() == target_lower:
                    return candidate
    return None
