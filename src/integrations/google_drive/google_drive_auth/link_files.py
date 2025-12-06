"""
File linking module for connecting ZIP files with Google Drive files.
Handles interactive file matching and storage.
"""
import os
from typing import List, Dict, Optional, Tuple
try:
    from googleapiclient.discovery import Resource
except ImportError:
    # For testing without googleapiclient installed
    Resource = type(None)

from .file_matcher import (
    _search_supported_files_by_names,
    _list_supported_drive_files,
    find_maybe_matches,
    search_by_name,
)
from .file_selector import select_from_matches, handle_no_matches
from src.db import store_file_link
import src.constants as constants

def find_and_link_files(service: Resource,project_name: str,zip_files: List[str],conn,user_id: int) -> Dict[str, List[str]]:
    """
    Find and link files from Google Drive to local ZIP files for a given project.
    """
    # Remove any existing links for this project first (to avoid duplicates)
    conn.execute("""
        DELETE FROM project_drive_files 
        WHERE user_id=? AND project_name=?
    """, (user_id, project_name))
    conn.commit()
    
    selected_files: Dict[str, Tuple[str, str, str]] = {}
    not_found_files: List[str] = []
    
    full_drive_cache: Dict[str, List[Dict]] = {"files": None}

    def _load_full_drive_files() -> List[Dict]:
        if full_drive_cache["files"] is None:
            full_drive_cache["files"] = _list_supported_drive_files(service)
        return full_drive_cache["files"]

    # Fetch only candidates that roughly match local file names (avoids scanning entire Drive)
    if constants.VERBOSE:
        print(f"\nLoading candidate files from Google Drive...")
    base_names = {os.path.splitext(name)[0].lower() for name in zip_files}
    all_drive_files = _search_supported_files_by_names(service, list(base_names))
    all_drive_files_list = [(f['id'], f['name'], f['mimeType']) for f in all_drive_files]
    expanded_drive_loaded = False
    
    if constants.VERBOSE:
        print(f"Matching files from '{project_name}' with Google Drive...")
        print("=" * 60)
    
    # Process each file one by one
    for idx, local_file_name in enumerate(zip_files, 1):
        print(f"\n[{idx}/{len(zip_files)}] Looking for: {local_file_name}")
        
        # Find maybe matches with the current (possibly narrowed) list
        maybe_matches = find_maybe_matches(local_file_name, project_name, all_drive_files)

        # If none found, lazily load the full Drive list to enable browsing/search
        if not maybe_matches and not expanded_drive_loaded:
            print("  No candidate matches found; loading full Drive file list for browsing...")
            all_drive_files = _list_supported_drive_files(service)
            all_drive_files_list = [(f['id'], f['name'], f['mimeType']) for f in all_drive_files]
            expanded_drive_loaded = True
            maybe_matches = find_maybe_matches(local_file_name, project_name, all_drive_files)
        
        if maybe_matches:
            selected = select_from_matches(
                local_file_name,
                maybe_matches,
                all_drive_files_list,
                search_by_name,
                load_all_drive_files=_load_full_drive_files,
            )
        else:
            print("  Couldn't find any files that might match.")
            # Ensure browse/search sees the full Drive list
            full_drive_files = _load_full_drive_files()
            full_drive_files_list = [(f['id'], f['name'], f['mimeType']) for f in full_drive_files]
            selected = handle_no_matches(local_file_name, full_drive_files_list, search_by_name)
        
        if selected:
            selected_files[local_file_name] = selected
        else:
            not_found_files.append(local_file_name)
    
    # Store all results in database (only once per file)
    for local_file_name, (drive_file_id, drive_file_name, mime_type) in selected_files.items():
        store_file_link(
            conn, user_id, project_name, local_file_name,
            drive_file_id, drive_file_name, mime_type, 'manual_selected'
        )
    
    for local_file_name in not_found_files:
        store_file_link(
            conn, user_id, project_name, local_file_name,
            'NOT_FOUND', None, None, 'not_found'
        )
    
    # Final summary
    display_final_summary(selected_files, not_found_files)
    
    return {
        'manual': list(selected_files.keys()),
        'not_found': not_found_files
    }


def display_final_summary(selected_files: Dict, not_found_files: List[str]):
    """Display final summary of all file linking results."""
    print("\n" + "=" * 60)
    print("FILE LINKING SUMMARY")
    print("=" * 60)
    
    if selected_files:
        print(f"\n✓ Linked ({len(selected_files)}):")
        for local_name, (_, drive_name, _) in selected_files.items():
            print(f"  • {local_name} → {drive_name}")
    
    if not_found_files:
        print(f"\n✗ Not found ({len(not_found_files)}):")
        for name in not_found_files:
            print(f"  • {name}")
    
    print("\n" + "=" * 60)
