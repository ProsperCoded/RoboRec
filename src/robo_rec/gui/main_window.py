"""MainWindow — sidebar + top bar + stacked content (Dashboard / action panels / GPU status)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from robo_rec.gui.dashboard import (
    ACTION_DERIVE_WALLET,
    ACTION_MISSING_WORDS,
    ACTION_REARRANGE,
    ACTION_TYPO_CORRECTION,
    Dashboard,
)
from robo_rec.gui.gpu_state import set_gpu_available
from robo_rec.gui.gpu_worker import GpuProbeWorker
from robo_rec.gui.icons import load_pixmap
from robo_rec.gui.panels.derive_wallet import DeriveWalletPanel
from robo_rec.gui.panels.gpu_status import GpuStatusPanel
from robo_rec.gui.panels.missing_words import MissingWordsPanel
from robo_rec.gui.panels.rearrange import RearrangePanel
from robo_rec.gui.panels.typo_correction import TypoCorrectionPanel
from robo_rec.gui.sidebar import Sidebar
from robo_rec.gui.terminal_sidebar import TerminalSidebar
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
        root_layout.addWidget(self._sidebar)

        content_area = QWidget()
        content_area.setObjectName("ContentArea")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        root_layout.addWidget(content_area, stretch=1)

        content_layout.addWidget(self._build_top_bar())

        self._stack = AnimatedStackedWidget()
        self._stack.currentChanged.connect(self._reset_scroll_positions)
        content_layout.addWidget(self._stack, stretch=1)

        self._scroll_wrappers: dict[QWidget, QScrollArea] = {}

        # Terminal output widget: floats above everything, anchored top-right
        # of the whole window (not tied to any single panel).
        self._terminal_sidebar = TerminalSidebar(central)
        self._terminal_sidebar.hide()

        self._dashboard = Dashboard()
        self._dashboard.action_selected.connect(self._show_action)
        self._add_scrollable(self._dashboard)

        self._missing_words_panel = MissingWordsPanel()
        self._missing_words_panel.back_requested.connect(self._show_dashboard)
        self._add_scrollable(self._missing_words_panel)

        self._rearrange_panel = RearrangePanel()
        self._rearrange_panel.back_requested.connect(self._show_dashboard)
        self._add_scrollable(self._rearrange_panel)

        self._derive_wallet_panel = DeriveWalletPanel()
        self._derive_wallet_panel.back_requested.connect(self._show_dashboard)
        self._add_scrollable(self._derive_wallet_panel)

        self._typo_correction_panel = TypoCorrectionPanel()
        self._typo_correction_panel.back_requested.connect(self._show_dashboard)
        self._add_scrollable(self._typo_correction_panel)

        self._gpu_status_panel = GpuStatusPanel()
        self._gpu_status_panel.back_requested.connect(self._show_dashboard)
        self._gpu_status_panel.set_report_callback(self.set_gpu_status)
        self._add_scrollable(self._gpu_status_panel)

        self._panels_by_action = {
            ACTION_MISSING_WORDS: self._missing_words_panel,
            ACTION_REARRANGE: self._rearrange_panel,
            ACTION_DERIVE_WALLET: self._derive_wallet_panel,
            ACTION_TYPO_CORRECTION: self._typo_correction_panel,
        }

        self._show_dashboard()
        self._probe_gpu_for_badge()
        self._reposition_terminal_widget()

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

    def get_terminal_sidebar(self) -> TerminalSidebar:
        """Get the terminal sidebar for logging output."""
        return self._terminal_sidebar

    def _reposition_terminal_widget(self) -> None:
        """Anchor the terminal widget to the top-right corner of the window,
        just below the top bar."""
        margin = 16
        top_bar_height = 56
        x = self.centralWidget().width() - self._terminal_sidebar.width() - margin
        y = top_bar_height + margin
        self._terminal_sidebar.move(max(0, x), y)
        self._terminal_sidebar.raise_()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().resizeEvent(event)
        self._reposition_terminal_widget()

    def set_gpu_status(self, detected: bool) -> None:
        """Update the top-bar GPU badge and the process-wide GPU-availability cache that
        recovery panels read for their time estimates. Called once at startup with a real
        probe result, and again whenever the GPU Status panel re-checks."""
        set_gpu_available(detected)
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

    def _add_scrollable(self, panel: QWidget) -> None:
        """Wrap `panel` in a QScrollArea and add it to the stack, so panels taller
        than the window (long forms, seed tile grids) scroll instead of clipping."""
        scroll_area = QScrollArea()
        scroll_area.setWidget(panel)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll_wrappers[panel] = scroll_area
        self._stack.addWidget(scroll_area)

    def _reset_scroll_positions(self) -> None:
        """Scroll the incoming page back to the top on every view switch, so
        re-entering a panel never lands mid-scroll from a previous visit."""
        current = self._stack.currentWidget()
        if isinstance(current, QScrollArea):
            current.verticalScrollBar().setValue(0)

    def _show_dashboard(self) -> None:
        self._sidebar.set_active(True)
        self._stack.setCurrentWidget(self._scroll_wrappers[self._dashboard])

    def _show_gpu_status(self) -> None:
        """Reached only via the top-bar GPU badge — not a sidebar tab, since it's a
        one-off diagnostics view rather than a recovery scenario. The sidebar's 'Actions'
        stays unchecked while here, matching the derive/missing-words/etc. panels."""
        self._sidebar.set_active(False)
        self._stack.setCurrentWidget(self._scroll_wrappers[self._gpu_status_panel])

    def _show_action(self, action: str) -> None:
        panel = self._panels_by_action.get(action)
        if panel is not None:
            self._sidebar.set_active(False)
            self._stack.setCurrentWidget(self._scroll_wrappers[panel])
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
