"""Tests for DELETE /resume/{resume_id}/projects endpoint (remove project from resume)."""
import json
from src.db.resumes import insert_resume_snapshot, list_resumes, get_resume_snapshot
from src.menu.resume.helpers import recompute_aggregated_skills


# ============================================================================
# Helper Functions
# ============================================================================

def create_resume_with_projects(conn, user_id, name, project_entries):
    """Create a test resume with detailed project entries. Returns resume ID."""
    resume_json = json.dumps({
        "projects": project_entries,
        "aggregated_skills": recompute_aggregated_skills(project_entries),
    })
    resume_id = insert_resume_snapshot(conn, user_id, name, resume_json)
    conn.commit()
    return resume_id


def make_project_entry(name, languages=None, frameworks=None, skills=None):
    """Build a minimal project entry dict."""
    return {
        "project_name": name,
        "languages": languages or [],
        "frameworks": frameworks or [],
        "skills": skills or [],
    }


def assert_success(response, expected_status=200):
    assert response.status_code == expected_status
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    return body


# ============================================================================
# Tests
# ============================================================================

def test_remove_project_from_multi_project_resume(client, auth_headers, seed_conn):
    """Removing a project from a multi-project resume returns the updated resume."""
    entries = [
        make_project_entry("ProjectA", languages=["Python"], skills=["OOP"]),
        make_project_entry("ProjectB", languages=["JavaScript"], skills=["Testing"]),
    ]
    resume_id = create_resume_with_projects(seed_conn, 1, "MyResume", entries)

    res = client.delete(
        f"/resume/{resume_id}/projects?project_name=ProjectA",
        headers=auth_headers,
    )
    body = assert_success(res)

    # Should return updated resume with only ProjectB
    assert body["data"] is not None
    projects = body["data"]["projects"]
    project_names = [p["project_name"] for p in projects]
    assert "ProjectA" not in project_names
    assert "ProjectB" in project_names


def test_remove_last_project_deletes_resume(client, auth_headers, seed_conn):
    """Removing the only project from a resume deletes the resume entirely."""
    entries = [make_project_entry("OnlyProject")]
    resume_id = create_resume_with_projects(seed_conn, 1, "SingleResume", entries)

    # Verify resume exists
    assert any(r["id"] == resume_id for r in list_resumes(seed_conn, 1))

    res = client.delete(
        f"/resume/{resume_id}/projects?project_name=OnlyProject",
        headers=auth_headers,
    )
    body = assert_success(res)
    assert body["data"] is None  # Resume was deleted

    # Verify resume is gone
    assert not any(r["id"] == resume_id for r in list_resumes(seed_conn, 1))


def test_remove_project_not_in_resume_returns_404(client, auth_headers, seed_conn):
    """Removing a project that isn't in the resume returns 404 with specific message."""
    entries = [make_project_entry("ProjectA")]
    resume_id = create_resume_with_projects(seed_conn, 1, "MyResume", entries)

    res = client.delete(
        f"/resume/{resume_id}/projects?project_name=NonExistent",
        headers=auth_headers,
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Project not found in resume"


def test_remove_project_from_nonexistent_resume_returns_404(client, auth_headers):
    """Removing a project from a resume that doesn't exist returns 404 with specific message."""
    res = client.delete(
        "/resume/999/projects?project_name=Anything",
        headers=auth_headers,
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Resume not found"


def test_aggregated_skills_recomputed_after_removal(client, auth_headers, seed_conn):
    """After removal, aggregated_skills should only reflect remaining projects."""
    entries = [
        make_project_entry("ProjectA", languages=["Python"], skills=["OOP"]),
        make_project_entry("ProjectB", languages=["JavaScript"], frameworks=["React"], skills=["Testing"]),
    ]
    resume_id = create_resume_with_projects(seed_conn, 1, "SkillResume", entries)

    res = client.delete(
        f"/resume/{resume_id}/projects?project_name=ProjectA",
        headers=auth_headers,
    )
    body = assert_success(res)

    agg = body["data"]["aggregated_skills"]
    # Python and OOP came from ProjectA, should be gone
    assert "Python" not in agg["languages"]
    assert "OOP" not in agg["technical_skills"]
    # JavaScript, React, Testing came from ProjectB, should remain
    assert "JavaScript" in agg["languages"]
    assert "React" in agg["frameworks"]
    assert "Testing" in agg["technical_skills"]


def test_remove_project_does_not_affect_other_resumes(client, auth_headers, seed_conn):
    """Removing a project from one resume does not affect other resumes."""
    entries = [
        make_project_entry("SharedProject", languages=["Python"]),
        make_project_entry("OtherProject", languages=["Go"]),
    ]
    resume_id_1 = create_resume_with_projects(seed_conn, 1, "Resume1", entries)
    resume_id_2 = create_resume_with_projects(seed_conn, 1, "Resume2", entries)

    # Remove SharedProject from Resume1 only
    res = client.delete(
        f"/resume/{resume_id_1}/projects?project_name=SharedProject",
        headers=auth_headers,
    )
    assert_success(res)

    # Resume2 should still have both projects
    snap = get_resume_snapshot(seed_conn, 1, resume_id_2)
    data = json.loads(snap["resume_json"])
    project_names = [p["project_name"] for p in data["projects"]]
    assert "SharedProject" in project_names
    assert "OtherProject" in project_names


def test_remove_project_requires_auth(client):
    """DELETE /resume/{id}/projects requires authentication."""
    res = client.delete("/resume/1/projects?project_name=Foo")
    assert res.status_code == 401
