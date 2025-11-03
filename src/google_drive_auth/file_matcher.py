"""
File matching module for finding ZIP files in Google Drive.

Implements matching strategies to automatically link files from the uploaded ZIP
with files in the user's Google Drive based on name similarity.
"""
from typing import Optional, Dict, List, Tuple
try:
    from googleapiclient.discovery import Resource
except ImportError:
    # For testing without googleapiclient installed
    Resource = type(None)

# Supported MIME types for text files
SUPPORTED_MIME_TYPES = [
    'application/vnd.google-apps.document',  # Google Docs
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # DOCX
    'application/msword',  # DOC
    'text/plain',  # Plain text
    'application/vnd.google-apps.spreadsheet'  # Google Sheets (may contain text)
]


def match_zip_files_to_drive(
    service: Resource,
    zip_files: List[str],
    project_name: Optional[str] = None
) -> Dict[str, Optional[Tuple[str, str, str]]]:
    """
    Match ZIP file names to Google Drive files using case-insensitive name match OR project name in drive file name.
    """
    # Get all supported files from Drive
    drive_files = _list_supported_drive_files(service)
    
    matches = {}
    project_lower = project_name.lower() if project_name else None
    
    for local_file_name in zip_files:
        local_lower = local_file_name.lower()
        match = None
        
        for drive_file in drive_files:
            drive_name_lower = drive_file['name'].lower()
            
            # Check: case-insensitive name match OR project name in drive file name
            if local_lower == drive_name_lower or (project_lower and project_lower in drive_name_lower):
                match = (drive_file['id'], drive_file['name'], drive_file['mimeType'])
                break
        
        matches[local_file_name] = match
    
    return matches


def _list_supported_drive_files(service: Resource) -> List[Dict]:
    """
    List all supported files from Google Drive.
    """
    files = []
    page_token = None
    
    while True:
        try:
            results = service.files().list(
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token,
                q="trashed=false"  # Exclude trashed files
            ).execute()
            
            items = results.get('files', [])
            
            # Filter by supported MIME types
            supported = [
                {'id': item['id'], 'name': item['name'], 'mimeType': item.get('mimeType', '')}
                for item in items
                if item.get('mimeType', '') in SUPPORTED_MIME_TYPES
            ]
            
            files.extend(supported)
            
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        except Exception as e:
            print(f"Error listing Drive files: {e}")
            break
    
    return files


def find_maybe_matches(local_file_name: str,project_name: Optional[str],drive_files: List[Dict]) -> List[Tuple[str, str, str]]:
    """
    Find potential matches for a single file.
    Looks for:
    - Case-insensitive exact name matches
    - Files containing the project name in their name
    """
    maybe_matches = []
    local_lower = local_file_name.lower()
    project_lower = project_name.lower() if project_name else None
    
    for drive_file in drive_files:
        drive_name = drive_file['name']
        drive_lower = drive_name.lower()
        file_id = drive_file['id']
        mime_type = drive_file['mimeType']
        
        # Check case-insensitive exact match OR project name in drive file name
        if local_lower == drive_lower or (project_lower and project_lower in drive_lower):
            maybe_matches.append((file_id, drive_name, mime_type))
    
    # Remove duplicates (by file_id) and sort by relevance
    seen = set()
    unique_matches = []
    for match in maybe_matches:
        if match[0] not in seen:
            seen.add(match[0])
            unique_matches.append(match)
    
    # Sort: exact matches first, then by name similarity
    unique_matches.sort(key=lambda x: (
        x[1].lower() != local_file_name.lower(),  # Exact matches first
        abs(len(x[1]) - len(local_file_name))  # Then by length similarity
    ))
    
    return unique_matches


def search_by_name(search_term: str, drive_files: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
    """
    Search Drive files by name (case-insensitive partial match).

    Returns:
        List of matching (file_id, file_name, mime_type) tuples
    """
    search_lower = search_term.lower()
    matches = []
    
    for file_id, file_name, mime_type in drive_files:
        if search_lower in file_name.lower():
            matches.append((file_id, file_name, mime_type))
    
    return matches

