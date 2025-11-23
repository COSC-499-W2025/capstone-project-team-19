import pytest
import src.integrations.github.github_api as api
import requests

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
    data = api.gh_get("T", "x")
    assert data == []

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
        {
            "number": 1,
            "title":"Bug",
            "body":"",
            "created_at":"2024-01-01T00",
            "closed_at":None,
            "labels":[],
            "user":{"login":"me"},
            "assignees":[]
        },
        {"pull_request":{}, "user":{"login":"me"}}
    ]
    monkeypatch.setattr(api.requests, "get", lambda *a, **k: FakeResp(200, fake))
    res = api.get_gh_repo_issues("T","o","r","me")
    assert res["total_opened"] == 1
    assert len(res["user_issues"]) == 1
    assert res["user_issues"][0]["title"] == "Bug"
    assert "user_issue_comments" in res
    assert isinstance(res["user_issue_comments"], list)

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
    assert res["user"]["commits"] == 5
    assert res["user"]["additions"] == 7
    assert res["user"]["deletions"] == 3
    assert res["user"]["contribution_percent"] == 100.0

def test_gh_get_graceful_failure(monkeypatch):
    class FakeResp:
        status_code = 500
        text = "server error"
        def json(self): return {}
    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResp())
    data = api.gh_get("fake", "fake")
    assert data == {}  # No crash, returns empty


def test_get_gh_pr_reviews_calls_correct_url(monkeypatch):
    captured = {}

    def fake_gh_get(token, url, retries=6, delay=2):
        captured["token"] = token
        captured["url"] = url
        return ["ok"]

    monkeypatch.setattr(api, "gh_get", fake_gh_get)

    result = api.get_gh_pr_reviews("TOKEN", "owner", "repo", 5)

    assert result == ["ok"]
    assert captured["url"] == "https://api.github.com/repos/owner/repo/pulls/5/reviews"
    assert captured["token"] == "TOKEN"

def test_get_gh_pr_review_comments_calls_correct_url(monkeypatch):
    captured = {}

    def fake_gh_get(token, url, retries=6, delay=2):
        captured["token"] = token
        captured["url"] = url
        return ["ok"]

    monkeypatch.setattr(api, "gh_get", fake_gh_get)

    result = api.get_gh_pr_review_comments("TOKEN", "owner", "repo", 7)

    assert result == ["ok"]
    assert captured["url"] == "https://api.github.com/repos/owner/repo/pulls/7/comments"
    assert captured["token"] == "TOKEN"

def test_get_gh_reviews_for_repo_aggregates(monkeypatch):
    calls = []

    def fake_reviews(token, owner, repo, pr):
        calls.append(("reviews", pr))
        return [f"review-{pr}"]

    def fake_comments(token, owner, repo, pr):
        calls.append(("comments", pr))
        return [f"comment-{pr}"]

    monkeypatch.setattr(api, "get_gh_pr_reviews", fake_reviews)
    monkeypatch.setattr(api, "get_gh_pr_review_comments", fake_comments)

    result = api.get_gh_reviews_for_repo("TOKEN", "owner", "repo", [1, 2])

    assert result == {
        1: {
            "reviews": ["review-1"],
            "review_comments": ["comment-1"],
        },
        2: {
            "reviews": ["review-2"],
            "review_comments": ["comment-2"],
        },
    }

    assert calls == [
        ("reviews", 1),
        ("comments", 1),
        ("reviews", 2),
        ("comments", 2),
    ]

def test_get_repo_commit_timestamps(monkeypatch):
    # Return two commits on page 1, then empty list to stop.
    fake_data = [
        FakeResp(200, [
            {"commit": {"author": {"date": "2024-03-01T12:00:00Z"}}},
            {"commit": {"author": {"date": "2024-03-02T15:30:00Z"}}},
        ]),
        FakeResp(200, [])
    ]

    seq = iter(fake_data)
    monkeypatch.setattr(api.requests, "get", lambda *a, **k: next(seq))

    timestamps = api.get_repo_commit_timestamps("T", "o", "r")

    assert len(timestamps) == 2
    assert timestamps[0].year == 2024 and timestamps[0].month == 3 and timestamps[0].day == 1
    assert timestamps[1].day == 2