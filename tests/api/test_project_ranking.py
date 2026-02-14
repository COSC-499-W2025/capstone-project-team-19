import json
from datetime import datetime, timezone

import src.db as db
from src.db.project_summaries import save_project_summary, get_project_summary_by_name


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_project(seed_conn, user_id: int, name: str, skill_score: float, summary_text: str | None = None) -> int:
    summary_data = {
        "project_name": name,
        "project_type": "code",
        "project_mode": "individual",
        "created_at": _iso_now(),
        "languages": ["Python"],
        "frameworks": [],
        "metrics": {
            "skills_detailed": [
                {"score": skill_score, "level": "Advanced"},
            ]
        },
    }
    if summary_text is not None:
        summary_data["summary_text"] = summary_text
    summary_json = json.dumps(summary_data)
    save_project_summary(seed_conn, user_id, name, summary_json)
    return get_project_summary_by_name(seed_conn, user_id, name)["project_summary_id"]


def test_get_projects_ranking_returns_ranked_list_and_scores(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)"
    )
    seed_conn.commit()

    a_id = _seed_project(seed_conn, user_id, "ProjectA", 1.0)
    b_id = _seed_project(seed_conn, user_id, "ProjectB", 0.1)
    assert a_id != b_id

    res = client.get("/projects/ranking", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    rankings = body["data"]["rankings"]
    assert len(rankings) == 2
    assert rankings[0]["project_name"] == "ProjectA"
    assert "score" in rankings[0]
    assert rankings[0]["manual_rank"] is None


def test_patch_project_ranking_sets_manual_rank(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)"
    )
    seed_conn.commit()

    _seed_project(seed_conn, user_id, "ProjectA", 1.0)
    b_id = _seed_project(seed_conn, user_id, "ProjectB", 0.1)

    # Force ProjectB to the top via manual rank
    res = client.patch(f"/projects/{b_id}/ranking", json={"rank": 1}, headers=auth_headers)
    assert res.status_code == 200

    res2 = client.get("/projects/ranking", headers=auth_headers)
    rankings = res2.json()["data"]["rankings"]
    assert rankings[0]["project_name"] == "ProjectB"
    assert rankings[0]["manual_rank"] == 1


def test_patch_project_ranking_move_down_reorders_properly(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)"
    )
    seed_conn.commit()

    a_id = _seed_project(seed_conn, user_id, "ProjectA", 1.0)
    b_id = _seed_project(seed_conn, user_id, "ProjectB", 0.9)
    c_id = _seed_project(seed_conn, user_id, "ProjectC", 0.8)

    # Set explicit initial order: A, B, C
    res = client.put("/projects/ranking", json={"project_ids": [a_id, b_id, c_id]}, headers=auth_headers)
    assert res.status_code == 200
    assert [r["project_name"] for r in res.json()["data"]["rankings"]] == ["ProjectA", "ProjectB", "ProjectC"]

    # Move A down to position 3 -> expected B, C, A
    res2 = client.patch(f"/projects/{a_id}/ranking", json={"rank": 3}, headers=auth_headers)
    assert res2.status_code == 200
    assert [r["project_name"] for r in res2.json()["data"]["rankings"]] == ["ProjectB", "ProjectC", "ProjectA"]
    assert [r["manual_rank"] for r in res2.json()["data"]["rankings"]] == [1, 2, 3]


def test_patch_project_ranking_requires_rank_field(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)"
    )
    seed_conn.commit()

    a_id = _seed_project(seed_conn, user_id, "ProjectA", 1.0)

    # Missing "rank" should be a validation error (prevents accidental clearing)
    res = client.patch(f"/projects/{a_id}/ranking", json={}, headers=auth_headers)
    assert res.status_code == 422


def test_put_projects_ranking_rejects_duplicate_ids(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)"
    )
    seed_conn.commit()

    a_id = _seed_project(seed_conn, user_id, "ProjectA", 1.0)
    b_id = _seed_project(seed_conn, user_id, "ProjectB", 0.1)

    res = client.put("/projects/ranking", json={"project_ids": [a_id, a_id]}, headers=auth_headers)
    assert res.status_code == 400


