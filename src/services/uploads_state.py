from __future__ import annotations

from typing import Any


def upload_response(upload_id: int, status: str, zip_name: str | None, state: dict) -> dict:
    return {
        "upload_id": upload_id,
        "status": status,
        "zip_name": zip_name,
        "state": state,
    }


def build_failed_parse_state(zip_name: str, zip_path: str) -> dict:
    return {
        "zip_name": zip_name,
        "zip_path": zip_path,
        "error": "No valid files were processed from ZIP.",
    }


def build_all_skipped_state(
    zip_name: str,
    zip_path: str,
    layout: dict,
    skipped: set[str],
    asks: dict,
    new_versions: dict,
) -> dict:
    return {
        "zip_name": zip_name,
        "zip_path": zip_path,
        "layout": layout,
        "files_info_count": 0,
        "dedup_skipped_projects": sorted(list(skipped)),
        "dedup_asks": asks,
        "dedup_new_versions": new_versions,
        "message": "All projects were skipped by deduplication (duplicates).",
    }


def build_base_state(
    zip_name: str,
    zip_path: str,
    layout: dict,
    files_info_count: int,
    skipped: set[str],
    asks: dict,
    new_versions: dict,
) -> dict:
    return {
        "zip_name": zip_name,
        "zip_path": zip_path,
        "layout": layout,
        "files_info_count": files_info_count,
        "dedup_skipped_projects": sorted(list(skipped)),
        "dedup_asks": asks,
        "dedup_new_versions": new_versions,
    }


def add_type_detection_patch(state: dict, classifications: dict[str, str], type_result: dict[str, Any]) -> dict:
    patch = dict(state)
    patch.update(
        {
            "classifications": classifications,
            "project_types_auto": type_result.get("auto_types") or {},
            "project_types_mixed": type_result.get("mixed_projects") or [],
            "project_types_unknown": type_result.get("unknown_projects") or [],
        }
    )
    return patch


def next_status_from_type_result(type_result: dict[str, Any]) -> str:
    mixed = type_result.get("mixed_projects") or []
    return "needs_project_types" if mixed else "needs_file_roles"
