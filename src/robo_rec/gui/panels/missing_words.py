"""Missing Words panel — UI shell only, no subprocess wiring yet.

Mirrors PRD 4.2: known positions support 1-4 missing words; unknown positions
support only 1-2 (combinatorics make 3+ unknown-position infeasible).
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from robo_rec.gui.panels.base_panel import BasePanel
from robo_rec.gui.widgets.seed_row import SeedRow

KNOWN_POSITION_WARNINGS = {
    3: "3 missing words (known positions) can take hours; faster with a GPU.",
    4: "4 missing words (known positions) may take hours to days. GPU is "
    "strongly recommended before starting.",
}
UNKNOWN_POSITION_MAX = 2


class MissingWordsPanel(BasePanel):
    def __init__(self, parent=None) -> None:
        super().__init__(
            "Missing Words",
            "Mark each blank position, then let Robo-Rec search the "
            "remaining words to fill them in.",
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

        position_group = QGroupBox("Blank position(s)")
        position_layout = QVBoxLayout(position_group)
        self._known_radio = QRadioButton("Known — I know which word(s) are blank")
        self._known_radio.setChecked(True)
        self._unknown_radio = QRadioButton("Unknown — I'm not sure which position(s)")
        self._known_radio.toggled.connect(self._on_position_mode_changed)
        position_layout.addWidget(self._known_radio)
        position_layout.addWidget(self._unknown_radio)
        options_row.addWidget(position_group)

        count_group = QGroupBox("Missing word count")
        count_layout = QHBoxLayout(count_group)
        self._count_combo = QComboBox()
        self._count_combo.addItems(["1", "2", "3", "4"])
        self._count_combo.currentIndexChanged.connect(self._on_count_changed)
        count_layout.addWidget(self._count_combo)
        options_row.addWidget(count_group)

        self.root_layout.addLayout(options_row)

        self._warning_label = QLabel()
        self._warning_label.setObjectName("WarningNotice")
        self._warning_label.setWordWrap(True)
        self._warning_label.hide()
        self.root_layout.addWidget(self._warning_label)

        tiles_label = QLabel("PHRASE — LEAVE BLANK POSITIONS EMPTY")
        tiles_label.setObjectName("SectionLabel")
        self.root_layout.addWidget(tiles_label)

        self._seed_row = SeedRow(length=12, editable=True)
        self.root_layout.addWidget(self._seed_row)

        target_group = QGroupBox("Verification target (optional)")
        target_form = QFormLayout(target_group)
        self._wallet_type_combo = QComboBox()
        self._wallet_type_combo.addItems(["Bitcoin (BIP39)", "Ethereum", "Other BIP39-compatible"])
        target_form.addRow("Wallet type", self._wallet_type_combo)
        self._address_field = QLineEdit()
        self._address_field.setPlaceholderText("Known address to verify against (optional)")
        target_form.addRow("Target address", self._address_field)
        self.root_layout.addWidget(target_group)

        self._start_button = QPushButton("Start Recovery")
        self._start_button.setObjectName("PrimaryButton")
        self._start_button.setEnabled(False)
        self._start_button.setToolTip("Not wired up yet — coming in a later pass")
        self.root_layout.addWidget(self._start_button)

        self.root_layout.addStretch(1)
        self._on_position_mode_changed()

    def _on_length_changed(self) -> None:
        length = 12 if self._length_combo.currentIndex() == 0 else 24
        self._seed_row.set_length(length)

    def _on_position_mode_changed(self) -> None:
        is_unknown = self._unknown_radio.isChecked()
        self._count_combo.clear()
        max_count = UNKNOWN_POSITION_MAX if is_unknown else 4
        self._count_combo.addItems([str(n) for n in range(1, max_count + 1)])
        self._on_count_changed()

    def _on_count_changed(self) -> None:
        count_text = self._count_combo.currentText()
        count = int(count_text) if count_text else 1
        warning = KNOWN_POSITION_WARNINGS.get(count) if self._known_radio.isChecked() else None
        if warning:
            self._warning_label.setText(warning)
            self._warning_label.show()
        else:
            self._warning_label.hide()
