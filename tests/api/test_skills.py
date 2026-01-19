from fastapi.testclient import TestClient
import pytest
from src.api.main import app
import src.db as db
from src.db.projects import record_project_classification


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

def test_skills_requires_user_header():
    """Test that skills endpoint requires X-User-Id header"""
    res = client.get("/skills")
    assert res.status_code == 401

def test_skills_with_user_header_returns_ok(setup_db):
    """Test that skills endpoint returns 200 OK with valid user header"""

    res = client.get("/skills", headers={"X-User-Id": "1"})
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert "data" in body   

def test_skills_with_false_user():
    """Test that skills endpoint returns 404 for non-existent user"""
    res = client.get("/skills", headers={"X-User-Id": "999999"})
    assert res.status_code == 404
    body = res.json()
    assert body["detail"] == "User not found"

def test_skills_with_data(setup_db):
    """Test that skills endpoint returns correct data structure with actual skills"""
    import json
    from src.db.skills import insert_project_skill
    
    record_project_classification(setup_db, 1, "/tmp/test.zip", "test.zip", "TestProject", "individual")
    insert_project_skill(setup_db, 1, "TestProject", "Python", "Advanced", 0.9, json.dumps([]))
    setup_db.commit()
    
    res = client.get("/skills", headers={"X-User-Id": "1"})
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    skills = body["data"]["skills"]
    
    assert len(skills) > 0
    skill = skills[0]
    assert "skill_name" in skill
    assert "level" in skill
    assert "score" in skill
    assert "project_name" in skill
    assert skill["skill_name"] == "Python"
    assert skill["level"] == "Advanced"
    assert skill["score"] == 0.9