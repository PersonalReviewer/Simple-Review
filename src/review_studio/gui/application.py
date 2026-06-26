"""Qt application bootstrap."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from review_studio.app.application import create_services
from review_studio.gui.main_window import MainWindow
from review_studio.gui.theme import apply_theme
from review_studio.gui.view_models.main_view_model import MainViewModel


def run_gui(argv: list[str] | None = None) -> int:
    """Start the Review Studio desktop application."""
    app = QApplication(argv or sys.argv)
    app.setApplicationName("Review Studio")
    app.setOrganizationName("Review Studio")

    services = create_services()
    view_model = MainViewModel(
        review_service=services.review_service,
        template_service=services.template_service,
        export_service=services.export_service,
        image_metadata_service=services.image_metadata_service,
    )
    apply_theme(app, view_model.settings.theme, view_model.settings.font_size)
    window = MainWindow(view_model)
    window.resize(1400, 850)
    window.show()
    return app.exec()