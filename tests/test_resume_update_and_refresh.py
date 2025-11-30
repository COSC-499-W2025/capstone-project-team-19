import json
import sqlite3

import pytest

from src.db import init_schema, list_resumes, get_resume_snapshot
from src.db.resumes import (
    insert_resume_snapshot,
    update_resume_snapshot,
    delete_resume_snapshot,
)
from src.menu import resume as resume_mod


def _make_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    # Create a dummy user so FK constraints (if enabled) are happy
    conn.execute(
        "INSERT INTO users (user_id, username, email) VALUES (?, ?, ?)",
        (1, "testuser", "test@example.com"),
    )
    conn.commit()
    return conn


def test_update_resume_snapshot_overwrites_json_and_text():
    conn = _make_conn()
    user_id = 1

    # Seed a snapshot
    snapshot = {"projects": [], "aggregated_skills": {}}
    insert_resume_snapshot(
        conn,
        user_id=user_id,
        name="Original",
        resume_json=json.dumps(snapshot),
        rendered_text="old text",
    )

    resumes = list_resumes(conn, user_id)
    assert len(resumes) == 1
    resume_id = resumes[0]["id"]

    # Update it
    updated_snapshot = {"projects": [{"project_name": "proj"}]}
    new_json = json.dumps(updated_snapshot)

    update_resume_snapshot(
        conn,
        user_id=user_id,
        resume_id=resume_id,
        resume_json=new_json,
        rendered_text="new text",
    )

    record = get_resume_snapshot(conn, user_id, resume_id)
    assert record is not None
    assert record["resume_json"] == new_json
    assert record["rendered_text"] == "new text"


def test_delete_resume_snapshot_removes_row():
    conn = _make_conn()
    user_id = 1

    insert_resume_snapshot(
        conn,
        user_id=user_id,
        name="ToDelete",
        resume_json=json.dumps({"foo": "bar"}),
        rendered_text=None,
    )

    resumes_before = list_resumes(conn, user_id)
    assert len(resumes_before) == 1
    resume_id = resumes_before[0]["id"]

    delete_resume_snapshot(conn, user_id, resume_id)

    resumes_after = list_resumes(conn, user_id)
    assert resumes_after == []
    assert get_resume_snapshot(conn, user_id, resume_id) is None


def test_refresh_saved_resumes_after_project_delete_updates_and_removes():
    """
    - One resume has [target_project + other_project] -> should be updated.
    - Another resume has only [target_project] -> should be deleted.
    """
    conn = _make_conn()
    user_id = 1
    target_project = "proj_to_delete"

    # Resume 1: mixed projects (should survive, minus deleted project)
    snapshot1 = {
        "projects": [
            {
                "project_name": target_project,
                "languages": ["Python"],
                "frameworks": ["FastAPI"],
                "skills": ["Clean code & quality", "Clear communication"],
            },
            {
                "project_name": "proj_keep",
                "languages": ["JavaScript"],
                "frameworks": ["React"],
                "skills": ["DevOps & CI/CD", "Analytical writing"],
            },
        ],
        "aggregated_skills": {
            "languages": ["WRONG"],
            "frameworks": ["WRONG"],
            "technical_skills": ["WRONG"],
            "writing_skills": ["WRONG"],
        },
    }

    # Resume 2: only target project (should be removed)
    snapshot2 = {
        "projects": [
            {
                "project_name": target_project,
                "languages": ["Python"],
                "frameworks": ["Django"],
                "skills": ["Clean code & quality", "Clear communication"],
            }
        ],
        "aggregated_skills": {
            "languages": ["Python"],
            "frameworks": ["Django"],
            "technical_skills": ["Clean code & quality"],
            "writing_skills": ["Clear communication"],
        },
    }

    insert_resume_snapshot(
        conn,
        user_id=user_id,
        name="WithTwoProjects",
        resume_json=json.dumps(snapshot1),
        rendered_text="snapshot1",
    )
    insert_resume_snapshot(
        conn,
        user_id=user_id,
        name="OnlyDeletedProject",
        resume_json=json.dumps(snapshot2),
        rendered_text="snapshot2",
    )

    # Sanity check
    resumes_before = list_resumes(conn, user_id)
    assert {r["name"] for r in resumes_before} == {
        "WithTwoProjects",
        "OnlyDeletedProject",
    }

    # Run refresh
    resume_mod.refresh_saved_resumes_after_project_delete(
        conn, user_id, target_project
    )

    # After refresh: only "WithTwoProjects" remains
    resumes_after = list_resumes(conn, user_id)
    assert {r["name"] for r in resumes_after} == {"WithTwoProjects"}

    remaining = resumes_after[0]
    record = get_resume_snapshot(conn, user_id, remaining["id"])
    stored = json.loads(record["resume_json"])

    # Projects list should only have the non-deleted project
    projects = stored.get("projects") or []
    assert len(projects) == 1
    assert projects[0]["project_name"] == "proj_keep"

    # Aggregated skills should be recomputed from the remaining project only
    agg = stored["aggregated_skills"]
    assert agg["languages"] == ["JavaScript"]
    assert agg["frameworks"] == ["React"]

    # All skills from the remaining project should appear in either
    # technical_skills or writing_skills.
    remaining_skills = {"DevOps & CI/CD", "Analytical writing"}
    combined = set(agg["technical_skills"]) | set(agg["writing_skills"])
    assert remaining_skills.issubset(combined)
