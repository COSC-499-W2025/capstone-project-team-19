"""
tests/api/test_skill_preferences_api.py

Tests for the skill preferences (highlighting) API endpoints.
"""

import pytest


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def user_with_skills(seed_conn, consent_user_id_1):
    """Create a user with some project skills for testing."""
    # First insert project classifications (required by get_skill_events INNER JOIN)
    projects = [
        (consent_user_id_1, "/tmp/test.zip", "test.zip", "project1", "individual", "code", "2024-01-01"),
        (consent_user_id_1, "/tmp/test.zip", "test.zip", "project2", "individual", "code", "2024-01-02"),
    ]
    for user_id, zip_path, zip_name, project_name, classification, project_type, recorded_at in projects:
        seed_conn.execute(
            """
            INSERT INTO project_classifications
            (user_id, zip_path, zip_name, project_name, classification, project_type, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, zip_path, zip_name, project_name, classification, project_type, recorded_at)
        )

    # Insert sample project skills
    skills = [
        (consent_user_id_1, "project1", "algorithms", "Advanced", 0.95),
        (consent_user_id_1, "project1", "data_structures", "Intermediate", 0.75),
        (consent_user_id_1, "project2", "api_and_backend", "Advanced", 0.85),
        (consent_user_id_1, "project2", "testing_and_ci", "Beginner", 0.50),
    ]
    for user_id, project_name, skill_name, level, score in skills:
        seed_conn.execute(
            """
            INSERT INTO project_skills (user_id, project_name, skill_name, level, score, evidence_json)
            VALUES (?, ?, ?, ?, ?, '[]')
            """,
            (user_id, project_name, skill_name, level, score)
        )
    seed_conn.commit()
    return consent_user_id_1


# =============================================================================
# GET /skills/preferences tests
# =============================================================================

class TestGetSkillPreferences:
    def test_requires_auth(self, client):
        res = client.get("/skills/preferences")
        assert res.status_code == 401

    def test_returns_empty_when_no_skills(self, client, auth_headers, consent_user_id_1):
        res = client.get("/skills/preferences", headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["skills"] == []
        assert body["data"]["context"] == "global"
        assert body["data"]["context_id"] is None

    def test_returns_all_skills_with_default_status(self, client, auth_headers, user_with_skills):
        res = client.get("/skills/preferences", headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True

        skills = body["data"]["skills"]
        assert len(skills) == 4

        # All skills should be highlighted by default
        for skill in skills:
            assert skill["is_highlighted"] is True
            assert "skill_name" in skill
            assert "project_count" in skill
            assert "max_score" in skill

    def test_returns_context_in_response(self, client, auth_headers, user_with_skills):
        res = client.get("/skills/preferences?context=portfolio", headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["data"]["context"] == "portfolio"


# =============================================================================
# PUT /skills/preferences tests
# =============================================================================

class TestUpdateSkillPreferences:
    def test_requires_auth(self, client):
        res = client.put("/skills/preferences", json={"skills": []})
        assert res.status_code == 401

    def test_update_single_skill(self, client, auth_headers, user_with_skills):
        res = client.put(
            "/skills/preferences",
            json={
                "skills": [
                    {"skill_name": "algorithms", "is_highlighted": False}
                ]
            },
            headers=auth_headers
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True

        # Find algorithms in response
        skills = body["data"]["skills"]
        algo = next(s for s in skills if s["skill_name"] == "algorithms")
        assert algo["is_highlighted"] is False

    def test_update_multiple_skills(self, client, auth_headers, user_with_skills):
        res = client.put(
            "/skills/preferences",
            json={
                "skills": [
                    {"skill_name": "algorithms", "is_highlighted": False},
                    {"skill_name": "data_structures", "is_highlighted": True, "display_order": 1},
                ]
            },
            headers=auth_headers
        )
        assert res.status_code == 200
        body = res.json()
        skills = body["data"]["skills"]

        algo = next(s for s in skills if s["skill_name"] == "algorithms")
        ds = next(s for s in skills if s["skill_name"] == "data_structures")

        assert algo["is_highlighted"] is False
        assert ds["is_highlighted"] is True
        assert ds["display_order"] == 1

    def test_partial_update_preserves_other_skills(self, client, auth_headers, user_with_skills):
        # First, hide algorithms
        client.put(
            "/skills/preferences",
            json={"skills": [{"skill_name": "algorithms", "is_highlighted": False}]},
            headers=auth_headers
        )

        # Then update only data_structures
        res = client.put(
            "/skills/preferences",
            json={"skills": [{"skill_name": "data_structures", "is_highlighted": False}]},
            headers=auth_headers
        )

        body = res.json()
        skills = body["data"]["skills"]

        # algorithms should still be hidden
        algo = next(s for s in skills if s["skill_name"] == "algorithms")
        ds = next(s for s in skills if s["skill_name"] == "data_structures")

        assert algo["is_highlighted"] is False
        assert ds["is_highlighted"] is False

    def test_update_display_order(self, client, auth_headers, user_with_skills):
        res = client.put(
            "/skills/preferences",
            json={
                "skills": [
                    {"skill_name": "testing_and_ci", "display_order": 1},
                    {"skill_name": "algorithms", "display_order": 2},
                ]
            },
            headers=auth_headers
        )
        assert res.status_code == 200
        body = res.json()
        skills = body["data"]["skills"]

        # Skills with display_order should be sorted first
        assert skills[0]["skill_name"] == "testing_and_ci"
        assert skills[1]["skill_name"] == "algorithms"

    def test_empty_skills_array(self, client, auth_headers, user_with_skills):
        res = client.put(
            "/skills/preferences",
            json={"skills": []},
            headers=auth_headers
        )
        assert res.status_code == 200

    def test_invalid_request_body(self, client, auth_headers):
        res = client.put(
            "/skills/preferences",
            json={"invalid": "data"},
            headers=auth_headers
        )
        assert res.status_code == 422


# =============================================================================
# DELETE /skills/preferences tests
# =============================================================================

class TestResetSkillPreferences:
    def test_requires_auth(self, client):
        res = client.delete("/skills/preferences")
        assert res.status_code == 401

    def test_reset_clears_preferences(self, client, auth_headers, user_with_skills):
        # First set some preferences
        client.put(
            "/skills/preferences",
            json={
                "skills": [
                    {"skill_name": "algorithms", "is_highlighted": False},
                    {"skill_name": "data_structures", "display_order": 1},
                ]
            },
            headers=auth_headers
        )

        # Then reset
        res = client.delete("/skills/preferences", headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True

        # All skills should be highlighted with no display_order
        skills = body["data"]["skills"]
        for skill in skills:
            assert skill["is_highlighted"] is True
            assert skill["display_order"] is None

    def test_reset_returns_global_context(self, client, auth_headers, user_with_skills):
        res = client.delete("/skills/preferences", headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["data"]["context"] == "global"
        assert body["data"]["context_id"] is None


# =============================================================================
# GET /skills/preferences/highlighted tests
# =============================================================================

class TestGetHighlightedSkills:
    def test_requires_auth(self, client):
        res = client.get("/skills/preferences/highlighted")
        assert res.status_code == 401

    def test_returns_all_skills_when_no_preferences(self, client, auth_headers, user_with_skills):
        res = client.get("/skills/preferences/highlighted", headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True

        skills = body["data"]["skills"]
        assert len(skills) == 4
        assert "algorithms" in skills
        assert "data_structures" in skills

    def test_excludes_hidden_skills(self, client, auth_headers, user_with_skills):
        # Hide some skills
        client.put(
            "/skills/preferences",
            json={
                "skills": [
                    {"skill_name": "algorithms", "is_highlighted": False},
                    {"skill_name": "api_and_backend", "is_highlighted": False},
                ]
            },
            headers=auth_headers
        )

        res = client.get("/skills/preferences/highlighted", headers=auth_headers)
        assert res.status_code == 200
        body = res.json()

        skills = body["data"]["skills"]
        assert "algorithms" not in skills
        assert "api_and_backend" not in skills
        assert "data_structures" in skills
        assert "testing_and_ci" in skills

    def test_respects_display_order(self, client, auth_headers, user_with_skills):
        # Set display order
        client.put(
            "/skills/preferences",
            json={
                "skills": [
                    {"skill_name": "testing_and_ci", "display_order": 1},
                    {"skill_name": "algorithms", "display_order": 2},
                ]
            },
            headers=auth_headers
        )

        res = client.get("/skills/preferences/highlighted", headers=auth_headers)
        assert res.status_code == 200
        body = res.json()

        skills = body["data"]["skills"]
        # Skills with display_order should come first, in order
        assert skills[0] == "testing_and_ci"
        assert skills[1] == "algorithms"

    def test_returns_context_in_response(self, client, auth_headers, user_with_skills):
        res = client.get("/skills/preferences/highlighted?context=portfolio", headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["data"]["context"] == "portfolio"


# =============================================================================
# Integration tests
# =============================================================================

class TestSkillPreferencesIntegration:
    def test_full_workflow(self, client, auth_headers, user_with_skills):
        """Test complete flow: get, update, verify, reset."""
        # 1. Get initial state - all highlighted
        res = client.get("/skills/preferences", headers=auth_headers)
        assert res.status_code == 200
        initial_skills = res.json()["data"]["skills"]
        assert all(s["is_highlighted"] for s in initial_skills)

        # 2. Hide some skills
        client.put(
            "/skills/preferences",
            json={
                "skills": [
                    {"skill_name": "algorithms", "is_highlighted": False},
                    {"skill_name": "testing_and_ci", "is_highlighted": False},
                ]
            },
            headers=auth_headers
        )

        # 3. Verify highlighted endpoint excludes hidden
        res = client.get("/skills/preferences/highlighted", headers=auth_headers)
        highlighted = res.json()["data"]["skills"]
        assert "algorithms" not in highlighted
        assert "testing_and_ci" not in highlighted
        assert len(highlighted) == 2

        # 4. Reset
        client.delete("/skills/preferences", headers=auth_headers)

        # 5. Verify all highlighted again
        res = client.get("/skills/preferences/highlighted", headers=auth_headers)
        highlighted = res.json()["data"]["skills"]
        assert len(highlighted) == 4
