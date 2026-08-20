"""MainWindow — sidebar + top bar + stacked content (Dashboard / action panels / GPU status)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget

from robo_rec.gui.dashboard import (
    ACTION_DERIVE_WALLET,
    ACTION_MISSING_WORDS,
    ACTION_REARRANGE,
    ACTION_TYPO_CORRECTION,
    Dashboard,
)
from robo_rec.gui.gpu_worker import GpuProbeWorker
from robo_rec.gui.icons import load_pixmap
from robo_rec.gui.panels.derive_wallet import DeriveWalletPanel
from robo_rec.gui.panels.gpu_status import GpuStatusPanel
from robo_rec.gui.panels.missing_words import MissingWordsPanel
from robo_rec.gui.panels.rearrange import RearrangePanel
from robo_rec.gui.panels.typo_correction import TypoCorrectionPanel
from robo_rec.gui.sidebar import Sidebar
from robo_rec.gui.theme import ACCENT, STYLESHEET, TEXT_SECONDARY
from robo_rec.gui.widgets.animated_stack import AnimatedStackedWidget


class _ClickableWidget(QWidget):
    """Plain QWidget with a clicked signal, used for the top-bar GPU badge."""

    clicked = Signal()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Robo-Rec")
        self.resize(1080, 680)
        self.setStyleSheet(STYLESHEET)

        self._startup_gpu_worker: GpuProbeWorker | None = None

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.actions_requested.connect(self._show_dashboard)
        self._sidebar.gpu_status_requested.connect(self._show_gpu_status)
        root_layout.addWidget(self._sidebar)

        content_area = QWidget()
        content_area.setObjectName("ContentArea")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        root_layout.addWidget(content_area, stretch=1)

        content_layout.addWidget(self._build_top_bar())

        self._stack = AnimatedStackedWidget()
        content_layout.addWidget(self._stack, stretch=1)

        self._dashboard = Dashboard()
        self._dashboard.action_selected.connect(self._show_action)
        self._stack.addWidget(self._dashboard)

        self._missing_words_panel = MissingWordsPanel()
        self._missing_words_panel.back_requested.connect(self._show_dashboard)
        self._stack.addWidget(self._missing_words_panel)

        self._rearrange_panel = RearrangePanel()
        self._rearrange_panel.back_requested.connect(self._show_dashboard)
        self._stack.addWidget(self._rearrange_panel)

        self._derive_wallet_panel = DeriveWalletPanel()
        self._derive_wallet_panel.back_requested.connect(self._show_dashboard)
        self._stack.addWidget(self._derive_wallet_panel)

        self._typo_correction_panel = TypoCorrectionPanel()
        self._typo_correction_panel.back_requested.connect(self._show_dashboard)
        self._stack.addWidget(self._typo_correction_panel)

        self._gpu_status_panel = GpuStatusPanel()
        self._gpu_status_panel.back_requested.connect(self._show_dashboard)
        self._gpu_status_panel.set_report_callback(self.set_gpu_status)
        self._stack.addWidget(self._gpu_status_panel)

        self._panels_by_action = {
            ACTION_MISSING_WORDS: self._missing_words_panel,
            ACTION_REARRANGE: self._rearrange_panel,
            ACTION_DERIVE_WALLET: self._derive_wallet_panel,
            ACTION_TYPO_CORRECTION: self._typo_correction_panel,
        }

        self._show_dashboard()
        self._probe_gpu_for_badge()

    def _build_top_bar(self) -> QWidget:
        top_bar = QWidget()
        top_bar.setObjectName("TopBar")
        top_bar.setFixedHeight(56)
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(24, 0, 24, 0)

        title = QLabel("Robo-Rec")
        title.setObjectName("AppTitle")
        layout.addWidget(title)
        layout.addStretch(1)

        self._gpu_badge = _ClickableWidget()
        self._gpu_badge.setObjectName("GpuBadge")
        self._gpu_badge.setCursor(Qt.CursorShape.PointingHandCursor)
        self._gpu_badge.setToolTip("View GPU Status")
        self._gpu_badge.clicked.connect(self._show_gpu_status)
        badge_layout = QHBoxLayout(self._gpu_badge)
        badge_layout.setContentsMargins(12, 4, 12, 4)
        badge_layout.setSpacing(6)
        self._gpu_badge_icon = QLabel()
        badge_layout.addWidget(self._gpu_badge_icon)
        self._gpu_badge_text = QLabel()
        badge_layout.addWidget(self._gpu_badge_text)
        layout.addWidget(self._gpu_badge)

        self.set_gpu_status(detected=False)
        return top_bar

    def set_gpu_status(self, detected: bool) -> None:
        """Update the top-bar GPU badge. Called once at startup with a real probe result,
        and again whenever the GPU Status panel re-checks."""
        color = ACCENT if detected else TEXT_SECONDARY
        self._gpu_badge_icon.setPixmap(load_pixmap("cpu", color, 14))
        self._gpu_badge_text.setText("GPU Detected" if detected else "CPU Only")
        self._gpu_badge.setProperty("state", "detected" if detected else "unavailable")
        self._gpu_badge.style().unpolish(self._gpu_badge)
        self._gpu_badge.style().polish(self._gpu_badge)

    def _probe_gpu_for_badge(self) -> None:
        """One-shot startup probe so the top-bar badge reflects reality immediately,
        without requiring the user to visit the GPU Status panel first."""
        self._startup_gpu_worker = GpuProbeWorker()
        self._startup_gpu_worker.finished.connect(self._on_startup_gpu_probe_finished)
        self._startup_gpu_worker.start()

    def _on_startup_gpu_probe_finished(self, report) -> None:
        self.set_gpu_status(report.gpu_acceleration_available)
        if self._startup_gpu_worker is not None:
            self._startup_gpu_worker.wait_and_cleanup()
            self._startup_gpu_worker = None

    def _show_dashboard(self) -> None:
        self._sidebar.set_active("actions")
        self._stack.setCurrentWidget(self._dashboard)

    def _show_gpu_status(self) -> None:
        self._sidebar.set_active("gpu_status")
        self._stack.setCurrentWidget(self._gpu_status_panel)

    def _show_action(self, action: str) -> None:
        panel = self._panels_by_action.get(action)
        if panel is not None:
            self._sidebar.set_active("actions")
            self._stack.setCurrentWidget(panel)
            if panel is self._missing_words_panel:
                self._missing_words_panel.focus_first_word()

    def closeEvent(self, event) -> None:
        """Cancel and join any in-flight background search/probe before the window (and
        its child QThreads) get destroyed — a QThread destroyed while still running is
        undefined behavior in Qt."""
        if self._startup_gpu_worker is not None:
            self._startup_gpu_worker.wait_and_cleanup()
            self._startup_gpu_worker = None
        for panel in (
            self._missing_words_panel,
            self._rearrange_panel,
            self._typo_correction_panel,
            self._gpu_status_panel,
        ):
            panel.shutdown()
        super().closeEvent(event)
