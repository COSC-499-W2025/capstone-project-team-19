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
