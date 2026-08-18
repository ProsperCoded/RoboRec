"""Get Wallet from Seed Phrase panel — UI shell only, purely local mock result.

Mirrors PRD 4.4: derive addresses across standard paths, optionally verify
against a target address.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from robo_rec.gui.panels.base_panel import BasePanel
from robo_rec.gui.widgets.seed_row import SeedRow

MOCK_ADDRESS = "1FMHvVtJkJFnSxaN9KUn5q3KtqNwej1sZ6"
MOCK_PRIVATE_KEY = "•" * 52


class DeriveWalletPanel(BasePanel):
    def __init__(self, parent=None) -> None:
        super().__init__(
            "Get Wallet from Seed Phrase",
            "Enter your complete, correctly-ordered phrase to derive its "
            "public address and private key.",
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

        token_group = QGroupBox("Token")
        token_layout = QHBoxLayout(token_group)
        self._token_combo = QComboBox()
        self._token_combo.addItems(["Bitcoin (BTC)", "Ethereum (ETH)", "Other BIP39-compatible"])
        token_layout.addWidget(self._token_combo)
        options_row.addWidget(token_group)

        self.root_layout.addLayout(options_row)

        tiles_label = QLabel("SEED PHRASE")
        tiles_label.setObjectName("SectionLabel")
        self.root_layout.addWidget(tiles_label)

        self._seed_row = SeedRow(length=12, editable=True)
        self.root_layout.addWidget(self._seed_row)

        target_group = QGroupBox("Verify against target address (optional)")
        target_layout = QHBoxLayout(target_group)
        self._address_field = QLineEdit()
        self._address_field.setPlaceholderText("Leave blank to just derive and display")
        target_layout.addWidget(self._address_field)
        self.root_layout.addWidget(target_group)

        self._derive_button = QPushButton("Derive")
        self._derive_button.setObjectName("PrimaryButton")
        self._derive_button.clicked.connect(self._on_derive_clicked)
        self.root_layout.addWidget(self._derive_button)

        self._result_group = QGroupBox("Result (sample — not yet wired to real derivation)")
        result_layout = QVBoxLayout(self._result_group)

        address_row = QHBoxLayout()
        address_row.addWidget(QLabel("Address:"))
        self._address_result = QLabel(MOCK_ADDRESS)
        self._address_result.setObjectName("SeedTileWord")
        address_row.addWidget(self._address_result)
        address_row.addStretch(1)
        result_layout.addLayout(address_row)

        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("Private key:"))
        self._key_result = QLabel(MOCK_PRIVATE_KEY)
        self._key_result.setObjectName("SeedTileWord")
        key_row.addWidget(self._key_result)
        self._reveal_button = QPushButton("Reveal")
        self._reveal_button.clicked.connect(self._on_reveal_clicked)
        key_row.addWidget(self._reveal_button)
        key_row.addStretch(1)
        result_layout.addLayout(key_row)

        self._result_group.setVisible(False)
        self.root_layout.addWidget(self._result_group)

        self.root_layout.addStretch(1)
        self._revealed = False

    def _on_length_changed(self) -> None:
        length = 12 if self._length_combo.currentIndex() == 0 else 24
        self._seed_row.set_length(length)

    def _on_derive_clicked(self) -> None:
        self._result_group.setVisible(True)

    def _on_reveal_clicked(self) -> None:
        self._revealed = not self._revealed
        if self._revealed:
            self._key_result.setText("Kx7f2m9pQ8VnR1TzW6xJhLd3sYb4NcAe5uGoP2iMk9RtFqW8vXzD")
            self._reveal_button.setText("Hide")
        else:
            self._key_result.setText(MOCK_PRIVATE_KEY)
            self._reveal_button.setText("Reveal")
