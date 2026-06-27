# Review Studio

Review Studio is a desktop app for writing structured vendor/product reviews without hand-building BBCode every time.

It gives you a form on the left, a live preview on the right, and a clean generated table output that can be copied or exported when the review is ready.

The goal is simple: I wanted to fix the amount of time each review would take, the handling of the bbcode, and the exporting process. This simplfies all and even can remove EXIF. Please consider checking out if you enjoy making indepth reviews.  

## SCROLL DOWN FOR SCREEN SHOTS!!!!!!!!!!!!!!!!!!!!!!!!!

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
- Removes EXIF/common image metadata locally by re-encoding fresh pixel-only files before posting images
- Lets you clone, edit, save, delete, and switch template profiles
- Organizes reviews into collapsible local folders/categories
- Optional experimental Imgur upload after metadata removal, disabled by default

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
<img width="526" height="449" alt="rating" src="https://github.com/user-attachments/assets/59a903c7-29cb-42f1-9a51-98202564352d" />

<img width="1402" height="881" alt="new" src="https://github.com/user-attachments/assets/281d7e65-1d95-4c56-aa88-e67fa155d9bd" />

<img width="441" height="790" alt="preview" src="https://github.com/user-attachments/assets/60539069-868c-4b39-959f-6b8991f97ac7" />


<img width="381" height="628" alt="format" src="https://github.com/user-attachments/assets/b57707bc-5c4a-492f-b2e4-7236d34c9d80" />

<img width="731" height="615" alt="metadata" src="https://github.com/user-attachments/assets/f8772f9c-ac4f-471a-ad8f-096f9a9ab325" />

<img width="838" height="693" alt="template" src="https://github.com/user-attachments/assets/981d3141-c400-428d-804d-24a2b2e63768" />

<img width="509" height="715" alt="listingtype" src="https://github.com/user-attachments/assets/db98374e-5ecd-4b78-a848-702821f0e8d9" />

<img width="728" height="359" alt="onion" src="https://github.com/user-attachments/assets/0736c3b6-a48f-4c60-bb76-74a58d74b602" />



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

## Image metadata remover

Use **Tools → Remove Image Metadata** to process images locally before posting them.

Supported output modes:

- overwrite originals
- same folder with a suffix such as `_clean`
- a separate output folder with the same file names

When ImageMagick is available, the scrubber uses ImageMagick `-strip` behavior for parity with `mogrify -strip`; otherwise it falls back to re-encoding images into fresh image objects from pixel data, dropping EXIF, PNG text chunks, and common container metadata that Pillow exposes. Supported formats are JPEG, PNG, WebP, TIFF, BMP, and GIF. Review Studio uses Pillow and does not upload images or call platform-specific tools unless the experimental Imgur option is explicitly enabled.

Experimental Imgur upload is off by default, requires your own Imgur Client ID, and is labeled as not recommended for privacy-sensitive use. The UI includes an **Onion Providers** popup with copy-friendly provider links for manual use instead. Clean locally first, then upload only if you choose to.

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

Use **Tools → Template Profiles** to switch profiles, clone the bundled profile, edit JSON, save custom profiles, or delete custom profiles.

User templates can also be added without changing Python code by placing JSON templates in:

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

## Review folders

The review library groups saved reviews into collapsible folders/categories. Set the folder name from the library panel to keep different review types, vendors, or markets separated without creating separate databases.

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
