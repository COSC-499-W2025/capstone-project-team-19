"""Tests for POST /resume/{resume_id}/projects endpoint (add project to resume)."""
import json
from src.db.project_summaries import save_project_summary, get_project_summary_by_name
from src.db.resumes import insert_resume_snapshot, get_resume_snapshot
from src.menu.resume.helpers import recompute_aggregated_skills


def make_project_entry(name, project_summary_id=None, **kwargs):
    """Build a minimal project entry dict."""
    entry = {
        "project_name": name,
        "project_summary_id": project_summary_id,
        "languages": kwargs.get("languages", []),
        "frameworks": kwargs.get("frameworks", []),
        "skills": kwargs.get("skills", []),
    }
    return entry


def create_resume_with_project(conn, user_id, name, project_name, project_summary_id):
    """Create a test resume with one project. Returns resume_id."""
    entries = [make_project_entry(project_name, project_summary_id)]
    resume_json = json.dumps({
        "projects": entries,
        "aggregated_skills": recompute_aggregated_skills(entries),
    })
    resume_id = insert_resume_snapshot(conn, user_id, name, resume_json)
    conn.commit()
    return resume_id


def test_add_project_to_resume_success(client, auth_headers, seed_conn):
    """Adding a project to a resume returns the updated resume."""
    summary_a = json.dumps({
        "project_name": "ProjectA",
        "project_type": "code",
        "project_mode": "individual",
        "languages": ["Python"],
        "frameworks": [],
        "summary_text": "Project A",
        "metrics": {},
    })
    summary_b = json.dumps({
        "project_name": "ProjectB",
        "project_type": "code",
        "project_mode": "individual",
        "languages": ["JavaScript"],
        "frameworks": [],
        "summary_text": "Project B",
        "metrics": {},
    })
    save_project_summary(seed_conn, 1, "ProjectA", summary_a)
    save_project_summary(seed_conn, 1, "ProjectB", summary_b)
    seed_conn.commit()
    id_a = get_project_summary_by_name(seed_conn, 1, "ProjectA")["project_summary_id"]
    id_b = get_project_summary_by_name(seed_conn, 1, "ProjectB")["project_summary_id"]

    resume_id = create_resume_with_project(seed_conn, 1, "MyResume", "ProjectA", id_a)

    res = client.post(
        f"/resume/{resume_id}/projects",
        json={"project_summary_id": id_b},
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    projects = body["data"]["projects"]
    names = [p["project_name"] for p in projects]
    assert "ProjectA" in names
    assert "ProjectB" in names


def test_add_project_already_in_resume_returns_400(client, auth_headers, seed_conn):
    """Adding a project already in the resume returns 400."""
    summary = json.dumps({
        "project_name": "OnlyProject",
        "project_type": "code",
        "project_mode": "individual",
        "languages": [],
        "frameworks": [],
        "summary_text": "Only",
        "metrics": {},
    })
    save_project_summary(seed_conn, 1, "OnlyProject", summary)
    seed_conn.commit()
    pid = get_project_summary_by_name(seed_conn, 1, "OnlyProject")["project_summary_id"]
    resume_id = create_resume_with_project(seed_conn, 1, "Resume", "OnlyProject", pid)

    res = client.post(
        f"/resume/{resume_id}/projects",
        json={"project_summary_id": pid},
        headers=auth_headers,
    )
    assert res.status_code == 400
    assert "already" in res.json()["detail"].lower()


def test_add_project_nonexistent_resume_returns_404(client, auth_headers, seed_conn):
    """Adding to a nonexistent resume returns 404."""
    summary = json.dumps({
        "project_name": "SomeProject",
        "project_type": "code",
        "project_mode": "individual",
        "languages": [],
        "frameworks": [],
        "summary_text": "X",
        "metrics": {},
    })
    save_project_summary(seed_conn, 1, "SomeProject", summary)
    seed_conn.commit()
    pid = get_project_summary_by_name(seed_conn, 1, "SomeProject")["project_summary_id"]

    res = client.post(
        "/resume/99999/projects",
        json={"project_summary_id": pid},
        headers=auth_headers,
    )
    assert res.status_code == 404


def test_add_project_invalid_id_returns_400(client, auth_headers, seed_conn):
    """Adding a project that doesn't exist returns 400."""
    summary = json.dumps({
        "project_name": "RealProject",
        "project_type": "code",
        "project_mode": "individual",
        "languages": [],
        "frameworks": [],
        "summary_text": "X",
        "metrics": {},
    })
    save_project_summary(seed_conn, 1, "RealProject", summary)
    seed_conn.commit()
    pid = get_project_summary_by_name(seed_conn, 1, "RealProject")["project_summary_id"]
    resume_id = create_resume_with_project(seed_conn, 1, "Resume", "RealProject", pid)

    res = client.post(
        f"/resume/{resume_id}/projects",
        json={"project_summary_id": 99999},
        headers=auth_headers,
    )
    assert res.status_code == 400


def test_add_project_requires_auth(client, seed_conn):
    """POST /resume/{id}/projects requires authentication."""
    summary = json.dumps({
        "project_name": "P",
        "project_type": "code",
        "project_mode": "individual",
        "languages": [],
        "frameworks": [],
        "summary_text": "x",
        "metrics": {},
    })
    save_project_summary(seed_conn, 1, "P", summary)
    seed_conn.commit()
    pid = get_project_summary_by_name(seed_conn, 1, "P")["project_summary_id"]
    resume_id = create_resume_with_project(seed_conn, 1, "R", "P", pid)

    res = client.post(
        f"/resume/{resume_id}/projects",
        json={"project_summary_id": pid},
    )
    assert res.status_code == 401
