"""
Tests for the edit project dates functionality.
"""

import json
import sqlite3
from datetime import datetime, UTC

import pytest

from src.db import (
    init_schema,
    save_project_summary,
    set_project_dates,
    get_project_dates,
    clear_project_dates,
    clear_all_project_dates,
    get_all_manual_dates,
)
from src.menu.project_dates import (
    edit_project_dates_menu,
    set_project_date,
    clear_specific_project_dates,
    reset_all_dates_to_auto,
    view_all_projects_with_dates,
)


def _make_summary(project_name: str, project_type: str = "code", project_mode: str = "individual") -> str:
    """Build a minimal ProjectSummary JSON string."""
    summary = {
        "project_name": project_name,
        "project_type": project_type,
        "project_mode": project_mode,
        "languages": [],
        "frameworks": [],
        "summary_text": None,
        "skills": [],
        "metrics": {},
        "contributions": {},
        "created_at": datetime.now(UTC).isoformat(),
        "project_id": None,
    }
    return json.dumps(summary)


def _mock_collect_project_data(conn, user_id, project_names):
    """Create a mock function that returns project data."""
    def mock_func(conn_arg, user_id_arg):
        assert conn_arg is conn
        assert user_id_arg == user_id
        return [(name, 1.0) for name in project_names]
    return mock_func


