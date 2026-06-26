"""Offscreen smoke tests for the PySide6 GUI."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QComboBox, QLineEdit

from review_studio.exporters.export_service import ExportService
from review_studio.gui.main_window import MainWindow
from review_studio.gui.view_models.main_view_model import MainViewModel
from review_studio.services.review_service import ReviewService
from review_studio.services.template_service import TemplateService
from review_studio.storage.repository import ReviewRepository
from review_studio.storage.settings import SettingsStore
from review_studio.templates.engine import TemplateEngine


class GuiSmokeTests(unittest.TestCase):
    """Verify the split-screen UI can instantiate and update preview."""

    app: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance()
        cls.app = app if isinstance(app, QApplication) else QApplication([])

    def test_main_window_live_preview_updates(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            engine = TemplateEngine()
            view_model = MainViewModel(
                ReviewService(ReviewRepository(root / "reviews"), SettingsStore(root / "settings.json")),
                TemplateService(engine),
                ExportService(engine),
            )
            window = MainWindow(view_model)
            vendor_widget = window._field_widgets["value.vendor_name"]
            self.assertIsInstance(vendor_widget, QLineEdit)
            vendor_edit = vendor_widget
            if isinstance(vendor_edit, QLineEdit):
                vendor_edit.setText("Vendor X")
            field_map = {field.identity: field for field in view_model.current_template.iter_fields()}
            window._update_template_field(field_map["value.vendor_name"], "Vendor X")
            rating_widget = window._field_widgets["rating.quality"]
            self.assertIsInstance(rating_widget, QComboBox)
            if isinstance(rating_widget, QComboBox):
                rating_widget.setCurrentIndex(rating_widget.findData("6"))
            window._refresh_preview(save=True)

            self.assertIn("Vendor X", window.raw_preview.toPlainText())
            self.assertIn("𝟔/𝟕 –[color=#5bc0de] 𝐀𝐃𝐕𝐀𝐍𝐂𝐄𝐃 [/color]", window.raw_preview.toPlainText())
            window.close()


if __name__ == "__main__":
    unittest.main()
