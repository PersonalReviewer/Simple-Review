"""Template loading and rendering services."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from jinja2 import Environment, StrictUndefined, TemplateError as JinjaTemplateError

from review_studio.domain.errors import TemplateError
from review_studio.domain.models import Review
from review_studio.domain.template_schema import ReviewTemplate
from review_studio.utils.paths import app_data_dir


class TemplateEngine:
    """Render reviews with bundled or future external Jinja templates."""

    def __init__(self, custom_template_dirs: list[Path] | None = None) -> None:
        self._environment = Environment(
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )
        self._templates = self._load_builtin_templates()
        self._load_custom_templates(custom_template_dirs or [app_data_dir() / "templates"])

    def available_templates(self) -> list[ReviewTemplate]:
        """Return all registered templates."""
        return list(self._templates.values())

    def get_template(self, template_id: str) -> ReviewTemplate:
        """Return a template by id, falling back to the bundled default."""
        return self._templates.get(template_id, self._templates["default_review"])

    def render(self, review: Review, template_id: str | None = None) -> str:
        """Render a review to the template's native output format."""
        selected = self.get_template(template_id or review.template_id)
        try:
            template = self._environment.from_string(selected.body)
            return template.render(**review.template_context(selected)).strip() + "\n"
        except JinjaTemplateError as exc:
            raise TemplateError(f"Could not render template '{selected.id}': {exc}") from exc

    def _load_builtin_templates(self) -> dict[str, ReviewTemplate]:
        """Load bundled JSON template definitions from package data."""
        templates: dict[str, ReviewTemplate] = {}
        package_files = resources.files("review_studio.templates.builtin")
        for template_file in package_files.iterdir():
            if template_file.name.endswith(".json"):
                data = json.loads(template_file.read_text(encoding="utf-8"))
                template = ReviewTemplate.from_dict(data)
                templates[template.id] = template
        if "default_review" not in templates:
            raise TemplateError("Bundled default_review template is missing")
        return templates

    def _load_custom_templates(self, directories: list[Path]) -> None:
        """Load user-provided JSON templates without code changes."""
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            for template_file in sorted(directory.glob("*.json")):
                try:
                    template = ReviewTemplate.from_dict(json.loads(template_file.read_text(encoding="utf-8")))
                    self._templates[template.id] = template
                except Exception as exc:
                    raise TemplateError(f"Could not load template {template_file}: {exc}") from exc