"""
parsing.py
-----------
Handles ZIP and directory parsing for project metadata extraction.
Includes:
  - MIME and extension validation
  - Duplicate detection
  - SQLite database storage linkage
"""

import os
import zipfile
import time
import mimetypes
from datetime import datetime

import warnings
warnings.filterwarnings("ignore", message="Duplicate name:")
# This is just to silence the warning in unit test (system doesn't know that we purposefully created a duplicate file for testing)

from db import connect, store_parsed_files, get_or_create_user

TEXT_EXTENSIONS = {".txt", ".csv", ".docx", ".pdf", ".xlsx", ".md"}
CODE_EXTENSIONS = {".py", ".java", ".js", ".html", ".css", ".c", ".cpp", ".h"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS.union(CODE_EXTENSIONS)


# Parses a ZIP archive, extracts metadata for supported files, and stores that metadata in the local SQLite database.
def parse_zip_file(zip_path, user_id: int | None = None, conn=None):
    """Extract a ZIP archive and persist file metadata to the database."""
    zip_path = str(zip_path)

    if not os.path.exists(zip_path):
        print(f"Error: The file at {zip_path} does not exist.")
        return
    
    if not zip_path.lower().endswith(".zip"):
        print(f"Error: The provided file is not a ZIP file.")
        return
    
    if not zipfile.is_zipfile(zip_path):
        print(f"Error: The file is not a valid ZIP archive.")
        return
    
    zip_stats = os.stat(zip_path)  # for created time

    files_info = collect_file_info(zip_path, zip_stats)

    if not files_info:
        print("No supported files found in the ZIP.")
        return []
    
    # Store parsed data in local database
    created_conn = False
    if conn is None:
        conn = connect()
        created_conn = True

    if user_id is None:
        user_id = get_or_create_user(conn, "local-user")

    store_parsed_files(conn, files_info, user_id)

    if created_conn:
        conn.close()

    print(f"Extracted and stored {len(files_info)} files in database (user_id={user_id})")
    return files_info


def classify_file(extension: str) -> str:
    if extension in TEXT_EXTENSIONS:
        return "text"
    elif extension in CODE_EXTENSIONS:
        return "code"
    else:
        return "other"


# MIME-based validation provides an extra safety check beyond file extensions, preventing misclassified or fake file types.
def is_valid_mime(file_path, extension):
    mime, _ = mimetypes.guess_type(file_path)
    
    # If windows can not guess the MIME, trust the extension
    if not mime:
        return extension in SUPPORTED_EXTENSIONS # trust extensions instead
    
    # Text formats
    if extension in TEXT_EXTENSIONS:
        # Expanded set of valid text-related MIME types
        valid_text_mimes = {
            "text/plain",
            "text/csv",
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/markdown",
            "text/x-markdown",
            "application/msword",  # older DOCs sometimes show up as this
            "application/vnd.ms-excel"
        }

        # CSV sometimes appears as plain text or Excel MIME on Windows
        if extension == ".csv" and (
            mime in ("text/plain", "application/vnd.ms-excel", "text/csv")
        ):
            return True

        return mime.startswith("text") or mime in valid_text_mimes

    # Code formats
    if extension in CODE_EXTENSIONS:
        valid_code_mimes = {
            "text/x-python",
            "text/x-c",
            "text/x-c++",
            "text/x-java-source",
            "application/javascript",
            "text/javascript",
            "text/html",
            "text/css",
        }
        return mime.startswith("text") or mime in valid_code_mimes
    return False


def collect_file_info(zip_path, zip_stats = None):
    """
    Collect metadata about supported files from either:
        - a ZIP archive, or
        - a directory (used in tests and local runs).
    
    Returns a list of file info dictionaries containing:
        file_path, file_name, extension, file_type, size_bytes, created, modified
    """

    if zip_stats is None:
        zip_stats = os.stat(zip_path)

    collected = []
    seen = set()

    # NOTE:
    # This function primarily extracts file metadata from ZIP archives for user-uploaded projects.
    # However, for testing purposes, it also supports scanning regular directories.
    # Some unit tests focus only on metadata accuracy (not ZIP handling),
    # so this dual behavior ensures consistent test coverage without rewriting the test suite.
    if os.path.isdir(zip_path):
        for folder, _, files in os.walk(zip_path):
            for file in files:
                full_path = os.path.join(folder, file)
                extension = os.path.splitext(file)[1].lower()

                # Skip unsupported file types
                if extension not in SUPPORTED_EXTENSIONS:
                    continue
                if not is_valid_mime(full_path, extension):
                    continue

                stats = os.stat(full_path)
                size = stats.st_size

                # Unique key includes directory path to avoid cross-folder duplicates
                key = (file, size, os.path.dirname(full_path))
                if key in seen:
                    continue
                seen.add(key)

                collected.append({
                    "file_path": os.path.relpath(full_path, zip_path),
                    "file_name": file,
                    "extension": extension,
                    "file_type": classify_file(extension),
                    "size_bytes": size,
                    "created": time.ctime(stats.st_ctime),
                    "modified": time.ctime(stats.st_mtime),
                })

        return collected

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for name in zip_ref.namelist():
            if name.endswith("/"):  # Skip folders
                continue

            info = zip_ref.getinfo(name)
            filename = os.path.basename(name)
            extension = os.path.splitext(filename)[1].lower()

            # Skip unsupported or unknown file types
            if extension not in SUPPORTED_EXTENSIONS:
                print(f"Unsupported file skipped: {filename}")
                continue

            mime, _ = mimetypes.guess_type(filename)
            if not is_valid_mime(filename, extension):
                print(f"Unsupported file skipped (invalid MIME): {filename} ({mime})")
                continue

            size = info.file_size

            # Skip exact duplicates (same path inside ZIP + same size)
            key = (name.lower(), size)
            if key in seen:
                print(f"Duplicate skipped: {filename}")
                continue
            seen.add(key)

            modified_dt = datetime(*info.date_time)

            collected.append({
                "file_path": name,
                "file_name": filename,
                "extension": extension,
                "file_type": classify_file(extension),
                "size_bytes": size,
                "created": time.ctime(zip_stats.st_ctime),  # ZIP creation (approx project creation)
                "modified": modified_dt.ctime(),  # File modification timestamp from ZIP metadata
            })
            
    return collected


BUCKET_LABELS = {
    "individual": "individual",
    "collaborative": "collaborative",
}


def analyze_project_layout(files_info: list[dict]) -> dict:
    """
    Inspect the parsed file list and infer project groupings.

    Returns a dictionary with:
      - root_name: the single top-level folder (if present)
      - auto_assignments: projects inferred as individual/collaborative
      - pending_projects: projects that still need manual classification
      - stray_locations: locations that only contained loose files
    """
    path_parts = []
    for entry in files_info:
        rel_path = entry.get("file_path") or entry.get("file_name")
        if not rel_path:
            continue
        normalized = rel_path.replace("\\", "/")
        parts = [part for part in normalized.split("/") if part]
        if not parts:
            continue
        if parts[0].startswith("__MACOSX"):
            continue
        path_parts.append(parts)

    if not path_parts:
        return {
            "root_name": None,
            "auto_assignments": {},
            "pending_projects": [],
            "stray_locations": [],
        }

    top_level_map: dict[str, list[list[str]]] = {}
    for parts in path_parts:
        top = parts[0]
        top_level_map.setdefault(top, []).append(parts)

    # Determine if there is a single root folder
    root_name = next(iter(top_level_map)) if len(top_level_map) == 1 else None

    auto_assignments: dict[str, str] = {}
    pending_projects: set[str] = set()
    stray_locations: set[str] = set()

    if root_name:
        root_paths = top_level_map[root_name]
        second_level_map: dict[str, list[list[str]]] = {}
        for parts in root_paths:
            if len(parts) > 1:
                second = parts[1]
                second_level_map.setdefault(second, []).append(parts)

        bucket_aliases = {
            name: BUCKET_LABELS[name.lower()]
            for name in second_level_map
            if name.lower() in BUCKET_LABELS
        }

        # Buckets for automatic classification
        for bucket_name, label in bucket_aliases.items():
            bucket_paths = second_level_map.get(bucket_name, [])
            projects = _collect_folder_names(bucket_paths, start_index=2)
            for project in projects:
                auto_assignments[project] = label
            if bucket_paths and not projects:
                stray_locations.add(bucket_name)

        # Remaining folders under the root
        for name, paths in second_level_map.items():
            if name.lower() in BUCKET_LABELS:
                continue
            if _has_nested_paths(paths, start_index=1):
                pending_projects.add(name)
            else:
                stray_locations.add(name)

        if not auto_assignments and not pending_projects:
            # Treat the root itself as a project if it only contains loose files
            if any(len(parts) == 2 for parts in root_paths):
                pending_projects.add(root_name)

    else:
        # Handle buckets that live at the top level
        bucket_aliases = {
            name: BUCKET_LABELS[name.lower()]
            for name in top_level_map
            if name.lower() in BUCKET_LABELS
        }

        for bucket_name, label in bucket_aliases.items():
            bucket_paths = top_level_map.get(bucket_name, [])
            projects = _collect_folder_names(bucket_paths, start_index=1)
            for project in projects:
                auto_assignments[project] = label
            if bucket_paths and not projects:
                stray_locations.add(bucket_name)

        for name, paths in top_level_map.items():
            if name.lower() in BUCKET_LABELS:
                continue
            if _has_nested_paths(paths, start_index=0):
                pending_projects.add(name)
            else:
                stray_locations.add(name)

    pending_list = sorted(project for project in pending_projects if project not in auto_assignments)
    return {
        "root_name": root_name,
        "auto_assignments": auto_assignments,
        "pending_projects": pending_list,
        "stray_locations": sorted(stray_locations),
    }


def _collect_folder_names(paths: list[list[str]], start_index: int) -> set[str]:
    """Collect folder names at the given index when deeper content exists."""
    projects: set[str] = set()
    for parts in paths:
        if len(parts) > start_index + 1:
            projects.add(parts[start_index])
    return projects


def _has_nested_paths(paths: list[list[str]], start_index: int) -> bool:
    """Return True if any path has deeper content beyond the given index."""
    return any(len(parts) > start_index + 1 for parts in paths)
