"""Preview helpers for raw and rendered review output."""

from __future__ import annotations

import html
import re


class PreviewRenderer:
    """Convert generated text into lightweight preview HTML where possible."""

    _simple_tags = {
        "b": "strong",
        "i": "em",
        "u": "u",
        "subtitle": "strong",
        "center": "div style=\"text-align: center;\"",
    }

    def bbcode_to_html(self, text: str) -> str:
        """Convert the supported subset of BBCode into safe HTML.

        The raw output remains authoritative. This renderer is intentionally
        conservative and escapes all text before replacing known BBCode tags.
        """
        escaped = html.escape(text)
        for bbcode, tag in self._simple_tags.items():
            escaped = re.sub(fr"\[{bbcode}\](.*?)\[/{bbcode}\]", fr"<{tag}>\1</{tag}>", escaped)
        escaped = escaped.replace("[hr]", "<hr>")
        escaped = re.sub(r"\[color=(#[0-9a-fA-F]{3,6})\](.*?)\[/color\]", r'<span style="color: \1; font-weight: 600;">\2</span>', escaped)
        escaped = re.sub(r"\[url=(.*?)\](.*?)\[/url\]", r'<a href="\1">\2</a>', escaped)
        escaped = self._tables_to_html(escaped)
        paragraphs = "<br>".join(escaped.splitlines())
        return f"""
        <html>
          <body style="font-family: sans-serif; line-height: 1.45;">
            {paragraphs}
          </body>
        </html>
        """

    def _tables_to_html(self, text: str) -> str:
        """Convert the supported table subset to HTML for preview readability."""
        replacements = {
            "[table]": '<table border="1" cellspacing="0" cellpadding="6" style="border-collapse: collapse; width: 100%; margin: 0.75rem 0;">',
            "[/table]": "</table>",
            "[tr]": "<tr>",
            "[/tr]": "</tr>",
            "[th]": '<th style="background: rgba(127,127,127,0.18);">',
            "[/th]": "</th>",
            "[td]": "<td>",
            "[/td]": "</td>",
        }
        for source, target in replacements.items():
            text = text.replace(source, target)
        return text

    def markdown_to_html(self, text: str) -> str:
        """Return a simple escaped HTML rendering for Markdown-like output."""
        escaped = html.escape(text)
        escaped = re.sub(r"^# (.*?)$", r"<h1>\1</h1>", escaped, flags=re.MULTILINE)
        escaped = re.sub(r"^## (.*?)$", r"<h2>\1</h2>", escaped, flags=re.MULTILINE)
        escaped = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", escaped)
        return f"<html><body style='font-family: sans-serif; line-height: 1.45;'>{escaped.replace(chr(10), '<br>')}</body></html>"