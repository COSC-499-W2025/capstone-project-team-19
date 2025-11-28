import pytest
import json
from unittest.mock import patch, call
from src.menu.project_summaries import view_old_project_summaries, display_project_summary
from src.db import (
    connect,
    init_schema,
    get_or_create_user,
    save_project_summary,
)


class TestViewOldProjectSummaries:
    """Tests for viewing old project summaries."""

    @pytest.fixture
    def setup_user(self):
        """Create a test user and return connection and user_id."""
        conn = connect()
        init_schema(conn)
        user_id = get_or_create_user(conn, "testuser")
        yield conn, user_id, "testuser"
        conn.close()

    def test_no_summaries_found(self, setup_user):
        """Test displaying message when user has no project summaries."""
        conn, user_id, username = setup_user

        with patch("builtins.input", return_value=""):
            with patch("builtins.print") as mock_print:
                result = view_old_project_summaries(conn, user_id, username)

                # Should return None when no summaries
                assert result is None

                # Should display appropriate message
                print_calls = [str(call) for call in mock_print.call_args_list]
                combined_output = " ".join(print_calls)

                assert "No project summaries found" in combined_output
                assert "testuser" in combined_output

    def test_multiple_projects_list_display(self, setup_user):
        """Test that multiple projects are listed with selection prompt."""
        conn, user_id, username = setup_user

        # Create multiple project summaries
        for i in range(3):
            summary_data = {
                "project_type": "web",
                "project_mode": "collaborative",
                "summary_text": f"Summary for project {i}"
            }
            save_project_summary(conn, user_id, f"Project{i}", json.dumps(summary_data))

        # User quits immediately
        with patch("builtins.input", return_value="q"):
            with patch("builtins.print") as mock_print:
                result = view_old_project_summaries(conn, user_id, username)

                assert result is None

                print_calls = [str(call) for call in mock_print.call_args_list]
                combined_output = " ".join(print_calls)

                # Should list all projects
                assert "Project0" in combined_output
                assert "Project1" in combined_output
                assert "Project2" in combined_output

    def test_select_project_by_number(self, setup_user):
        """Test selecting a specific project by number."""
        conn, user_id, username = setup_user

        # Create multiple projects
        for i in range(3):
            summary_data = {
                "project_type": "mobile",
                "project_mode": "individual",
                "summary_text": f"This is project {i}"
            }
            save_project_summary(conn, user_id, f"Project{i}", json.dumps(summary_data))

        # User selects project 2, then quits
        with patch("builtins.input", side_effect=["2", "n"]):
            with patch("builtins.print") as mock_print:
                result = view_old_project_summaries(conn, user_id, username)

                assert result is None

                print_calls = [str(call) for call in mock_print.call_args_list]
                combined_output = " ".join(print_calls)

                # Should display selected project
                assert "PROJECT SUMMARY: Project1" in combined_output
                assert "This is project 1" in combined_output

    def test_view_another_project_yes(self, setup_user):
        """Test viewing another project after first selection."""
        conn, user_id, username = setup_user

        # Create multiple projects
        for i in range(3):
            summary_data = {
                "project_type": "cli",
                "project_mode": "collaborative",
                "summary_text": f"CLI project {i}"
            }
            save_project_summary(conn, user_id, f"CLIProject{i}", json.dumps(summary_data))

        # User views project 1, then views project 3, then quits
        with patch("builtins.input", side_effect=["1", "y", "3", "n"]):
            with patch("builtins.print") as mock_print:
                result = view_old_project_summaries(conn, user_id, username)

                assert result is None

                print_calls = [str(call) for call in mock_print.call_args_list]
                combined_output = " ".join(print_calls)

                # Should display both projects
                assert "CLIProject0" in combined_output
                assert "CLIProject2" in combined_output

    def test_view_another_project_no(self, setup_user):
        """Test declining to view another project returns to main menu."""
        conn, user_id, username = setup_user

        # Create projects
        for i in range(2):
            summary_data = {
                "project_type": "web",
                "project_mode": "individual",
                "summary_text": f"Web app {i}"
            }
            save_project_summary(conn, user_id, f"WebApp{i}", json.dumps(summary_data))

        # User views project 1, then declines to view another
        with patch("builtins.input", side_effect=["1", "n"]):
            with patch("builtins.print") as mock_print:
                result = view_old_project_summaries(conn, user_id, username)

                assert result is None

                print_calls = [str(call) for call in mock_print.call_args_list]
                combined_output = " ".join(print_calls)

                assert "Returning to main menu" in combined_output

    def test_quit_with_q(self, setup_user):
        """Test quitting with 'q' command."""
        conn, user_id, username = setup_user

        # Create projects
        for i in range(2):
            summary_data = {
                "project_type": "game",
                "project_mode": "collaborative",
                "summary_text": f"Game project {i}"
            }
            save_project_summary(conn, user_id, f"Game{i}", json.dumps(summary_data))

        with patch("builtins.input", return_value="q"):
            with patch("builtins.print") as mock_print:
                result = view_old_project_summaries(conn, user_id, username)

                assert result is None

                print_calls = [str(call) for call in mock_print.call_args_list]
                combined_output = " ".join(print_calls)

                assert "Returning to main menu" in combined_output

    def test_invalid_selection_number_out_of_range(self, setup_user):
        """Test handling invalid selection (number out of range)."""
        conn, user_id, username = setup_user

        # Create 2 projects
        for i in range(2):
            summary_data = {
                "project_type": "web",
                "project_mode": "individual",
                "summary_text": f"Project {i}"
            }
            save_project_summary(conn, user_id, f"Project{i}", json.dumps(summary_data))

        # User tries to select project 5 (out of range), then quits
        with patch("builtins.input", side_effect=["5", "q"]):
            with patch("builtins.print") as mock_print:
                result = view_old_project_summaries(conn, user_id, username)

                assert result is None

                print_calls = [str(call) for call in mock_print.call_args_list]
                combined_output = " ".join(print_calls)

                assert "Please enter a number between 1 and 2" in combined_output

    def test_invalid_selection_non_numeric(self, setup_user):
        """Test handling invalid selection (non-numeric input)."""
        conn, user_id, username = setup_user

        # Create projects
        for i in range(2):
            summary_data = {
                "project_type": "api",
                "project_mode": "collaborative",
                "summary_text": f"API {i}"
            }
            save_project_summary(conn, user_id, f"API{i}", json.dumps(summary_data))

        # User enters invalid input, then quits
        with patch("builtins.input", side_effect=["abc", "q"]):
            with patch("builtins.print") as mock_print:
                result = view_old_project_summaries(conn, user_id, username)

                assert result is None

                print_calls = [str(call) for call in mock_print.call_args_list]
                combined_output = " ".join(print_calls)

                assert "Invalid input" in combined_output


