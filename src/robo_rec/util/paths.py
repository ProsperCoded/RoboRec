"""Single source of truth for resolving the repo root and the vendored btcrecover checkout."""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path


class BtcrecoverNotFoundError(FileNotFoundError):
    """Raised when the vendored btcrecover checkout can't be located."""


def is_compiled() -> bool:
    """Check whether the code is running from a frozen/compiled executable.

    PyInstaller exposes ``sys.frozen`` while Nuitka injects ``__compiled__``
    into compiled module globals. ``__compiled__`` is not a builtin module
    name, so checking ``sys.builtin_module_names`` misclassified Nuitka's
    one-file extraction directory as a normal source checkout.
    """
    return bool(getattr(sys, "frozen", False) or globals().get("__compiled__"))


@lru_cache(maxsize=1)
def repo_root() -> Path:
    """Resolve the project root by walking up from this file until pyproject.toml is found.

    In compiled mode, returns the directory where robo_rec package resides.
    """
    if is_compiled():
        # In Nuitka onefile mode, __file__ points to a temp extracted location
        # We need to find where the robo_rec package is within the onefile structure
        here = Path(__file__).resolve()
        # Walk up from util/paths.py -> util -> robo_rec and that's the package root
        # The onefile extracts to a temp dir, so repo_root is essentially the temp base
        for candidate in (here, *here.parents):
            if (candidate / "vendor").is_dir() and (candidate / "vendor" / "btcrecover").is_dir():
                return candidate
            # Fallback: return parent of robo_rec package
            if candidate.name == "robo_rec" and (candidate.parent / "vendor").is_dir():
                return candidate.parent
        # If all else fails, return the executable directory
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

