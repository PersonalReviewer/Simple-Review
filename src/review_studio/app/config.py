"""Configuration skeleton for Review Studio.

Concrete settings and platform-specific paths will be added in a later milestone.
"""

from __future__ import annotations

from dataclasses import dataclass



@dataclass(frozen=True, slots=True)
class AppConfig:
    """Minimal immutable application configuration placeholder."""

    app_name: str = "Review Studio"

    organization_name: str = "Review Studio"
