import flet as ft
import os
from subprocess import call
import json
import sys
import logging
import time
import re

# Unique ID generation
# ----------------------------------------------------------------------
def generate_unique_id(page, prefix=""):
    """
    Generate a unique ID based on current epoch time.
    Checks session storage to ensure no duplicates exist.
    If a duplicate is found, increments the epoch value until unique.
    
    Args:
        page: The Flet page object containing session data
        prefix: Optional prefix to prepend before the standard dg_ ID.
    
    Returns:
        str: Unique ID formatted as "dg_<epoch_time>" or
             "<prefix>_dg_<epoch_time>" when prefix is supplied.
    
    Example:
        >>> generate_unique_id(page)
        'dg_1729123456'
        >>> generate_unique_id(page, prefix="tdps")
        'tdps_dg_1729123456'
    """
    # Initialize the set of generated IDs in session if not present
    if not hasattr(page.session, 'generated_ids'):
        page.session.generated_ids = set()

    normalized_prefix = str(prefix or "").strip().rstrip("_")
    
    # Start with current epoch time
    epoch_time = int(time.time())
    base_id = f"dg_{epoch_time}"
    unique_id = f"{normalized_prefix}_{base_id}" if normalized_prefix else base_id
    
    # Increment until we find a unique ID
    while unique_id in page.session.generated_ids:
        epoch_time += 1
        base_id = f"dg_{epoch_time}"
        unique_id = f"{normalized_prefix}_{base_id}" if normalized_prefix else base_id
    
    # Store the new ID in session
    page.session.generated_ids.add(unique_id)
    
    return unique_id

# 'key' field management
# ----------------------------------------------------------------------
# Rules for 'key' management:
#   1. A 'key' value always contains a 'dg_<epoch_time>' string as generated
#      by generate_unique_id().
#   2. To help ensure EVERY 'key' is universally unique there may be a <slug>
#      or <prefix> value before the 'dg_' with an underscore separator, e.g.
#      'tdps_dg_1729123456'.
#   3. Any record or filename that contains a 'dg_<epoch_time>' value or
#      fragment in ANY field MUST maintain that 'key' value throughout its life.

# Matches 'dg_<digits>' optionally preceded by '<slug>_' where the slug
# contains letters, digits, or hyphens.
KEY_REGEX = re.compile(r"(?:[A-Za-z0-9][A-Za-z0-9-]*_)?dg_\d+")


def is_valid_key(value):
    """
    Check whether a value is a valid 'key' string.

    A valid key is exactly 'dg_<epoch_time>' or '<slug>_dg_<epoch_time>'
    where <slug> contains only letters, digits, or hyphens.

    Args:
        value: The value to check (non-string values are coerced with str()).

    Returns:
        bool: True if the value exactly matches the key pattern.

    Example:
        >>> is_valid_key('dg_1729123456')
        True
        >>> is_valid_key('tdps_dg_1729123456')
        True
        >>> is_valid_key('photo dg_1729123456.jpg')
        False
    """
    if value is None:
        return False
    return KEY_REGEX.fullmatch(str(value).strip()) is not None


def extract_key(text):
    """
    Find and return the first 'key' fragment embedded in arbitrary text.

    Searches for 'dg_<epoch_time>' optionally preceded by '<slug>_'.  Works on
    any CSV field value or filename.  When a word immediately precedes 'dg_'
    with an underscore separator it is treated as the slug and included in the
    returned fragment (the longest valid key fragment is maintained).

    Args:
        text: The text to search.

    Returns:
        str or None: The matched key fragment (e.g. 'dg_1729123456' or
        'tdps_dg_1729123456'), or None if no fragment is present.

    Example:
        >>> extract_key('photo tdps_dg_1729123456.jpg')
        'tdps_dg_1729123456'
        >>> extract_key('scan_dg_1729123456.tif')
        'scan_dg_1729123456'
        >>> extract_key('no key here') is None
        True
    """
    if text is None:
        return None
    match = KEY_REGEX.search(str(text))
    return match.group(0) if match else None


