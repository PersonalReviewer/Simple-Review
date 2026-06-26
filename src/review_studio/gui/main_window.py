"""Main Review Studio desktop window."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QMouseEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDockWidget,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QComboBox,
    QInputDialog,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from review_studio.domain.models import Review
from review_studio.domain.template_schema import FieldType, TemplateField
from review_studio.exporters.export_service import ExportFormat
from review_studio.gui.exif_cleaner_dialog import ExifCleanerDialog
from review_studio.gui.settings_dialog import SettingsDialog
from review_studio.gui.template_manager_dialog import TemplateManagerDialog
from review_studio.gui.theme import apply_theme
from review_studio.gui.view_models.main_view_model import MainViewModel
from review_studio.preview.renderer import PreviewRenderer


LOGGER = logging.getLogger(__name__)


class ReviewLibraryTree(QTreeWidget):
    """Review tree with a safe manual drag-to-folder gesture.

    Qt's native ``InternalMove`` mode can reparent ``QTreeWidgetItem`` objects in C++
    while Python code is also refreshing the tree, which can segfault on release.
    This widget deliberately disables native drag/drop and treats a left-button
    press/move/release as a lightweight gesture: it records the dragged review id,
    reads the folder under the mouse on release, and lets the view-model perform
    the move. Qt never mutates the tree structure during the gesture.
    """

    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self._window = window
        self._drag_review_id = ""
        self._drag_start_pos: QPoint | None = None
        self._manual_drag_active = False
        self.setHeaderHidden(True)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)
        self.setDropIndicatorShown(False)
        self.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Remember review items that may become manual drag gestures."""
        super().mousePressEvent(event)
        if event.button() != Qt.MouseButton.LeftButton:
            return
        item = self.itemAt(event.position().toPoint())
        review_id = str(item.data(0, Qt.ItemDataRole.UserRole) or "") if item is not None else ""
        self._drag_review_id = review_id
        self._drag_start_pos = event.position().toPoint() if review_id else None
        self._manual_drag_active = False

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Show a drag cursor once the pointer moves past the drag threshold."""
        if self._drag_review_id and self._drag_start_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            distance = (event.position().toPoint() - self._drag_start_pos).manhattanLength()
            if distance >= QApplication.startDragDistance():
                self._manual_drag_active = True
                self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Move the dragged review to the folder under the pointer on release."""
        review_id = self._drag_review_id
        was_dragging = self._manual_drag_active
        self._clear_manual_drag()
        if event.button() == Qt.MouseButton.LeftButton and review_id and was_dragging:
            category = self._category_for_item(self.itemAt(event.position().toPoint()))
            if category:
                QTimer.singleShot(0, lambda rid=review_id, cat=category: self._window.move_review_to_category(rid, cat))
                event.accept()
                return
        super().mouseReleaseEvent(event)

    def _category_for_item(self, item: QTreeWidgetItem | None) -> str:
        """Return the folder/category represented by a tree item."""
        if item is None:
            return ""
        category = str(item.data(0, Qt.ItemDataRole.UserRole + 1) or "")
        if not category and item.parent() is not None:
            category = str(item.parent().data(0, Qt.ItemDataRole.UserRole + 1) or "")
        return category

    def _clear_manual_drag(self) -> None:
        """Reset manual drag state and restore the normal cursor."""
        self._drag_review_id = ""
        self._drag_start_pos = None
        self._manual_drag_active = False
        self.viewport().unsetCursor()


