"""Live proof-of-life check: generates a disposable BIP-39 mnemonic, derives its real
BTC/ETH/SOL addresses independently (bip_utils / py_crypto_hd_wallet via robo_rec.derivation,
not btcrecover's own code), then runs each one through the actual recovery engine
(BtcrecoverRunner) with two words blanked out, and confirms it recovers the correct phrase.

This is the same round-trip used to diagnose a real "no GPU acceleration" report where GPU
correctness/throughput both checked out fine on their own — the actual bug turned out to be
that Solana recovery was requesting GPU support the engine doesn't have for it (see
robo_rec.recovery.args._OPENCL_CAPABLE_WALLET_TYPES). A live self-test per coin, not just a
GPU probe, is what caught that; a diagnostics export that only re-ran the GPU probe would have
looked identical whether or not that bug was present.

Never uses a real wallet's mnemonic or address — everything here is generated fresh and
thrown away. Takes roughly 30-90s per coin (mostly the recovery subprocess's own startup and
candidate-checksum/derivation work, not the search itself, since the search space is tiny).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from bip_utils import Bip39MnemonicGenerator

from robo_rec.derivation import SupportedCoin, derive_addresses
from robo_rec.recovery.models import MissingWordKnownPositionSpec
from robo_rec.recovery.runner import BtcrecoverRunner

_NUM_WORDS = 24
_BLANK_POSITIONS = (22, 23)  # last two words, 0-indexed

# Mirrors robo_rec.gui.coin_options._WALLET_TYPE_BY_COIN. Duplicated rather than imported so
# this module (used from a background diagnostics worker) never pulls in the gui package.
_WALLET_TYPE_BY_COIN = {
    SupportedCoin.BITCOIN: "bip39",
    SupportedCoin.ETHEREUM: "ethereum",
    SupportedCoin.SOLANA: "solana",
}


@dataclass(frozen=True)
class SelfTestResult:
    coin: str
    passed: bool
    elapsed_seconds: float
    gpu_requested: bool
    gpu_actually_used: bool
    error: str | None
    # Sensitive — only ever populated when the caller wants an unredacted report.
    mnemonic: str | None = None
    address: str | None = None
    recovered_mnemonic: str | None = None


def _address_for(coin: SupportedCoin, mnemonic: str) -> str:
    if coin is SupportedCoin.BITCOIN:
        # bip84 (bech32, native SegWit) — the modern default wallets use.
        addr = next(iter(derive_addresses(mnemonic, coin=coin, path_types=("bip84",))))
    else:
        addr = next(iter(derive_addresses(mnemonic, coin=coin)))
    return addr.address


def run_one_self_test(coin: SupportedCoin, *, use_gpu: bool, keep_sensitive: bool) -> SelfTestResult:
    mnemonic = str(Bip39MnemonicGenerator().FromWordsNumber(_NUM_WORDS))
    words = mnemonic.split()
    address = _address_for(coin, mnemonic)

    spec_words: list[str | None] = list(words)
    for pos in _BLANK_POSITIONS:
        spec_words[pos] = None

    spec = MissingWordKnownPositionSpec(
        words=spec_words, wallet_type=_WALLET_TYPE_BY_COIN[coin], addrs=[address]
    )
    runner = BtcrecoverRunner(spec, use_gpu=use_gpu)

    t0 = time.time()
    result = None
    error: str | None = None
    try:
        for event in runner.run_iter():
            if event.kind == "finished":
                result = event.result
    except Exception as exc:  # noqa: BLE001 - a self-test failure is a *result*, not a crash
        error = f"{type(exc).__name__}: {exc}"
    elapsed = time.time() - t0

    recovered = result.mnemonic if result else None
    passed = error is None and result is not None and recovered == " ".join(words)
    argv_had_gpu_flag = use_gpu and _WALLET_TYPE_BY_COIN[coin] in {"bip39", "ethereum"}

    return SelfTestResult(
        coin=coin.value,
        passed=passed,
        elapsed_seconds=elapsed,
        gpu_requested=use_gpu,
        gpu_actually_used=argv_had_gpu_flag,
        error=error,
        mnemonic=mnemonic if keep_sensitive else None,
        address=address if keep_sensitive else None,
        recovered_mnemonic=recovered if keep_sensitive else None,
    )


def run_self_test(*, use_gpu: bool, keep_sensitive: bool) -> list[SelfTestResult]:
    """Runs the BTC/ETH/SOL round-trip in sequence (not parallel — recovery subprocesses are
    already multi-threaded/GPU-bound, running three at once would just make each slower and
    muddy the timing numbers)."""
    return [
        run_one_self_test(coin, use_gpu=use_gpu, keep_sensitive=keep_sensitive)
        for coin in (SupportedCoin.BITCOIN, SupportedCoin.ETHEREUM, SupportedCoin.SOLANA)
    ]


__all__ = ["SelfTestResult", "run_self_test"]
