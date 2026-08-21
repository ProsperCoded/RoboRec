"""BtcrecoverRunner: owns one seedrecover.py subprocess invocation, streams parsed
RecoveryEvent objects back to the caller, and supports thread-safe cancellation.

Qt-agnostic by design (no PySide6 import) — intended to be driven from a GUI-owned worker
thread (QThread/QRunnable), never the Qt main/event-loop thread, since runs can take from
seconds to hours (PRD 4.2/4.1). See the approved plan's Section B for the full rationale.
"""

from __future__ import annotations

import os
import subprocess
import threading
from collections.abc import Callable, Iterator
from pathlib import Path

from robo_rec.recovery.args import (
    build_missing_word_known_position_args,
    build_missing_word_unknown_position_args,
    build_rearrangement_args,
    build_typo_correction_args,
)
from robo_rec.recovery.exceptions import LaunchError
from robo_rec.recovery.models import (
    MissingWordKnownPositionSpec,
    MissingWordUnknownPositionSpec,
    RearrangementSpec,
    RecoveryEvent,
    RecoveryResult,
    RecoverySpec,
    TypoCorrectionSpec,
)
from robo_rec.recovery.parser import parse_line
from robo_rec.util.paths import btcrecover_root, seedrecover_script
from robo_rec.util.process import python_executable, stream_lines


def _build_argv_and_tokenlist(
    spec: RecoverySpec, *, use_gpu: bool
) -> tuple[list[str], Path | None]:
    if isinstance(spec, RearrangementSpec):
        argv, tokenlist_path = build_rearrangement_args(spec, use_gpu=use_gpu)
        return argv, tokenlist_path
    if isinstance(spec, MissingWordKnownPositionSpec):
        return build_missing_word_known_position_args(spec, use_gpu=use_gpu), None
    if isinstance(spec, MissingWordUnknownPositionSpec):
        return build_missing_word_unknown_position_args(spec, use_gpu=use_gpu), None
    if isinstance(spec, TypoCorrectionSpec):
        return build_typo_correction_args(spec, use_gpu=use_gpu), None
    raise TypeError(f"Unrecognized RecoverySpec variant: {type(spec).__name__}")


class BtcrecoverRunner:
    """Not Qt-affine; safe to construct and drive from any single thread at a time."""

    def __init__(
        self,
        spec: RecoverySpec,
        *,
        btcrecover_dir: Path | None = None,
        use_gpu: bool = False,
    ) -> None:
        self._spec = spec
        self._btcrecover_dir = btcrecover_dir or btcrecover_root()
        self._use_gpu = use_gpu
        self._process: subprocess.Popen | None = None
        self._stop_event = threading.Event()
        self._tokenlist_path: Path | None = None

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def cancel(self) -> None:
        """Thread-safe: safe to call from the Qt main thread while run()/run_iter()
        executes on a worker thread."""
        self._stop_event.set()
        process = self._process
        if process is not None and process.poll() is None:
            process.terminate()

    def run(self, on_event: Callable[[RecoveryEvent], None]) -> RecoveryResult:
        """Blocking — call from a worker thread. Streams events to on_event; returns the
        final RecoveryResult once the subprocess exits."""
        result: RecoveryResult | None = None
        for event in self.run_iter():
            on_event(event)
            if event.kind == "finished":
                result = event.result
        assert result is not None
        return result

    def run_iter(self) -> Iterator[RecoveryEvent]:
        """Generator alternative to run(). Final yielded event has kind == 'finished' with
        .result populated. Cleans up any generated tokenlist file on exit or cancellation."""
        argv, tokenlist_path = _build_argv_and_tokenlist(self._spec, use_gpu=self._use_gpu)
        self._tokenlist_path = tokenlist_path
        full_argv = [python_executable(), str(seedrecover_script()), *argv]

        try:
            process, lines = stream_lines(
                full_argv, cwd=self._btcrecover_dir, stop_event=self._stop_event
            )
        except OSError as exc:
            raise LaunchError(f"Failed to launch seedrecover.py: {exc}") from exc

        # Assign self._process BEFORE yielding: cancel() reads self._process, and once
        # control returns to the caller after a yield, cancel() may be called immediately
        # (e.g. a GUI Cancel button right after seeing the "started" event). If the
        # assignment happened after this yield, an early cancel() would be a silent no-op
        # and the subprocess would run to completion unattended.
        self._process = process

        yield RecoveryEvent(kind="started", message="Starting recovery search...")
        found_result: RecoveryResult | None = None
        mnemonic: str | None = None
        matched_path: str | None = None

        try:
            for line in lines:
                event = parse_line(line)
                if event.kind == "found" and event.result is not None:
                    if event.result.mnemonic is not None:
                        mnemonic = event.result.mnemonic
                    if event.result.matched_path is not None:
                        matched_path = event.result.matched_path
                yield event

            return_code = process.wait()
        finally:
            self._cleanup_tokenlist()

        succeeded = mnemonic is not None
        found_result = RecoveryResult(
            mnemonic=mnemonic,
            matched_address=self._first_target_address(),
            matched_path=matched_path,
            return_code=return_code,
            succeeded=succeeded,
        )
        yield RecoveryEvent(
            kind="finished",
            message="Recovery finished." if succeeded else "Recovery finished: not found.",
            result=found_result,
        )

    def _first_target_address(self) -> str | None:
        addrs = getattr(self._spec, "addrs", None)
        return addrs[0] if addrs else None

    def _cleanup_tokenlist(self) -> None:
        if self._tokenlist_path is not None:
            try:
                os.unlink(self._tokenlist_path)
            except FileNotFoundError:
                pass
            self._tokenlist_path = None
