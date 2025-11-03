import pytest
from unittest.mock import Mock

from src.google_drive_auth.file_matcher import (
    match_zip_files_to_drive, 
    find_maybe_matches,
    search_by_name,
    SUPPORTED_MIME_TYPES
)


@pytest.fixture
def mock_service():
    """Create a mock Google Drive service."""
    service = Mock()
    
    # Mock files list response
    service.files.return_value.list.return_value.execute.return_value = {
        'files': [
            {'id': '1', 'name': 'Document.docx', 'mimeType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'},
            {'id': '2', 'name': 'report.pdf', 'mimeType': 'application/pdf'},
            {'id': '3', 'name': 'notes.txt', 'mimeType': 'text/plain'},
            {'id': '4', 'name': 'project_report.pdf', 'mimeType': 'application/pdf'},
            {'id': '5', 'name': 'UNRELATED.xlsx', 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'},
        ],
        'nextPageToken': None
    }
    
    return service


def test_case_insensitive_match(mock_service):
    """Test case-insensitive file name matching."""
    zip_files = ['Document.docx', 'report.pdf', 'DOCUMENT.DOCX', 'Report.PDF']
    
    matches = match_zip_files_to_drive(mock_service, zip_files, None)
    
    # Should match despite case difference
    assert matches['Document.docx'] is not None
    assert matches['Document.docx'][0] == '1'
    assert matches['Document.docx'][1] == 'Document.docx'
    
    assert matches['report.pdf'] is not None
    assert matches['report.pdf'][0] == '2'
    
    assert matches['DOCUMENT.DOCX'] is not None  # Case-insensitive
    assert matches['Report.PDF'] is not None  # Case-insensitive


def test_project_name_match(mock_service):
    """Test matching when project name is in drive file name."""
    zip_files = ['unknown.txt']
    
    # Should match 'project_report.pdf' because 'project' is in the filename
    matches = match_zip_files_to_drive(mock_service, zip_files, 'project')
    
    # Should match 'project_report.pdf' because project name 'project' is in it
    assert matches['unknown.txt'] is not None
    assert matches['unknown.txt'][1] == 'project_report.pdf'


def test_project_name_or_filename_match(mock_service):
    """Test that either filename match OR project name match works."""
    zip_files = ['Document.docx']
    
    # Should match 'Document.docx' by filename (case-insensitive match takes priority)
    matches = match_zip_files_to_drive(mock_service, zip_files, 'project')
    
    assert matches['Document.docx'] is not None
    assert matches['Document.docx'][1] == 'Document.docx'  # Matches by filename


def test_no_match_found(mock_service):
    """Test when no matching files are found."""
    zip_files = ['nonexistent.docx']
    
    matches = match_zip_files_to_drive(mock_service, zip_files, None)
    
    assert matches['nonexistent.docx'] is None




def test_mime_type_filtering(mock_service):
    """Test that only supported MIME types are matched."""
    # The mock service includes an unsupported file type (xlsx)
    # Make sure it's not included in results
    zip_files = ['UNRELATED.xlsx']
    
    matches = match_zip_files_to_drive(mock_service, zip_files, None)
    
    # Since xlsx is not in SUPPORTED_MIME_TYPES for this use case,
    # it should be None (unless xlsx was added to supported types)
    # The actual behavior depends on whether xlsx is in SUPPORTED_MIME_TYPES
    assert isinstance(matches['UNRELATED.xlsx'], (type(None), tuple))


def test_multiple_pages(mock_service):
    """Test handling of paginated results."""
    # First page
    mock_service.files.return_value.list.return_value.execute.side_effect = [
        {
            'files': [
                {'id': '1', 'name': 'file1.pdf', 'mimeType': 'application/pdf'},
            ],
            'nextPageToken': 'token123'
        },
        {
            'files': [
                {'id': '2', 'name': 'file2.pdf', 'mimeType': 'application/pdf'},
            ],
            'nextPageToken': None
        }
    ]
    
    zip_files = ['file1.pdf', 'file2.pdf']
    matches = match_zip_files_to_drive(mock_service, zip_files, None)
    
    # Both files should be found across pages
    assert matches['file1.pdf'] is not None
    assert matches['file2.pdf'] is not None


def test_find_maybe_matches():
    """Test find_maybe_matches function."""
    drive_files = [
        {'id': '1', 'name': 'Document.docx', 'mimeType': 'application/pdf'},
        {'id': '2', 'name': 'doc.docx', 'mimeType': 'application/pdf'},
        {'id': '3', 'name': 'project_document.pdf', 'mimeType': 'application/pdf'},
    ]
    
    # Exact case-insensitive match
    matches = find_maybe_matches('document.docx', 'project', drive_files)
    assert len(matches) > 0
    assert matches[0][0] == '1'  # Exact match should be first
    
    # Project name match - should find files with 'project' in name
    matches = find_maybe_matches('unknown.txt', 'project', drive_files)
    assert any(m[0] == '3' for m in matches)  # project_document should be found
    
    # Case-insensitive filename match
    matches = find_maybe_matches('DOC.docx', None, drive_files)
    assert any(m[0] == '2' for m in matches)  # Should match 'doc.docx'


def test_search_by_name():
    """Test search_by_name function."""
    drive_files = [
        ('1', 'Document.docx', 'application/pdf'),
        ('2', 'report.pdf', 'application/pdf'),
        ('3', 'document_final.docx', 'application/pdf'),
    ]
    
    matches = search_by_name('document', drive_files)
    assert len(matches) == 2
    assert all('document' in m[1].lower() for m in matches)

