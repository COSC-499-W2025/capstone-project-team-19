from __future__ import annotations

import sqlite3
from pathlib import Path
from fastapi import HTTPException
from typing import Optional

from src.db.uploads import get_upload_by_id, patch_upload_state
from src.utils.parsing import ZIP_DATA_DIR
from src.services.uploads_file_roles_util import safe_relpath
from src.utils.helpers import extract_text_file, normalize_pdf_paragraphs
from src.analysis.text_collaborative.text_sections import extract_document_sections


_ALLOWED_SECTION_STATUSES = {"needs_file_roles", "needs_summaries", "analyzing", "done"}


def list_main_file_sections(
    conn: sqlite3.Connection,
    user_id: int,
    upload_id: int,
    project_name: str,
    *,
    max_section_chars: int = 2000,
) -> dict:
    upload, state, main_file_relpath, abs_path = _get_main_file_context(
        conn, user_id, upload_id, project_name
    )

    sections_raw, cache_patch = _get_cached_or_compute_sections(
        conn=conn,
        user_id=user_id,
        state=state,
        project_name=project_name,
        abs_path=abs_path,
        relpath=main_file_relpath,
    )

    # Persist cache only if we had to compute.
    if cache_patch:
        patch_upload_state(
            conn,
            upload["upload_id"],
            patch=cache_patch,
            status=upload["status"],
        )

    sections = []
    for i, s in enumerate(sections_raw, start=1):
        title = (s.get("header") or "").strip() or (s.get("preview") or "").strip() or f"Section {i}"
        preview = (s.get("preview") or "").strip()
        content = (s.get("text") or "").strip()

        is_truncated = False
        if max_section_chars and len(content) > max_section_chars:
            content = content[:max_section_chars].rstrip() + "…"
            is_truncated = True

        sections.append(
            {
                "id": i,
                "title": title,
                "preview": preview,
                "content": content,
                "is_truncated": is_truncated,
            }
        )

    project_key = (state.get("dedup_project_keys") or {}).get(project_name)
    version_key = (state.get("dedup_version_keys") or {}).get(project_name)
    return {"project_key": project_key, "version_key": version_key, "project_name": project_name, "main_file": main_file_relpath, "sections": sections}


def set_main_file_contributed_sections(
    conn: sqlite3.Connection,
    user_id: int,
    upload_id: int,
    project_name: str,
    selected_section_ids: list[int],
) -> dict:
    upload, state, main_file_relpath, abs_path = _get_main_file_context(
        conn, user_id, upload_id, project_name
    )

    sections_raw, cache_patch = _get_cached_or_compute_sections(
        conn=conn,
        user_id=user_id,
        state=state,
        project_name=project_name,
        abs_path=abs_path,
        relpath=main_file_relpath,
    )
    n_sections = len(sections_raw)

    selected_section_ids = selected_section_ids or []
    invalid = sorted({i for i in selected_section_ids if not isinstance(i, int) or i < 1 or i > n_sections})
    if invalid:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "selected_section_ids contains invalid ids",
                "invalid_ids": invalid,
                "valid_range": [1, n_sections],
            },
        )

    deduped_sorted = sorted(set(selected_section_ids))

    contributions = dict(state.get("contributions") or {})
    proj = dict(contributions.get(project_name) or {})
    proj["main_file"] = main_file_relpath
    proj["main_section_ids"] = deduped_sorted
    contributions[project_name] = proj

    patch: dict = {"contributions": contributions}
    if cache_patch:
        # one DB write: store derived_sections + contributions together
        patch.update(cache_patch)

    new_state = patch_upload_state(
        conn,
        upload["upload_id"],
        patch=patch,
        status=upload["status"],
    )

    return {
        "upload_id": upload["upload_id"],
        "status": upload["status"],
        "zip_name": upload.get("zip_name"),
        "state": new_state,
    }


