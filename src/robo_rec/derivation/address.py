"""Standalone BIP44/49/84 address derivation and verification (PRD 4.4).

Pure, offline, synchronous, sub-second — uses bip_utils directly rather than btcrecover's own
WalletBIP32/WalletBIP39 classes, which are architected around the search/checksum-matching
loop and require a live search target or GUI/exit() fallback (confirmed by reading
vendor/btcrecover/btcrecover/btcrseed.py — no clean standalone "just derive" API exists
there). Safe to call directly on the Qt main thread; no subprocess involved.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

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


def _derive_one(
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
        _derive_one(seed_bytes, coin, pt, account=account, address_index=address_index)
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
                    seed_bytes, coin, path_type, account=account, address_index=address_index
                )
                if candidate.address.lower() == target_lower:
                    return candidate
    return None