class MainWindow(QMainWindow):
    """Professional split-screen review editor with live preview."""

    def __init__(self, view_model: MainViewModel) -> None:
        super().__init__()
        self.view_model = view_model
        self.preview_renderer = PreviewRenderer()
        self._loading = False
        self._field_widgets: dict[str, QWidget] = {}
        self._rating_guidance_labels: dict[str, QLabel] = {}

        self.setWindowTitle("Review Studio")
        self._build_actions()
        self._build_menu()
        self._build_toolbar()
        self._build_library_dock()
        self._build_central_editor()
        self._build_status_bar()
        self._build_timers()
        self._populate_form(self.view_model.current_review)
        self._refresh_library()
        self._refresh_preview(save=False)

    def _build_actions(self) -> None:
        """Create window actions and keyboard shortcuts."""
        self.new_action = QAction("New Review", self)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.new_action.triggered.connect(self._new_review)

        self.exif_cleaner_action = QAction("Remove Image Metadata…", self)
        self.exif_cleaner_action.setShortcut(QKeySequence("Ctrl+Shift+M"))
        self.exif_cleaner_action.triggered.connect(self._open_exif_cleaner)

        self.template_manager_action = QAction("Template Profiles…", self)
        self.template_manager_action.setShortcut(QKeySequence("Ctrl+Shift+T"))
        self.template_manager_action.triggered.connect(self._open_template_manager)

        self.save_action = QAction("Save", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self._save_now)

        self.copy_action = QAction("Copy Preview", self)
        self.copy_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self.copy_action.triggered.connect(self._copy_preview)

        self.export_action = QAction("Export…", self)
        self.export_action.setShortcut(QKeySequence("Ctrl+E"))
        self.export_action.triggered.connect(self._export_review)

        self.duplicate_action = QAction("Duplicate Review", self)
        self.duplicate_action.setShortcut(QKeySequence("Ctrl+D"))
        self.duplicate_action.triggered.connect(self._duplicate_review)

        self.delete_action = QAction("Delete Review", self)
        self.delete_action.setShortcut(QKeySequence("Ctrl+Delete"))
        self.delete_action.triggered.connect(self._delete_review)

        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self._undo)

        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.triggered.connect(self._redo)

        self.settings_action = QAction("Settings…", self)
        self.settings_action.setShortcut(QKeySequence("Ctrl+,"))
        self.settings_action.triggered.connect(self._open_settings)

    def _build_menu(self) -> None:
        """Create the menu bar."""
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.export_action)
        file_menu.addSeparator()
        file_menu.addAction(self.settings_action)
        file_menu.addSeparator()
        file_menu.addAction("Quit", self.close, QKeySequence.StandardKey.Quit)

        edit_menu = self.menuBar().addMenu("Edit")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.copy_action)

        review_menu = self.menuBar().addMenu("Review")
        review_menu.addAction(self.duplicate_action)
        review_menu.addAction(self.delete_action)

        tools_menu = self.menuBar().addMenu("Tools")
        tools_menu.addAction(self.exif_cleaner_action)
        tools_menu.addAction(self.template_manager_action)

    def _build_toolbar(self) -> None:
        """Create the primary toolbar."""
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.save_action)
        toolbar.addAction(self.duplicate_action)
        toolbar.addAction(self.copy_action)
        toolbar.addAction(self.export_action)
        toolbar.addAction(self.exif_cleaner_action)

    def _build_library_dock(self) -> None:
        """Create review library/search navigation."""
        dock = QDockWidget("Review Library", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search reviews…")
        self.search_box.textChanged.connect(self._refresh_library)

        self.review_tree = ReviewLibraryTree(self)
        self.review_tree.itemActivated.connect(self._open_library_item)
        self.review_tree.itemClicked.connect(self._open_library_item_from_click)

        folder_label = QLabel("Current folder")
        folder_label.setStyleSheet("font-weight: 700;")
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.setPlaceholderText("Choose or type folder…")
        self.category_combo.setToolTip("Pick an existing folder or type a new one, then click Move.")
        move_category_button = QPushButton("Move")
        move_category_button.setToolTip("Move the current review to the selected folder.")
        move_category_button.clicked.connect(self._set_current_category)
        new_category_button = QPushButton("New Folder…")
        new_category_button.clicked.connect(self._create_category)
        category_row = QHBoxLayout()
        category_row.addWidget(self.category_combo, 1)
        category_row.addWidget(move_category_button)
        category_row.addWidget(new_category_button)

        new_button = QPushButton("Create Review")
        new_button.clicked.connect(self._new_review)
        duplicate_button = QPushButton("Duplicate")
        duplicate_button.clicked.connect(self._duplicate_review)
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self._delete_review)

        buttons = QHBoxLayout()
        buttons.addWidget(new_button)
        buttons.addWidget(duplicate_button)
        buttons.addWidget(delete_button)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(self.search_box)
        layout.addWidget(self.review_tree, 1)
        layout.addWidget(folder_label)
        layout.addLayout(category_row)
        layout.addLayout(buttons)
        dock.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    def _build_central_editor(self) -> None:
        """Create split-screen editor and preview panels."""
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_editor_panel())
        splitter.addWidget(self._build_preview_panel())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)
        self.setCentralWidget(splitter)

    def _build_editor_panel(self) -> QWidget:
        """Create the structured form editor."""
        container = QWidget()
        layout = QVBoxLayout(container)
        title = QLabel("Structured Review Editor")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        self._field_widgets.clear()
        self._rating_guidance_labels.clear()
        for section in self.view_model.current_template.sections:
            form_layout.addWidget(self._build_template_section_group(section.title, section.fields))
        form_layout.addStretch(1)
        scroll.setWidget(form_container)
        layout.addWidget(scroll, 1)
        return container

    def _build_template_section_group(self, title: str, fields: tuple[TemplateField, ...]) -> QGroupBox:
        """Create a form section from template metadata."""
        group = QGroupBox(title)
        form = QFormLayout(group)
        for field in fields:
            widget = self._create_template_field_widget(field)
            self._field_widgets[field.identity] = widget
            form.addRow(field.label, widget)
            if field.field_type is FieldType.RATING and isinstance(widget, QComboBox):
                guidance = QLabel(self._rating_guidance_text(field, widget))
                guidance.setWordWrap(True)
                guidance.setStyleSheet("color: #8a94a6; font-size: 12px; padding-bottom: 6px;")
                self._rating_guidance_labels[field.identity] = guidance
                form.addRow("Recommendation", guidance)
        return group

    def _create_template_field_widget(self, field: TemplateField) -> QWidget:
        """Create the correct editor widget for a template field."""
        if field.field_type in {FieldType.TEXT, FieldType.URL}:
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(field.placeholder or field.label)
            line_edit.setToolTip(self._field_tooltip(field))
            line_edit.textEdited.connect(lambda value, field_def=field: self._update_template_field(field_def, value))
            return line_edit
        if field.field_type is FieldType.MULTILINE:
            text_edit = QTextEdit()
            text_edit.setAcceptRichText(False)
            text_edit.setPlaceholderText(field.placeholder or field.label)
            text_edit.setToolTip(self._field_tooltip(field))
            text_edit.setMinimumHeight(130 if field.key == "final_summary" else 88)
            text_edit.textChanged.connect(lambda field_def=field, widget=text_edit: self._update_template_field(field_def, widget.toPlainText()))
            return text_edit
        if field.field_type is FieldType.SELECT:
            combo = QComboBox()
            combo.addItems(field.options)
            combo.setToolTip(self._field_tooltip(field))
            combo.currentTextChanged.connect(lambda value, field_def=field: self._update_template_field(field_def, value))
            return combo
        if field.field_type is FieldType.RATING:
            combo = QComboBox()
            for option in self.view_model.current_template.rating_options:
                combo.addItem(option.display_name, option.storage_value)
                guidance = self.view_model.current_template.rating_guidance_for(field, option.storage_value)
                combo.setItemData(combo.count() - 1, guidance, role=Qt.ItemDataRole.ToolTipRole)
            combo.setToolTip("Select a rating. The recommendation below is editor guidance only and is not added to the exported review.")
            combo.currentIndexChanged.connect(lambda _index, field_def=field, widget=combo: self._handle_rating_change(field_def, widget))
            return combo
        msg = f"Unsupported field type: {field.field_type.value}"
        raise ValueError(msg)

    def _field_tooltip(self, field: TemplateField) -> str:
        """Return helpful tooltip text for a generated field."""
        required = " Required field." if field.required else ""
        return f"{field.label}.{required} Template variable: {field.identity}"

    def _handle_rating_change(self, field: TemplateField, widget: QComboBox) -> None:
        """Update editor guidance and persist the selected rating value."""
        self._update_rating_guidance_label(field, widget)
        self._update_template_field(field, str(widget.currentData()))

    def _update_rating_guidance_label(self, field: TemplateField, widget: QComboBox) -> None:
        """Refresh editor-only guidance for a rating dropdown."""
        label = self._rating_guidance_labels.get(field.identity)
        if label is not None:
            label.setText(self._rating_guidance_text(field, widget))

    def _rating_guidance_text(self, field: TemplateField, widget: QComboBox) -> str:
        """Return selected rating recommendation text for display below a dropdown."""
        guidance = self.view_model.current_template.rating_guidance_for(field, str(widget.currentData()))
        return f"Recommendation: {guidance}"

    def _build_preview_panel(self) -> QWidget:
        """Create live raw/rendered preview tabs."""
        container = QWidget()
        layout = QVBoxLayout(container)
        header = QHBoxLayout()
        title = QLabel("Live Preview")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        copy_button = QPushButton("Copy")
        copy_button.clicked.connect(self._copy_preview)
        export_button = QPushButton("Export")
        export_button.clicked.connect(self._export_review)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(copy_button)
        header.addWidget(export_button)
        layout.addLayout(header)

        self.preview_tabs = QTabWidget()
        self.raw_preview = QPlainTextEdit()
        self.raw_preview.setReadOnly(True)
        self.raw_preview.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.rendered_preview = QTextBrowser()
        self.rendered_preview.setOpenExternalLinks(True)
        self.preview_tabs.addTab(self.raw_preview, "Raw Output")
        self.preview_tabs.addTab(self.rendered_preview, "Rendered Preview")
        layout.addWidget(self.preview_tabs, 1)

        self.validation_label = QLabel()
        self.validation_label.setWordWrap(True)
        layout.addWidget(self.validation_label)
        return container

    def _build_status_bar(self) -> None:
        """Create status bar widgets."""
        self.autosave_label = QLabel("Autosave ready")
        self.statusBar().addPermanentWidget(self.autosave_label)
        self.statusBar().showMessage("Ready")

    def _build_timers(self) -> None:
        """Create autosave and preview debounce timers."""
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(75)
        self.preview_timer.timeout.connect(self._refresh_preview)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(self.view_model.settings.autosave_interval_seconds * 1000)
        self.autosave_timer.timeout.connect(self._autosave)
        self.autosave_timer.start()

    def _populate_form(self, review: Review) -> None:
        """Populate editor widgets from a review without firing updates."""
        self._loading = True
        for field in self.view_model.current_template.iter_fields():
            widget = self._field_widgets.get(field.identity)
            value = review.field_value(field.namespace, field.key)
            if isinstance(widget, QLineEdit):
                widget.setText(value)
            elif isinstance(widget, QTextEdit):
                widget.setPlainText(value)
            elif isinstance(widget, QComboBox):
                if field.field_type is FieldType.RATING:
                    index = widget.findData(value or "na")
                else:
                    index = widget.findText(value)
                widget.setCurrentIndex(max(index, 0))
        self._loading = False
        self.setWindowTitle(f"Review Studio — {review.display_title()}")

    def _update_template_field(self, field: TemplateField, value: str) -> None:
        """Handle edits from a dynamically generated template field."""
        if self._loading:
            return
        self.view_model.update_template_field(field, value)
        self._schedule_live_update()

    def _schedule_live_update(self) -> None:
        """Refresh preview immediately while coalescing rapid keystrokes."""
        self.preview_timer.start()
        self.statusBar().showMessage("Editing… autosave pending", 1500)

    def _refresh_preview(self, save: bool = False) -> None:
        """Refresh raw/rendered preview and optional persistence."""
        try:
            raw = self.view_model.render_raw_preview()
            self.raw_preview.setPlainText(raw)
            self.rendered_preview.setHtml(self.preview_renderer.bbcode_to_html(raw))
            messages = self.view_model.validation_messages()
            self.validation_label.setText("Validation: " + " | ".join(messages) if messages else "Validation: OK")
            self.setWindowTitle(f"Review Studio — {self.view_model.current_review.display_title()}")
            if save:
                self.view_model.save_current_review()
                self._refresh_library(select_current=True)
        except Exception as exc:
            LOGGER.exception("Could not refresh preview")
            self.validation_label.setText(f"Preview error: {exc}")

    def _autosave(self) -> None:
        """Persist the current review without interrupting the user."""
        try:
            self.view_model.save_current_review()
            self._refresh_library(select_current=True)
            self.autosave_label.setText("Autosaved")
        except Exception as exc:
            LOGGER.exception("Autosave failed")
            self.autosave_label.setText("Autosave failed")
            self.statusBar().showMessage(f"Autosave failed: {exc}", 5000)

    def _save_now(self) -> None:
        """Manually save the current review."""
        self._refresh_preview(save=True)
        self.statusBar().showMessage("Review saved", 2500)

    def _copy_preview(self) -> None:
        """Copy the raw generated review to the clipboard instantly."""
        QApplication.clipboard().setText(self.raw_preview.toPlainText())
        self.statusBar().showMessage("Generated review copied to clipboard", 2500)

    def _export_review(self) -> None:
        """Export the current review to a user-selected file."""
        filters = "BBCode (*.bbcode);;Markdown (*.md);;HTML (*.html);;Plain Text (*.txt);;JSON (*.json)"
        default = self.view_model.settings.normalized_export_folder() / f"{self.view_model.current_review.display_title()}.bbcode"
        path_text, selected_filter = QFileDialog.getSaveFileName(self, "Export Review", str(default), filters)
        if not path_text:
            return
        export_format = self._format_from_filter(selected_filter, Path(path_text))
        try:
            self.view_model.export_current_review(export_format, Path(path_text))
            self.statusBar().showMessage(f"Exported {export_format.value} review", 4000)
        except Exception as exc:
            LOGGER.exception("Export failed")
            QMessageBox.critical(self, "Export Failed", str(exc))

    def _format_from_filter(self, selected_filter: str, path: Path) -> ExportFormat:
        """Infer the export format from dialog filter/path."""
        suffix = path.suffix.lower()
        if "Markdown" in selected_filter or suffix == ".md":
            return ExportFormat.MARKDOWN
        if "HTML" in selected_filter or suffix in {".html", ".htm"}:
            return ExportFormat.HTML
        if "Plain" in selected_filter or suffix == ".txt":
            return ExportFormat.TEXT
        if "JSON" in selected_filter or suffix == ".json":
            return ExportFormat.JSON
        return ExportFormat.BBCODE

    def _refresh_library(self, *_args: object, select_current: bool = False) -> None:
        """Refresh the review library list."""
        query = self.search_box.text() if hasattr(self, "search_box") else ""
        reviews = self.view_model.search_reviews(query)
        current_id = self.view_model.current_review.id
        self.review_tree.blockSignals(True)
        self.review_tree.clear()
        self._refresh_category_combo(reviews)
        grouped: dict[str, list[Review]] = {}
        for review in reviews:
            grouped.setdefault(review.category or "Uncategorized", []).append(review)
        if not query.strip():
            for category in self.view_model.categories():
                grouped.setdefault(category, [])
        for category in sorted(grouped):
            folder_item = QTreeWidgetItem([f"📁 {category} ({len(grouped[category])})"])
            folder_item.setData(0, Qt.ItemDataRole.UserRole, "")
            folder_item.setData(0, Qt.ItemDataRole.UserRole + 1, category)
            folder_item.setFlags(
                folder_item.flags()
                | Qt.ItemFlag.ItemIsDropEnabled
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            self.review_tree.addTopLevelItem(folder_item)
            folder_item.setExpanded(True)
            for review in grouped[category]:
                item = QTreeWidgetItem([review.display_title()])
                item.setData(0, Qt.ItemDataRole.UserRole, review.id)
                item.setData(0, Qt.ItemDataRole.UserRole + 1, category)
                item.setFlags(
                    item.flags()
                    | Qt.ItemFlag.ItemIsDragEnabled
                    | Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                )
                vendor = review.values.get("vendor_name", review.vendor)
                product = review.values.get("product_name", review.product)
                item.setToolTip(0, f"Updated: {review.updated_at}\nFolder: {review.category}\nVendor: {vendor}\nProduct: {product}")
                folder_item.addChild(item)
                if select_current and review.id == current_id:
                    self.review_tree.setCurrentItem(item)
        if not grouped:
            item = QTreeWidgetItem(["No reviews found"])
            item.setData(0, Qt.ItemDataRole.UserRole, "")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.review_tree.addTopLevelItem(item)
        self.review_tree.blockSignals(False)

    def _refresh_category_combo(self, reviews: list[Review]) -> None:
        """Refresh folder/category options without losing the current value."""
        current_category = self.view_model.current_review.category or "Uncategorized"
        categories = sorted({current_category, *self.view_model.categories()})
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItems(categories)
        index = self.category_combo.findText(current_category)
        self.category_combo.setCurrentIndex(max(index, 0))
        self.category_combo.setEditText(current_category)
        self.category_combo.blockSignals(False)

    def _open_library_item(self, item: QTreeWidgetItem | None) -> None:
        """Open an item from the review library."""
        if item is None:
            return
        review_id = str(item.data(0, Qt.ItemDataRole.UserRole) or "")
        if not review_id:
            item.setExpanded(not item.isExpanded())
            return
        if review_id == self.view_model.current_review.id:
            return
        self._autosave()
        try:
            review = self.view_model.select_review(review_id)
            self._populate_form(review)
            self._refresh_preview(save=False)
        except Exception as exc:
            LOGGER.exception("Could not open review")
            QMessageBox.warning(self, "Open Review Failed", str(exc))

    def _open_library_item_from_click(self, item: QTreeWidgetItem, _column: int) -> None:
        """Open plain single-clicks while preserving shift/ctrl multi-selection."""
        modifiers = QApplication.keyboardModifiers()
        if modifiers & (Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.ControlModifier):
            return
        if len(self._selected_review_ids()) > 1:
            return
        self._open_library_item(item)

    def _set_current_category(self) -> None:
        """Update the folder/category for the current review."""
        category = self.category_combo.currentText().strip() or "Uncategorized"
        self.view_model.set_current_category(category)
        self._refresh_library(select_current=True)
        self.statusBar().showMessage(f"Review moved to folder: {category}", 2500)

    def move_review_to_category(self, review_id: str, category: str) -> None:
        """Move a review to a folder after drag/drop."""
        self.view_model.move_review_to_category(review_id, category)
        self._refresh_library(select_current=True)
        self.statusBar().showMessage(f"Review moved to folder: {category}", 2500)

    def _create_category(self) -> None:
        """Prompt for a new folder/category without moving the current review."""
        category, accepted = QInputDialog.getText(
            self,
            "New Review Folder",
            "Folder name:",
            text=self.category_combo.currentText().strip() or "Uncategorized",
        )
        if not accepted:
            return
        clean_category = self.view_model.create_category(category)
        self._refresh_library(select_current=True)
        self.category_combo.setEditText(clean_category)
        self.statusBar().showMessage(f"Folder created: {clean_category}. Click Move or drag a review into it.", 3500)

    def _new_review(self) -> None:
        """Create a new review and focus the first field."""
        self._autosave()
        review = self.view_model.create_review()
        self._populate_form(review)
        self._refresh_library(select_current=True)
        self._refresh_preview(save=False)
        first_widget = next(iter(self._field_widgets.values()), None)
        if first_widget is not None:
            first_widget.setFocus()

    def _duplicate_review(self) -> None:
        """Duplicate the current review."""
        self._autosave()
        review = self.view_model.duplicate_current_review()
        self._populate_form(review)
        self._refresh_library(select_current=True)
        self._refresh_preview(save=False)
        self.statusBar().showMessage("Review duplicated", 2500)

    def _delete_review(self) -> None:
        """Delete the selected review or reviews after confirmation."""
        selected_review_ids = self._selected_review_ids()
        if not selected_review_ids:
            selected_review_ids = [self.view_model.current_review.id]

        if len(selected_review_ids) == 1:
            review = self._review_by_id(selected_review_ids[0]) or self.view_model.current_review
            message = f"Delete '{review.display_title()}'? This cannot be undone."
            title = "Delete Review"
        else:
            message = f"Delete {len(selected_review_ids)} selected reviews? This cannot be undone."
            title = "Delete Reviews"
        response = QMessageBox.question(
            self,
            title,
            message,
        )
        if response != QMessageBox.StandardButton.Yes:
            return
        deleted_count = self.view_model.delete_reviews(selected_review_ids)
        self._populate_form(self.view_model.current_review)
        self._refresh_library(select_current=True)
        self._refresh_preview(save=False)
        self.statusBar().showMessage(f"Deleted {deleted_count} review{'s' if deleted_count != 1 else ''}", 2500)

    def _selected_review_ids(self) -> list[str]:
        """Return selected review ids, excluding folder/category rows."""
        ids: list[str] = []
        for item in self.review_tree.selectedItems():
            review_id = str(item.data(0, Qt.ItemDataRole.UserRole) or "")
            if review_id:
                ids.append(review_id)
        return list(dict.fromkeys(ids))

    def _review_by_id(self, review_id: str) -> Review | None:
        """Return a review from the current library by id if present."""
        for review in self.view_model.list_reviews():
            if review.id == review_id:
                return review
        return None

    def _open_settings(self) -> None:
        """Open settings and apply changes."""
        dialog = SettingsDialog(self.view_model.settings, self)
        if dialog.exec() != SettingsDialog.DialogCode.Accepted:
            return
        settings = dialog.updated_settings()
        self.view_model.update_settings(settings)
        self.autosave_timer.setInterval(settings.autosave_interval_seconds * 1000)
        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_theme(app, settings.theme, settings.font_size)
        self.statusBar().showMessage("Settings saved", 2500)

    def _open_exif_cleaner(self) -> None:
        """Open the local image metadata removal workflow."""
        dialog = ExifCleanerDialog(self.view_model.image_metadata_service, self)
        dialog.exec()

    def _open_template_manager(self) -> None:
        """Open template profile manager and switch the active profile if requested."""
        dialog = TemplateManagerDialog(
            self.view_model.template_service,
            self.view_model.current_review.template_id,
            self,
        )
        if dialog.exec() != TemplateManagerDialog.DialogCode.Accepted:
            return
        try:
            self.view_model.switch_template(dialog.selected_template_id)
            self._build_central_editor()
            self._populate_form(self.view_model.current_review)
            self._refresh_preview(save=True)
            self.statusBar().showMessage(f"Template profile switched to {dialog.selected_template_id}", 3000)
        except Exception as exc:
            LOGGER.exception("Template switch failed")
            QMessageBox.critical(self, "Template Switch Failed", str(exc))

    def _undo(self) -> None:
        """Run undo on the focused editor widget when supported."""
        widget = QApplication.focusWidget()
        if widget is not None and hasattr(widget, "undo"):
            widget.undo()

    def _redo(self) -> None:
        """Run redo on the focused editor widget when supported."""
        widget = QApplication.focusWidget()
        if widget is not None and hasattr(widget, "redo"):
            widget.redo()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Save work before closing."""
        try:
            self.view_model.save_current_review()
        except Exception as exc:
            LOGGER.exception("Final save failed")
            response = QMessageBox.warning(
                self,
                "Save Failed",
                f"Review Studio could not save your latest changes:\n{exc}\n\nClose anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if response != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        event.accept()