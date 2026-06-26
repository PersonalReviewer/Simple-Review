"""Template schema definitions for template-driven reviews."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FieldType(Enum):
    """Supported template field widget/value types."""

    TEXT = "text"
    MULTILINE = "multiline"
    URL = "url"
    RATING = "rating"
    SELECT = "select"


class FieldNamespace(Enum):
    """Variable namespace used by a template field."""

    VALUE = "value"
    RATING = "rating"
    COMMENT = "comment"


@dataclass(frozen=True, slots=True)
class RatingOption:
    """One reusable rating option from a template definition."""

    value: int | None
    name: str
    color: str
    description: str

    @property
    def storage_value(self) -> str:
        """Return the stable value stored in review JSON."""
        return "na" if self.value is None else str(self.value)

    @property
    def display_name(self) -> str:
        """Return the friendly dropdown label."""
        if self.value is None:
            return "N/A"
        return f"{self.value}/7 - {self.name}"

    @property
    def bbcode(self) -> str:
        """Return the formatted BBCode rating representation."""
        if self.value is None:
            return "N/A"
        return f"{_bold_digits(str(self.value))}/𝟕 –[color={self.color}] {_bold_text(self.name.upper())} [/color]"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RatingOption:
        """Create a rating option from JSON-compatible data."""
        raw_value = data.get("value")
        value = None if raw_value is None or str(raw_value).lower() in {"na", "n/a"} else int(raw_value)
        return cls(
            value=value,
            name=str(data.get("name", "N/A" if value is None else value)),
            color=str(data.get("color", "#999999")),
            description=str(data.get("description", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize a rating option to JSON-compatible data."""
        return {
            "value": self.value,
            "name": self.name,
            "color": self.color,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class TemplateField:
    """A field definition used to generate GUI controls and render variables."""

    key: str
    label: str
    field_type: FieldType
    namespace: FieldNamespace = FieldNamespace.VALUE
    options: tuple[str, ...] = ()
    required: bool = False
    placeholder: str = ""
    rating_scale: str = "standard"

    @property
    def identity(self) -> str:
        """Return a unique identity for GUI bindings and persistence."""
        return f"{self.namespace.value}.{self.key}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TemplateField:
        """Create a field definition from JSON-compatible data."""
        return cls(
            key=str(data["key"]),
            label=str(data["label"]),
            field_type=FieldType(str(data.get("type", "text"))),
            namespace=FieldNamespace(str(data.get("namespace", "value"))),
            options=tuple(str(option) for option in data.get("options", [])),
            required=bool(data.get("required", False)),
            placeholder=str(data.get("placeholder", "")),
            rating_scale=str(data.get("rating_scale", "standard")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize a field definition to JSON-compatible data."""
        data: dict[str, Any] = {
            "key": self.key,
            "label": self.label,
            "type": self.field_type.value,
        }
        if self.namespace is not FieldNamespace.VALUE:
            data["namespace"] = self.namespace.value
        if self.options:
            data["options"] = list(self.options)
        if self.required:
            data["required"] = self.required
        if self.placeholder:
            data["placeholder"] = self.placeholder
        if self.rating_scale != "standard":
            data["rating_scale"] = self.rating_scale
        return data


@dataclass(frozen=True, slots=True)
class TemplateSection:
    """A logical section in a template-driven review editor."""

    title: str
    fields: tuple[TemplateField, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TemplateSection:
        """Create a section from JSON-compatible data."""
        return cls(
            title=str(data["title"]),
            fields=tuple(TemplateField.from_dict(field_data) for field_data in data.get("fields", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize a section to JSON-compatible data."""
        return {"title": self.title, "fields": [field.to_dict() for field in self.fields]}


@dataclass(frozen=True, slots=True)
class ReviewTemplate:
    """A complete template definition loaded from JSON."""

    id: str
    name: str
    description: str
    default_format: str
    sections: tuple[TemplateSection, ...]
    rating_options: tuple[RatingOption, ...]
    body: str
    version: str = "1.0"
    rating_scales: dict[str, dict[str, str]] | None = None

    def iter_fields(self) -> tuple[TemplateField, ...]:
        """Return all fields in section order."""
        return tuple(field for section in self.sections for field in section.fields)

    def rating_option_for(self, value: str | int | None) -> RatingOption:
        """Return a rating option by stored value, safely falling back to N/A."""
        normalized = "na" if value is None else str(value).strip().lower()
        for option in self.rating_options:
            if normalized in {option.storage_value.lower(), option.display_name.lower()}:
                return option
        return self.rating_options[0]

    def rating_guidance_for(self, field: TemplateField, value: str | int | None) -> str:
        """Return editor-only guidance text for a rating field/value."""
        normalized = "na" if value is None else str(value).strip().lower()
        if self.rating_scales:
            scale = self.rating_scales.get(field.rating_scale, {})
            if normalized in scale:
                return scale[normalized]
        return self.rating_option_for(value).description

    def to_dict(self) -> dict[str, Any]:
        """Serialize a review template to JSON-compatible data."""
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "default_format": self.default_format,
            "rating_options": [option.to_dict() for option in self.rating_options],
            "sections": [section.to_dict() for section in self.sections],
            "body": self.body,
        }
        if self.rating_scales:
            data["rating_scales"] = self.rating_scales
        return data

    def with_identity(self, template_id: str, name: str) -> ReviewTemplate:
        """Return a copy with a different id/name for custom profiles."""
        return ReviewTemplate(
            id=template_id,
            name=name,
            description=self.description,
            default_format=self.default_format,
            sections=self.sections,
            rating_options=self.rating_options,
            body=self.body,
            version=self.version,
            rating_scales=self.rating_scales,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReviewTemplate:
        """Create a review template from JSON-compatible data."""
        rating_scales = {
            str(scale_id): {str(value).strip().lower(): str(description) for value, description in dict(scale).items()}
            for scale_id, scale in dict(data.get("rating_scales", {})).items()
        }
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            description=str(data.get("description", "")),
            default_format=str(data.get("default_format", "bbcode")),
            version=str(data.get("version", "1.0")),
            sections=tuple(TemplateSection.from_dict(section) for section in data.get("sections", [])),
            rating_options=tuple(RatingOption.from_dict(option) for option in data.get("rating_options", [])),
            body=str(data.get("body", "")),
            rating_scales=rating_scales,
        )


def default_rating_options() -> tuple[RatingOption, ...]:
    """Return the default Review Studio rating scale."""
    return (
        RatingOption(None, "N/A", "#999999", "This area does not apply to the review."),
        RatingOption(1, "Failure", "#d9534f", "Unacceptable: failed to meet the basic requirement."),
        RatingOption(2, "Poor", "#f06c64", "Weak: significant issues or below expected quality."),
        RatingOption(3, "Basic", "#f0ad4e", "Limited: usable but minimal or inconsistent."),
        RatingOption(4, "Adequate", "#90d00f", "Baseline: Solid, reliable, meets reasonable expectations."),
        RatingOption(5, "Strong", "#5cb85c", "Good: clearly above baseline with minor concerns only."),
        RatingOption(6, "Advanced", "#5bc0de", "Very good: polished and consistently reliable."),
        RatingOption(7, "Exceptional", "#428bca", "Excellent: meaningfully exceeds expectations."),
    )


def _bold_digits(text: str) -> str:
    """Return mathematical bold digits used by the default table template."""
    translation = str.maketrans("0123456789", "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗")
    return text.translate(translation)


def _bold_text(text: str) -> str:
    """Return mathematical bold Latin letters for rating labels."""
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    bold = "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳"
    return text.translate(str.maketrans(normal, bold))