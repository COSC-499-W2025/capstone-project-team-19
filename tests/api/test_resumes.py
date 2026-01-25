import json
import pytest
from src.db.resumes import insert_resume_snapshot

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