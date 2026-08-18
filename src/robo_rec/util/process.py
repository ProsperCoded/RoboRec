"""Shared subprocess helpers: line-buffered streaming from a child process's stdout."""

from __future__ import annotations

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
    process = subprocess.Popen(
        argv,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
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
