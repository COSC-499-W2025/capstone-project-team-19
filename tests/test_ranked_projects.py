"""
Tests for ranked_projects.py view_ranked_projects function.
"""
import pytest
import json
from unittest.mock import patch
from src.db import (
    connect,
    init_schema,
    get_or_create_user,
    save_project_summary,
    get_all_project_ranks,
)
from src.menu.ranked_projects import (
    view_ranked_projects,
    view_top_projects_summaries,
    view_all_ranked_projects,
    interactive_reorder,
    set_specific_rank,
)


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
    
    # First input selects option 1, second input selects option 6 to exit
    with patch("builtins.input", side_effect=["1", "6"]):
        with patch("builtins.print") as mock_print:
            result = view_ranked_projects(conn, user_id, "testuser")
            assert result is None  # Should exit with option 6
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

    # First input selects option 2, second input selects option 6 to exit
    with patch("builtins.input", side_effect=["2", "6"]):
        with patch("builtins.print") as mock_print:
            result = view_ranked_projects(conn, user_id, "testuser")
            assert result is None  # Should exit with option 6
            output = " ".join(str(call) for call in mock_print.call_args_list)
            # Should show menu options
            assert "View summaries of top projects" in output
            # Should show top projects
            assert "Top" in output
            assert "TestProj" in output


def test_view_ranked_projects_menu_option_6(setup_user):
    """Test that option 6 returns to main menu."""
    conn, user_id = setup_user

    with patch("builtins.input", side_effect=["6"]):
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
    with patch("builtins.input", side_effect=["invalid", "6"]):
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

def test_interactive_reorder_valid_input(setup_user):
    """Test interactive_reorder with valid number input."""
    conn, user_id = setup_user

    # Create 3 projects with different scores
    for i, score in enumerate([0.9, 0.7, 0.5], start=1):
        summary = _summary_dict(
            project_name=f"Project{i}",
            metrics={"skills_detailed": [{"score": score}], "activity_type": {"writing": 1}}
        )
        save_project_summary(conn, user_id, f"Project{i}", json.dumps(summary))

    # Reorder: 3, 1, 2 (Project3 first, Project1 second, Project2 third)
    with patch("builtins.input", return_value="3, 1, 2"):
        with patch("builtins.print") as mock_print:
            interactive_reorder(conn, user_id)
            output = " ".join(str(call) for call in mock_print.call_args_list)
            assert "Successfully reordered 3 projects" in output

    # Verify the new ranking
    ranks = dict(get_all_project_ranks(conn, user_id))
    assert ranks["Project3"] == 1
    assert ranks["Project1"] == 2
    assert ranks["Project2"] == 3


def test_interactive_reorder_partial_reorder(setup_user):
    """Test interactive_reorder with only some projects listed."""
    conn, user_id = setup_user

    # Create 4 projects
    for i in range(1, 5):
        summary = _summary_dict(
            project_name=f"Project{i}",
            metrics={"skills_detailed": [{"score": 0.8}], "activity_type": {"writing": 1}}
        )
        save_project_summary(conn, user_id, f"Project{i}", json.dumps(summary))

    # Only reorder first 2 projects
    with patch("builtins.input", return_value="2, 1"):
        with patch("builtins.print") as mock_print:
            interactive_reorder(conn, user_id)
            output = " ".join(str(call) for call in mock_print.call_args_list)
            assert "Successfully reordered 2 projects" in output
            assert "2 project(s) not listed will use automatic ranking" in output

    # Verify rankings
    ranks = dict(get_all_project_ranks(conn, user_id))
    assert ranks["Project2"] == 1
    assert ranks["Project1"] == 2
    # Project3 and Project4 should not have manual ranks
    assert "Project3" not in ranks or ranks.get("Project3") is None
    assert "Project4" not in ranks or ranks.get("Project4") is None

