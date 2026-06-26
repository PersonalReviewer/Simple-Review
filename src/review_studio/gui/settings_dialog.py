"""Settings dialog for Review Studio."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from review_studio.storage.settings import UserSettings


class SettingsDialog(QDialog):
    """Allow users to edit persistent application settings."""

    def __init__(self, settings: UserSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Review Studio Settings")
        self._settings = settings

        self.theme = QComboBox()
        self.theme.addItems(["dark", "light"])
        self.theme.setCurrentText(settings.theme)

        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setValue(settings.font_size)

        self.autosave_interval = QSpinBox()
        self.autosave_interval.setRange(1, 300)
        self.autosave_interval.setSuffix(" seconds")
        self.autosave_interval.setValue(settings.autosave_interval_seconds)

        self.review_library_folder = QLineEdit(settings.review_library_folder)
        self.export_folder = QLineEdit(settings.default_export_folder)
        self.template_id = QLineEdit(settings.default_template_id)
        self.template_id.setReadOnly(True)

        form = QFormLayout()
        form.addRow("Theme", self.theme)
        form.addRow("Font size", self.font_size)
        form.addRow("Autosave interval", self.autosave_interval)
        form.addRow("Review library folder", self._folder_row(self.review_library_folder))
        form.addRow("Default export folder", self._folder_row(self.export_folder))
        form.addRow("Default template", self.template_id)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def updated_settings(self) -> UserSettings:
        """Return a settings object reflecting the dialog state."""
        return UserSettings(
            theme=self.theme.currentText(),
            font_size=self.font_size.value(),
            autosave_interval_seconds=self.autosave_interval.value(),
            default_export_folder=self.export_folder.text().strip(),
            review_library_folder=self.review_library_folder.text().strip(),
            default_template_id=self.template_id.text().strip() or "default_review",
            recent_review_ids=list(self._settings.recent_review_ids),
        )

    def _folder_row(self, line_edit: QLineEdit) -> QWidget:
        """Create a folder picker row."""
        container = QWidget()
        button = QPushButton("Browse…")
        button.clicked.connect(lambda: self._choose_folder(line_edit))
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(line_edit)
        layout.addWidget(button)
        return container

    def _choose_folder(self, line_edit: QLineEdit) -> None:
        """Prompt for a directory and place it into ``line_edit``."""
        selected = QFileDialog.getExistingDirectory(self, "Choose Folder", line_edit.text())
        if selected:
            line_edit.setText(selected)
