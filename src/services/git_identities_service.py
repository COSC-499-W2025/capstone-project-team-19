from __future__ import annotations

import os
from typing import List, Tuple
from sqlite3 import Connection
from fastapi import HTTPException

from src.api.schemas.git_identities import GitIdentityOptionDTO
from src.analysis.code_collaborative.code_collaborative_analysis_helper import collect_repo_authors
from src.db import (
    ensure_user_github_table,
    load_user_github,
    save_user_github,
    get_project_for_upload_by_key,
)
from src.services.uploads_run_state_service import merge_project_run_inputs
from src.utils.helpers import is_git_repo
from src.utils.parsing import ZIP_DATA_DIR


def _resolve_api_repo_dir(
    *,
    zip_path: str,
    upload_zip_name: str,
    layout_root_name: str | None,
    project: str,
    classification: str | None,
) -> str | None:
    upload_stem = os.path.splitext(os.path.basename(zip_path))[0]
    inner_root = os.path.splitext(upload_zip_name)[0] or layout_root_name
    if not inner_root:
        return None

    base_root = os.path.join(ZIP_DATA_DIR, upload_stem, inner_root)
    classification_norm = (classification or "").lower()

    if classification_norm == "individual":
        candidate_roots = [
            os.path.join(base_root, "individual", project),
            os.path.join(base_root, project),
        ]
    elif classification_norm == "collaborative":
        candidate_roots = [
            os.path.join(base_root, "collaborative", project),
            os.path.join(base_root, project),
        ]
    else:
        candidate_roots = [
            os.path.join(base_root, "individual", project),
            os.path.join(base_root, "collaborative", project),
            os.path.join(base_root, project),
        ]

    for cand in candidate_roots:
        if os.path.isdir(cand) and is_git_repo(cand):
            return cand
    return None


def _build_options_from_authors(
    authors: List[Tuple[str, str, int]],
    allow_collaborators: bool,
) -> List[GitIdentityOptionDTO]:
    if not allow_collaborators:
        return []

    if not authors:
        return []

    return [
        GitIdentityOptionDTO(index=i, name=an or None, email=ae or None, commit_count=c)
        for i, (an, ae, c) in enumerate(authors, start=1)
    ]


def get_git_identities(
    conn: Connection,
    user_id: int,
    upload: dict,
    project_key: int,
) -> Tuple[List[GitIdentityOptionDTO], List[int]]:
    upload_id = upload.get("upload_id")
    if not upload_id:
        raise HTTPException(status_code=400, detail="Upload missing upload_id")

    zip_path = upload.get("zip_path")
    if not zip_path:
        raise HTTPException(status_code=400, detail="Upload missing zip_path")

    zip_name = upload.get("zip_name") or ""
    if not zip_name:
        raise HTTPException(status_code=400, detail="Upload missing zip_name")

    row = get_project_for_upload_by_key(conn, user_id, project_key, upload_id)
    if not row:
        raise HTTPException(status_code=404, detail="Project not found in this upload")

    project_name = row["project_name"]
    classification = row["classification"]
    project_type = row["project_type"]
    if project_type != "code":
        raise HTTPException(status_code=409, detail="Project is not a code project")

    state = upload.get("state") or {}
    layout_root_name = (state.get("layout") or {}).get("root_name")
    repo_dir = _resolve_api_repo_dir(
        zip_path=zip_path,
        upload_zip_name=zip_name,
        layout_root_name=layout_root_name,
        project=project_name,
        classification=classification,
    )
    if not repo_dir:
        merge_project_run_inputs(
            conn,
            upload_id,
            project_name,
            {
                "capabilities": {
                    "git": {
                        "repo_detected": False,
                        "commit_count_hint": 0,
                        "author_count_hint": 0,
                        "multi_author_hint": False,
                    }
                }
            },
        )
        raise HTTPException(status_code=404, detail="No local Git repo found for this project")

    allow_collaborators = classification == "collaborative"
    authors = collect_repo_authors(repo_dir) or []
    options = _build_options_from_authors(authors, allow_collaborators)
    commit_count_hint = int(sum((a[2] or 0) for a in authors))
    author_count_hint = len(authors)
    multi_author_hint = author_count_hint > 1

    ensure_user_github_table(conn)
    aliases = load_user_github(conn, user_id)

    selected_indices: list[int] = []
    for opt in options:
        if opt.email and opt.email.lower() in aliases["emails"]:
            selected_indices.append(opt.index)
        elif opt.name and opt.name.strip().lower() in aliases["names"]:
            selected_indices.append(opt.index)

    merge_project_run_inputs(
        conn,
        upload_id,
        project_name,
        {
            "capabilities": {
                "git": {
                    "repo_detected": True,
                    "commit_count_hint": commit_count_hint,
                    "author_count_hint": author_count_hint,
                    "multi_author_hint": multi_author_hint,
                    "selected_identity_indices": sorted(selected_indices),
                }
            }
        },
    )

    return options, selected_indices


