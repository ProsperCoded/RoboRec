"""Shared subprocess helpers: line-buffered streaming from a child process's stdout."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from collections.abc import Iterator
from pathlib import Path


def stream_lines(
    argv: list[str],
    *,
    cwd: Path,
    stop_event: threading.Event | None = None,
) -> tuple[subprocess.Popen, Iterator[str]]:
    """Launch argv with cwd, returning the Popen handle and an iterator over stdout lines.

    stderr is merged into stdout so callers see everything in arrival order (btcrecover
    interleaves informational prints on both streams). The iterator stops when the process
    exits or stop_event is set (caller is responsible for then terminating the process).
    """
    # On Windows, a console-subsystem child (seedrecover.exe, or the dev-mode
    # python.exe) can still briefly flash a console window even with stdout/stderr
    # piped, unless the new process is explicitly told not to allocate one.
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    # Python block-buffers stdout (~8KB) whenever it isn't a tty, and a pipe isn't one.
    # bufsize=1 below only makes *this* process read line-by-line — it has no effect on how
    # the child writes. Without this the child holds every phase/ETA line until it exits or
    # fills the buffer, so a search that runs for hours delivers its entire log in one burst
    # at the end and the GUI's progress panel sits blank throughout (verified: a 13-second
    # run emitted all 30 lines simultaneously on exit).
    env = os.environ | {"PYTHONUNBUFFERED": "1"}

    process = subprocess.Popen(
        argv,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        creationflags=creationflags,
        env=env,
    )

    def _lines() -> Iterator[str]:
        assert process.stdout is not None
        try:
            for line in process.stdout:
                if stop_event is not None and stop_event.is_set():
                    break
                yield line.rstrip("\n")
        finally:
            process.stdout.close()

    return process, _lines()


def python_executable() -> str:
    """The interpreter to invoke child scripts with — same one running this process."""
    return sys.executable
