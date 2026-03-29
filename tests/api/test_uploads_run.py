from __future__ import annotations

from datetime import datetime, timezone
from src.db.uploads import create_upload


def _set_internal_consent(seed_conn, *, user_id: int, status: str = "accepted") -> None:
    seed_conn.execute(
        "INSERT INTO consent_log(user_id, status, timestamp) VALUES (?, ?, ?)",
        (user_id, status, datetime.now(timezone.utc).isoformat()),
    )
    seed_conn.commit()


def _set_external_consent(seed_conn, *, user_id: int, status: str = "accepted") -> None:
    seed_conn.execute(
        "INSERT INTO external_consent(user_id, status, timestamp) VALUES (?, ?, ?)",
        (user_id, status, datetime.now(timezone.utc).isoformat()),
    )
    seed_conn.commit()


def _create_upload(
    seed_conn,
    *,
    user_id: int,
    status: str,
    state: dict,
    seed_internal_consent: bool = True,
    seed_external_consent: bool = True,
) -> int:
    if seed_internal_consent:
        _set_internal_consent(seed_conn, user_id=user_id, status="accepted")
    if seed_external_consent:
        _set_external_consent(seed_conn, user_id=user_id, status="accepted")

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
            "dedup_version_keys": {
                "BuddyCart": 101,
                "paper": 102,
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
            "run_inputs": {
                "projects": {
                    "BuddyCart": {
                        "capabilities": {
                            "git": {
                                "repo_detected": True,
                                "commit_count_hint": 10,
                                "multi_author_hint": False,
                                "selected_identity_indices": [],
                            }
                        },
                        "integrations": {
                            "github": {"state": "connected", "repo_linked": True},
                        },
                        "manual_inputs": {
                            "manual_project_summary_set": True,
                            "key_role_set": True,
                        },
                    },
                    "paper": {
                        "integrations": {
                            "drive": {"state": "connected", "linked_files_count": 2},
                        },
                        "manual_inputs": {
                            "contribution_sections_set": True,
                            "supporting_text_files_set": True,
                            "manual_contribution_summary_set": True,
                            "key_role_set": True,
                        },
                    },
                }
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
            "dedup_version_keys": {"capstone-project-team-19": 11},
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


def test_run_preflight_manual_type_overrides_stale_mixed_list(client, auth_headers, seed_conn):
    upload_id = _create_upload(
        seed_conn,
        user_id=1,
        status="needs_file_roles",
        state={
            "dedup_project_keys": {"capstone-project-team-19": 1},
            "dedup_version_keys": {"capstone-project-team-19": 11},
            "classifications": {"capstone-project-team-19": "collaborative"},
            "project_types_auto": {},
            "project_types_manual": {"capstone-project-team-19": "code"},
            "project_types_mixed": ["capstone-project-team-19"],
            "project_types_unknown": [],
            "run_inputs": {
                "projects": {
                    "capstone-project-team-19": {
                        "capabilities": {
                            "git": {
                                "repo_detected": True,
                                "commit_count_hint": 10,
                                "multi_author_hint": False,
                            }
                        },
                        "integrations": {"github": {"state": "connected", "repo_linked": True}},
                        "manual_inputs": {"manual_contribution_summary_set": True, "key_role_set": True},
                    }
                }
            },
        },
    )

    res = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "all", "force_rerun": False},
    )
    assert res.status_code == 200
    assert res.json()["data"]["ready"] is True


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
            "dedup_version_keys": {
                "BuddyCart": 11,
                "paper": 12,
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
            "dedup_version_keys": {"BuddyCart": 11},
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
    assert res.json()["detail"]["errors"] == [{"code": "no_projects_for_scope", "scope": "collaborative"}]


def test_run_preflight_returns_404_for_missing_upload(client, auth_headers):
    res = client.post(
        "/projects/upload/999999/run",
        headers=auth_headers,
        json={"scope": "all", "force_rerun": False},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Upload not found"


def test_run_preflight_blocks_missing_internal_consent(client, auth_headers, seed_conn):
    upload_id = _create_upload(
        seed_conn,
        user_id=1,
        status="needs_file_roles",
        state={
            "dedup_project_keys": {"BuddyCart": 1},
            "dedup_version_keys": {"BuddyCart": 11},
            "classifications": {"BuddyCart": "individual"},
            "project_types_auto": {"BuddyCart": "code"},
            "project_types_mixed": [],
            "project_types_unknown": [],
        },
        seed_internal_consent=False,
    )

    res = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "all", "force_rerun": False},
    )
    assert res.status_code == 409
    body = res.json()
    assert body["detail"]["message"] == "Upload state is incomplete for analysis run"
    assert {"code": "missing_internal_consent"} in body["detail"]["errors"]


