"""JSON review repository and library search."""

from __future__ import annotations

import logging
from pathlib import Path

from review_studio.domain.errors import StorageError
from review_studio.domain.models import Review
from review_studio.storage.json_store import atomic_write_json, read_json
from review_studio.utils.paths import reviews_dir


LOGGER = logging.getLogger(__name__)


class ReviewRepository:
    """Store individual reviews as portable JSON files."""

    extension = ".reviewstudio.json"

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or reviews_dir()
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, review_id: str) -> Path:
        """Return the file path for a review id."""
        safe_id = "".join(char for char in review_id if char.isalnum() or char in {"-", "_"})
        return self.root / f"{safe_id}{self.extension}"

    def save(self, review: Review) -> Path:
        """Persist a review using an atomic write."""
        review.touch()
        path = self.path_for(review.id)
        atomic_write_json(path, review.to_dict())
        return path

    def load(self, review_id: str) -> Review:
        """Load a review by id."""
        path = self.path_for(review_id)
        try:
            data = read_json(path, {})
        except StorageError:
            backup_path = path.with_suffix(path.suffix + ".bak")
            if not backup_path.exists():
                raise
            LOGGER.warning("Review file %s is unreadable; loading backup %s", path, backup_path)
            data = read_json(backup_path, {})
        return Review.from_dict(data)

    def delete(self, review_id: str) -> None:
        """Delete a review if it exists."""
        path = self.path_for(review_id)
        if path.exists():
            path.unlink()

    def list_reviews(self) -> list[Review]:
        """Load all reviews in the library, newest first."""
        reviews: list[Review] = []
        for path in sorted(self.root.glob(f"*{self.extension}")):
            try:
                reviews.append(Review.from_dict(read_json(path, {})))
            except Exception as exc:
                LOGGER.warning("Skipping unreadable review file %s: %s", path, exc)
                continue
        return sorted(reviews, key=lambda review: review.updated_at, reverse=True)

    def search(self, query: str) -> list[Review]:
        """Search reviews by common metadata and comments."""
        normalized = query.strip().lower()
        if not normalized:
            return self.list_reviews()
        results: list[Review] = []
        for review in self.list_reviews():
            haystack = "\n".join(
                [
                    review.title,
                    review.vendor,
                    review.market,
                    review.product,
                    review.category,
                    review.summary,
                    review.vendor_comments,
                    review.product_comments,
                    "\n".join(review.values.values()),
                    "\n".join(review.comments.values()),
                ]
            ).lower()
            if normalized in haystack:
                results.append(review)
        return results