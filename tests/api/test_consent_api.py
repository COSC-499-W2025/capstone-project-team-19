import pytest
import src.db as db


# POST /privacy-consent/internal tests

def test_internal_consent_requires_user_header(client):
    res = client.post("/privacy-consent/internal", json={"status": "accepted"})
    assert res.status_code == 401


def test_internal_consent_with_invalid_user(client):
    """Test that endpoints reject tokens with non-existent user IDs."""
    from src.api.auth.security import create_access_token
    # Create token for user 999 that doesn't exist
    token = create_access_token(
        secret="test-secret-key-for-testing",
        user_id=999,
        username="nonexistent",
        expires_minutes=60
    )
    res = client.post(
        "/privacy-consent/internal",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found"


def test_internal_consent_accepted(consent_user_id_1, client, auth_headers):
    res = client.post(
        "/privacy-consent/internal",
        json={"status": "accepted"},
        headers=auth_headers
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    assert body["data"]["status"] == "accepted"
    assert body["data"]["user_id"] == consent_user_id_1
    assert "consent_id" in body["data"]
    assert "timestamp" in body["data"]


def test_internal_consent_rejected(client, auth_headers):
    res = client.post(
        "/privacy-consent/internal",
        json={"status": "rejected"},
        headers=auth_headers
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    assert body["data"]["status"] == "rejected"


def test_internal_consent_invalid_status(client, auth_headers):
    res = client.post(
        "/privacy-consent/internal",
        json={"status": "maybe"},
        headers=auth_headers
    )
    assert res.status_code == 422


# POST /privacy-consent/external tests

def test_external_consent_requires_user_header(client):
    res = client.post("/privacy-consent/external", json={"status": "accepted"})
    assert res.status_code == 401


def test_external_consent_accepted(consent_user_id_1, client, auth_headers):
    res = client.post(
        "/privacy-consent/external",
        json={"status": "accepted"},
        headers=auth_headers
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    assert body["data"]["status"] == "accepted"
    assert body["data"]["user_id"] == consent_user_id_1


def test_external_consent_rejected(client, auth_headers):
    res = client.post(
        "/privacy-consent/external",
        json={"status": "rejected"},
        headers=auth_headers
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    assert body["data"]["status"] == "rejected"


# GET /privacy-consent/status tests

def test_get_consent_status_requires_user_header(client):
    res = client.get("/privacy-consent/status")
    assert res.status_code == 401


def test_get_consent_status_with_invalid_user(client):
    """Test that endpoints reject tokens with non-existent user IDs."""
    from src.api.auth.security import create_access_token
    # Create token for user 999 that doesn't exist
    token = create_access_token(
        secret="test-secret-key-for-testing",
        user_id=999,
        username="nonexistent",
        expires_minutes=60
    )
    res = client.get(
        "/privacy-consent/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found"


def test_get_consent_status_no_consents(consent_user_id_2, client):
    """Test that GET consent/status returns empty consents for user with no records."""
    from src.api.auth.security import create_access_token
    # Create token for user 2
    token = create_access_token(
        secret="test-secret-key-for-testing",
        user_id=consent_user_id_2,
        username="new-user",
        expires_minutes=60
    )
    res = client.get(
        "/privacy-consent/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["user_id"] == consent_user_id_2
    assert body["data"]["internal_consent"] is None
    assert body["data"]["external_consent"] is None


def test_get_consent_status_after_recording(client, auth_headers):
    # Record internal consent
    client.post(
        "/privacy-consent/internal",
        json={"status": "accepted"},
        headers=auth_headers
    )

    # Record external consent
    client.post(
        "/privacy-consent/external",
        json={"status": "rejected"},
        headers=auth_headers
    )

    # Get status
    res = client.get("/privacy-consent/status", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["internal_consent"] == "accepted"
    assert body["data"]["external_consent"] == "rejected"


def test_get_consent_status_returns_latest(client, auth_headers):
    # Record initial consent
    client.post(
        "/privacy-consent/internal",
        json={"status": "accepted"},
        headers=auth_headers
    )

    # Change consent
    client.post(
        "/privacy-consent/internal",
        json={"status": "rejected"},
        headers=auth_headers
    )

    # Get status - should return the latest (rejected)
    res = client.get("/privacy-consent/status", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["internal_consent"] == "rejected"
