from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_projects_requires_user_header():
    res = client.get("/projects")
    assert res.status_code == 401

def test_projects_with_user_header_returns_ok():
    res = client.get("/projects", headers={"X-User-Id": "1"})
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert "data" in body