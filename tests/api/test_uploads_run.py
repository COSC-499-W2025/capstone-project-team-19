from __future__ import annotations

from src.db.uploads import create_upload


def _create_upload(seed_conn, *, user_id: int, status: str, state: dict) -> int:
    return create_upload(
        seed_conn,
        user_id=user_id,
        zip_name="test.zip",
        zip_path="/tmp/test.zip",
        status=status,
        state=state,
    )


def test_run_preflight_ready_all_scope(client, auth_headers, seed_conn):
    upload_id = _create_upload(
        seed_conn,
        user_id=1,
        status="needs_file_roles",
        state={
            "dedup_project_keys": {
                "BuddyCart": 1,
                "paper": 2,
            },
            "classifications": {
                "BuddyCart": "individual",
                "paper": "collaborative",
            },
            "project_types_auto": {
                "BuddyCart": "code",
                "paper": "text",
            },
            "project_types_mixed": [],
            "project_types_unknown": [],
            "file_roles": {
                "paper": {"main_file": "real_test/paper/main.pdf"},
            },
        },
    )

    res = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "all", "force_rerun": False},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["upload_id"] == upload_id
    assert body["data"]["scope"] == "all"
    assert body["data"]["ready"] is True
    assert body["data"]["warnings"] == []


def test_run_preflight_blocks_unresolved_project_types(client, auth_headers, seed_conn):
    upload_id = _create_upload(
        seed_conn,
        user_id=1,
        status="needs_file_roles",
        state={
            "dedup_project_keys": {"capstone-project-team-19": 1},
            "classifications": {"capstone-project-team-19": "collaborative"},
            "project_types_auto": {},
            "project_types_manual": {},
            "project_types_mixed": ["capstone-project-team-19"],
            "project_types_unknown": [],
        },
    )

    res = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "all", "force_rerun": False},
    )
    assert res.status_code == 409
    body = res.json()
    assert body["detail"]["message"] == "Upload state is incomplete for analysis run"
    assert body["detail"]["errors"] == [
        {
            "code": "unresolved_project_types",
            "projects": ["capstone-project-team-19"],
        }
    ]


def test_run_preflight_scope_filters_missing_main_file(client, auth_headers, seed_conn):
    upload_id = _create_upload(
        seed_conn,
        user_id=1,
        status="needs_file_roles",
        state={
            "dedup_project_keys": {
                "BuddyCart": 1,
                "paper": 2,
            },
            "classifications": {
                "BuddyCart": "individual",
                "paper": "collaborative",
            },
            "project_types_auto": {
                "BuddyCart": "code",
                "paper": "text",
            },
            "project_types_mixed": [],
            "project_types_unknown": [],
            "file_roles": {},
        },
    )

    # Individual scope only sees BuddyCart (code), so this is ready.
    ok = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "individual", "force_rerun": False},
    )
    assert ok.status_code == 200
    assert ok.json()["data"]["ready"] is True

    # Collaborative scope includes paper (text), so missing main_file is a blocker.
    bad = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "collaborative", "force_rerun": False},
    )
    assert bad.status_code == 409
    assert bad.json()["detail"]["errors"] == [{"code": "missing_main_file", "project": "paper"}]


def test_run_preflight_collaborative_scope_with_no_projects_returns_409(client, auth_headers, seed_conn):
    upload_id = _create_upload(
        seed_conn,
        user_id=1,
        status="needs_file_roles",
        state={
            "dedup_project_keys": {"BuddyCart": 1},
            "classifications": {"BuddyCart": "individual"},
            "project_types_auto": {"BuddyCart": "code"},
            "project_types_mixed": [],
            "project_types_unknown": [],
        },
    )

    res = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "collaborative", "force_rerun": False},
    )
    assert res.status_code == 409
    assert res.json()["detail"]["errors"] == [{"code": "no_projects_in_scope", "scope": "collaborative"}]


def test_run_preflight_returns_404_for_missing_upload(client, auth_headers):
    res = client.post(
        "/projects/upload/999999/run",
        headers=auth_headers,
        json={"scope": "all", "force_rerun": False},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Upload not found"
