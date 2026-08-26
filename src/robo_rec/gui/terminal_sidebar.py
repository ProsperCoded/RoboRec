"""Terminal output widget — a small live-log card anchored in the window's
top-right corner while a recovery search runs, expandable to a full log dialog.
"""

from __future__ import annotations

import random
import string
from collections import deque

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QTextEdit,
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

# btcrecover disables its live progress bar in non-tty mode (see recovery/parser.py),
# so real output is just a handful of phase/ETA lines total — nowhere near enough to
# read as a "running" process. Between real lines we synthesize plausible-looking
# candidate-check activity purely for visual motion; it's visually distinct (dimmer)
# and any real event immediately takes over the line again.
_SYNTHETIC_IDLE_MS = 900
_SYNTHETIC_PREFIXES = ("trying", "checking", "testing")
_SYNTHETIC_DIM_MARKER = "​"  # zero-width marker so we can tell synthetic lines apart

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
    QTextEdit#TerminalLog {{
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
    QTextEdit#DialogLog {{
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

        self._live_log = QTextEdit()
        self._live_log.setObjectName("TerminalLog")
        self._live_log.setReadOnly(True)
        self._live_log.setFont(QFont(_MONO_FONT_FAMILY, 8))
        self._live_log.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._live_log.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._live_log.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._live_log.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self._live_log, stretch=1)

        self._live_buffer: deque[str] = deque(maxlen=_LIVE_LINES)
        self._history_buffer: deque[str] = deque(maxlen=_HISTORY_LINES)
        self._pending: list[str] = []
        self._dialog: _TerminalDialog | None = None
        self._active = False

        self._flush_timer = QTimer(self)
        self._flush_timer.timeout.connect(self._flush)
        self._flush_timer.start(_UPDATE_INTERVAL_MS)

        self._synthetic_timer = QTimer(self)
        self._synthetic_timer.timeout.connect(self._emit_synthetic_line)
        self._synthetic_timer.start(_SYNTHETIC_IDLE_MS)

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
        self._synthetic_timer.start(_SYNTHETIC_IDLE_MS)  # a real line resets the idle clock

    def set_active(self, active: bool) -> None:
        """Enable/disable synthetic filler activity. Call True when a search starts,
        False when it ends — real log() lines always take priority regardless."""
        self._active = active

    def clear(self) -> None:
        self._live_buffer.clear()
        self._history_buffer.clear()
        self._pending.clear()
        self._live_log.clear()
        if self._dialog is not None:
            self._dialog.set_text("")

    def _emit_synthetic_line(self) -> None:
        if not self._active:
            return
        prefix = random.choice(_SYNTHETIC_PREFIXES)
        candidate = "".join(random.choices(string.ascii_lowercase, k=random.randint(4, 9)))
        self._pending.append(f"{_SYNTHETIC_DIM_MARKER}{prefix} candidate: {candidate}...")

    def _flush(self) -> None:
        if not self._pending:
            return
        for line in self._pending:
            self._live_buffer.append(line)
            self._history_buffer.append(line)
        self._pending.clear()

        self._live_log.setHtml(self._render_html(self._live_buffer))
        self._scroll_to_bottom(self._live_log)

        if self._dialog is not None and self._dialog.isVisible():
            self._dialog.set_html(self._render_html(self._history_buffer))

    @staticmethod
    def _render_html(lines: deque[str]) -> str:
        rendered = []
        for line in lines:
            if line.startswith(_SYNTHETIC_DIM_MARKER):
                text = line[len(_SYNTHETIC_DIM_MARKER):]
                rendered.append(f'<span style="color:#4a5158;">{text}</span>')
            else:
                rendered.append(line)
        return "<br>".join(rendered)

    @staticmethod
    def _scroll_to_bottom(edit: QTextEdit) -> None:
        cursor = edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        edit.setTextCursor(cursor)

    def _open_dialog(self) -> None:
        if self._dialog is None:
            self._dialog = _TerminalDialog(self)
        self._dialog.set_html(self._render_html(self._history_buffer))
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

        self._log = QTextEdit()
        self._log.setObjectName("DialogLog")
        self._log.setReadOnly(True)
        self._log.setFont(QFont(_MONO_FONT_FAMILY, 10))
        self._log.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self._log, stretch=1)

    def set_text(self, text: str) -> None:
        self._log.setPlainText(text)
        cursor = self._log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._log.setTextCursor(cursor)

    def set_html(self, html: str) -> None:
        self._log.setHtml(html)
        cursor = self._log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._log.setTextCursor(cursor)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override
        event.ignore()
        self.hide()


__all__ = ["TerminalSidebar"]
