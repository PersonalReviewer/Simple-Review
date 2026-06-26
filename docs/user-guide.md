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
- Group reviews into collapsible folders/categories
- Drag reviews into folder rows to move them
- Click folder arrows to collapse/expand review groups
- Rename the current review folder/category from the library panel
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

## Image Metadata Removal

Use **Tools → Remove Image Metadata** to strip EXIF/common metadata from images before sharing them. When ImageMagick is installed, the scrubber uses ImageMagick `-strip` behavior for parity with `mogrify -strip`. If ImageMagick is not available, it falls back to re-encoding fresh image files from pixel data to avoid carrying forward EXIF, PNG text chunks, and common metadata containers exposed by Pillow.

Output choices:

- **Overwrite originals:** replaces the selected images after writing through a temporary file.
- **Same folder, new name:** writes cleaned copies next to originals using a suffix like `_clean`.
- **New folder, same names:** writes cleaned copies into a folder you choose.

All processing is local by default. No image is uploaded by Review Studio unless you explicitly enable the experimental Imgur option and provide an Imgur Client ID.

### Experimental Imgur Upload

The Imgur option is disabled by default and is marked as not recommended for privacy-sensitive use. When enabled, Review Studio cleans the image first, then uploads the cleaned file using anonymous Imgur API access with your Client ID. Failed uploads are reported per file.

Use the **Onion Providers** button to open a copy-friendly popup with manual onion image provider options:

- DeadDrop - `http://deaddrop3m4nxdjueza5vgebsruydayytjy2lf3vj5eqmywtdv7fcrqd.onion/`
- ImageGirl - `http://apig2yathivs562p4gkgtpe4azrqlgxohopsgddrkjxkegkxdt75wqqd.onion/`
- Black Cloud - `http://bcloudwenjxgcxjh6uheyt72a5isimzgg4kv5u74jb2s22y3hzpwh6id.onion`

Review Studio does not open or upload to onion providers automatically; the list is provided for manual copy/paste.

## Template Profiles

Use **Tools → Template Profiles** to manage review formats. You can:

- switch the active profile
- clone the bundled default profile
- edit/save custom JSON profiles
- delete custom profiles

The bundled `default_review` profile is protected. Clone it before editing.

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
- `Ctrl+Shift+M`: remove image metadata
- `Ctrl+Shift+T`: template profiles
- `Ctrl+Delete`: delete review