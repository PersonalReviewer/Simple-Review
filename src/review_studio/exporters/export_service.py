"""Export services for generated reviews."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from review_studio.domain.errors import ExportError
from review_studio.domain.models import Review
from review_studio.templates.engine import TemplateEngine


class ExportFormat(Enum):
    """Supported export formats."""

    BBCODE = "bbcode"
    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"
    JSON = "json"


@dataclass(frozen=True, slots=True)
class ExportResult:
    """Result of an export operation."""

    path: Path
    format: ExportFormat


class ExportService:
    """Convert and write reviews to supported output formats."""

    def __init__(self, template_engine: TemplateEngine) -> None:
        self._template_engine = template_engine

    def render(self, review: Review, export_format: ExportFormat) -> str:
        """Render a review in the requested format."""
        bbcode = self._template_engine.render(review)
        if export_format is ExportFormat.BBCODE:
            return bbcode
        if export_format is ExportFormat.JSON:
            return json.dumps(review.to_dict(), indent=2, ensure_ascii=False) + "\n"
        if export_format is ExportFormat.TEXT:
            return self._bbcode_to_text(bbcode)
        if export_format is ExportFormat.MARKDOWN:
            return self._bbcode_to_markdown(bbcode)
        if export_format is ExportFormat.HTML:
            return self._bbcode_to_html(bbcode)
        raise ExportError(f"Unsupported export format: {export_format.value}")

    def export_to_file(self, review: Review, export_format: ExportFormat, path: Path) -> ExportResult:
        """Write rendered output to a file."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(self.render(review, export_format), encoding="utf-8")
        except OSError as exc:
            raise ExportError(f"Could not export review to {path}: {exc}") from exc
        return ExportResult(path=path, format=export_format)

    def _bbcode_to_text(self, text: str) -> str:
        """Strip supported BBCode tags for plain text export."""
        stripped = re.sub(r"\[/?(?:b|i|u)\]", "", text)
        stripped = re.sub(r"\[/?(?:table|tr|th|td|center|subtitle)\]", "", stripped)
        stripped = re.sub(r"\[color=.*?\](.*?)\[/color\]", r"\1", stripped)
        stripped = stripped.replace("[hr]", "----------------------------------------")
        stripped = re.sub(r"\[url=(.*?)\](.*?)\[/url\]", r"\2 (\1)", stripped)
        return stripped

    def _bbcode_to_markdown(self, text: str) -> str:
        """Convert supported BBCode tags to Markdown."""
        converted = re.sub(r"\[b\](.*?)\[/b\]", r"**\1**", text)
        converted = re.sub(r"\[i\](.*?)\[/i\]", r"*\1*", converted)
        converted = re.sub(r"\[u\](.*?)\[/u\]", r"\1", converted)
        converted = re.sub(r"\[/?(?:table|tr)\]", "", converted)
        converted = re.sub(r"\[/?(?:th|td|center|subtitle)\]", "", converted)
        converted = re.sub(r"\[color=.*?\](.*?)\[/color\]", r"\1", converted)
        converted = converted.replace("[hr]", "---")
        converted = re.sub(r"\[url=(.*?)\](.*?)\[/url\]", r"[\2](\1)", converted)
        return converted

    def _bbcode_to_html(self, text: str) -> str:
        """Convert supported BBCode tags to standalone HTML."""
        import html

        escaped = html.escape(text)
        escaped = re.sub(r"\[b\](.*?)\[/b\]", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"\[i\](.*?)\[/i\]", r"<em>\1</em>", escaped)
        escaped = re.sub(r"\[u\](.*?)\[/u\]", r"<u>\1</u>", escaped)
        escaped = re.sub(r"\[subtitle\](.*?)\[/subtitle\]", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"\[center\](.*?)\[/center\]", r'<div style="text-align: center;">\1</div>', escaped)
        escaped = re.sub(r"\[color=(#[0-9a-fA-F]{3,6})\](.*?)\[/color\]", r'<span style="color: \1; font-weight: 600;">\2</span>', escaped)
        escaped = self._tables_to_html(escaped)
        escaped = escaped.replace("[hr]", "<hr>")
        escaped = re.sub(r"\[url=(.*?)\](.*?)\[/url\]", r'<a href="\1">\2</a>', escaped)
        return (
            "<!doctype html>\n<html lang=\"en\">\n<head>\n"
            "<meta charset=\"utf-8\">\n<title>Review Export</title>\n</head>\n"
            f"<body>{escaped.replace(chr(10), '<br>')}</body>\n</html>\n"
        )

    def _tables_to_html(self, text: str) -> str:
        """Convert supported BBCode table tags to HTML."""
        replacements = {
            "[table]": '<table border="1" cellspacing="0" cellpadding="6" style="border-collapse: collapse; width: 100%; margin: 0.75rem 0;">',
            "[/table]": "</table>",
            "[tr]": "<tr>",
            "[/tr]": "</tr>",
            "[th]": "<th>",
            "[/th]": "</th>",
            "[td]": "<td>",
            "[/td]": "</td>",
        }
        for source, target in replacements.items():
            text = text.replace(source, target)
        return text