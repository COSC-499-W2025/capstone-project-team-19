import pytest

from src.db.project_feedback import upsert_project_feedback
from src.api.auth.security import create_access_token
from tests.api.conftest import seed_project


def _seed_feedback(
    seed_conn,
    user_id: int,
    project_name: str,
    *,
    project_type: str = "code",
    skill_name: str,
    file_name: str = "",
    criterion_key: str,
    criterion_label: str,
    expected: str | None = None,
    observed: dict | None = None,
    suggestion: str | None = None,
) -> None:
    upsert_project_feedback(
        seed_conn,
        user_id,
        project_name,
        project_type,
        skill_name,
        criterion_key,
        criterion_label,
        expected=expected,
        observed=observed,
        suggestion=suggestion,
        file_name=file_name,
    )


def test_feedback_requires_auth(client):
    res = client.get("/projects/1/feedback")
    assert res.status_code == 401


def test_feedback_nonexistent_user_404(client, auth_headers_nonexistent_user):
    res = client.get("/projects/1/feedback", headers=auth_headers_nonexistent_user)
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found"


def test_feedback_project_not_found_404(client, auth_headers):
    res = client.get("/projects/999999/feedback", headers=auth_headers)
    assert res.status_code == 404
    assert "project not found" in res.json()["detail"].lower()


def test_feedback_route_requires_int_project_id(client, auth_headers):
    res = client.get("/projects/not-an-int/feedback", headers=auth_headers)
    assert res.status_code == 404


def test_feedback_project_belongs_to_other_user_returns_404(client, seed_conn, consent_user_id_2, auth_headers):
    other_user_project_id = seed_project(seed_conn, consent_user_id_2, "OtherUsersProject")

    # user 1 requesting user 2's project_id should look like "not found"
    res = client.get(f"/projects/{other_user_project_id}/feedback", headers=auth_headers)
    assert res.status_code == 404
    assert "project not found" in res.json()["detail"].lower()


def test_feedback_project_exists_but_no_feedback_returns_empty_list(client, auth_headers, seed_conn):
    project_id = seed_project(seed_conn, 1, "NoFeedbackProject")

    res = client.get(f"/projects/{project_id}/feedback", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["error"] is None
    assert body["data"]["project_id"] == project_id
    assert body["data"]["project_name"] == "NoFeedbackProject"
    assert body["data"]["feedback"] == []


def test_feedback_project_exists_with_feedback_rows_returns_sorted_items(client, auth_headers, seed_conn):
    project_name = "FeedbackProject"
    project_id = seed_project(seed_conn, 1, project_name)

    # Intentionally insert out-of-order. DB query orders by skill_name, file_name, criterion_key.
    _seed_feedback(
        seed_conn,
        1,
        project_name,
        skill_name="structure",
        file_name="b.py",
        criterion_key="b_key",
        criterion_label="B label",
        expected="Do B",
        observed={"count": 2},
        suggestion="Fix B",
    )
    _seed_feedback(
        seed_conn,
        1,
        project_name,
        skill_name="clarity",
        file_name="",
        criterion_key="a_key",
        criterion_label="A label",
        expected="Do A",
        observed={"threshold": 0.5},
        suggestion="Fix A",
    )
    _seed_feedback(
        seed_conn,
        1,
        project_name,
        skill_name="structure",
        file_name="a.py",
        criterion_key="a_key",
        criterion_label="A2 label",
        expected="Do A2",
        observed={"x": 1},
        suggestion="Fix A2",
    )

    res = client.get(f"/projects/{project_id}/feedback", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True

    data = body["data"]
    assert data["project_id"] == project_id
    assert data["project_name"] == project_name

    items = data["feedback"]
    assert len(items) == 3

    # verify sort order
    keys = [(i["skill_name"], i["file_name"], i["criterion_key"]) for i in items]
    assert keys == sorted(keys)

    # verify a representative row shape (observed should be a dict, generated_at should exist)
    first = items[0]
    assert "skill_name" in first
    assert "criterion_label" in first
    assert isinstance(first["observed"], dict)
    assert first["generated_at"] is not None


def test_feedback_preflight_options_returns_405_without_cors(client, auth_headers, seed_conn):
    """
    Edge case: without CORSMiddleware, browsers may send OPTIONS preflight for this route.
    This documents current behavior (405). If you add CORS middleware later, update/remove this test.
    """
    project_id = seed_project(seed_conn, 1, "CorsProject")
    res = client.options(f"/projects/{project_id}/feedback", headers=auth_headers)
    assert res.status_code == 405


@pytest.fixture
def auth_headers_user_2(consent_user_id_2):
    """
    Helper fixture: auth header for user_id=2.
    """
    token = create_access_token(
        secret="test-secret-key-for-testing",
        user_id=consent_user_id_2,
        username="new-user",
        expires_minutes=60,
    )
    return {"Authorization": f"Bearer {token}"}

