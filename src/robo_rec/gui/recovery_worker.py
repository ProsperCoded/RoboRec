"""Qt bridge for robo_rec.recovery.BtcrecoverRunner.

The engine (robo_rec.recovery) is deliberately Qt-agnostic (no PySide6 import, per the
approved engine-layer plan) so it stays testable headlessly and reusable outside Qt. This
module is the one place that couples it to Qt.

RecoveryWorker itself is created on and lives on the Qt main thread — its signals are
therefore delivered to connected slots via a queued connection on the main thread, which is
what makes it safe for panels to update widgets directly from event/finished/failed handlers.
The actual blocking BtcrecoverRunner.run_iter() loop runs on a *separate* internal QObject
(_RunnerTask) that gets moved to a background QThread; _RunnerTask re-emits everything through
RecoveryWorker via plain method calls (not signal/slot), which is safe here because
_RunnerTask calls them synchronously and RecoveryWorker.emit() is thread-safe regardless of
which thread calls it — only the *delivery* to a receiver depends on the receiver's thread
affinity, which is what puts these callbacks back on the main thread.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from robo_rec.recovery.exceptions import RecoveryError
from robo_rec.recovery.models import RecoveryEvent, RecoveryResult, RecoverySpec
from robo_rec.recovery.runner import BtcrecoverRunner


class _RunnerTask(QObject):
    """Lives on the background QThread. Never construct/use outside RecoveryWorker."""

    event = Signal(object)  # RecoveryEvent
    finished = Signal(object)  # RecoveryResult
    failed = Signal(str)

    def __init__(self, runner: BtcrecoverRunner) -> None:
        super().__init__()
        self._runner = runner

    def run(self) -> None:
        try:
            for recovery_event in self._runner.run_iter():
                self.event.emit(recovery_event)
                if recovery_event.kind == "finished" and recovery_event.result is not None:
                    self.finished.emit(recovery_event.result)
        except RecoveryError as exc:
            self.failed.emit(str(exc))


class RecoveryWorker(QObject):
    """Create on the Qt main thread; connect to event/finished/failed with ordinary slots —
    they're guaranteed to run on the main thread. Create one per search; call
    wait_and_cleanup() after finished/failed fires (or after cancel()), then discard."""

    event = Signal(object)  # RecoveryEvent
    finished = Signal(object)  # RecoveryResult
    failed = Signal(str)  # error message, when the subprocess couldn't even launch

    def __init__(self, spec: RecoverySpec, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._runner = BtcrecoverRunner(spec)
        self._thread = QThread(self)
        self._task = _RunnerTask(self._runner)
        self._task.moveToThread(self._thread)

        self._task.event.connect(self.event)
        self._task.finished.connect(self.finished)
        self._task.failed.connect(self.failed)
        self._task.finished.connect(self._thread.quit)
        self._task.failed.connect(self._thread.quit)

        self._thread.started.connect(self._task.run)

    def start(self) -> None:
        self._thread.start()

    def cancel(self) -> None:
        """Safe to call from the Qt main thread while the search runs on the worker
        thread — BtcrecoverRunner.cancel() is designed for exactly this."""
        self._runner.cancel()

    def wait_and_cleanup(self) -> None:
        """Call after finished/failed fires (or after cancel()) to join the background
        thread before discarding this worker, so it doesn't leak a running QThread."""
        self._thread.quit()
        self._thread.wait()


__all__ = ["RecoveryEvent", "RecoveryResult", "RecoveryWorker"]
