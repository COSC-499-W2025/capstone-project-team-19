import json
import sqlite3
from datetime import datetime, UTC

import pytest

from src.db import init_schema, save_project_summary, list_resumes, get_resume_snapshot
from src.menu import resume as resume_mod


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


def test_create_resume_uses_top_five(monkeypatch):
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    # Seed six project summaries
    names = [f"proj{i}" for i in range(6)]
    for name in names:
        save_project_summary(conn, user_id, name, _make_summary(name))

    # Rank projects with scores (proj0 highest, proj5 lowest)
    ranked = [(name, score) for score, name in enumerate(reversed(names), start=1)]
    ranked.sort(key=lambda x: x[1], reverse=True)

    def fake_collect_project_data(conn_arg, user_id_arg):
        assert conn_arg is conn
        assert user_id_arg == user_id
        return ranked

    # Always accept default resume name
    monkeypatch.setattr("builtins.input", lambda _: "")
    monkeypatch.setattr(resume_mod, "collect_project_data", fake_collect_project_data)

    resume_mod._handle_create_resume(conn, user_id, "TestUser")

    snapshots = list_resumes(conn, user_id)
    assert len(snapshots) == 1

    snap = get_resume_snapshot(conn, user_id, snapshots[0]["id"])
    assert snap is not None

    data = json.loads(snap["resume_json"])
    project_names = {p["project_name"] for p in data.get("projects", [])}

    # Expect only top 5 projects (exclude the lowest-ranked)
    expected_top = set(name for name, _ in ranked[:5])
    assert project_names == expected_top


def test_create_resume_no_summaries(monkeypatch):
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    # No summaries seeded
    monkeypatch.setattr("builtins.input", lambda _: "")

    resume_mod._handle_create_resume(conn, user_id, "TestUser")

    snapshots = list_resumes(conn, user_id)
    assert snapshots == []


def test_view_existing_resume_lists_and_renders(monkeypatch, capsys):
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    # Seed one summary and a resume snapshot
    save_project_summary(conn, user_id, "projA", _make_summary("projA"))
    snap_data = {"projects": [{"project_name": "projA"}], "aggregated_skills": {}}
    resume_mod.insert_resume_snapshot(conn, user_id, "MyResume", json.dumps(snap_data), "Rendered text")

    # Mock selection of first resume
    inputs = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    resume_mod._handle_view_existing_resume(conn, user_id)

    captured = capsys.readouterr().out
    assert "MyResume" in captured
    assert "Rendered text" in captured


def test_view_existing_resume_no_resumes(capsys):
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    resume_mod._handle_view_existing_resume(conn, user_id)
    captured = capsys.readouterr().out
    assert "No saved resumes yet" in captured


def test_create_resume_with_fewer_than_five_projects(monkeypatch):
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    # Seed three project summaries
    for name in ["p1", "p2", "p3"]:
        save_project_summary(conn, user_id, name, _make_summary(name))

    # Mock ranking returning just these three
    def fake_collect_project_data(conn_arg, user_id_arg):
        return [("p1", 1.0), ("p2", 0.9), ("p3", 0.8)]

    monkeypatch.setattr("builtins.input", lambda _: "")
    monkeypatch.setattr(resume_mod, "collect_project_data", fake_collect_project_data)

    resume_mod._handle_create_resume(conn, user_id, "TestUser")

    snaps = list_resumes(conn, user_id)
    assert len(snaps) == 1
    data = json.loads(snaps[0]["name"] or "{}") if False else json.loads(get_resume_snapshot(conn, user_id, snaps[0]["id"])["resume_json"])
    projects = {p["project_name"] for p in data.get("projects", [])}
    assert projects == {"p1", "p2", "p3"}