class TestEditProjectDatesMenu:
    """Tests for the main edit project dates menu."""

    def test_menu_displays_all_options(self, monkeypatch, capsys):
        """Test that all menu options are displayed."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        # Mock input to immediately exit (choice 5)
        monkeypatch.setattr("builtins.input", lambda _: "5")

        edit_project_dates_menu(conn, user_id, "testuser")

        captured = capsys.readouterr().out
        assert "1. View all projects with dates" in captured
        assert "2. Set dates for specific project" in captured
        assert "3. Clear dates for specific project (revert to automatic)" in captured
        assert "4. Reset all to automatic dates" in captured
        assert "5. Return to main menu" in captured

    def test_menu_returns_on_choice_5(self, monkeypatch):
        """Test that choosing option 5 returns to main menu."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        monkeypatch.setattr("builtins.input", lambda _: "5")
        result = edit_project_dates_menu(conn, user_id, "testuser")

        assert result is None

    def test_menu_handles_invalid_choice(self, monkeypatch, capsys):
        """Test that invalid menu choices are rejected."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        # Mock input to enter invalid choice, then exit
        inputs = iter(["99", "5"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        edit_project_dates_menu(conn, user_id, "testuser")

        captured = capsys.readouterr().out
        assert "Invalid choice" in captured


class TestSetProjectDate:
    """Tests for setting project dates."""

    def test_set_project_date_success(self, monkeypatch, capsys):
        """Test successfully setting dates for a project."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        # Seed a project
        project_name = "TestProject"
        save_project_summary(conn, user_id, project_name, _make_summary(project_name))

        # Mock collect_project_data
        from src.menu import project_dates
        monkeypatch.setattr(
            project_dates,
            "collect_project_data",
            _mock_collect_project_data(conn, user_id, [project_name])
        )

        # Mock inputs: project number (1), start date, end date
        inputs = iter(["1", "2024-01-01", "2024-12-31"])
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        set_project_date(conn, user_id)

        # Verify dates were saved
        dates = get_project_dates(conn, user_id, project_name)
        assert dates is not None
        start, end = dates
        assert start == "2024-01-01"
        assert end == "2024-12-31"

        captured = capsys.readouterr().out
        assert "Dates updated" in captured
        assert "TestProject" in captured

    def test_set_project_date_start_only(self, monkeypatch, capsys):
        """Test setting only start date."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        project_name = "TestProject"
        save_project_summary(conn, user_id, project_name, _make_summary(project_name))

        from src.menu import project_dates
        monkeypatch.setattr(
            project_dates,
            "collect_project_data",
            _mock_collect_project_data(conn, user_id, [project_name])
        )

        # Mock inputs: project number (1), start date, empty end date
        inputs = iter(["1", "2024-01-01", ""])
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        set_project_date(conn, user_id)

        dates = get_project_dates(conn, user_id, project_name)
        assert dates is not None
        start, end = dates
        assert start == "2024-01-01"
        assert end is None

    def test_set_project_date_no_dates_provided(self, monkeypatch, capsys):
        """Test that providing no dates makes no changes."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        project_name = "TestProject"
        save_project_summary(conn, user_id, project_name, _make_summary(project_name))

        from src.menu import project_dates
        monkeypatch.setattr(
            project_dates,
            "collect_project_data",
            _mock_collect_project_data(conn, user_id, [project_name])
        )

        # Get initial dates (should be None, None)
        initial_dates = get_project_dates(conn, user_id, project_name)

        # Mock inputs: project number (1), empty start, empty end
        inputs = iter(["1", "", ""])
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        set_project_date(conn, user_id)

        # Dates should remain unchanged
        dates = get_project_dates(conn, user_id, project_name)
        assert dates == initial_dates

        captured = capsys.readouterr().out
        assert "No dates provided" in captured

    def test_set_project_date_invalid_month(self, monkeypatch, capsys):
        """Test that invalid month (13) is rejected."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        project_name = "TestProject"
        save_project_summary(conn, user_id, project_name, _make_summary(project_name))

        from src.menu import project_dates
        monkeypatch.setattr(
            project_dates,
            "collect_project_data",
            _mock_collect_project_data(conn, user_id, [project_name])
        )

        # Mock inputs: project number, invalid month, then skip, skip end
        inputs = iter(["1", "2024-13-01", "", ""])
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        set_project_date(conn, user_id)

        captured = capsys.readouterr().out
        assert "Invalid date" in captured

    def test_set_project_date_invalid_day(self, monkeypatch, capsys):
        """Test that invalid day (Feb 30) is rejected."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        project_name = "TestProject"
        save_project_summary(conn, user_id, project_name, _make_summary(project_name))

        from src.menu import project_dates
        monkeypatch.setattr(
            project_dates,
            "collect_project_data",
            _mock_collect_project_data(conn, user_id, [project_name])
        )

        # Mock inputs: project number, invalid day (Feb 30), then valid, end date
        inputs = iter(["1", "2024-02-30", "2024-02-28", "2024-12-31"])
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        set_project_date(conn, user_id)

        captured = capsys.readouterr().out
        assert "Invalid date" in captured
        assert "Dates updated" in captured

    def test_set_project_date_start_after_end(self, monkeypatch, capsys):
        """Test that start date after end date is rejected."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        project_name = "TestProject"
        save_project_summary(conn, user_id, project_name, _make_summary(project_name))

        from src.menu import project_dates
        monkeypatch.setattr(
            project_dates,
            "collect_project_data",
            _mock_collect_project_data(conn, user_id, [project_name])
        )

        # Mock inputs: project number, start date after end date
        inputs = iter(["1", "2024-12-31", "2024-01-01"])
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        set_project_date(conn, user_id)

        captured = capsys.readouterr().out
        assert "Start date cannot be after end date" in captured

        # Verify dates were NOT saved
        dates = get_project_dates(conn, user_id, project_name)
        assert dates == (None, None)

    def test_set_project_date_invalid_project_number(self, monkeypatch, capsys):
        """Test that invalid project numbers are rejected."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        project_name = "TestProject"
        save_project_summary(conn, user_id, project_name, _make_summary(project_name))

        from src.menu import project_dates
        monkeypatch.setattr(
            project_dates,
            "collect_project_data",
            _mock_collect_project_data(conn, user_id, [project_name])
        )

        # Mock input: invalid project number
        monkeypatch.setattr("builtins.input", lambda prompt: "99")

        set_project_date(conn, user_id)

        captured = capsys.readouterr().out
        assert "Invalid project number" in captured

    def test_set_project_date_no_projects(self, monkeypatch, capsys):
        """Test behavior when no projects are available."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        from src.menu import project_dates
        monkeypatch.setattr(
            project_dates,
            "collect_project_data",
            _mock_collect_project_data(conn, user_id, [])
        )

        set_project_date(conn, user_id)

        captured = capsys.readouterr().out
        assert "No projects found" in captured


class TestClearSpecificProjectDates:
    """Tests for clearing dates for specific projects."""

    def test_clear_specific_project_dates_confirm_yes(self, monkeypatch, capsys):
        """Test clearing dates with 'yes' confirmation."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        # Seed project and set manual dates
        project_name = "TestProject"
        save_project_summary(conn, user_id, project_name, _make_summary(project_name))
        set_project_dates(conn, user_id, project_name, "2024-01-01", "2024-12-31")

        # Verify dates were set
        dates = get_project_dates(conn, user_id, project_name)
        assert dates == ("2024-01-01", "2024-12-31")

        # Mock inputs: project number (1), confirmation (yes)
        inputs = iter(["1", "yes"])
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        clear_specific_project_dates(conn, user_id)

        # Verify dates were cleared (should be None, None)
        dates = get_project_dates(conn, user_id, project_name)
        assert dates == (None, None)

        captured = capsys.readouterr().out
        assert "Manual dates cleared" in captured

    def test_clear_specific_project_dates_confirm_y(self, monkeypatch, capsys):
        """Test clearing dates with 'y' confirmation."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        project_name = "TestProject"
        save_project_summary(conn, user_id, project_name, _make_summary(project_name))
        set_project_dates(conn, user_id, project_name, "2024-01-01", "2024-12-31")

        inputs = iter(["1", "y"])
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        clear_specific_project_dates(conn, user_id)

        dates = get_project_dates(conn, user_id, project_name)
        assert dates == (None, None)

    def test_clear_specific_project_dates_cancelled(self, monkeypatch, capsys):
        """Test cancelling the clear operation."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        project_name = "TestProject"
        save_project_summary(conn, user_id, project_name, _make_summary(project_name))
        set_project_dates(conn, user_id, project_name, "2024-01-01", "2024-12-31")

        # Mock inputs: project number (1), confirmation (no)
        inputs = iter(["1", "no"])
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        clear_specific_project_dates(conn, user_id)

        # Verify dates were NOT cleared
        assert get_project_dates(conn, user_id, project_name) is not None

        captured = capsys.readouterr().out
        assert "Cancelled" in captured

    def test_clear_specific_project_dates_no_manual_dates(self, monkeypatch, capsys):
        """Test when there are no projects with manual dates."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        clear_specific_project_dates(conn, user_id)

        captured = capsys.readouterr().out
        assert "No projects with manual dates found" in captured


class TestResetAllDatesToAuto:
    """Tests for resetting all dates to automatic."""

    def test_reset_all_dates_confirmed(self, monkeypatch, capsys):
        """Test resetting all dates with confirmation."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        # Seed multiple projects with manual dates
        for i in range(3):
            project_name = f"Project{i}"
            save_project_summary(conn, user_id, project_name, _make_summary(project_name))
            set_project_dates(conn, user_id, project_name, "2024-01-01", "2024-12-31")

        # Verify dates were set
        assert len(get_all_manual_dates(conn, user_id)) == 3

        # Mock confirmation: yes
        monkeypatch.setattr("builtins.input", lambda prompt: "yes")

        reset_all_dates_to_auto(conn, user_id)

        # Verify all dates were cleared
        assert len(get_all_manual_dates(conn, user_id)) == 0

        captured = capsys.readouterr().out
        assert "All manual dates cleared" in captured

    def test_reset_all_dates_cancelled(self, monkeypatch, capsys):
        """Test cancelling the reset operation."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        # Seed project with manual dates
        project_name = "Project1"
        save_project_summary(conn, user_id, project_name, _make_summary(project_name))
        set_project_dates(conn, user_id, project_name, "2024-01-01", "2024-12-31")

        # Mock confirmation: no
        monkeypatch.setattr("builtins.input", lambda prompt: "no")

        reset_all_dates_to_auto(conn, user_id)

        # Verify dates were NOT cleared
        assert len(get_all_manual_dates(conn, user_id)) == 1

        captured = capsys.readouterr().out
        assert "Cancelled" in captured

    def test_reset_all_dates_invalid_input(self, monkeypatch, capsys):
        """Test invalid confirmation input."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        # Mock confirmation: invalid
        monkeypatch.setattr("builtins.input", lambda prompt: "maybe")

        reset_all_dates_to_auto(conn, user_id)

        captured = capsys.readouterr().out
        assert "Invalid input" in captured


