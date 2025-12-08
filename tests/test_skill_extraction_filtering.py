"""
Tests for collaborative project file filtering in skill extraction.

Tests that skill extraction correctly filters files based on user contributions
for collaborative projects, while using all files for individual projects.
"""

import pytest
import sqlite3
from unittest.mock import patch, Mock
from src.analysis.skills.flows.skill_extraction import extract_skills
from src.db import init_schema
from src.db.file_contributions import store_file_contributions
from src import constants

@pytest.fixture
def test_conn():
    """Create an in-memory database with schema for testing."""
    conn = sqlite3.connect(":memory:")
    init_schema(conn)

    # Insert a test user
    conn.execute("INSERT INTO users (user_id, username) VALUES (1, 'testuser')")
    conn.commit()

    yield conn
    conn.close()


def test_individual_project_no_filtering(test_conn):
    """Test that individual projects analyze all files without filtering."""
    # Setup project classification as individual
    test_conn.execute("""
        INSERT INTO project_classifications (user_id, zip_path, zip_name, project_name, classification, project_type, recorded_at)
        VALUES (1, '/tmp/test.zip', 'test', 'myproject', 'individual', 'code', datetime('now'))
    """)
    test_conn.commit()

    # Mock _fetch_files to return 5 files
    mock_files = [
        {"file_name": "file1.py", "file_path": "file1.py"},
        {"file_name": "file2.py", "file_path": "file2.py"},
        {"file_name": "file3.py", "file_path": "file3.py"},
        {"file_name": "file4.py", "file_path": "file4.py"},
        {"file_name": "file5.py", "file_path": "file5.py"},
    ]

    with patch("src.analysis.skills.flows.skill_extraction._fetch_files", return_value=mock_files), \
         patch("src.analysis.skills.flows.skill_extraction.extract_code_skills") as mock_extract:

        extract_skills(test_conn, user_id=1, project_name="myproject")

        # Should be called with all 5 files (no filtering)
        mock_extract.assert_called_once()
        args, kwargs = mock_extract.call_args
        assert len(args[4]) == 5  # 5th argument is files list


def test_collaborative_project_with_filtering(test_conn):
    """Test that collaborative projects filter files based on contributions."""
    # Setup project classification as collaborative
    test_conn.execute("""
        INSERT INTO project_classifications (user_id, zip_path, zip_name, project_name, classification, project_type, recorded_at)
        VALUES (1, '/tmp/test.zip', 'test', 'teamproject', 'collaborative', 'code', datetime('now'))
    """)
    test_conn.commit()

    # Store file contributions - user only worked on 2 of 5 files
    contributions = {
        "file1.py": {"lines_changed": 100, "commits_count": 3},
        "file3.py": {"lines_changed": 50, "commits_count": 1},
    }
    store_file_contributions(test_conn, user_id=1, project_name="teamproject", file_contributions=contributions)

    # Mock _fetch_files to return 5 files
    mock_files = [
        {"file_name": "file1.py", "file_path": "file1.py"},
        {"file_name": "file2.py", "file_path": "file2.py"},
        {"file_name": "file3.py", "file_path": "file3.py"},
        {"file_name": "file4.py", "file_path": "file4.py"},
        {"file_name": "file5.py", "file_path": "file5.py"},
    ]

    with patch("src.analysis.skills.flows.skill_extraction._fetch_files", return_value=mock_files), \
         patch("src.analysis.skills.flows.skill_extraction.extract_code_skills") as mock_extract:

        extract_skills(test_conn, user_id=1, project_name="teamproject")

        # Should be called with only 2 files (filtered)
        mock_extract.assert_called_once()
        args, kwargs = mock_extract.call_args
        filtered_files = args[4]

        assert len(filtered_files) == 2
        assert any(f["file_name"] == "file1.py" for f in filtered_files)
        assert any(f["file_name"] == "file3.py" for f in filtered_files)


def test_collaborative_project_no_contribution_data(test_conn):
    """Test collaborative project when contribution data doesn't exist - uses all files."""
    # Setup project classification as collaborative
    test_conn.execute("""
        INSERT INTO project_classifications (user_id, zip_path, zip_name, project_name, classification, project_type, recorded_at)
        VALUES (1, '/tmp/test.zip', 'test', 'teamproject', 'collaborative', 'code', datetime('now'))
    """)
    test_conn.commit()

    # No contribution data stored - simulates old projects before this feature

    mock_files = [
        {"file_name": "file1.py", "file_path": "file1.py"},
        {"file_name": "file2.py", "file_path": "file2.py"},
    ]

    with patch("src.analysis.skills.flows.skill_extraction._fetch_files", return_value=mock_files), \
         patch("src.analysis.skills.flows.skill_extraction.extract_code_skills") as mock_extract:

        extract_skills(test_conn, user_id=1, project_name="teamproject")

        # Should use all files (no filtering when contribution data missing)
        mock_extract.assert_called_once()
        args, kwargs = mock_extract.call_args
        assert len(args[4]) == 2


