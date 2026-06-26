"""Build Review Studio with PyInstaller."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run the PyInstaller build using the repository spec file."""
    if shutil.which("pyinstaller") is None:
        print("PyInstaller is not installed. Run: python -m pip install pyinstaller", file=sys.stderr)
        return 1
    spec = Path("packaging/review-studio.spec")
    command = ["pyinstaller", str(spec), "--clean", "--noconfirm"]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())