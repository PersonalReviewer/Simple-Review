"""Dialog for removing image metadata."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from review_studio.services.image_metadata_service import (
    ImageCleanupOptions,
    ImageMetadataService,
    ImageOutputMode,
)


class ExifCleanerDialog(QDialog):
    """Simple image metadata removal workflow."""

    onion_providers = {
        "DeadDrop": "http://deaddrop3m4nxdjueza5vgebsruydayytjy2lf3vj5eqmywtdv7fcrqd.onion/",
        "ImageGirl": "http://apig2yathivs562p4gkgtpe4azrqlgxohopsgddrkjxkegkxdt75wqqd.onion/",
        "Black Cloud": "http://bcloudwenjxgcxjh6uheyt72a5isimzgg4kv5u74jb2s22y3hzpwh6id.onion",
    }

    def __init__(self, service: ImageMetadataService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Remove Image Metadata")
        self.resize(720, 520)
        self._service = service

        self.file_list = QListWidget()
        add_files = QPushButton("Add Images…")
        add_files.clicked.connect(self._add_files)
        remove_selected = QPushButton("Remove Selected")
        remove_selected.clicked.connect(lambda: [self.file_list.takeItem(row) for row in sorted(self._selected_rows(), reverse=True)])
        clear = QPushButton("Clear")
        clear.clicked.connect(self.file_list.clear)

        file_buttons = QHBoxLayout()
        file_buttons.addWidget(add_files)
        file_buttons.addWidget(remove_selected)
        file_buttons.addWidget(clear)

        self.overwrite = QRadioButton("Overwrite originals")
        self.same_folder = QRadioButton("Same folder, new name")
        self.output_folder = QRadioButton("New folder, same names")
        self.same_folder.setChecked(True)
        self.output_group = QButtonGroup(self)
        for button in [self.overwrite, self.same_folder, self.output_folder]:
            self.output_group.addButton(button)

        self.suffix = QLineEdit("_clean")
        self.folder = QLineEdit()
        self.upload_to_imgur = QCheckBox("Upload cleaned images to Imgur after processing (experimental, off by default)")
        self.imgur_client_id = QLineEdit()
        self.imgur_client_id.setPlaceholderText("Imgur Client ID (required only when upload is enabled)")
        imgur_warning = QLabel("Not recommended to use Imgur; use an onion image provider when privacy matters.")
        imgur_warning.setWordWrap(True)
        onion_button = QPushButton("Onion Providers")
        onion_button.clicked.connect(self._show_onion_providers)
        onion_row = QHBoxLayout()
        onion_row.addWidget(imgur_warning, 1)
        onion_row.addWidget(onion_button)
        browse_folder = QPushButton("Browse…")
        browse_folder.clicked.connect(self._choose_folder)
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.folder)
        folder_row.addWidget(browse_folder)

        form = QFormLayout()
        form.addRow("Mode", self.overwrite)
        form.addRow("", self.same_folder)
        form.addRow("", self.output_folder)
        form.addRow("New name suffix", self.suffix)
        form.addRow("Output folder", folder_row)
        form.addRow("Experimental upload", self.upload_to_imgur)
        form.addRow("Privacy note", onion_row)
        form.addRow("Imgur Client ID", self.imgur_client_id)

        self.results = QTextEdit()
        self.results.setReadOnly(True)
        self.results.setPlaceholderText("Results will appear here.")

        run_button = QPushButton("Remove Metadata")
        run_button.clicked.connect(self._run)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        note = QLabel("All processing is local. Output strips EXIF/common metadata and keeps pixel content.")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addWidget(self.file_list, 1)
        layout.addLayout(file_buttons)
        layout.addLayout(form)
        layout.addWidget(run_button)
        layout.addWidget(self.results, 1)
        layout.addWidget(buttons)

    def _selected_rows(self) -> list[int]:
        return [self.file_list.row(item) for item in self.file_list.selectedItems()]

    def _add_files(self) -> None:
        filters = "Images (*.jpg *.jpeg *.png *.webp *.tif *.tiff *.bmp *.gif);;All Files (*)"
        paths, _selected = QFileDialog.getOpenFileNames(self, "Choose Images", "", filters)
        existing = {self.file_list.item(index).text() for index in range(self.file_list.count())}
        for path in paths:
            if path not in existing:
                self.file_list.addItem(path)

    def _choose_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Choose Output Folder", self.folder.text())
        if selected:
            self.folder.setText(selected)

    def _show_onion_providers(self) -> None:
        """Show copy-friendly onion image provider options."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Onion Image Providers")
        dialog.resize(720, 320)

        text = "\n".join(f"{name} - {url}" for name, url in self.onion_providers.items())
        body = QTextEdit()
        body.setReadOnly(True)
        body.setPlainText(text)

        copy_button = QPushButton("Copy Providers")
        copy_button.clicked.connect(lambda: QApplication.clipboard().setText(text))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)

        layout = QVBoxLayout(dialog)
        note = QLabel(
            "These are provided as manual copy/paste options. Review Studio does not open or upload to onion services automatically."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addWidget(body, 1)
        layout.addWidget(copy_button)
        layout.addWidget(buttons)
        dialog.exec()

    def _options(self) -> ImageCleanupOptions:
        if self.overwrite.isChecked():
            return ImageCleanupOptions(
                output_mode=ImageOutputMode.OVERWRITE,
                upload_to_imgur=self.upload_to_imgur.isChecked(),
                imgur_client_id=self.imgur_client_id.text().strip(),
            )
        if self.output_folder.isChecked():
            folder_text = self.folder.text().strip()
            if not folder_text:
                raise ValueError("Choose an output folder first.")
            return ImageCleanupOptions(
                output_mode=ImageOutputMode.OUTPUT_FOLDER,
                output_folder=Path(folder_text),
                upload_to_imgur=self.upload_to_imgur.isChecked(),
                imgur_client_id=self.imgur_client_id.text().strip(),
            )
        return ImageCleanupOptions(
            output_mode=ImageOutputMode.SAME_FOLDER_SUFFIX,
            suffix=self.suffix.text().strip() or "_clean",
            upload_to_imgur=self.upload_to_imgur.isChecked(),
            imgur_client_id=self.imgur_client_id.text().strip(),
        )

    def _run(self) -> None:
        paths = [Path(self.file_list.item(index).text()) for index in range(self.file_list.count())]
        if not paths:
            QMessageBox.information(self, "No Images", "Add one or more images first.")
            return
        try:
            options = self._options()
        except ValueError as exc:
            QMessageBox.warning(self, "Output Required", str(exc))
            return
        results = self._service.clean_images(paths, options)
        lines = []
        success_count = 0
        for result in results:
            status = "OK" if result.success else "FAILED"
            if result.success:
                success_count += 1
            upload = f" | Imgur: {result.uploaded_url}" if result.uploaded_url else ""
            lines.append(f"{status}: {result.source} -> {result.destination} ({result.message}){upload}")
        self.results.setPlainText("\n".join(lines))
        QMessageBox.information(self, "Metadata Removal Complete", f"Processed {success_count}/{len(results)} images successfully.")
