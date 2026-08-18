"""Sidebar — a single 'Actions' tab that opens the dashboard.

Per the sketch: not a multi-item nav menu, just one labeled vertical tab.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

SIDEBAR_WIDTH = 64


class Sidebar(QWidget):
    actions_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(8)

        self._actions_tab = QPushButton("A\nC\nT\nI\nO\nN\nS")
        self._actions_tab.setObjectName("SidebarActionsTab")
        self._actions_tab.setCheckable(True)
        self._actions_tab.setChecked(True)
        self._actions_tab.setFixedHeight(220)
        self._actions_tab.clicked.connect(self.actions_requested.emit)
        layout.addWidget(self._actions_tab, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addStretch(1)

    def set_active(self, active: bool) -> None:
        self._actions_tab.setChecked(active)