def ensure_key(record, page=None, slug="", filename=None, key_field="key"):
    """
    Enforce 'key' management rules for a CSV record (a mutable mapping such as
    a dict of field names to values).  The record is updated in place and the
    enforced key is returned.

    Rules enforced, in order:
      1. If record[key_field] is already a valid key, it is kept unchanged.
      2. Otherwise every field of the record (and `filename`, if given) is
         scanned for an embedded 'dg_<epoch_time>' fragment; the first
         fragment found becomes the key so the value is maintained throughout
         the record's life.
      3. Otherwise a new key is minted with generate_unique_id() (using `page`
         for session de-duplication when available) and the optional `slug`.

    Args:
        record (dict): Mutable mapping of CSV field names to values.
        page: Optional Flet page object; passed to generate_unique_id() so new
              keys are de-duplicated within the session.
        slug (str): Optional slug/prefix applied only when a NEW key is
                    generated, e.g. 'tdps' produces 'tdps_dg_<epoch>'.
        filename (str): Optional filename associated with the record; scanned
                        for a key fragment before a new key is generated.
        key_field (str): Name of the key column. Defaults to 'key'.

    Returns:
        str: The enforced key value.

    Example:
        >>> row = {'filename': 'scan dg_1729123456.tif', 'title': 'Photo'}
        >>> ensure_key(row)
        'dg_1729123456'
        >>> row['key']
        'dg_1729123456'
    """
    # Rule 1 - an existing valid key MUST be maintained
    existing = record.get(key_field)
    if is_valid_key(existing):
        return str(existing).strip()

    # Rule 2 - maintain any dg_<epoch_time> fragment found in any field
    # (including a malformed key field) or in the associated filename
    search_values = list(record.values())
    if filename:
        search_values.append(filename)
    for value in search_values:
        fragment = extract_key(value)
        if fragment:
            record[key_field] = fragment
            logging.info(f"Maintained existing key '{fragment}' in field '{key_field}'")
            return fragment

    # Rule 3 - mint a brand-new key
    if page is not None:
        new_key = generate_unique_id(page, prefix=slug)
    else:
        normalized_slug = str(slug or "").strip().rstrip("_")
        base_id = f"dg_{int(time.time())}"
        new_key = f"{normalized_slug}_{base_id}" if normalized_slug else base_id
        logging.warning("ensure_key() minted a key without a page session; "
                        "uniqueness is not de-duplicated across the session")

    record[key_field] = new_key
    logging.info(f"Generated new key '{new_key}' in field '{key_field}'")
    return new_key

# Simple string matching functions
# ----------------------------------------------------------------------
def calculate_string_similarity(str1, str2):
    """
    Calculate similarity between two strings using a simple approach.
    Returns a percentage (0-100) of how similar the strings are.
    """
    if str1 == str2:
        return 100
    
    # Simple substring matching approach
    if str1 in str2 or str2 in str1:
        # Calculate ratio based on length overlap
        overlap = min(len(str1), len(str2))
        total = max(len(str1), len(str2))
        return int((overlap / total) * 100)
    
    # Count common characters
    common_chars = 0
    str1_chars = list(str1)
    str2_chars = list(str2)
    
    for char in str1_chars:
        if char in str2_chars:
            common_chars += 1
            str2_chars.remove(char)
    
    # Calculate similarity based on common characters
    total_chars = max(len(str1), len(str2))
    if total_chars == 0:
        return 0
    
    return int((common_chars / total_chars) * 100)

def sanitize_filename(filename):
    """
    Sanitize a filename by replacing spaces and special characters.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        str: Sanitized filename with spaces replaced by underscores,
             special characters removed, and hyphens cleaned up
    """
    import re
    # Replace spaces with underscores
    sanitized = filename.replace(' ', '_')
    # Remove or replace other problematic characters (keep word chars, hyphens, underscores, dots)
    sanitized = re.sub(r'[^\w\-_\.]', '_', sanitized)
    # Clean up multiple underscores around hyphens: _-_ or -_ or _- becomes just -
    sanitized = re.sub(r'_*-_*', '-', sanitized)
    # Clean up any remaining multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized

