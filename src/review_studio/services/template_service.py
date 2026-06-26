"""Application-facing template service."""

from __future__ import annotations

from review_studio.domain.models import Review
from review_studio.domain.template_schema import ReviewTemplate
from review_studio.templates.engine import TemplateEngine


class TemplateService:
    """Expose template workflows without leaking engine details to the GUI."""

    def __init__(self, engine: TemplateEngine) -> None:
        self.engine = engine

    def render_review(self, review: Review) -> str:
        """Render a review using its selected template."""
        return self.engine.render(review)

    def get_template(self, template_id: str) -> ReviewTemplate:
        """Return a template by id with engine fallback semantics."""
        return self.engine.get_template(template_id)

    def templates(self) -> list[ReviewTemplate]:
        """Return available templates."""
        return self.engine.available_templates()

    def refresh(self) -> None:
        """Reload templates from disk."""
        self.engine.refresh()

    def save_custom_template(self, template: ReviewTemplate) -> None:
        """Save a custom template profile."""
        self.engine.save_custom_template(template)

    def delete_custom_template(self, template_id: str) -> None:
        """Delete a custom template profile."""
        self.engine.delete_custom_template(template_id)