class TestViewAllProjectsWithDates:
    """Tests for viewing all projects with dates."""

    def test_view_projects_with_manual_dates(self, monkeypatch, capsys):
        """Test viewing projects with manual dates set."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1
        username = "testuser"

        # Seed project with manual dates
        project_name = "TestProject"
        save_project_summary(conn, user_id, project_name, _make_summary(project_name))
        set_project_dates(conn, user_id, project_name, "2024-01-01", "2024-12-31")

        from src.menu import project_dates
        monkeypatch.setattr(
            project_dates,
            "collect_project_data",
            _mock_collect_project_data(conn, user_id, [project_name])
        )

        view_all_projects_with_dates(conn, user_id, username)

        captured = capsys.readouterr().out
        assert "TestProject" in captured
        assert "2024-01-01" in captured
        assert "2024-12-31" in captured
        assert "MANUAL" in captured

    def test_view_projects_no_projects(self, monkeypatch, capsys):
        """Test viewing when no projects exist."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1
        username = "testuser"

        from src.menu import project_dates
        monkeypatch.setattr(
            project_dates,
            "collect_project_data",
            _mock_collect_project_data(conn, user_id, [])
        )

        view_all_projects_with_dates(conn, user_id, username)

        captured = capsys.readouterr().out
        assert "No projects found" in captured


