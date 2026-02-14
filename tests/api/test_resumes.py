import json
import pytest
from src.db.resumes import insert_resume_snapshot
from src.db.project_summaries import save_project_summary, get_project_summary_by_name
from src.db.skill_preferences import get_user_skill_preferences

#TESTS
# All Resumes tests
def test_resumes_requires_user_header(client):
    res = client.get("/resume")
    assert res.status_code == 401

def test_resumes_with_user_header_returns_ok(client, auth_headers):  
    res = client.get("/resume", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert "data" in body

def test_resumes_with_false_user(client, auth_headers_nonexistent_user):
    res = client.get("/resume", headers=auth_headers_nonexistent_user)
    assert res.status_code == 404
    body = res.json()
    assert body["detail"] == "User not found"

def test_resumes_list_with_data(client, auth_headers, seed_conn):
    """Test that GET /resume returns correct list structure with actual resumes"""

    resume_json1 = json.dumps({
        "projects": [{"project_name": "Project1"}],
        "aggregated_skills": {}
    })
    resume_json2 = json.dumps({
        "projects": [{"project_name": "Project2"}],
        "aggregated_skills": {}
    })
    
    resume_id1 = insert_resume_snapshot(seed_conn, 1, "Resume 1", resume_json1)
    resume_id2 = insert_resume_snapshot(seed_conn, 1, "Resume 2", resume_json2)
    seed_conn.commit()
    
    res = client.get("/resume", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    
    assert "resumes" in body["data"]
    resumes = body["data"]["resumes"]
    assert isinstance(resumes, list)
    assert len(resumes) >= 2
    
    resume1 = next((r for r in resumes if r["id"] == resume_id1), None)
    assert resume1 is not None
    assert resume1["name"] == "Resume 1"
    assert "created_at" in resume1
    
    resume2 = next((r for r in resumes if r["id"] == resume_id2), None)
    assert resume2 is not None
    assert resume2["name"] == "Resume 2"

# Resume by ID tests
def test_get_resume_by_id_requires_user_header(client):
    """Test that GET /resume/{id} requires X-User-Id header"""
    res = client.get("/resume/1")
    assert res.status_code == 401

def test_get_resume_by_id_with_false_user(client, auth_headers_nonexistent_user):
    """Test that GET /resume/{id} returns 404 for non-existent user"""
    res = client.get("/resume/1", headers=auth_headers_nonexistent_user)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

def test_get_resume_by_id_not_found(client, auth_headers):
    """Test getting a resume that doesn't exist"""
    res = client.get("/resume/999", headers=auth_headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

def test_get_resume_by_id_success(client, auth_headers, seed_conn):
    """Test getting a resume that exists"""
    resume_json = json.dumps({
        "projects": [{
            "project_name": "TestProject",
            "project_type": "code",
            "languages": ["Python"],
            "skills": ["Backend Development"]
        }],
        "aggregated_skills": {
            "languages": ["Python"],
            "technical_skills": ["Backend Development"]
        }
    })
    resume_id = insert_resume_snapshot(seed_conn, 1, "Test Resume", resume_json)
    seed_conn.commit()
    
    res = client.get(f"/resume/{resume_id}", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["id"] == resume_id
    assert data["name"] == "Test Resume"
    assert len(data["projects"]) == 1
    assert data["projects"][0]["project_name"] == "TestProject"
    assert data["aggregated_skills"]["languages"] == ["Python"]

# POST /resume/generate tests
def test_generate_resume_requires_user_header(client):
    """Test that POST /resume/generate requires X-User-Id header"""
    res = client.post("/resume/generate", json={"name": "Test"})
    assert res.status_code == 401


def test_generate_resume_with_false_user(client, auth_headers_nonexistent_user):
    """Test that POST /resume/generate returns 404 for non-existent user"""
    res = client.post("/resume/generate", json={"name": "Test"}, headers=auth_headers_nonexistent_user)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_generate_resume_no_projects_returns_error(client, auth_headers):
    """Test that generating resume with no projects returns 400"""
    res = client.post(
        "/resume/generate",
        json={"name": "Empty Resume", "project_ids": []},
        headers=auth_headers
    )
    assert res.status_code == 400
    assert "no valid projects" in res.json()["detail"].lower()


def test_generate_resume_invalid_project_ids_returns_error(client, auth_headers):
    """Test that generating resume with invalid project IDs returns 400"""
    res = client.post(
        "/resume/generate",
        json={"name": "Bad Resume", "project_ids": [999, 1000]},
        headers=auth_headers
    )
    assert res.status_code == 400
    assert "no valid projects" in res.json()["detail"].lower()


def test_generate_resume_with_project_ids_success(client, auth_headers, seed_conn):
    """Test generating a resume with specific project IDs"""
    # Create project summaries
    summary_json = json.dumps({
        "project_name": "TestProject",
        "project_type": "code",
        "project_mode": "individual",
        "languages": ["Python", "JavaScript"],
        "frameworks": ["FastAPI"],
        "summary_text": "A test project",
        "metrics": {}
    })
    save_project_summary(seed_conn, 1, "TestProject", summary_json)
    seed_conn.commit()
    project_id = get_project_summary_by_name(seed_conn, 1, "TestProject")["project_summary_id"]

    res = client.post(
        "/resume/generate",
        json={"name": "My Resume", "project_ids": [project_id]},
        headers=auth_headers
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True

    data = body["data"]
    assert data["name"] == "My Resume"
    assert "id" in data
    assert len(data["projects"]) == 1
    assert data["projects"][0]["project_name"] == "TestProject"
    assert "Python" in data["aggregated_skills"]["languages"]


def test_generate_resume_without_project_ids_uses_top_ranked(client, auth_headers, seed_conn):
    """Test generating resume without project_ids uses top 5 ranked projects"""
    # Create multiple project summaries
    for i in range(3):
        summary_json = json.dumps({
            "project_name": f"Project{i}",
            "project_type": "code",
            "project_mode": "individual",
            "languages": ["Python"],
            "frameworks": [],
            "summary_text": f"Project {i} description",
            "metrics": {}
        })
        save_project_summary(seed_conn, 1, f"Project{i}", summary_json)
    seed_conn.commit()

    res = client.post(
        "/resume/generate",
        json={"name": "Auto Resume"},
        headers=auth_headers
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True

    data = body["data"]
    assert data["name"] == "Auto Resume"
    assert len(data["projects"]) <= 5  # Max 5 projects


# POST /resume/{resume_id}/edit tests
def test_edit_resume_requires_user_header(client):
    """Test that POST /resume/{id}/edit requires X-User-Id header"""
    res = client.post("/resume/1/edit", json={
        "project_name": "Test",
        "scope": "resume_only"
    })
    assert res.status_code == 401


def test_edit_resume_not_found(client, auth_headers):
    """Test editing a resume that doesn't exist"""
    res = client.post(
        "/resume/999/edit",
        json={"project_name": "Test", "scope": "resume_only"},
        headers=auth_headers
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_edit_resume_project_not_found(client, auth_headers, seed_conn):
    """Test editing a project that doesn't exist in the resume"""
    resume_json = json.dumps({
        "projects": [{"project_name": "ExistingProject"}],
        "aggregated_skills": {}
    })
    resume_id = insert_resume_snapshot(seed_conn, 1, "Test Resume", resume_json)
    seed_conn.commit()

    res = client.post(
        f"/resume/{resume_id}/edit",
        json={"project_name": "NonExistentProject", "scope": "resume_only"},
        headers=auth_headers
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_edit_resume_resume_only_scope(client, auth_headers, seed_conn):
    """Test editing a resume with resume_only scope"""
    resume_json = json.dumps({
        "projects": [{
            "project_name": "TestProject",
            "project_type": "code",
            "project_mode": "individual",
            "summary_text": "Original summary"
        }],
        "aggregated_skills": {}
    })
    resume_id = insert_resume_snapshot(seed_conn, 1, "Test Resume", resume_json)
    seed_conn.commit()

    res = client.post(
        f"/resume/{resume_id}/edit",
        json={
            "project_name": "TestProject",
            "scope": "resume_only",
            "summary_text": "Updated summary",
            "display_name": "Custom Display Name"
        },
        headers=auth_headers
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True

    # Verify the rendered_text was updated (contains the new summary)
    data = body["data"]
    assert data["rendered_text"] is not None
    assert "Updated summary" in data["rendered_text"]
    assert "Custom Display Name" in data["rendered_text"]


def test_edit_resume_update_name(client, auth_headers, seed_conn):
    """Test renaming a resume"""
    resume_json = json.dumps({
        "projects": [{"project_name": "TestProject"}],
        "aggregated_skills": {}
    })
    resume_id = insert_resume_snapshot(seed_conn, 1, "Old Name", resume_json)
    seed_conn.commit()

    res = client.post(
        f"/resume/{resume_id}/edit",
        json={
            "name": "New Name",
            "project_name": "TestProject",
            "scope": "resume_only"
        },
        headers=auth_headers
    )
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["name"] == "New Name"


def test_edit_resume_name_only(client, auth_headers, seed_conn):
    """Test renaming a resume without editing any project (name-only update)"""
    resume_json = json.dumps({
        "projects": [{"project_name": "TestProject"}],
        "aggregated_skills": {}
    })
    resume_id = insert_resume_snapshot(seed_conn, 1, "Original Name", resume_json)
    seed_conn.commit()

    # Only provide name, no project_name or scope
    res = client.post(
        f"/resume/{resume_id}/edit",
        json={"name": "Renamed Resume"},
        headers=auth_headers
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["name"] == "Renamed Resume"

def test_edit_resume_skill_preferences_without_project_name(client, auth_headers, seed_conn):
    """Skill preferences can be updated at resume scope without project_name."""
    resume_json = json.dumps({
        "projects": [{"project_name": "TestProject"}],
        "aggregated_skills": {}
    })
    resume_id = insert_resume_snapshot(seed_conn, 1, "Test Resume", resume_json)
    seed_conn.commit()

    res = client.post(
        f"/resume/{resume_id}/edit",
        json={
            "skill_preferences": [
                {"skill_name": "algorithms", "is_highlighted": False, "display_order": 2}
            ]
        },
        headers=auth_headers
    )
    assert res.status_code == 200

    prefs = get_user_skill_preferences(
        seed_conn, user_id=1, context="resume", context_id=resume_id
    )
    assert len(prefs) == 1
    assert prefs[0]["skill_name"] == "algorithms"
    assert prefs[0]["is_highlighted"] is False
    assert prefs[0]["display_order"] == 2


def test_edit_resume_contribution_bullets(client, auth_headers, seed_conn):
    """Test editing contribution bullets with replace mode (default)"""
    resume_json = json.dumps({
        "projects": [{
            "project_name": "TestProject",
            "project_type": "code",
            "project_mode": "individual"
        }],
        "aggregated_skills": {}
    })
    resume_id = insert_resume_snapshot(seed_conn, 1, "Test Resume", resume_json)
    seed_conn.commit()

    bullets = ["Built feature X", "Improved performance by 50%"]
    res = client.post(
        f"/resume/{resume_id}/edit",
        json={
            "project_name": "TestProject",
            "scope": "resume_only",
            "contribution_bullets": bullets
        },
        headers=auth_headers
    )
    assert res.status_code == 200

    # Verify the rendered_text contains the new bullets
    data = res.json()["data"]
    assert data["rendered_text"] is not None
    assert "Built feature X" in data["rendered_text"]
    assert "Improved performance by 50%" in data["rendered_text"]


def test_edit_resume_contribution_bullets_append_mode(client, auth_headers, seed_conn):
    """Test editing contribution bullets with append mode"""
    resume_json = json.dumps({
        "projects": [{
            "project_name": "TestProject",
            "project_type": "code",
            "project_mode": "individual",
            "contribution_bullets": ["Existing bullet 1", "Existing bullet 2"]
        }],
        "aggregated_skills": {}
    })
    resume_id = insert_resume_snapshot(seed_conn, 1, "Test Resume", resume_json)
    seed_conn.commit()

    new_bullets = ["New bullet 3", "New bullet 4"]
    res = client.post(
        f"/resume/{resume_id}/edit",
        json={
            "project_name": "TestProject",
            "scope": "resume_only",
            "contribution_bullets": new_bullets,
            "contribution_edit_mode": "append"
        },
        headers=auth_headers
    )
    assert res.status_code == 200

    # Verify the rendered_text contains both old and new bullets
    data = res.json()["data"]
    assert data["rendered_text"] is not None
    assert "Existing bullet 1" in data["rendered_text"]
    assert "Existing bullet 2" in data["rendered_text"]
    assert "New bullet 3" in data["rendered_text"]
    assert "New bullet 4" in data["rendered_text"]


def test_edit_resume_global_scope(client, auth_headers, seed_conn):
    """Test editing with global scope updates project_summaries"""
    # Create project summary first
    summary_json = json.dumps({
        "project_name": "TestProject",
        "project_type": "code",
        "project_mode": "individual",
        "languages": ["Python"],
        "summary_text": "Original",
        "metrics": {}
    })
    save_project_summary(seed_conn, 1, "TestProject", summary_json)
    seed_conn.commit()

    # Create resume with this project
    resume_json = json.dumps({
        "projects": [{
            "project_name": "TestProject",
            "project_type": "code",
            "summary_text": "Original"
        }],
        "aggregated_skills": {}
    })
    resume_id = insert_resume_snapshot(seed_conn, 1, "Test Resume", resume_json)
    seed_conn.commit()

    res = client.post(
        f"/resume/{resume_id}/edit",
        json={
            "project_name": "TestProject",
            "scope": "global",
            "summary_text": "Globally updated summary"
        },
        headers=auth_headers
    )
    assert res.status_code == 200

    # Verify project_summaries was updated with manual_overrides
    project_row = get_project_summary_by_name(seed_conn, 1, "TestProject")
    summary_dict = json.loads(project_row["summary_json"])
    assert summary_dict.get("manual_overrides", {}).get("summary_text") == "Globally updated summary"