class TestDisplayProjectSummary:
    """Tests for displaying individual project summary details."""

    @pytest.fixture
    def setup_user(self):
        """Create a test user and return connection and user_id."""
        conn = connect()
        init_schema(conn)
        user_id = get_or_create_user(conn, "testuser")
        yield conn, user_id
        conn.close()

    def test_display_valid_project_summary(self, setup_user):
        """Test displaying a valid project summary."""
        conn, user_id = setup_user

        summary_data = {
            "project_type": "web",
            "project_mode": "collaborative",
            "summary_text": "Detailed project description here"
        }
        save_project_summary(conn, user_id, "WebProject", json.dumps(summary_data))

        with patch("builtins.print") as mock_print:
            display_project_summary(conn, user_id, "WebProject")

            print_calls = [str(call) for call in mock_print.call_args_list]
            combined_output = " ".join(print_calls)

            # Should display all key information
            assert "PROJECT SUMMARY: WebProject" in combined_output
            assert "web" in combined_output
            assert "collaborative" in combined_output
            assert "Detailed project description here" in combined_output

    def test_display_project_with_empty_summary_text(self, setup_user):
        """Test displaying project with empty summary_text."""
        conn, user_id = setup_user

        summary_data = {
            "project_type": "mobile",
            "project_mode": "collaborative",
            "summary_text": ""
        }
        save_project_summary(conn, user_id, "EmptyTextProject", json.dumps(summary_data))

        with patch("builtins.print") as mock_print:
            display_project_summary(conn, user_id, "EmptyTextProject")

            print_calls = [str(call) for call in mock_print.call_args_list]
            combined_output = " ".join(print_calls)

            # Should display header and metadata
            assert "PROJECT SUMMARY: EmptyTextProject" in combined_output
            assert "mobile" in combined_output