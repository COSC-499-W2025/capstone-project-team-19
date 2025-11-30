"""
Tests for ranked_projects.py view_ranked_projects function.
"""
import pytest
import json
from unittest.mock import patch
from src.db import connect, init_schema, get_or_create_user, save_project_summary
from src.menu.ranked_projects import view_ranked_projects, view_top_projects_summaries, view_all_ranked_projects


def _summary_dict(**kwargs):
    """Helper to create ProjectSummary dict."""
    result = {
        "project_name": kwargs.get("project_name", "Test"),
        "project_type": kwargs.get("project_type", "code"),
        "project_mode": kwargs.get("project_mode", "individual"),
        "languages": kwargs.get("languages", []),
        "frameworks": kwargs.get("frameworks", []),
        "metrics": kwargs.get("metrics", {}),
        "contributions": kwargs.get("contributions", {}),
        "created_at": "2024-01-01T00:00:00+00:00"
    }
    # Add summary_text if provided
    if "summary_text" in kwargs:
        result["summary_text"] = kwargs["summary_text"]
    return result


@pytest.fixture
def setup_user():
    """Create test user."""
    conn = connect()
    init_schema(conn)
    user_id = get_or_create_user(conn, "testuser")
    yield conn, user_id
    conn.close()


def test_view_all_ranked_projects_no_projects(setup_user):
    """Test view_all_ranked_projects when user has no projects."""
    conn, user_id = setup_user
    with patch("builtins.print") as mock_print:
        view_all_ranked_projects(conn, user_id, "testuser")
        output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "No projects found" in output


def test_view_all_ranked_projects_single_project(setup_user):
    """Test view_all_ranked_projects displaying single project."""
    conn, user_id = setup_user
    summary = _summary_dict(project_name="TestProj", metrics={"skills_detailed": [{"score": 0.8}], "activity_type": {"writing": 1}})
    save_project_summary(conn, user_id, "TestProj", json.dumps(summary))
    with patch("builtins.print") as mock_print:
        view_all_ranked_projects(conn, user_id, "testuser")
        output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "TestProj" in output
        assert "testuser" in output
        assert "Rank" in output


def test_view_all_ranked_projects_multiple_sorted(setup_user):
    """Test view_all_ranked_projects displays multiple projects in sorted order."""
    conn, user_id = setup_user
    high = _summary_dict(project_name="High", metrics={"skills_detailed": [{"score": 0.9}], "activity_type": {"writing": 1}, "complexity": {"summary": {"total_files": 30, "total_lines": 5000, "total_functions": 50, "avg_complexity": 5, "maintainability_index": 90}}})
    low = _summary_dict(project_name="Low", metrics={"skills_detailed": [{"score": 0.3}], "activity_type": {"writing": 1}})
    save_project_summary(conn, user_id, "High", json.dumps(high))
    save_project_summary(conn, user_id, "Low", json.dumps(low))
    with patch("builtins.print") as mock_print:
        view_all_ranked_projects(conn, user_id, "testuser")
        output = " ".join(str(call) for call in mock_print.call_args_list)
        high_idx = output.find("High")
        low_idx = output.find("Low")
        assert high_idx < low_idx


def test_view_all_ranked_projects_long_name_truncated(setup_user):
    """Test view_all_ranked_projects truncates long project names."""
    conn, user_id = setup_user
    summary = _summary_dict(project_name="A" * 60, metrics={"skills_detailed": [{"score": 0.8}]})
    save_project_summary(conn, user_id, "A" * 60, json.dumps(summary))
    with patch("builtins.print") as mock_print:
        view_all_ranked_projects(conn, user_id, "testuser")
        output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "..." in output


def test_view_all_ranked_projects_exception_handling(setup_user):
    """Test exception handling in view_all_ranked_projects."""
    conn, user_id = setup_user
    with patch("src.menu.ranked_projects.collect_project_data", side_effect=Exception("Test error")):
        with patch("builtins.print") as mock_print:
            view_all_ranked_projects(conn, user_id, "testuser")
            output = " ".join(str(call) for call in mock_print.call_args_list)
            assert "Error ranking projects" in output


def test_view_ranked_projects_menu_option_1(setup_user):
    """Test that option 1 calls view_all_ranked_projects."""
    conn, user_id = setup_user
    summary = _summary_dict(project_name="TestProj", metrics={"skills_detailed": [{"score": 0.8}], "activity_type": {"writing": 1}})
    save_project_summary(conn, user_id, "TestProj", json.dumps(summary))
    
    # First input selects option 1, second input selects option 3 to exit
    with patch("builtins.input", side_effect=["1", "3"]):
        with patch("builtins.print") as mock_print:
            result = view_ranked_projects(conn, user_id, "testuser")
            assert result is None  # Should exit with option 3
            output = " ".join(str(call) for call in mock_print.call_args_list)
            # Should show menu options
            assert "View all ranked projects" in output
            # Should show the project
            assert "TestProj" in output
            assert "Ranked Projects" in output


def test_view_ranked_projects_menu_option_2(setup_user):
    """Test that option 2 calls view_top_projects_summaries."""
    conn, user_id = setup_user
    summary = _summary_dict(
        project_name="TestProj",
        metrics={"skills_detailed": [{"score": 0.8}], "activity_type": {"writing": 1}},
        summary_text="This is a test summary"
    )
    save_project_summary(conn, user_id, "TestProj", json.dumps(summary))
    
    # First input selects option 2, second input selects option 3 to exit
    with patch("builtins.input", side_effect=["2", "3"]):
        with patch("builtins.print") as mock_print:
            result = view_ranked_projects(conn, user_id, "testuser")
            assert result is None  # Should exit with option 3
            output = " ".join(str(call) for call in mock_print.call_args_list)
            # Should show menu options
            assert "View summaries of top projects" in output
            # Should show top projects
            assert "Top" in output
            assert "TestProj" in output


