# Template Authoring Guide

Review Studio templates are JSON documents that define both the editor structure and the
rendered output.

## Location

Bundled templates live in:

```text
src/review_studio/templates/builtin/
```

User templates can be placed in:

```text
<app data directory>/templates/
```

## Template Structure

Each template includes:

- `id`
- `name`
- `version`
- `description`
- `default_format`
- `rating_options`
- `sections`
- `body`

## Field Types

Supported field types:

- `text`
- `url`
- `multiline`
- `select`
- `rating`

## Field Namespaces

Fields can write to one of three namespaces:

- `value`: referenced as `{{vendor_name}}`
- `rating`: referenced as `{{rating.price_value}}`
- `comment`: referenced as `{{comment.price_value}}`

## Rating Options

Each rating option stores:

```json
{
  "value": 4,
  "name": "Adequate",
  "color": "#90d00f",
  "description": "Baseline: Solid, reliable, meets reasonable expectations."
}
```

The renderer converts the selected rating to formatted BBCode.

## Compatibility Rule

Adding sections or fields to a JSON template should not require Python code changes. Python
changes are only needed for new field types or new rendering behavior.