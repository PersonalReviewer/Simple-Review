# Installation Guide

## Requirements

- Python 3.11 or newer
- Linux, Windows, or macOS

Linux is the primary development target. Windows and macOS are supported by design through
PySide6, platform-aware storage paths, and standard Python packaging.

## Install from Source

```bash
git clone <repository-url> review-studio
cd review-studio
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
review-studio
```

On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
review-studio
```

## Smoke Check

```bash
review-studio --smoke
```

Expected output:

```text
Review Studio startup smoke check passed.
```

## Troubleshooting GUI Startup

On Linux, Qt may require platform plugins and common desktop libraries. If the GUI fails to
start, confirm that your system has a normal desktop session and Qt dependencies installed.

For CI/headless smoke checks:

```bash
QT_QPA_PLATFORM=offscreen review-studio --smoke
```