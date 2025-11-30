"""
Tests for ranked_projects.py view_ranked_projects function.
"""
import pytest
import json
from unittest.mock import patch
from src.db import connect, init_schema, get_or_create_user, save_project_summary
from src.menu.ranked_projects import view_ranked_projects


def _summary_dict(**kwargs):
    """Helper to create ProjectSummary dict."""
    return {
        "project_name": kwargs.get("project_name", "Test"),
        "project_type": kwargs.get("project_type", "code"),
        "project_mode": kwargs.get("project_mode", "individual"),
        "languages": kwargs.get("languages", []),
        "frameworks": kwargs.get("frameworks", []),
        "metrics": kwargs.get("metrics", {}),
        "contributions": kwargs.get("contributions", {}),
        "created_at": "2024-01-01T00:00:00+00:00"
    }


@pytest.fixture
def setup_user():
    """Create test user."""
    conn = connect()
    init_schema(conn)
    user_id = get_or_create_user(conn, "testuser")
    yield conn, user_id
    conn.close()


def test_no_projects(setup_user):
    """Test when user has no projects."""
    conn, user_id = setup_user
    with patch("builtins.print") as mock_print:
        view_ranked_projects(conn, user_id, "testuser")
        output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "No projects found" in output


def test_single_project(setup_user):
    """Test displaying single project."""
    conn, user_id = setup_user
    summary = _summary_dict(project_name="TestProj", metrics={"skills_detailed": [{"score": 0.8}], "activity_type": {"writing": 1}})
    save_project_summary(conn, user_id, "TestProj", json.dumps(summary))
    with patch("builtins.print") as mock_print:
        view_ranked_projects(conn, user_id, "testuser")
        output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "TestProj" in output
        assert "testuser" in output
        assert "Rank" in output


def test_multiple_projects_sorted(setup_user):
    """Test multiple projects displayed in sorted order."""
    conn, user_id = setup_user
    high = _summary_dict(project_name="High", metrics={"skills_detailed": [{"score": 0.9}], "activity_type": {"writing": 1}, "complexity": {"summary": {"total_files": 30, "total_lines": 5000, "total_functions": 50, "avg_complexity": 5, "maintainability_index": 90}}})
    low = _summary_dict(project_name="Low", metrics={"skills_detailed": [{"score": 0.3}], "activity_type": {"writing": 1}})
    save_project_summary(conn, user_id, "High", json.dumps(high))
    save_project_summary(conn, user_id, "Low", json.dumps(low))
    with patch("builtins.print") as mock_print:
        view_ranked_projects(conn, user_id, "testuser")
        output = " ".join(str(call) for call in mock_print.call_args_list)
        high_idx = output.find("High")
        low_idx = output.find("Low")
        assert high_idx < low_idx


def test_long_name_truncated(setup_user):
    """Test long project names are truncated."""
    conn, user_id = setup_user
    summary = _summary_dict(project_name="A" * 60, metrics={"skills_detailed": [{"score": 0.8}]})
    save_project_summary(conn, user_id, "A" * 60, json.dumps(summary))
    with patch("builtins.print") as mock_print:
        view_ranked_projects(conn, user_id, "testuser")
        output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "..." in output


def test_exception_handling(setup_user):
    """Test exception handling."""
    conn, user_id = setup_user
    with patch("src.menu.ranked_projects.collect_project_data", side_effect=Exception("Test error")):
        with patch("builtins.print") as mock_print:
            view_ranked_projects(conn, user_id, "testuser")
            output = " ".join(str(call) for call in mock_print.call_args_list)
            assert "Error ranking projects" in output