def perform_fuzzy_search(base_path, target_filename, threshold=90):
    """
    Recursively search for files in base_path and find the best match for target_filename
    using simple string matching.
    
    Enhanced to handle files without extensions: if the target filename has no extension,
    an exact match of the basename (without extension) gets a score of 90 or more.
    
    Args:
        base_path (str): The directory to start searching from
        target_filename (str): The filename to match against
        threshold (int): The minimum match percentage to consider a match (0-100)
        
    Returns:
        tuple: (best_match_path, best_match_ratio) or (None, 0) if no match found
    """
    try:
        best_match_path = None
        best_match_ratio = 0
        
        # Check if target filename has an extension
        target_name, target_ext = os.path.splitext(target_filename)
        target_has_extension = bool(target_ext)
        
        for root, dirs, files in os.walk(base_path):
            for filename in files:
                # Calculate simple string similarity ratio
                ratio = calculate_string_similarity(filename.lower(), target_filename.lower())
                
                # Enhanced logic for files without extensions
                if not target_has_extension:
                    # If target has no extension, check for exact basename match
                    file_name, file_ext = os.path.splitext(filename)
                    if file_name.lower() == target_name.lower():
                        # Exact basename match gets high score (90+)
                        # Give slightly higher score based on extension length to prefer shorter extensions
                        ratio = max(ratio, 90 + min(10, 10 - len(file_ext)))
                
                # Update best match if this ratio is higher
                if ratio > best_match_ratio:
                    best_match_ratio = ratio
                    best_match_path = os.path.join(root, filename)
                    
                    # If we found a perfect match, we can return immediately
                    if ratio == 100:
                        return (best_match_path, ratio)
        
        # Always return the best match path and ratio found, regardless of threshold
        # The caller will decide whether to accept it based on the threshold
        return (best_match_path, best_match_ratio)
            
    except Exception as e:
        logging.error(f"Error in fuzzy search: {str(e)}")
        return (None, 0)


def perform_fuzzy_search_for_transcript(base_path, target_filename, threshold=90):
    """
    Enhanced fuzzy search specifically for transcript records.
    
    When searching for a transcript record, this function:
    1. Prioritizes finding media files (audio/video) over CSV files
    2. Also locates matching transcript .csv files with the same basename
    
    Args:
        base_path (str): The directory to start searching from
        target_filename (str): The filename to match against
        threshold (int): The minimum match percentage to consider a match (0-100)
        
    Returns:
        tuple: (media_path, media_ratio, transcript_csv_path) or (None, 0, None) if no match found
        - media_path: Path to the best matching media file (audio/video)
        - media_ratio: Match score for the media file
        - transcript_csv_path: Path to matching transcript .csv file (if found)
    """
    try:
        # Media file extensions to prioritize
        media_extensions = {'.mp3', '.mp4', '.wav', '.m4a', '.flac', '.ogg', '.webm', '.mov', '.avi', '.mkv'}
        
        best_media_path = None
        best_media_ratio = 0
        transcript_csv_path = None
        
        # Check if target filename has an extension
        target_name, target_ext = os.path.splitext(target_filename)
        target_has_extension = bool(target_ext)
        
        for root, dirs, files in os.walk(base_path):
            for filename in files:
                file_name, file_ext = os.path.splitext(filename)
                file_ext_lower = file_ext.lower()
                
                # Calculate similarity
                ratio = calculate_string_similarity(filename.lower(), target_filename.lower())
                
                # Enhanced logic for files without extensions
                if not target_has_extension and file_name.lower() == target_name.lower():
                    # Exact basename match gets high score (90+)
                    ratio = max(ratio, 90 + min(10, 10 - len(file_ext)))
                
                # Check if this is a media file
                if file_ext_lower in media_extensions:
                    # Update best media match if this ratio is higher
                    if ratio > best_media_ratio:
                        best_media_ratio = ratio
                        best_media_path = os.path.join(root, filename)
                        
                        # If we found a perfect match, we can stop looking for media
                        if ratio == 100:
                            # But continue to look for transcript CSV in this directory
                            pass
                
                # Also look for matching transcript CSV files
                if file_ext_lower == '.csv':
                    # Check if basename matches (for transcript files)
                    if not target_has_extension and file_name.lower() == target_name.lower():
                        transcript_csv_path = os.path.join(root, filename)
                        logging.info(f"Found matching transcript CSV: {transcript_csv_path}")
                    elif target_has_extension and file_name.lower() == target_name.lower():
                        transcript_csv_path = os.path.join(root, filename)
                        logging.info(f"Found matching transcript CSV: {transcript_csv_path}")
        
        return (best_media_path, best_media_ratio, transcript_csv_path)
            
    except Exception as e:
        logging.error(f"Error in transcript fuzzy search: {str(e)}")
        return (None, 0, None)


