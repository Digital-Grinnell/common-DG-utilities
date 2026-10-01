# Common DG Utilities

Shared utilities for Digital Grinnell Flet-based applications.

## Features

- **Unique ID Generation**: Generate epoch-based unique IDs in `dg_<epoch>` form, with optional `<prefix>_dg_<epoch>` support
- **Key Management**: Enforce and maintain `dg_<epoch>` key values across CSV records and filenames
- **String Similarity**: Calculate similarity between strings for fuzzy matching
- **Filename Sanitization**: Clean and sanitize filenames
- **Fuzzy Search**: Search for files with fuzzy matching capabilities
- **Config Management**: Read and manage configuration files
- **Session Utilities**: Helper functions for Flet session management

## Installation

Install in editable mode from the local directory:

```bash
pip install -e ~/GitHub/common_DG_utilities
```

## Usage

```python
from common_dg_utilities import generate_unique_id

# Generate a unique ID
unique_id = generate_unique_id(page)  # Returns: dg_1234567890

# Generate a prefixed unique ID
prefixed_id = generate_unique_id(page, prefix="tdps")  # Returns: tdps_dg_1234567890
```

## Functions

### `generate_unique_id(page, prefix="")`
Generate a unique ID based on current epoch time with `dg_` prefix.
When `prefix` is supplied, the result becomes `<prefix>_dg_<epoch>`.
Prevents duplicates by checking session storage.

### `ensure_key(record, page=None, slug="", filename=None, key_field="key")`
Enforce `key` field rules on a CSV record (dict), updating it in place and
returning the key:
1. An existing valid `key` is kept unchanged.
2. Otherwise the first `dg_<epoch>` fragment found in any field (or in
   `filename`) is adopted as the key so it is maintained for life.
3. Otherwise a new key is minted via `generate_unique_id` with optional `slug`.

### `is_valid_key(value)`
Return True if `value` is exactly `dg_<epoch>` or `<slug>_dg_<epoch>`.

### `extract_key(text)`
Return the first `dg_<epoch>` (or `<slug>_dg_<epoch>`) fragment embedded in
arbitrary text, or None.

### `calculate_string_similarity(str1, str2)`
Calculate similarity score between two strings.

### `sanitize_filename(filename)`
Clean and sanitize filenames for safe file system use.

### `perform_fuzzy_search(base_path, target_filename, threshold=90)`
Search for files using fuzzy matching.

### And more...
See `dg_utils.py` for complete function documentation.

## Applications Using This Library

- `manage-digital-ingest-flet-CollectionBuilder`
- `Oral-History-Workflow`

## License

MIT License
