import pytest
MODULE = "src.google_drive_auth.text_project_setup"


def _call_setup(monkeypatch, fetch_files, user_input, oauth_return=None, link_return=None, link_side_effect=None):
    """Helper to call setup_text_project_drive_connection with patched dependencies.

    - fetch_files: value to return from _fetch_files
    - user_input: what input() should return
    - oauth_return: tuple to return from google_drive_oauth (creds, service) or exception to raise
    - link_return: dict to return from find_and_link_files
    - link_side_effect: exception to raise from find_and_link_files
    """
    # patch _fetch_files
    monkeypatch.setattr(f"{MODULE}._fetch_files", lambda conn, user_id, project_name, only_text: fetch_files)

    # patch input()
    monkeypatch.setattr("builtins.input", lambda prompt="": user_input)

    # patch google_drive_oauth
    if isinstance(oauth_return, Exception):
        def _oauth():
            raise oauth_return
        monkeypatch.setattr(f"{MODULE}.google_drive_oauth", lambda: (_oauth()))
    elif oauth_return is None:
        # leave default behavior (not patched) — but to be safe patch to return (None, None, None)
        monkeypatch.setattr(f"{MODULE}.google_drive_oauth", lambda: (None, None, None))
    else:
        monkeypatch.setattr(f"{MODULE}.google_drive_oauth", lambda: oauth_return)

    # patch get_user_email to avoid real Google calls
    monkeypatch.setattr(f"{MODULE}.get_user_email", lambda creds: "user@example.com")

    # patch find_and_link_files
    if link_side_effect is not None:
        def _link(*args, **kwargs):
            raise link_side_effect
        monkeypatch.setattr(f"{MODULE}.find_and_link_files", _link)
    else:
        monkeypatch.setattr(f"{MODULE}.find_and_link_files", lambda service, project_name, zip_file_names, conn, user_id: link_return)

    # call the function
    from src.google_drive_auth.text_project_setup import setup_text_project_drive_connection

    return setup_text_project_drive_connection(conn=None, user_id=1, project_name="proj")


def test_no_text_files(monkeypatch):
    """If no text files found, setup is skipped."""
    res = _call_setup(monkeypatch, fetch_files=[], user_input="n")
    assert res["success"] is False
    assert res["error"] == "No text files found"
    assert res["zip_file_names"] == []


def test_user_declines_connection(monkeypatch):
    """If user declines Google Drive connection, setup is skipped."""
    files = [{"file_name": "a.txt"}]
    res = _call_setup(monkeypatch, fetch_files=files, user_input="n")
    assert res["success"] is False
    assert res["error"] == "User declined connection"
    assert res["zip_file_names"] == ["a.txt"]


def test_oauth_exception_is_handled(monkeypatch):
    """If oauth raises exception, it's handled gracefully."""
    files = [{"file_name": "a.txt"}]
    res = _call_setup(monkeypatch, fetch_files=files, user_input="y", oauth_return=Exception("auth failed"))
    assert res["success"] is False
    assert "auth failed" in res["error"]


def test_oauth_returns_no_service(monkeypatch):
    """If oauth returns no service, it's handled gracefully."""
    files = [{"file_name": "a.txt"}, {"file_name": "b.txt"}]
    # oauth returns (creds, None)
    res = _call_setup(monkeypatch, fetch_files=files, user_input="y", oauth_return=(None, None, None))
    assert res["success"] is False
    assert res["error"] == "OAuth authentication failed"
    assert res["files_not_found"] == len(files)


def test_linking_success(monkeypatch):
    """Successful linking of some files."""
    files = [{"file_name": "a.txt"}, {"file_name": "b.txt"}]
    oauth = ("creds", "drive_service", "docs_service")
    link_result = {"manual": ["a.txt"], "not_found": ["b.txt"]}
    res = _call_setup(monkeypatch, fetch_files=files, user_input="y", oauth_return=oauth, link_return=link_result)
    assert res["success"] is True
    assert res["files_linked"] == 1
    assert res["files_not_found"] == 1
    assert "drive_service" in res
    assert "docs_service" in res


def test_linking_raises_exception(monkeypatch):
    """If linking raises exception, it's handled gracefully."""
    files = [{"file_name": "a.txt"}]
    oauth = ("creds", "drive_service", "docs_service")
    res = _call_setup(monkeypatch, fetch_files=files, user_input="y", oauth_return=oauth, link_side_effect=RuntimeError("link failed"))
    assert res["success"] is False
    assert "link failed" in res["error"]
