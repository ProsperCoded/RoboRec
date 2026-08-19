"""Scrambled Seed Phrase panel — UI shell only, no subprocess wiring yet.

Mirrors PRD 4.1: 12-word full rearrangement is supported; for 24-word
phrases only a scrambled sub-segment (with a known-correct remainder) is
supported — full 24-word rearrangement is infeasible (24!).
"""

from __future__ import annotations

import math

from PySide6.QtCore import QTimer
from PySide6.QtGui import QTransform
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from robo_rec.gui.icons import load_pixmap
from robo_rec.gui.panels.base_panel import BasePanel
from robo_rec.gui.theme import ACCENT
from robo_rec.gui.widgets.animated_stack import AnimatedStackedWidget
from robo_rec.gui.widgets.seed_row import SeedRow

# Illustrative combinations-per-minute rate for the estimate shown before a run;
# not a measured benchmark — real timing depends on hardware and GPU availability.
COMBINATIONS_PER_MINUTE = 2_000_000


def estimate_minutes(scrambled_count: int) -> float:
    if scrambled_count < 2:
        return 0.0
    return max(math.factorial(scrambled_count) / COMBINATIONS_PER_MINUTE, 0.1)


def format_estimate(minutes: float) -> str:
    if minutes < 1:
        return "under a minute"
    if minutes < 60:
        return f"~{minutes:.0f} min"
    hours = minutes / 60
    if hours < 48:
        return f"~{hours:.1f} hrs"
    return f"~{hours / 24:.1f} days"


class RearrangePanel(BasePanel):
    def __init__(self, parent=None) -> None:
        super().__init__(
            "Scrambled Seed Phrase",
            "Enter the words in any order you remember them. Robo-Rec will "
            "search for the arrangement that produces a valid phrase.",
            parent,
        )

        self._view_stack = AnimatedStackedWidget()
        self.root_layout.addWidget(self._view_stack, stretch=1)

        self._view_stack.addWidget(self._build_form_view())
        self._view_stack.addWidget(self._build_loading_view())
        self._view_stack.addWidget(self._build_result_view())

        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(180)
        self._progress_timer.timeout.connect(self._advance_progress)
        self._progress_value = 0
        self._loading_rotation = 0

        self._on_length_changed()

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

        self._segment_group = QGroupBox("Known-correct segment (24-word only)")
        segment_layout = QHBoxLayout(self._segment_group)
        segment_layout.addWidget(QLabel("Scrambled word count:"))
        self._segment_spin = QSpinBox()
        self._segment_spin.setRange(2, 12)
        self._segment_spin.setValue(12)
        self._segment_spin.valueChanged.connect(self._refresh_estimate)
        segment_layout.addWidget(self._segment_spin)
        self._segment_group.setVisible(False)
        options_row.addWidget(self._segment_group)

        layout.addLayout(options_row)

        self._infeasible_notice = QLabel(
            "Full 24-word rearrangement (all positions unknown) is not "
            "supported — 24! is computationally infeasible. Identify a "
            "known-correct segment above to narrow the search."
        )
        self._infeasible_notice.setObjectName("WarningNotice")
        self._infeasible_notice.setWordWrap(True)
        self._infeasible_notice.hide()
        layout.addWidget(self._infeasible_notice)

        tiles_label = QLabel("WORDS IN ANY ORDER")
        tiles_label.setObjectName("SectionLabel")
        layout.addWidget(tiles_label)

        self._seed_row = SeedRow(length=12, editable=True)
        layout.addWidget(self._seed_row)

        estimate_row = QHBoxLayout()
        self._estimate_label = QLabel()
        self._estimate_label.setObjectName("InfoNotice")
        estimate_row.addWidget(self._estimate_label, stretch=1)
        layout.addLayout(estimate_row)

        self._start_button = QPushButton("Start Rearrangement")
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

        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        self._loading_icon = QLabel()
        self._loading_icon.setPixmap(load_pixmap("loader-circle", ACCENT, 22))
        title_row.addWidget(self._loading_icon)
        title = QLabel("Searching for the correct order…")
        title.setObjectName("DashboardTitle")
        title_row.addWidget(title)
        title_row.addStretch(1)
        layout.addLayout(title_row)

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

        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        result_icon = QLabel()
        result_icon.setPixmap(load_pixmap("party-popper", ACCENT, 22))
        title_row.addWidget(result_icon)
        title = QLabel("Found the correct order")
        title.setObjectName("DashboardTitle")
        title_row.addWidget(title)
        title_row.addStretch(1)
        layout.addLayout(title_row)

        subtitle = QLabel("Every word below is in its correct, checksum-valid position.")
        subtitle.setObjectName("DashboardSubtitle")
        layout.addWidget(subtitle)

        self._result_row = SeedRow(length=12, editable=False)
        layout.addWidget(self._result_row)

        again_button = QPushButton("Start Another Rearrangement")
        again_button.clicked.connect(self._reset_to_form)
        layout.addWidget(again_button)

        layout.addStretch(2)
        return view

    # ---- behavior ---------------------------------------------------

    def _on_length_changed(self) -> None:
        is_24 = self._length_combo.currentIndex() == 1
        length = 24 if is_24 else 12
        self._seed_row.set_length(length)
        self._segment_group.setVisible(is_24)
        self._infeasible_notice.setVisible(is_24)
        self._refresh_estimate()

    def _refresh_estimate(self) -> None:
        is_24 = self._length_combo.currentIndex() == 1
        scrambled_count = self._segment_spin.value() if is_24 else len(self._seed_row.tiles())
        minutes = estimate_minutes(scrambled_count)
        self._estimate_label.setText(
            f"Estimated time: {format_estimate(minutes)} (based on {scrambled_count} scrambled word(s))"
        )

    def _on_proceed_clicked(self) -> None:
        self._refresh_estimate()
        self._loading_subtitle.setText(f"{self._estimate_label.text()}. This is a preview run.")
        self._progress_value = 0
        self._progress_bar.setValue(0)
        self._view_stack.setCurrentIndex(1)
        self._progress_timer.start()

    def _advance_progress(self) -> None:
        self._progress_value = min(self._progress_value + 7, 100)
        self._progress_bar.setValue(self._progress_value)
        self._loading_rotation = (self._loading_rotation + 30) % 360
        pixmap = load_pixmap("loader-circle", ACCENT, 22)
        transform = QTransform().rotate(self._loading_rotation)
        self._loading_icon.setPixmap(pixmap.transformed(transform))
        if self._progress_value >= 100:
            self._progress_timer.stop()
            self._show_result()

    def _show_result(self) -> None:
        length = len(self._seed_row.tiles())
        self._result_row.set_length(length)
        words = self._seed_row.words()
        ordered = sorted((w for w in words if w), key=str.lower) + [
            "found" for w in words if not w
        ]
        self._result_row.set_words(ordered[:length])
        self._view_stack.setCurrentIndex(2)

    def _reset_to_form(self) -> None:
        self._view_stack.setCurrentIndex(0)
