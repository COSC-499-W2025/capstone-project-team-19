"""
High-level Google Drive setup for text collaboration projects.

Orchestrates the complete flow of:
1. Checking for text files in the project
2. Prompting user for Google Drive connection
3. Authenticating with Google Drive
4. Linking files between ZIP and Google Drive
5. Storing mappings in the database
"""
from typing import Dict, Any, Optional
from src.utils.helpers import _fetch_files
from .google_drive_oauth import get_user_email, google_drive_oauth
from .link_files import find_and_link_files
try:
    from src import constants
except ModuleNotFoundError:
    import constants

def setup_text_project_drive_connection(
    conn,
    user_id: int,
    project_name: str
) -> Dict[str, Any]:
    """
    High-level function to set up Google Drive connection for a text project.
    """
    if constants.VERBOSE:
        print(f"\n[COLLABORATIVE TEXT] Setting up Google Drive connection for '{project_name}'")
    
    # Step 1: Fetch text files from ZIP for this project
    zip_text_files = _fetch_files(conn, user_id, project_name, only_text=True)
    
    if not zip_text_files:
        print(f"No text files found for project '{project_name}'. Skipping Drive connection.")
        return {
            'success': False,
            'files_linked': 0,
            'files_not_found': 0,
            'zip_file_names': [],
            'error': 'No text files found'
        }
    
    # Extract just the file names
    zip_file_names = [f['file_name'] for f in zip_text_files]
    print(f"Found {len(zip_file_names)} text file(s) in project:")
    for file_info in zip_text_files:
        print(f"  • {file_info['file_name']}")
    
    # Step 2: Prompt user to connect Google Drive
    if constants.VERBOSE:
        print(f"\nFound collaborative Text project '{project_name}'.")
        print("Google Drive connection is required for contribution analysis on collaborative text projects.")
    response = input("\nConnect Google Drive now? (y/n): ").strip().lower()
    
    if response not in {'y', 'yes'}:
        print("Skipping Google Drive connection. Contribution analysis will not be available for this project.")
        return {
            'success': False,
            'files_linked': 0,
            'files_not_found': 0,
            'zip_file_names': zip_file_names,
            'error': 'User declined connection'
        }
    
    # Step 3: Run OAuth flow (fresh each time)
    try:
        creds, drive_service, docs_service = google_drive_oauth()
        if not drive_service or not docs_service:
            print("Failed to connect Google Drive. Skipping file linking.")
            return {
                'success': False,
                'files_linked': 0,
                'files_not_found': len(zip_file_names),
                'zip_file_names': zip_file_names,
                'error': 'OAuth authentication failed'
            }
    except Exception as e:
        print(f"Error connecting to Google Drive: {e}")
        print("Skipping file linking.")
        return {
            'success': False,
            'files_linked': 0,
            'files_not_found': len(zip_file_names),
            'zip_file_names': zip_file_names,
            'error': str(e)
        }
    user_email = get_user_email(creds)
    
    # Step 4: Link files
    if constants.VERBOSE:
        print(f"\nLinking files from '{project_name}' with Google Drive...")
    
    try:
        results = find_and_link_files(drive_service, project_name, zip_file_names, conn, user_id)
        
        # Extract results
        total_found = len(results.get('manual', []))
        total_not_found = len(results.get('not_found', []))
        
        # Step 5: Display summary
        if total_found > 0:
            if constants.VERBOSE:
                print(f"\n✓ Successfully linked {total_found} file(s) to Google Drive.")
        
        if total_not_found > 0:
            if constants.VERBOSE:
                print(f"✗ Could not link {total_not_found} file(s). These files will not be included in contribution analysis.")
        
        print(f"\nGoogle Drive setup complete for '{project_name}'. File mappings have been saved.")
        
        return {
            'success': True,
            'files_linked': total_found,
            'files_not_found': total_not_found,
            'zip_file_names': zip_file_names,
            'creds': creds,
            'drive_service': drive_service,
            'docs_service': docs_service,
            'user_email': user_email,
            'error': None
        }
        
    except Exception as e:
        print(f"Error linking files: {e}")
        print("Skipping file linking for this project.")
        return {
            'success': False,
            'files_linked': 0,
            'files_not_found': len(zip_file_names),
            'zip_file_names': zip_file_names,
            'error': str(e)
        }