def test_run_preflight_blocks_upload_not_ready_status(client, auth_headers, seed_conn):
    upload_id = _create_upload(
        seed_conn,
        user_id=1,
        status="needs_classification",
        state={
            "dedup_project_keys": {"BuddyCart": 1},
            "dedup_version_keys": {"BuddyCart": 11},
            "classifications": {"BuddyCart": "individual"},
            "project_types_auto": {"BuddyCart": "code"},
        },
    )
    res = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "all", "force_rerun": False},
    )
    assert res.status_code == 409
    assert res.json()["detail"]["errors"] == [{"code": "upload_not_ready", "status": "needs_classification"}]


def test_run_preflight_blocks_missing_version_keys(client, auth_headers, seed_conn):
    upload_id = _create_upload(
        seed_conn,
        user_id=1,
        status="needs_file_roles",
        state={
            "dedup_project_keys": {"BuddyCart": 1},
            "dedup_version_keys": {},
            "classifications": {"BuddyCart": "individual"},
            "project_types_auto": {"BuddyCart": "code"},
        },
    )
    res = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "all", "force_rerun": False},
    )
    assert res.status_code == 409
    assert {"code": "missing_version_keys", "projects": ["BuddyCart"]} in res.json()["detail"]["errors"]


def test_run_preflight_returns_matrix_warnings_for_code_individual(client, auth_headers, seed_conn):
    _set_internal_consent(seed_conn, user_id=1, status="accepted")
    _set_external_consent(seed_conn, user_id=1, status="rejected")

    upload_id = create_upload(
        seed_conn,
        user_id=1,
        zip_name="test.zip",
        zip_path="/tmp/test.zip",
        status="needs_file_roles",
        state={
            "dedup_project_keys": {"BuddyCart": 1},
            "dedup_version_keys": {"BuddyCart": 11},
            "classifications": {"BuddyCart": "individual"},
            "project_types_auto": {"BuddyCart": "code"},
            "project_types_mixed": [],
            "project_types_unknown": [],
            "run_inputs": {
                "projects": {
                    "BuddyCart": {
                        "capabilities": {
                            "git": {
                                "repo_detected": False,
                                "commit_count_hint": 0,
                                "multi_author_hint": False,
                            }
                        },
                        "integrations": {
                            "github": {
                                "state": "unset",
                                "repo_linked": False,
                            }
                        },
                        "manual_inputs": {
                            "manual_project_summary_set": False,
                            "key_role_set": False,
                        },
                    }
                }
            },
        },
    )

    res = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "individual", "force_rerun": False},
    )
    assert res.status_code == 200
    warnings = res.json()["data"]["warnings"]
    assert {"code": "no_git_repo_detected", "project": "BuddyCart"} in warnings
    assert {"code": "github_not_configured", "project": "BuddyCart"} in warnings
    assert {"code": "missing_github_link", "project": "BuddyCart"} in warnings
    assert {"code": "llm_disabled", "project": "BuddyCart"} in warnings
    assert {"code": "missing_manual_summary", "project": "BuddyCart"} in warnings
    assert {"code": "missing_key_role", "project": "BuddyCart"} in warnings


def test_run_preflight_returns_missing_git_identities_warning_for_collab_code(client, auth_headers, seed_conn):
    upload_id = _create_upload(
        seed_conn,
        user_id=1,
        status="needs_file_roles",
        state={
            "dedup_project_keys": {"capstone-project-team-19": 1},
            "dedup_version_keys": {"capstone-project-team-19": 11},
            "classifications": {"capstone-project-team-19": "collaborative"},
            "project_types_auto": {"capstone-project-team-19": "code"},
            "project_types_mixed": [],
            "project_types_unknown": [],
            "run_inputs": {
                "projects": {
                    "capstone-project-team-19": {
                        "capabilities": {
                            "git": {
                                "repo_detected": True,
                                "commit_count_hint": 12,
                                "multi_author_hint": True,
                                "selected_identity_indices": [],
                            }
                        },
                        "integrations": {"github": {"state": "connected", "repo_linked": True}},
                        "manual_inputs": {
                            "manual_contribution_summary_set": True,
                            "key_role_set": True,
                        },
                    }
                }
            },
        },
    )

    res = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "collaborative", "force_rerun": False},
    )
    assert res.status_code == 200
    warnings = res.json()["data"]["warnings"]
    assert {"code": "missing_git_identities", "project": "capstone-project-team-19"} in warnings


