"""Application composition root.

This module wires concrete infrastructure adapters into application services.
The GUI imports services from here instead of constructing storage/template
objects directly, keeping startup composition centralized and easy to test.
"""

from __future__ import annotations

from dataclasses import dataclass

from review_studio.exporters.export_service import ExportService
from review_studio.services.review_service import ReviewService
from review_studio.services.template_service import TemplateService
from review_studio.storage.repository import ReviewRepository
from review_studio.storage.settings import SettingsStore
from review_studio.templates.engine import TemplateEngine


@dataclass(frozen=True, slots=True)
class ApplicationInfo:
    """Static application metadata used by the skeleton."""

    name: str = "Review Studio"
    version: str = "0.1.0"


@dataclass(frozen=True, slots=True)
class ApplicationServices:
    """Concrete services required by the desktop application."""

    template_engine: TemplateEngine
    template_service: TemplateService
    review_service: ReviewService
    export_service: ExportService


def create_services() -> ApplicationServices:
    """Create the default application service graph."""
    template_engine = TemplateEngine()
    return ApplicationServices(
        template_engine=template_engine,
        template_service=TemplateService(template_engine),
        review_service=ReviewService(ReviewRepository(), SettingsStore()),
        export_service=ExportService(template_engine),
    )
