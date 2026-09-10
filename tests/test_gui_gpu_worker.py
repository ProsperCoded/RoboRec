from unittest.mock import patch

from PySide6.QtCore import QThread

from robo_rec.gui.gpu_worker import GpuProbeWorker


def test_gpu_probe_worker_delivers_on_main_thread(qtbot):
    main_thread = QThread.currentThread()
    worker = GpuProbeWorker()

    with qtbot.waitSignal(worker.finished, timeout=15000) as blocker:
        worker.start()

    report = blocker.args[0]
    assert QThread.currentThread() is main_thread
    assert isinstance(report.opencl_available, bool)
    assert report.cpu_info.logical_cores

    worker.wait_and_cleanup()


def test_gpu_probe_worker_default_does_not_force_recheck(qtbot):
    with patch(
        "robo_rec.gui.gpu_worker.probe_gpu_status", return_value="fake-report"
    ) as probe_mock:
        worker = GpuProbeWorker()
        with qtbot.waitSignal(worker.finished, timeout=5000):
            worker.start()
        worker.wait_and_cleanup()
    probe_mock.assert_called_once_with(force_recheck=False)


def test_gpu_probe_worker_force_recheck_true_is_threaded_through(qtbot):
    """The GPU Status panel's "Re-check GPU" button relies on this to actually bypass
    a cached correctness verdict rather than silently reusing it."""
    with patch(
        "robo_rec.gui.gpu_worker.probe_gpu_status", return_value="fake-report"
    ) as probe_mock:
        worker = GpuProbeWorker(force_recheck=True)
        with qtbot.waitSignal(worker.finished, timeout=5000):
            worker.start()
        worker.wait_and_cleanup()
    probe_mock.assert_called_once_with(force_recheck=True)
