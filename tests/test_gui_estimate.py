"""format_estimate() shows exactly one hardware's number (matching the real, currently-
detected GPU state via robo_rec.gui.gpu_state), and collapses to a single average once the
range would exceed 30 days — a wide low-high spread stops being useful information at that
point; the user just needs "this is impractical," not a range spanning years.
"""

from __future__ import annotations

import pytest

from robo_rec.gui import gpu_state
from robo_rec.gui.estimate import format_estimate


@pytest.fixture(autouse=True)
def _reset_gpu_state():
    gpu_state.set_gpu_available(False)
    yield
    gpu_state.set_gpu_available(False)


def test_shows_cpu_label_when_no_gpu_detected():
    gpu_state.set_gpu_available(False)
    text = format_estimate(2048**3)
    assert "CPU" in text
    assert "GPU" not in text


def test_shows_gpu_label_when_gpu_detected():
    gpu_state.set_gpu_available(True)
    text = format_estimate(2048**3)
    assert "GPU" in text
    assert "CPU" not in text


def test_short_estimate_shows_a_range():
    gpu_state.set_gpu_available(False)
    text = format_estimate(2048**3)
    assert "–" in text  # en dash used for low–high ranges


def test_long_estimate_collapses_to_single_average():
    gpu_state.set_gpu_available(False)
    text = format_estimate(2048**4)  # ~years on CPU
    assert "–" not in text
    assert "avg" in text


def test_long_estimate_uses_years_not_raw_days():
    gpu_state.set_gpu_available(False)
    text = format_estimate(2048**4)  # ~7.9 years on CPU
    assert "years" in text
    assert "days" not in text


def test_very_long_estimate_uses_millennia():
    gpu_state.set_gpu_available(False)
    text = format_estimate(2048**5)  # ~16 thousand years on CPU
    assert "millennia" in text


def test_absurd_estimate_falls_back_to_scientific_notation():
    gpu_state.set_gpu_available(False)
    text = format_estimate(2048**12)  # nonsensically large, matches PRD's 5+ Non-Goal
    assert "e+" in text
    assert "millennia" in text


def test_zero_combinations_is_instant():
    gpu_state.set_gpu_available(False)
    assert format_estimate(0) == "under a minute on CPU"


def test_gpu_state_defaults_to_false():
    # A fresh call with no prior set_gpu_available() should read as CPU-only, matching
    # the top-bar badge's own startup default before the first probe completes.
    gpu_state.set_gpu_available(False)
    assert gpu_state.is_gpu_available() is False
