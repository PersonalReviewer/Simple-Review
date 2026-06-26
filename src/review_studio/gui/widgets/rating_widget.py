"""Reusable rating editor widget."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QTextEdit, QVBoxLayout, QWidget

from review_studio.domain.models import RatingField
from review_studio.domain.value_objects import RATING_DEFINITIONS, RatingValue, parse_rating


class RatingWidget(QWidget):
    """Edit a structured rating and related comments."""

    changed = Signal(str, str, str)

    def __init__(self, rating_name: str, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.rating_name = rating_name

        self.label = QLabel(label)
        self.combo = QComboBox()
        for rating in RatingValue:
            definition = RATING_DEFINITIONS[rating]
            self.combo.addItem(rating.format(), rating.value)
            self.combo.setItemData(self.combo.count() - 1, definition.description, role=3)
        self.combo.setToolTip("Select the rating that should appear in the generated review.")

        self.comments = QTextEdit()
        self.comments.setAcceptRichText(False)
        self.comments.setPlaceholderText(f"Comments for {label.lower()}...")
        self.comments.setMinimumHeight(72)

        header = QHBoxLayout()
        header.addWidget(self.label)
        header.addStretch(1)
        header.addWidget(self.combo)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(header)
        layout.addWidget(self.comments)

        self.combo.currentIndexChanged.connect(self._emit_changed)
        self.comments.textChanged.connect(self._emit_changed)

    def set_rating(self, rating: RatingField) -> None:
        """Populate the widget from a domain rating field."""
        self.blockSignals(True)
        self.combo.blockSignals(True)
        self.comments.blockSignals(True)
        index = self.combo.findData(rating.value.value)
        self.combo.setCurrentIndex(max(index, 0))
        self.comments.setPlainText(rating.comments)
        self.comments.blockSignals(False)
        self.combo.blockSignals(False)
        self.blockSignals(False)

    def rating_value(self) -> RatingValue:
        """Return the currently selected rating value."""
        return parse_rating(str(self.combo.currentData()))

    def rating_comments(self) -> str:
        """Return the current comments text."""
        return self.comments.toPlainText()

    def _emit_changed(self) -> None:
        """Emit the widget's normalized state."""
        self.changed.emit(self.rating_name, self.rating_value().value, self.rating_comments())
