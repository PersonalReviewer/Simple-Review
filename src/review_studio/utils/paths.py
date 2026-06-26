"""Cross-platform application paths."""

from __future__ import annotations

from pathlib import Path

from platformdirs import user_config_dir, user_data_dir


APP_NAME = "Review Studio"
APP_AUTHOR = "Review Studio"


def app_data_dir() -> Path:
    """Return the per-user application data directory."""
    path = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def app_config_dir() -> Path:
    """Return the per-user application configuration directory."""
    path = Path(user_config_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def reviews_dir() -> Path:
    """Return the default review-library directory."""
    path = app_data_dir() / "reviews"
    path.mkdir(parents=True, exist_ok=True)
    return path