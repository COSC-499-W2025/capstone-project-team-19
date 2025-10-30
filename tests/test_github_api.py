import pytest
import src.github_auth.github_api as api

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
    assert repos == ["me/one", "MyOrg/alpha", "me/two"]  # lowercase sorted