def test_put_projects_ranking_replaces_entire_order(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)"
    )
    seed_conn.commit()

    a_id = _seed_project(seed_conn, user_id, "ProjectA", 1.0)
    b_id = _seed_project(seed_conn, user_id, "ProjectB", 0.1)
    c_id = _seed_project(seed_conn, user_id, "ProjectC", 0.5)

    # Replace order explicitly
    res = client.put("/projects/ranking", json={"project_ids": [b_id, c_id, a_id]}, headers=auth_headers)
    assert res.status_code == 200
    rankings = res.json()["data"]["rankings"]
    assert [r["project_name"] for r in rankings] == ["ProjectB", "ProjectC", "ProjectA"]
    assert [r["manual_rank"] for r in rankings] == [1, 2, 3]


def test_post_projects_ranking_reset_clears_manual_ranks(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)"
    )
    seed_conn.commit()

    a_id = _seed_project(seed_conn, user_id, "ProjectA", 1.0)
    b_id = _seed_project(seed_conn, user_id, "ProjectB", 0.1)

    res = client.put("/projects/ranking", json={"project_ids": [b_id, a_id]}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["rankings"][0]["manual_rank"] == 1

    res2 = client.post("/projects/ranking/reset", headers=auth_headers)
    assert res2.status_code == 200
    rankings = res2.json()["data"]["rankings"]
    assert all(r["manual_rank"] is None for r in rankings)


def test_get_projects_top_returns_exactly_limit_items(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    seed_conn.commit()

    _seed_project(seed_conn, user_id, "ProjectA", 1.0)
    _seed_project(seed_conn, user_id, "ProjectB", 0.9)
    _seed_project(seed_conn, user_id, "ProjectC", 0.8)

    res = client.get("/projects/top?limit=3", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    top = body["data"]["topProjects"]
    assert len(top) == 3


def test_get_projects_top_sorted_like_ranking(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    seed_conn.commit()

    _seed_project(seed_conn, user_id, "ProjectA", 1.0)
    _seed_project(seed_conn, user_id, "ProjectB", 0.5)
    _seed_project(seed_conn, user_id, "ProjectC", 0.2)

    ranking_res = client.get("/projects/ranking", headers=auth_headers)
    top_res = client.get("/projects/top?limit=3", headers=auth_headers)
    assert top_res.status_code == 200

    rankings = ranking_res.json()["data"]["rankings"]
    top = top_res.json()["data"]["topProjects"]

    assert [t["title"] for t in top] == [r["project_name"] for r in rankings]
    assert [t["rankScore"] for t in top] == [r["score"] for r in rankings]
    assert all(t["rankScore"] >= t2["rankScore"] for t, t2 in zip(top, top[1:]))


def test_get_projects_top_response_keys_match_exactly(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    seed_conn.commit()

    _seed_project(seed_conn, user_id, "ProjectA", 1.0)

    res = client.get("/projects/top?limit=1", headers=auth_headers)
    assert res.status_code == 200
    top = res.json()["data"]["topProjects"]
    assert len(top) == 1
    item = top[0]
    assert set(item.keys()) == {"projectId", "title", "rankScore", "summarySnippet", "versionCount"}
    assert item["versionCount"] >= 0


def test_get_projects_top_includes_summary_snippet(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    seed_conn.commit()

    summary = "A web app for task management with React and FastAPI. Demonstrates full-stack development."
    _seed_project(seed_conn, user_id, "TaskApp", 0.9, summary_text=summary)

    res = client.get("/projects/top?limit=1", headers=auth_headers)
    assert res.status_code == 200
    item = res.json()["data"]["topProjects"][0]
    assert item["summarySnippet"] is not None
    assert "task management" in (item["summarySnippet"] or "").lower() or "web app" in (item["summarySnippet"] or "").lower()


def test_get_project_evolution_returns_structure(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    seed_conn.commit()

    pid = _seed_project(seed_conn, user_id, "EvolveProj", 0.8)

    res = client.get(f"/projects/{pid}/evolution", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["projectId"] == str(pid)
    assert data["title"] == "EvolveProj"
    assert "versions" in data
    assert isinstance(data["versions"], list)


def test_get_project_evolution_404_for_unknown(client, auth_headers):
    res = client.get("/projects/99999/evolution", headers=auth_headers)
    assert res.status_code == 404