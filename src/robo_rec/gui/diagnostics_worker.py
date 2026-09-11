"""Qt bridge for robo_rec.diagnostics.report.build_diagnostics_report().

Building the full report runs a live BTC/ETH/SOL self-test (~30-90s per coin, so a few
minutes total) in addition to the GPU probe — must run off the Qt main thread or the whole
GUI freezes for that long. Same QThread pattern as gpu_worker.GpuProbeWorker.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, QThread, Signal

from robo_rec.diagnostics.report import build_diagnostics_report


class _BuildTask(QObject):
    finished = Signal(object)  # dict, or None on failure
    failed = Signal(str)

    def __init__(self, *, use_gpu_for_self_test: bool, include_sensitive: bool) -> None:
        super().__init__()
        self._use_gpu_for_self_test = use_gpu_for_self_test
        self._include_sensitive = include_sensitive

    def run(self) -> None:
        try:
            report = build_diagnostics_report(
                use_gpu_for_self_test=self._use_gpu_for_self_test,
                include_sensitive=self._include_sensitive,
            )
        except Exception as exc:  # noqa: BLE001 - report the failure, don't crash the GUI
            self.failed.emit(f"{type(exc).__name__}: {exc}")
            return
        self.finished.emit(report)


class DiagnosticsWorker(QObject):
    """Create on the Qt main thread, connect to `finished`/`failed`, call start(). One-shot —
    create a fresh instance for each export."""

    finished = Signal(object)  # dict
    failed = Signal(str)

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        use_gpu_for_self_test: bool,
        include_sensitive: bool,
    ) -> None:
        super().__init__(parent)
        self._thread = QThread(self)
        self._task = _BuildTask(
            use_gpu_for_self_test=use_gpu_for_self_test, include_sensitive=include_sensitive
        )
        self._task.moveToThread(self._thread)
        self._task.finished.connect(self.finished)
        self._task.failed.connect(self.failed)
        self._task.finished.connect(self._thread.quit)
        self._task.failed.connect(self._thread.quit)
        self._thread.started.connect(self._task.run)

    def start(self) -> None:
        self._thread.start()

    def wait_and_cleanup(self) -> None:
        self._thread.quit()
        self._thread.wait()


__all__ = ["DiagnosticsWorker"]
