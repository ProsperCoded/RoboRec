"""SeedRow — a wrapping grid of SeedTile widgets representing a full mnemonic."""

from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QWidget

from robo_rec.gui.widgets.seed_tile import SeedTile

TILES_PER_ROW = 6


class SeedRow(QWidget):
    """Lays out `length` SeedTiles in a grid, rebuildable when length changes."""

    def __init__(self, length: int = 12, *, editable: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._editable = editable
        self._tiles: list[SeedTile] = []
        self._layout = QGridLayout(self)
        self._layout.setSpacing(8)
        self.set_length(length)

    def set_length(self, length: int) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._tiles = []
        for i in range(length):
            tile = SeedTile(i, editable=self._editable)
            self._tiles.append(tile)
            self._layout.addWidget(tile, i // TILES_PER_ROW, i % TILES_PER_ROW)

    def tiles(self) -> list[SeedTile]:
        return self._tiles

    def words(self) -> list[str]:
        return [tile.word() for tile in self._tiles]

    def set_words(self, words: list[str]) -> None:
        for tile, word in zip(self._tiles, words, strict=False):
            tile.set_word(word)
