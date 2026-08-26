"""Live terminal output sidebar with expandable log panel."""

from __future__ import annotations

from collections import deque
from PySide6.QtCore import Qt, QTimer, Signal, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPlainTextEdit, QPushButton, QFrame, QHBoxLayout
)
from PySide6.QtGui import QFont, QColor, QIcon


class TerminalSidebar(QFrame):
    """Live terminal output display with expandable history panel."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            TerminalSidebar {
                background-color: #1e1e1e;
                border-left: 1px solid #333;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar with expand/minimize buttons
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(8, 8, 8, 8)

        # Title
        title = QLabel("Output")
        title.setStyleSheet("color: #aaa; font-weight: bold; font-size: 11px;")
        top_bar.addWidget(title)
        top_bar.addStretch()

        # Expand/collapse button
        self.expand_btn = QPushButton("▼")
        self.expand_btn.setFixedSize(24, 24)
        self.expand_btn.setFlat(True)
        self.expand_btn.setToolTip("Expand to see full history")
        self.expand_btn.setStyleSheet("""
            QPushButton {
                color: #888;
                font-weight: bold;
                border: none;
                padding: 0px;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #0f0;
            }
        """)
        self.expand_btn.clicked.connect(self.toggle_expand)

        # Minimize button (only visible when expanded)
        self.minimize_btn = QPushButton("✕")
        self.minimize_btn.setFixedSize(24, 24)
        self.minimize_btn.setFlat(True)
        self.minimize_btn.setToolTip("Collapse panel")
        self.minimize_btn.setVisible(False)
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                color: #888;
                font-weight: bold;
                border: none;
                padding: 0px;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #f44;
            }
        """)
        self.minimize_btn.clicked.connect(self.collapse)

        top_bar.addWidget(self.expand_btn)
        top_bar.addWidget(self.minimize_btn)

        layout.addLayout(top_bar)

        # Live output display (always visible)
        self.live_display = QPlainTextEdit()
        self.live_display.setReadOnly(True)
        self.live_display.setMaximumHeight(120)
        self.live_display.setFont(QFont("Courier", 9))
        self.live_display.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                border: none;
                padding: 4px;
                margin: 0px;
            }
        """)
        layout.addWidget(self.live_display)

        # Expandable history panel (fills remaining space when expanded)
        self.history_panel = QFrame()
        self.history_panel.setMaximumHeight(0)  # Start collapsed
        self.history_panel.setMinimumHeight(0)
        self.history_panel.setStyleSheet("""
            QFrame {
                background-color: #0d0d0d;
                border-top: 1px solid #333;
            }
        """)

        history_layout = QVBoxLayout(self.history_panel)
        history_layout.setContentsMargins(0, 0, 0, 0)

        self.history_display = QPlainTextEdit()
        self.history_display.setReadOnly(True)
        self.history_display.setFont(QFont("Courier", 8))
        self.history_display.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0d0d0d;
                color: #666;
                border: none;
                padding: 4px;
                margin: 0px;
            }
        """)
        history_layout.addWidget(self.history_display)
        layout.addWidget(self.history_panel)

        layout.addStretch()

        # Animation for expand/collapse
        self.expand_anim = QPropertyAnimation(self.history_panel, b"maximumHeight")
        self.expand_anim.setDuration(300)
        self.expand_anim.setEasingCurve(QEasingCurve.InOutQuad)

        # State
        self.is_expanded = False
        self.live_buffer = deque(maxlen=15)  # Last 15 lines for live view
        self.history_buffer = deque(maxlen=500)  # Last 500 lines for history
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._flush_live_display)
        self.update_timer.start(300)  # 300ms throttle

        self.pending_lines = []  # Batch updates

    def log(self, line: str, level: str = "info") -> None:
        """Add a log line. Filtering happens here."""
        # Filter: only show essential levels
        if level not in ("info", "warn", "error", "progress", "found"):
            return

        # Truncate long lines
        if len(line) > 100:
            line = line[:97] + "..."

        self.pending_lines.append(line)
        self.history_buffer.append(line)

    def _flush_live_display(self) -> None:
        """Flush pending lines to display (called every 300ms)."""
        if not self.pending_lines:
            return

        for line in self.pending_lines:
            self.live_buffer.append(line)

        self.pending_lines.clear()

        # Update live display
        text = '\n'.join(self.live_buffer)
        self.live_display.setPlainText(text)

        # Scroll to bottom
        cursor = self.live_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.live_display.setTextCursor(cursor)

        # Update history if expanded
        if self.is_expanded:
            self._update_history_display()

    def _update_history_display(self) -> None:
        """Update the history panel (called when expanded or when history changes)."""
        text = '\n'.join(self.history_buffer)
        self.history_display.setPlainText(text)

        # Scroll to bottom
        cursor = self.history_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.history_display.setTextCursor(cursor)

    def toggle_expand(self) -> None:
        """Expand/collapse the history panel with animation."""
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self) -> None:
        """Expand to show full history panel."""
        if self.is_expanded:
            return

        self.expand_anim.setStartValue(0)
        self.expand_anim.setEndValue(2000)  # Fill most of screen
        self.expand_btn.setText("▲")
        self.expand_btn.setToolTip("Collapse")
        self.minimize_btn.setVisible(True)
        self._update_history_display()
        self.expand_anim.start()
        self.is_expanded = True

    def collapse(self) -> None:
        """Collapse to show only live panel."""
        if not self.is_expanded:
            return

        self.expand_anim.setStartValue(self.history_panel.maximumHeight())
        self.expand_anim.setEndValue(0)
        self.expand_btn.setText("▼")
        self.expand_btn.setToolTip("Expand to see full history")
        self.minimize_btn.setVisible(False)
        self.expand_anim.start()
        self.is_expanded = False

    def clear(self) -> None:
        """Clear all logs."""
        self.live_buffer.clear()
        self.history_buffer.clear()
        self.pending_lines.clear()
        self.live_display.clear()
        self.history_display.clear()


__all__ = ["TerminalSidebar"]
