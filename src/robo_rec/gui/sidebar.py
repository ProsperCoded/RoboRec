"""Sidebar — currently one 'Actions' entry. GPU Status is reached via the top-bar badge,
not a sidebar tab (it's a one-off diagnostics view, not a recovery scenario)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from robo_rec.gui.icons import load_icon
from robo_rec.gui.theme import ACCENT, TEXT_SECONDARY

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

        brand = QLabel()
        brand.setObjectName("SidebarBrand")

        logo_path = Path(__file__).parent / "assets" / "app-icon.svg"
        if logo_path.exists():
            from PySide6.QtSvg import QSvgRenderer
            from PySide6.QtGui import QPainter, QPixmap

            renderer = QSvgRenderer(str(logo_path))
            if renderer.isValid():
                size = 36
                pixmap = QPixmap(size, size)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                brand.setPixmap(pixmap)
        else:
            brand.setText("ROBO-REC")
        layout.addWidget(brand)

        layout.addSpacing(20)

        nav_label = QLabel("NAVIGATION")
        nav_label.setObjectName("SectionLabel")
        layout.addWidget(nav_label)
        layout.addSpacing(4)

        self._icon_active = load_icon("flag", ACCENT, 16)
        self._icon_inactive = load_icon("flag", TEXT_SECONDARY, 16)

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
        layout.addWidget(self._actions_tab)

        layout.addStretch(1)

    def set_active(self, active: bool) -> None:
        self._actions_tab.setChecked(active)
        self._actions_tab.setIcon(self._icon_active if active else self._icon_inactive)
