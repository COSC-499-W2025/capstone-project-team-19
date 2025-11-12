import pytest
import sqlite3
from unittest.mock import Mock, patch, MagicMock

from src.db import init_schema, get_or_create_user, store_file_link
from src.integrations.google_drive.google_drive_auth.link_files import find_and_link_files


@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    return conn


@pytest.fixture
def mock_service():
    """Create mock Google Drive service."""
    service = Mock()
    
    # Mock the files().list() chain correctly
    mock_list_result = Mock()
    mock_list_result.execute.return_value = {
        'files': [
            {'id': '1', 'name': 'Document.docx', 'mimeType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'},
            {'id': '2', 'name': 'report.pdf', 'mimeType': 'application/pdf'},
        ],
        'nextPageToken': None
    }
    
    mock_files = Mock()
    mock_files.list.return_value = mock_list_result
    service.files.return_value = mock_files
    return service


def test_find_and_link_files_successful_matching(monkeypatch, conn, mock_service):
    """Test successful file matching with user selection."""
    user_id = get_or_create_user(conn, "TestUser")
    
    # Mock file_selector functions to simulate user selecting matches
    def mock_select_from_matches(local_name, matches, all_files, search_func):
        return matches[0] if matches else None
    
    def mock_handle_no_matches(local_name, all_files, search_func):
        return None
    
    monkeypatch.setattr(
        "src.google_drive_auth.link_files.select_from_matches",
        mock_select_from_matches
    )
    monkeypatch.setattr(
        "src.google_drive_auth.link_files.handle_no_matches",
        mock_handle_no_matches
    )
    
    results = find_and_link_files(
        mock_service, "TestProject", 
        ["Document.docx", "report.pdf"], 
        conn, user_id
    )
    
    assert len(results['manual']) == 2
    assert "Document.docx" in results['manual']
    assert "report.pdf" in results['manual']
    
    # Verify database - should have exactly 2 entries
    rows = conn.execute("""
        SELECT local_file_name FROM project_drive_files
        WHERE user_id=? AND project_name=?
    """, (user_id, "TestProject")).fetchall()
    assert len(rows) == 2


def test_find_and_link_files_partial_matching(monkeypatch, conn, mock_service):
    """Test partial matching with some files found and some skipped."""
    user_id = get_or_create_user(conn, "TestUser")
    
    # Mock select_from_matches - return match for first, None for second
    call_count = [0]
    def mock_select_from_matches(local_name, matches, all_files, search_func):
        call_count[0] += 1
        if call_count[0] == 1:
            return matches[0] if matches else None
        else:
            return None
    
    def mock_handle_no_matches(local_name, all_files, search_func):
        return None
    
    monkeypatch.setattr(
        "src.google_drive_auth.link_files.select_from_matches",
        mock_select_from_matches
    )
    monkeypatch.setattr(
        "src.google_drive_auth.link_files.handle_no_matches",
        mock_handle_no_matches
    )
    
    results = find_and_link_files(
        mock_service, "TestProject", 
        ["Document.docx", "missing.pdf"], 
        conn, user_id
    )
    
    assert "Document.docx" in results['manual']
    assert "missing.pdf" in results['not_found']
    
    # Verify database - should have exactly 2 entries (one linked, one not_found)
    rows = conn.execute("""
        SELECT local_file_name, status FROM project_drive_files
        WHERE user_id=? AND project_name=?
    """, (user_id, "TestProject")).fetchall()
    assert len(rows) == 2
    statuses = {row[1] for row in rows}
    assert 'manual_selected' in statuses
    assert 'not_found' in statuses


def test_no_duplicate_storage(monkeypatch, conn, mock_service):
    """Test that files are not stored multiple times."""
    user_id = get_or_create_user(conn, "TestUser")
    
    def mock_select_from_matches(local_name, matches, all_files, search_func):
        return matches[0] if matches else None
    
    def mock_handle_no_matches(local_name, all_files, search_func):
        return None
    
    monkeypatch.setattr(
        "src.google_drive_auth.link_files.select_from_matches",
        mock_select_from_matches
    )
    monkeypatch.setattr(
        "src.google_drive_auth.link_files.handle_no_matches",
        mock_handle_no_matches
    )
    
    # Call twice with same files
    find_and_link_files(mock_service, "TestProject", ["Document.docx"], conn, user_id)
    find_and_link_files(mock_service, "TestProject", ["Document.docx"], conn, user_id)
    
    # Should still have only 1 entry (old one deleted, new one inserted)
    rows = conn.execute("""
        SELECT local_file_name FROM project_drive_files
        WHERE user_id=? AND project_name=? AND local_file_name=?
    """, (user_id, "TestProject", "Document.docx")).fetchall()
    assert len(rows) == 1


def test_store_file_link(conn):
    """Test storing file links in database."""
    user_id = get_or_create_user(conn, "TestUser")
    
    store_file_link(
        conn, user_id, "TestProject", "file1.docx",
        "drive_id_123", "File1.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "auto_matched"
    )
    
    # Verify it was stored
    rows = conn.execute("""
        SELECT local_file_name, drive_file_id, status
        FROM project_drive_files
        WHERE user_id=? AND project_name=?
    """, (user_id, "TestProject")).fetchall()
    
    assert len(rows) == 1
    assert rows[0][0] == "file1.docx"
    assert rows[0][1] == "drive_id_123"
    assert rows[0][2] == "auto_matched"


def test_store_file_link_not_found_status(conn):
    """Test storing files with not_found status."""
    user_id = get_or_create_user(conn, "TestUser")
    
    store_file_link(
        conn, user_id, "TestProject", "missing.docx",
        "NOT_FOUND", None, None, "not_found"
    )
    
    rows = conn.execute("""
        SELECT status FROM project_drive_files
        WHERE user_id=? AND project_name=? AND local_file_name=?
    """, (user_id, "TestProject", "missing.docx")).fetchall()
    
    assert len(rows) == 1
    assert rows[0][0] == "not_found"
