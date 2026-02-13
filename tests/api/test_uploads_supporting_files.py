import pytest

from .test_uploads_wizard import _make_zip_bytes
from .test_uploads_file_roles import _advance_to_needs_file_roles, _cleanup_upload_artifacts

PROJECT = "ProjectA"


def build_zip_for_supporting_files(project: str = PROJECT) -> bytes:
    return _make_zip_bytes(
        {
            f"{project}/main_report.txt": "Main report content.\nIntro...\n",
            f"{project}/reading_notes.txt": "Notes...\n",
            f"{project}/outline.txt": "Outline...\n",
            f"{project}/data1.csv": "a,b\n1,2\n",
            f"{project}/data2.csv": "x,y\n3,4\n",
        }
    )


def get_upload_state(client, auth_headers, upload_id: int) -> dict:
    res = client.get(f"/projects/upload/{upload_id}", headers=auth_headers)
    assert res.status_code == 200
    return res.json()["data"].get("state") or {}


def get_project_key_from_state(state: dict, project_name: str) -> int:
    pk = (state.get("dedup_project_keys") or {}).get(project_name)
    assert pk is not None, f"project_key not found for {project_name} in state"
    return int(pk)


def get_project_key_for_upload(client, auth_headers, upload_id: int, project_name: str) -> int:
    state = get_upload_state(client, auth_headers, upload_id)
    return get_project_key_from_state(state, project_name)


