import pytest
import requests
from urllib.parse import parse_qs, urlparse
from src.integrations.google_drive import google_drive_web_oauth


# HELPERS
class FakeResponse:
    """Reusable fake HTTP response for mocking."""
    def __init__(self, status, data):
        self.status_code = status
        self._data = data

    def json(self):
        return self._data

    @property
    def text(self):
        return str(self._data)

def setup_module_vars(monkeypatch, client_id="test_client_id", client_secret="test_secret", redirect_uri=None):
    """Helper to set up module-level variables for tests."""
    monkeypatch.setattr(google_drive_web_oauth, "GOOGLE_CLIENT_ID", client_id)
    monkeypatch.setattr(google_drive_web_oauth, "GOOGLE_CLIENT_SECRET", client_secret)
    if redirect_uri:
        monkeypatch.setattr(google_drive_web_oauth, "GOOGLE_REDIRECT_URI", redirect_uri)
    else:
        monkeypatch.setattr(google_drive_web_oauth, "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

def parse_auth_url(url):
    """Helper to parse auth URL and extract query parameters."""
    parsed = urlparse(url)
    return parse_qs(parsed.query)

# FIXTURES
@pytest.fixture
def module_vars(monkeypatch):
    """Fixture providing default module vars for all tests."""
    setup_module_vars(monkeypatch)
    yield

# TESTS for generate_google_auth_url

def test_generate_auth_url_success_with_params(monkeypatch, module_vars):
    """Test URL generation with default parameters."""
    url = google_drive_web_oauth.generate_google_auth_url()
    params = parse_auth_url(url)
    assert params["client_id"][0] == "test_client_id"
    assert params["redirect_uri"][0] == "http://localhost:8000/auth/google/callback"
    assert params["response_type"][0] == "code"
    assert params["access_type"][0] == "offline"
    assert params["prompt"][0] == "consent"
    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth")

    # Verify all expected scopes are present
    scope_str = params["scope"][0]
    assert "drive.readonly" in scope_str
    assert "drive.metadata.readonly" in scope_str
    assert "userinfo.email" in scope_str
    assert "userinfo.profile" in scope_str
    assert "openid" in scope_str

def test_generate_auth_url_with_state(monkeypatch, module_vars):
    """Test URL generation includes state parameter when provided."""
    url = google_drive_web_oauth.generate_google_auth_url(state="abc123")
    params = parse_auth_url(url)
    assert params["state"][0] == "abc123"

def test_generate_auth_url_without_state(monkeypatch, module_vars):
    """Test URL generation omits state parameter when not provided."""
    url = google_drive_web_oauth.generate_google_auth_url()
    params = parse_auth_url(url)
    assert "state" not in params

def test_generate_auth_url_custom_redirect(monkeypatch):
    """Test URL generation uses custom redirect URI."""
    setup_module_vars(monkeypatch, redirect_uri="http://example.com/callback")
    url = google_drive_web_oauth.generate_google_auth_url()

    params = parse_auth_url(url)
    assert params["redirect_uri"][0] == "http://example.com/callback"

def test_generate_auth_url_missing_client_id(monkeypatch):
    """Test raises ValueError when GOOGLE_CLIENT_ID is missing."""
    setup_module_vars(monkeypatch, client_id=None)

    with pytest.raises(ValueError, match="GOOGLE_CLIENT_ID"):
        google_drive_web_oauth.generate_google_auth_url()

# TESTS for exchange_code_for_tokens

def test_exchange_code_success(monkeypatch, module_vars):
    """Test successful code exchange returns tokens."""
    fake_resp = FakeResponse(200, {
        "access_token": "ya29.token123",
        "refresh_token": "1//refresh456",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "openid https://www.googleapis.com/auth/drive.readonly"
    })
    captured_data = {}
    def fake_post(url, data, headers):
        captured_data.update(data)
        return fake_resp

    monkeypatch.setattr(requests, "post", fake_post)

    result = google_drive_web_oauth.exchange_code_for_tokens("code123")
    assert result["access_token"] == "ya29.token123"
    assert result["refresh_token"] == "1//refresh456"
    assert result["expires_in"] == 3600
    assert result["token_type"] == "Bearer"
    assert captured_data["code"] == "code123"
    assert captured_data["grant_type"] == "authorization_code"
    assert captured_data["redirect_uri"] == "http://localhost:8000/auth/google/callback"

def test_exchange_code_missing_client_id(monkeypatch):
    """Test raises ValueError when GOOGLE_CLIENT_ID is missing."""
    setup_module_vars(monkeypatch, client_id=None, client_secret="secret")
    with pytest.raises(ValueError, match="GOOGLE_CLIENT_ID"):
        google_drive_web_oauth.exchange_code_for_tokens("code123")

def test_exchange_code_missing_client_secret(monkeypatch):
    """Test raises ValueError when GOOGLE_CLIENT_SECRET is missing."""
    setup_module_vars(monkeypatch, client_secret=None)
    with pytest.raises(ValueError, match="GOOGLE_CLIENT_SECRET"):
        google_drive_web_oauth.exchange_code_for_tokens("code123")

def test_exchange_code_oauth_error_response(monkeypatch, module_vars):
    """Test handles OAuth error in response body."""
    fake_resp = FakeResponse(200, {"error": "invalid_grant", "error_description": "Code expired"})
    monkeypatch.setattr(requests, "post", lambda *a, **k: fake_resp)
    assert google_drive_web_oauth.exchange_code_for_tokens("badcode") is None

def test_exchange_code_http_error(monkeypatch, module_vars):
    """Test handles non-200 HTTP status code."""
    fake_resp = FakeResponse(400, {"error": "bad_request"})
    monkeypatch.setattr(requests, "post", lambda *a, **k: fake_resp)
    assert google_drive_web_oauth.exchange_code_for_tokens("code123") is None

def test_exchange_code_no_access_token(monkeypatch, module_vars):
    """Test handles response missing access_token."""
    fake_resp = FakeResponse(200, {"token_type": "Bearer"})
    monkeypatch.setattr(requests, "post", lambda *a, **k: fake_resp)
    assert google_drive_web_oauth.exchange_code_for_tokens("code123") is None

def test_exchange_code_network_error(monkeypatch, module_vars):
    """Test handles network exceptions gracefully."""
    monkeypatch.setattr(requests, "post", lambda *a, **k: (_ for _ in ()).throw(requests.RequestException("Network error")))
    result = google_drive_web_oauth.exchange_code_for_tokens("code123")
    assert result is None