def test_interactive_reorder_invalid_numbers(setup_user):
    """Test interactive_reorder with invalid number input."""
    conn, user_id = setup_user

    # Create projects
    for i in range(1, 3):
        summary = _summary_dict(
            project_name=f"Project{i}",
            metrics={"skills_detailed": [{"score": 0.8}], "activity_type": {"writing": 1}}
        )
        save_project_summary(conn, user_id, f"Project{i}", json.dumps(summary))

    with patch("builtins.input", return_value="abc, def"):
        with patch("builtins.print") as mock_print:
            interactive_reorder(conn, user_id)
            output = " ".join(str(call) for call in mock_print.call_args_list)
            assert "Error" in output
            assert "valid numbers" in output

def test_interactive_reorder_out_of_range(setup_user):
    """Test interactive_reorder with numbers out of range."""
    conn, user_id = setup_user

    # Create 3 projects
    for i in range(1, 4):
        summary = _summary_dict(
            project_name=f"Project{i}",
            metrics={"skills_detailed": [{"score": 0.8}], "activity_type": {"writing": 1}}
        )
        save_project_summary(conn, user_id, f"Project{i}", json.dumps(summary))

    # Try to use number 5 (out of range)
    with patch("builtins.input", return_value="1, 5, 2"):
        with patch("builtins.print") as mock_print:
            interactive_reorder(conn, user_id)
            output = " ".join(str(call) for call in mock_print.call_args_list)
            assert "Error" in output
            assert "between 1 and 3" in output

def test_interactive_reorder_no_projects(setup_user):
    """Test interactive_reorder with no projects."""
    conn, user_id = setup_user

    with patch("builtins.print") as mock_print:
        interactive_reorder(conn, user_id)
        output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "No projects found" in output

def test_interactive_reorder_single_project(setup_user):
    """Test interactive_reorder with single project."""
    conn, user_id = setup_user

    summary = _summary_dict(
        project_name="OnlyProject",
        metrics={"skills_detailed": [{"score": 0.8}], "activity_type": {"writing": 1}}
    )
    save_project_summary(conn, user_id, "OnlyProject", json.dumps(summary))

    with patch("builtins.input", return_value="1"):
        with patch("builtins.print") as mock_print:
            interactive_reorder(conn, user_id)
            output = " ".join(str(call) for call in mock_print.call_args_list)
            assert "Successfully reordered 1 projects" in output

def test_set_specific_rank_valid_input(setup_user):
    """Test set_specific_rank with valid input."""
    conn, user_id = setup_user

    # Create 3 projects
    for i in range(1, 4):
        summary = _summary_dict(
            project_name=f"Project{i}",
            metrics={"skills_detailed": [{"score": 0.9 - i * 0.1}], "activity_type": {"writing": 1}}
        )
        save_project_summary(conn, user_id, f"Project{i}", json.dumps(summary))

    # Move Project3 to position 1
    with patch("builtins.input", side_effect=["3", "1"]):
        with patch("builtins.print") as mock_print:
            set_specific_rank(conn, user_id)
            output = " ".join(str(call) for call in mock_print.call_args_list)
            assert "'Project3' moved to position #1" in output

    # Verify all projects have sequential ranks
    ranks = dict(get_all_project_ranks(conn, user_id))
    assert ranks["Project3"] == 1
    assert ranks["Project1"] == 2
    assert ranks["Project2"] == 3


def test_set_specific_rank_move_down(setup_user):
    """Test set_specific_rank moving a project down in ranking."""
    conn, user_id = setup_user

    # Create 3 projects
    for i in range(1, 4):
        summary = _summary_dict(
            project_name=f"Project{i}",
            metrics={"skills_detailed": [{"score": 0.9 - i * 0.1}], "activity_type": {"writing": 1}}
        )
        save_project_summary(conn, user_id, f"Project{i}", json.dumps(summary))

    # Move Project1 (currently at position 1) to position 3
    with patch("builtins.input", side_effect=["1", "3"]):
        with patch("builtins.print") as mock_print:
            set_specific_rank(conn, user_id)
            output = " ".join(str(call) for call in mock_print.call_args_list)
            assert "'Project1' moved to position #3" in output

    # Verify new order
    ranks = dict(get_all_project_ranks(conn, user_id))
    assert ranks["Project2"] == 1
    assert ranks["Project3"] == 2
    assert ranks["Project1"] == 3


