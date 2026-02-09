import shutil
from pathlib import Path

import pytest
from src.utils.parsing import ZIP_DATA_DIR

from .test_uploads_wizard import _make_zip_bytes


def _cleanup_upload_artifacts(upload_state: dict) -> None:
    zip_path = (upload_state or {}).get("zip_path")
    if not zip_path:
        return

    try:
        zp = Path(zip_path)
        extract_dir = Path(ZIP_DATA_DIR) / zp.stem
        if extract_dir.exists():
            shutil.rmtree(extract_dir, ignore_errors=True)
        if zp.exists():
            zp.unlink(missing_ok=True)
    except Exception:
        pass


pytestmark = pytest.mark.usefixtures("seed_conn")


def _advance_past_blocks(client, auth_headers, upload: dict) -> dict:
    """
    Best-effort: move upload past needs_dedup / needs_classification / needs_project_types
    so the first upload is fully "registered" in the DB for dedup comparisons.
    """
    upload_id = upload["upload_id"]

    # Resolve dedup (default: new_project for all asks)
    if upload["status"] == "needs_dedup":
        asks = (upload.get("state") or {}).get("dedup_asks") or {}
        decisions = {k: "new_project" for k in asks.keys()}
        res = client.post(
            f"/projects/upload/{upload_id}/dedup/resolve",
            headers=auth_headers,
            json={"decisions": decisions},
        )
        assert res.status_code == 200
        upload = res.json()["data"]

    # Classify all known projects as individual (simple default)
    if upload["status"] == "needs_classification":
        layout = (upload.get("state") or {}).get("layout") or {}
        known = set(layout.get("pending_projects") or []) | set((layout.get("auto_assignments") or {}).keys())
        assignments = {p: "individual" for p in known} or {"ProjectA": "individual"}

        res = client.post(
            f"/projects/upload/{upload_id}/classifications",
            headers=auth_headers,
            json={"assignments": assignments},
        )
        assert res.status_code == 200
        upload = res.json()["data"]

    # Choose types for mixed/unknown if required (default: text)
    if upload["status"] == "needs_project_types":
        state = upload.get("state") or {}
        needs = set(state.get("project_types_mixed") or []) | set(state.get("project_types_unknown") or [])
        project_types = {p: "text" for p in needs} or {"ProjectA": "text"}

        res = client.post(
            f"/projects/upload/{upload_id}/project-types",
            headers=auth_headers,
            json={"project_types": project_types},
        )
        assert res.status_code == 200
        upload = res.json()["data"]

    return upload


def test_upload_loose_match_may_trigger_needs_dedup_and_resolve_endpoint_behaves(client, auth_headers):
    """
    Depending on dedup thresholds, this may either:
      - produce needs_dedup (ask range), OR
      - auto-handle (new_version/new_project), OR
      - skip (if considered exact by hash-only rules)

    We keep the test stable by:
      1) asserting that if needs_dedup happens, resolve clears asks, OR
      2) otherwise asserting asks is empty and resolve endpoint returns 409 for this upload.
    """
    # Seed a baseline project with multiple files
    base_files = {f"ProjectA/file{i}.txt": f"content-{i}" for i in range(1, 9)}  # 8 files
    zip1 = _make_zip_bytes(base_files)
    res1 = client.post(
        "/projects/upload",
        headers=auth_headers,
        files={"file": ("base.zip", zip1, "application/zip")},
    )
    assert res1.status_code == 200
    upload1 = res1.json()["data"]
    state1 = upload1.get("state") or {}

    upload1 = _advance_past_blocks(client, auth_headers, upload1)
    state1 = upload1.get("state") or {}

    # Variant: remove one file (7/8 overlap)
    variant_files = {k: v for k, v in base_files.items() if not k.endswith("file8.txt")}
    zip2 = _make_zip_bytes(variant_files)
    res2 = client.post(
        "/projects/upload",
        headers=auth_headers,
        files={"file": ("variant.zip", zip2, "application/zip")},
    )
    assert res2.status_code == 200
    upload2 = res2.json()["data"]
    state2 = upload2.get("state") or {}
    upload_id = upload2["upload_id"]

    if upload2["status"] == "needs_dedup":
        asks = state2.get("dedup_asks") or {}
        assert "ProjectA" in asks

        resolve_res = client.post(
            f"/projects/upload/{upload_id}/dedup/resolve",
            headers=auth_headers,
            json={"decisions": {"ProjectA": "new_version"}},
        )
        assert resolve_res.status_code == 200
        resolved = resolve_res.json()["data"]

        assert resolved["status"] != "needs_dedup"
        resolved_state = resolved.get("state") or {}
        assert (resolved_state.get("dedup_asks") or {}) == {}
        assert (resolved_state.get("dedup_resolved") or {}).get("ProjectA") == "new_version"

        _cleanup_upload_artifacts(state1)
        _cleanup_upload_artifacts(state2)
        _cleanup_upload_artifacts(resolved_state)
        return

    # Otherwise: ensure asks is empty (dedup didn't require manual resolution)
    assert (state2.get("dedup_asks") or {}) == {}

    # And resolving anyway should be blocked by status
    bad = client.post(
        f"/projects/upload/{upload_id}/dedup/resolve",
        headers=auth_headers,
        json={"decisions": {"ProjectA": "new_version"}},
    )
    assert bad.status_code == 409

    _cleanup_upload_artifacts(state1)
    _cleanup_upload_artifacts(state2)


