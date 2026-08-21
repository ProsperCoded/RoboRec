"""CopyButton — a small icon button that copies given text to the clipboard and briefly
shows a checkmark confirmation before reverting to the copy icon.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import QApplication, QPushButton, QWidget

from robo_rec.gui.icons import load_icon
from robo_rec.gui.theme import ACCENT, TEXT_SECONDARY

_CONFIRM_MS = 1500


class CopyButton(QPushButton):
    def __init__(self, text_to_copy: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._text_to_copy = text_to_copy
        self.setObjectName("CopyButton")
        self.setIcon(load_icon("copy", TEXT_SECONDARY, 14))
        self.setIconSize(QSize(14, 14))
        self.setToolTip("Copy to clipboard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(28, 28)
        self.clicked.connect(self._on_clicked)

        self._revert_timer = QTimer(self)
        self._revert_timer.setSingleShot(True)
        self._revert_timer.setInterval(_CONFIRM_MS)
        self._revert_timer.timeout.connect(self._revert_icon)

    def set_text_to_copy(self, text: str) -> None:
        self._text_to_copy = text

    def _on_clicked(self) -> None:
        if not self._text_to_copy:
            return
        QApplication.clipboard().setText(self._text_to_copy)
        self.setIcon(load_icon("check", ACCENT, 14))
        self.setToolTip("Copied!")
        self._revert_timer.start()

    def _revert_icon(self) -> None:
        self.setIcon(load_icon("copy", TEXT_SECONDARY, 14))
        self.setToolTip("Copy to clipboard")
