"""Terminal output widget — a small live-log card anchored in the window's
top-right corner while a recovery search runs, expandable to a full log dialog.
"""

from __future__ import annotations

from collections import deque

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from robo_rec.gui.icons import load_icon
from robo_rec.gui.theme import ACCENT

_CARD_WIDTH = 300
_CARD_HEIGHT = 130
_LIVE_LINES = 8
_HISTORY_LINES = 500
_UPDATE_INTERVAL_MS = 300
_MAX_LINE_LEN = 100

_MONO_FONT_FAMILY = "Menlo, Consolas, monospace"

_CARD_STYLE = f"""
    QFrame#TerminalCard {{
        background-color: #14181f;
        border: 1px solid #2a3138;
        border-radius: 10px;
    }}
    QLabel#TerminalTitle {{
        color: #9aa4af;
        font-weight: 600;
        font-size: 11px;
    }}
    QPlainTextEdit#TerminalLog {{
        background-color: #0b0e13;
        color: {ACCENT};
        border: 1px solid #232a31;
        border-radius: 6px;
        padding: 6px 8px;
    }}
    QPushButton#TerminalIconBtn {{
        background: transparent;
        border: none;
        border-radius: 4px;
        padding: 2px;
    }}
    QPushButton#TerminalIconBtn:hover {{
        background-color: #232a31;
    }}
"""

_DIALOG_STYLE = f"""
    QDialog {{
        background-color: #0f1318;
    }}
    QLabel#DialogTitle {{
        color: #e6e9ec;
        font-weight: 600;
        font-size: 14px;
    }}
    QPlainTextEdit#DialogLog {{
        background-color: #0b0e13;
        color: {ACCENT};
        border: 1px solid #232a31;
        border-radius: 8px;
        padding: 12px;
    }}
    QPushButton#DialogCloseBtn {{
        background-color: #1b2129;
        color: #c7ccd1;
        border: 1px solid #2a3138;
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 12px;
    }}
    QPushButton#DialogCloseBtn:hover {{
        background-color: #232a31;
    }}
"""


class TerminalSidebar(QFrame):
    """Compact live-log card. Click anywhere on it to open the full log dialog.
    Hidden by default — callers show() it when a search starts and hide() it
    when the search ends."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TerminalCard")
        self.setStyleSheet(_CARD_STYLE)
        self.setFixedSize(_CARD_WIDTH, _CARD_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        pulse = QLabel("●")
        pulse.setStyleSheet(f"color: {ACCENT}; font-size: 9px;")
        header.addWidget(pulse)

        title = QLabel("Live output")
        title.setObjectName("TerminalTitle")
        header.addWidget(title)
        header.addStretch()

        expand_btn = QPushButton()
        expand_btn.setObjectName("TerminalIconBtn")
        expand_btn.setIcon(load_icon("square-plus", "#9aa4af", 14))
        expand_btn.setIconSize(QSize(14, 14))
        expand_btn.setFixedSize(22, 22)
        expand_btn.setToolTip("Expand log")
        expand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        expand_btn.clicked.connect(self._open_dialog)
        header.addWidget(expand_btn)

        layout.addLayout(header)

        self._live_log = QPlainTextEdit()
        self._live_log.setObjectName("TerminalLog")
        self._live_log.setReadOnly(True)
        self._live_log.setFont(QFont(_MONO_FONT_FAMILY, 8))
        self._live_log.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._live_log.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._live_log.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._live_log.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self._live_log, stretch=1)

        self._live_buffer: deque[str] = deque(maxlen=_LIVE_LINES)
        self._history_buffer: deque[str] = deque(maxlen=_HISTORY_LINES)
        self._pending: list[str] = []
        self._dialog: _TerminalDialog | None = None

        self._flush_timer = QTimer(self)
        self._flush_timer.timeout.connect(self._flush)
        self._flush_timer.start(_UPDATE_INTERVAL_MS)

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_dialog()
        super().mousePressEvent(event)

    def log(self, line: str, level: str = "info") -> None:
        """Queue a log line. Filtering by level is expected to happen upstream
        (see log_filter.extract_log_from_event); this just truncates and buffers."""
        if not line:
            return
        if len(line) > _MAX_LINE_LEN:
            line = line[: _MAX_LINE_LEN - 1] + "…"
        self._pending.append(line)

    def clear(self) -> None:
        self._live_buffer.clear()
        self._history_buffer.clear()
        self._pending.clear()
        self._live_log.clear()
        if self._dialog is not None:
            self._dialog.set_text("")

    def _flush(self) -> None:
        if not self._pending:
            return
        for line in self._pending:
            self._live_buffer.append(line)
            self._history_buffer.append(line)
        self._pending.clear()

        self._live_log.setPlainText("\n".join(self._live_buffer))
        self._scroll_to_bottom(self._live_log)

        if self._dialog is not None and self._dialog.isVisible():
            self._dialog.set_text("\n".join(self._history_buffer))

    @staticmethod
    def _scroll_to_bottom(edit: QPlainTextEdit) -> None:
        cursor = edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        edit.setTextCursor(cursor)

    def _open_dialog(self) -> None:
        if self._dialog is None:
            self._dialog = _TerminalDialog(self)
        self._dialog.set_text("\n".join(self._history_buffer))
        self._dialog.show()
        self._dialog.raise_()
        self._dialog.activateWindow()


class _TerminalDialog(QDialog):
    """Full log view. A plain window (not modal) so the recovery panel behind
    it stays visible and interactive — closing it just hides it."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Robo-Rec — Live Output")
        self.setStyleSheet(_DIALOG_STYLE)
        self.resize(1100, 640)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Live Output")
        title.setObjectName("DialogTitle")
        header.addWidget(title)
        header.addStretch()

        minimize_btn = QPushButton()
        minimize_btn.setObjectName("DialogCloseBtn")
        minimize_btn.setIcon(load_icon("chevron-left", "#c7ccd1", 12))
        minimize_btn.setIconSize(QSize(12, 12))
        minimize_btn.setText(" Minimize")
        minimize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        minimize_btn.clicked.connect(self.hide)
        header.addWidget(minimize_btn)

        layout.addLayout(header)

        self._log = QPlainTextEdit()
        self._log.setObjectName("DialogLog")
        self._log.setReadOnly(True)
        self._log.setFont(QFont(_MONO_FONT_FAMILY, 10))
        self._log.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self._log, stretch=1)

    def set_text(self, text: str) -> None:
        self._log.setPlainText(text)
        cursor = self._log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._log.setTextCursor(cursor)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override
        event.ignore()
        self.hide()


__all__ = ["TerminalSidebar"]
