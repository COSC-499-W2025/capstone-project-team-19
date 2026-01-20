from __future__ import annotations

import re
from pathlib import Path


def safe_upload_zip_name(name: str) -> str:
    name = (name or "").strip()
    name = name.split("/")[-1].split("\\")[-1]
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    return name or "upload.zip"


def extract_dir_from_upload_zip(zip_data_dir: str, zip_path: str) -> Path:
    """
    parse_zip_file extracts under ZIP_DATA_DIR/<zip_stem>.
    """
    return Path(zip_data_dir) / Path(zip_path).stem


def rename_project_in_layout(layout: dict, old: str, new: str) -> dict:
    auto_assignments = dict(layout.get("auto_assignments") or {})
    pending = list(layout.get("pending_projects") or [])

    if old in auto_assignments:
        val = auto_assignments.pop(old)
        auto_assignments.setdefault(new, val)

    was_pending = old in pending
    pending = [p for p in pending if p != old]
    if was_pending and new not in pending:
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
