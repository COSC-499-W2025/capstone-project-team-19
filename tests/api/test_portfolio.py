import json
import pytest
from src.db.project_summaries import save_project_summary, get_project_summary_by_name
from src.db.skill_preferences import get_user_skill_preferences


def _make_summary_json(project_name, project_type="code", project_mode="individual", **extra):
    """Helper to build a valid summary_json string for seeding."""
    data = {
        "project_name": project_name,
        "project_type": project_type,
        "project_mode": project_mode,
        "languages": extra.get("languages", ["Python"]),
        "frameworks": extra.get("frameworks", []),
        "summary_text": extra.get("summary_text", f"Summary for {project_name}"),
        "skills": extra.get("skills", ["Backend Development"]),
        "metrics": extra.get("metrics", {}),
        "contributions": extra.get("contributions", {}),
    }
    data.update({k: v for k, v in extra.items() if k not in data})
    return json.dumps(data)


# ---------------------------------------------------------------------------
# POST /portfolio/generate
# ---------------------------------------------------------------------------

class TestPortfolioGenerate:

    def test_requires_auth(self, client):
        res = client.post("/portfolio/generate", json={"name": "My Portfolio"})
        assert res.status_code == 401

    def test_nonexistent_user(self, client, auth_headers_nonexistent_user):
        res = client.post(
            "/portfolio/generate",
            json={"name": "My Portfolio"},
            headers=auth_headers_nonexistent_user,
        )
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

    def test_no_projects_returns_400(self, client, auth_headers):
        res = client.post(
            "/portfolio/generate",
            json={"name": "Empty Portfolio"},
            headers=auth_headers,
        )
        assert res.status_code == 400
        assert "no projects" in res.json()["detail"].lower()

    def test_missing_name_returns_422(self, client, auth_headers):
        res = client.post(
            "/portfolio/generate",
            json={},
            headers=auth_headers,
        )
        assert res.status_code == 422

    def test_generate_single_project(self, client, auth_headers, seed_conn):
        save_project_summary(
            seed_conn, 1, "ProjectAlpha",
            _make_summary_json("ProjectAlpha", languages=["Python", "Go"]),
        )
        seed_conn.commit()

        res = client.post(
            "/portfolio/generate",
            json={"name": "My Portfolio"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True

        data = body["data"]
        assert len(data["projects"]) == 1

        proj = data["projects"][0]
        assert proj["project_name"] == "ProjectAlpha"
        assert proj["display_name"]  # should be non-empty
        assert isinstance(proj["score"], float)
        assert isinstance(proj["languages"], list)
        assert isinstance(proj["frameworks"], list)
        assert isinstance(proj["skills"], list)
        assert isinstance(proj["contribution_bullets"], list)

        assert data["rendered_text"] is not None
        assert "My Portfolio" in data["rendered_text"]

    def test_generate_multiple_projects(self, client, auth_headers, seed_conn):
        for i in range(3):
            save_project_summary(
                seed_conn, 1, f"Project{i}",
                _make_summary_json(f"Project{i}"),
            )
        seed_conn.commit()

        res = client.post(
            "/portfolio/generate",
            json={"name": "Full Portfolio"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert len(data["projects"]) == 3

        # Projects should be ordered by score (descending)
        scores = [p["score"] for p in data["projects"]]
        assert scores == sorted(scores, reverse=True)

    def test_generate_includes_text_project(self, client, auth_headers, seed_conn):
        save_project_summary(
            seed_conn, 1, "TextProject",
            _make_summary_json(
                "TextProject",
                project_type="text",
                languages=[],
                summary_text="A text-based project",
            ),
        )
        seed_conn.commit()

        res = client.post(
            "/portfolio/generate",
            json={"name": "Portfolio"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        proj = res.json()["data"]["projects"][0]
        assert proj["project_type"] == "text"
        assert proj["languages"] == []

    def test_generate_with_portfolio_overrides(self, client, auth_headers, seed_conn):
        """Verify that portfolio_overrides in summary_json are reflected."""
        summary = {
            "project_name": "OverrideProject",
            "project_type": "code",
            "project_mode": "individual",
            "languages": ["Rust"],
            "frameworks": [],
            "summary_text": "Original summary",
            "skills": [],
            "metrics": {},
            "portfolio_overrides": {
                "display_name": "Custom Display",
                "summary_text": "Overridden summary",
            },
        }
        save_project_summary(seed_conn, 1, "OverrideProject", json.dumps(summary))
        seed_conn.commit()

        res = client.post(
            "/portfolio/generate",
            json={"name": "Portfolio"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        proj = res.json()["data"]["projects"][0]
        assert proj["display_name"] == "Custom Display"
        assert proj["summary_text"] == "Overridden summary"


# ---------------------------------------------------------------------------
# POST /portfolio/edit
# ---------------------------------------------------------------------------

class TestPortfolioEdit:

    def test_requires_auth(self, client):
        res = client.post("/portfolio/edit", json={
            "project_summary_id": 1,
        })
        assert res.status_code == 401

    def test_project_not_found(self, client, auth_headers):
        res = client.post(
            "/portfolio/edit",
            json={"project_summary_id": 99999},
            headers=auth_headers,
        )
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

    def test_edit_portfolio_only_display_name(self, client, auth_headers, seed_conn):
        save_project_summary(
            seed_conn, 1, "EditProject",
            _make_summary_json("EditProject"),
        )
        seed_conn.commit()
        ps_id = get_project_summary_by_name(seed_conn, 1, "EditProject")["project_summary_id"]

        res = client.post(
            "/portfolio/edit",
            json={
                "project_summary_id": ps_id,
                "scope": "portfolio_only",
                "display_name": "Fancy Name",
            },
            headers=auth_headers,
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True

        # The portfolio should be regenerated with the override applied
        data = body["data"]
        assert len(data["projects"]) >= 1
        proj = next(p for p in data["projects"] if p["project_name"] == "EditProject")
        assert proj["display_name"] == "Fancy Name"

        # Verify portfolio_overrides stored in DB
        row = get_project_summary_by_name(seed_conn, 1, "EditProject")
        summary_dict = json.loads(row["summary_json"])
        assert summary_dict["portfolio_overrides"]["display_name"] == "Fancy Name"

    def test_edit_portfolio_only_summary_text(self, client, auth_headers, seed_conn):
        save_project_summary(
            seed_conn, 1, "SummaryProject",
            _make_summary_json("SummaryProject"),
        )
        seed_conn.commit()
        ps_id = get_project_summary_by_name(seed_conn, 1, "SummaryProject")["project_summary_id"]

        res = client.post(
            "/portfolio/edit",
            json={
                "project_summary_id": ps_id,
                "scope": "portfolio_only",
                "summary_text": "New portfolio summary",
            },
            headers=auth_headers,
        )
        assert res.status_code == 200

        row = get_project_summary_by_name(seed_conn, 1, "SummaryProject")
        summary_dict = json.loads(row["summary_json"])
        assert summary_dict["portfolio_overrides"]["summary_text"] == "New portfolio summary"

    def test_edit_portfolio_only_contribution_bullets(self, client, auth_headers, seed_conn):
        save_project_summary(
            seed_conn, 1, "BulletProject",
            _make_summary_json("BulletProject"),
        )
        seed_conn.commit()
        ps_id = get_project_summary_by_name(seed_conn, 1, "BulletProject")["project_summary_id"]

        bullets = ["Built the auth system", "Optimized queries"]
        res = client.post(
            "/portfolio/edit",
            json={
                "project_summary_id": ps_id,
                "scope": "portfolio_only",
                "contribution_bullets": bullets,
            },
            headers=auth_headers,
        )
        assert res.status_code == 200

        row = get_project_summary_by_name(seed_conn, 1, "BulletProject")
        summary_dict = json.loads(row["summary_json"])
        assert summary_dict["portfolio_overrides"]["contribution_bullets"] == bullets

    def test_edit_portfolio_skill_preferences(self, client, auth_headers, seed_conn):
        save_project_summary(
            seed_conn, 1, "SkillsProject",
            _make_summary_json("SkillsProject"),
        )
        seed_conn.commit()

        res = client.post(
            "/portfolio/edit",
            json={
                "project_name": "SkillsProject",
                "scope": "portfolio_only",
                "skill_preferences": [
                    {"skill_name": "algorithms", "is_highlighted": False, "display_order": 1},
                ],
            },
            headers=auth_headers,
        )
        assert res.status_code == 200

        row = get_project_summary_by_name(seed_conn, 1, "SkillsProject")
        prefs = get_user_skill_preferences(
            seed_conn, user_id=1, context="portfolio", project_key=row["project_key"]
        )
        assert len(prefs) == 1
        assert prefs[0]["skill_name"] == "algorithms"
        assert prefs[0]["is_highlighted"] is False
        assert prefs[0]["display_order"] == 1

    def test_edit_global_scope(self, client, auth_headers, seed_conn):
        save_project_summary(
            seed_conn, 1, "GlobalProject",
            _make_summary_json("GlobalProject"),
        )
        seed_conn.commit()
        ps_id = get_project_summary_by_name(seed_conn, 1, "GlobalProject")["project_summary_id"]

        res = client.post(
            "/portfolio/edit",
            json={
                "project_summary_id": ps_id,
                "scope": "global",
                "summary_text": "Global summary update",
                "display_name": "Global Display",
            },
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert res.json()["success"] is True

        # Verify manual_overrides were set in project_summaries
        row = get_project_summary_by_name(seed_conn, 1, "GlobalProject")
        summary_dict = json.loads(row["summary_json"])
        manual = summary_dict.get("manual_overrides", {})
        assert manual.get("summary_text") == "Global summary update"
        assert manual.get("display_name") == "Global Display"

        # portfolio_overrides for these fields should be cleared
        portfolio_ov = summary_dict.get("portfolio_overrides", {})
        assert "summary_text" not in portfolio_ov
        assert "display_name" not in portfolio_ov

    def test_edit_no_updates_returns_current_portfolio(self, client, auth_headers, seed_conn):
        """When no fields are provided, the endpoint should return the current portfolio."""
        save_project_summary(
            seed_conn, 1, "NoChangeProject",
            _make_summary_json("NoChangeProject"),
        )
        seed_conn.commit()
        ps_id = get_project_summary_by_name(seed_conn, 1, "NoChangeProject")["project_summary_id"]

        res = client.post(
            "/portfolio/edit",
            json={"project_summary_id": ps_id},
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert len(data["projects"]) >= 1

    def test_edit_clear_override_with_empty_string(self, client, auth_headers, seed_conn):
        """Setting a field to empty string should clear that override."""
        summary = {
            "project_name": "ClearProject",
            "project_type": "code",
            "project_mode": "individual",
            "languages": [],
            "frameworks": [],
            "summary_text": "Original",
            "skills": [],
            "metrics": {},
            "portfolio_overrides": {
                "display_name": "Old Override",
            },
        }
        save_project_summary(seed_conn, 1, "ClearProject", json.dumps(summary))
        seed_conn.commit()
        ps_id = get_project_summary_by_name(seed_conn, 1, "ClearProject")["project_summary_id"]

        res = client.post(
            "/portfolio/edit",
            json={
                "project_summary_id": ps_id,
                "scope": "portfolio_only",
                "display_name": "",
            },
            headers=auth_headers,
        )
        assert res.status_code == 200

        row = get_project_summary_by_name(seed_conn, 1, "ClearProject")
        summary_dict = json.loads(row["summary_json"])
        # The override should be removed (empty string clears it)
        portfolio_ov = summary_dict.get("portfolio_overrides", {})
        assert "display_name" not in portfolio_ov

    def test_edit_default_scope_is_portfolio_only(self, client, auth_headers, seed_conn):
        """When scope is not provided, it should default to portfolio_only."""
        save_project_summary(
            seed_conn, 1, "DefaultScope",
            _make_summary_json("DefaultScope"),
        )
        seed_conn.commit()
        ps_id = get_project_summary_by_name(seed_conn, 1, "DefaultScope")["project_summary_id"]

        res = client.post(
            "/portfolio/edit",
            json={
                "project_summary_id": ps_id,
                "display_name": "Scoped Name",
            },
            headers=auth_headers,
        )
        assert res.status_code == 200

        # Should be stored as portfolio_overrides, not manual_overrides
        row = get_project_summary_by_name(seed_conn, 1, "DefaultScope")
        summary_dict = json.loads(row["summary_json"])
        assert summary_dict.get("portfolio_overrides", {}).get("display_name") == "Scoped Name"
        assert "display_name" not in summary_dict.get("manual_overrides", {})
