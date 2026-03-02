import pytest

from src.db.projects import get_project_key
from .test_uploads_wizard import _make_zip_bytes
from .test_uploads_file_roles import _cleanup_upload_artifacts

PROJECT = "ProjectA"


def build_zip_no_csv(project: str = PROJECT) -> bytes:
    # No CSVs on purpose -> supporting TEXT selection should be enough to advance to needs_summaries
    return _make_zip_bytes(
        {
            f"{project}/main_report.txt": "Main report content.\nIntro...\n",
            f"{project}/reading_notes.txt": "Notes...\n",
        }
    )


def get_upload_state(client, auth_headers, upload_id: int) -> dict:
    res = client.get(f"/projects/upload/{upload_id}", headers=auth_headers)
    assert res.status_code == 200
    return res.json()["data"].get("state") or {}


def get_files_payload(client, auth_headers, upload_id: int, project: str) -> dict:
    res = client.get(
        f"/projects/upload/{upload_id}/projects/{project}/files",
        headers=auth_headers,
    )
    assert res.status_code == 200
    return res.json()["data"]


def pick_relpath_by_filename(files: list[dict], filename: str) -> str:
    for f in files:
        if (f.get("file_name") or "") == filename:
            rp = f.get("relpath")
            if isinstance(rp, str) and rp:
                return rp
    raise AssertionError(f"Could not find relpath for filename={filename}")


def _advance_to_needs_file_roles_collab_text(client, auth_headers, zip_bytes: bytes) -> dict:
    """
    Same as test_uploads_file_roles._advance_to_needs_file_roles, but:
      - classify as collaborative (so summaries are required)
      - ensure project type is text if project-types step appears
    """
    res = client.post(
        "/projects/upload",
        headers=auth_headers,
        files={"file": ("test.zip", zip_bytes, "application/zip")},
    )
    assert res.status_code == 200
    upload = res.json()["data"]
    upload_id = upload["upload_id"]

    # resolve dedup if needed
    if upload["status"] == "needs_dedup":
        asks = (upload.get("state") or {}).get("dedup_asks") or {}
        decisions = {k: "new_project" for k in asks.keys()}
        res_d = client.post(
            f"/projects/upload/{upload_id}/dedup/resolve",
            headers=auth_headers,
            json={"decisions": decisions},
        )
        assert res_d.status_code == 200
        upload = res_d.json()["data"]

    # classify as collaborative
    if upload["status"] == "needs_classification":
        layout = (upload.get("state") or {}).get("layout") or {}
        known = set(layout.get("pending_projects") or []) | set((layout.get("auto_assignments") or {}).keys())
        assignments = {p: "collaborative" for p in known} or {"ProjectA": "collaborative"}

        res2 = client.post(
            f"/projects/upload/{upload_id}/classifications",
            headers=auth_headers,
            json={"assignments": assignments},
        )
        assert res2.status_code == 200
        upload = res2.json()["data"]

    # if it needs project types, force text
    if upload["status"] == "needs_project_types":
        state = upload.get("state") or {}
        needs = set(state.get("project_types_mixed") or []) | set(state.get("project_types_unknown") or [])
        project_types = {p: "text" for p in needs} or {"ProjectA": "text"}

        res3 = client.post(
            f"/projects/upload/{upload_id}/project-types",
            headers=auth_headers,
            json={"project_types": project_types},
        )
        assert res3.status_code == 200
        upload = res3.json()["data"]

    assert upload["status"] == "needs_file_roles"
    return upload


def setup_upload_to_needs_summaries_no_csv(client, auth_headers, zip_bytes: bytes, project: str = PROJECT) -> int:
    """
    Advances the wizard to needs_summaries for a collaborative text project with NO CSV files:
    - upload -> needs_file_roles (collaborative)
    - set main file
    - set main section ids (empty list to mark step complete)
    - set supporting text files -> should transition status -> needs_summaries
    Returns upload_id
    """
    upload = _advance_to_needs_file_roles_collab_text(client, auth_headers, zip_bytes)
    upload_id = upload["upload_id"]

    files_payload = get_files_payload(client, auth_headers, upload_id, project)

    main_relpath = pick_relpath_by_filename(files_payload["all_files"], "main_report.txt")
    supporting_relpath = pick_relpath_by_filename(files_payload["all_files"], "reading_notes.txt")

    # set main file
    res_main = client.post(
        f"/projects/upload/{upload_id}/projects/{project}/main-file",
        headers=auth_headers,
        json={"relpath": main_relpath},
    )
    assert res_main.status_code == 200

    # mark sections step complete (required for needs_summaries transition for collab text)
    res_sections = client.post(
        f"/projects/upload/{upload_id}/projects/{project}/text/contributions",
        headers=auth_headers,
        json={"selected_section_ids": []},
    )
    assert res_sections.status_code == 200

    # set supporting text files -> should move to needs_summaries (no CSVs exist)
    res_support = client.post(
        f"/projects/upload/{upload_id}/projects/{project}/supporting-text-files",
        headers=auth_headers,
        json={"relpaths": [supporting_relpath]},
    )
    assert res_support.status_code == 200
    assert res_support.json()["data"]["status"] == "needs_summaries"

    return upload_id


def _get_project_key_for_test(seed_conn, user_id: int, project_name: str) -> int:
    pk = get_project_key(seed_conn, user_id, project_name)
    assert isinstance(pk, int)
    return pk


def test_post_manual_project_summary_happy_path_persists(client, auth_headers, seed_conn):
    upload_id = setup_upload_to_needs_summaries_no_csv(client, auth_headers, build_zip_no_csv(PROJECT), PROJECT)

    project_key = _get_project_key_for_test(seed_conn, 1, PROJECT)
    pk_str = str(project_key)

    text = "Built X, improved Y."
    res = client.post(
        f"/projects/upload/{upload_id}/projects/{project_key}/manual-project-summary",
        headers=auth_headers,
        json={"summary_text": text},
    )
    assert res.status_code == 200

    body = res.json()
    assert body["success"] is True
    state = body["data"].get("state") or {}
    assert (state.get("manual_project_summaries") or {}).get(pk_str) == text

    persisted_state = get_upload_state(client, auth_headers, upload_id)
    assert (persisted_state.get("manual_project_summaries") or {}).get(pk_str) == text

    _cleanup_upload_artifacts(persisted_state)


def test_post_manual_contribution_summary_happy_path_persists(client, auth_headers, seed_conn):
    upload_id = setup_upload_to_needs_summaries_no_csv(client, auth_headers, build_zip_no_csv(PROJECT), PROJECT)

    project_key = _get_project_key_for_test(seed_conn, 1, PROJECT)
    pk_str = str(project_key)

    desc = "I owned the API + tests."
    res = client.post(
        f"/projects/upload/{upload_id}/projects/{project_key}/manual-contribution-summary",
        headers=auth_headers,
        json={"manual_contribution_summary": desc},
    )
    assert res.status_code == 200

    body = res.json()
    assert body["success"] is True
    state = body["data"].get("state") or {}
    contrib = ((state.get("contributions") or {}).get(pk_str)) or {}
    assert contrib.get("manual_contribution_summary") == desc

    persisted_state = get_upload_state(client, auth_headers, upload_id)
    persisted_contrib = ((persisted_state.get("contributions") or {}).get(pk_str)) or {}
    assert persisted_contrib.get("manual_contribution_summary") == desc

    _cleanup_upload_artifacts(persisted_state)