class TestDatabaseFunctions:
    """Tests for the underlying database functions."""

    def test_set_and_get_project_dates(self):
        """Test setting and retrieving project dates."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1
        project_name = "TestProject"

        # Create a project first
        save_project_summary(conn, user_id, project_name, _make_summary(project_name))

        # Initially no manual dates (returns None, None)
        dates = get_project_dates(conn, user_id, project_name)
        assert dates == (None, None)

        # Set dates
        set_project_dates(conn, user_id, project_name, "2024-01-01", "2024-12-31")

        # Retrieve dates
        dates = get_project_dates(conn, user_id, project_name)
        assert dates is not None
        start, end = dates
        assert start == "2024-01-01"
        assert end == "2024-12-31"

    def test_clear_project_dates(self):
        """Test clearing project dates."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1
        project_name = "TestProject"

        # Create a project first
        save_project_summary(conn, user_id, project_name, _make_summary(project_name))

        # Set dates
        set_project_dates(conn, user_id, project_name, "2024-01-01", "2024-12-31")
        dates = get_project_dates(conn, user_id, project_name)
        assert dates == ("2024-01-01", "2024-12-31")

        # Clear dates
        clear_project_dates(conn, user_id, project_name)
        dates = get_project_dates(conn, user_id, project_name)
        assert dates == (None, None)

    def test_clear_all_project_dates(self):
        """Test clearing all project dates."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        # Create and set dates for multiple projects
        for i in range(3):
            project_name = f"Project{i}"
            save_project_summary(conn, user_id, project_name, _make_summary(project_name))
            set_project_dates(conn, user_id, project_name, "2024-01-01", "2024-12-31")

        # Verify dates were set
        assert len(get_all_manual_dates(conn, user_id)) == 3

        # Clear all dates
        clear_all_project_dates(conn, user_id)

        # Verify all dates were cleared
        assert len(get_all_manual_dates(conn, user_id)) == 0

    def test_get_all_manual_dates(self):
        """Test retrieving all manual dates."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1

        # Create and set dates for multiple projects
        projects = ["ProjectA", "ProjectB", "ProjectC"]
        for project_name in projects:
            save_project_summary(conn, user_id, project_name, _make_summary(project_name))
            set_project_dates(conn, user_id, project_name, "2024-01-01", "2024-12-31")

        # Get all manual dates
        manual_dates = get_all_manual_dates(conn, user_id)
        assert len(manual_dates) == 3

        # Verify project names are in results
        project_names = [name for name, _, _ in manual_dates]
        assert set(project_names) == set(projects)

    def test_update_existing_dates(self):
        """Test updating existing project dates."""
        conn = sqlite3.connect(":memory:")
        init_schema(conn)
        user_id = 1
        project_name = "TestProject"

        # Create a project first
        save_project_summary(conn, user_id, project_name, _make_summary(project_name))

        # Set initial dates
        set_project_dates(conn, user_id, project_name, "2024-01-01", "2024-06-30")

        dates = get_project_dates(conn, user_id, project_name)
        assert dates == ("2024-01-01", "2024-06-30")

        # Update dates
        set_project_dates(conn, user_id, project_name, "2024-07-01", "2024-12-31")

        dates = get_project_dates(conn, user_id, project_name)
        assert dates == ("2024-07-01", "2024-12-31")
