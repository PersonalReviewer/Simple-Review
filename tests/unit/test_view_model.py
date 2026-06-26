"""Tests for GUI-independent view model workflows."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from review_studio.exporters.export_service import ExportService
from review_studio.gui.view_models.main_view_model import MainViewModel
from review_studio.services.review_service import ReviewService
from review_studio.services.template_service import TemplateService
from review_studio.storage.repository import ReviewRepository
from review_studio.storage.settings import SettingsStore, UserSettings
from review_studio.templates.engine import TemplateEngine


class ViewModelTests(unittest.TestCase):
    """Verify main-window workflows without requiring Qt."""

    def test_review_workflow(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            engine = TemplateEngine()
            view_model = MainViewModel(
                ReviewService(ReviewRepository(root / "reviews"), SettingsStore(root / "settings.json")),
                TemplateService(engine),
                ExportService(engine),
            )
            fields = {field.identity: field for field in view_model.current_template.iter_fields()}

            view_model.update_template_field(fields["value.vendor_name"], "Vendor")
            view_model.update_template_field(fields["value.product_name"], "Product")
            view_model.update_template_field(fields["rating.quality"], "6")
            view_model.update_template_field(fields["comment.quality"], "Quality comment")
            view_model.save_current_review()

            raw_preview = view_model.render_raw_preview()
            duplicate = view_model.duplicate_current_review()

            self.assertIn("/u/Vendor", raw_preview)
            self.assertIn("Product", raw_preview)
            self.assertIn("𝟔/𝟕 –[color=#5bc0de] 𝐀𝐃𝐕𝐀𝐍𝐂𝐄𝐃 [/color]", raw_preview)
            self.assertIn("Quality comment", raw_preview)
            self.assertIn("Copy", duplicate.title)
            self.assertGreaterEqual(len(view_model.list_reviews()), 2)

    def test_settings_can_move_library_folder(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            engine = TemplateEngine()
            service = ReviewService(ReviewRepository(root / "reviews"), SettingsStore(root / "settings.json"))
            view_model = MainViewModel(service, TemplateService(engine), ExportService(engine))
            new_library = root / "new-library"

            view_model.update_settings(UserSettings(review_library_folder=str(new_library)))

            self.assertEqual(service.repository.root, new_library)
            self.assertTrue(new_library.exists())

    def test_review_category_round_trip_and_search(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            engine = TemplateEngine()
            service = ReviewService(ReviewRepository(root / "reviews"), SettingsStore(root / "settings.json"))
            view_model = MainViewModel(service, TemplateService(engine), ExportService(engine))

            view_model.set_current_category("Vendors")
            review_id = view_model.current_review.id
            loaded = service.repository.load(review_id)

            self.assertEqual(loaded.category, "Vendors")
            self.assertEqual(service.search_reviews("vendors")[0].id, review_id)

    def test_delete_reviews_removes_multiple_and_selects_replacement(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            engine = TemplateEngine()
            service = ReviewService(ReviewRepository(root / "reviews"), SettingsStore(root / "settings.json"))
            view_model = MainViewModel(service, TemplateService(engine), ExportService(engine))

            first_id = view_model.current_review.id
            second_id = view_model.create_review().id
            third_id = view_model.create_review().id

            deleted_count = view_model.delete_reviews([first_id, second_id, second_id])

            self.assertEqual(deleted_count, 2)
            remaining_ids = {review.id for review in view_model.list_reviews()}
            self.assertEqual(remaining_ids, {third_id})
            self.assertEqual(view_model.current_review.id, third_id)


if __name__ == "__main__":
    unittest.main()
