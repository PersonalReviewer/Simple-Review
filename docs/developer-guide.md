# Developer Guide

## Architecture

Review Studio uses a layered architecture:

```text
review_studio.gui
  -> review_studio.gui.view_models
  -> review_studio.services
  -> review_studio.domain
  -> review_studio.storage / templates / exporters / preview
```

## Important Modules

- `domain.models`: review document, ratings, serialization
- `domain.template_schema`: JSON template schema, sections, fields, and rating definitions
- `domain.value_objects`: rating values and descriptions
- `templates.engine`: Jinja2 template rendering
- `storage.repository`: atomic JSON review persistence and search
- `storage.settings`: persistent user settings
- `exporters.export_service`: BBCode/Markdown/HTML/text/JSON export
- `gui.main_window`: PySide6 split-screen UI
- `gui.view_models.main_view_model`: GUI-independent workflow coordination

## Template Rules

Bundled templates live under:

```text
src/review_studio/templates/builtin/
```

Do not hardcode templates in GUI code. Template rendering should go through
`TemplateEngine` and `TemplateService`.

The GUI must generate editor controls from `ReviewTemplate.sections`. New templates should not
require Python changes unless they introduce a new field type.

### Template Field Model

Fields define:

- `key`: variable name
- `label`: user-facing label
- `type`: `text`, `url`, `multiline`, `select`, or `rating`
- `namespace`: `value`, `rating`, or `comment`
- `required`: validation guidance
- `options`: select options when applicable

Template body examples:

```jinja2
{{ vendor_name }}
{{ rating.price_value }}
{{ comment.price_value }}
```

Ratings are stored as stable values such as `na`, `1`, `2`, etc. Rendering converts them to
formatted BBCode using the active template's rating definitions.

## Testing

Run tests with:

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python -m unittest discover -s tests
```

GUI tests use the Qt offscreen platform to avoid requiring a visible display in CI.

## Data Safety

Review files are JSON documents written with atomic replacement. Changes to persistence
should preserve this behavior and include tests for save/load/search/delete workflows.

Existing files are backed up as `.bak` before replacement. Repository loading attempts to use
the backup when the primary JSON file is corrupt.

## Adding Features

When adding a new feature:

1. Define or update domain concepts first.
2. Add service/view-model workflow behavior.
3. Add GUI wiring last.
4. Add tests close to the layer being changed.
5. Run the full test suite.