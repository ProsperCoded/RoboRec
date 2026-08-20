"""SeedTile — the app's signature widget.

Each BIP39 word position is rendered as a small bordered tile, like a physical
letter tile or evidence tag, rather than a row in a generic form. The same
widget is reused across all three action panels: editable with a blank state
for Missing Words, draggable for Scrambled Seed Phrase, and read-only for
Get Wallet from Seed Phrase.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from robo_rec.gui.icons import load_icon
from robo_rec.gui.theme import ACCENT, TEXT_MUTED

BLANK_PLACEHOLDER = "····"


class _WordField(QLineEdit):
    """QLineEdit that splits a multi-word paste across sibling SeedTiles."""

    paste_overflow = Signal(int, list)
    advance_requested = Signal(int)

    def __init__(self, index: int, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._index = index

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.advance_requested.emit(self._index)
            if event.key() != Qt.Key.Key_Tab:
                return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source) -> None:
        text = source.text() if source.hasText() else ""
        words = text.split()
        if len(words) <= 1:
            super().insertFromMimeData(source)
            return
        self.setText(words[0])
        self.paste_overflow.emit(self._index, words[1:])


class SeedTile(QWidget):
    """A single seed-word slot: index label over an editable/read-only word field.

    When lockable=True (used by the Rearrange panel's 24-word known-correct-segment case),
    a small lock toggle appears next to the index, letting the user mark this tile as
    "this word is definitely in this position" vs. the default "somewhere in the scrambled
    group". Locked state has no effect for panels that don't opt into it.
    """

    word_changed = Signal(int, str)
    paste_overflow = Signal(int, list)
    advance_requested = Signal(int)
    lock_toggled = Signal(int, bool)

    def __init__(
        self,
        index: int,
        word: str = "",
        *,
        editable: bool = True,
        lockable: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SeedTile")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._index = index
        self._locked = False
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(112, 52)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(4)
        self._index_label = QLabel(f"{index + 1:02d}")
        self._index_label.setObjectName("SeedTileIndex")
        header_row.addWidget(self._index_label)
        header_row.addStretch(1)

        self._lock_button: QPushButton | None = None
        if lockable:
            self._lock_button = QPushButton()
            self._lock_button.setObjectName("SeedTileLockButton")
            self._lock_button.setIcon(load_icon("lock-open", TEXT_MUTED, 12))
            self._lock_button.setIconSize(QSize(12, 12))
            self._lock_button.setFlat(True)
            self._lock_button.setFixedSize(16, 16)
            self._lock_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self._lock_button.setToolTip("Mark this word as definitely in this position")
            self._lock_button.clicked.connect(self._on_lock_clicked)
            header_row.addWidget(self._lock_button)
        layout.addLayout(header_row)

        self._word_field = _WordField(index, word)
        self._word_field.setObjectName("SeedTileWord")
        self._word_field.setPlaceholderText(BLANK_PLACEHOLDER)
        self._word_field.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._word_field.setReadOnly(not editable)
        self._word_field.setFrame(False)
        self._word_field.textChanged.connect(self._on_text_changed)
        self._word_field.paste_overflow.connect(self.paste_overflow.emit)
        self._word_field.advance_requested.connect(self.advance_requested.emit)
        layout.addWidget(self._word_field)

        self.set_blank(word == "")

    def _on_text_changed(self, text: str) -> None:
        self.set_blank(text == "")
        self.word_changed.emit(self._index, text)

    def _on_lock_clicked(self) -> None:
        self.set_locked(not self._locked)
        self.lock_toggled.emit(self._index, self._locked)

    @property
    def index(self) -> int:
        return self._index

    def word(self) -> str:
        return self._word_field.text()

    def set_word(self, word: str) -> None:
        self._word_field.setText(word)

    def set_editable(self, editable: bool) -> None:
        self._word_field.setReadOnly(not editable)

    def is_locked(self) -> bool:
        return self._locked

    def set_locked(self, locked: bool) -> None:
        self._locked = locked
        if self._lock_button is not None:
            icon_name = "lock" if locked else "lock-open"
            icon_color = ACCENT if locked else TEXT_MUTED
            self._lock_button.setIcon(load_icon(icon_name, icon_color, 12))
        self.setProperty("locked", "true" if locked else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def set_blank(self, is_blank: bool) -> None:
        self.setProperty("blank", "true" if is_blank else "false")
        self.setProperty("filled", "false" if is_blank else "true")
        self.style().unpolish(self)
        self.style().polish(self)

    def focus_word_field(self) -> None:
        self._word_field.setFocus()
        self._word_field.selectAll()
