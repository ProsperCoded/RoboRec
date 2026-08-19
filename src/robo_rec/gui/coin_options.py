"""Maps the GUI's token/coin combo-box labels to derivation.SupportedCoin and to the
--wallet-type string seedrecover.py expects. Single source of truth so every panel's
combo box stays consistent with what the engine actually supports.
"""

from __future__ import annotations

from dataclasses import dataclass

from robo_rec.derivation import SupportedCoin

# seedrecover.py --wallet-type values, confirmed against vendor/btcrecover/btcrecover/btcrseed.py
# register_selectable_wallet_class(...) decorators (case-insensitive per btcrecover's own
# argument handling — see line ~4892's `args.wallet_type.lower() == "ethereum"` check).
_WALLET_TYPE_BY_COIN = {
    SupportedCoin.BITCOIN: "bip39",
    SupportedCoin.ETHEREUM: "ethereum",
    SupportedCoin.SOLANA: "solana",
}


@dataclass(frozen=True)
class CoinOption:
    label: str
    coin: SupportedCoin | None  # None marks a not-yet-supported placeholder option
    address_prefixes: tuple[str, ...] = ()


COIN_OPTIONS: tuple[CoinOption, ...] = (
    CoinOption("Bitcoin (BTC)", SupportedCoin.BITCOIN, ("1", "3", "bc1")),
    CoinOption("Ethereum (ETH)", SupportedCoin.ETHEREUM, ("0x",)),
    CoinOption("Solana (SOL)", SupportedCoin.SOLANA, ()),
    CoinOption("Other BIP39-compatible", None, ()),
)

COIN_OPTION_LABELS: tuple[str, ...] = tuple(option.label for option in COIN_OPTIONS)

UNSUPPORTED_COIN_MESSAGE = (
    "This token isn't supported yet — Robo-Rec currently supports Bitcoin, Ethereum, "
    "and Solana. Pick one of those to continue."
)


def coin_for_label(label: str) -> SupportedCoin | None:
    for option in COIN_OPTIONS:
        if option.label == label:
            return option.coin
    return None


def wallet_type_for_coin(coin: SupportedCoin) -> str:
    return _WALLET_TYPE_BY_COIN[coin]


def detect_coin_label(address: str) -> str | None:
    address = address.strip()
    for option in COIN_OPTIONS:
        for prefix in option.address_prefixes:
            if address.startswith(prefix):
                return option.label
    return None
