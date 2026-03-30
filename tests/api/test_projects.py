import json
from src.db.project_summaries import save_project_summary, get_project_summary_by_name
import src.db as db


def test_projects_requires_user_header(client):
    res = client.get("/projects")
    assert res.status_code == 401

def test_projects_with_user_header_returns_ok(client, auth_headers):
    conn = db.connect()
    conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    conn.commit()
    conn.close()
    
    res = client.get("/projects", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert "data" in body

def test_projects_with_false_user(client, auth_headers_nonexistent_user):
    res = client.get("/projects", headers=auth_headers_nonexistent_user)
    assert res.status_code == 404
    body = res.json()
    assert body["detail"] == "User not found"

def test_get_project_by_id_not_found(client, auth_headers):
    """Test getting a project that doesn't exist"""
    res = client.get("/projects/999", headers=auth_headers)
    assert res.status_code == 404
    body = res.json()
    assert "not found" in body.get("detail", "").lower()

def test_get_project_by_id_success(client, auth_headers):
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
    res = client.get(f"/projects/{project_id}", headers=auth_headers)

    assert res.status_code == 200
    data = res.json()["data"]

    assert data["project_summary_id"] == project_id
    assert data["project_name"] == "TestProject"
    assert data["project_type"] == "code"
    assert data["languages"] == ["Python"]
    assert data["summary_text"] == "A test project"

    conn.close()


def test_get_project_resolves_manual_override(client, auth_headers):
    """manual_overrides.summary_text should take precedence over base summary_text"""
    conn = db.connect()
    db.init_schema(conn)
    conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    conn.commit()

    summary_json = json.dumps({
        "project_name": "OverrideProject",
        "project_type": "code",
        "summary_text": "Original summary",
        "manual_overrides": {"summary_text": "Overridden summary"},
    })
    save_project_summary(conn, 1, "OverrideProject", summary_json)

    project_id = get_project_summary_by_name(conn, 1, "OverrideProject")["project_summary_id"]
    res = client.get(f"/projects/{project_id}", headers=auth_headers)

    assert res.status_code == 200
    assert res.json()["data"]["summary_text"] == "Overridden summary"
    conn.close()


def test_patch_project_summary_not_found(client, auth_headers):
    """PATCH /projects/{id}/summary returns 404 for unknown project"""
    res = client.patch("/projects/999/summary", json={"summary_text": "new"}, headers=auth_headers)
    assert res.status_code == 404


def test_patch_project_summary_updates_summary_text(client, auth_headers):
    """PATCH /projects/{id}/summary updates summary_text and returns updated project"""
    conn = db.connect()
    db.init_schema(conn)
    conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    conn.commit()

    summary_json = json.dumps({
        "project_name": "PatchProject",
        "project_type": "code",
        "summary_text": "Old summary",
    })
    save_project_summary(conn, 1, "PatchProject", summary_json)

    project_id = get_project_summary_by_name(conn, 1, "PatchProject")["project_summary_id"]
    res = client.patch(
        f"/projects/{project_id}/summary",
        json={"summary_text": "Updated summary"},
        headers=auth_headers,
    )

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["summary_text"] == "Updated summary"
    conn.close()


def test_patch_project_summary_updates_contribution_summary(client, auth_headers):
    """PATCH /projects/{id}/summary updates contribution_summary in contributions dict"""
    conn = db.connect()
    db.init_schema(conn)
    conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    conn.commit()

    summary_json = json.dumps({
        "project_name": "CollabProject",
        "project_type": "text",
        "project_mode": "collaborative",
        "contributions": {},
    })
    save_project_summary(conn, 1, "CollabProject", summary_json)

    project_id = get_project_summary_by_name(conn, 1, "CollabProject")["project_summary_id"]
    res = client.patch(
        f"/projects/{project_id}/summary",
        json={"contribution_summary": "I built the backend."},
        headers=auth_headers,
    )

    assert res.status_code == 200
    row = get_project_summary_by_name(conn, 1, "CollabProject")
    saved = json.loads(row["summary_json"])
    assert saved["contributions"]["manual_contribution_summary"] == "I built the backend."
    conn.close()