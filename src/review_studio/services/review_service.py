"""Application service for review-library workflows."""

from __future__ import annotations

from review_studio.domain.models import Review
from review_studio.domain.template_schema import FieldNamespace
from review_studio.storage.repository import ReviewRepository
from review_studio.storage.settings import SettingsStore, UserSettings


class ReviewService:
    """Coordinate review creation, persistence, duplication, and search."""

    def __init__(self, repository: ReviewRepository, settings_store: SettingsStore) -> None:
        self.repository = repository
        self.settings_store = settings_store
        self.settings = settings_store.load()

    def create_review(self) -> Review:
        """Create and persist a new empty review."""
        template_id = self.settings.default_template_id
        if template_id == "default_bbcode" or template_id == "default_trip_report":
            template_id = "default_review"
        review = Review(template_id=template_id)
        self.save_review(review)
        return review

    def create_trip_report(self) -> Review:
        """Create and persist a new empty trip report."""
        review = Review(template_id="default_trip_report", category="Trip Reports")
        from datetime import datetime
        now = datetime.now()
        cur_date = now.strftime("%Y-%m-%d")
        cur_time = now.strftime("%H:%M")
        review.set_field_value(FieldNamespace.VALUE, "start_time", f"{cur_date} @ {cur_time}")
        review.set_field_value(FieldNamespace.VALUE, "timeline_log", f"* **T+00:00** ({cur_time}) - [Ingestion] Dose administered.")
        self.save_review(review)
        return review

    def save_review(self, review: Review) -> None:
        """Persist a review and update recent-review settings."""
        self.repository.save(review)
        self._mark_recent(review.id)

    def duplicate_review(self, review: Review) -> Review:
        """Duplicate and persist a review."""
        duplicate = review.duplicate()
        self.save_review(duplicate)
        return duplicate

    def delete_review(self, review_id: str) -> None:
        """Delete a review and remove it from recents."""
        self.repository.delete(review_id)
        self.settings.recent_review_ids = [item for item in self.settings.recent_review_ids if item != review_id]
        self.settings_store.save(self.settings)

    def list_reviews(self) -> list[Review]:
        """Return all reviews."""
        return self.repository.list_reviews()

    def search_reviews(self, query: str) -> list[Review]:
        """Search the review library."""
        return self.repository.search(query)

    def save_settings(self, settings: UserSettings) -> None:
        """Persist settings and update service state."""
        self.settings = settings
        self.repository.root = settings.normalized_library_folder()
        self.repository.root.mkdir(parents=True, exist_ok=True)
        self.settings_store.save(settings)

    def _mark_recent(self, review_id: str) -> None:
        """Record a review id as recently used."""
        recents = [item for item in self.settings.recent_review_ids if item != review_id]
        recents.insert(0, review_id)
        self.settings.recent_review_ids = recents[:20]
        self.settings_store.save(self.settings)