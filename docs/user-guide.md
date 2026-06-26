# User Guide

## Workflow

1. Open Review Studio.
2. Create a review.
3. Fill out the structured editor on the left.
4. Watch the generated output update live on the right.
5. Copy or export the completed review.

Users should not need to manually edit BBCode.

## Review Editor

The editor is generated from the active review template. The default template captures:

- Vendor information
- Market information
- Product information
- Purchase date, price, quantity, and order ID
- Quality, value, accuracy, communication, shipping, customer service, and overall ratings
- Comments for each rating
- Shipping details
- Customer service details
- Final summary

## Ratings

Ratings render automatically in the final output:

- `N/A`
- `1/7 - Failure`
- `2/7 - Poor`
- `3/7 - Basic`
- `4/7 - Adequate`
- `5/7 - Strong`
- `6/7 - Advanced`
- `7/7 - Exceptional`

Each rating includes guidance text as a tooltip.

## Live Preview

The preview panel includes:

- **Raw Output:** exact text to copy/export
- **Rendered Preview:** lightweight rendered view for supported markup

Changing a rating or comment updates the preview automatically; no generate button is needed.

## Review Library

The library panel lets you:

- Search previous reviews
- Open old reviews
- Duplicate reviews
- Delete reviews
- Create new reviews

Review Studio restores recent work on startup and autosaves while editing.

## Data Safety

Review Studio saves each review as a JSON file. Writes are atomic and a `.bak` file is kept
when an existing review is replaced. If a review file becomes unreadable, Review Studio tries
to load the backup copy.

The review library search includes template-generated fields and comments.

## Custom Templates

Custom JSON templates can be placed in the user templates folder under the app data directory.
On startup, Review Studio loads bundled templates first, then user templates. A user template
with the same `id` can override a bundled template.

Template fields are rendered automatically in the editor; no GUI code changes are needed for
new template sections or fields.

## Export

Supported export formats:

- BBCode
- Markdown
- HTML
- Plain text
- JSON

Use **Export** or `Ctrl+E`.

## Shortcuts

- `Ctrl+N`: new review
- `Ctrl+S`: save
- `Ctrl+D`: duplicate review
- `Ctrl+E`: export
- `Ctrl+Shift+C`: copy generated preview
- `Ctrl+Z` / `Ctrl+Y`: undo/redo in the focused editor
- `Ctrl+,`: settings
- `Ctrl+Delete`: delete review