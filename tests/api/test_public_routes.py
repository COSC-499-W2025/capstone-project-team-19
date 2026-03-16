import json
from unittest.mock import patch

from tests.api.conftest import seed_project
from src.db.resumes import insert_resume_snapshot


def seed_resume(seed_conn, user_id: int, name: str, projects: list | None = None) -> int:
    """Insert a minimal resume snapshot and return its id."""
    payload = {
        "projects": projects or [],
        "aggregated_skills": {
            "languages": [],
            "frameworks": [],
            "technical_skills": [],
            "writing_skills": [],
        },
    }
    return insert_resume_snapshot(seed_conn, user_id, name, json.dumps(payload))

def seed_user(seed_conn, user_id: int, username: str) -> int:
    seed_conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (?, ?, NULL)",
        (user_id, username),
    )
    seed_conn.execute(
        "INSERT OR REPLACE INTO portfolio_settings(user_id, portfolio_public) VALUES (?, 1)",
        (user_id,),
    )
    seed_conn.commit()
    return user_id

# ── GET /public/{username}/projects ───────────────────────────────────────────

class TestPublicListProjects:
    def test_no_auth_required(self, client, seed_conn):
        """Public endpoint must not return 401 when no token is sent."""
        seed_user(seed_conn, 10, "johndoe")
        res = client.get("/public/johndoe/projects")
        assert res.status_code != 401
        assert res.status_code == 200

    def test_success_shape(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        res = client.get("/public/johndoe/projects")
        body = res.json()
        assert body["success"] is True
        assert "projects" in body["data"]
        assert body["error"] is None

    def test_empty_list_when_no_projects(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        res = client.get("/public/johndoe/projects")
        assert res.status_code == 200
        assert res.json()["data"]["projects"] == []

    def test_returns_only_target_users_projects(self, client, seed_conn):
        """Projects from another user must not appear in the response."""
        seed_user(seed_conn, 10, "johndoe")
        seed_user(seed_conn, 11, "janedoe")
        seed_project(seed_conn, 10, "Alpha", is_public=True)
        seed_project(seed_conn, 11, "Beta", is_public=True)

        res = client.get("/public/johndoe/projects")
        assert res.status_code == 200
        names = [p["project_name"] for p in res.json()["data"]["projects"]]
        assert "Alpha" in names
        assert "Beta" not in names

    def test_project_list_item_fields(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        seed_project(seed_conn, 10, "Alpha", is_public=True)

        res = client.get("/public/johndoe/projects")
        item = res.json()["data"]["projects"][0]
        assert "project_summary_id" in item
        assert "project_name" in item
        assert item["project_name"] == "Alpha"

    def test_unknown_username_returns_404(self, client):
        res = client.get("/public/nobody/projects")
        assert res.status_code == 404
        assert res.json()["detail"] == "User not found"

# ── GET /public/{username}/projects/{project_id} ──────────────────────────────

class TestPublicGetProject:
    def test_no_auth_required(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        pid = seed_project(seed_conn, 10, "Alpha", is_public=True)
        res = client.get(f"/public/johndoe/projects/{pid}")
        assert res.status_code != 401
        assert res.status_code == 200

    def test_returns_project_detail(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        pid = seed_project(
            seed_conn, 10, "Alpha",
            languages=["Python"],
            summary_text="A test summary",
            is_public=True,
        )
        res = client.get(f"/public/johndoe/projects/{pid}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["project_summary_id"] == pid
        assert data["project_name"] == "Alpha"
        assert data["summary_text"] == "A test summary"
        assert "Python" in data["languages"]

    def test_success_shape(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        pid = seed_project(seed_conn, 10, "Alpha", is_public=True)
        body = client.get(f"/public/johndoe/projects/{pid}").json()
        assert body["success"] is True
        assert body["error"] is None
        assert "data" in body

    def test_unknown_username_returns_404(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        pid = seed_project(seed_conn, 10, "Alpha")
        res = client.get(f"/public/nobody/projects/{pid}")
        assert res.status_code == 404
        assert res.json()["detail"] == "User not found"

    def test_nonexistent_project_id_returns_404(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        res = client.get("/public/johndoe/projects/99999")
        assert res.status_code == 404
        assert res.json()["detail"] == "Project not found"

    def test_another_users_project_returns_404(self, client, seed_conn):
        """Requesting johndoe's URL with janedoe's project_id must 404."""
        seed_user(seed_conn, 10, "johndoe")
        seed_user(seed_conn, 11, "janedoe")
        other_pid = seed_project(seed_conn, 11, "BetaProject")

        res = client.get(f"/public/johndoe/projects/{other_pid}")
        assert res.status_code == 404

# ── GET /public/{username}/projects/{project_id}/thumbnail ────────────────────

class TestPublicGetThumbnail:
    def test_no_thumbnail_returns_404(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        pid = seed_project(seed_conn, 10, "Alpha")
        res = client.get(f"/public/johndoe/projects/{pid}/thumbnail")
        assert res.status_code == 404

    def test_unknown_username_returns_404(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        pid = seed_project(seed_conn, 10, "Alpha")
        res = client.get(f"/public/nobody/projects/{pid}/thumbnail")
        assert res.status_code == 404
        assert res.json()["detail"] == "User not found"

    def test_returns_image_when_thumbnail_exists(self, client, seed_conn, tmp_path):
        seed_user(seed_conn, 10, "johndoe")
        pid = seed_project(seed_conn, 10, "Alpha", is_public=True)

        fake_png = tmp_path / "thumb.png"
        fake_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)  # minimal PNG header

        with patch("src.api.routes.public.get_thumbnail", return_value=str(fake_png)):
            res = client.get(f"/public/johndoe/projects/{pid}/thumbnail")

        assert res.status_code == 200
        assert res.headers["content-type"].startswith("image/png")

    def test_no_auth_required_on_thumbnail(self, client, seed_conn, tmp_path):
        seed_user(seed_conn, 10, "johndoe")
        pid = seed_project(seed_conn, 10, "Alpha")

        fake_png = tmp_path / "thumb.png"
        fake_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)

        with patch("src.api.routes.public.get_thumbnail", return_value=str(fake_png)):
            res = client.get(f"/public/johndoe/projects/{pid}/thumbnail")

        assert res.status_code != 401


# ── GET /public/{username}/ranking ────────────────────────────────────────────

class TestPublicGetRanking:
    def test_no_auth_required(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        res = client.get("/public/johndoe/ranking")
        assert res.status_code != 401
        assert res.status_code == 200

    def test_success_shape(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        body = client.get("/public/johndoe/ranking").json()
        assert body["success"] is True
        assert "rankings" in body["data"]
        assert body["error"] is None

    def test_empty_ranking_for_user_with_no_projects(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        res = client.get("/public/johndoe/ranking")
        assert res.json()["data"]["rankings"] == []

    def test_ranking_contains_only_target_users_projects(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        seed_user(seed_conn, 11, "janedoe")
        seed_project(seed_conn, 10, "Alpha", is_public=True)
        seed_project(seed_conn, 10, "Beta", is_public=True)
        seed_project(seed_conn, 11, "Gamma", is_public=True)

        res = client.get("/public/johndoe/ranking")
        names = [r["project_name"] for r in res.json()["data"]["rankings"]]
        assert "Alpha" in names
        assert "Beta" in names
        assert "Gamma" not in names

    def test_ranking_item_has_required_fields(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        seed_project(seed_conn, 10, "Alpha", is_public=True)

        item = client.get("/public/johndoe/ranking").json()["data"]["rankings"][0]
        assert "rank" in item
        assert "project_summary_id" in item
        assert "project_name" in item

    def test_rank_field_is_sequential(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        seed_project(seed_conn, 10, "Alpha", is_public=True)
        seed_project(seed_conn, 10, "Beta", is_public=True)

        rankings = client.get("/public/johndoe/ranking").json()["data"]["rankings"]
        ranks = [r["rank"] for r in rankings]
        assert ranks == sorted(ranks)
        assert ranks[0] == 1

    def test_unknown_username_returns_404(self, client):
        res = client.get("/public/nobody/ranking")
        assert res.status_code == 404
        assert res.json()["detail"] == "User not found"

# ── GET /public/{username}/skills ─────────────────────────────────────────────

class TestPublicGetSkills:
    def test_no_auth_required(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        res = client.get("/public/johndoe/skills")
        assert res.status_code != 401
        assert res.status_code == 200

    def test_success_shape(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        body = client.get("/public/johndoe/skills").json()
        assert body["success"] is True
        assert "skills" in body["data"]
        assert body["error"] is None

    def test_empty_skills_for_new_user(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        res = client.get("/public/johndoe/skills")
        assert res.json()["data"]["skills"] == []

    def test_unknown_username_returns_404(self, client):
        res = client.get("/public/nobody/skills")
        assert res.status_code == 404
        assert res.json()["detail"] == "User not found"

# ── GET /public/{username}/skills/timeline ────────────────────────────────────

class TestPublicGetSkillsTimeline:
    def test_no_auth_required(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        res = client.get("/public/johndoe/skills/timeline")
        assert res.status_code != 401
        assert res.status_code == 200

    def test_success_shape(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        body = client.get("/public/johndoe/skills/timeline").json()
        assert body["success"] is True
        assert body["error"] is None

    def test_timeline_data_fields(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        data = client.get("/public/johndoe/skills/timeline").json()["data"]
        assert "dated" in data
        assert "undated" in data
        assert "current_totals" in data
        assert "summary" in data

    def test_unknown_username_returns_404(self, client):
        res = client.get("/public/nobody/skills/timeline")
        assert res.status_code == 404
        assert res.json()["detail"] == "User not found"


# ── GET /public/{username}/resumes ────────────────────────────────────────────

class TestPublicListResumes:
    def test_no_auth_required(self, client, seed_conn):
        """Public endpoint must not return 401 when no token is sent."""
        seed_user(seed_conn, 10, "johndoe")
        res = client.get("/public/johndoe/resumes")
        assert res.status_code != 401
        assert res.status_code == 200

    def test_success_shape(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        body = client.get("/public/johndoe/resumes").json()
        assert body["success"] is True
        assert "resumes" in body["data"]
        assert body["error"] is None

    def test_empty_list_when_no_resumes(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        res = client.get("/public/johndoe/resumes")
        assert res.status_code == 200
        assert res.json()["data"]["resumes"] == []

    def test_returns_only_target_users_resumes(self, client, seed_conn):
        """Resumes from another user must not appear in the response."""
        seed_user(seed_conn, 10, "johndoe")
        seed_user(seed_conn, 11, "janedoe")
        seed_resume(seed_conn, 10, "My Resume")
        seed_resume(seed_conn, 11, "Other Resume")

        res = client.get("/public/johndoe/resumes")
        assert res.status_code == 200
        names = [r["name"] for r in res.json()["data"]["resumes"]]
        assert "My Resume" in names
        assert "Other Resume" not in names

    def test_resume_list_item_fields(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        seed_resume(seed_conn, 10, "My Resume")

        item = client.get("/public/johndoe/resumes").json()["data"]["resumes"][0]
        assert "id" in item
        assert "name" in item
        assert item["name"] == "My Resume"

    def test_unknown_username_returns_404(self, client):
        res = client.get("/public/nobody/resumes")
        assert res.status_code == 404
        assert res.json()["detail"] == "User not found"


# ── GET /public/{username}/resumes/{resume_id} ────────────────────────────────

class TestPublicGetResume:
    def test_no_auth_required(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        rid = seed_resume(seed_conn, 10, "My Resume")
        res = client.get(f"/public/johndoe/resumes/{rid}")
        assert res.status_code != 401
        assert res.status_code == 200

    def test_success_shape(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        rid = seed_resume(seed_conn, 10, "My Resume")
        body = client.get(f"/public/johndoe/resumes/{rid}").json()
        assert body["success"] is True
        assert body["error"] is None
        assert "data" in body

    def test_returns_resume_detail(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        projects = [
            {
                "project_name": "Alpha",
                "project_type": "code",
                "project_mode": "individual",
                "languages": ["Python"],
                "frameworks": [],
                "summary_text": "A test project",
                "skills": [],
                "contribution_bullets": [],
                "activities": [],
                "key_role": None,
                "text_type": None,
                "contribution_percent": None,
                "start_date": None,
                "end_date": None,
            }
        ]
        rid = seed_resume(seed_conn, 10, "My Resume", projects=projects)
        data = client.get(f"/public/johndoe/resumes/{rid}").json()["data"]

        assert data["id"] == rid
        assert data["name"] == "My Resume"
        assert len(data["projects"]) == 1
        assert data["projects"][0]["project_name"] == "Alpha"
        assert "aggregated_skills" in data

    def test_unknown_username_returns_404(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        rid = seed_resume(seed_conn, 10, "My Resume")
        res = client.get(f"/public/nobody/resumes/{rid}")
        assert res.status_code == 404
        assert res.json()["detail"] == "User not found"

    def test_nonexistent_resume_id_returns_404(self, client, seed_conn):
        seed_user(seed_conn, 10, "johndoe")
        res = client.get("/public/johndoe/resumes/99999")
        assert res.status_code == 404
        assert res.json()["detail"] == "Resume not found"

    def test_another_users_resume_returns_404(self, client, seed_conn):
        """Requesting johndoe's URL with janedoe's resume_id must 404."""
        seed_user(seed_conn, 10, "johndoe")
        seed_user(seed_conn, 11, "janedoe")
        other_rid = seed_resume(seed_conn, 11, "Private Resume")

        res = client.get(f"/public/johndoe/resumes/{other_rid}")
        assert res.status_code == 404


# ── Cross-cutting: no write endpoints on public router ────────────────────────

class TestPublicRouterIsReadOnly:
    def test_no_post_to_projects(self, client, seed_conn):
        """There must be no POST /public/{username}/projects endpoint."""
        seed_user(seed_conn, 10, "johndoe")
        res = client.post("/public/johndoe/projects", json={})
        assert res.status_code == 405  # Method Not Allowed

    def test_no_delete_to_project(self, client, seed_conn):
        """There must be no DELETE /public/{username}/projects/{id} endpoint."""
        seed_user(seed_conn, 10, "johndoe")
        pid = seed_project(seed_conn, 10, "Alpha")
        res = client.delete(f"/public/johndoe/projects/{pid}")
        assert res.status_code == 405

    def test_no_put_to_ranking(self, client, seed_conn):
        """There must be no PUT /public/{username}/ranking endpoint."""
        seed_user(seed_conn, 10, "johndoe")
        res = client.put("/public/johndoe/ranking", json={"project_ids": []})
        assert res.status_code == 405
