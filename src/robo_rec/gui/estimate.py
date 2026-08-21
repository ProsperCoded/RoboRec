"""Shared time-estimate math for recovery panels.

Shows a single estimate for whichever hardware is actually available (GPU if detected,
CPU otherwise — robo_rec.gui.gpu_state reflects the real probe result) rather than always
listing both, since a user without a GPU has no use for a GPU-speed number and vice versa.

Rates are illustrative order-of-magnitude ballparks, not a measured benchmark — real timing
depends on the user's specific hardware. btcrecover's real work per candidate (BIP39
seed-to-address derivation, i.e. secp256k1 EC math) is far slower than raw hashing, which is
why CPU and GPU rates differ by orders of magnitude here.

The low end of the range assumes an "expected case": the correct phrase is found partway
through the search, not necessarily on the very last candidate, so it's modeled as half of
an exhaustive search at the faster end of the hardware range. The high end is the worst
case: an exhaustive search at the slower end of the range. Past 30 days the low/high spread
stops being useful information (the user just needs to know "this is impractical"), so it
collapses into a single average instead of a widening range.
"""

from __future__ import annotations

from robo_rec.gui.gpu_state import is_gpu_available

# candidates/second, low-end to high-end hardware
CPU_RATE_LOW = 40_000
CPU_RATE_HIGH = 150_000
GPU_RATE_LOW = 800_000
GPU_RATE_HIGH = 5_000_000

_COLLAPSE_TO_AVERAGE_AFTER_DAYS = 30

# (unit label, days per unit) — checked largest-first so a huge estimate lands on
# "centuries"/"millennia" instead of an unreadable multi-digit day count (PRD 4.2's own
# 4-missing-known-position case alone can run into the thousands of days).
_DAY_UNITS: tuple[tuple[str, float], ...] = (
    ("millennia", 365.25 * 1000),
    ("centuries", 365.25 * 100),
    ("decades", 365.25 * 10),
    ("years", 365.25),
    ("months", 30.44),
)


def estimate_minutes_range(combinations: float, *, use_gpu: bool) -> tuple[float, float]:
    """Returns (low, high) minutes for this many combinations on the given hardware."""
    if combinations <= 0:
        return (0.0, 0.0)
    rate_low, rate_high = (GPU_RATE_LOW, GPU_RATE_HIGH) if use_gpu else (CPU_RATE_LOW, CPU_RATE_HIGH)
    low = combinations / rate_high / 60 / 2
    high = combinations / rate_low / 60
    return (max(low, 0.05), max(high, 0.05))


def _format_days(days: float) -> str:
    """Picks the largest whole unit (months/years/decades/centuries/millennia) that keeps
    the displayed number readable, falling back to plain days for anything under a month.
    Beyond ~1 million millennia even that unit produces an unreadable number (e.g. PRD 4.2's
    explicitly-unsupported 5+ missing-word cases), so it switches to scientific notation."""
    millennia = days / (365.25 * 1000)
    if millennia >= 1_000_000:
        return f"{millennia:.1e} millennia"
    for label, days_per_unit in _DAY_UNITS:
        if days >= days_per_unit:
            return f"{days / days_per_unit:.1f} {label}"
    return f"{days:.1f} days"


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
    if high_days > _COLLAPSE_TO_AVERAGE_AFTER_DAYS:
        return f"~{_format_days((low_days + high_days) / 2)} (avg)"
    return f"{low_days:.1f}–{high_days:.1f} days"


def format_estimate(combinations: float) -> str:
    """A single estimate for whichever hardware is actually available right now."""
    use_gpu = is_gpu_available()
    low, high = estimate_minutes_range(combinations, use_gpu=use_gpu)
    hardware_label = "with a GPU" if use_gpu else "on CPU"
    return f"{_format_span(low, high)} {hardware_label}"