def perform_fuzzy_search_batch(base_path, target_filenames, threshold=90, progress_callback=None, cancel_check=None, transcript_info=None):
    """
    Perform fuzzy search for multiple filenames sequentially with progress tracking and cancellation support.
    
    Enhanced to handle transcript records: when a file is marked as a transcript, it searches for
    media files (audio/video) and also captures matching transcript .csv files.
    
    Args:
        base_path (str): The directory to start searching from
        target_filenames (list): List of filenames to match against
        threshold (int): The minimum fuzzy match ratio to consider a match (0-100)
        progress_callback (callable): Optional callback function to report progress (0.0 to 1.0)
        cancel_check (callable): Optional function that returns True if search should be cancelled
        transcript_info (dict): Optional dictionary mapping filenames to display_template values
                                If a filename maps to 'transcript', special transcript search is used
        
    Returns:
        dict: Dictionary with results. For normal files: {filename: (match_path, ratio)}
              For transcript files: {filename: (media_path, ratio, transcript_csv_path)}
              Returns None if cancelled
    """
    results = {}
    total_files = len(target_filenames)
    
    if progress_callback:
        # Start with 0% progress
        progress_callback(0)
    
    for index, filename in enumerate(target_filenames):
        # Check for cancellation
        if cancel_check and cancel_check():
            logging.info("Fuzzy search cancelled by user")
            return None
        
        # Check if this is a transcript record
        is_transcript = False
        if transcript_info and filename in transcript_info:
            display_template = transcript_info[filename].lower().strip()
            is_transcript = (display_template == 'transcript')
        
        if is_transcript:
            logging.info(f"Searching for TRANSCRIPT media/CSV for '{filename}' ({index + 1}/{total_files})")
        else:
            logging.info(f"Searching for match to '{filename}' ({index + 1}/{total_files})")
        
        # Update progress after each file
        if progress_callback:
            progress = (index + 1) / total_files
            progress_callback(progress)
        
        # Use appropriate search method
        if is_transcript:
            media_path, ratio, transcript_csv = perform_fuzzy_search_for_transcript(base_path, filename, threshold)
            results[filename] = (media_path, ratio, transcript_csv)
            
            # Log the results
            if media_path and ratio >= threshold:
                logging.info(f"Found media match for transcript '{filename}': {media_path} ({ratio}% match)")
                if transcript_csv:
                    logging.info(f"Also found transcript CSV: {transcript_csv}")
            else:
                logging.info(f"No media match found for transcript '{filename}' meeting {threshold}% threshold")
        else:
            match_path, ratio = perform_fuzzy_search(base_path, filename, threshold)
            results[filename] = (match_path, ratio)
            
            # Log the result
            if match_path and ratio >= threshold:
                logging.info(f"Found match for '{filename}': {match_path} ({ratio}% match)")
            else:
                logging.info(f"No match found for '{filename}' meeting {threshold}% threshold")
    
    # Only show 100% if we completed the search (not cancelled)
    if progress_callback:
        progress_callback(1.0)
        
    return results

# # Example AppBar component
# def build_app_bar( ):
#     return ft.AppBar(title=ft.Text("My App"), actions=[
#         ft.IconButton(icon=ft.Icons.MENU),
#         ]
#     )