def get_files_payload(client, auth_headers, upload_id: int, project: str) -> dict:
    res = client.get(f"/projects/upload/{upload_id}", headers=auth_headers)
    assert res.status_code == 200
    state = res.json()["data"].get("state") or {}
    project_key = get_project_key_from_state(state, project)
    res = client.get(
        f"/projects/upload/{upload_id}/projects/{project_key}/files",
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


def get_project_contrib(state: dict, project: str) -> dict:
    return ((state.get("contributions") or {}).get(project)) or {}


def post_set_main_file(client, auth_headers, upload_id: int, project: str, main_relpath: str) -> dict:
    res = client.get(f"/projects/upload/{upload_id}", headers=auth_headers)
    assert res.status_code == 200
    state = res.json()["data"].get("state") or {}
    project_key = get_project_key_from_state(state, project)
    res = client.post(
        f"/projects/upload/{upload_id}/projects/{project_key}/main-file",
        headers=auth_headers,
        json={"relpath": main_relpath},
    )
    assert res.status_code == 200
    return res.json()["data"].get("state") or {}


def setup_upload_and_set_main(client, auth_headers, zip_bytes: bytes, project: str = PROJECT):
    """
    Shared setup so supporting-file endpoints are actually reachable (avoids 409).
    Returns: (upload_id, files_payload, main_relpath)
    """
    upload = _advance_to_needs_file_roles(client, auth_headers, zip_bytes)
    upload_id = upload["upload_id"]

    files_payload = get_files_payload(client, auth_headers, upload_id, project)
    main_relpath = pick_relpath_by_filename(files_payload["all_files"], "main_report.txt")

    post_set_main_file(client, auth_headers, upload_id, project, main_relpath)
    return upload_id, files_payload, main_relpath


def supporting_text_candidates(files_payload: dict, main_relpath: str) -> list[str]:
    out: list[str] = []
    for f in (files_payload.get("text_files") or []):
        rp = f.get("relpath")
        ext = (f.get("extension") or "").lower()
        if not isinstance(rp, str) or not rp:
            continue
        if rp == main_relpath:
            continue
        if ext == ".csv" or (f.get("file_name") or "").lower().endswith(".csv"):
            continue
        out.append(rp)
    return out


def supporting_csv_candidates(files_payload: dict) -> list[str]:
    out: list[str] = []
    for f in (files_payload.get("csv_files") or []):
        rp = f.get("relpath")
        if isinstance(rp, str) and rp:
            out.append(rp)
    return out


def test_post_supporting_text_files_happy_path_persists_and_dedupes(client, auth_headers):
    upload_id, files_payload, main_relpath = setup_upload_and_set_main(
        client, auth_headers, build_zip_for_supporting_files(PROJECT), PROJECT
    )

    candidates = supporting_text_candidates(files_payload, main_relpath)
    assert len(candidates) >= 2

    selected = [candidates[0], candidates[1], candidates[0]]  # duplicates on purpose

    project_key = get_project_key_for_upload(client, auth_headers, upload_id, PROJECT)
    res = client.post(
        f"/projects/upload/{upload_id}/projects/{project_key}/supporting-text-files",
        headers=auth_headers,
        json={"relpaths": selected},
    )
    assert res.status_code == 200
    state = res.json()["data"].get("state") or {}
    contrib = get_project_contrib(state, PROJECT)

    stored = contrib.get("supporting_text_relpaths") or []
    assert sorted(stored) == sorted(set(selected))
    assert main_relpath not in stored

    persisted_state = get_upload_state(client, auth_headers, upload_id)
    persisted_contrib = get_project_contrib(persisted_state, PROJECT)
    assert sorted(persisted_contrib.get("supporting_text_relpaths") or []) == sorted(set(selected))

    _cleanup_upload_artifacts(persisted_state)


def test_post_supporting_text_files_rejects_main_file(client, auth_headers):
    upload_id, files_payload, main_relpath = setup_upload_and_set_main(
        client, auth_headers, build_zip_for_supporting_files(PROJECT), PROJECT
    )

    candidates = supporting_text_candidates(files_payload, main_relpath)
    assert candidates

    project_key = get_project_key_for_upload(client, auth_headers, upload_id, PROJECT)
    res = client.post(
        f"/projects/upload/{upload_id}/projects/{project_key}/supporting-text-files",
        headers=auth_headers,
        json={"relpaths": [candidates[0], main_relpath]},
    )
    assert res.status_code == 422

    persisted_state = get_upload_state(client, auth_headers, upload_id)
    contrib = get_project_contrib(persisted_state, PROJECT)
    assert "supporting_text_relpaths" not in contrib

    _cleanup_upload_artifacts(persisted_state)


def test_post_supporting_text_files_invalid_relpath_is_atomic(client, auth_headers):
    upload_id, files_payload, main_relpath = setup_upload_and_set_main(
        client, auth_headers, build_zip_for_supporting_files(PROJECT), PROJECT
    )

    candidates = supporting_text_candidates(files_payload, main_relpath)
    assert candidates

    valid_one = candidates[0]
    invalid_one = valid_one + "__does_not_exist"

    project_key = get_project_key_for_upload(client, auth_headers, upload_id, PROJECT)
    res = client.post(
        f"/projects/upload/{upload_id}/projects/{project_key}/supporting-text-files",
        headers=auth_headers,
        json={"relpaths": [valid_one, invalid_one]},
    )
    assert res.status_code in (404, 422)

    persisted_state = get_upload_state(client, auth_headers, upload_id)
    contrib = get_project_contrib(persisted_state, PROJECT)
    assert "supporting_text_relpaths" not in contrib

    _cleanup_upload_artifacts(persisted_state)


def test_post_supporting_text_files_rejects_unsafe_relpath(client, auth_headers):
    # set main file first so we reach safe_relpath validation (422)
    upload_id, _, _ = setup_upload_and_set_main(
        client, auth_headers, build_zip_for_supporting_files(PROJECT), PROJECT
    )

    project_key = get_project_key_for_upload(client, auth_headers, upload_id, PROJECT)
    res = client.post(
        f"/projects/upload/{upload_id}/projects/{project_key}/supporting-text-files",
        headers=auth_headers,
        json={"relpaths": ["../evil.txt"]},
    )
    assert res.status_code == 422

    persisted_state = get_upload_state(client, auth_headers, upload_id)
    _cleanup_upload_artifacts(persisted_state)


def test_post_supporting_csv_files_happy_path_persists_and_dedupes(client, auth_headers):
    upload_id, files_payload, _ = setup_upload_and_set_main(
        client, auth_headers, build_zip_for_supporting_files(PROJECT), PROJECT
    )

    csvs = supporting_csv_candidates(files_payload)
    assert len(csvs) >= 2

    selected = [csvs[0], csvs[1], csvs[0]]

    project_key = get_project_key_for_upload(client, auth_headers, upload_id, PROJECT)
    res = client.post(
        f"/projects/upload/{upload_id}/projects/{project_key}/supporting-csv-files",
        headers=auth_headers,
        json={"relpaths": selected},
    )
    assert res.status_code == 200

    state = res.json()["data"].get("state") or {}
    contrib = get_project_contrib(state, PROJECT)
    stored = contrib.get("supporting_csv_relpaths") or []
    assert sorted(stored) == sorted(set(selected))

    persisted_state = get_upload_state(client, auth_headers, upload_id)
    persisted_contrib = get_project_contrib(persisted_state, PROJECT)
    assert sorted(persisted_contrib.get("supporting_csv_relpaths") or []) == sorted(set(selected))

    _cleanup_upload_artifacts(persisted_state)


def test_post_supporting_csv_files_rejects_non_csv(client, auth_headers):
    upload_id, files_payload, _ = setup_upload_and_set_main(
        client, auth_headers, build_zip_for_supporting_files(PROJECT), PROJECT
    )

    non_csv_text = pick_relpath_by_filename(files_payload["all_files"], "reading_notes.txt")

    project_key = get_project_key_for_upload(client, auth_headers, upload_id, PROJECT)
    res = client.post(
        f"/projects/upload/{upload_id}/projects/{project_key}/supporting-csv-files",
        headers=auth_headers,
        json={"relpaths": [non_csv_text]},
    )
    assert res.status_code == 422

    persisted_state = get_upload_state(client, auth_headers, upload_id)
    contrib = get_project_contrib(persisted_state, PROJECT)
    assert "supporting_csv_relpaths" not in contrib

    _cleanup_upload_artifacts(persisted_state)


def test_supporting_files_requires_needs_file_roles(client, auth_headers):
    zip_bytes = _make_zip_bytes(
        {
            "ProjectA/main_report.txt": "hi",
            "ProjectB/main_report.txt": "hi",
        }
    )
    start = client.post(
        "/projects/upload",
        headers=auth_headers,
        files={"file": ("two_projects.zip", zip_bytes, "application/zip")},
    )
    assert start.status_code == 200
    upload = start.json()["data"]
    upload_id = upload["upload_id"]
    state = upload.get("state") or {}
    project_key = get_project_key_from_state(state, "ProjectA")

    res = client.post(
        f"/projects/upload/{upload_id}/projects/{project_key}/supporting-text-files",
        headers=auth_headers,
        json={"relpaths": ["ProjectA/reading_notes.txt"]},
    )
    assert res.status_code == 409

    _cleanup_upload_artifacts((upload.get("state") or {}))