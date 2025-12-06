"""
File matching module for finding ZIP files in Google Drive.

Implements matching strategies to automatically link files from the uploaded ZIP
with files in the user's Google Drive based on name similarity.
"""
import os
from typing import Optional, Dict, List, Tuple
try:
    from googleapiclient.discovery import Resource
except ImportError:
    # For testing without googleapiclient installed
    Resource = type(None)
import src.constants as constants

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
    Match ZIP file names to Google Drive files using:
    - Case-insensitive base name match (ignores extensions)
    """
    drive_files = _list_supported_drive_files(service)
    matches = {}
    project_lower = project_name.lower() if project_name else None

    for local_file_name in zip_files:
        local_base = os.path.splitext(local_file_name)[0].lower()
        match = None

        for drive_file in drive_files:
            drive_lower = drive_file['name'].lower()
            drive_base = os.path.splitext(drive_file['name'])[0].lower()

            # Check: case-insensitive base name match OR project name in drive file name
            if local_base == drive_base or (project_lower and project_lower in drive_lower):
                match = (drive_file['id'], drive_file['name'], drive_file['mimeType'])
                break
  
        if match is None:
            print(f"  [NO MATCH] '{local_file_name}'")
        matches[local_file_name] = match

    return matches


def _list_supported_drive_files(service: Resource) -> List[Dict]:
    """
    List supported files from Google Drive with server-side MIME type filtering.
    """
    files = []
    page_token = None
   
    mime_type_conditions = " or ".join([f"mimeType='{mime}'" for mime in SUPPORTED_MIME_TYPES])
    
    # Build query: exclude trashed files AND filter by MIME types
    query = f"trashed=false and ({mime_type_conditions})"
    
    while True:
        try:
            results = service.files().list(
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token,
                q=query
            ).execute()
            
            items = results.get('files', [])
            
            # Convert to our format (no need to filter by MIME type anymore since
            # server already filtered, but we keep this for safety/consistency)
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


def find_maybe_matches(local_file_name: str, project_name: Optional[str], drive_files: List[Dict]) -> List[Tuple[str, str, str]]:
    """
    Find potential matches for a single file.
    Looks for:
    - Case-insensitive base name matches (ignores extensions)
    - Files containing the project name in their name
    """
    maybe_matches = []
    local_base = os.path.splitext(local_file_name)[0].lower()
    project_lower = project_name.lower() if project_name else None
    
    for drive_file in drive_files:
        drive_name = drive_file['name']
        drive_lower = drive_name.lower()
        drive_base = os.path.splitext(drive_name)[0].lower()
        file_id = drive_file['id']
        mime_type = drive_file['mimeType']
        
        # Check case-insensitive base name match OR project name in drive file name
        if local_base == drive_base or (project_lower and project_lower in drive_lower):
            if constants.VERBOSE:
                print(f"  [POTENTIAL MATCH] '{local_file_name}' -> '{drive_name}'")
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
    
    if not unique_matches:
        if constants.VERBOSE:
            print(f"  [NO MATCHES] '{local_file_name}'")
    
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


def _search_supported_files_by_names(service: Resource, name_substrings: List[str], page_size: int = 100) -> List[Dict]:
    """
    Fetch supported files whose names contain any of the given substrings.
    Batches substrings to reduce API calls and avoid full-drive scans.
    """
    all_files: Dict[str, Dict] = {}
    mime_type_conditions = " or ".join([f"mimeType='{mime}'" for mime in SUPPORTED_MIME_TYPES])

    chunk_size = 5
    for i in range(0, len(name_substrings), chunk_size):
        chunk = [s for s in name_substrings[i : i + chunk_size] if s]
        if not chunk:
            continue
        name_parts = []
        for raw in chunk:
            escaped = raw.replace("'", "\\'")
            name_parts.append(f"name contains '{escaped}'")
        query = f"trashed=false and ({mime_type_conditions}) and ({' or '.join(name_parts)})"

        page_token = None
        while True:
            try:
                results = service.files().list(
                    pageSize=page_size,
                    fields="nextPageToken, files(id, name, mimeType)",
                    pageToken=page_token,
                    q=query,
                    corpora="user"
                ).execute()
                items = results.get("files", [])
                for item in items:
                    mime = item.get("mimeType", "")
                    if mime in SUPPORTED_MIME_TYPES:
                        all_files[item["id"]] = {
                            "id": item["id"],
                            "name": item["name"],
                            "mimeType": mime
                        }
                page_token = results.get("nextPageToken")
                if not page_token:
                    break
            except Exception as e:
                print(f"Error searching Drive files: {e}")
                break

    return list(all_files.values())
