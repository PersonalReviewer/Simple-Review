"""Main-window view model.

The view model coordinates application services and exposes GUI-friendly
operations. It intentionally contains no Qt types, which keeps business
workflow behavior testable without launching a desktop session.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from review_studio.domain.models import RatingField, Review
from review_studio.domain.template_schema import FieldNamespace, ReviewTemplate, TemplateField
from review_studio.domain.value_objects import RatingValue, parse_rating
from review_studio.exporters.export_service import ExportFormat, ExportService
from review_studio.services.image_metadata_service import ImageMetadataService
from review_studio.services.review_service import ReviewService
from review_studio.services.template_service import TemplateService
from review_studio.storage.settings import UserSettings


class MainViewModel:
    """State and workflows for the main Review Studio window."""

    def __init__(
        self,
        review_service: ReviewService,
        template_service: TemplateService,
        export_service: ExportService,
        image_metadata_service: ImageMetadataService | None = None,
    ) -> None:
        self.review_service = review_service
        self.template_service = template_service
        self.export_service = export_service
        self.image_metadata_service = image_metadata_service or ImageMetadataService()
        self.settings = review_service.settings
        self.current_review = self._restore_or_create_review()

    @property
    def current_template(self) -> ReviewTemplate:
        """Return the template that drives the active review editor."""
        return self.template_service.get_template(self.current_review.template_id)

    def _restore_or_create_review(self) -> Review:
        """Restore the most recent review, or create a new one."""
        for review_id in self.settings.recent_review_ids:
            try:
                return self.review_service.repository.load(review_id)
            except Exception:
                continue
        reviews = self.review_service.list_reviews()
        if reviews:
            return reviews[0]
        return self.review_service.create_review()

    def create_review(self) -> Review:
        """Create and select a new review."""
        self.current_review = self.review_service.create_review()
        return self.current_review

    def create_trip_report(self) -> Review:
        """Create and select a new trip report."""
        self.current_review = self.review_service.create_trip_report()
        return self.current_review

    def select_review(self, review_id: str) -> Review:
        """Load and select an existing review."""
        self.current_review = self.review_service.repository.load(review_id)
        self.review_service.save_review(self.current_review)
        return self.current_review

    def duplicate_current_review(self) -> Review:
        """Duplicate and select the current review."""
        self.current_review = self.review_service.duplicate_review(self.current_review)
        return self.current_review

    def delete_current_review(self) -> None:
        """Delete the current review and select a safe replacement."""
        deleted_id = self.current_review.id
        self.review_service.delete_review(deleted_id)
        reviews = self.review_service.list_reviews()
        self.current_review = reviews[0] if reviews else self.review_service.create_review()

    def delete_reviews(self, review_ids: list[str]) -> int:
        """Delete selected reviews and select a safe replacement.

        Duplicate ids are ignored while preserving the user's selection order.
        Returns the number of unique reviews deleted.
        """
        unique_ids = list(dict.fromkeys(review_id for review_id in review_ids if review_id))
        if not unique_ids:
            return 0
        for review_id in unique_ids:
            self.review_service.delete_review(review_id)
        reviews = self.review_service.list_reviews()
        self.current_review = reviews[0] if reviews else self.review_service.create_review()
        return len(unique_ids)

    def list_reviews(self) -> list[Review]:
        """Return all reviews for the library."""
        return self.review_service.list_reviews()

    def search_reviews(self, query: str) -> list[Review]:
        """Search existing reviews."""
        return self.review_service.search_reviews(query)

    def update_field(self, field_name: str, value: str) -> None:
        """Update a top-level text field on the current review."""
        if not hasattr(self.current_review, field_name):
            msg = f"Unknown review field: {field_name}"
            raise AttributeError(msg)
        setattr(self.current_review, field_name, value)
        if field_name in {"title", "vendor", "product"}:
            self.current_review.title = self._automatic_title()

    def update_template_field(self, field: TemplateField, value: str) -> None:
        """Update a template-defined field on the current review."""
        self.current_review.set_field_value(field.namespace, field.key, value)
        if field.key in {"vendor_name", "product_name"}:
            self.current_review.title = self._automatic_title()

    def switch_template(self, template_id: str) -> None:
        """Switch the current review and default setting to a template profile."""
        self.template_service.get_template(template_id)
        self.current_review.template_id = template_id
        self.settings.default_template_id = template_id
        self.review_service.save_settings(self.settings)
        self.save_current_review()

    def categories(self) -> list[str]:
        """Return known review folders/categories."""
        discovered = {review.category or "Uncategorized" for review in self.review_service.list_reviews()}
        configured = {category.strip() or "Uncategorized" for category in self.settings.review_categories}
        return sorted({"Uncategorized", *configured, *discovered})

    def create_category(self, category: str) -> str:
        """Create/select a category without moving the active review."""
        clean_category = category.strip() or "Uncategorized"
        categories = self.categories()
        if clean_category not in categories:
            categories.append(clean_category)
            self.settings.review_categories = sorted(set(categories))
            self.review_service.save_settings(self.settings)
        return clean_category

    def set_current_category(self, category: str) -> None:
        """Move the current review into a library category/folder."""
        clean_category = self.create_category(category)
        self.current_review.category = clean_category
        self.save_current_review()

    def move_review_to_category(self, review_id: str, category: str) -> None:
        """Move any saved review into a category/folder."""
        clean_category = self.create_category(category)
        if review_id == self.current_review.id:
            self.set_current_category(clean_category)
            return
        review = self.review_service.repository.load(review_id)
        review.category = clean_category
        self.review_service.save_review(review)

    def template_field_value(self, field: TemplateField) -> str:
        """Return the current value for a template-defined field."""
        return self.current_review.field_value(field.namespace, field.key)

    def _automatic_title(self) -> str:
        """Build the generated title used by the current form workflow."""
        if self.current_review.template_id == "default_trip_report":
            substance = self.current_review.values.get("substance", "")
            dosage = self.current_review.values.get("dosage", "")
            time_val = self.current_review.values.get("start_time", "")
            parts = [p.strip() for p in [substance, f"({dosage})" if dosage else "", f"@ {time_val}" if time_val else ""] if p.strip()]
            return " ".join(parts) if parts else "Untitled Trip Report"

        parts = [
            part.strip()
            for part in [
                self.current_review.values.get("vendor_name", self.current_review.vendor),
                self.current_review.values.get("product_name", self.current_review.product),
            ]
            if part.strip()
        ]
        return " - ".join(parts) if parts else "Untitled Review"

    def update_rating_value(self, rating_name: str, value: str | RatingValue) -> None:
        """Update a rating value."""
        self._rating_field(rating_name).value = parse_rating(value)

    def update_rating_comments(self, rating_name: str, comments: str) -> None:
        """Update comments for a rating."""
        self._rating_field(rating_name).comments = comments

    def _rating_field(self, rating_name: str) -> RatingField:
        """Return a named rating field."""
        if not hasattr(self.current_review.ratings, rating_name):
            msg = f"Unknown rating field: {rating_name}"
            raise AttributeError(msg)
        return cast(RatingField, getattr(self.current_review.ratings, rating_name))

    def render_raw_preview(self) -> str:
        """Render the current review in the selected template's native format."""
        return self.template_service.render_review(self.current_review)

    def render_export(self, export_format: ExportFormat) -> str:
        """Render the current review in an export format."""
        return self.export_service.render(self.current_review, export_format)

    def export_current_review(self, export_format: ExportFormat, path: Path) -> None:
        """Export the current review."""
        self.export_service.export_to_file(self.current_review, export_format, path)

    def save_current_review(self) -> None:
        """Persist current review."""
        self.review_service.save_review(self.current_review)

    def update_settings(self, settings: UserSettings) -> None:
        """Persist updated settings."""
        self.settings = settings
        self.review_service.save_settings(settings)

    def validation_messages(self) -> list[str]:
        """Return non-blocking validation guidance for the current review."""
        messages: list[str] = []
        for field in self.current_template.iter_fields():
            if field.required and not self.current_review.field_value(field.namespace, field.key).strip():
                messages.append(f"{field.label} is missing.")
        return messages

    def as_form_values(self) -> dict[str, Any]:
        """Return current review values for form population."""
        return self.current_review.to_dict()