def test_view_ranked_projects_menu_option_3(setup_user):
    """Test that option 3 returns to main menu."""
    conn, user_id = setup_user
    
    with patch("builtins.input", side_effect=["3"]):
        with patch("builtins.print") as mock_print:
            result = view_ranked_projects(conn, user_id, "testuser")
            # Should return None (exit menu)
            assert result is None
            output = " ".join(str(call) for call in mock_print.call_args_list)
            # Should show menu options
            assert "Return to main menu" in output


def test_view_ranked_projects_invalid_choice(setup_user):
    """Test that invalid choice shows error and loops back."""
    conn, user_id = setup_user
    
    # First invalid, then valid choice to exit
    with patch("builtins.input", side_effect=["invalid", "3"]):
        with patch("builtins.print") as mock_print:
            result = view_ranked_projects(conn, user_id, "testuser")
            assert result is None
            output = " ".join(str(call) for call in mock_print.call_args_list)
            # Should show error message
            assert "Invalid choice" in output


def test_view_top_projects_summaries_no_projects(setup_user):
    """Test view_top_projects_summaries with no projects."""
    conn, user_id = setup_user
    
    with patch("builtins.print") as mock_print:
        view_top_projects_summaries(conn, user_id, "testuser")
        output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "No projects found" in output


def test_view_top_projects_summaries_with_summary(setup_user):
    """Test view_top_projects_summaries displays project summaries."""
    conn, user_id = setup_user
    summary = _summary_dict(
        project_name="TestProj",
        project_type="text",
        project_mode="individual",
        metrics={"skills_detailed": [{"score": 0.8}], "activity_type": {"writing": 1}},
        summary_text="This is a test project summary"
    )
    save_project_summary(conn, user_id, "TestProj", json.dumps(summary))
    
    with patch("builtins.print") as mock_print:
        view_top_projects_summaries(conn, user_id, "testuser")
        output = " ".join(str(call) for call in mock_print.call_args_list)
        # Should show top projects header
        assert "Top" in output
        assert "Projects" in output
        # Should show project name and score
        assert "TestProj" in output
        assert "Score" in output
        # Should show project type and mode
        assert "Project Type" in output
        assert "text" in output
        assert "Project Mode" in output
        assert "individual" in output
        # Should show summary text
        assert "SUMMARY" in output
        assert "This is a test project summary" in output


def test_view_top_projects_summaries_without_summary_text(setup_user):
    """Test view_top_projects_summaries when summary_text is missing."""
    conn, user_id = setup_user
    summary = _summary_dict(
        project_name="TestProj",
        project_type="code",
        project_mode="individual",
        metrics={"skills_detailed": [{"score": 0.8}], "activity_type": {"writing": 1}}
        # No summary_text field
    )
    save_project_summary(conn, user_id, "TestProj", json.dumps(summary))
    
    with patch("builtins.print") as mock_print:
        view_top_projects_summaries(conn, user_id, "testuser")
        output = " ".join(str(call) for call in mock_print.call_args_list)
        # Should show project
        assert "TestProj" in output
        # Should show message about missing summary
        assert "No summary text available" in output


def test_view_top_projects_summaries_multiple_projects(setup_user):
    """Test view_top_projects_summaries with multiple projects (top 3)."""
    conn, user_id = setup_user
    
    # Create 3 projects with different scores
    for i, score in enumerate([0.9, 0.7, 0.5], start=1):
        summary = _summary_dict(
            project_name=f"Project{i}",
            metrics={"skills_detailed": [{"score": score}], "activity_type": {"writing": 1}},
            summary_text=f"Summary for Project{i}"
        )
        save_project_summary(conn, user_id, f"Project{i}", json.dumps(summary))
    
    with patch("builtins.print") as mock_print:
        view_top_projects_summaries(conn, user_id, "testuser")
        output = " ".join(str(call) for call in mock_print.call_args_list)
        # Should show all 3 projects
        assert "Top 3 Projects" in output
        assert "Project1" in output
        assert "Project2" in output
        assert "Project3" in output
        # Should show summaries
        assert "Summary for Project1" in output
        assert "Summary for Project2" in output
        assert "Summary for Project3" in output


def test_view_top_projects_summaries_less_than_3(setup_user):
    """Test view_top_projects_summaries with fewer than 3 projects."""
    conn, user_id = setup_user
    
    # Create only 2 projects
    for i, score in enumerate([0.9, 0.7], start=1):
        summary = _summary_dict(
            project_name=f"Project{i}",
            metrics={"skills_detailed": [{"score": score}], "activity_type": {"writing": 1}},
            summary_text=f"Summary for Project{i}"
        )
        save_project_summary(conn, user_id, f"Project{i}", json.dumps(summary))
    
    with patch("builtins.print") as mock_print:
        view_top_projects_summaries(conn, user_id, "testuser")
        output = " ".join(str(call) for call in mock_print.call_args_list)
        # Should show "Top 2 Projects" (not 3)
        assert "Top 2 Projects" in output
        assert "Project1" in output
        assert "Project2" in output


def test_view_top_projects_summaries_exception_handling(setup_user):
    """Test exception handling in view_top_projects_summaries."""
    conn, user_id = setup_user
    
    with patch("src.menu.ranked_projects.collect_project_data", side_effect=Exception("Test error")):
        with patch("builtins.print") as mock_print:
            view_top_projects_summaries(conn, user_id, "testuser")
            output = " ".join(str(call) for call in mock_print.call_args_list)
            assert "Error printing top projects summaries" in output
