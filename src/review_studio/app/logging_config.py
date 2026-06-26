"""Logging configuration for Review Studio."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from review_studio.utils.paths import app_data_dir


def configure_logging() -> None:
    """Configure file and console logging once."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    root_logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    log_file = app_data_dir() / "review-studio.log"
    file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)