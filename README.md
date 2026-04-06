# Common DG Utilities

Shared utilities for Digital Grinnell Flet-based applications.

## Features

- **Unique ID Generation**: Generate epoch-based unique IDs with `dg_` prefix
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
```

## Functions

### `generate_unique_id(page)`
Generate a unique ID based on current epoch time with `dg_` prefix.
Prevents duplicates by checking session storage.

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
