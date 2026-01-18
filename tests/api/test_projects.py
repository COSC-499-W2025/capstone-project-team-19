import json
from fastapi.testclient import TestClient
from src.db.project_summaries import save_project_summary, get_project_summary_by_name
from src.api.main import app
import src.db as db

client = TestClient(app)

def test_projects_requires_user_header():
    res = client.get("/projects")
    assert res.status_code == 401

def test_projects_with_user_header_returns_ok():
    conn = db.connect()
    conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    conn.commit()
    conn.close()
    
    res = client.get("/projects", headers={"X-User-Id": "1"})
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert "data" in body

def test_projects_with_false_user():
    res = client.get("/projects", headers={"X-User-Id": "100"})
    assert res.status_code == 404
    body = res.json()
    assert body["detail"] == "User not found"

def test_get_project_by_id_not_found():
    """Test getting a project that doesn't exist"""
    res = client.get("/projects/999", headers={"X-User-Id": "1"})
    assert res.status_code == 404
    body = res.json()
    assert body["success"] is False or "not found" in body.get("detail", "").lower()

def test_get_project_by_id_success():
    """Test getting a project with flattened fields"""
    conn = db.connect()
    db.init_schema(conn)
    conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    conn.commit()
    
    summary_json = json.dumps({
        "project_name": "TestProject",
        "project_type": "code",
        "languages": ["Python"],
        "summary_text": "A test project"
    })
    save_project_summary(conn, 1, "TestProject", summary_json)
    
    project_id = get_project_summary_by_name(conn, 1, "TestProject")["project_summary_id"]
    res = client.get(f"/projects/{project_id}", headers={"X-User-Id": "1"})
    
    assert res.status_code == 200
    data = res.json()["data"]
    
    assert data["project_summary_id"] == project_id
    assert data["project_name"] == "TestProject"
    assert data["project_type"] == "code"
    assert data["languages"] == ["Python"]  
    assert data["summary_text"] == "A test project" 
    
    conn.close()