def test_run_preflight_returns_missing_drive_links_warning_for_collab_text(client, auth_headers, seed_conn):
    upload_id = _create_upload(
        seed_conn,
        user_id=1,
        status="needs_file_roles",
        state={
            "dedup_project_keys": {"paper": 1},
            "dedup_version_keys": {"paper": 11},
            "classifications": {"paper": "collaborative"},
            "project_types_auto": {"paper": "text"},
            "project_types_mixed": [],
            "project_types_unknown": [],
            "file_roles": {"paper": {"main_file": "real_test/paper/main.pdf"}},
            "run_inputs": {
                "projects": {
                    "paper": {
                        "integrations": {"drive": {"state": "connected", "linked_files_count": 0}},
                        "manual_inputs": {
                            "contribution_sections_set": True,
                            "supporting_text_files_set": True,
                            "manual_contribution_summary_set": True,
                            "key_role_set": True,
                        },
                    }
                }
            },
        },
    )

    res = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "collaborative", "force_rerun": False},
    )
    assert res.status_code == 200
    warnings = res.json()["data"]["warnings"]
    assert {"code": "missing_drive_links", "project": "paper"} in warnings


def test_run_preflight_does_not_require_contributed_sections_for_individual_text(client, auth_headers, seed_conn):
    upload_id = _create_upload(
        seed_conn,
        user_id=1,
        status="needs_file_roles",
        state={
            "dedup_project_keys": {"journal": 1},
            "dedup_version_keys": {"journal": 11},
            "classifications": {"journal": "individual"},
            "project_types_auto": {"journal": "text"},
            "project_types_mixed": [],
            "project_types_unknown": [],
            "file_roles": {"journal": {"main_file": "real_test/journal/main.txt"}},
            "run_inputs": {
                "projects": {
                    "journal": {
                        "manual_inputs": {
                            "manual_project_summary_set": True,
                            "key_role_set": True,
                        },
                    }
                }
            },
        },
    )

    res = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "individual", "force_rerun": False},
    )
    assert res.status_code == 200
    warnings = res.json()["data"]["warnings"]
    assert {"code": "missing_contribution_sections", "project": "journal"} not in warnings


def test_run_tracks_completion_by_scope_and_sets_done_only_after_all_scopes(client, auth_headers, seed_conn, monkeypatch, tmp_path):
    zip_path = tmp_path / "ready.zip"
    zip_path.write_bytes(b"placeholder")

    upload_id = _create_upload(
        seed_conn,
        user_id=1,
        status="needs_file_roles",
        state={
            "zip_path": str(zip_path),
            "dedup_project_keys": {"BuddyCart": 1, "paper": 2},
            "dedup_version_keys": {"BuddyCart": 11, "paper": 12},
            "classifications": {"BuddyCart": "individual", "paper": "collaborative"},
            "project_types_auto": {"BuddyCart": "code", "paper": "text"},
            "project_types_mixed": [],
            "project_types_unknown": [],
            "file_roles": {"paper": {"main_file": "ready/paper/main.pdf"}},
        },
    )

    monkeypatch.setattr(
        "src.services.uploads_run_service.has_executable_files_for_scope",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        "src.services.uploads_run_service.execute_upload_scope_analysis",
        lambda *args, **kwargs: {"executed_count": 2},
    )

    res_ind = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "individual", "force_rerun": False},
    )
    assert res_ind.status_code == 200

    state_after_ind = client.get(f"/projects/upload/{upload_id}", headers=auth_headers).json()["data"]
    assert state_after_ind["status"] == "needs_file_roles"
    completed = (state_after_ind["state"].get("run_state") or {}).get("completed_scopes") or []
    assert completed == ["individual"]

    res_collab = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "collaborative", "force_rerun": False},
    )
    assert res_collab.status_code == 200

    state_after_collab = client.get(f"/projects/upload/{upload_id}", headers=auth_headers).json()["data"]
    assert state_after_collab["status"] == "done"
    completed = sorted((state_after_collab["state"].get("run_state") or {}).get("completed_scopes") or [])
    assert completed == ["collaborative", "individual"]


