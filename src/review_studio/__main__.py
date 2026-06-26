"""Command-line entry point for Review Studio."""

from __future__ import annotations

import argparse
import logging
import sys

from review_studio import __version__
from review_studio.app.logging_config import configure_logging


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(description="Review Studio desktop application")
    parser.add_argument("--version", action="store_true", help="print the application version")
    parser.add_argument("--smoke", action="store_true", help="run a startup smoke check without opening the GUI")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run Review Studio.

    By default this starts the PySide6 desktop application. The ``--smoke``
    option exists for automated checks and packaging validation in headless
    environments.
    """
    configure_logging()
    args = build_parser().parse_args(argv)
    if args.version:
        print(f"Review Studio {__version__}")
        return 0
    if args.smoke:
        from review_studio.app.application import create_services

        create_services()
        print("Review Studio startup smoke check passed.")
        return 0

    try:
        from review_studio.gui.application import run_gui

        return run_gui(sys.argv if argv is None else [sys.argv[0], *argv])
    except Exception:
        logging.getLogger(__name__).exception("Review Studio failed to start")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
