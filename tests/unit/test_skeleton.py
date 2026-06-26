"""Smoke tests for the initial Review Studio skeleton."""

from __future__ import annotations

import contextlib
import io
import unittest

import review_studio
from review_studio.__main__ import main
from review_studio.app.application import ApplicationInfo


class SkeletonTests(unittest.TestCase):
    """Verify the package skeleton imports and runs."""

    def test_version_is_defined(self) -> None:
        self.assertEqual(review_studio.__version__, "0.1.0")

    def test_application_info_defaults(self) -> None:
        app_info = ApplicationInfo()

        self.assertEqual(app_info.name, "Review Studio")
        self.assertEqual(app_info.version, review_studio.__version__)

    def test_main_smoke_returns_success(self) -> None:
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["--smoke"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(output.getvalue(), "Review Studio startup smoke check passed.\n")


if __name__ == "__main__":
    unittest.main()