def test_collaborative_project_path_matching_verbose_on(test_conn, capsys):
    """Test that file path matching works correctly with different path formats."""
    # Setup project classification as collaborative
    test_conn.execute("""
        INSERT INTO project_classifications (user_id, zip_path, zip_name, project_name, classification, project_type, recorded_at)
        VALUES (1, '/tmp/test.zip', 'test', 'proj', 'collaborative', 'code', datetime('now'))
    """)
    test_conn.commit()

    # Store contributions with relative path
    contributions = {
        "src/main.py": {"lines_changed": 100, "commits_count": 3},
    }
    store_file_contributions(test_conn, 1, "proj", contributions)

    # Mock files with different path format (includes project prefix)
    mock_files = [
        {"file_name": "main.py", "file_path": "test-proj/src/main.py"},
        {"file_name": "utils.py", "file_path": "test-proj/src/utils.py"},
    ]

    # turn on verbose for this test only
    constants.VERBOSE = True

    with patch("src.analysis.skills.flows.skill_extraction._fetch_files", return_value=mock_files), \
         patch("src.analysis.skills.flows.skill_extraction.extract_code_skills") as mock_extract:

        extract_skills(test_conn, 1, "proj")

        # Should match by basename (main.py matches src/main.py)
        mock_extract.assert_called_once()
        args, kwargs = mock_extract.call_args
        filtered_files = args[4]

        assert len(filtered_files) == 1
        assert filtered_files[0]["file_name"] == "main.py"

    # Check console output (only in VERBOSE mode)
    captured = capsys.readouterr()
    assert "Filtered to 1/2 files" in captured.out

def test_collaborative_project_path_matching_non_verbose(test_conn, capsys):
    """Same scenario as path matching, but VERBOSE = False → no debug output."""
    test_conn.execute("""
        INSERT INTO project_classifications (user_id, zip_path, zip_name, project_name, classification, project_type, recorded_at)
        VALUES (1, '/tmp/test.zip', 'test', 'proj2', 'collaborative', 'code', datetime('now'))
    """)
    test_conn.commit()

    contributions = {
        "src/main.py": {"lines_changed": 100, "commits_count": 3},
    }
    store_file_contributions(test_conn, 1, "proj2", contributions)

    mock_files = [
        {"file_name": "main.py", "file_path": "test-proj/src/main.py"},
        {"file_name": "utils.py", "file_path": "test-proj/src/utils.py"},
    ]

    # ensure verbose OFF
    constants.VERBOSE = False

    with patch("src.analysis.skills.flows.skill_extraction._fetch_files", return_value=mock_files), \
         patch("src.analysis.skills.flows.skill_extraction.extract_code_skills") as mock_extract:

        extract_skills(test_conn, 1, "proj2")

        mock_extract.assert_called_once()
        args, kwargs = mock_extract.call_args
        files_used = args[4]
        assert len(files_used) == 1       # filtering still works
        assert files_used[0]["file_name"] == "main.py"

    # ❗ expected: NO debug print
    captured = capsys.readouterr()
    assert "Filtered to" not in captured.out

def test_missing_project_type_skips_extraction(test_conn, capsys):
    """Test that extraction is skipped when project_type is missing."""
    # Insert classification without project_type
    test_conn.execute("""
        INSERT INTO project_classifications (user_id, zip_path, zip_name, project_name, classification, recorded_at)
        VALUES (1, '/tmp/test.zip', 'test', 'incomplete', 'individual', datetime('now'))
    """)
    test_conn.commit()

    with patch("src.analysis.skills.flows.skill_extraction.extract_code_skills") as mock_extract:
        extract_skills(test_conn, 1, "incomplete")

        # Should not call extract_code_skills
        mock_extract.assert_not_called()

    captured = capsys.readouterr()
    assert "missing metadata" in captured.out


def test_no_files_found_skips_extraction(test_conn, capsys):
    """Test that extraction is skipped when no files are found."""
    test_conn.execute("""
        INSERT INTO project_classifications (user_id, zip_path, zip_name, project_name, classification, project_type, recorded_at)
        VALUES (1, '/tmp/test.zip', 'test', 'emptyproject', 'individual', 'code', datetime('now'))
    """)
    test_conn.commit()

    with patch("src.analysis.skills.flows.skill_extraction._fetch_files", return_value=[]), \
         patch("src.analysis.skills.flows.skill_extraction.extract_code_skills") as mock_extract:

        extract_skills(test_conn, 1, "emptyproject")

        # Should not call extract_code_skills
        mock_extract.assert_not_called()

    captured = capsys.readouterr()
    assert "No files found" in captured.out


def test_collaborative_all_files_filtered_out(test_conn, capsys):
    """Test edge case where all files are filtered out (user contributed to no code files)."""
    test_conn.execute("""
        INSERT INTO project_classifications (user_id, zip_path, zip_name, project_name, classification, project_type, recorded_at)
        VALUES (1, '/tmp/test.zip', 'test', 'teamproject', 'collaborative', 'code', datetime('now'))
    """)
    test_conn.commit()

    # User only contributed to docs, not code
    contributions = {
        "README.md": {"lines_changed": 100, "commits_count": 3},
    }
    store_file_contributions(test_conn, 1, "teamproject", contributions)

    # But only code files are in the files list
    mock_files = [
        {"file_name": "main.py", "file_path": "src/main.py"},
        {"file_name": "utils.py", "file_path": "src/utils.py"},
    ]

    with patch("src.analysis.skills.flows.skill_extraction._fetch_files", return_value=mock_files), \
         patch("src.analysis.skills.flows.skill_extraction.extract_code_skills") as mock_extract:

        extract_skills(test_conn, 1, "teamproject")

        # Should not call extract_code_skills (no files left after filtering)
        mock_extract.assert_not_called()

    captured = capsys.readouterr()
    assert "No contributed files found" in captured.out
