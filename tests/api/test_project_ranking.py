import json
from datetime import datetime, timezone

import pytest
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


# ---------------------------------------------------------------------------
# Enriched evolution tests (file diffs, skill progression, metrics)
# ---------------------------------------------------------------------------

def _seed_two_versions(seed_conn, user_id, project_name):
    """Create a project with two versions, version_files, version_skills, and version_summaries."""
    from src.db.project_summaries import save_project_summary, get_project_summary_by_name

    pk_row = seed_conn.execute(
        "SELECT project_key FROM projects WHERE user_id = ? AND display_name = ?",
        (user_id, project_name),
    ).fetchone()
    if pk_row:
        pk = pk_row[0]
    else:
        cur = seed_conn.execute(
            "INSERT INTO projects(user_id, display_name, classification, project_type) VALUES (?, ?, 'individual', 'code')",
            (user_id, project_name),
        )
        pk = cur.lastrowid
    seed_conn.commit()

    # version 1
    cur1 = seed_conn.execute(
        "INSERT INTO project_versions(project_key, upload_id, fingerprint_strict, fingerprint_loose, created_at) VALUES (?, 1, 'fp1', 'fl1', '2025-01-01T00:00:00')",
        (pk,),
    )
    vk1 = cur1.lastrowid

    seed_conn.executemany(
        "INSERT INTO version_files(version_key, relpath, file_hash) VALUES (?, ?, ?)",
        [(vk1, "src/main.py", "aaa"), (vk1, "src/util.py", "bbb")],
    )
    seed_conn.execute(
        "INSERT OR REPLACE INTO version_summaries(version_key, summary_text, lines_added, lines_deleted, languages_json, frameworks_json, avg_complexity, total_files) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (vk1, "Initial version", 100, 10, '["Python"]', '["FastAPI"]', 2.5, 2),
    )
    seed_conn.executemany(
        "INSERT OR REPLACE INTO version_skills(version_key, skill_name, level, score) VALUES (?, ?, ?, ?)",
        [(vk1, "Python", "intermediate", 0.5), (vk1, "OOP", "beginner", 0.3)],
    )

    # version 2
    cur2 = seed_conn.execute(
        "INSERT INTO project_versions(project_key, upload_id, fingerprint_strict, fingerprint_loose, created_at) VALUES (?, 2, 'fp2', 'fl2', '2025-02-01T00:00:00')",
        (pk,),
    )
    vk2 = cur2.lastrowid

    seed_conn.executemany(
        "INSERT INTO version_files(version_key, relpath, file_hash) VALUES (?, ?, ?)",
        [
            (vk2, "src/main.py", "aaa_changed"),  # modified
            (vk2, "src/util.py", "bbb"),           # unchanged
            (vk2, "src/tests.py", "ccc"),           # added
        ],
    )
    seed_conn.execute(
        "INSERT OR REPLACE INTO version_summaries(version_key, summary_text, lines_added, lines_deleted, languages_json, frameworks_json, avg_complexity, total_files) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (vk2, "Added tests and refactored", 250, 30, '["Python"]', '["FastAPI", "pytest"]', 3.1, 3),
    )
    seed_conn.executemany(
        "INSERT OR REPLACE INTO version_skills(version_key, skill_name, level, score) VALUES (?, ?, ?, ?)",
        [(vk2, "Python", "advanced", 0.8), (vk2, "Testing", "beginner", 0.3)],
    )

    # project summary so the endpoint can find the project
    summary_json = json.dumps({
        "project_name": project_name,
        "project_type": "code",
        "project_mode": "individual",
        "created_at": _iso_now(),
        "languages": ["Python"],
        "frameworks": ["FastAPI", "pytest"],
        "metrics": {"skills_detailed": [{"score": 0.8, "level": "Advanced"}]},
    })
    save_project_summary(seed_conn, user_id, project_name, summary_json)
    seed_conn.commit()

    pid = get_project_summary_by_name(seed_conn, user_id, project_name)["project_summary_id"]
    return pid, vk1, vk2


def test_evolution_file_diff_between_versions(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    seed_conn.commit()

    pid, vk1, vk2 = _seed_two_versions(seed_conn, user_id, "FileDiffEvol")

    res = client.get(f"/projects/{pid}/evolution", headers=auth_headers)
    assert res.status_code == 200
    versions = res.json()["data"]["versions"]
    assert len(versions) == 2

    v1, v2 = versions[0], versions[1]

    # First version has no file diff (no predecessor)
    assert v1["diff"] is None or v1.get("diff", {}).get("files") is None

    # Second version has file diff
    assert v2["diff"] is not None
    files = v2["diff"]["files"]
    assert "src/tests.py" in files["filesAdded"]
    assert "src/main.py" in files["filesModified"]
    assert files["filesRemoved"] == []
    assert files["unchangedCount"] == 1


def test_evolution_skill_progression(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    seed_conn.commit()

    pid, vk1, vk2 = _seed_two_versions(seed_conn, user_id, "SkillProgEvol")

    res = client.get(f"/projects/{pid}/evolution", headers=auth_headers)
    assert res.status_code == 200
    versions = res.json()["data"]["versions"]
    v1, v2 = versions[0], versions[1]

    # First version: no progression (no predecessor)
    assert v1["skillProgression"] is None

    # Second version: Python improved, OOP removed, Testing added
    sp = v2["skillProgression"]
    assert sp is not None
    new_names = [s["skill_name"] for s in sp["newSkills"]]
    assert "Testing" in new_names

    improved_names = [s["skill_name"] for s in sp["improvedSkills"]]
    assert "Python" in improved_names

    removed_names = [s["skill_name"] for s in sp["removedSkills"]]
    assert "OOP" in removed_names


def test_evolution_enriched_metrics(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    seed_conn.commit()

    pid, vk1, vk2 = _seed_two_versions(seed_conn, user_id, "MetricsEvol")

    res = client.get(f"/projects/{pid}/evolution", headers=auth_headers)
    assert res.status_code == 200
    versions = res.json()["data"]["versions"]

    v1 = versions[0]
    assert v1["languages"] == ["Python"]
    assert v1["frameworks"] == ["FastAPI"]
    assert v1["avgComplexity"] == pytest.approx(2.5)
    assert v1["totalFiles"] == 2

    v2 = versions[1]
    assert v2["languages"] == ["Python"]
    assert "pytest" in v2["frameworks"]
    assert v2["avgComplexity"] == pytest.approx(3.1)
    assert v2["totalFiles"] == 3


def test_evolution_single_version_has_no_diff(client, auth_headers, seed_conn):
    user_id = 1
    seed_conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    seed_conn.commit()

    pid = _seed_project(seed_conn, user_id, "SingleVerEvol", 0.7)

    res = client.get(f"/projects/{pid}/evolution", headers=auth_headers)
    assert res.status_code == 200
    versions = res.json()["data"]["versions"]
    for v in versions:
        assert v.get("diff") is None or v["diff"].get("files") is None
        assert v.get("skillProgression") is None