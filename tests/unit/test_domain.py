"""Unit tests for core domain models and value objects."""

from __future__ import annotations

import unittest

from review_studio.domain.models import Review
from review_studio.domain.value_objects import RatingValue, parse_rating


class DomainTests(unittest.TestCase):
    """Verify stable domain behavior."""

    def test_rating_formatting(self) -> None:
        self.assertEqual(RatingValue.NOT_APPLICABLE.format(), "N/A")
        self.assertEqual(RatingValue.FAILURE.format(), "1/7 Failure")
        self.assertEqual(RatingValue.ADVANCED.format(), "6/7 Advanced")
        self.assertEqual(RatingValue.EXCEPTIONAL.format(), "7/7 Exceptional")

    def test_parse_rating_is_tolerant(self) -> None:
        self.assertIs(parse_rating("6"), RatingValue.ADVANCED)
        self.assertIs(parse_rating("6/7 Advanced"), RatingValue.ADVANCED)
        self.assertIs(parse_rating("not applicable"), RatingValue.NOT_APPLICABLE)
        self.assertIs(parse_rating("unknown"), RatingValue.NOT_APPLICABLE)

    def test_review_round_trip_and_duplicate(self) -> None:
        review = Review(vendor="Acme", product="Anvil", market="Industrial")
        review.ratings.overall.value = RatingValue.STRONG
        data = review.to_dict()
        loaded = Review.from_dict(data)
        duplicate = loaded.duplicate()

        self.assertEqual(loaded.vendor, "Acme")
        self.assertEqual(loaded.ratings.overall.value, RatingValue.STRONG)
        self.assertNotEqual(loaded.id, duplicate.id)
        self.assertIn("Copy", duplicate.title)


if __name__ == "__main__":
    unittest.main()
