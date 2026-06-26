"""Tests for custom template profile persistence."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from review_studio.templates.engine import TemplateEngine


class TemplateProfileTests(unittest.TestCase):
    """Verify clone/save/delete custom template profile workflows."""

    def test_custom_template_round_trip(self) -> None:
        with TemporaryDirectory() as temporary:
            engine = TemplateEngine(custom_template_dirs=[Path(temporary)])
            original = engine.get_template("default_review")
            custom = original.with_identity("custom_profile", "Custom Profile")

            saved_path = engine.save_custom_template(custom)
            self.assertTrue(saved_path.exists())
            self.assertEqual(engine.get_template("custom_profile").name, "Custom Profile")

            engine.delete_custom_template("custom_profile")
            self.assertFalse(saved_path.exists())
            self.assertEqual(engine.get_template("custom_profile").id, "default_review")


if __name__ == "__main__":
    unittest.main()
