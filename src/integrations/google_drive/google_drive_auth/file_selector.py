"""
Interactive file selection UI module.
Handles all user interaction for selecting files from Google Drive.
"""
from typing import List, Dict, Tuple, Optional, Callable


def select_from_matches(
    local_file_name: str,
    maybe_matches: List[Tuple[str, str, str]],
    all_drive_files: List[Tuple[str, str, str]],
    search_function: Callable
) -> Optional[Tuple[str, str, str]]:
    """
    Show potential matches and get user selection.
    """
    print(f"\nFound {len(maybe_matches)} potential match(es):")
    for match_idx, (file_id, file_name, mime_type) in enumerate(maybe_matches, 1):
        print(f"  {match_idx}. {file_name}")
    
    print(f"  {len(maybe_matches) + 1}. None of these (search by name or browse all)")
    print(f"  {len(maybe_matches) + 2}. Skip this file")
    
    while True:
        try:
            choice = input(f"\nSelect option (1-{len(maybe_matches) + 2}): ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(maybe_matches):
                # User selected a match
                selected = maybe_matches[choice_num - 1]
                file_id, file_name, mime_type = selected
                print(f"  ✓ Selected: {file_name}")
                return selected
            elif choice_num == len(maybe_matches) + 1:
                # User wants to search or browse
                return handle_no_matches(local_file_name, all_drive_files, search_function)
            elif choice_num == len(maybe_matches) + 2:
                # Skip
                print(f"  X Skipped: {local_file_name}")
                return None
            else:
                print("  Invalid choice, please try again.")
        except ValueError:
            print("  Please enter a number.")


def handle_no_matches(
    local_file_name: str,
    all_drive_files: List[Tuple[str, str, str]],
    search_function: Callable
) -> Optional[Tuple[str, str, str]]:
    """
    Handle case when no maybe matches found - offer search or browse.
    """
    print(f"\n  Couldn't find any files that might match '{local_file_name}'.")
    print("  If you know this file exists on your Google Drive:")
    print("  1. Type the exact name as it appears in Google Drive (to search)")
    print("  2. Press 'b' to browse all files")
    print("  3. Press 's' to skip this file")
    
    while True:
        choice = input("  Your choice: ").strip().lower()
        
        if choice == 'b':
            # Browse all files
            return browse_all_files(local_file_name, all_drive_files)
        elif choice == 's':
            # Skip
            print(f"  ✗ Skipped: {local_file_name}")
            return None
        elif choice:
            # User typed a name to search
            selected = search_and_select(choice, all_drive_files, search_function, local_file_name)
            if selected is not None:  # None means try again
                return selected
            # If search didn't result in selection, loop back
        else:
            print("  Please enter 'b' to browse, 's' to skip, or type a file name.")


def search_and_select(
    search_term: str,
    all_drive_files: List[Tuple[str, str, str]],
    search_function: Callable[[str], List[Tuple[str, str, str]]],
    local_file_name: str
) -> Optional[Tuple[str, str, str]]:
    """
    Search for files by name and let user select.
    """
    matching = search_function(search_term, all_drive_files)
    if matching:
        print(f"  Found {len(matching)} file(s) with that name:")
        for match_idx, (file_id, file_name, mime_type) in enumerate(matching, 1):
            print(f"    {match_idx}. {file_name}")
        print(f"    {len(matching) + 1}. Try again")
        
        try:
            sub_choice = int(input("  Select (or enter number to try again): ").strip())
            if 1 <= sub_choice <= len(matching):
                file_id, file_name, mime_type = matching[sub_choice - 1]
                print(f"  ✓ Selected: {file_name}")
                return (file_id, file_name, mime_type)
            elif sub_choice == len(matching) + 1:
                # Try again - return None to loop back
                print(f"  Searching again for '{local_file_name}'...")
                return None
        except ValueError:
            print("  Invalid input. Please enter a number.")
    else:
        print("  No files found with that name. Try again or browse all files.")
    
    return None


def browse_all_files(
    local_file_name: str,
    all_files: List[Tuple[str, str, str]]
) -> Optional[Tuple[str, str, str]]:
    """
    Show paginated file selection menu.
    
    Args:
        local_file_name: Name of the file being matched
        all_files: List of all Drive files as (file_id, file_name, mime_type)
    
    Returns:
        Selected (file_id, file_name, mime_type) if selected, None if skipped
    """
    page_size = 20
    page = 0
    
    while True:
        start = page * page_size
        end = start + page_size
        page_files = all_files[start:end]
        
        print(f"\nAll files in Google Drive (page {page + 1}, showing {len(page_files)} files):")
        for idx, (file_id, file_name, mime_type) in enumerate(page_files, 1):
            print(f"  {idx}. {file_name}")
        
        if end < len(all_files):
            print(f"  {len(page_files) + 1}. Next page")
            print(f"  {len(page_files) + 2}. Skip this file")
        else:
            print(f"  {len(page_files) + 1}. Skip this file")
        
        try:
            choice = input(f"Select file number: ").strip()
            choice_num = int(choice)
            
            if choice_num <= len(page_files):
                file_id, file_name, mime_type = page_files[choice_num - 1]
                print(f"  ✓ Selected: {file_name}")
                return (file_id, file_name, mime_type)
            elif choice_num == len(page_files) + 1 and end < len(all_files):
                page += 1
                continue
            else:
                return None  # Skipped
        except (ValueError, IndexError):
            print("  Invalid selection")
            return None

