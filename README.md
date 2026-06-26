# Review Studio

Review Studio is a desktop app for writing structured vendor/product reviews without hand-building BBCode every time.

It gives you a form on the left, a live preview on the right, and a clean generated table output that can be copied or exported when the review is ready.

The goal is simple: make reviews consistent, readable, backed up, and easier to write without turning the output into a mess.

## What it does

- Builds reviews from a structured editor instead of a blank text box
- Generates BBCode table output automatically
- Shows a live raw preview while you type
- Shows a rendered preview for easier checking before posting
- Keeps a local review library with autosave
- Lets you search, duplicate, delete, and reopen reviews
- Exports to BBCode, Markdown, HTML, plain text, and JSON
- Uses template files instead of hardcoding the review format into the GUI
- Keeps rating recommendations inside the editor, not in the final post
- Supports dark/light theme settings

## Current default review format

The bundled default template generates a BBCode table with sections for:

- vendor / product / market
- product details
- price value
- reagent test result
- quantity
- quality / potency
- aesthetic
- picture link
- overall product rating
- shipping option
- shipping time
- stealth quality
- overall shipping
- customer service
- final summary

The raw BBCode stays visible at all times so you can inspect exactly what will be copied or exported.

## Rating guidance

Review Studio uses a 7-point scale plus `N/A`.

The rating descriptions are shown as editor guidance under the dropdowns. They are not inserted into the generated review.

There are two built-in guidance scales:

- **Standard Scale** — used for normal quality/value/service ratings
- **Stealth Scale** — used for the Stealth Quality field

The final output only shows the selected rating value/name, for example:

```bbcode
𝟒/𝟕 –[color=#90d00f] 𝐀𝐃𝐄𝐐𝐔𝐀𝐓𝐄 [/color]
```

## Screenshots

Screenshots are not committed yet. The first public release should include:

- main split-screen editor
- rating dropdown with recommendation text
- rendered BBCode table preview
- review library/search
- settings dialog

Recommended location:

```text
docs/images/
```

## Requirements

- Python 3.11+
- PySide6
- Jinja2
- platformdirs
- pydantic

## Install from source

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
review-studio
```

From a source checkout without installing:

```bash
PYTHONPATH=src python -m review_studio
```

Smoke check:

```bash
PYTHONPATH=src python -m review_studio --smoke
```

Headless smoke check:

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python -m review_studio --smoke
```

## Tests

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python -m unittest discover -s tests
```

Optional checks:

```bash
python -m pip install -e .[dev]
ruff check src tests
mypy src tests
```

## Architecture

Review Studio is split into layers so the GUI does not own the business rules:

```text
GUI widgets/views
  -> GUI-independent view models
  -> application services
  -> domain models/value objects
  -> storage/templates/exporters/platform paths
```

Important parts:

- `review_studio.gui.main_window` — PySide6 split-screen interface
- `review_studio.gui.view_models.main_view_model` — GUI-independent workflow state
- `review_studio.domain.models` — review model and migration compatibility
- `review_studio.domain.template_schema` — JSON template schema and rating guidance
- `review_studio.templates.engine` — template loading/rendering
- `review_studio.storage.repository` — local JSON review library
- `review_studio.exporters.export_service` — BBCode/Markdown/HTML/text/JSON export

## Template system

The editor is generated from JSON templates. The default template is here:

```text
src/review_studio/templates/builtin/default_review.json
```

Templates define:

- sections
- fields
- field types
- required fields
- rating options
- rating guidance scales
- BBCode/Jinja output body

User templates can be added without changing Python code by placing JSON templates in:

```text
<app data directory>/templates/
```

Template variables include plain values, ratings, and comments:

```jinja2
{{ vendor_name }}
{{ product_name }}
{{ rating.quality }}
{{ comment.quality }}
```

## Data storage

Reviews are stored as local JSON files.

Persistence is intentionally boring and inspectable:

- one review per JSON file
- atomic writes
- `.bak` backup before replacing an existing review
- corrupted files are skipped in library listing instead of crashing the app
- loading a review attempts backup recovery if the main file is unreadable

## Packaging

PyInstaller packaging files are included:

```bash
python scripts/package.py
```

See [docs/packaging.md](docs/packaging.md) for platform notes.

## Documentation

- [Installation Guide](docs/installation.md)
- [User Guide](docs/user-guide.md)
- [Developer Guide](docs/developer-guide.md)
- [Template Authoring Guide](docs/templates.md)
- [Packaging Guide](docs/packaging.md)
- [Contributing Guide](CONTRIBUTING.md)

## Project status

This is an early public release. The core workflow is working and tested, but packaged installers and screenshots still need release work.

Known next steps:

- add screenshots
- add packaged builds for Linux/Windows/macOS
- add template manager UI
- add stronger template diagnostics
- expand BBCode preview coverage

## License

MIT. See [LICENSE](LICENSE).
