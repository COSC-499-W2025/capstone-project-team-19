import json
from fastapi.testclient import TestClient
import pytest
from src.api.main import app
import src.db as db
from src.db.resumes import insert_resume_snapshot
from src.db.project_summaries import save_project_summary, get_project_summary_by_name

client = TestClient(app)
@pytest.fixture
def setup_db(tmp_path, monkeypatch):
    """Fixture to set up database with schema and test user - uses TEST database"""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("APP_DB_PATH", str(db_path))
    
    conn = db.connect()
    db.init_schema(conn)
    conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    conn.commit()
    yield conn
    conn.close()

#TESTS
# All Resumes tests
def test_resumes_requires_user_header():
    res = client.get("/resume")
    assert res.status_code == 401

def test_resumes_with_user_header_returns_ok(setup_db):  
    res = client.get("/resume", headers={"X-User-Id": "1"})
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert "data" in body

def test_resumes_with_false_user():
    res = client.get("/resume", headers={"X-User-Id": "999999"})
    assert res.status_code == 404
    body = res.json()
    assert body["detail"] == "User not found"

def test_resumes_list_with_data(setup_db):
    """Test that GET /resume returns correct list structure with actual resumes"""

    resume_json1 = json.dumps({
        "projects": [{"project_name": "Project1"}],
        "aggregated_skills": {}
    })
    resume_json2 = json.dumps({
        "projects": [{"project_name": "Project2"}],
        "aggregated_skills": {}
    })
    
    resume_id1 = insert_resume_snapshot(setup_db, 1, "Resume 1", resume_json1)
    resume_id2 = insert_resume_snapshot(setup_db, 1, "Resume 2", resume_json2)
    setup_db.commit()
    
    res = client.get("/resume", headers={"X-User-Id": "1"})
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
def test_get_resume_by_id_requires_user_header():
    """Test that GET /resume/{id} requires X-User-Id header"""
    res = client.get("/resume/1")
    assert res.status_code == 401

def test_get_resume_by_id_with_false_user():
    """Test that GET /resume/{id} returns 404 for non-existent user"""
    res = client.get("/resume/1", headers={"X-User-Id": "999999"})
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

def test_get_resume_by_id_not_found(setup_db):
    """Test getting a resume that doesn't exist"""
    res = client.get("/resume/999", headers={"X-User-Id": "1"})
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

def test_get_resume_by_id_success(setup_db):
    """Test getting a resume that exists"""
    conn = db.connect()
    db.init_schema(conn)
    conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    conn.commit()
    
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
    resume_id = insert_resume_snapshot(conn, 1, "Test Resume", resume_json)
    conn.close()
    
    res = client.get(f"/resume/{resume_id}", headers={"X-User-Id": "1"})
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
def test_generate_resume_requires_user_header():
    """Test that POST /resume/generate requires X-User-Id header"""
    res = client.post("/resume/generate", json={"name": "Test"})
    assert res.status_code == 401


def test_generate_resume_with_false_user():
    """Test that POST /resume/generate returns 404 for non-existent user"""
    res = client.post("/resume/generate", json={"name": "Test"}, headers={"X-User-Id": "999999"})
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_generate_resume_no_projects_returns_error(setup_db):
    """Test that generating resume with no projects returns 400"""
    res = client.post(
        "/resume/generate",
        json={"name": "Empty Resume", "project_ids": []},
        headers={"X-User-Id": "1"}
    )
    assert res.status_code == 400
    assert "no valid projects" in res.json()["detail"].lower()


def test_generate_resume_invalid_project_ids_returns_error(setup_db):
    """Test that generating resume with invalid project IDs returns 400"""
    res = client.post(
        "/resume/generate",
        json={"name": "Bad Resume", "project_ids": [999, 1000]},
        headers={"X-User-Id": "1"}
    )
    assert res.status_code == 400
    assert "no valid projects" in res.json()["detail"].lower()


