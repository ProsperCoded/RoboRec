"""BasePanel — shared header + back-to-dashboard breadcrumb for action panels."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class BasePanel(QWidget):
    back_requested = Signal()

    def __init__(self, title: str, subtitle: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(32, 24, 32, 28)
        self.root_layout.setSpacing(18)

        breadcrumb = QPushButton("← Back to Actions")
        breadcrumb.setObjectName("BreadcrumbButton")
        breadcrumb.setFlat(True)
        breadcrumb.setCursor(self.cursor())
        breadcrumb.clicked.connect(self.back_requested.emit)
        self.root_layout.addWidget(breadcrumb)

        header = QLabel(title)
        header.setObjectName("PanelHeader")
        self.root_layout.addWidget(header)

        sub = QLabel(subtitle)
        sub.setObjectName("PanelSubtitle")
        sub.setWordWrap(True)
        self.root_layout.addWidget(sub)
