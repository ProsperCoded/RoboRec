"""Qt bridge for robo_rec.gpu.probe_gpu_status().

The OpenCL and NVIDIA probes shell out to subprocesses, while the optional PyCUDA check uses
module discovery. A full probe_gpu_status() call is
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

    def __init__(self, *, force_recheck: bool) -> None:
        super().__init__()
        self._force_recheck = force_recheck

    def run(self) -> None:
        self.finished.emit(probe_gpu_status(force_recheck=self._force_recheck))


class GpuProbeWorker(QObject):
    """Create on the Qt main thread, connect to `finished`, call start(). One-shot — create
    a fresh GpuProbeWorker for each re-probe (e.g. a Refresh button).

    force_recheck=True bypasses the cached OpenCL correctness verdict (see
    robo_rec.gpu.correctness_cache) and re-runs the full test for this device/driver —
    what the GPU Status panel's "Re-check GPU" button asks for. The default False path
    is what MainWindow's startup probe uses: cheap when a verdict is already cached."""

    finished = Signal(object)  # GpuStatusReport

    def __init__(self, parent: QObject | None = None, *, force_recheck: bool = False) -> None:
        super().__init__(parent)
        self._thread = QThread(self)
        self._task = _ProbeTask(force_recheck=force_recheck)
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