def save_git_identities(
    conn: Connection,
    user_id: int,
    upload: dict,
    project_key: int,
    selected_indices: List[int],
    extra_emails: List[str],
) -> Tuple[List[GitIdentityOptionDTO], List[int]]:
    upload_id = upload.get("upload_id")
    if not upload_id:
        raise HTTPException(status_code=400, detail="Upload missing upload_id")

    zip_path = upload.get("zip_path")
    if not zip_path:
        raise HTTPException(status_code=400, detail="Upload missing zip_path")

    zip_name = upload.get("zip_name") or ""
    if not zip_name:
        raise HTTPException(status_code=400, detail="Upload missing zip_name")

    row = get_project_for_upload_by_key(conn, user_id, project_key, upload_id)
    if not row:
        raise HTTPException(status_code=404, detail="Project not found in this upload")

    project_name = row["project_name"]
    classification = row["classification"]
    project_type = row["project_type"]
    if project_type != "code":
        raise HTTPException(status_code=409, detail="Project is not a code project")
    if classification != "collaborative":
        raise HTTPException(
            status_code=409,
            detail="Git identity selection is only for collaborative projects",
        )

    state = upload.get("state") or {}
    layout_root_name = (state.get("layout") or {}).get("root_name")
    repo_dir = _resolve_api_repo_dir(
        zip_path=zip_path,
        upload_zip_name=zip_name,
        layout_root_name=layout_root_name,
        project=project_name,
        classification=classification,
    )
    if not repo_dir:
        merge_project_run_inputs(
            conn,
            upload_id,
            project_name,
            {
                "capabilities": {
                    "git": {
                        "repo_detected": False,
                        "commit_count_hint": 0,
                        "author_count_hint": 0,
                        "multi_author_hint": False,
                    }
                }
            },
        )
        raise HTTPException(status_code=404, detail="No local Git repo found for this project")

    authors = collect_repo_authors(repo_dir) or []
    options = _build_options_from_authors(authors, allow_collaborators=True)
    commit_count_hint = int(sum((a[2] or 0) for a in authors))
    author_count_hint = len(authors)
    multi_author_hint = author_count_hint > 1
    if not options:
        merge_project_run_inputs(
            conn,
            upload_id,
            project_name,
            {
                "capabilities": {
                    "git": {
                        "repo_detected": True,
                        "commit_count_hint": commit_count_hint,
                        "author_count_hint": author_count_hint,
                        "multi_author_hint": multi_author_hint,
                        "selected_identity_indices": [],
                    }
                }
            },
        )
        raise HTTPException(status_code=404, detail="No git identities found for this project")

    max_idx = len(options)
    bad = [i for i in selected_indices if i < 1 or i > max_idx]
    if bad:
        raise HTTPException(
            status_code=422,
            detail={"invalid_indices": bad, "valid_range": [1, max_idx]},
        )

    emails: list[str] = []
    names: list[str] = []
    for opt in options:
        if opt.index in selected_indices:
            if opt.email:
                emails.append(opt.email)
            if opt.name:
                names.append(opt.name)

    if extra_emails:
        emails.extend(extra_emails)

    ensure_user_github_table(conn)
    save_user_github(conn, user_id, emails, names)

    aliases = load_user_github(conn, user_id)
    selected_indices_out: list[int] = []
    for opt in options:
        if opt.email and opt.email.lower() in aliases["emails"]:
            selected_indices_out.append(opt.index)
        elif opt.name and opt.name.strip().lower() in aliases["names"]:
            selected_indices_out.append(opt.index)

    merge_project_run_inputs(
        conn,
        upload_id,
        project_name,
        {
            "capabilities": {
                "git": {
                    "repo_detected": True,
                    "commit_count_hint": commit_count_hint,
                    "author_count_hint": author_count_hint,
                    "multi_author_hint": multi_author_hint,
                    "selected_identity_indices": sorted(selected_indices_out),
                }
            }
        },
    )

    return options, selected_indices_out