def test_run_blocks_scope_rerun_without_force(client, auth_headers, seed_conn, monkeypatch, tmp_path):
    zip_path = tmp_path / "ready2.zip"
    zip_path.write_bytes(b"placeholder")

    upload_id = _create_upload(
        seed_conn,
        user_id=1,
        status="needs_file_roles",
        state={
            "zip_path": str(zip_path),
            "run_state": {"completed_scopes": ["individual"]},
            "dedup_project_keys": {"BuddyCart": 1},
            "dedup_version_keys": {"BuddyCart": 11},
            "classifications": {"BuddyCart": "individual"},
            "project_types_auto": {"BuddyCart": "code"},
            "project_types_mixed": [],
            "project_types_unknown": [],
        },
    )

    monkeypatch.setattr(
        "src.services.uploads_run_service.has_executable_files_for_scope",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        "src.services.uploads_run_service.execute_upload_scope_analysis",
        lambda *args, **kwargs: {"executed_count": 1},
    )

    blocked = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "individual", "force_rerun": False},
    )
    assert blocked.status_code == 409
    assert blocked.json()["detail"] == {"code": "scope_already_completed", "scope": "individual"}

    forced = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "individual", "force_rerun": True},
    )
    assert forced.status_code == 200


def test_run_check_mode_reports_readiness_and_never_executes(
    client, auth_headers, seed_conn, monkeypatch, tmp_path
):
    blocked_upload_id = _create_upload(
        seed_conn,
        user_id=1,
        status="needs_file_roles",
        state={
            "dedup_project_keys": {"capstone-project-team-19": 1},
            "dedup_version_keys": {"capstone-project-team-19": 11},
            "classifications": {"capstone-project-team-19": "collaborative"},
            "project_types_auto": {},
            "project_types_manual": {},
            "project_types_mixed": ["capstone-project-team-19"],
            "project_types_unknown": [],
        },
    )
    blocked = client.post(
        f"/projects/upload/{blocked_upload_id}/run",
        headers=auth_headers,
        json={"scope": "all", "force_rerun": False, "mode": "check"},
    )
    assert blocked.status_code == 200
    blocked_body = blocked.json()["data"]
    assert blocked_body["ready"] is False
    assert blocked_body["errors"] == [
        {"code": "unresolved_project_types", "projects": ["capstone-project-team-19"]}
    ]

    zip_path = tmp_path / "ready.zip"
    zip_path.write_bytes(b"placeholder")

    ready_upload_id = _create_upload(
        seed_conn,
        user_id=1,
        status="needs_file_roles",
        state={
            "zip_path": str(zip_path),
            "dedup_project_keys": {"BuddyCart": 1},
            "dedup_version_keys": {"BuddyCart": 11},
            "classifications": {"BuddyCart": "individual"},
            "project_types_auto": {"BuddyCart": "code"},
            "project_types_mixed": [],
            "project_types_unknown": [],
        },
    )

    monkeypatch.setattr(
        "src.services.uploads_run_service.has_executable_files_for_scope",
        lambda *args, **kwargs: True,
    )
    called = {"execute": 0}

    def _fake_execute(*args, **kwargs):
        called["execute"] += 1

    monkeypatch.setattr(
        "src.services.uploads_run_service.execute_upload_scope_analysis",
        _fake_execute,
    )

    ready = client.post(
        f"/projects/upload/{ready_upload_id}/run",
        headers=auth_headers,
        json={"scope": "individual", "force_rerun": False, "mode": "check"},
    )
    assert ready.status_code == 200
    ready_body = ready.json()["data"]
    assert ready_body["ready"] is True
    assert ready_body["errors"] == []
    assert called["execute"] == 0

    upload = client.get(f"/projects/upload/{ready_upload_id}", headers=auth_headers).json()["data"]
    assert upload["status"] == "needs_file_roles"
