"""Qt bridge for robo_rec.gpu.probe_gpu_status().

Each individual probe (opencl_probe, nvidia_probe, pycuda_probe) shells out to a subprocess
or does a filesystem/import check with its own timeout, so a full probe_gpu_status() call is
normally well under a second — but it can stall up to the sum of each probe's timeout in a
degenerate case (e.g. a hung subprocess), so it's still run off the Qt main thread rather than
assumed instant. Uses the same QThread pattern as recovery_worker.py: the worker QObject lives
on the main thread and only re-emits from a background-thread task, so its signals are always
delivered on the main thread.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from robo_rec.gpu.report import GpuStatusReport, probe_gpu_status


class _ProbeTask(QObject):
    finished = Signal(object)  # GpuStatusReport

    def run(self) -> None:
        self.finished.emit(probe_gpu_status())


class GpuProbeWorker(QObject):
    """Create on the Qt main thread, connect to `finished`, call start(). One-shot — create
    a fresh GpuProbeWorker for each re-probe (e.g. a Refresh button)."""

    finished = Signal(object)  # GpuStatusReport

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread = QThread(self)
        self._task = _ProbeTask()
        self._task.moveToThread(self._thread)
        self._task.finished.connect(self.finished)
        self._task.finished.connect(self._thread.quit)
        self._thread.started.connect(self._task.run)

    def start(self) -> None:
        self._thread.start()

    def wait_and_cleanup(self) -> None:
        self._thread.quit()
        self._thread.wait()


__all__ = ["GpuProbeWorker", "GpuStatusReport"]