def test_set_specific_rank_set_to_auto(setup_user):
    """Test set_specific_rank setting a project to automatic ranking."""
    conn, user_id = setup_user

    # Create projects
    for i in range(1, 3):
        summary = _summary_dict(
            project_name=f"Project{i}",
            metrics={"skills_detailed": [{"score": 0.8}], "activity_type": {"writing": 1}}
        )
        save_project_summary(conn, user_id, f"Project{i}", json.dumps(summary))

    # First set a manual rank
    with patch("builtins.input", side_effect=["1", "2"]):
        set_specific_rank(conn, user_id)

    # Verify it was set
    ranks = dict(get_all_project_ranks(conn, user_id))
    assert "Project1" in ranks

    # Now set it back to auto
    with patch("builtins.input", side_effect=["2", "auto"]):  # Project1 is now at position 2
        with patch("builtins.print") as mock_print:
            set_specific_rank(conn, user_id)
            output = " ".join(str(call) for call in mock_print.call_args_list)
            assert "now uses automatic ranking" in output


def test_set_specific_rank_invalid_project_number(setup_user):
    """Test set_specific_rank with invalid project number."""
    conn, user_id = setup_user

    # Create projects
    for i in range(1, 3):
        summary = _summary_dict(
            project_name=f"Project{i}",
            metrics={"skills_detailed": [{"score": 0.8}], "activity_type": {"writing": 1}}
        )
        save_project_summary(conn, user_id, f"Project{i}", json.dumps(summary))

    # Try invalid project number
    with patch("builtins.input", return_value="5"):
        with patch("builtins.print") as mock_print:
            set_specific_rank(conn, user_id)
            output = " ".join(str(call) for call in mock_print.call_args_list)
            assert "Invalid project number" in output


def test_set_specific_rank_invalid_rank_number(setup_user):
    """Test set_specific_rank with invalid rank number."""
    conn, user_id = setup_user

    # Create projects
    for i in range(1, 3):
        summary = _summary_dict(
            project_name=f"Project{i}",
            metrics={"skills_detailed": [{"score": 0.8}], "activity_type": {"writing": 1}}
        )
        save_project_summary(conn, user_id, f"Project{i}", json.dumps(summary))

    # Try invalid rank (too high)
    with patch("builtins.input", side_effect=["1", "10"]):
        with patch("builtins.print") as mock_print:
            set_specific_rank(conn, user_id)
            output = " ".join(str(call) for call in mock_print.call_args_list)
            assert "Rank must be between 1 and 2" in output

def test_set_specific_rank_no_projects(setup_user):
    """Test set_specific_rank with no projects."""
    conn, user_id = setup_user

    with patch("builtins.print") as mock_print:
        set_specific_rank(conn, user_id)
        output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "No projects found" in output

def test_set_specific_rank_preserves_other_rankings(setup_user):
    """Test that set_specific_rank preserves rankings of other projects."""
    conn, user_id = setup_user

    # Create 4 projects
    for i in range(1, 5):
        summary = _summary_dict(
            project_name=f"Project{i}",
            metrics={"skills_detailed": [{"score": 0.9 - i * 0.1}], "activity_type": {"writing": 1}}
        )
        save_project_summary(conn, user_id, f"Project{i}", json.dumps(summary))

    # Move Project4 to position 1
    with patch("builtins.input", side_effect=["4", "1"]):
        set_specific_rank(conn, user_id)

    # Verify all projects now have sequential manual ranks
    ranks = dict(get_all_project_ranks(conn, user_id))
    assert len(ranks) == 4
    assert ranks["Project4"] == 1
    # Other projects should have been shifted
    assert all(rank in [1, 2, 3, 4] for rank in ranks.values())
