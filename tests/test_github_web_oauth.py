import pytest
import requests
from urllib.parse import parse_qs, urlparse
from src.integrations.github import github_web_oauth

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
    monkeypatch.setattr(github_web_oauth, "GITHUB_CLIENT_ID", client_id)
    monkeypatch.setattr(github_web_oauth, "GITHUB_CLIENT_SECRET", client_secret)
    if redirect_uri:
        monkeypatch.setattr(github_web_oauth, "GITHUB_REDIRECT_URI", redirect_uri)
    else:
        monkeypatch.setattr(github_web_oauth, "GITHUB_REDIRECT_URI", "http://localhost:8000/auth/github/callback")

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

# TESTS for generate_github_auth_url

def test_generate_auth_url_success_with_params(monkeypatch, module_vars):
    """Test URL generation with default and custom parameters."""
    # Test default
    url = github_web_oauth.generate_github_auth_url()
    params = parse_auth_url(url)
    assert params["client_id"][0] == "test_client_id"
    assert params["redirect_uri"][0] == "http://localhost:8000/auth/github/callback"
    assert params["scope"][0] == "repo read:user read:org"
    assert url.startswith("https://github.com/login/oauth/authorize")
    
    url_with_state = github_web_oauth.generate_github_auth_url(state="abc123")
    params_state = parse_auth_url(url_with_state)
    assert params_state["state"][0] == "abc123"
    
    url_custom = github_web_oauth.generate_github_auth_url(scope="repo")
    params_custom = parse_auth_url(url_custom)
    assert params_custom["scope"][0] == "repo"

def test_generate_auth_url_custom_redirect(monkeypatch):
    """Test URL generation uses custom redirect URI."""
    setup_module_vars(monkeypatch, redirect_uri="http://example.com/callback")
    url = github_web_oauth.generate_github_auth_url()
    
    params = parse_auth_url(url)
    assert params["redirect_uri"][0] == "http://example.com/callback"

def test_generate_auth_url_missing_client_id(monkeypatch):
    """Test raises ValueError when GITHUB_CLIENT_ID is missing."""
    setup_module_vars(monkeypatch, client_id=None)
    
    with pytest.raises(ValueError, match="GITHUB_CLIENT_ID"):
        github_web_oauth.generate_github_auth_url()

# TESTS FOR exchange_code_for_token 
def test_exchange_code_success(monkeypatch, module_vars):
    """Test successful code exchange with and without state."""
    fake_resp = FakeResponse(200, {
        "access_token": "token123",
        "token_type": "bearer",
        "scope": "repo"
    })
    captured_data = {}
    def fake_post(url, data, headers):
        captured_data.update(data)
        return fake_resp
    
    monkeypatch.setattr(requests, "post", fake_post)

    result = github_web_oauth.exchange_code_for_token("code123")
    assert result["access_token"] == "token123"
    assert result["token_type"] == "bearer"
    assert captured_data["code"] == "code123"

    captured_data.clear()
    result = github_web_oauth.exchange_code_for_token("code456", state="state789")
    assert result["access_token"] == "token123"
    assert captured_data["state"] == "state789"

def test_exchange_code_missing_credentials(monkeypatch):
    """Test raises ValueError when credentials are missing."""
    setup_module_vars(monkeypatch, client_id=None, client_secret="secret")
    with pytest.raises(ValueError, match="GITHUB_CLIENT_ID"):
        github_web_oauth.exchange_code_for_token("code123")
    
    setup_module_vars(monkeypatch, client_secret=None)
    with pytest.raises(ValueError, match="GITHUB_CLIENT_SECRET"):
        github_web_oauth.exchange_code_for_token("code123")


def test_exchange_code_error_responses(monkeypatch, module_vars):
    """Test handles various error responses from GitHub."""
    fake_resp_error = FakeResponse(200, {"error": "invalid_code", "error_description": "Bad code"})
    monkeypatch.setattr(requests, "post", lambda *a, **k: fake_resp_error)
    assert github_web_oauth.exchange_code_for_token("badcode") is None
    
    fake_resp_http = FakeResponse(400, {"error": "bad_request"})
    monkeypatch.setattr(requests, "post", lambda *a, **k: fake_resp_http)
    assert github_web_oauth.exchange_code_for_token("code123") is None

    fake_resp_no_token = FakeResponse(200, {"token_type": "bearer"})
    monkeypatch.setattr(requests, "post", lambda *a, **k: fake_resp_no_token)
    assert github_web_oauth.exchange_code_for_token("code123") is None


def test_exchange_code_network_error(monkeypatch, module_vars):
    """Test handles network exceptions."""
    monkeypatch.setattr(requests, "post", lambda *a, **k: (_ for _ in ()).throw(requests.RequestException("Network error")))
    result = github_web_oauth.exchange_code_for_token("code123")
    assert result is None