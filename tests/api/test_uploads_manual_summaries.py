import pytest

from .test_uploads_wizard import _make_zip_bytes
from .test_uploads_file_roles import _advance_to_needs_file_roles, _cleanup_upload_artifacts

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


def setup_upload_to_needs_summaries_no_csv(client, auth_headers, zip_bytes: bytes, project: str = PROJECT) -> int:
    """
    Advances the wizard to needs_summaries for a project with NO CSV files:
    - upload -> needs_file_roles
    - set main file
    - set supporting text files (should transition status -> needs_summaries)
    Returns upload_id
    """
    upload = _advance_to_needs_file_roles(client, auth_headers, zip_bytes)
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

    # set supporting text files -> should move to needs_summaries (no CSVs exist)
    res_support = client.post(
        f"/projects/upload/{upload_id}/projects/{project}/supporting-text-files",
        headers=auth_headers,
        json={"relpaths": [supporting_relpath]},
    )
    assert res_support.status_code == 200
    assert res_support.json()["data"]["status"] == "needs_summaries"

    return upload_id


def test_post_manual_project_summary_happy_path_persists(client, auth_headers):
    upload_id = setup_upload_to_needs_summaries_no_csv(client, auth_headers, build_zip_no_csv(PROJECT), PROJECT)

    text = "Built X, improved Y."
    res = client.post(
        f"/projects/upload/{upload_id}/projects/{PROJECT}/manual-project-summary",
        headers=auth_headers,
        json={"summary_text": text},
    )
    assert res.status_code == 200

    body = res.json()
    assert body["success"] is True
    state = body["data"].get("state") or {}
    assert (state.get("manual_project_summaries") or {}).get(PROJECT) == text

    persisted_state = get_upload_state(client, auth_headers, upload_id)
    assert (persisted_state.get("manual_project_summaries") or {}).get(PROJECT) == text

    _cleanup_upload_artifacts(persisted_state)


def test_post_manual_contribution_summary_happy_path_persists(client, auth_headers):
    upload_id = setup_upload_to_needs_summaries_no_csv(client, auth_headers, build_zip_no_csv(PROJECT), PROJECT)

    desc = "I owned the API + tests."
    res = client.post(
        f"/projects/upload/{upload_id}/projects/{PROJECT}/manual-contribution-summary",
        headers=auth_headers,
        json={"manual_contribution_summary": desc},
    )
    assert res.status_code == 200

    body = res.json()
    assert body["success"] is True
    state = body["data"].get("state") or {}
    contrib = ((state.get("contributions") or {}).get(PROJECT)) or {}
    assert contrib.get("manual_contribution_summary") == desc

    persisted_state = get_upload_state(client, auth_headers, upload_id)
    persisted_contrib = ((persisted_state.get("contributions") or {}).get(PROJECT)) or {}
    assert persisted_contrib.get("manual_contribution_summary") == desc

    _cleanup_upload_artifacts(persisted_state)