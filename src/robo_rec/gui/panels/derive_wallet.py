"""Get Wallet from Seed Phrase panel — wired to robo_rec.derivation.

Mirrors PRD 4.4: derive addresses across standard paths, optionally verify
against a target address. No private key is ever derived or displayed —
PRD 4.4 only specifies address derivation/verification.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from robo_rec.derivation import derive_addresses, verify_address
from robo_rec.gui.coin_options import COIN_OPTION_LABELS, UNSUPPORTED_COIN_MESSAGE, coin_for_label
from robo_rec.gui.panels.base_panel import BasePanel
from robo_rec.gui.widgets.copy_button import CopyButton
from robo_rec.gui.widgets.seed_row import SeedRow
from robo_rec.util.mnemonic import is_valid_mnemonic


class DeriveWalletPanel(BasePanel):
    def __init__(self, parent=None) -> None:
        super().__init__(
            "Get Wallet from Seed Phrase",
            "Enter your complete, correctly-ordered phrase to derive its public address.",
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
        self._token_combo.addItems(list(COIN_OPTION_LABELS))
        token_layout.addWidget(self._token_combo)
        options_row.addWidget(token_group)

        self.root_layout.addLayout(options_row)

        tiles_label = QLabel("SEED PHRASE")
        tiles_label.setObjectName("SectionLabel")
        self.root_layout.addWidget(tiles_label)

        self._seed_row = SeedRow(length=12, editable=True)
        self._seed_row.length_exceeded.connect(self._on_seed_row_length_exceeded)
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

        self._result_group = QGroupBox("Derived addresses")
        self._result_layout = QVBoxLayout(self._result_group)
        self._result_group.setVisible(False)
        self.root_layout.addWidget(self._result_group)

        self.root_layout.addStretch(1)

    def _on_length_changed(self) -> None:
        length = 12 if self._length_combo.currentIndex() == 0 else 24
        self._seed_row.set_length(length)

    def _on_seed_row_length_exceeded(self, words: list[str]) -> None:
        """A paste had more words than the row currently fits — grow to 24 words
        (the only longer supported length) and re-run the paste at the new size."""
        if len(words) <= 12 or self._length_combo.currentIndex() == 1:
            return
        self._length_combo.setCurrentIndex(1)  # triggers _on_length_changed -> set_length(24)
        self._seed_row.paste_all(words)

    def _on_derive_clicked(self) -> None:
        words = self._seed_row.words()
        if any(not w for w in words):
            QMessageBox.warning(
                self,
                "Complete phrase required",
                "Derivation needs every word filled in — this panel is for complete, "
                "correctly-ordered phrases. Use Missing Words or Scrambled Seed Phrase "
                "first if the phrase isn't complete yet.",
            )
            return

        mnemonic = " ".join(words)
        if not is_valid_mnemonic(mnemonic):
            QMessageBox.warning(
                self,
                "Invalid phrase",
                "This phrase doesn't pass BIP39 checksum validation — check for typos, "
                "or use the Missing Words / Scrambled Seed Phrase tools if you're not "
                "certain it's correct.",
            )
            return

        coin = coin_for_label(self._token_combo.currentText())
        if coin is None:
            QMessageBox.warning(self, "Unsupported token", UNSUPPORTED_COIN_MESSAGE)
            return

        target = self._address_field.text().strip()

        self._clear_results()

        if target:
            match = verify_address(mnemonic, target, coin=coin)
            if match is not None:
                self._add_result_row(
                    f"✓ Verified match — {match.wallet_software_label}",
                    match.address,
                    match.derivation_path,
                )
            else:
                self._add_result_row(
                    "✗ No match found in the standard address range for this token",
                    target,
                    None,
                )
        else:
            for derived in derive_addresses(mnemonic, coin=coin):
                self._add_result_row(derived.wallet_software_label, derived.address, derived.derivation_path)

        self._result_group.setVisible(True)

    def _clear_results(self) -> None:
        """Removes every previous result row. Each row is a QWidget (see
        _add_result_row), so takeAt(0).widget() reliably catches it — a bare
        sub-layout wouldn't be, and its child widgets would leak on screen
        underneath the next derive's results."""
        while self._result_layout.count():
            item = self._result_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _add_result_row(self, label: str, address: str, path: str | None) -> None:
        row_widget = QWidget()
        row = QVBoxLayout(row_widget)
        row.setContentsMargins(0, 0, 0, 0)
        label_widget = QLabel(label)
        label_widget.setObjectName("SectionLabel")
        row.addWidget(label_widget)

        address_row = QHBoxLayout()
        address_field = QLineEdit(address)
        address_field.setReadOnly(True)
        address_field.setObjectName("SeedTileWord")
        address_row.addWidget(address_field, stretch=1)
        address_row.addWidget(CopyButton(address))
        row.addLayout(address_row)

        if path:
            path_label = QLabel(f"Path: {path}")
            path_label.setObjectName("InfoNotice")
            row.addWidget(path_label)

        self._result_layout.addWidget(row_widget)
