"""SeedRow — a wrapping grid of SeedTile widgets representing a full mnemonic.

Supports the "paste all known words, leave blanks" interaction from the
Missing Words sketch: pasting a multi-word phrase into any tile distributes
the remaining words across the following tiles, and pressing space/enter/tab
advances focus to the next tile — so a user can paste or type straight
through the whole phrase without touching the mouse.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QWidget

from robo_rec.gui.widgets.seed_tile import SeedTile

TILES_PER_ROW = 6


class SeedRow(QWidget):
    """Lays out `length` SeedTiles in a grid, rebuildable when length changes."""

    words_changed = Signal()

    def __init__(self, length: int = 12, *, editable: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._editable = editable
        self._tiles: list[SeedTile] = []
        self._layout = QGridLayout(self)
        self._layout.setSpacing(8)
        self.set_length(length)

    def set_length(self, length: int) -> None:
        if length == len(self._tiles):
            return
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._tiles = []
        for i in range(length):
            tile = SeedTile(i, editable=self._editable)
            tile.word_changed.connect(lambda *_: self.words_changed.emit())
            tile.paste_overflow.connect(self._on_paste_overflow)
            tile.advance_requested.connect(self._on_advance_requested)
            self._tiles.append(tile)
            self._layout.addWidget(tile, i // TILES_PER_ROW, i % TILES_PER_ROW)
        self.words_changed.emit()

    def tiles(self) -> list[SeedTile]:
        return self._tiles

    def words(self) -> list[str]:
        return [tile.word() for tile in self._tiles]

    def set_words(self, words: list[str]) -> None:
        for tile, word in zip(self._tiles, words, strict=False):
            tile.set_word(word)

    def missing_count(self) -> int:
        return sum(1 for tile in self._tiles if tile.word() == "")

    def focus_first_blank(self) -> None:
        for tile in self._tiles:
            if tile.word() == "":
                tile.focus_word_field()
                return
        if self._tiles:
            self._tiles[0].focus_word_field()

    def _on_paste_overflow(self, index: int, remaining_words: list[str]) -> None:
        for offset, word in enumerate(remaining_words, start=1):
            target_index = index + offset
            if target_index >= len(self._tiles):
                break
            self._tiles[target_index].set_word(word)
        next_index = min(index + len(remaining_words) + 1, len(self._tiles) - 1)
        if 0 <= next_index < len(self._tiles):
            self._tiles[next_index].focus_word_field()

    def _on_advance_requested(self, index: int) -> None:
        next_index = index + 1
        if next_index < len(self._tiles):
            self._tiles[next_index].focus_word_field()
