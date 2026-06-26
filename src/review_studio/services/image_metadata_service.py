"""Local image metadata removal service.

The service intentionally performs all work on local files. It does not shell out to
platform-specific tools, does not upload images, and only depends on Pillow for
cross-platform image decoding/encoding.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PIL import Image, ImageOps, ImageSequence, UnidentifiedImageError

from review_studio.domain.errors import ImageProcessingError


class ImageOutputMode(Enum):
    """Where cleaned image files should be written."""

    OVERWRITE = "overwrite"
    SAME_FOLDER_SUFFIX = "same_folder_suffix"
    OUTPUT_FOLDER = "output_folder"


@dataclass(frozen=True, slots=True)
class ImageCleanupOptions:
    """Options for metadata removal."""

    output_mode: ImageOutputMode = ImageOutputMode.SAME_FOLDER_SUFFIX
    suffix: str = "_clean"
    output_folder: Path | None = None
    upload_to_imgur: bool = False
    imgur_client_id: str = ""
    prefer_image_magick: bool = True


@dataclass(frozen=True, slots=True)
class ImageCleanupResult:
    """Result for one processed image."""

    source: Path
    destination: Path
    success: bool
    message: str = ""
    uploaded_url: str = ""


class ImageMetadataService:
    """Remove EXIF and common embedded metadata from image files."""

    supported_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".tif",
        ".tiff",
        ".bmp",
        ".gif",
    }

    def clean_images(self, paths: list[Path], options: ImageCleanupOptions) -> list[ImageCleanupResult]:
        """Clean all provided image paths, returning per-file results."""
        results: list[ImageCleanupResult] = []
        for path in paths:
            try:
                results.append(self.clean_image(path, options))
            except Exception as exc:  # noqa: BLE001 - collect per-file failures for the GUI
                results.append(
                    ImageCleanupResult(
                        source=path,
                        destination=self.destination_for(path, options),
                        success=False,
                        message=str(exc),
                    )
                )
        return results

    def clean_image(self, path: Path, options: ImageCleanupOptions) -> ImageCleanupResult:
        """Remove metadata from a single image file."""
        source = path.expanduser().resolve()
        if not source.exists() or not source.is_file():
            raise ImageProcessingError(f"Image does not exist: {source}")
        if source.suffix.lower() not in self.supported_extensions:
            raise ImageProcessingError(f"Unsupported image type: {source.suffix}")

        destination = self.destination_for(source, options)
        destination.parent.mkdir(parents=True, exist_ok=True)

        try:
            used_backend = "Pillow pixel re-encode"
            if options.output_mode is ImageOutputMode.OVERWRITE:
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=source.suffix,
                    dir=str(source.parent),
                ) as temporary:
                    temp_path = Path(temporary.name)
                try:
                    used_backend = self._write_clean_image(source, temp_path, options)
                    os.replace(temp_path, source)
                finally:
                    temp_path.unlink(missing_ok=True)
            else:
                used_backend = self._write_clean_image(source, destination, options)
        except UnidentifiedImageError as exc:
            raise ImageProcessingError(f"Could not identify image: {source}") from exc
        except OSError as exc:
            raise ImageProcessingError(f"Could not process image {source}: {exc}") from exc

        uploaded_url = ""
        message = f"metadata removed via {used_backend}"
        if options.upload_to_imgur:
            uploaded_url = self.upload_to_imgur(destination, options.imgur_client_id)
            message = f"metadata removed; uploaded to {uploaded_url}"

        return ImageCleanupResult(
            source=source,
            destination=destination,
            success=True,
            message=message,
            uploaded_url=uploaded_url,
        )

    def destination_for(self, source: Path, options: ImageCleanupOptions) -> Path:
        """Return the destination path for a source image/options pair."""
        source = source.expanduser()
        if options.output_mode is ImageOutputMode.OVERWRITE:
            return source
        if options.output_mode is ImageOutputMode.SAME_FOLDER_SUFFIX:
            suffix = options.suffix.strip() or "_clean"
            return source.with_name(f"{source.stem}{suffix}{source.suffix}")
        if options.output_folder is None:
            raise ImageProcessingError("Output folder is required for output-folder mode")
        return options.output_folder.expanduser() / source.name

    def _write_clean_image(self, source: Path, destination: Path, options: ImageCleanupOptions) -> str:
        """Write image pixel data without EXIF/text metadata."""
        if options.prefer_image_magick and self._write_with_image_magick(source, destination):
            return "ImageMagick -strip"

        with Image.open(source) as image:
            image_format = image.format or self._format_from_suffix(destination)
            if getattr(image, "is_animated", False):
                self._write_animated_clean_image(image, destination, image_format)
                return "Pillow pixel re-encode"

            cleaned = ImageOps.exif_transpose(image)
            cleaned.load()
            cleaned = self._pixel_only_copy(cleaned)
            cleaned = self._normalized_for_format(cleaned, image_format)
            save_kwargs = self._save_kwargs(image_format)
            cleaned.save(destination, format=image_format, **save_kwargs)
        return "Pillow pixel re-encode"

    def _write_with_image_magick(self, source: Path, destination: Path) -> bool:
        """Use ImageMagick's strip behavior when available.

        This gives users parity with the common ``mogrify -strip`` workflow while
        keeping Pillow as the cross-platform fallback when ImageMagick is absent.
        """
        executable = shutil.which("magick") or shutil.which("convert")
        if executable is None:
            return False
        command = [executable, str(source), "-auto-orient", "-strip", str(destination)]
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError):
            return False
        return destination.exists()

    def _write_animated_clean_image(self, image: Image.Image, destination: Path, image_format: str) -> None:
        """Write animated images without carrying over metadata containers."""
        frames: list[Image.Image] = []
        durations: list[int] = []
        for frame in ImageSequence.Iterator(image):
            frame_copy = self._pixel_only_copy(ImageOps.exif_transpose(frame))
            frames.append(self._normalized_for_format(frame_copy, image_format))
            durations.append(int(frame.info.get("duration", image.info.get("duration", 100))))
        if not frames:
            raise ImageProcessingError("Animated image contains no frames")
        save_kwargs = self._save_kwargs(image_format)
        if image_format.upper() in {"GIF", "WEBP"}:
            save_kwargs.update(
                {
                    "save_all": True,
                    "append_images": frames[1:],
                    "duration": durations,
                    "loop": int(image.info.get("loop", 0)),
                }
            )
        frames[0].save(destination, format=image_format, **save_kwargs)


    def upload_to_imgur(self, path: Path, client_id: str) -> str:
        """Upload a cleaned image to Imgur using anonymous API access.

        This is experimental and opt-in. The caller must provide an Imgur Client ID.
        """
        clean_client_id = client_id.strip()
        if not clean_client_id:
            raise ImageProcessingError("Imgur upload requires a Client ID")
        payload = urllib.parse.urlencode(
            {"image": base64.b64encode(path.read_bytes()).decode("ascii"), "type": "base64"}
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://api.imgur.com/3/image",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Client-ID {clean_client_id}",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "ReviewStudio/0.1",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
            raise ImageProcessingError(f"Imgur upload failed: {exc}") from exc
        link = str(data.get("data", {}).get("link", ""))
        if not link:
            raise ImageProcessingError("Imgur upload did not return a link")
        return link

    def _pixel_only_copy(self, image: Image.Image) -> Image.Image:
        """Return a new image object containing only pixel data, not metadata dicts."""
        source = image.copy()
        if source.mode in {"P", "PA"}:
            source = source.convert("RGBA")
        clean = Image.new(source.mode, source.size)
        clean.paste(source)
        return clean

    def _normalized_for_format(self, image: Image.Image, image_format: str) -> Image.Image:
        """Normalize modes that cannot be written by some formats."""
        normalized = image.copy()
        if image_format.upper() in {"JPEG", "JPG"} and normalized.mode not in {"RGB", "L"}:
            normalized = normalized.convert("RGB")
        return normalized

    def _save_kwargs(self, image_format: str) -> dict[str, object]:
        """Return conservative save options that do not preserve metadata."""
        normalized = image_format.upper()
        if normalized in {"JPEG", "JPG"}:
            return {"quality": 95, "optimize": True}
        if normalized == "PNG":
            return {"optimize": True}
        if normalized == "WEBP":
            return {"quality": 95, "method": 6}
        return {}

    def _format_from_suffix(self, path: Path) -> str:
        """Infer a Pillow format name from a file suffix."""
        suffix = path.suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            return "JPEG"
        if suffix == ".png":
            return "PNG"
        if suffix == ".webp":
            return "WEBP"
        if suffix in {".tif", ".tiff"}:
            return "TIFF"
        if suffix == ".gif":
            return "GIF"
        if suffix == ".bmp":
            return "BMP"
        raise ImageProcessingError(f"Unsupported image type: {suffix}")
