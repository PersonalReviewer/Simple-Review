"""Safe JSON persistence primitives."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from review_studio.domain.errors import StorageError


def read_json(path: Path, default: Any) -> Any:
    """Read JSON from disk, returning ``default`` when the file is absent."""
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError(f"Could not read JSON file {path}: {exc}") from exc


def atomic_write_json(path: Path, data: Any) -> None:
    """Atomically write JSON to reduce the risk of data loss."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        if path.exists():
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        os.replace(temporary, path)
    except OSError as exc:
        raise StorageError(f"Could not write JSON file {path}: {exc}") from exc