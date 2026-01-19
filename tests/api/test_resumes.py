import json
from fastapi.testclient import TestClient
import pytest
from src.api.main import app
import src.db as db
from src.db.resumes import insert_resume_snapshot

client = TestClient(app)
@pytest.fixture
def setup_db():
    """Fixture to set up database with schema and test user"""
    conn = db.connect()
    db.init_schema(conn)
    conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    conn.commit()
    yield conn
    conn.close()

#TESTS
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
    
    # Create a test resume
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