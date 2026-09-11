"""Client-side address format/checksum validation, run before a search starts.

Not part of the original PRD — added after two separate incidents (one duplicated-paste
address, one copy-pasted spec example address) where a malformed test address let a
multi-minute-to-multi-hour recovery search run to completion and report a misleading,
generic "No matching phrase found," instead of catching the obvious mistake immediately.

This is a *format and checksum* check only — it proves an address is well-formed for the
selected coin (right prefix, right length, right checksum where the format has one), never
that it's a real, funded, or actually-associated-with-this-wallet address. A search can still
legitimately fail even after this passes; this only rules out the "it was never going to
match because it's not a valid address at all" class of mistake.
"""

from __future__ import annotations

import re

from bip_utils import (
    CoinsConf,
    EthAddrDecoder,
    P2PKHAddrDecoder,
    P2SHAddrDecoder,
    P2TRAddrDecoder,
    P2WPKHAddrDecoder,
    SolAddrDecoder,
)

from robo_rec.derivation.paths import SupportedCoin

_ETH_ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

_DOUBLED_PASTE_MESSAGE = (
    "This looks like the address got pasted in twice by accident — it's the same text "
    "repeated back-to-back with nothing in between. Try copying and pasting it again."
)


def _looks_doubled(address: str) -> bool:
    """Catches the exact failure mode seen twice in practice: a clipboard paste that
    silently duplicated the whole string with no separator. Only flags even-length strings
    of reasonable size to avoid false positives on short, legitimately repetitive input."""
    if len(address) < 16 or len(address) % 2 != 0:
        return False
    half = len(address) // 2
    return address[:half] == address[half:]


def _validate_bitcoin(address: str) -> str | None:
    btc = CoinsConf.BitcoinMainNet
    decoders = (
        (P2PKHAddrDecoder, {"net_ver": btc.ParamByKey("p2pkh_net_ver")}),
        (P2SHAddrDecoder, {"net_ver": btc.ParamByKey("p2sh_net_ver")}),
        (P2WPKHAddrDecoder, {"hrp": btc.ParamByKey("p2wpkh_hrp")}),
        (P2TRAddrDecoder, {"hrp": btc.ParamByKey("p2tr_hrp")}),
    )
    for decoder, kwargs in decoders:
        try:
            decoder.DecodeAddr(address, **kwargs)
            return None
        except ValueError:
            continue

    if address.startswith(("bc1q",)):
        return (
            "This looks like a Bitcoin bech32 (native SegWit) address, but its checksum "
            "doesn't match — check for a typo or a copy/paste mistake."
        )
    if address.startswith("bc1p"):
        return (
            "This looks like a Bitcoin taproot address, but its checksum doesn't match — "
            "check for a typo or a copy/paste mistake."
        )
    if address.startswith(("1", "3")):
        return (
            "This looks like a Bitcoin address, but its checksum doesn't match — check for "
            "a typo or a copy/paste mistake."
        )
    return (
        "This doesn't look like a valid Bitcoin address — it should start with 1, 3, "
        "bc1q, or bc1p."
    )


def _validate_ethereum(address: str) -> str | None:
    if not _ETH_ADDR_RE.match(address):
        return (
            'This doesn\'t look like an Ethereum address — expected "0x" followed by 40 '
            "hex characters."
        )
    # EIP-55 checksum casing is optional: an all-lowercase or all-uppercase address is a
    # legitimate, common, unchecksummed form (many wallets/explorers display it that way).
    # Only a MIXED-case address is required to match the checksum exactly.
    hex_part = address[2:]
    if hex_part == hex_part.lower() or hex_part == hex_part.upper():
        return None
    try:
        EthAddrDecoder.DecodeAddr(address)
    except ValueError:
        return (
            "This Ethereum address has mixed upper/lowercase letters but doesn't match the "
            "expected checksum (EIP-55) — check for a typo, or double-check it was copied "
            "correctly."
        )
    return None


def _validate_solana(address: str) -> str | None:
    try:
        SolAddrDecoder.DecodeAddr(address)
        return None
    except ValueError:
        return (
            "This doesn't look like a valid Solana address — it should be a base58-encoded "
            "string that decodes to a 32-byte key. Check for a typo or a copy/paste mistake."
        )


_VALIDATORS = {
    SupportedCoin.BITCOIN: _validate_bitcoin,
    SupportedCoin.ETHEREUM: _validate_ethereum,
    SupportedCoin.SOLANA: _validate_solana,
}


def validate_address(address: str, coin: SupportedCoin) -> str | None:
    """Returns None if `address` is a well-formed, checksum-valid address for `coin`,
    otherwise a short, user-facing message explaining what looks wrong. Does not touch the
    network or claim the address is real/funded/associated with anything."""
    address = address.strip()
    if not address:
        return "Enter an address you know is associated with this wallet."
    if _looks_doubled(address):
        return _DOUBLED_PASTE_MESSAGE
    return _VALIDATORS[coin](address)


__all__ = ["validate_address"]
