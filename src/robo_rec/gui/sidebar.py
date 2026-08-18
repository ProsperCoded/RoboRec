"""Sidebar — currently one 'Actions' entry, built to hold more nav items later."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

SIDEBAR_WIDTH = 200


class Sidebar(QWidget):
    actions_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 16)
        layout.setSpacing(4)

        brand = QLabel("ROBO-REC")
        brand.setObjectName("SidebarBrand")
        layout.addWidget(brand)

        layout.addSpacing(20)

        nav_label = QLabel("NAVIGATION")
        nav_label.setObjectName("SectionLabel")
        layout.addWidget(nav_label)
        layout.addSpacing(4)

        self._actions_tab = QPushButton("  ⚑   Actions")
        self._actions_tab.setObjectName("SidebarNavItem")
        self._actions_tab.setCheckable(True)
        self._actions_tab.setChecked(True)
        self._actions_tab.setFixedHeight(40)
        self._actions_tab.setCursor(Qt.CursorShape.PointingHandCursor)
        self._actions_tab.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self._actions_tab.clicked.connect(self.actions_requested.emit)
        layout.addWidget(self._actions_tab)

        layout.addStretch(1)

    def set_active(self, active: bool) -> None:
        self._actions_tab.setChecked(active)
