"""Core domain models for Review Studio."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from review_studio.domain.template_schema import FieldNamespace, ReviewTemplate
from review_studio.domain.value_objects import RatingValue, parse_rating


CURRENT_REVIEW_SCHEMA_VERSION = 1


def utc_now() -> datetime:
    """Return the current UTC timestamp with timezone information."""
    return datetime.now(tz=UTC)


def timestamp() -> str:
    """Return an ISO-8601 UTC timestamp for persistence."""
    return utc_now().isoformat()


@dataclass(slots=True)
class RatingField:
    """A rating plus optional explanatory comments."""

    value: RatingValue = RatingValue.NOT_APPLICABLE
    comments: str = ""

    def to_dict(self) -> dict[str, str]:
        """Serialize the rating for JSON storage."""
        return {"value": self.value.value, "comments": self.comments}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RatingField:
        """Deserialize a rating field from JSON-compatible data."""
        if not isinstance(data, dict):
            return cls()
        return cls(value=parse_rating(data.get("value")), comments=str(data.get("comments", "")))


@dataclass(slots=True)
class ReviewRatings:
    """Reusable rating group for the review editor."""

    quality: RatingField = field(default_factory=RatingField)
    value: RatingField = field(default_factory=RatingField)
    accuracy: RatingField = field(default_factory=RatingField)
    communication: RatingField = field(default_factory=RatingField)
    shipping: RatingField = field(default_factory=RatingField)
    customer_service: RatingField = field(default_factory=RatingField)
    overall: RatingField = field(default_factory=RatingField)

    def to_dict(self) -> dict[str, dict[str, str]]:
        """Serialize all ratings."""
        return {
            "quality": self.quality.to_dict(),
            "value": self.value.to_dict(),
            "accuracy": self.accuracy.to_dict(),
            "communication": self.communication.to_dict(),
            "shipping": self.shipping.to_dict(),
            "customer_service": self.customer_service.to_dict(),
            "overall": self.overall.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ReviewRatings:
        """Deserialize ratings from persisted data."""
        if not isinstance(data, dict):
            return cls()
        return cls(
            quality=RatingField.from_dict(data.get("quality")),
            value=RatingField.from_dict(data.get("value")),
            accuracy=RatingField.from_dict(data.get("accuracy")),
            communication=RatingField.from_dict(data.get("communication")),
            shipping=RatingField.from_dict(data.get("shipping")),
            customer_service=RatingField.from_dict(data.get("customer_service")),
            overall=RatingField.from_dict(data.get("overall")),
        )


@dataclass(slots=True)
class Review:
    """A complete user-authored review document."""

    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = "Untitled Review"
    vendor: str = ""
    market: str = ""
    product: str = ""
    product_url: str = ""
    purchase_date: str = ""
    purchase_price: str = ""
    currency: str = "USD"
    quantity: str = ""
    order_id: str = ""
    ratings: ReviewRatings = field(default_factory=ReviewRatings)
    vendor_comments: str = ""
    product_comments: str = ""
    market_comments: str = ""
    pricing_comments: str = ""
    shipping_information: str = ""
    customer_service_information: str = ""
    summary: str = ""
    template_id: str = "default_review"
    category: str = "Uncategorized"
    values: dict[str, str] = field(default_factory=dict)
    rating_values: dict[str, str] = field(default_factory=dict)
    comments: dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=timestamp)
    updated_at: str = field(default_factory=timestamp)
    schema_version: int = CURRENT_REVIEW_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Initialize dynamic template fields from legacy constructor values."""
        self._migrate_legacy_fields()

    def touch(self) -> None:
        """Update the modification timestamp."""
        self.updated_at = timestamp()

    def display_title(self) -> str:
        """Return a useful title for library/navigation views."""
        if self.template_id == "default_trip_report":
            substance = self.values.get("substance", "")
            dosage = self.values.get("dosage", "")
            time_val = self.values.get("start_time", "")
            parts = [p.strip() for p in [substance, f"({dosage})" if dosage else "", f"@ {time_val}" if time_val else ""] if p.strip()]
            if parts:
                generated = " ".join(parts)
                return f"{generated} Copy" if self.title.endswith(" Copy") else generated
            return "Untitled Trip Report"

        vendor = self.values.get("vendor_name", self.vendor)
        product = self.values.get("product_name", self.product)
        parts = [part.strip() for part in [vendor, product] if part.strip()]
        if parts:
            generated = " - ".join(parts)
            return f"{generated} Copy" if self.title.endswith(" Copy") else generated
        if self.title.strip() and self.title != "Untitled Review":
            return self.title.strip()
        return "Untitled Review"

    def field_value(self, namespace: FieldNamespace, key: str) -> str:
        """Return a template field value by namespace/key."""
        if namespace is FieldNamespace.RATING:
            return self.rating_values.get(key, "na")
        if namespace is FieldNamespace.COMMENT:
            return self.comments.get(key, "")
        return self.values.get(key, "")

    def set_field_value(self, namespace: FieldNamespace, key: str, value: str) -> None:
        """Set a template field value by namespace/key."""
        if namespace is FieldNamespace.RATING:
            self.rating_values[key] = value or "na"
        elif namespace is FieldNamespace.COMMENT:
            self.comments[key] = value
        else:
            self.values[key] = value
        if key in {"vendor_name", "product_name", "substance", "dosage", "start_time"}:
            self.title = self.display_title()

    def duplicate(self) -> Review:
        """Create an unsaved duplicate with a new identity."""
        data = self.to_dict()
        data["id"] = str(uuid4())
        data["title"] = f"{self.display_title()} Copy"
        now = timestamp()
        data["created_at"] = now
        data["updated_at"] = now
        return Review.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the review for JSON storage and export."""
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "title": self.title,
            "vendor": self.vendor,
            "market": self.market,
            "product": self.product,
            "product_url": self.product_url,
            "purchase_date": self.purchase_date,
            "purchase_price": self.purchase_price,
            "currency": self.currency,
            "quantity": self.quantity,
            "order_id": self.order_id,
            "ratings": self.ratings.to_dict(),
            "vendor_comments": self.vendor_comments,
            "product_comments": self.product_comments,
            "market_comments": self.market_comments,
            "pricing_comments": self.pricing_comments,
            "shipping_information": self.shipping_information,
            "customer_service_information": self.customer_service_information,
            "summary": self.summary,
            "template_id": self.template_id,
            "category": self.category,
            "values": dict(self.values),
            "rating_values": dict(self.rating_values),
            "comments": dict(self.comments),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Review:
        """Deserialize a review from JSON-compatible data."""
        review = cls(
            schema_version=int(data.get("schema_version", CURRENT_REVIEW_SCHEMA_VERSION)),
            id=str(data.get("id") or uuid4()),
            title=str(data.get("title", "Untitled Review")),
            vendor=str(data.get("vendor", "")),
            market=str(data.get("market", "")),
            product=str(data.get("product", "")),
            product_url=str(data.get("product_url", "")),
            purchase_date=str(data.get("purchase_date", "")),
            purchase_price=str(data.get("purchase_price", "")),
            currency=str(data.get("currency", "USD")),
            quantity=str(data.get("quantity", "")),
            order_id=str(data.get("order_id", "")),
            ratings=ReviewRatings.from_dict(data.get("ratings")),
            vendor_comments=str(data.get("vendor_comments", "")),
            product_comments=str(data.get("product_comments", "")),
            market_comments=str(data.get("market_comments", "")),
            pricing_comments=str(data.get("pricing_comments", "")),
            shipping_information=str(data.get("shipping_information", "")),
            customer_service_information=str(data.get("customer_service_information", "")),
            summary=str(data.get("summary", "")),
            template_id=str(data.get("template_id", "default_review")),
            category=str(data.get("category", "Uncategorized") or "Uncategorized"),
            values={str(key): str(value) for key, value in dict(data.get("values", {})).items()},
            rating_values={str(key): str(value) for key, value in dict(data.get("rating_values", {})).items()},
            comments={str(key): str(value) for key, value in dict(data.get("comments", {})).items()},
            created_at=str(data.get("created_at", timestamp())),
            updated_at=str(data.get("updated_at", timestamp())),
        )
        review._migrate_legacy_fields()
        return review

    def _migrate_legacy_fields(self) -> None:
        """Populate dynamic template values from legacy fixed fields when needed."""
        legacy_values = {
            "vendor_name": self.vendor,
            "market": self.market,
            "product_name": self.product,
            "quantity": self.quantity,
            "price": self.purchase_price,
            "picture_album_url": self.product_url,
            "album_name": "Pictures" if self.product_url else "",
            "shipping_method": self.shipping_information,
            "final_summary": self.summary,
        }
        for key, value in legacy_values.items():
            if value and key not in self.values:
                self.values[key] = value
        legacy_comments = {
            "price_value": self.pricing_comments,
            "quality": self.product_comments,
            "shipping_time": self.shipping_information,
            "overall_customer_service": self.customer_service_information,
        }
        for key, value in legacy_comments.items():
            if value and key not in self.comments:
                self.comments[key] = value
        legacy_ratings = {
            "quality": self.ratings.quality.value.value,
            "price_value": self.ratings.value.value.value,
            "overall_product": self.ratings.overall.value.value,
            "shipping_time": self.ratings.shipping.value.value,
            "overall_customer_service": self.ratings.customer_service.value.value,
        }
        for key, value in legacy_ratings.items():
            if key not in self.rating_values:
                self.rating_values[key] = value

    def template_context(self, template: ReviewTemplate | None = None) -> dict[str, Any]:
        """Return a rendering context for template engines."""
        if template is not None:
            value_context: dict[str, str] = {}
            rating_context: dict[str, str] = {}
            comment_context: dict[str, str] = {}
            for field_def in template.iter_fields():
                if field_def.namespace is FieldNamespace.RATING:
                    option = template.rating_option_for(self.rating_values.get(field_def.key, "na"))
                    rating_context[field_def.key] = option.bbcode
                elif field_def.namespace is FieldNamespace.COMMENT:
                    comment_context[field_def.key] = self.comments.get(field_def.key, "")
                else:
                    value_context[field_def.key] = self.values.get(field_def.key, "")
            context: dict[str, Any] = dict(value_context)
            context["rating"] = rating_context
            context["comment"] = comment_context
            context["display_title"] = self.display_title()
            return context

        data = self.to_dict()
        data["display_title"] = self.display_title()
        data["ratings_formatted"] = {
            "quality": self.ratings.quality.value.format(),
            "value": self.ratings.value.value.format(),
            "accuracy": self.ratings.accuracy.value.format(),
            "communication": self.ratings.communication.value.format(),
            "shipping": self.ratings.shipping.value.format(),
            "customer_service": self.ratings.customer_service.value.format(),
            "overall": self.ratings.overall.value.format(),
        }
        return data
