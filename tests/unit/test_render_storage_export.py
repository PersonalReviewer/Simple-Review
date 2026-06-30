"""Tests for template rendering, storage, settings, and exports."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from review_studio.domain.models import Review
from review_studio.exporters.export_service import ExportFormat, ExportService
from review_studio.storage.repository import ReviewRepository
from review_studio.storage.settings import SettingsStore, UserSettings
from review_studio.templates.engine import TemplateEngine


class RenderStorageExportTests(unittest.TestCase):
    """Verify non-GUI workflows that protect user work."""

    def test_template_renders_rating_changes(self) -> None:
        review = Review(vendor="Vendor", market="Market", product="Product")
        engine = TemplateEngine()

        review.rating_values["quality"] = "4"
        before = engine.render(review)
        review.rating_values["quality"] = "6"
        after = engine.render(review)

        self.assertIn("[td] Quality/Potency Rating [/td]", before)
        self.assertIn("𝟒/𝟕 –[color=#90d00f] 𝐀𝐃𝐄𝐐𝐔𝐀𝐓𝐄 [/color]", before)
        self.assertIn("𝟔/𝟕 –[color=#5bc0de] 𝐀𝐃𝐕𝐀𝐍𝐂𝐄𝐃 [/color]", after)

    def test_repository_round_trip_search_duplicate_delete(self) -> None:
        with TemporaryDirectory() as temporary:
            repository = ReviewRepository(Path(temporary))
            review = Review(vendor="Searchable Vendor", product="Widget")
            repository.save(review)

            loaded = repository.load(review.id)
            duplicate = loaded.duplicate()
            repository.save(duplicate)

            self.assertEqual(loaded.vendor, "Searchable Vendor")
            self.assertEqual(len(repository.search("searchable")), 2)
            self.assertEqual(len(repository.list_reviews()), 2)
            repository.delete(review.id)
            self.assertEqual(len(repository.list_reviews()), 1)

    def test_settings_round_trip(self) -> None:
        with TemporaryDirectory() as temporary:
            store = SettingsStore(Path(temporary) / "settings.json")
            settings = UserSettings(theme="light", font_size=14, autosave_interval_seconds=9)
            store.save(settings)
            loaded = store.load()

            self.assertEqual(loaded.theme, "light")
            self.assertEqual(loaded.font_size, 14)
            self.assertEqual(loaded.autosave_interval_seconds, 9)

    def test_export_formats(self) -> None:
        review = Review(vendor="Vendor", market="Market", product="Product", summary="Summary")
        review.rating_values["quality"] = "6"
        exporter = ExportService(TemplateEngine())

        self.assertIn("[table]", exporter.render(review, ExportFormat.BBCODE))
        self.assertIn("Quality/Potency Rating", exporter.render(review, ExportFormat.MARKDOWN))
        self.assertIn("𝟔/𝟕 – 𝐀𝐃𝐕𝐀𝐍𝐂𝐄𝐃", exporter.render(review, ExportFormat.TEXT))
        self.assertIn("<table", exporter.render(review, ExportFormat.HTML))
        self.assertIn("<span style=\"color: #5bc0de; font-weight: 600;\"> 𝐀𝐃𝐕𝐀𝐍𝐂𝐄𝐃 </span>", exporter.render(review, ExportFormat.HTML))
        self.assertIn('"vendor": "Vendor"', exporter.render(review, ExportFormat.JSON))

    def test_trip_report_export_formats(self) -> None:
        review = Review(template_id="default_trip_report")
        review.values["substance"] = "Acid"
        review.values["dosage"] = "150ug"
        review.values["start_time"] = "2026-06-30 @ 10:00"
        review.values["timeline_log"] = "* T+00:00 Ingested"
        exporter = ExportService(TemplateEngine())

        self.assertIn("# Acid Experience Report", exporter.render(review, ExportFormat.MARKDOWN))
        self.assertIn("150ug", exporter.render(review, ExportFormat.HTML))
        self.assertIn("Acid", exporter.render(review, ExportFormat.TEXT))


if __name__ == "__main__":
    unittest.main()
