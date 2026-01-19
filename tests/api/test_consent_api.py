import pytest
from fastapi.testclient import TestClient
from src.api.main import app
import src.db as db

client = TestClient(app)


@pytest.fixture
def test_user():
    """Create test user with id 1."""
    conn = db.connect()
    conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)")
    conn.commit()
    conn.close()
    return 1


@pytest.fixture
def test_user_2():
    """Create test user with id 2."""
    conn = db.connect()
    conn.execute("INSERT OR IGNORE INTO users(user_id, username, email) VALUES (2, 'new-user', NULL)")
    conn.commit()
    conn.close()
    return 2


# POST /privacy-consent/internal tests

def test_internal_consent_requires_user_header():
    res = client.post("/privacy-consent/internal", json={"status": "accepted"})
    assert res.status_code == 401


def test_internal_consent_with_invalid_user():
    res = client.post(
        "/privacy-consent/internal",
        json={"status": "accepted"},
        headers={"X-User-Id": "9999"}
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found"


def test_internal_consent_accepted(test_user):
    res = client.post(
        "/privacy-consent/internal",
        json={"status": "accepted"},
        headers={"X-User-Id": str(test_user)}
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    assert body["data"]["status"] == "accepted"
    assert body["data"]["user_id"] == test_user
    assert "consent_id" in body["data"]
    assert "timestamp" in body["data"]


def test_internal_consent_rejected(test_user):
    res = client.post(
        "/privacy-consent/internal",
        json={"status": "rejected"},
        headers={"X-User-Id": str(test_user)}
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    assert body["data"]["status"] == "rejected"


def test_internal_consent_invalid_status(test_user):
    res = client.post(
        "/privacy-consent/internal",
        json={"status": "maybe"},
        headers={"X-User-Id": str(test_user)}
    )
    assert res.status_code == 422


# POST /privacy-consent/external tests

def test_external_consent_requires_user_header():
    res = client.post("/privacy-consent/external", json={"status": "accepted"})
    assert res.status_code == 401


def test_external_consent_accepted(test_user):
    res = client.post(
        "/privacy-consent/external",
        json={"status": "accepted"},
        headers={"X-User-Id": str(test_user)}
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    assert body["data"]["status"] == "accepted"
    assert body["data"]["user_id"] == test_user


def test_external_consent_rejected(test_user):
    res = client.post(
        "/privacy-consent/external",
        json={"status": "rejected"},
        headers={"X-User-Id": str(test_user)}
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    assert body["data"]["status"] == "rejected"


# GET /privacy-consent/status tests

def test_get_consent_status_requires_user_header():
    res = client.get("/privacy-consent/status")
    assert res.status_code == 401


def test_get_consent_status_with_invalid_user():
    res = client.get("/privacy-consent/status", headers={"X-User-Id": "9999"})
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found"


def test_get_consent_status_no_consents(test_user_2):
    res = client.get("/privacy-consent/status", headers={"X-User-Id": str(test_user_2)})
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["user_id"] == test_user_2
    assert body["data"]["internal_consent"] is None
    assert body["data"]["external_consent"] is None


def test_get_consent_status_after_recording(test_user):
    # Record internal consent
    client.post(
        "/privacy-consent/internal",
        json={"status": "accepted"},
        headers={"X-User-Id": str(test_user)}
    )

    # Record external consent
    client.post(
        "/privacy-consent/external",
        json={"status": "rejected"},
        headers={"X-User-Id": str(test_user)}
    )

    # Get status
    res = client.get("/privacy-consent/status", headers={"X-User-Id": str(test_user)})
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["internal_consent"] == "accepted"
    assert body["data"]["external_consent"] == "rejected"


def test_get_consent_status_returns_latest(test_user):
    # Record initial consent
    client.post(
        "/privacy-consent/internal",
        json={"status": "accepted"},
        headers={"X-User-Id": str(test_user)}
    )

    # Change consent
    client.post(
        "/privacy-consent/internal",
        json={"status": "rejected"},
        headers={"X-User-Id": str(test_user)}
    )

    # Get status - should return the latest (rejected)
    res = client.get("/privacy-consent/status", headers={"X-User-Id": str(test_user)})
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["internal_consent"] == "rejected"
