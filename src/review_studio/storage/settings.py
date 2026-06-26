"""Persistent user settings."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from review_studio.storage.json_store import atomic_write_json, read_json
from review_studio.utils.paths import app_config_dir, reviews_dir


@dataclass(slots=True)
class UserSettings:
    """Configurable application preferences."""

    theme: str = "dark"
    font_size: int = 11
    autosave_interval_seconds: int = 5
    default_export_folder: str = ""
    review_library_folder: str = ""
    default_template_id: str = "default_review"
    recent_review_ids: list[str] = field(default_factory=list)
    review_categories: list[str] = field(default_factory=lambda: ["Uncategorized"])

    def normalized_library_folder(self) -> Path:
        """Return the configured or default review library folder."""
        if self.review_library_folder:
            return Path(self.review_library_folder).expanduser()
        return reviews_dir()

    def normalized_export_folder(self) -> Path:
        """Return the configured or default export folder."""
        if self.default_export_folder:
            return Path(self.default_export_folder).expanduser()
        return self.normalized_library_folder()

    def to_dict(self) -> dict[str, Any]:
        """Serialize settings."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> UserSettings:
        """Deserialize settings with safe defaults."""
        if not isinstance(data, dict):
            return cls()
        return cls(
            theme=str(data.get("theme", "dark")),
            font_size=int(data.get("font_size", 11)),
            autosave_interval_seconds=max(1, int(data.get("autosave_interval_seconds", 5))),
            default_export_folder=str(data.get("default_export_folder", "")),
            review_library_folder=str(data.get("review_library_folder", "")),
            default_template_id=str(data.get("default_template_id", "default_review")),
            recent_review_ids=[str(item) for item in data.get("recent_review_ids", [])],
            review_categories=[str(item) for item in data.get("review_categories", ["Uncategorized"])],
        )


class SettingsStore:
    """Load and save ``UserSettings``."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or app_config_dir() / "settings.json"

    def load(self) -> UserSettings:
        """Load persisted settings."""
        return UserSettings.from_dict(read_json(self.path, {}))

    def save(self, settings: UserSettings) -> None:
        """Persist settings."""
        atomic_write_json(self.path, settings.to_dict())