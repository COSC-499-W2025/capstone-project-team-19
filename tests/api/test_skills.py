import json

import pytest
import src.db as db
from src.db.projects import record_project_classification
from tests.api.conftest import seed_project

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

def test_skills_requires_user_header(client):
    """Test that skills endpoint requires X-User-Id header"""
    res = client.get("/skills")
    assert res.status_code == 401

def test_skills_with_user_header_returns_ok(client, auth_headers):
    """Test that skills endpoint returns 200 OK with valid user header"""

    res = client.get("/skills", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert "data" in body   

def test_skills_with_false_user(client, auth_headers_nonexistent_user):
    """Test that skills endpoint returns 404 for non-existent user"""
    res = client.get("/skills", headers=auth_headers_nonexistent_user)
    assert res.status_code == 404
    body = res.json()
    assert body["detail"] == "User not found"

def test_skills_with_data(client, auth_headers, seed_conn):
    """Test that skills endpoint returns correct data structure with actual skills"""
    import json
    from src.db.skills import insert_project_skill
    from src.db.projects import record_project_classifications
    
    # Record project classification in the seed_conn
    record_project_classifications(seed_conn, 1, "/tmp/test.zip", "test.zip", {"TestProject": "individual"})
    insert_project_skill(seed_conn, 1, "TestProject", "Python", "Advanced", 0.9, json.dumps([]))
    seed_conn.commit()
    
    res = client.get("/skills", headers=auth_headers)
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


def test_activity_by_date_returns_structure(client, auth_headers):
    """GET /skills/activity-by-date returns 200 with expected keys."""
    res = client.get("/skills/activity-by-date", headers=auth_headers)
    assert res.status_code == 200
    d = res.json()["data"]
    for k in ("row_labels", "col_labels", "matrix", "available_years", "projects_by_date"):
        assert k in d


def test_activity_by_date_with_project_dates(client, auth_headers, seed_conn):
    """With project dates set, activity-by-date includes project in projects_by_date."""
    seed_project(seed_conn, 1, "ProjA")
    db.set_project_dates(seed_conn, 1, "ProjA", "2024-01-01", "2024-01-07")
    seed_conn.commit()
    res = client.get("/skills/activity-by-date?year=2024", headers=auth_headers)
    assert res.status_code == 200
    d = res.json()["data"]
    assert d["projects_by_date"]
    assert any("ProjA" in projs for projs in d["projects_by_date"].values())