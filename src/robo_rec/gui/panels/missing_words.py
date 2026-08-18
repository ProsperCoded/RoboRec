"""Missing Words panel — UI shell only, no subprocess wiring yet.

Single unified flow per the user's sketch: paste/type the words you know in
order, leave boxes blank for the ones you don't. A "do you know the exact
position of each blank" toggle decides how the engine will search (mirrors
PRD 4.2: known positions support 1-4 missing words; unknown positions support
only 1-2, since combinatorics make 3+ unknown-position infeasible).
"""

from __future__ import annotations

import math

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from robo_rec.gui.panels.base_panel import BasePanel
from robo_rec.gui.widgets.seed_row import SeedRow

KNOWN_POSITION_MAX = 4
UNKNOWN_POSITION_MAX = 2

KNOWN_POSITION_WARNINGS = {
    3: "3 missing words at known positions can take hours; faster with a GPU.",
    4: "4 missing words at known positions may take hours to days. GPU is "
    "strongly recommended before starting.",
}
UNKNOWN_POSITION_OVER_LIMIT = (
    "Robo-Rec can only search unknown positions for 1-2 missing words — beyond "
    "that the number of possible arrangements is infeasible to check. Mark the "
    "positions you do know, or reduce the number of blanks."
)

# Illustrative combinations-per-minute rate for the estimate shown before a run;
# not a measured benchmark — real timing depends on hardware and GPU availability.
COMBINATIONS_PER_MINUTE = 2_000_000

TOKEN_PREFIXES = {
    "1": "Bitcoin (BTC)",
    "3": "Bitcoin (BTC)",
    "bc1": "Bitcoin (BTC)",
    "0x": "Ethereum (ETH)",
}


def estimate_minutes(total_words: int, missing: int, *, known_position: bool) -> float:
    if missing == 0:
        return 0.0
    combinations = 2048**missing
    if not known_position:
        combinations *= math.comb(total_words, missing)
    return max(combinations / COMBINATIONS_PER_MINUTE, 0.1)


def format_estimate(minutes: float) -> str:
    if minutes < 1:
        return "under a minute"
    if minutes < 60:
        return f"~{minutes:.0f} min"
    hours = minutes / 60
    if hours < 48:
        return f"~{hours:.1f} hrs"
    return f"~{hours / 24:.1f} days"


def detect_token(address: str) -> str | None:
    address = address.strip()
    for prefix, token in TOKEN_PREFIXES.items():
        if address.startswith(prefix):
            return token
    return None


