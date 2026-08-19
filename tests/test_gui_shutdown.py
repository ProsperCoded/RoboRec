"""Closing the main window while a background search/probe is in flight must not destroy
a still-running QThread (undefined behavior in Qt, previously reproducible when the
window's startup GPU probe hadn't finished before teardown). MainWindow.closeEvent joins
every panel's worker via panel.shutdown() to guard against this.
"""

from __future__ import annotations

from robo_rec.gui.main_window import MainWindow
from robo_rec.recovery.models import MissingWordUnknownPositionSpec

MNEMONIC = "rotate dream drip opinion key dove region mind visit diesel negative speed"
ADDRESS = "1FMHvVtJkJFnSxaN9KUn5q3KtqNwej1sZ6"


def test_close_immediately_after_construction_does_not_leak_gpu_probe_thread(qtbot):
    # Regression: the startup GPU probe (fired in MainWindow.__init__) previously had no
    # guaranteed join point, so closing the window right after construction could destroy
    # its background QThread mid-flight.
    window = MainWindow()
    qtbot.addWidget(window)
    window.close()


def test_close_with_active_recovery_search_joins_worker_cleanly(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    words = MNEMONIC.split()
    del words[4]
    del words[7]
    spec = MissingWordUnknownPositionSpec(
        words=words, full_length=12, wallet_type="bip39", addrs=[ADDRESS]
    )
    panel = window._missing_words_panel
    panel._start_search(spec)
    qtbot.waitUntil(lambda: panel._worker is not None, timeout=2000)

    window.close()
    assert panel._worker is None
