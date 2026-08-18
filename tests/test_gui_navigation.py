from robo_rec.gui.dashboard import (
    ACTION_DERIVE_WALLET,
    ACTION_MISSING_WORDS,
    ACTION_REARRANGE,
)
from robo_rec.gui.main_window import MainWindow


def test_dashboard_is_initial_view(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    assert window._stack.currentWidget() is window._dashboard


def test_selecting_each_action_swaps_to_its_panel(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window._show_action(ACTION_MISSING_WORDS)
    assert window._stack.currentWidget() is window._missing_words_panel

    window._show_action(ACTION_REARRANGE)
    assert window._stack.currentWidget() is window._rearrange_panel

    window._show_action(ACTION_DERIVE_WALLET)
    assert window._stack.currentWidget() is window._derive_wallet_panel


def test_back_breadcrumb_returns_to_dashboard(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window._show_action(ACTION_MISSING_WORDS)
    window._missing_words_panel.back_requested.emit()
    assert window._stack.currentWidget() is window._dashboard


def test_gpu_badge_reflects_status(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.set_gpu_status(detected=True)
    assert window._gpu_badge.text() == "GPU Detected"

    window.set_gpu_status(detected=False)
    assert window._gpu_badge.text() == "CPU Only"
