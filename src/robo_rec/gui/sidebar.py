"""Sidebar — 'Actions' (dashboard) and 'GPU Status' nav entries."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QLabel, QPushButton, QVBoxLayout, QWidget

from robo_rec.gui.icons import load_icon
from robo_rec.gui.theme import ACCENT, TEXT_SECONDARY

SIDEBAR_WIDTH = 200


class Sidebar(QWidget):
    actions_requested = Signal()
    gpu_status_requested = Signal()

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

        self._icon_active = load_icon("flag", ACCENT, 16)
        self._icon_inactive = load_icon("flag", TEXT_SECONDARY, 16)
        self._gpu_icon_active = load_icon("cpu", ACCENT, 16)
        self._gpu_icon_inactive = load_icon("cpu", TEXT_SECONDARY, 16)

        nav_group = QButtonGroup(self)
        nav_group.setExclusive(True)

        self._actions_tab = QPushButton("  Actions")
        self._actions_tab.setObjectName("SidebarNavItem")
        self._actions_tab.setIcon(self._icon_active)
        self._actions_tab.setIconSize(QSize(16, 16))
        self._actions_tab.setCheckable(True)
        self._actions_tab.setChecked(True)
        self._actions_tab.setFixedHeight(40)
        self._actions_tab.setCursor(Qt.CursorShape.PointingHandCursor)
        self._actions_tab.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self._actions_tab.clicked.connect(self.actions_requested.emit)
        nav_group.addButton(self._actions_tab)
        layout.addWidget(self._actions_tab)

        self._gpu_status_tab = QPushButton("  GPU Status")
        self._gpu_status_tab.setObjectName("SidebarNavItem")
        self._gpu_status_tab.setIcon(self._gpu_icon_inactive)
        self._gpu_status_tab.setIconSize(QSize(16, 16))
        self._gpu_status_tab.setCheckable(True)
        self._gpu_status_tab.setFixedHeight(40)
        self._gpu_status_tab.setCursor(Qt.CursorShape.PointingHandCursor)
        self._gpu_status_tab.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self._gpu_status_tab.clicked.connect(self.gpu_status_requested.emit)
        nav_group.addButton(self._gpu_status_tab)
        layout.addWidget(self._gpu_status_tab)

        layout.addStretch(1)

    def set_active(self, active: str) -> None:
        """active is 'actions' or 'gpu_status'."""
        is_actions = active == "actions"
        self._actions_tab.setChecked(is_actions)
        self._actions_tab.setIcon(self._icon_active if is_actions else self._icon_inactive)
        is_gpu = active == "gpu_status"
        self._gpu_status_tab.setChecked(is_gpu)
        self._gpu_status_tab.setIcon(self._gpu_icon_active if is_gpu else self._gpu_icon_inactive)
