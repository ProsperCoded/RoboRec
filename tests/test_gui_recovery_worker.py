"""RecoveryWorker is the one place robo_rec.recovery gets coupled to Qt threading. These
tests confirm the coupling is actually thread-safe (signals delivered on the main thread)
and that cancellation works through the Qt layer, not just the underlying engine."""

from __future__ import annotations

from PySide6.QtCore import QThread

from robo_rec.gui.recovery_worker import RecoveryWorker
from robo_rec.recovery.models import MissingWordKnownPositionSpec, MissingWordUnknownPositionSpec

MNEMONIC = "rotate dream drip opinion key dove region mind visit diesel negative speed"
ADDRESS = "1FMHvVtJkJFnSxaN9KUn5q3KtqNwej1sZ6"


def test_events_and_finished_deliver_on_main_thread(qtbot):
    words = MNEMONIC.split()
    words[4] = None
    spec = MissingWordKnownPositionSpec(words=words, wallet_type="bip39", addrs=[ADDRESS])

    worker = RecoveryWorker(spec)
    main_thread = QThread.currentThread()
    event_threads = []
    worker.event.connect(lambda e: event_threads.append(QThread.currentThread() is main_thread))

    with qtbot.waitSignal(worker.finished, timeout=15000) as blocker:
        worker.start()

    result = blocker.args[0]
    assert result.succeeded is True
    assert result.mnemonic == MNEMONIC
    assert event_threads, "expected at least one RecoveryEvent"
    assert all(event_threads), "every event callback must run on the Qt main thread"

    worker.wait_and_cleanup()


def test_cancel_stops_search_promptly(qtbot):
    words = MNEMONIC.split()
    del words[4]
    del words[7]
    spec = MissingWordUnknownPositionSpec(
        words=words, full_length=12, wallet_type="bip39", addrs=[ADDRESS]
    )

    worker = RecoveryWorker(spec)
    started = []
    worker.event.connect(lambda e: started.append(e.kind) if e.kind == "started" else None)

    with qtbot.waitSignal(worker.finished, timeout=10000) as blocker:
        worker.start()
        qtbot.waitUntil(lambda: len(started) > 0, timeout=5000)
        worker.cancel()

    result = blocker.args[0]
    assert result.succeeded is False
    worker.wait_and_cleanup()


def test_failed_signal_on_launch_error(qtbot, monkeypatch):
    from robo_rec.recovery import runner as runner_module

    def _boom(*args, **kwargs):
        raise runner_module.LaunchError("simulated launch failure")

    monkeypatch.setattr(runner_module.BtcrecoverRunner, "run_iter", _boom)

    words = MNEMONIC.split()
    words[4] = None
    spec = MissingWordKnownPositionSpec(words=words, wallet_type="bip39", addrs=[ADDRESS])
    worker = RecoveryWorker(spec)

    with qtbot.waitSignal(worker.failed, timeout=5000) as blocker:
        worker.start()

    assert "simulated launch failure" in blocker.args[0]
    worker.wait_and_cleanup()
