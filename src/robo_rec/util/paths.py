"""Single source of truth for resolving the repo root and the vendored btcrecover checkout."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


class BtcrecoverNotFoundError(FileNotFoundError):
    """Raised when the vendored btcrecover checkout can't be located."""


@lru_cache(maxsize=1)
def repo_root() -> Path:
    """Resolve the project root by walking up from this file until pyproject.toml is found.

    Works under `uv run` dev mode. A frozen Nuitka build resolves assets differently (see
    robo-rec-implementation.md Section 1.1 and the PRD 6.4 packaging notes); when packaging
    is implemented, this function is the one place that needs a Nuitka-aware branch.
    """
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
    if not (candidate / "seedrecover.py").is_file():
        raise BtcrecoverNotFoundError(
            f"vendor/btcrecover checkout not found or incomplete at {candidate}. "
            "Run `git submodule update --init --recursive`."
        )
    return candidate


def seedrecover_script() -> Path:
    return btcrecover_root() / "seedrecover.py"
