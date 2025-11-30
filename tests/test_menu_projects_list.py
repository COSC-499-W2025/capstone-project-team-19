import pytest
import json
from unittest.mock import patch
from datetime import datetime
from src.menu.projects_list import project_list
from src.db import (
    connect,
    init_schema,
    get_or_create_user,
    record_project_classification,
    save_project_summary,
)
from src.db.text_activity import store_text_activity_contribution

#Helper functions and fixtures

@pytest.fixture
def setup_user():
    """Create a test user and return connection and user_id."""
    conn = connect()
    init_schema(conn)
    user_id = get_or_create_user(conn, "testuser")
    yield conn, user_id, "testuser"
    conn.close()

def create_text_project_with_date(conn, user_id, project_name, end_date):
    """Helper to create a text project with completion date."""
    record_project_classification(conn, user_id, f"/path/{project_name}.zip", project_name.lower(), project_name, "individual")
    conn.execute("UPDATE project_classifications SET project_type = 'text' WHERE project_name = ?", (project_name,))
    summary = {"project_type": "text", "project_mode": "individual"}
    save_project_summary(conn, user_id, project_name, json.dumps(summary))
    classification_id = conn.execute(
        "SELECT classification_id FROM project_classifications WHERE project_name = ?", (project_name,)
    ).fetchone()[0]
    store_text_activity_contribution(conn, classification_id, {
        "timestamp_analysis": {
            "end_date": end_date,
        }
    })

def create_code_project_with_date(conn, user_id, project_name, last_commit_date, is_collaborative=False):
    """Helper to create a code project with completion date."""
    mode = "collaborative" if is_collaborative else "individual"
    record_project_classification(conn, user_id, f"/path/{project_name}.zip", project_name.lower(), project_name, mode)
    conn.execute("UPDATE project_classifications SET project_type = 'code' WHERE project_name = ?", (project_name,))
    
    # Create summary with git commit stats in JSON
    if is_collaborative:
        summary = {
            "project_type": "code",
            "project_mode": "collaborative",
            "metrics": {
                "collaborative_git": {
                    "last_commit_date": last_commit_date
                }
            }
        }
    else:
        summary = {
            "project_type": "code",
            "project_mode": "individual",
            "metrics": {
                "git": {
                    "commit_stats": {
                        "last_commit_date": last_commit_date
                    }
                }
            }
        }
    
    save_project_summary(conn, user_id, project_name, json.dumps(summary))

# Tests

def test_no_projects_found(setup_user):
    """Test displaying message when user has no projects."""
    conn, user_id, username = setup_user

    with patch("builtins.input", return_value=""):
        with patch("builtins.print") as mock_print:
            result = project_list(conn, user_id, username)

            assert result is None
            print_calls = [str(call) for call in mock_print.call_args_list]
            combined_output = " ".join(print_calls)

            assert "No projects found" in combined_output
            assert "testuser" in combined_output


def test_displays_text_projects_with_dates(setup_user):
    """Test that text projects are displayed with formatted dates."""
    conn, user_id, username = setup_user
    create_text_project_with_date(conn, user_id, "TestProject", datetime(2024, 12, 10))

    with patch("builtins.input", return_value=""):
        with patch("builtins.print") as mock_print:
            result = project_list(conn, user_id, username)

            assert result is None
            print_calls = [str(call) for call in mock_print.call_args_list]
            combined_output = " ".join(print_calls)

            assert "TestProject" in combined_output
            assert "Dec 10 2024" in combined_output or "2024-12-10" in combined_output
            assert "-" in combined_output

def test_displays_code_project_with_date(setup_user):
    """Test that code projects are displayed with formatted dates."""
    conn, user_id, username = setup_user
    create_code_project_with_date(conn, user_id, "CodeProject", "2024-12-15", is_collaborative=False)

    with patch("builtins.input", return_value=""):
        with patch("builtins.print") as mock_print:
            result = project_list(conn, user_id, username)

            assert result is None
            print_calls = [str(call) for call in mock_print.call_args_list]
            combined_output = " ".join(print_calls)

            assert "CodeProject" in combined_output
            assert "Dec 15 2024" in combined_output or "2024-12-15" in combined_output
            assert "-" in combined_output


def test_mixed_text_and_code_projects(setup_user):
    """Test that text and code projects are ordered together by completion date."""
    conn, user_id, username = setup_user
    # Create projects with different dates
    create_text_project_with_date(conn, user_id, "OldTextProject", datetime(2024, 1, 10))
    create_code_project_with_date(conn, user_id, "NewCodeProject", "2024-12-20", is_collaborative=False)
    create_text_project_with_date(conn, user_id, "MidTextProject", datetime(2024, 6, 15))

    with patch("builtins.input", return_value=""):
        with patch("builtins.print") as mock_print:
            result = project_list(conn, user_id, username)

            assert result is None
            print_calls = [str(call) for call in mock_print.call_args_list]
            combined_output = " ".join(print_calls)

            # Check order: newest first
            new_index = combined_output.find("NewCodeProject")
            mid_index = combined_output.find("MidTextProject")
            old_index = combined_output.find("OldTextProject")
            assert new_index < mid_index < old_index


def test_handles_projects_without_dates(setup_user):
    """Test that projects without dates display 'Date unknown'."""
    conn, user_id, username = setup_user
    
    record_project_classification(conn, user_id, "/path/test.zip", "test", "NoDateProject", "individual")
    conn.execute("UPDATE project_classifications SET project_type = 'code' WHERE project_name = 'NoDateProject'")
    summary = {"project_type": "code", "project_mode": "individual"}
    save_project_summary(conn, user_id, "NoDateProject", json.dumps(summary))

    with patch("builtins.input", return_value=""):
        with patch("builtins.print") as mock_print:
            result = project_list(conn, user_id, username)

            assert result is None
            print_calls = [str(call) for call in mock_print.call_args_list]
            combined_output = " ".join(print_calls)

            assert "NoDateProject" in combined_output
            assert "Date unknown" in combined_output