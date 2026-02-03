from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from fastapi import HTTPException

from src.db.uploads import get_upload_by_id, patch_upload_state
from src.utils.parsing import ZIP_DATA_DIR
from src.services.uploads_file_roles_util import safe_relpath
from src.utils.helpers import extract_text_file


_ALLOWED_SECTION_STATUSES = {"needs_file_roles", "needs_summaries", "analyzing", "done"}


def list_main_file_sections(
    conn: sqlite3.Connection,
    user_id: int,
    upload_id: int,
    project_name: str,
    *,
    max_section_chars: int = 2000,
) -> dict:
    """
    Returns numbered sections from the selected main file.
    Stores nothing; purely derived from current upload + main file selection.
    """
    upload = _require_upload(conn, user_id, upload_id)
    _require_status(upload, _ALLOWED_SECTION_STATUSES)

    state = upload.get("state") or {}
    main_file_relpath = _get_main_file_relpath_or_409(state, project_name)

    abs_path = _resolve_main_file_abs_path(main_file_relpath)
    if not abs_path.exists():
        raise HTTPException(
            status_code=404,
            detail={"message": "Main file not found on disk", "relpath": main_file_relpath},
        )

    full_text = extract_text_file(str(abs_path), conn, user_id) or ""
    if not full_text.strip():
        raise HTTPException(
            status_code=422,
            detail={"message": "Main file could not be extracted or is empty", "relpath": main_file_relpath},
        )

    sections_raw = _extract_sections(full_text)

    sections = []
    for i, s in enumerate(sections_raw, start=1):
        title = (s.get("header") or "").strip()
        preview = (s.get("preview") or "").strip()
        content = (s.get("text") or "").strip()

        if not title:
            title = preview or f"Section {i}"

        is_truncated = False
        if max_section_chars is not None and max_section_chars > 0 and len(content) > max_section_chars:
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

    return {
        "project_name": project_name,
        "main_file": main_file_relpath,
        "sections": sections,
    }


def set_main_file_contributed_sections(
    conn: sqlite3.Connection,
    user_id: int,
    upload_id: int,
    project_name: str,
    selected_section_ids: list[int],
) -> dict:
    """
    Validates selection IDs against server-derived sections and persists only the IDs into uploads.state_json.
    """
    upload = _require_upload(conn, user_id, upload_id)
    _require_status(upload, _ALLOWED_SECTION_STATUSES)

    state = upload.get("state") or {}
    main_file_relpath = _get_main_file_relpath_or_409(state, project_name)

    abs_path = _resolve_main_file_abs_path(main_file_relpath)
    if not abs_path.exists():
        raise HTTPException(
            status_code=404,
            detail={"message": "Main file not found on disk", "relpath": main_file_relpath},
        )

    full_text = extract_text_file(str(abs_path), conn, user_id) or ""
    if not full_text.strip():
        raise HTTPException(
            status_code=422,
            detail={"message": "Main file could not be extracted or is empty", "relpath": main_file_relpath},
        )

    sections_raw = _extract_sections(full_text)
    n_sections = len(sections_raw)

    # Allow empty selection (means 0 contribution)
    selected_section_ids = selected_section_ids or []

    # Validate ids
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

    # Persist into state_json under a contributions namespace
    contributions = dict(state.get("contributions") or {})
    proj = dict(contributions.get(project_name) or {})
    proj["main_file"] = main_file_relpath
    proj["main_section_ids"] = deduped_sorted
    contributions[project_name] = proj

    # Patch (safe even if patch is shallow)
    new_state = patch_upload_state(conn, upload_id, patch={"contributions": contributions}, status=upload["status"])

    return {
        "upload_id": upload["upload_id"],
        "status": upload["status"],
        "zip_name": upload.get("zip_name"),
        "state": new_state,
    }


# Helpers
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


def _resolve_main_file_abs_path(relpath: str) -> Path:
    # relpath is ZIP_DATA_DIR-relative (posix style)
    base = Path(ZIP_DATA_DIR).resolve()
    p = (base / Path(relpath)).resolve()
    # hard safety: ensure under ZIP_DATA_DIR
    if base not in p.parents and p != base:
        raise HTTPException(status_code=422, detail="Invalid relpath (escapes ZIP_DATA_DIR)")
    return p


def _extract_sections(full_text: str) -> list[dict]:
    """
    Split into sections by simple header detection, else fallback to paragraph chunks.
    Returns list of {header, preview, text}.
    """

    lines = full_text.split("\n")
    sections: list[dict] = []

    # fairly permissive header line, but avoids tiny 1-2 char lines
    header_re = re.compile(r"^[A-Z][A-Za-z0-9 ,:\-]{2,}$")

    buf: list[str] = []
    current_header: str | None = None

    def flush():
        nonlocal buf, current_header
        text = "\n".join([x for x in buf if x.strip()]).strip()
        buf = []
        if not text:
            return
        preview = text[:60].replace("\n", " ").strip()
        sections.append({"header": current_header, "preview": preview, "text": text})

    for raw in lines:
        s = raw.strip()
        if not s:
            # keep blank lines as soft separators
            buf.append("")
            continue

        if header_re.match(s) and len(s.split()) <= 10:
            # new header
            if buf:
                flush()
            current_header = s
            continue

        buf.append(s)

    if buf:
        flush()

    # If we didn't really detect headers, fallback to paragraph-ish chunks
    if not sections or all(sec.get("header") is None for sec in sections):
        chunks = [c.strip() for c in re.split(r"\n\s*\n+", full_text.strip()) if c.strip()]
        sections = []
        for c in chunks:
            preview_words = " ".join(c.split()[:8]).strip()
            sections.append(
                {
                    "header": None,
                    "preview": (preview_words + "…") if preview_words else c[:60],
                    "text": c,
                }
            )

    return sections