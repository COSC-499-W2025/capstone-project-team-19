from __future__ import annotations

from pathlib import Path
import re
from typing import Any


def safe_upload_zip_name(name: str) -> str:
    name = (name or "").strip()
    name = name.split("/")[-1].split("\\")[-1]
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    return name or "upload.zip"


def extract_dir_from_upload_zip(zip_data_dir: str, zip_path: str) -> Path:
    # parse_zip_file extracts under ZIP_DATA_DIR/<zip_stem>
    return Path(zip_data_dir) / Path(zip_path).stem


def rename_project_in_layout(layout: dict, old: str, new: str) -> dict:
    auto_assignments = dict(layout.get("auto_assignments") or {})
    pending = list(layout.get("pending_projects") or [])

    if old in auto_assignments:
        val = auto_assignments.pop(old)
        auto_assignments.setdefault(new, val)

    # only rename in pending if it was actually pending
    if old in pending:
        pending = [p for p in pending if p != old]
        if new not in pending:
            pending.append(new)

    layout["auto_assignments"] = auto_assignments
    layout["pending_projects"] = pending
    return layout


def remove_project_from_layout(layout: dict, name: str) -> dict:
    auto_assignments = dict(layout.get("auto_assignments") or {})
    pending = list(layout.get("pending_projects") or [])

    auto_assignments.pop(name, None)
    pending = [p for p in pending if p != name]

    layout["auto_assignments"] = auto_assignments
    layout["pending_projects"] = pending
    return layout


def apply_project_rename_to_files_info(files_info: list[dict], old: str, new: str) -> None:
    for f in files_info:
        if f.get("project_name") == old:
            f["project_name"] = new


def build_project_filetype_index(files_info: list[dict]) -> dict[str, dict[str, bool]]:
    out: dict[str, dict[str, bool]] = {} # Returns: { project_name: {"has_code": bool, "has_text": bool} }

    for f in files_info:
        project = f.get("project_name")
        if not project:
            continue
        entry = out.setdefault(project, {"has_code": False, "has_text": False})
        ft = (f.get("file_type") or "").lower()
        if ft == "code":
            entry["has_code"] = True
            continue
        if ft == "text":
            entry["has_text"] = True
            continue

    return out


def infer_project_types_from_index(
    projects: set[str] | list[str],
    index: dict[str, dict[str, bool]],
) -> dict[str, Any]:
    auto_types: dict[str, str] = {}
    mixed: list[str] = []
    unknown: list[str] = []

    for project in projects:
        flags = index.get(project) or {}
        has_code = bool(flags.get("has_code"))
        has_text = bool(flags.get("has_text"))

        if has_code and has_text:
            mixed.append(project)
        elif has_code:
            auto_types[project] = "code"
        elif has_text:
            auto_types[project] = "text"
        else:
            unknown.append(project)

    return {
        "auto_types": auto_types,
        "mixed_projects": sorted(mixed),
        "unknown_projects": sorted(unknown),
    }


def rename_project_key_in_index(
    index: dict[str, dict[str, bool]],
    old: str,
    new: str,
) -> dict[str, dict[str, bool]]:
    if old == new:
        return index
    if old not in index:
        return index

    old_flags = index.pop(old)
    new_flags = index.setdefault(new, {"has_code": False, "has_text": False})

    new_flags["has_code"] = bool(new_flags.get("has_code")) or bool(old_flags.get("has_code"))
    new_flags["has_text"] = bool(new_flags.get("has_text")) or bool(old_flags.get("has_text"))

    return index


def remove_project_key_in_index(
    index: dict[str, dict[str, bool]],
    project: str,
) -> dict[str, dict[str, bool]]:
    index.pop(project, None)
    return index


