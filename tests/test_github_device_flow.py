import pytest
import requests
import time
from src.github.github_device_flow import request_device_code, poll_for_token
from src.github.github_device_flow import GITHUB_CLIENT_ID, DEVICE_CODE_URL, TOKEN_URL


class FakeResponse:
    def __init__(self, status, data):
        self.status_code = status
        self._data = data

    def json(self):
        return self._data

    @property
    def text(self):
        return str(self._data)


# request_device_code tests
def test_request_device_code_success(monkeypatch):
    fake_resp = FakeResponse(200, {"device_code": "abc", "user_code": "xyz"})

    def fake_post(url, data, headers):
        assert url == DEVICE_CODE_URL
        assert data["client_id"] == GITHUB_CLIENT_ID
        assert "scope" in data
        return fake_resp

    monkeypatch.setattr(requests, "post", fake_post)

    result = request_device_code("repo")
    assert result == {"device_code": "abc", "user_code": "xyz"}


def test_request_device_code_failure(monkeypatch):
    fake_resp = FakeResponse(400, {"error": "bad request"})

    monkeypatch.setattr(requests, "post", lambda *a, **k: fake_resp)

    with pytest.raises(RuntimeError):
        request_device_code()


# poll_for_token tests
def test_poll_for_token_immediate_success(monkeypatch):
    fake_resp = FakeResponse(200, {"access_token": "TOKEN123"})

    monkeypatch.setattr(requests, "post", lambda *a, **k: fake_resp)

    token = poll_for_token("abc", 1)
    assert token == "TOKEN123"


def test_poll_for_token_waits_and_succeeds(monkeypatch):
    responses = iter([
        FakeResponse(200, {"error": "authorization_pending"}),
        FakeResponse(200, {"access_token": "TOKEN456"})
    ])

    monkeypatch.setattr(requests, "post", lambda *a, **k: next(responses))
    monkeypatch.setattr(time, "sleep", lambda x: None)  # skip wait

    token = poll_for_token("abc", 1)
    assert token == "TOKEN456"


def test_poll_for_token_error(monkeypatch):
    fake_resp = FakeResponse(200, {"error": "access_denied"})

    monkeypatch.setattr(requests, "post", lambda *a, **k: fake_resp)

    with pytest.raises(RuntimeError):
        poll_for_token("abc", 1)
