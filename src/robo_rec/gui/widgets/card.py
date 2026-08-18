"""ActionCard — a clickable dashboard tile for one supported action."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget


class ActionCard(QWidget):
    """A single selectable action on the dashboard (Missing Words, etc.)."""

    clicked = Signal()

    def __init__(
        self,
        glyph: str,
        title: str,
        description: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("ActionCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(150)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        glyph_label = QLabel(glyph)
        glyph_label.setObjectName("CardGlyph")
        layout.addWidget(glyph_label)

        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setObjectName("CardDescription")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addStretch(1)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
