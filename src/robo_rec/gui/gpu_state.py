"""Process-wide cache of the last known GPU-acceleration availability.

MainWindow updates this whenever a GPU probe completes (startup probe or a re-check from
the GPU Status panel); recovery panels read it synchronously to decide which single
time estimate to show (PRD 4.5 — recovery uses GPU when available, CPU otherwise), instead
of every panel needing its own reference back to MainWindow or running its own probe.

Defaults to False (CPU-only) until the first probe completes, matching the top-bar badge's
own startup default.
"""

from __future__ import annotations

_gpu_available: bool = False


def set_gpu_available(available: bool) -> None:
    global _gpu_available
    _gpu_available = available


def is_gpu_available() -> bool:
    return _gpu_available
