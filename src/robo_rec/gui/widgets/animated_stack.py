"""AnimatedStackedWidget — QStackedWidget with a cross-fade between pages."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QStackedWidget, QWidget

FADE_DURATION_MS = 180


class AnimatedStackedWidget(QStackedWidget):
    """Fades the incoming page in when the current index changes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._effect: QGraphicsOpacityEffect | None = None
        self._animation: QPropertyAnimation | None = None

    def setCurrentIndex(self, index: int) -> None:
        if index == self.currentIndex():
            return
        super().setCurrentIndex(index)
        self._fade_in_current()

    def setCurrentWidget(self, widget: QWidget) -> None:
        if widget is self.currentWidget():
            return
        super().setCurrentWidget(widget)
        self._fade_in_current()

    def _fade_in_current(self) -> None:
        page = self.currentWidget()
        if page is None:
            return
        effect = QGraphicsOpacityEffect(page)
        page.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(FADE_DURATION_MS)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(lambda: page.setGraphicsEffect(None))
        # Keep references alive until the animation finishes.
        self._effect = effect
        self._animation = animation
        animation.start()