# # Example AppBar component
# def get_app_bar(page=None):
#     if page:
#         page.appbar=ft.AppBar(
#                 title=ft.Text("Flet-X: Manage Digital Ingest"),
#                 actions=[
#                     ft.FilledButton(
#                         text="Home",
#                         # on_click=data.go(data.route_init),
#                     ),
#                     ft.VerticalDivider(opacity=0),
#                     ft.FilledButton(
#                         text="Counter",
#                         # on_click=data.go("/counter/test/0"),
#                     ),
#                     ft.VerticalDivider(opacity=0),
#                     ft.FilledButton(
#                         text="Picker",
#                         # on_click=data.go("/picker"),
#                     ),
#                     ft.VerticalDivider(opacity=0),
#                     ft.FilledButton(
#                         text="Mode",
#                         # on_click=data.go("/mode"),
#                     ),
#                     ft.VerticalDivider(opacity=0),
#                     ft.FilledButton(
#                         text="Show Data",
#                         # on_click=data.go("/show_data"),
#                     ),
#                     ft.VerticalDivider(opacity=0),
#                     ft.FilledButton(
#                         text="Exit",
#                         # on_click=data.go("/exit"),
#                     ),
#                     # One more divider for better button spacing
#                     ft.VerticalDivider(opacity=0),
#                 ],
#                 bgcolor="#121113",
#             )
#         return pageappbar





