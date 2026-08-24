"""Single source of truth for resolving the repo root and the vendored btcrecover checkout."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


class BtcrecoverNotFoundError(FileNotFoundError):
    """Raised when the vendored btcrecover checkout can't be located."""


import os
import sys

def is_compiled() -> bool:
    """Check if the code is running under a compiled Nuitka binary."""
    return hasattr(sys, "frozen") or "__compiled__" in sys.builtin_module_names


@lru_cache(maxsize=1)
def repo_root() -> Path:
    """Resolve the project root by walking up from this file until pyproject.toml is found.

    In compiled mode, returns the directory containing the executable.
    """
    if is_compiled():
        return Path(sys.executable).parent

    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise FileNotFoundError(
        "Could not locate repo root (no pyproject.toml found above "
        f"{here})"
    )


def btcrecover_root() -> Path:
    """Path to vendor/btcrecover, the directory seedrecover.py must be run from."""
    candidate = repo_root() / "vendor" / "btcrecover"
    if not is_compiled() and not (candidate / "seedrecover.py").is_file():
        raise BtcrecoverNotFoundError(
            f"vendor/btcrecover checkout not found or incomplete at {candidate}. "
            "Run `git submodule update --init --recursive`."
        )
    return candidate


def seedrecover_script() -> Path:
    return btcrecover_root() / "seedrecover.py"


def seedrecover_command() -> list[str]:
    """Get the command prefix to execute seedrecover.

    In dev mode, this returns [sys.executable, 'path/to/seedrecover.py'].
    In compiled mode, it returns ['path/to/seedrecover.exe'].
    """
    if is_compiled():
        binary_name = "seedrecover.exe" if os.name == "nt" else "seedrecover"
        return [str(repo_root() / binary_name)]
    return [sys.executable, str(seedrecover_script())]

