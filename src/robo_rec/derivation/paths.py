"""Supported coins and their derivation path/coin registry (PRD 4.4, 8).

BIP49 (P2SH-wrapped Segwit) and BIP84 (native Segwit) are Bitcoin-family standards only —
Ethereum and similar account-based chains only use BIP44. path_types_for_coin() reflects
this so callers never build a meaningless "BIP84 Ethereum" request.

Solana gets its own "solana" path type, derived via py_crypto_hd_wallet in address.py rather
than bip_utils — see that module's docstring for why: it deliberately matches the exact path
(m/44'/501'/account'/change'/index, the full BIP44 shape) that vendor/btcrecover's own
WalletSolana._verify_seed() uses, so recovery (btcrecover-backed) and derivation (this
module) agree on the same address for the same phrase.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from bip_utils import Bip44Coins, Bip49Coins, Bip84Coins

PathType = Literal["bip44", "bip49", "bip84", "solana"]


class SupportedCoin(Enum):
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"
    SOLANA = "solana"


@dataclass(frozen=True)
class _CoinConfig:
    slip44_coin_type: int
    bip44: object | None
    bip49: object | None
    bip84: object | None
    solana_supported: bool = False


_COIN_CONFIG: dict[SupportedCoin, _CoinConfig] = {
    SupportedCoin.BITCOIN: _CoinConfig(
        slip44_coin_type=0,
        bip44=Bip44Coins.BITCOIN,
        bip49=Bip49Coins.BITCOIN,
        bip84=Bip84Coins.BITCOIN,
    ),
    SupportedCoin.ETHEREUM: _CoinConfig(
        slip44_coin_type=60,
        bip44=Bip44Coins.ETHEREUM,
        bip49=None,
        bip84=None,
    ),
    SupportedCoin.SOLANA: _CoinConfig(
        slip44_coin_type=501,
        bip44=None,
        bip49=None,
        bip84=None,
        solana_supported=True,
    ),
}

# (path_type, purpose) — purpose is the BIP number itself, used as the hardened purpose index.
# Solana doesn't use this (its path is built directly in address.py via py_crypto_hd_wallet).
_PURPOSE_BY_PATH_TYPE: dict[PathType, int] = {"bip44": 44, "bip49": 49, "bip84": 84}

# Common wallet-software labels per (coin, path_type), for PRD 4.4's "reports which
# path/wallet type it corresponds to" requirement.
_WALLET_LABELS: dict[tuple[SupportedCoin, PathType], str] = {
    (SupportedCoin.BITCOIN, "bip44"): "Legacy (P2PKH) — most older wallets",
    (SupportedCoin.BITCOIN, "bip49"): "SegWit-compatible (P2SH-P2WPKH) — many hardware wallets",
    (SupportedCoin.BITCOIN, "bip84"): "Native SegWit (Bech32) — modern default (Electrum, Trezor, Ledger)",
    (SupportedCoin.ETHEREUM, "bip44"): "Standard Ethereum path — MetaMask, Trust Wallet, Ledger, Trezor",
    (SupportedCoin.SOLANA, "solana"): "Standard Solana path — Phantom, Solflare, most Solana wallets",
}


def coin_config(coin: SupportedCoin) -> _CoinConfig:
    return _COIN_CONFIG[coin]


def path_types_for_coin(coin: SupportedCoin) -> tuple[PathType, ...]:
    config = coin_config(coin)
    types: list[PathType] = [
        pt for pt in ("bip44", "bip49", "bip84") if getattr(config, pt) is not None
    ]
    if config.solana_supported:
        types.append("solana")
    return tuple(types)


def wallet_label(coin: SupportedCoin, path_type: PathType) -> str:
    return _WALLET_LABELS.get((coin, path_type), f"{path_type.upper()} standard path")


def derivation_path_str(
    coin: SupportedCoin, path_type: PathType, *, account: int, change: int, address_index: int
) -> str:
    coin_type = coin_config(coin).slip44_coin_type
    if path_type == "solana":
        # ed25519 (SLIP-0010) requires every level hardened — matches py_crypto_hd_wallet's
        # (and btcrecover's WalletSolana's) actual derivation, confirmed by direct address
        # comparison in this session (see address.py's module docstring).
        return f"m/44'/{coin_type}'/{account}'/{change}'/{address_index}'"
    purpose = _PURPOSE_BY_PATH_TYPE[path_type]
    return f"m/{purpose}'/{coin_type}'/{account}'/{change}/{address_index}"