def test_resolve_dedup_backfills_version_key_for_ask_case(client, auth_headers, seed_conn):
    """
    Deterministic 'ask' reproduction:
    - Upload 1 registers a baseline project/version
    - Upload 2 has identical content but different filenames -> loose fingerprint matches -> 'ask'
    Then resolving as new_version should:
      - rename the project's files to the existing project name
      - backfill files.version_key for this upload's rows
      - update state.dedup_version_keys / state.dedup_project_keys
    """
    # Baseline upload (creates a project + version)
    base_files = {
        "BaseProj/a.txt": "same-A",
        "BaseProj/b.txt": "same-B",
    }
    zip1 = _make_zip_bytes(base_files)
    res1 = client.post(
        "/projects/upload",
        headers=auth_headers,
        files={"file": ("base.zip", zip1, "application/zip")},
    )
    assert res1.status_code == 200
    upload1 = _advance_past_blocks(client, auth_headers, res1.json()["data"])
    _cleanup_upload_artifacts((upload1.get("state") or {}))

    # Variant upload: identical contents, different file paths -> triggers loose-fp 'ask'
    variant_files = {
        "VariantProj/x.txt": "same-A",
        "VariantProj/y.txt": "same-B",
    }
    zip2 = _make_zip_bytes(variant_files)
    res2 = client.post(
        "/projects/upload",
        headers=auth_headers,
        files={"file": ("variant.zip", zip2, "application/zip")},
    )
    assert res2.status_code == 200
    upload2 = res2.json()["data"]
    state2 = upload2.get("state") or {}
    upload_id = upload2["upload_id"]

    assert upload2["status"] == "needs_dedup"
    asks = state2.get("dedup_asks") or {}
    assert "VariantProj" in asks
    assert asks["VariantProj"].get("existing") == "BaseProj"

    # Before resolve: ask-case files are not yet inserted into the versioned-only `files` table.
    versions_before = seed_conn.execute(
        """
        SELECT COUNT(*) AS n
        FROM project_versions pv
        JOIN projects p ON p.project_key = pv.project_key
        WHERE p.user_id = 1 AND p.display_name = 'BaseProj'
        """,
    ).fetchone()
    assert int(versions_before["n"]) == 1

    # Resolve as new_version; this should rename VariantProj -> BaseProj and attach version_key.
    resolved_res = client.post(
        f"/projects/upload/{upload_id}/dedup/resolve",
        headers=auth_headers,
        json={"decisions": {"VariantProj": "new_version"}},
    )
    assert resolved_res.status_code == 200
    resolved = resolved_res.json()["data"]
    resolved_state = resolved.get("state") or {}

    # State should now have keys for BaseProj for this upload
    assert isinstance((resolved_state.get("dedup_project_keys") or {}).get("BaseProj"), int)
    assert isinstance((resolved_state.get("dedup_version_keys") or {}).get("BaseProj"), int)

    # After resolve: BaseProj should have a new version, and the latest version should have files.
    versions_after = seed_conn.execute(
        """
        SELECT COUNT(*) AS n
        FROM project_versions pv
        JOIN projects p ON p.project_key = pv.project_key
        WHERE p.user_id = 1 AND p.display_name = 'BaseProj'
        """,
    ).fetchone()
    assert int(versions_after["n"]) >= 2

    latest_vk = seed_conn.execute(
        """
        SELECT pv.version_key
        FROM project_versions pv
        JOIN projects p ON p.project_key = pv.project_key
        WHERE p.user_id = 1 AND p.display_name = 'BaseProj'
        ORDER BY pv.version_key DESC
        LIMIT 1
        """,
    ).fetchone()
    assert latest_vk is not None
    latest_vk = int(latest_vk[0])

    latest_files = seed_conn.execute(
        "SELECT COUNT(*) AS n FROM files WHERE user_id = 1 AND version_key = ?",
        (latest_vk,),
    ).fetchone()
    assert int(latest_files["n"]) == 2

    _cleanup_upload_artifacts(state2)
    _cleanup_upload_artifacts(resolved_state)