# -----------------------
# Shared main-file context
# -----------------------
def _get_main_file_context(
    conn: sqlite3.Connection,
    user_id: int,
    upload_id: int,
    project_name: str,
) -> tuple[dict, dict, str, Path]:
    upload = _require_upload(conn, user_id, upload_id)
    _require_status(upload, _ALLOWED_SECTION_STATUSES)

    state = upload.get("state") or {}
    main_file_relpath = _get_main_file_relpath_or_409(state, project_name)

    zip_path = upload.get("zip_path") or state.get("zip_path")
    if not zip_path:
        raise HTTPException(status_code=400, detail="Upload missing zip_path")

    abs_path = _resolve_main_file_abs_path(zip_path, main_file_relpath)
    return upload, state, main_file_relpath, abs_path


# -----------------------
# Cached sections helper
# -----------------------
def _get_cached_or_compute_sections(
    *,
    conn: sqlite3.Connection,
    user_id: int,
    state: dict,
    project_name: str,
    abs_path: Path,
    relpath: str,
) -> tuple[list[dict], Optional[dict]]:
    """
    Returns (sections, patch) where patch is a state patch to persist the cache
    (or None if we reused a valid cache).
    Cache key: state["derived_sections"][project_name] = {"main_file": relpath, "sections": [...]}
    """
    derived_sections = state.get("derived_sections")
    if not isinstance(derived_sections, dict):
        derived_sections = {}

    cache = derived_sections.get(project_name)
    if isinstance(cache, dict):
        cached_main_file = cache.get("main_file")
        cached_sections = cache.get("sections")
        if cached_main_file == relpath and isinstance(cached_sections, list) and cached_sections:
            return cached_sections, None

    sections = _derive_main_file_sections(conn, user_id, abs_path, relpath)

    # build a patch that preserves other projects' cached sections
    derived_sections_new = dict(derived_sections)
    derived_sections_new[project_name] = {
        "main_file": relpath,
        "sections": sections,
    }

    return sections, {"derived_sections": derived_sections_new}


# -----------------------
# Core shared derivation
# -----------------------
def _derive_main_file_sections(
    conn: sqlite3.Connection,
    user_id: int,
    abs_path: Path,
    relpath: str,
) -> list[dict]:
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail={"message": "Main file not found on disk", "relpath": relpath})

    raw = extract_text_file(str(abs_path), conn, user_id) or ""
    if not raw.strip():
        raise HTTPException(
            status_code=422,
            detail={"message": "Main file could not be extracted or is empty", "relpath": relpath},
        )

    # EXACTLY what CLI does before extract_document_sections()
    normalized_paragraphs = normalize_pdf_paragraphs(raw) or []
    normalized_text = "\n\n".join(normalized_paragraphs).strip()

    return extract_document_sections(normalized_text) or []


# -----------------------
# Existing helpers
# -----------------------
def _require_upload(conn: sqlite3.Connection, user_id: int, upload_id: int) -> dict:
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload


def _require_status(upload: dict, allowed: set[str]) -> None:
    status = upload.get("status")
    if status not in allowed:
        raise HTTPException(status_code=409, detail=f"Upload not ready for this action (status={status})")


def _get_main_file_relpath_or_409(state: dict, project_name: str) -> str:
    file_roles = state.get("file_roles") or {}
    proj_roles = file_roles.get(project_name) or {}
    relpath = proj_roles.get("main_file")

    if not relpath:
        raise HTTPException(
            status_code=409,
            detail={"message": "Main file not selected for this project", "project_name": project_name},
        )

    try:
        return safe_relpath(relpath)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


def _resolve_main_file_abs_path(zip_path: str, relpath: str) -> Path:
    base = Path(ZIP_DATA_DIR).resolve()
    extract_dir = (base / Path(zip_path).stem).resolve()

    rel = Path(relpath)

    if rel.parts and rel.parts[0] == Path(zip_path).stem:
        p = (base / rel).resolve()
    else:
        p = (extract_dir / rel).resolve()

    if base not in p.parents and p != base:
        raise HTTPException(status_code=422, detail="Invalid relpath (escapes ZIP_DATA_DIR)")
    return p