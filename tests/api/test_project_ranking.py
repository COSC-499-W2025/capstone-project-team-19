import json
from datetime import datetime, timezone

import src.db as db
from src.db.project_summaries import save_project_summary, get_project_summary_by_name


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_project(seed_conn, user_id: int, name: str, skill_score: float) -> int:
    summary_json = json.dumps(
        {
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
    )
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

