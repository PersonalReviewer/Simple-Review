"""Application theme helpers."""

from __future__ import annotations

from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtWidgets import QApplication


def apply_theme(app: QApplication, theme: str, font_size: int) -> None:
    """Apply a light or dark Qt palette and global font size."""
    font = QFont()
    font.setPointSize(font_size)
    app.setFont(font)

    if theme.lower() == "light":
        app.setPalette(QApplication.style().standardPalette())
        app.setStyleSheet(_base_stylesheet())
        return

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(32, 34, 37))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(235, 235, 235))
    palette.setColor(QPalette.ColorRole.Base, QColor(24, 26, 29))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(38, 41, 45))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(235, 235, 235))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(24, 26, 29))
    palette.setColor(QPalette.ColorRole.Text, QColor(235, 235, 235))
    palette.setColor(QPalette.ColorRole.Button, QColor(45, 48, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(235, 235, 235))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 85, 85))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(88, 166, 255))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)
    app.setStyleSheet(_base_stylesheet())


def _base_stylesheet() -> str:
    """Return shared application styling."""
    return """
    QMainWindow, QDialog { background: palette(window); }
    QGroupBox { font-weight: 600; margin-top: 12px; padding-top: 12px; }
    QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
    QPushButton { padding: 6px 10px; border-radius: 4px; }
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {
        padding: 4px; border: 1px solid palette(mid); border-radius: 4px;
    }
    QListWidget::item { padding: 6px; }
    QStatusBar { font-size: 11px; }
    """