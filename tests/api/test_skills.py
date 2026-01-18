from fastapi.testclient import TestClient
from src.api.main import app
import src.db as db

client = TestClient(app)

def test_skills_requires_user_header():
    """Test that skills endpoint requires X-User-Id header"""
    res = client.get("/skills")
    assert res.status_code == 401

def test_skills_with_user_header_returns_ok():
    """Test that skills endpoint returns 200 OK with valid user header"""
    conn = db.connect()
    conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    conn.commit()
    conn.close()
    
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
