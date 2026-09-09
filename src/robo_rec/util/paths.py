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


def app_executable() -> str:
    """Absolute path to the program currently running.

    ``sys.executable`` is the obvious choice, and it is wrong in exactly the case
    that matters: Nuitka's ``--standalone`` mode makes the dist folder look like a
    Python installation (``sys.prefix`` points at it) and reports
    ``<dist>/python.exe`` as the executable — a file standalone builds never ship.
    Handing that path to ``subprocess`` fails with "[WinError 2] The system cannot
    find the file specified", which is why re-launching the app to run the OpenCL
    probe helper worked from source (where ``sys.executable`` really is the
    interpreter) but silently reported "no GPU" in every compiled build.
    """
    if not is_compiled():
        return sys.executable

    candidates: list[str] = []

    if sys.platform == "win32":
        # Authoritative: reports the running image's real path no matter how the
        # process was started, where argv[0] can be a bare name (launched via
        # PATH) or resolve against a working directory the app has since changed.
        import ctypes

        buffer = ctypes.create_unicode_buffer(32768)
        if ctypes.windll.kernel32.GetModuleFileNameW(None, buffer, len(buffer)):
            candidates.append(buffer.value)

    # Nuitka stashes the launch path here before anything can mutate sys.argv.
    original_argv0 = getattr(globals().get("__compiled__"), "original_argv0", None)
    if original_argv0:
        candidates.append(original_argv0)
    if sys.argv and sys.argv[0]:
        candidates.append(sys.argv[0])

    for candidate in candidates:
        resolved = Path(candidate).resolve()
        if resolved.is_file():
            return str(resolved)

    return sys.executable


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
        # If all else fails, return the executable directory. Note app_executable()
        # rather than sys.executable: under --standalone the latter names a
        # python.exe that isn't there (see app_executable's docstring).
        return Path(app_executable()).parent

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
    # -u so phase/ETA lines reach the GUI as they're printed rather than in one burst when
    # the process exits (see util.process.stream_lines); the compiled build relies on the
    # PYTHONUNBUFFERED it sets, since there's no interpreter flag to pass there.
    return [sys.executable, "-u", str(seedrecover_script())]

