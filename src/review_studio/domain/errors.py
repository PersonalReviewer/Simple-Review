"""Domain error definitions for future milestones."""

from __future__ import annotations


class ReviewStudioError(Exception):
    """Base exception for Review Studio errors."""


class TemplateError(ReviewStudioError):
    """Raised when a template cannot be loaded or rendered."""


class StorageError(ReviewStudioError):
    """Raised when persistence operations fail."""


class ExportError(ReviewStudioError):
    """Raised when an export operation fails."""


class ValidationError(ReviewStudioError):
    """Raised when review data is invalid for a workflow."""
