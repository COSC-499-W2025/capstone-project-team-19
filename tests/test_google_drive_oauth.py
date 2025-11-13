import pytest
from unittest.mock import Mock

from src.integrations.google_drive.google_drive_auth.google_drive_oauth import google_drive_oauth


@pytest.fixture
def mock_credentials_file(tmp_path):
    """Create a temporary credentials.json file."""
    creds_file = tmp_path / "credentials.json"
    creds_data = {
        "installed": {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }
    import json
    creds_file.write_text(json.dumps(creds_data))
    return str(creds_file)


def test_google_drive_oauth_happy_path(monkeypatch, mock_credentials_file):
    """Test successful OAuth flow."""
    # Mock credentials object
    mock_creds = Mock()
    mock_creds.token = "fake_access_token"
    mock_creds.refresh_token = "fake_refresh_token"
    mock_creds.expiry = None
    
    # Mock service objects
    mock_drive_service = Mock()
    mock_docs_service = Mock()
    
    # Mock InstalledAppFlow
    mock_flow = Mock()
    mock_flow.run_local_server.return_value = mock_creds
    mock_flow_class = Mock()
    mock_flow_class.from_client_secrets_file.return_value = mock_flow
    
    monkeypatch.setattr(
        "src.integrations.google_drive.google_drive_auth.google_drive_oauth.InstalledAppFlow",
        mock_flow_class
    )
    
    # Mock build function
    def mock_build(api_name, api_version, credentials=None):
        if api_name == "drive":
            return mock_drive_service
        if api_name == "docs":
            return mock_docs_service
        raise AssertionError(f"Unexpected build call: {api_name} {api_version}")
    monkeypatch.setattr(
        "src.integrations.google_drive.google_drive_auth.google_drive_oauth.build",
        mock_build
    )
    
    # Run OAuth
    creds, drive_service, docs_service = google_drive_oauth(mock_credentials_file)
    
    assert creds == mock_creds
    assert drive_service == mock_drive_service
    assert docs_service == mock_docs_service
    assert mock_flow_class.from_client_secrets_file.called


def test_google_drive_oauth_missing_credentials_file():
    """Test error when credentials file is missing."""
    with pytest.raises(FileNotFoundError):
        google_drive_oauth("/nonexistent/path/credentials.json")


def test_google_drive_oauth_flow_error(monkeypatch, mock_credentials_file):
    """Test error during OAuth flow."""
    # Mock InstalledAppFlow to raise exception
    mock_flow = Mock()
    mock_flow.run_local_server.side_effect = Exception("OAuth error")
    mock_flow_class = Mock()
    mock_flow_class.from_client_secrets_file.return_value = mock_flow
    
    monkeypatch.setattr(
        "src.integrations.google_drive.google_drive_auth.google_drive_oauth.InstalledAppFlow",
        mock_flow_class
    )
    
    creds, drive_service, docs_service = google_drive_oauth(mock_credentials_file)
    
    assert creds is None
    assert drive_service is None
    assert docs_service is None


def test_google_drive_oauth_default_credentials_path(monkeypatch, tmp_path):
    """Test default credentials path resolution."""
    # Create credentials file in module directory structure
    module_dir = tmp_path / "src" / "google_drive_auth"
    module_dir.mkdir(parents=True)
    creds_file = module_dir / "credentials.json"
    creds_file.write_text('{"installed": {"client_id": "test", "client_secret": "test"}}')
    
    mock_creds = Mock()
    mock_creds.token = "token"
    mock_creds.refresh_token = "refresh"
    mock_creds.expiry = None
    
    mock_drive_service = Mock()
    mock_docs_service = Mock()
    
    mock_flow = Mock()
    mock_flow.run_local_server.return_value = mock_creds
    mock_flow_class = Mock()
    mock_flow_class.from_client_secrets_file.return_value = mock_flow
    
    monkeypatch.setattr(
        "src.integrations.google_drive.google_drive_auth.google_drive_oauth.InstalledAppFlow",
        mock_flow_class
    )
    
    def mock_build(api_name, api_version, credentials=None):
        if api_name == "drive":
            return mock_drive_service
        if api_name == "docs":
            return mock_docs_service
        raise AssertionError(f"Unexpected build call: {api_name} {api_version}")
    monkeypatch.setattr(
        "src.integrations.google_drive.google_drive_auth.google_drive_oauth.build",
        mock_build
    )
    
    # Mock the path resolution to use our temp directory
    def mock_dirname(path):
        return str(module_dir)
    
    def mock_abspath(path):
        return str(module_dir / "__file__")
    
    monkeypatch.setattr(
        "src.integrations.google_drive.google_drive_auth.google_drive_oauth.os.path.dirname",
        mock_dirname
    )
    monkeypatch.setattr(
        "src.integrations.google_drive.google_drive_auth.google_drive_oauth.os.path.abspath",
        mock_abspath
    )
    monkeypatch.setattr(
        "src.integrations.google_drive.google_drive_auth.google_drive_oauth.os.path.exists",
        lambda x: str(x) == str(creds_file)
    )
    
    # Call without path - should use default
    creds, drive_service, docs_service = google_drive_oauth()
    
    # Should attempt to use default path
    assert mock_flow_class.from_client_secrets_file.called
    assert creds == mock_creds
    assert drive_service == mock_drive_service
    assert docs_service == mock_docs_service
