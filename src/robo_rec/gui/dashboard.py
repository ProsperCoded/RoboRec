"""Dashboard — the default view: 'Welcome, select issue' plus three action cards."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from robo_rec.gui.widgets.card import ActionCard

ACTION_MISSING_WORDS = "missing_words"
ACTION_REARRANGE = "rearrange"
ACTION_DERIVE_WALLET = "derive_wallet"


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
            "Every recovery runs locally — nothing here ever leaves this machine."
        )
        subtitle.setObjectName("DashboardSubtitle")
        layout.addWidget(subtitle)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(18)

        missing_words_card = ActionCard(
            "hash",
            "Missing Words",
            "One or more words are blank or illegible. Recover them from the "
            "rest of the phrase.",
        )
        missing_words_card.clicked.connect(
            lambda: self.action_selected.emit(ACTION_MISSING_WORDS)
        )
        cards_row.addWidget(missing_words_card)

        rearrange_card = ActionCard(
            "shuffle",
            "Scrambled Seed Phrase",
            "All the words are correct but out of order. Find the correct "
            "arrangement.",
        )
        rearrange_card.clicked.connect(
            lambda: self.action_selected.emit(ACTION_REARRANGE)
        )
        cards_row.addWidget(rearrange_card)

        derive_wallet_card = ActionCard(
            "key",
            "Get Wallet from Seed Phrase",
            "Phrase is complete and correct. Derive its public address and "
            "private key.",
        )
        derive_wallet_card.clicked.connect(
            lambda: self.action_selected.emit(ACTION_DERIVE_WALLET)
        )
        cards_row.addWidget(derive_wallet_card)

        layout.addLayout(cards_row)
        layout.addStretch(1)
