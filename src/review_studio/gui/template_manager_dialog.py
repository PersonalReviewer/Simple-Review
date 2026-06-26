"""Template/profile manager dialog."""

from __future__ import annotations

import json

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from review_studio.domain.template_schema import ReviewTemplate
from review_studio.services.template_service import TemplateService


class TemplateManagerDialog(QDialog):
    """Manage and switch review template profiles."""

    def __init__(self, service: TemplateService, current_template_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Template Profiles")
        self.resize(840, 680)
        self._service = service
        self.selected_template_id = current_template_id

        self.template_combo = QComboBox()
        self.template_combo.currentIndexChanged.connect(lambda _index: self._load_selected_template())
        self.template_id = QLineEdit()
        self.template_name = QLineEdit()
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Template JSON appears here. Save as a custom profile before editing bundled templates.")

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(lambda: self._reload_templates())
        apply_button = QPushButton("Use Selected Profile")
        apply_button.clicked.connect(self._apply_selected)
        clone_button = QPushButton("Clone As Custom…")
        clone_button.clicked.connect(self._clone_current)
        save_button = QPushButton("Save Custom Profile")
        save_button.clicked.connect(self._save_custom)
        validate_button = QPushButton("Validate JSON")
        validate_button.clicked.connect(self._validate_json)
        delete_button = QPushButton("Delete Custom Profile")
        delete_button.clicked.connect(self._delete_custom)

        top = QHBoxLayout()
        top.addWidget(self.template_combo, 1)
        top.addWidget(refresh_button)
        top.addWidget(apply_button)

        form = QFormLayout()
        form.addRow("Template ID", self.template_id)
        form.addRow("Template Name", self.template_name)

        button_row = QHBoxLayout()
        button_row.addWidget(clone_button)
        button_row.addWidget(validate_button)
        button_row.addWidget(save_button)
        button_row.addWidget(delete_button)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        note = QLabel("Templates are review profiles. Custom profiles are stored as JSON in the app data templates folder.")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addLayout(top)
        layout.addLayout(form)
        layout.addWidget(self.editor, 1)
        layout.addLayout(button_row)
        layout.addWidget(buttons)

        self._reload_templates(current_template_id)

    def _reload_templates(self, preferred_id: str | None = None) -> None:
        self._service.refresh()
        templates = self._service.templates()
        self.template_combo.blockSignals(True)
        self.template_combo.clear()
        for template in templates:
            self.template_combo.addItem(f"{template.id} — {template.name}", template.id)
        target = preferred_id or self.selected_template_id
        index = self.template_combo.findData(target)
        self.template_combo.setCurrentIndex(max(index, 0))
        self.template_combo.blockSignals(False)
        self._load_selected_template()

    def _current_template_id(self) -> str:
        return str(self.template_combo.currentData() or "default_review")

    def _load_selected_template(self) -> None:
        template = self._service.get_template(self._current_template_id())
        self.template_id.setText(template.id)
        self.template_name.setText(template.name)
        self.editor.setPlainText(json.dumps(template.to_dict(), indent=2, ensure_ascii=False))

    def _apply_selected(self) -> None:
        self.selected_template_id = self._current_template_id()
        self.accept()

    def _clone_current(self) -> None:
        template = self._service.get_template(self._current_template_id())
        clone_id = f"{template.id}_custom"
        clone = template.with_identity(clone_id, f"{template.name} Custom")
        self._service.save_custom_template(clone)
        self._reload_templates(clone_id)
        QMessageBox.information(self, "Template Cloned", f"Created custom profile '{clone_id}'.")

    def _save_custom(self) -> None:
        try:
            data = json.loads(self.editor.toPlainText())
            data["id"] = self.template_id.text().strip() or data.get("id", "custom_review")
            data["name"] = self.template_name.text().strip() or data.get("name", data["id"])
            template = ReviewTemplate.from_dict(data)
            if template.id == "default_review":
                QMessageBox.warning(self, "Bundled Template", "Use Clone As Custom before editing the bundled default profile.")
                return
            self._service.save_custom_template(template)
        except Exception as exc:  # noqa: BLE001 - show validation error in GUI
            QMessageBox.critical(self, "Template Save Failed", str(exc))
            return
        self._reload_templates(template.id)
        QMessageBox.information(self, "Template Saved", f"Saved custom profile '{template.id}'.")

    def _validate_json(self) -> None:
        """Validate the current JSON editor contents without saving."""
        try:
            ReviewTemplate.from_dict(json.loads(self.editor.toPlainText()))
        except Exception as exc:  # noqa: BLE001 - show validation errors in GUI
            QMessageBox.critical(self, "Template Invalid", str(exc))
            return
        QMessageBox.information(self, "Template Valid", "Template JSON is valid.")

    def _delete_custom(self) -> None:
        template_id = self._current_template_id()
        if template_id == "default_review":
            QMessageBox.warning(self, "Bundled Template", "The bundled default profile cannot be deleted.")
            return
        self._service.delete_custom_template(template_id)
        self._reload_templates("default_review")
        QMessageBox.information(self, "Template Deleted", f"Deleted custom profile '{template_id}'.")