class MissingWordsPanel(BasePanel):
    def __init__(self, parent=None) -> None:
        super().__init__(
            "Missing Words",
            "Type or paste the words you know, in order. Leave a box blank "
            "for each word you don't know.",
            parent,
        )

        self._view_stack = QStackedWidget()
        self.root_layout.addWidget(self._view_stack, stretch=1)

        self._view_stack.addWidget(self._build_form_view())
        self._view_stack.addWidget(self._build_loading_view())
        self._view_stack.addWidget(self._build_result_view())

        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(180)
        self._progress_timer.timeout.connect(self._advance_progress)
        self._progress_value = 0

        self._refresh_missing_count()

    # ---- form view ----------------------------------------------------

    def _build_form_view(self) -> QWidget:
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        options_row = QHBoxLayout()
        options_row.setSpacing(16)

        length_group = QGroupBox("Phrase length")
        length_layout = QHBoxLayout(length_group)
        self._length_combo = QComboBox()
        self._length_combo.addItems(["12 words", "24 words"])
        self._length_combo.currentIndexChanged.connect(self._on_length_changed)
        length_layout.addWidget(self._length_combo)
        options_row.addWidget(length_group)

        position_group = QGroupBox("Do you know the position of each blank?")
        position_layout = QHBoxLayout(position_group)
        self._known_radio = QRadioButton("Yes, mark exact blanks")
        self._known_radio.setChecked(True)
        self._unknown_radio = QRadioButton("No, just missing somewhere")
        position_group_btns = QButtonGroup(self)
        position_group_btns.addButton(self._known_radio)
        position_group_btns.addButton(self._unknown_radio)
        self._known_radio.toggled.connect(self._refresh_missing_count)
        position_layout.addWidget(self._known_radio)
        position_layout.addWidget(self._unknown_radio)
        options_row.addWidget(position_group, stretch=1)

        layout.addLayout(options_row)

        self._warning_label = QLabel()
        self._warning_label.setObjectName("WarningNotice")
        self._warning_label.setWordWrap(True)
        self._warning_label.hide()
        layout.addWidget(self._warning_label)

        tiles_header = QHBoxLayout()
        tiles_label = QLabel("PASTE ALL KNOWN WORDS, IN ORDER")
        tiles_label.setObjectName("SectionLabel")
        tiles_header.addWidget(tiles_label)
        tiles_header.addStretch(1)
        self._missing_count_label = QLabel()
        self._missing_count_label.setObjectName("SectionLabel")
        tiles_header.addWidget(self._missing_count_label)
        layout.addLayout(tiles_header)

        self._seed_row = SeedRow(length=12, editable=True)
        self._seed_row.words_changed.connect(self._refresh_missing_count)
        layout.addWidget(self._seed_row)

        target_group = QGroupBox("Test address")
        target_layout = QHBoxLayout(target_group)
        self._address_field = QLineEdit()
        self._address_field.setPlaceholderText("An address you know is associated with this wallet")
        self._address_field.textChanged.connect(self._on_address_changed)
        target_layout.addWidget(self._address_field, stretch=1)
        self._token_combo = QComboBox()
        self._token_combo.addItems(["Bitcoin (BTC)", "Ethereum (ETH)", "Solana (SOL)", "Other BIP39-compatible"])
        target_layout.addWidget(self._token_combo)
        layout.addWidget(target_group)

        estimate_row = QHBoxLayout()
        self._estimate_label = QLabel()
        self._estimate_label.setObjectName("InfoNotice")
        estimate_row.addWidget(self._estimate_label, stretch=1)
        layout.addLayout(estimate_row)

        self._start_button = QPushButton("Proceed")
        self._start_button.setObjectName("PrimaryButton")
        self._start_button.clicked.connect(self._on_proceed_clicked)
        layout.addWidget(self._start_button)

        layout.addStretch(1)
        return view

    # ---- loading view ---------------------------------------------------

    def _build_loading_view(self) -> QWidget:
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(0, 60, 0, 0)
        layout.setSpacing(16)
        layout.addStretch(1)

        title = QLabel("Searching for your seed phrase…")
        title.setObjectName("DashboardTitle")
        layout.addWidget(title)

        self._loading_subtitle = QLabel()
        self._loading_subtitle.setObjectName("DashboardSubtitle")
        layout.addWidget(self._loading_subtitle)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(8)
        layout.addWidget(self._progress_bar)

        layout.addStretch(2)
        return view

    # ---- result view ---------------------------------------------------

    def _build_result_view(self) -> QWidget:
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(0, 40, 0, 0)
        layout.setSpacing(16)
        layout.addStretch(1)

        title = QLabel("🎉 Recovered your seed phrase")
        title.setObjectName("DashboardTitle")
        layout.addWidget(title)

        subtitle = QLabel("Every word below matches a valid, address-verified phrase.")
        subtitle.setObjectName("DashboardSubtitle")
        layout.addWidget(subtitle)

        self._result_row = SeedRow(length=12, editable=False)
        layout.addWidget(self._result_row)

        again_button = QPushButton("Start Another Recovery")
        again_button.clicked.connect(self._reset_to_form)
        layout.addWidget(again_button)

        layout.addStretch(2)
        return view

    # ---- behavior ---------------------------------------------------

    def _on_length_changed(self) -> None:
        length = 12 if self._length_combo.currentIndex() == 0 else 24
        self._seed_row.set_length(length)
        self._refresh_missing_count()

    def _on_address_changed(self, text: str) -> None:
        detected = detect_token(text)
        if detected:
            index = self._token_combo.findText(detected)
            if index >= 0:
                self._token_combo.setCurrentIndex(index)

    def _refresh_missing_count(self) -> None:
        missing = self._seed_row.missing_count()
        total = len(self._seed_row.tiles())
        known_position = self._known_radio.isChecked()

        self._missing_count_label.setText(f"MISSING WORDS: {missing} (derived)")

        limit = KNOWN_POSITION_MAX if known_position else UNKNOWN_POSITION_MAX
        over_limit = missing > limit

        warning = None
        if over_limit and not known_position:
            warning = UNKNOWN_POSITION_OVER_LIMIT
        elif over_limit and known_position:
            warning = (
                f"{missing} missing words at known positions is beyond what Robo-Rec "
                "supports (max 4). Fill in more words to continue."
            )
        elif known_position:
            warning = KNOWN_POSITION_WARNINGS.get(missing)

        if warning:
            self._warning_label.setText(warning)
            self._warning_label.show()
        else:
            self._warning_label.hide()

        if missing == 0:
            estimate_text = "Fill in at least one blank to see a time estimate."
        else:
            minutes = estimate_minutes(total, missing, known_position=known_position)
            estimate_text = f"Estimated time: {format_estimate(minutes)} (based on {missing} missing word(s))"
        self._estimate_label.setText(estimate_text)

        self._start_button.setEnabled(0 < missing <= limit)

    def _on_proceed_clicked(self) -> None:
        missing = self._seed_row.missing_count()
        known_position = self._known_radio.isChecked()
        minutes = estimate_minutes(len(self._seed_row.tiles()), missing, known_position=known_position)
        self._loading_subtitle.setText(f"Estimated time: {format_estimate(minutes)}. This is a preview run.")
        self._progress_value = 0
        self._progress_bar.setValue(0)
        self._view_stack.setCurrentIndex(1)
        self._progress_timer.start()

    def _advance_progress(self) -> None:
        self._progress_value = min(self._progress_value + 7, 100)
        self._progress_bar.setValue(self._progress_value)
        if self._progress_value >= 100:
            self._progress_timer.stop()
            self._show_result()

    def _show_result(self) -> None:
        self._result_row.set_length(len(self._seed_row.tiles()))
        placeholder_words = [word or "found" for word in self._seed_row.words()]
        self._result_row.set_words(placeholder_words)
        self._view_stack.setCurrentIndex(2)

    def _reset_to_form(self) -> None:
        self._view_stack.setCurrentIndex(0)
        self._seed_row.focus_first_blank()

    def focus_first_word(self) -> None:
        if self._view_stack.currentIndex() == 0:
            self._seed_row.focus_first_blank()
