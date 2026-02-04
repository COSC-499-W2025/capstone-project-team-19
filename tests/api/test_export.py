"""
Tests for resume and portfolio export endpoints.

Endpoints tested:
- GET /resume/{resume_id}/export/docx
- GET /resume/{resume_id}/export/pdf
- GET /portfolio/export/docx
- GET /portfolio/export/pdf
"""

import json

import pytest

from src.db.resumes import insert_resume_snapshot
from src.db.project_summaries import save_project_summary
from src.api.auth.security import create_access_token


TEST_JWT_SECRET = "test-secret-key-for-testing"

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PDF_MIME = "application/pdf"


def _seed_resume(seed_conn, user_id: int, name: str = "Test Resume") -> int:
    """Create a minimal resume snapshot and return its ID."""
    resume_json = json.dumps({
        "projects": [
            {
                "project_name": "Test Project",
                "project_type": "code",
                "project_mode": "individual",
                "start_date": "2025-01-01",
                "end_date": "2025-06-01",
                "summary_text": "A test project summary.",
                "contribution_bullets": ["Built the API", "Wrote tests"],
                "key_role": "Backend Developer",
            }
        ],
        "aggregated_skills": {
            "languages": ["Python"],
            "frameworks": ["FastAPI"],
            "technical_skills": ["REST APIs"],
            "writing_skills": [],
        },
    })
    return insert_resume_snapshot(seed_conn, user_id, name, resume_json)


def _seed_project(seed_conn, user_id: int, name: str = "Test Project") -> None:
    """Create a minimal project summary for portfolio export."""
    summary_json = json.dumps({
        "project_name": name,
        "project_type": "code",
        "project_mode": "individual",
        "summary_text": "A test project for portfolio.",
        "languages": ["Python 80%"],
        "frameworks": ["FastAPI"],
    })
    save_project_summary(seed_conn, user_id, name, summary_json)


# ------------------------------------------------------------------------------
# Resume Export Tests
# ------------------------------------------------------------------------------

def test_resume_export_docx_requires_auth(client):
    res = client.get("/resume/1/export/docx")
    assert res.status_code == 401


def test_resume_export_pdf_requires_auth(client):
    res = client.get("/resume/1/export/pdf")
    assert res.status_code == 401


def test_resume_export_docx_not_found(client, auth_headers):
    res = client.get("/resume/999999/export/docx", headers=auth_headers)
    assert res.status_code == 404
    assert "resume not found" in res.json()["detail"].lower()


def test_resume_export_pdf_not_found(client, auth_headers):
    res = client.get("/resume/999999/export/pdf", headers=auth_headers)
    assert res.status_code == 404
    assert "resume not found" in res.json()["detail"].lower()


def test_resume_export_docx_success(client, auth_headers, seed_conn, consent_user_id_1):
    resume_id = _seed_resume(seed_conn, consent_user_id_1)

    res = client.get(f"/resume/{resume_id}/export/docx", headers=auth_headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == DOCX_MIME
    assert "attachment" in res.headers.get("content-disposition", "").lower() or \
           ".docx" in res.headers.get("content-disposition", "")
    # Check we got actual file content
    assert len(res.content) > 0


def test_resume_export_pdf_success(client, auth_headers, seed_conn, consent_user_id_1):
    resume_id = _seed_resume(seed_conn, consent_user_id_1)

    res = client.get(f"/resume/{resume_id}/export/pdf", headers=auth_headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == PDF_MIME
    assert len(res.content) > 0
    # PDF files start with %PDF
    assert res.content[:4] == b"%PDF"


def test_resume_export_cross_user_returns_404(client, seed_conn, consent_user_id_1, consent_user_id_2):
    """User 1 cannot export User 2's resume."""
    # Create resume for user 2
    resume_id = _seed_resume(seed_conn, consent_user_id_2, "User2 Resume")

    # User 1 tries to access it
    token = create_access_token(
        secret=TEST_JWT_SECRET,
        user_id=consent_user_id_1,
        username="test-user",
        expires_minutes=60,
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(f"/resume/{resume_id}/export/docx", headers=headers)
    assert res.status_code == 404


# ------------------------------------------------------------------------------
# Portfolio Export Tests
# ------------------------------------------------------------------------------

def test_portfolio_export_docx_requires_auth(client):
    res = client.get("/portfolio/export/docx")
    assert res.status_code == 401


def test_portfolio_export_pdf_requires_auth(client):
    res = client.get("/portfolio/export/pdf")
    assert res.status_code == 401


def test_portfolio_export_docx_success_empty(client, auth_headers, consent_user_id_1):
    """Portfolio export works even with no projects (returns empty doc)."""
    res = client.get("/portfolio/export/docx", headers=auth_headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == DOCX_MIME
    assert len(res.content) > 0


def test_portfolio_export_pdf_success_empty(client, auth_headers, consent_user_id_1):
    """Portfolio export works even with no projects (returns empty doc)."""
    res = client.get("/portfolio/export/pdf", headers=auth_headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == PDF_MIME
    assert len(res.content) > 0
    assert res.content[:4] == b"%PDF"


def test_portfolio_export_docx_with_project(client, auth_headers, seed_conn, consent_user_id_1):
    """Portfolio export includes seeded project."""
    _seed_project(seed_conn, consent_user_id_1, "My Portfolio Project")

    res = client.get("/portfolio/export/docx", headers=auth_headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == DOCX_MIME
    assert len(res.content) > 0


def test_portfolio_export_pdf_with_project(client, auth_headers, seed_conn, consent_user_id_1):
    """Portfolio export includes seeded project."""
    _seed_project(seed_conn, consent_user_id_1, "My Portfolio Project")

    res = client.get("/portfolio/export/pdf", headers=auth_headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == PDF_MIME
    assert len(res.content) > 0
    assert res.content[:4] == b"%PDF"
