# Packaging Guide

Review Studio is prepared for PyInstaller-based desktop packaging.

## Install Packaging Dependency

```bash
python -m pip install pyinstaller
```

## Build on Linux

```bash
python scripts/package.py
```

or directly:

```bash
pyinstaller packaging/review-studio.spec --clean --noconfirm
```

The output will be placed in `dist/`.

## Windows

Run the build on Windows to produce Windows binaries:

```powershell
python -m pip install -e . pyinstaller
python scripts/package.py
```

## macOS

Run the build on macOS to produce a `.app` bundle:

```bash
python -m pip install -e . pyinstaller
python scripts/package.py
```

macOS distribution may also require signing and notarization for public releases.

## Packaging Notes

- Bundled JSON templates are package data and must be included in bundled builds.
- Qt plugin packaging should be smoke-tested on each platform.
- Run `review-studio --smoke` before packaging and launch the packaged app after packaging.