import json
from fastapi.testclient import TestClient
import pytest
from src.api.main import app
import src.db as db
from src.db.resumes import insert_resume_snapshot

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