"""
Tests for the eligible roles endpoint.

Endpoints tested:
- GET /resume/{resume_id}/projects/{project_summary_id}/eligible-roles
"""

import json
import pytest

from src.db.resumes import insert_resume_snapshot
from src.api.auth.security import create_access_token
from tests.api.conftest import seed_project


TEST_JWT_SECRET = "test-secret-key-for-testing"


def _seed_resume_with_project(
    seed_conn,
    user_id: int,
    project_name: str,
    project_type: str,
    project_summary_id: int,
    key_role: str = "Backend Developer",
) -> int:
    resume_json = json.dumps({
        "projects": [
            {
                "project_summary_id": project_summary_id,
                "project_name": project_name,
                "project_type": project_type,
                "project_mode": "individual",
                "start_date": "2025-01-01",
                "end_date": "2025-06-01",
                "summary_text": "A test project.",
                "contribution_bullets": ["Did stuff"],
                "key_role": key_role,
            }
        ],
        "aggregated_skills": {
            "languages": [],
            "frameworks": [],
            "technical_skills": [],
            "writing_skills": [],
        },
    })
    return insert_resume_snapshot(seed_conn, user_id, "Test Resume", resume_json)


def _seed_project_skills(seed_conn, user_id: int, project_name: str, scores: dict[str, float]):
    """Insert project_skills rows directly via project_key lookup."""
    row = seed_conn.execute(
        "SELECT project_key FROM projects WHERE user_id = ? AND display_name = ?",
        (user_id, project_name),
    ).fetchone()
    assert row is not None, f"Project '{project_name}' not found -- seed it first"
    project_key = row[0]

    for skill_name, score in scores.items():
        seed_conn.execute(
            """
            INSERT OR REPLACE INTO project_skills (user_id, project_key, skill_name, level, score)
            VALUES (?, ?, ?, 'intermediate', ?)
            """,
            (user_id, project_key, skill_name, score),
        )
    seed_conn.commit()


def test_eligible_roles_requires_auth(client):
    res = client.get("/resume/1/projects/1/eligible-roles")
    assert res.status_code == 401


def test_eligible_roles_returns_404_for_missing_resume(client, auth_headers):
    res = client.get("/resume/999999/projects/1/eligible-roles", headers=auth_headers)
    assert res.status_code == 404


def test_eligible_roles_returns_404_for_project_not_in_resume(client, auth_headers, seed_conn, consent_user_id_1):
    project_key = seed_project(seed_conn, consent_user_id_1, "MyProject")
    resume_id = _seed_resume_with_project(
        seed_conn, consent_user_id_1, "MyProject", "code", project_key
    )
    res = client.get(f"/resume/{resume_id}/projects/999999/eligible-roles", headers=auth_headers)
    assert res.status_code == 404


def test_eligible_roles_returns_all_when_no_skills_analyzed(client, auth_headers, seed_conn, consent_user_id_1):
    """No rows in project_skills yet -- should return all roles for the project type."""
    from src.analysis.skills.roles.role_eligibility import CODE_ROLES
    project_key = seed_project(seed_conn, consent_user_id_1, "NewProject")
    resume_id = _seed_resume_with_project(
        seed_conn, consent_user_id_1, "NewProject", "code", project_key
    )
    res = client.get(f"/resume/{resume_id}/projects/{project_key}/eligible-roles", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert sorted(data["data"]["roles"]) == sorted(CODE_ROLES.keys())


def test_eligible_roles_filters_by_analyzed_skill_scores(client, auth_headers, seed_conn, consent_user_id_1):
    """After analysis, only roles matching bucket scores should be returned."""
    project_key = seed_project(seed_conn, consent_user_id_1, "AlgoProject")
    _seed_project_skills(seed_conn, consent_user_id_1, "AlgoProject", {
        "algorithms": 0.7,
        "data_structures": 0.6,
        "api_and_backend": 0.0,
        "frontend_skills": 0.0,
        "architecture_and_design": 0.0,
        "testing_and_ci": 0.0,
        "security_and_error_handling": 0.0,
        "clean_code_and_quality": 0.0,
    })
    resume_id = _seed_resume_with_project(
        seed_conn, consent_user_id_1, "AlgoProject", "code", project_key
    )
    res = client.get(f"/resume/{resume_id}/projects/{project_key}/eligible-roles", headers=auth_headers)
    assert res.status_code == 200
    roles = res.json()["data"]["roles"]
    assert "Algorithms Engineer" in roles
    assert "Data Engineer" in roles
    assert "Backend Developer" not in roles
    assert "Frontend Developer" not in roles


def test_eligible_roles_text_project_returns_text_roles(client, auth_headers, seed_conn, consent_user_id_1):
    from src.analysis.skills.roles.role_eligibility import TEXT_ROLES
    project_key = seed_project(seed_conn, consent_user_id_1, "EssayProject")
    resume_id = _seed_resume_with_project(
        seed_conn, consent_user_id_1, "EssayProject", "text", project_key
    )
    res = client.get(f"/resume/{resume_id}/projects/{project_key}/eligible-roles", headers=auth_headers)
    assert res.status_code == 200
    assert sorted(res.json()["data"]["roles"]) == sorted(TEXT_ROLES.keys())


def test_eligible_roles_cross_user_returns_404(client, seed_conn, consent_user_id_1, consent_user_id_2):
    """User 1 cannot access User 2's resume eligible roles."""
    project_key = seed_project(seed_conn, consent_user_id_2, "PrivateProject")
    resume_id = _seed_resume_with_project(
        seed_conn, consent_user_id_2, "PrivateProject", "code", project_key
    )
    token = create_access_token(
        secret=TEST_JWT_SECRET,
        user_id=consent_user_id_1,
        username="test-user",
        expires_minutes=60,
    )
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get(f"/resume/{resume_id}/projects/{project_key}/eligible-roles", headers=headers)
    assert res.status_code == 404


def test_eligible_roles_response_shape(client, auth_headers, seed_conn, consent_user_id_1):
    project_key = seed_project(seed_conn, consent_user_id_1, "ShapeProject")
    resume_id = _seed_resume_with_project(
        seed_conn, consent_user_id_1, "ShapeProject", "code", project_key
    )
    res = client.get(f"/resume/{resume_id}/projects/{project_key}/eligible-roles", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert "success" in body
    assert "data" in body
    assert "roles" in body["data"]
    assert isinstance(body["data"]["roles"], list)
    assert all(isinstance(r, str) for r in body["data"]["roles"])