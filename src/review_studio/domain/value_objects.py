"""Domain value objects used throughout Review Studio.

The value objects in this module intentionally have no GUI or persistence
dependencies. They define stable application concepts that can be reused by the
editor, template renderer, exporters, tests, and future extension points.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RatingValue(Enum):
    """Supported review rating values.

    Ratings are displayed as fixed labels so every output format remains
    consistent. ``NOT_APPLICABLE`` intentionally renders as ``N/A`` instead of a
    numeric score.
    """

    NOT_APPLICABLE = "na"
    FAILURE = "1"
    POOR = "2"
    BASIC = "3"
    ADEQUATE = "4"
    STRONG = "5"
    ADVANCED = "6"
    EXCEPTIONAL = "7"

    @property
    def score(self) -> int | None:
        """Return the numeric score, or ``None`` for not applicable."""
        if self is RatingValue.NOT_APPLICABLE:
            return None
        return int(self.value)

    @property
    def label(self) -> str:
        """Return the human-readable rating label."""
        return RATING_DEFINITIONS[self].label

    @property
    def description(self) -> str:
        """Return guidance text for this rating."""
        return RATING_DEFINITIONS[self].description

    def format(self) -> str:
        """Return the canonical text used in generated reviews."""
        if self is RatingValue.NOT_APPLICABLE:
            return "N/A"
        return f"{self.value}/7 {self.label}"


@dataclass(frozen=True, slots=True)
class RatingDefinition:
    """Display metadata for a rating value."""

    value: RatingValue
    label: str
    description: str


RATING_DEFINITIONS: dict[RatingValue, RatingDefinition] = {
    RatingValue.NOT_APPLICABLE: RatingDefinition(
        RatingValue.NOT_APPLICABLE,
        "N/A",
        "This area does not apply to the review.",
    ),
    RatingValue.FAILURE: RatingDefinition(
        RatingValue.FAILURE,
        "Failure",
        "Unacceptable or failed to meet the basic requirement.",
    ),
    RatingValue.POOR: RatingDefinition(
        RatingValue.POOR,
        "Poor",
        "Significant issues; below a reasonable baseline.",
    ),
    RatingValue.BASIC: RatingDefinition(
        RatingValue.BASIC,
        "Basic",
        "Functional but limited, inconsistent, or minimally acceptable.",
    ),
    RatingValue.ADEQUATE: RatingDefinition(
        RatingValue.ADEQUATE,
        "Adequate",
        "Acceptable overall with room for improvement.",
    ),
    RatingValue.STRONG: RatingDefinition(
        RatingValue.STRONG,
        "Strong",
        "Good quality and reliable in normal use.",
    ),
    RatingValue.ADVANCED: RatingDefinition(
        RatingValue.ADVANCED,
        "Advanced",
        "Very good execution with only minor concerns.",
    ),
    RatingValue.EXCEPTIONAL: RatingDefinition(
        RatingValue.EXCEPTIONAL,
        "Exceptional",
        "Excellent result that meaningfully exceeds expectations.",
    ),
}


def parse_rating(value: str | RatingValue | None) -> RatingValue:
    """Parse persisted or UI-provided rating data into a ``RatingValue``.

    Args:
        value: Raw rating value from storage, UI, or existing domain object.

    Returns:
        A valid ``RatingValue``. Unknown or blank values are treated as N/A so
        old/corrupt user files degrade safely instead of crashing the app.
    """
    if isinstance(value, RatingValue):
        return value
    if value is None:
        return RatingValue.NOT_APPLICABLE
    normalized = str(value).strip().lower()
    for rating in RatingValue:
        if normalized in {rating.value.lower(), rating.name.lower(), rating.format().lower()}:
            return rating
    if normalized in {"n/a", "na", "not applicable"}:
        return RatingValue.NOT_APPLICABLE
    return RatingValue.NOT_APPLICABLE
