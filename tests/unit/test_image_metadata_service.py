"""Tests for local image metadata removal."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from review_studio.services.image_metadata_service import (
    ImageCleanupOptions,
    ImageMetadataService,
    ImageOutputMode,
)


class ImageMetadataServiceTests(unittest.TestCase):
    """Verify image metadata cleanup output modes."""

    def test_clean_jpeg_to_same_folder_suffix_removes_exif(self) -> None:
        with TemporaryDirectory() as temporary:
            source = Path(temporary) / "sample.jpg"
            image = Image.new("RGB", (10, 10), "red")
            exif = Image.Exif()
            exif[0x010F] = "CameraBrand"
            image.save(source, exif=exif)

            result = ImageMetadataService().clean_image(source, ImageCleanupOptions())

            self.assertTrue(result.success)
            self.assertEqual(result.destination.name, "sample_clean.jpg")
            with Image.open(result.destination) as cleaned:
                self.assertEqual(dict(cleaned.getexif()), {})

    def test_clean_to_output_folder_preserves_original(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "sample.png"
            output = root / "cleaned"
            Image.new("RGB", (4, 4), "blue").save(source)

            result = ImageMetadataService().clean_image(
                source,
                ImageCleanupOptions(
                    output_mode=ImageOutputMode.OUTPUT_FOLDER,
                    output_folder=output,
                ),
            )

            self.assertTrue(source.exists())
            self.assertEqual(result.destination, output / "sample.png")
            self.assertTrue(result.destination.exists())

    def test_clean_png_text_metadata_removed(self) -> None:
        with TemporaryDirectory() as temporary:
            source = Path(temporary) / "sample.png"
            metadata = PngInfo()
            metadata.add_text("Comment", "private note")
            Image.new("RGB", (8, 8), "green").save(source, pnginfo=metadata)

            result = ImageMetadataService().clean_image(source, ImageCleanupOptions())

            with Image.open(result.destination) as cleaned:
                self.assertNotIn("Comment", cleaned.info)

    def test_imgur_upload_is_default_off(self) -> None:
        with TemporaryDirectory() as temporary:
            source = Path(temporary) / "sample.png"
            Image.new("RGB", (4, 4), "purple").save(source)

            result = ImageMetadataService().clean_image(source, ImageCleanupOptions())

            self.assertEqual(result.uploaded_url, "")
            self.assertEqual(result.message, "metadata removed")


if __name__ == "__main__":
    unittest.main()
