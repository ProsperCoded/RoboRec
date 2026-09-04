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
