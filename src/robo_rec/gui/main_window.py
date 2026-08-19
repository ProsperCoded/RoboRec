"""MainWindow — sidebar + top bar + stacked content (Dashboard / action panels)."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget

from robo_rec.gui.dashboard import (
    ACTION_DERIVE_WALLET,
    ACTION_MISSING_WORDS,
    ACTION_REARRANGE,
    Dashboard,
)
from robo_rec.gui.icons import load_pixmap
from robo_rec.gui.panels.derive_wallet import DeriveWalletPanel
from robo_rec.gui.panels.missing_words import MissingWordsPanel
from robo_rec.gui.panels.rearrange import RearrangePanel
from robo_rec.gui.sidebar import Sidebar
from robo_rec.gui.theme import ACCENT, STYLESHEET, TEXT_SECONDARY
from robo_rec.gui.widgets.animated_stack import AnimatedStackedWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Robo-Rec")
        self.resize(1080, 680)
        self.setStyleSheet(STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.actions_requested.connect(self._show_dashboard)
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

        self._panels_by_action = {
            ACTION_MISSING_WORDS: self._missing_words_panel,
            ACTION_REARRANGE: self._rearrange_panel,
            ACTION_DERIVE_WALLET: self._derive_wallet_panel,
        }

        self._show_dashboard()

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

        self._gpu_badge = QWidget()
        self._gpu_badge.setObjectName("GpuBadge")
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

    def set_gpu_status(self, *, detected: bool) -> None:
        """Update the GPU badge. Detection wiring lands with the GPU status panel."""
        color = ACCENT if detected else TEXT_SECONDARY
        self._gpu_badge_icon.setPixmap(load_pixmap("cpu", color, 14))
        self._gpu_badge_text.setText("GPU Detected" if detected else "CPU Only")
        self._gpu_badge.setProperty("state", "detected" if detected else "unavailable")
        self._gpu_badge.style().unpolish(self._gpu_badge)
        self._gpu_badge.style().polish(self._gpu_badge)

    def _show_dashboard(self) -> None:
        self._sidebar.set_active(True)
        self._stack.setCurrentWidget(self._dashboard)

    def _show_action(self, action: str) -> None:
        panel = self._panels_by_action.get(action)
        if panel is not None:
            self._sidebar.set_active(False)
            self._stack.setCurrentWidget(panel)
            if panel is self._missing_words_panel:
                self._missing_words_panel.focus_first_word()