# Read markdown file from _data directory
# ------------------------------------------------------------------------------
def read_markdown(filename):
    """
    Read markdown content from a file.
    
    Args:
        filename (str): The filename (with path) to read
        
    Returns:
        str: The markdown content
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.error(f"Markdown file not found: {filename}")
        return f"# Error\n\nMarkdown file not found: {filename}"
    except Exception as e:
        logging.error(f"Error reading markdown file {filename}: {e}")
        return f"# Error\n\nError reading markdown file: {str(e)}"


# Read config from _data/config.json and return as 'config'
# ------------------------------------------------------------------------------
def read_config(page=None):
    # Load configuration from _data/config.json
    with open('_data/config.json', 'r') as config_file:
        config = json.load(config_file) 

    # Print config values to console for debugging and store them in page.session
    print(f"Values from _data/config.json... ")
    for key, value in config.items( ):
        print(f"{key}: {value}")
        # Store config values in page session if needed
        if page:
            page.session.set(key, value)  

    return config


# Helper function to get session value with default
# ------------------------------------------------------------------------------
def session_get(page, key, default=None):
    """
    Get a value from page.session with a default fallback.
    
    Args:
        page: The Flet page object
        key (str): The session key to retrieve
        default: The default value to return if key is not found or is None
        
    Returns:
        The session value or the default value
    """
    value = page.session.get(key)
    return value if value is not None else default


# Helper function to display message in the SnackBar
# ------------------------------------------------------------
def show_message(page, text, is_error=False):
    """Helper function to update and show the SnackBar."""
    logger = page.session.get("logger")
    if is_error:
        logger.error(text)
    else:
        logger.info(text)
    
    # Ensure snackbar exists
    if not hasattr(page, 'snack_bar') or page.snack_bar is None:
        page.snack_bar = ft.SnackBar(content=ft.Text(text))
    
    page.snack_bar.content.value = text
    page.snack_bar.bgcolor = ft.Colors.RED_600 if is_error else ft.Colors.GREEN_600
    page.open(page.snack_bar)
    page.update()


# Validate CSV headings against verified heading files
# ------------------------------------------------------------
def validate_csv_headings(csv_file_path, mode):
    """
    Validate CSV file headings against verified heading files for CollectionBuilder.
    
    Args:
        csv_file_path: Path to the CSV file to validate
        mode: 'CollectionBuilder' (Alma no longer supported)
        
    Returns:
        tuple: (is_valid: bool, unmatched_headings: list, error_message: str or None)
        - is_valid: Always True for CollectionBuilder (permissive validation)
        - unmatched_headings: List of headings that don't match verified list
        - error_message: Error message if there was a problem, None otherwise
        
    Notes:
        - For CollectionBuilder mode: CSV headings are checked against verified list,
          but extra headings are allowed (more permissive).
        - Order of headings does not matter, only the names.
    """
    import pandas as pd
    
    # Use CollectionBuilder verified headings file
    verified_file = os.path.join("_data", "verified_CSV_headings_for_GCCB_projects.csv")
    
    # Check if verified file exists
    if not os.path.exists(verified_file):
        return (False, [], f"Verified headings file not found: {verified_file}")
    
    # Check if CSV file exists
    if not os.path.exists(csv_file_path):
        return (False, [], f"CSV file not found: {csv_file_path}")
    
    try:
        # Read the verified headings (first row only)
        verified_df = pd.read_csv(verified_file, nrows=0, dtype=str, keep_default_na=False)
        verified_headings = set(verified_df.columns.tolist())
        
        # Read the CSV file headings (first row only) with multiple encodings
        csv_df = None
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
        
        for encoding in encodings:
            try:
                # Read all columns as strings to prevent scientific notation
                csv_df = pd.read_csv(csv_file_path, nrows=0, encoding=encoding, dtype=str, keep_default_na=False)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if csv_df is None:
            return (False, [], f"Could not read CSV file with any supported encoding")
        
        csv_headings = set(csv_df.columns.tolist())
        
        # Find headings in CSV that are NOT in verified list
        unmatched_headings = list(csv_headings - verified_headings)
        
        # CollectionBuilder mode: be permissive - just report unmatched but don't fail
        # (extra headings are OK)
        return (True, unmatched_headings, None)
            
    except Exception as e:
        return (False, [], f"Error validating CSV headings: {str(e)}")

# MIME type mapping
# ----------------------------------------------------------------------
def get_mime_type(filename):
    """
    Get the MIME type for a file based on its extension.
    
    Args:
        filename (str): The filename or path to check
        
    Returns:
        str: MIME type string (e.g., 'image/jpeg', 'application/pdf')
             Returns 'application/octet-stream' for unknown types
    
    Example:
        >>> get_mime_type('photo.jpg')
        'image/jpeg'
        >>> get_mime_type('document.pdf')
        'application/pdf'
        >>> get_mime_type('video.mp4')
        'video/mp4'
    """
    import os
    
    # Get extension (lowercase, without the dot)
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    
    # Comprehensive MIME type mapping
    mime_types = {
        # Images
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'tif': 'image/tiff',
        'tiff': 'image/tiff',
        'svg': 'image/svg+xml',
        'webp': 'image/webp',
        'ico': 'image/x-icon',
        
        # Documents
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'odt': 'application/vnd.oasis.opendocument.text',
        'ods': 'application/vnd.oasis.opendocument.spreadsheet',
        'odp': 'application/vnd.oasis.opendocument.presentation',
        
        # Text
        'txt': 'text/plain',
        'csv': 'text/csv',
        'html': 'text/html',
        'htm': 'text/html',
        'xml': 'application/xml',
        'json': 'application/json',
        'md': 'text/markdown',
        'rtf': 'application/rtf',
        
        # Audio
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'ogg': 'audio/ogg',
        'flac': 'audio/flac',
        'm4a': 'audio/mp4',
        'aac': 'audio/aac',
        'wma': 'audio/x-ms-wma',
        
        # Video
        'mp4': 'video/mp4',
        'avi': 'video/x-msvideo',
        'mov': 'video/quicktime',
        'wmv': 'video/x-ms-wmv',
        'flv': 'video/x-flv',
        'mkv': 'video/x-matroska',
        'webm': 'video/webm',
        'mpg': 'video/mpeg',
        'mpeg': 'video/mpeg',
        
        # Archives
        'zip': 'application/zip',
        'tar': 'application/x-tar',
        'gz': 'application/gzip',
        'bz2': 'application/x-bzip2',
        'rar': 'application/vnd.rar',
        '7z': 'application/x-7z-compressed',
        
        # Other
        'js': 'application/javascript',
        'css': 'text/css',
        'py': 'text/x-python',
        'sh': 'application/x-sh',
        'exe': 'application/x-msdownload',
    }
    
    return mime_types.get(ext, 'application/octet-stream')
