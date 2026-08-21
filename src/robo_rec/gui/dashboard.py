"""Dashboard — the default view: 'Welcome, select issue' plus three action cards."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from robo_rec.gui.widgets.card import ActionCard

ACTION_MISSING_WORDS = "missing_words"
ACTION_REARRANGE = "rearrange"
ACTION_DERIVE_WALLET = "derive_wallet"
ACTION_TYPO_CORRECTION = "typo_correction"


class Dashboard(QWidget):
    action_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(24)

        title = QLabel("Welcome. Select the issue with your seed phrase.")
        title.setObjectName("DashboardTitle")
        title.setWordWrap(True)
        layout.addWidget(title)

        subtitle = QLabel(
            "everything runs locally - nothing is stored/persisted"
        )
        subtitle.setObjectName("DashboardSubtitle")
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(18)

        missing_words_card = ActionCard(
            "hash",
            "Missing Words",
            "One or more words are blank or illegible. Recover them from the "
            "rest of the phrase.",
        )
        missing_words_card.clicked.connect(
            lambda: self.action_selected.emit(ACTION_MISSING_WORDS)
        )
        grid.addWidget(missing_words_card, 0, 0)

        rearrange_card = ActionCard(
            "shuffle",
            "Scrambled Seed Phrase",
            "All the words are correct but out of order. Find the correct "
            "arrangement.",
        )
        rearrange_card.clicked.connect(
            lambda: self.action_selected.emit(ACTION_REARRANGE)
        )
        grid.addWidget(rearrange_card, 0, 1)

        derive_wallet_card = ActionCard(
            "key",
            "Get Wallet from Seed Phrase",
            "Phrase is complete and correct. Derive and verify its public address.",
        )
        derive_wallet_card.clicked.connect(
            lambda: self.action_selected.emit(ACTION_DERIVE_WALLET)
        )
        grid.addWidget(derive_wallet_card, 1, 0)

        typo_correction_card = ActionCard(
            "square-plus",
            "Typo Correction",
            "Phrase is complete but a word or two might be misspelled. Search "
            "nearby spellings for the correct phrase.",
        )
        typo_correction_card.clicked.connect(
            lambda: self.action_selected.emit(ACTION_TYPO_CORRECTION)
        )
        grid.addWidget(typo_correction_card, 1, 1)

        layout.addLayout(grid)
        layout.addStretch(1)
