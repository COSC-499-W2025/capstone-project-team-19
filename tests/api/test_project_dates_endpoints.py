import json
from datetime import datetime, timezone

import src.db as db
from src.db.project_summaries import save_project_summary, get_project_summary_by_name
from src.db.project_summaries import set_project_dates as db_set_project_dates


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_project(seed_conn, user_id: int, name: str, project_type: str = "code", project_mode: str = "individual") -> int:
    summary_json = json.dumps(
        {
            "project_name": name,
            "project_type": project_type,
            "project_mode": project_mode,
            "created_at": _iso_now(),
            "languages": ["Python"],
            "frameworks": [],
            "metrics": {"skills_detailed": [{"score": 0.5, "level": "Intermediate"}]},
        }
    )
    save_project_summary(seed_conn, user_id, name, summary_json)
    return get_project_summary_by_name(seed_conn, user_id, name)["project_summary_id"]


def test_get_project_dates_requires_auth(client):
    res = client.get("/projects/dates")
    assert res.status_code == 401


def test_get_project_dates_lists_projects(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    seed_conn.commit()

    _seed_project(seed_conn, user_id, "ProjectA")
    _seed_project(seed_conn, user_id, "ProjectB")

    res = client.get("/projects/dates", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert "projects" in body["data"]
    assert len(body["data"]["projects"]) == 2


def test_patch_project_dates_sets_manual_dates(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    seed_conn.commit()

    project_id = _seed_project(seed_conn, user_id, "ProjectA")

    res = client.patch(
        f"/projects/{project_id}/dates",
        json={"start_date": "2024-01-01", "end_date": "2024-12-31"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["project_summary_id"] == project_id
    assert data["source"] == "MANUAL"
    assert data["start_date"] == "2024-01-01"
    assert data["end_date"] == "2024-12-31"


def test_patch_project_dates_rejects_invalid_range(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    seed_conn.commit()

    project_id = _seed_project(seed_conn, user_id, "ProjectA")
    res = client.patch(
        f"/projects/{project_id}/dates",
        json={"start_date": "2024-12-31", "end_date": "2024-01-01"},
        headers=auth_headers,
    )
    assert res.status_code == 400


def test_delete_project_dates_clears_manual_overrides(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    seed_conn.commit()

    project_id = _seed_project(seed_conn, user_id, "ProjectA")

    # seed manual dates in DB
    db_set_project_dates(seed_conn, user_id, "ProjectA", "2024-01-01", "2024-12-31")

    res = client.delete(f"/projects/{project_id}/dates", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["project_summary_id"] == project_id
    assert data["manual_start_date"] is None
    assert data["manual_end_date"] is None
    assert data["source"] in ["AUTO", "MANUAL"]  # depends on auto duration availability


def test_post_project_dates_reset_clears_all_manual_overrides(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    seed_conn.commit()

    _seed_project(seed_conn, user_id, "ProjectA")
    _seed_project(seed_conn, user_id, "ProjectB")
    db_set_project_dates(seed_conn, user_id, "ProjectA", "2024-01-01", None)
    db_set_project_dates(seed_conn, user_id, "ProjectB", None, "2024-12-31")

    res = client.post("/projects/dates/reset", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["cleared_count"] == 2

