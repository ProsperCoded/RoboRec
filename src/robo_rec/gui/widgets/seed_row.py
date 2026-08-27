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
    locks_changed = Signal()
    # Emitted with the full pasted word list when it has more words than the row
    # currently has tiles for (e.g. a 24-word phrase pasted while set to 12 words).
    # Panels connect this to grow their length setting and re-run paste_all().
    length_exceeded = Signal(list)

    def __init__(
        self,
        length: int = 12,
        *,
        editable: bool = True,
        lockable: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._editable = editable
        self._lockable = lockable
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
            tile = SeedTile(i, editable=self._editable, lockable=self._lockable)
            tile.word_changed.connect(lambda *_: self.words_changed.emit())
            tile.paste_overflow.connect(self._on_paste_overflow)
            tile.advance_requested.connect(self._on_advance_requested)
            tile.lock_toggled.connect(lambda *_: self.locks_changed.emit())
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

    def locked_indices(self) -> list[int]:
        return [tile.index for tile in self._tiles if tile.is_locked()]

    def set_all_locked(self, locked: bool) -> None:
        for tile in self._tiles:
            tile.set_locked(locked)
        self.locks_changed.emit()

    def focus_first_blank(self) -> None:
        for tile in self._tiles:
            if tile.word() == "":
                tile.focus_word_field()
                return
        if self._tiles:
            self._tiles[0].focus_word_field()

    def paste_all(self, words: list[str]) -> None:
        """Fill tiles from `words` starting at index 0, focusing the tile after the
        last word placed (or the last tile, if the phrase fills the row)."""
        for i, word in enumerate(words):
            if i >= len(self._tiles):
                break
            self._tiles[i].set_word(word)
        next_index = min(len(words), len(self._tiles) - 1)
        if 0 <= next_index < len(self._tiles):
            self._tiles[next_index].focus_word_field()

    def _on_paste_overflow(self, index: int, remaining_words: list[str]) -> None:
        total_pasted = index + 1 + len(remaining_words)
        if total_pasted > len(self._tiles):
            # Doesn't fit at the current length (e.g. a 24-word phrase pasted while
            # still set to 12 words) — surface the words already in earlier tiles
            # plus the whole paste, so the panel can grow the row and redo the paste
            # from position 0, rather than silently truncating the phrase.
            words_before = [tile.word() for tile in self._tiles[:index]]
            pasted_words = [*words_before, self._tiles[index].word(), *remaining_words]
            self.length_exceeded.emit(pasted_words)
            return
        for offset, word in enumerate(remaining_words, start=1):
            target_index = index + offset
            self._tiles[target_index].set_word(word)
        next_index = min(index + len(remaining_words) + 1, len(self._tiles) - 1)
        if 0 <= next_index < len(self._tiles):
            self._tiles[next_index].focus_word_field()

    def _on_advance_requested(self, index: int) -> None:
        next_index = index + 1
        if next_index < len(self._tiles):
            self._tiles[next_index].focus_word_field()
