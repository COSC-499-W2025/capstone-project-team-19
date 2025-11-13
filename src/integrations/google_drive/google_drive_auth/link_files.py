"""
File linking module for connecting ZIP files with Google Drive files.
Handles interactive file matching and storage.
"""
from typing import List, Dict, Optional, Tuple
try:
    from googleapiclient.discovery import Resource
except ImportError:
    # For testing without googleapiclient installed
    Resource = type(None)

from .file_matcher import _list_supported_drive_files, find_maybe_matches, search_by_name
from .file_selector import select_from_matches, handle_no_matches
from src.db import store_file_link


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
    
    # Get all Drive files once at the start
    print(f"\nLoading files from Google Drive...")
    all_drive_files = _list_supported_drive_files(service)
    all_drive_files_list = [(f['id'], f['name'], f['mimeType']) for f in all_drive_files]
    
    print(f"Matching files from '{project_name}' with Google Drive...")
    print("=" * 60)
    
    # Process each file one by one
    for idx, local_file_name in enumerate(zip_files, 1):
        print(f"\n[{idx}/{len(zip_files)}] Looking for: {local_file_name}")
        
        # Find maybe matches
        maybe_matches = find_maybe_matches(local_file_name, project_name, all_drive_files)
        
        if maybe_matches:
            selected = select_from_matches(
                local_file_name, maybe_matches, all_drive_files_list, search_by_name
            )
        else:
            print("  Couldn't find any files that might match.")
            selected = handle_no_matches(local_file_name, all_drive_files_list, search_by_name)
        
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
