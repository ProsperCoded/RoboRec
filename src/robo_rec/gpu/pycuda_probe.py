"""In-process check for whether pycuda is importable (PRD 4.5's PyCUDA accessibility ask).

Uses find_spec rather than a real import so this never has side effects (pycuda's actual
import can attempt to initialize a CUDA context) — accessibility here means "is it installed
and importable," not "does a CUDA device actually initialize."
"""

from __future__ import annotations

import importlib.util


def probe_pycuda_importable() -> bool:
    try:
        return importlib.util.find_spec("pycuda") is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False
