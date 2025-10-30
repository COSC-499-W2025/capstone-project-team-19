import pytest, requests
import src.github_auth.github_api as api
from src.github_auth.link_repo import list_user_repos

class FakeResponse:
    def __init__(self, status, data):
        self.status_code = status
        self._data = data

    def json(self):
        return self._data

def test_list_user_repos(monkeypatch):
    fake_personal = [{"full_name": "me/one"}, {"full_name": "me/Two"}]
    fake_orgs = [{"login": "MyOrg"}]
    fake_org_repos = [{"full_name": "MyOrg/alpha", "permissions": {"push": True}},
                      {"full_name": "MyOrg/beta", "permissions": {"push": False}}]

    class FakeResp:
        def __init__(self, json, code=200):
            self._j = json; self.status_code = code
        def json(self): return self._j

    def fake_get(url, headers):
        if "user/repos" in url: return FakeResp(fake_personal)
        if "user/orgs" in url: return FakeResp(fake_orgs)
        if "orgs/MyOrg/repos" in url: return FakeResp(fake_org_repos)
        return FakeResp([])

    monkeypatch.setattr(api.requests, "get", fake_get)

    repos = api.list_user_repos("fake")
    assert repos == ["me/one", "me/Two", "MyOrg/alpha"]


def test_returns_empty_when_no_repos(monkeypatch):
    # 1) personal repos call returns empty
    # 2) orgs call returns empty
    sequence = iter([
        FakeResponse(200, []),  # user repos
        FakeResponse(200, []),  # orgs
    ])

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: next(sequence))

    assert list_user_repos("TOKEN123") == []


def test_personal_repos(monkeypatch):
    sequence = iter([
        FakeResponse(200, [{"full_name": "user/RepoA"}, {"full_name": "user/RepoB"}]),
        FakeResponse(200, []),  # orgs
    ])

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: next(sequence))

    assert list_user_repos("X") == ["user/RepoA", "user/RepoB"]


def test_org_repos_with_push(monkeypatch):
    sequence = iter([
        FakeResponse(200, []),  # personal repos
        FakeResponse(200, [{"login": "org1"}]),  # org list
        FakeResponse(200, [
            {"full_name": "org1/Repo1", "permissions": {"push": True}},
            {"full_name": "org1/Repo2", "permissions": {"push": False}},
        ]),
    ])

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: next(sequence))

    assert list_user_repos("X") == ["org1/Repo1"]


def test_dedup_case_insensitive(monkeypatch):
    sequence = iter([
        FakeResponse(200, [{"full_name": "user/Repo"}]),
        FakeResponse(200, []),  # orgs
    ])

    # Simulate org returns same repo name in caps
    sequence = iter([
        FakeResponse(200, [{"full_name": "User/Repo"}]),  # personal
        FakeResponse(200, [{"login": "Org"}]),  # org list
        FakeResponse(200, [{"full_name": "user/repo", "permissions": {"push": True}}])
    ])

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: next(sequence))

    assert list_user_repos("X") == ["User/Repo"]


def test_api_failure(monkeypatch):
    # personal repos fails
    # orgs succeeds but no orgs
    sequence = iter([
        FakeResponse(500, None),
        FakeResponse(200, []),
    ])

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: next(sequence))

    assert list_user_repos("X") == []


def test_auth_header_used(monkeypatch):
    captured_headers = {}

    def fake_get(url, headers):
        captured_headers["header"] = headers
        return FakeResponse(200, [])

    monkeypatch.setattr(requests, "get", fake_get)

    list_user_repos("MYTOKEN")

    assert captured_headers["header"]["Authorization"] == "Bearer MYTOKEN"