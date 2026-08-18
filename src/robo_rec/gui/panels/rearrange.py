"""Scrambled Seed Phrase panel — UI shell only, no subprocess wiring yet.

Mirrors PRD 4.1: 12-word full rearrangement is supported; for 24-word
phrases only a scrambled sub-segment (with a known-correct remainder) is
supported — full 24-word rearrangement is infeasible (24!).
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
)

from robo_rec.gui.panels.base_panel import BasePanel
from robo_rec.gui.widgets.seed_row import SeedRow


class RearrangePanel(BasePanel):
    def __init__(self, parent=None) -> None:
        super().__init__(
            "Scrambled Seed Phrase",
            "Enter the words in any order you remember them. Robo-Rec will "
            "search for the arrangement that produces a valid phrase.",
            parent,
        )

        options_row = QHBoxLayout()
        options_row.setSpacing(16)

        length_group = QGroupBox("Phrase length")
        length_layout = QHBoxLayout(length_group)
        self._length_combo = QComboBox()
        self._length_combo.addItems(["12 words", "24 words"])
        self._length_combo.currentIndexChanged.connect(self._on_length_changed)
        length_layout.addWidget(self._length_combo)
        options_row.addWidget(length_group)

        self._segment_group = QGroupBox("Known-correct segment (24-word only)")
        segment_layout = QHBoxLayout(self._segment_group)
        segment_layout.addWidget(QLabel("Scrambled word count:"))
        self._segment_spin = QSpinBox()
        self._segment_spin.setRange(2, 12)
        self._segment_spin.setValue(12)
        segment_layout.addWidget(self._segment_spin)
        self._segment_group.setVisible(False)
        options_row.addWidget(self._segment_group)

        self.root_layout.addLayout(options_row)

        self._infeasible_notice = QLabel(
            "Full 24-word rearrangement (all positions unknown) is not "
            "supported — 24! is computationally infeasible. Identify a "
            "known-correct segment above to narrow the search."
        )
        self._infeasible_notice.setObjectName("WarningNotice")
        self._infeasible_notice.setWordWrap(True)
        self._infeasible_notice.hide()
        self.root_layout.addWidget(self._infeasible_notice)

        tiles_label = QLabel("WORDS IN ANY ORDER")
        tiles_label.setObjectName("SectionLabel")
        self.root_layout.addWidget(tiles_label)

        self._seed_row = SeedRow(length=12, editable=True)
        self.root_layout.addWidget(self._seed_row)

        self._start_button = QPushButton("Start Rearrangement")
        self._start_button.setObjectName("PrimaryButton")
        self._start_button.setEnabled(False)
        self._start_button.setToolTip("Not wired up yet — coming in a later pass")
        self.root_layout.addWidget(self._start_button)

        self.root_layout.addStretch(1)

    def _on_length_changed(self) -> None:
        is_24 = self._length_combo.currentIndex() == 1
        length = 24 if is_24 else 12
        self._seed_row.set_length(length)
        self._segment_group.setVisible(is_24)
        self._infeasible_notice.setVisible(is_24)
