"""Shared time-estimate math for recovery panels.

Shows a CPU-GPU range rather than a single number, since actual throughput
varies a lot by hardware and btcrecover's real work per candidate (BIP39
seed-to-address derivation, i.e. secp256k1 EC math) is far slower than raw
hashing — so a single flat rate either massively overstates (if calibrated to
GPU speed) or understates (if calibrated to CPU speed) the likely duration.

Rates are illustrative order-of-magnitude ballparks, not a measured
benchmark — real timing depends on the user's specific hardware.

The low end of each range assumes an "expected case": the correct phrase is
found partway through the search, not necessarily on the very last
candidate, so it's modeled as half of an exhaustive search at the faster end
of the hardware range. The high end is the worst case: an exhaustive search
at the slower end of the hardware range. This keeps the range honest (it's
still a real search, not a guarantee) while not defaulting to the
pessimistic worst-case-only framing for the number a user sees first.
"""

from __future__ import annotations

# candidates/second, low-end to high-end hardware
CPU_RATE_LOW = 40_000
CPU_RATE_HIGH = 150_000
GPU_RATE_LOW = 800_000
GPU_RATE_HIGH = 5_000_000


def estimate_minutes_range(combinations: float) -> tuple[float, float, float, float]:
    """Returns (cpu_low, cpu_high, gpu_low, gpu_high) minutes for this many combinations."""
    if combinations <= 0:
        return (0.0, 0.0, 0.0, 0.0)
    cpu_low = combinations / CPU_RATE_HIGH / 60 / 2
    cpu_high = combinations / CPU_RATE_LOW / 60
    gpu_low = combinations / GPU_RATE_HIGH / 60 / 2
    gpu_high = combinations / GPU_RATE_LOW / 60
    return (
        max(cpu_low, 0.05),
        max(cpu_high, 0.05),
        max(gpu_low, 0.05),
        max(gpu_high, 0.05),
    )


def _format_span(low: float, high: float) -> str:
    if high < 1:
        return "under a minute"
    if high < 60:
        return f"{low:.0f}–{high:.0f} min" if low >= 1 else f"under {high:.0f} min"
    low_hours, high_hours = low / 60, high / 60
    # Pick the unit from the low bound so a range like "8-60 hrs" doesn't get
    # dragged into days just because the pessimistic end crossed 48 hrs.
    if low_hours < 48:
        return f"{low_hours:.1f}–{high_hours:.1f} hrs"
    low_days, high_days = low_hours / 24, high_hours / 24
    return f"{low_days:.1f}–{high_days:.1f} days"


def format_estimate_range(combinations: float) -> str:
    cpu_low, cpu_high, gpu_low, gpu_high = estimate_minutes_range(combinations)
    cpu_text = _format_span(cpu_low, cpu_high)
    gpu_text = _format_span(gpu_low, gpu_high)
    return f"{cpu_text} on CPU · {gpu_text} with a GPU"
