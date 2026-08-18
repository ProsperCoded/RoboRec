"""SeedTile — the app's signature widget.

Each BIP39 word position is rendered as a small bordered tile, like a physical
letter tile or evidence tag, rather than a row in a generic form. The same
widget is reused across all three action panels: editable with a blank state
for Missing Words, draggable for Scrambled Seed Phrase, and read-only for
Get Wallet from Seed Phrase.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QLineEdit, QSizePolicy, QVBoxLayout, QWidget

BLANK_PLACEHOLDER = "····"


class SeedTile(QWidget):
    """A single seed-word slot: index label over an editable/read-only word field."""

    word_changed = Signal(int, str)

    def __init__(
        self,
        index: int,
        word: str = "",
        *,
        editable: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SeedTile")
        self._index = index
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(84, 52)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        self._index_label = QLabel(f"{index + 1:02d}")
        self._index_label.setObjectName("SeedTileIndex")
        layout.addWidget(self._index_label)

        self._word_field = QLineEdit(word)
        self._word_field.setObjectName("SeedTileWord")
        self._word_field.setPlaceholderText(BLANK_PLACEHOLDER)
        self._word_field.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._word_field.setReadOnly(not editable)
        self._word_field.setFrame(False)
        self._word_field.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._word_field)

        self.set_blank(word == "")

    def _on_text_changed(self, text: str) -> None:
        self.set_blank(text == "")
        self.word_changed.emit(self._index, text)

    @property
    def index(self) -> int:
        return self._index

    def word(self) -> str:
        return self._word_field.text()

    def set_word(self, word: str) -> None:
        self._word_field.setText(word)

    def set_editable(self, editable: bool) -> None:
        self._word_field.setReadOnly(not editable)

    def set_blank(self, is_blank: bool) -> None:
        self.setProperty("blank", "true" if is_blank else "false")
        self.setProperty("filled", "false" if is_blank else "true")
        self.style().unpolish(self)
        self.style().polish(self)