def test_generate_resume_with_project_ids_success(setup_db):
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
    save_project_summary(setup_db, 1, "TestProject", summary_json)
    project_id = get_project_summary_by_name(setup_db, 1, "TestProject")["project_summary_id"]

    res = client.post(
        "/resume/generate",
        json={"name": "My Resume", "project_ids": [project_id]},
        headers={"X-User-Id": "1"}
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


def test_generate_resume_without_project_ids_uses_top_ranked(setup_db):
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
        save_project_summary(setup_db, 1, f"Project{i}", summary_json)

    res = client.post(
        "/resume/generate",
        json={"name": "Auto Resume"},
        headers={"X-User-Id": "1"}
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True

    data = body["data"]
    assert data["name"] == "Auto Resume"
    assert len(data["projects"]) <= 5  # Max 5 projects


# POST /resume/{resume_id}/edit tests
def test_edit_resume_requires_user_header():
    """Test that POST /resume/{id}/edit requires X-User-Id header"""
    res = client.post("/resume/1/edit", json={
        "project_name": "Test",
        "scope": "resume_only"
    })
    assert res.status_code == 401


def test_edit_resume_not_found(setup_db):
    """Test editing a resume that doesn't exist"""
    res = client.post(
        "/resume/999/edit",
        json={"project_name": "Test", "scope": "resume_only"},
        headers={"X-User-Id": "1"}
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_edit_resume_project_not_found(setup_db):
    """Test editing a project that doesn't exist in the resume"""
    resume_json = json.dumps({
        "projects": [{"project_name": "ExistingProject"}],
        "aggregated_skills": {}
    })
    resume_id = insert_resume_snapshot(setup_db, 1, "Test Resume", resume_json)

    res = client.post(
        f"/resume/{resume_id}/edit",
        json={"project_name": "NonExistentProject", "scope": "resume_only"},
        headers={"X-User-Id": "1"}
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_edit_resume_resume_only_scope(setup_db):
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
    resume_id = insert_resume_snapshot(setup_db, 1, "Test Resume", resume_json)

    res = client.post(
        f"/resume/{resume_id}/edit",
        json={
            "project_name": "TestProject",
            "scope": "resume_only",
            "summary_text": "Updated summary",
            "display_name": "Custom Display Name"
        },
        headers={"X-User-Id": "1"}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True

    # Verify the rendered_text was updated (contains the new summary)
    data = body["data"]
    assert data["rendered_text"] is not None
    assert "Updated summary" in data["rendered_text"]
    assert "Custom Display Name" in data["rendered_text"]


def test_edit_resume_update_name(setup_db):
    """Test renaming a resume"""
    resume_json = json.dumps({
        "projects": [{"project_name": "TestProject"}],
        "aggregated_skills": {}
    })
    resume_id = insert_resume_snapshot(setup_db, 1, "Old Name", resume_json)

    res = client.post(
        f"/resume/{resume_id}/edit",
        json={
            "name": "New Name",
            "project_name": "TestProject",
            "scope": "resume_only"
        },
        headers={"X-User-Id": "1"}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["name"] == "New Name"


def test_edit_resume_contribution_bullets(setup_db):
    """Test editing contribution bullets"""
    resume_json = json.dumps({
        "projects": [{
            "project_name": "TestProject",
            "project_type": "code",
            "project_mode": "individual"
        }],
        "aggregated_skills": {}
    })
    resume_id = insert_resume_snapshot(setup_db, 1, "Test Resume", resume_json)

    bullets = ["Built feature X", "Improved performance by 50%"]
    res = client.post(
        f"/resume/{resume_id}/edit",
        json={
            "project_name": "TestProject",
            "scope": "resume_only",
            "contribution_bullets": bullets
        },
        headers={"X-User-Id": "1"}
    )
    assert res.status_code == 200

    # Verify the rendered_text contains the new bullets
    data = res.json()["data"]
    assert data["rendered_text"] is not None
    assert "Built feature X" in data["rendered_text"]
    assert "Improved performance by 50%" in data["rendered_text"]


def test_edit_resume_global_scope(setup_db):
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
    save_project_summary(setup_db, 1, "TestProject", summary_json)

    # Create resume with this project
    resume_json = json.dumps({
        "projects": [{
            "project_name": "TestProject",
            "project_type": "code",
            "summary_text": "Original"
        }],
        "aggregated_skills": {}
    })
    resume_id = insert_resume_snapshot(setup_db, 1, "Test Resume", resume_json)

    res = client.post(
        f"/resume/{resume_id}/edit",
        json={
            "project_name": "TestProject",
            "scope": "global",
            "summary_text": "Globally updated summary"
        },
        headers={"X-User-Id": "1"}
    )
    assert res.status_code == 200

    # Verify project_summaries was updated with manual_overrides
    project_row = get_project_summary_by_name(setup_db, 1, "TestProject")
    summary_dict = json.loads(project_row["summary_json"])
    assert summary_dict.get("manual_overrides", {}).get("summary_text") == "Globally updated summary"