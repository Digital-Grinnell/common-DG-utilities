"""
Common DG (Digital Grinnell) Utilities
Shared utilities for Flet-based Digital Grinnell applications.
"""

from .dg_utils import (
    generate_unique_id,
    calculate_string_similarity,
    sanitize_filename,
    perform_fuzzy_search,
    perform_fuzzy_search_for_transcript,
    perform_fuzzy_search_batch,
    read_markdown,
    read_config,
    session_get,
    show_message,
    validate_csv_headings,
)

__version__ = "0.1.0"
__all__ = [
    "generate_unique_id",
    "calculate_string_similarity",
    "sanitize_filename",
    "perform_fuzzy_search",
    "perform_fuzzy_search_for_transcript",
    "perform_fuzzy_search_batch",
    "read_markdown",
    "read_config",
    "session_get",
    "show_message",
    "validate_csv_headings",
]
