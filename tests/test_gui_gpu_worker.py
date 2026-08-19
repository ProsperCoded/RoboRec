from PySide6.QtCore import QThread

from robo_rec.gui.gpu_worker import GpuProbeWorker


def test_gpu_probe_worker_delivers_on_main_thread(qtbot):
    main_thread = QThread.currentThread()
    worker = GpuProbeWorker()

    with qtbot.waitSignal(worker.finished, timeout=15000) as blocker:
        worker.start()

    report = blocker.args[0]
    assert QThread.currentThread() is main_thread
    # This dev machine has no discrete GPU (see robo-rec-implementation.md) — every probe
    # degrades gracefully rather than raising, so the report should reflect that cleanly.
    assert report.opencl_available is False
    assert report.probe_errors

    worker.wait_and_cleanup()
