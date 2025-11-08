import pytest
import src.github.github_api as api

class FakeResp:
    def __init__(self, status, data):
        self.status_code = status
        self._data = data
        self.text = str(data)
    def json(self):
        return self._data

def fake_get_sequence(monkeypatch, responses):
    seq = iter(responses)
    monkeypatch.setattr(api.requests, "get", lambda *a, **k: next(seq))

def test_list_user_repos(monkeypatch):
    personal = [{"full_name": "me/one"}, {"full_name": "me/Two"}]
    orgs = [{"login": "MyOrg"}]
    org_repos = [
        {"full_name": "MyOrg/alpha", "permissions": {"push": True}},
        {"full_name": "MyOrg/beta", "permissions": {"push": False}},
    ]

    def fake_get(url, headers):
        if "user/repos" in url: return FakeResp(200, personal)
        if "user/orgs" in url: return FakeResp(200, orgs)
        if "orgs/MyOrg/repos" in url: return FakeResp(200, org_repos)
        return FakeResp(200, [])

    monkeypatch.setattr(api.requests, "get", fake_get)

    assert api.list_user_repos("x") == ["me/one", "me/Two", "MyOrg/alpha"]

def test_list_user_repos_empty(monkeypatch):
    fake_get_sequence(monkeypatch, [
        FakeResp(200, []), FakeResp(200, [])
    ])
    assert api.list_user_repos("t") == []

def test_gh_get_success(monkeypatch):
    monkeypatch.setattr(api.requests, "get", lambda *a, **k: FakeResp(200, {"ok": True}))
    assert api.gh_get("T", "x") == {"ok": True}

def test_gh_get_missing_token():
    with pytest.raises(ValueError):
        api.gh_get("", "x")

def test_gh_get_failure(monkeypatch):
    monkeypatch.setattr(api.requests, "get", lambda *a, **k: FakeResp(500, {"err": True}))
    with pytest.raises(RuntimeError):
        api.gh_get("T", "x")

def test_get_authenticated_user(monkeypatch):
    data = {"login": "me", "id":1, "name":"A", "email":"b", "html_url":"url"}
    monkeypatch.setattr(api.requests, "get", lambda *a, **k: FakeResp(200, data))
    res = api.get_authenticated_user("T")
    assert res["login"] == "me"
    assert res["profile_url"] == "url"

def test_commit_activity(monkeypatch):
    fake_get_sequence(monkeypatch, [
        FakeResp(200, [
            {"commit":{"author":{"date":"2024-01-01T00"}}},
            {"commit":{"author":{"date":"2024-01-01T01"}}},
        ]),
        FakeResp(200, [])
    ])
    assert api.get_gh_repo_commit_activity("T","o","r","me") == {"2024-01-01": 2}

def test_get_issues(monkeypatch):
    fake = [
        {"title":"Bug","body":"","created_at":"2024-01-01T00","closed_at":None,
         "labels":[],"user":{"login":"me"},"assignees":[]},
        {"pull_request":{}, "user":{"login":"me"}},
    ]
    monkeypatch.setattr(api.requests, "get", lambda *a, **k: FakeResp(200, fake))
    res = api.get_gh_repo_issues("T","o","r","me")
    assert res["total_opened"] == 1
    assert len(res["user_issues"]) == 1
    assert res["user_issues"][0]["title"] == "Bug"

def test_get_prs(monkeypatch):
    fake = [
        {"user":{"login":"me"},
         "title":"PR1","body":"",
         "created_at":"2024-02-01T00",
         "merged_at":"2024-02-02T00",
         "labels":[],"state":"closed"},
        {"user":{"login":"other"}},
    ]
    monkeypatch.setattr(api.requests, "get", lambda *a, **k: FakeResp(200, fake))
    res = api.get_gh_repo_prs("T","o","r","me")
    assert res["total_opened"] == 1
    assert res["total_merged"] == 1
    assert res["user_prs"][0]["merged"] is True

def test_contributions_poll(monkeypatch):
    fake_get_sequence(monkeypatch, [
        FakeResp(200, {"message":"202"}),
        FakeResp(200, [{
            "author":{"login":"me"},
            "total":5,
            "weeks":[{"a":3,"d":1}, {"a":4,"d":2}]
        }])
    ])
    res = api.get_gh_repo_contributions("T","o","r","me")
    assert res["commits"] == 5
    assert res["additions"] == 7
    assert res["deletions"] == 3
    assert res["contribution_percent"] == 100.0
