import pytest

from src.menu.delete.delete_project import handle_delete_project
from src.menu.delete.delete_resume import handle_delete_resume
from src.menu.delete.common import post_delete_next_steps


def test_handle_delete_project_with_resume_refresh(monkeypatch):
    """
    User selects a project, confirms delete, chooses to refresh resumes.
    Should call delete_project_everywhere and refresh_saved_resumes_after_project_delete.
    """
    called_delete = []
    called_refresh = []

    def fake_select_project(conn, user_id, username):
        return "proj_one"

    def fake_delete_project_everywhere(conn, user_id, project_name):
        called_delete.append((conn, user_id, project_name))

    def fake_refresh(conn, user_id, project_name):
        called_refresh.append((conn, user_id, project_name))

    def fake_post_next_steps(conn, user_id, username):
        # Avoid further input loops
        return

    # IMPORTANT: patch where the functions are USED, not where they originate
    monkeypatch.setattr(
        "src.menu.delete.delete_project._select_project", fake_select_project
    )
    monkeypatch.setattr(
        "src.menu.delete.delete_project.delete_project_everywhere",
        fake_delete_project_everywhere,
    )
    monkeypatch.setattr(
        "src.menu.delete.delete_project.refresh_saved_resumes_after_project_delete",
        fake_refresh,
    )
    monkeypatch.setattr(
        "src.menu.delete.delete_project.post_delete_next_steps",
        fake_post_next_steps,
    )

    # Input sequence: confirm "DELETE", then choice "1" (refresh resumes)
    inputs = iter(["DELETE", "1"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    dummy_conn = object()
    handle_delete_project(dummy_conn, user_id=1, username="alice")

    assert called_delete == [(dummy_conn, 1, "proj_one")]
    assert called_refresh == [(dummy_conn, 1, "proj_one")]


def test_handle_delete_project_keep_old_resumes(monkeypatch):
    """
    User selects a project, confirms delete, chooses to keep old resumes.
    Should call delete_project_everywhere but NOT refresh_saved_resumes_after_project_delete.
    """
    called_delete = []
    called_refresh = []

    def fake_select_project(conn, user_id, username):
        return "proj_two"

    def fake_delete_project_everywhere(conn, user_id, project_name):
        called_delete.append((conn, user_id, project_name))

    def fake_refresh(conn, user_id, project_name):
        called_refresh.append((conn, user_id, project_name))

    def fake_post_next_steps(conn, user_id, username):
        return

    monkeypatch.setattr(
        "src.menu.delete.delete_project._select_project", fake_select_project
    )
    monkeypatch.setattr(
        "src.menu.delete.delete_project.delete_project_everywhere",
        fake_delete_project_everywhere,
    )
    monkeypatch.setattr(
        "src.menu.delete.delete_project.refresh_saved_resumes_after_project_delete",
        fake_refresh,
    )
    monkeypatch.setattr(
        "src.menu.delete.delete_project.post_delete_next_steps",
        fake_post_next_steps,
    )

    # Input sequence: confirm "DELETE", then choice "2" (keep resumes)
    inputs = iter(["DELETE", "2"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    dummy_conn = object()
    handle_delete_project(dummy_conn, user_id=1, username="alice")

    assert called_delete == [(dummy_conn, 1, "proj_two")]
    assert called_refresh == []


def test_handle_delete_resume_happy_path(monkeypatch):
    """
    User selects a resume by index, confirms DELETE; should delete correct snapshot.
    """
    called_delete = []

    def fake_list_resumes(conn, user_id):
        return [
            {"id": 10, "name": "Resume A", "created_at": "2025-01-01"},
            {"id": 20, "name": "Resume B", "created_at": "2025-01-02"},
        ]

    def fake_delete_resume_snapshot(conn, user_id, resume_id):
        called_delete.append((conn, user_id, resume_id))

    def fake_post_next_steps(conn, user_id, username):
        return

    # Patch the names USED in delete_resume.py
    monkeypatch.setattr(
        "src.menu.delete.delete_resume.list_resumes", fake_list_resumes
    )
    monkeypatch.setattr(
        "src.menu.delete.delete_resume.delete_resume_snapshot",
        fake_delete_resume_snapshot,
    )
    monkeypatch.setattr(
        "src.menu.delete.delete_resume.post_delete_next_steps",
        fake_post_next_steps,
    )

    # Inputs: "1" to select first resume, then "DELETE" to confirm
    inputs = iter(["1", "DELETE"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    dummy_conn = object()
    handle_delete_resume(dummy_conn, user_id=1, username="alice")

    assert called_delete == [(dummy_conn, 1, 10)]


def test_post_delete_next_steps_routes_to_portfolio_and_resume(monkeypatch):
    """
    Ensure post_delete_next_steps routes correctly for options 1 and 2.
    """
    calls = {"portfolio": 0, "resume": 0}

    def fake_portfolio(conn, user_id, username):
        calls["portfolio"] += 1

    def fake_create_resume(conn, user_id, username):
        calls["resume"] += 1

    # Patch functions as they are imported & used inside common.py
    monkeypatch.setattr(
        "src.menu.delete.common.view_portfolio_items", fake_portfolio
    )
    monkeypatch.setattr(
        "src.menu.delete.common._handle_create_resume",
        fake_create_resume,
    )

    # Option 1: view updated portfolio
    inputs1 = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs1))
    post_delete_next_steps(object(), 1, "alice")
    assert calls["portfolio"] == 1
    assert calls["resume"] == 0

    # Option 2: create new resume
    inputs2 = iter(["2"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs2))
    post_delete_next_steps(object(), 1, "alice")
    assert calls["portfolio"] == 1  # unchanged
    assert calls["resume"] == 1

    # Option 3: back to main menu
    inputs3 = iter(["3"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs3))
    post_delete_next_steps(object(), 1, "alice")
    # No additional calls
    assert calls["portfolio"] == 1
    assert calls["resume"] == 1


