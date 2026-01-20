from __future__ import annotations

from fastapi import HTTPException


def require_upload_owned(upload: dict | None, user_id: int) -> dict:
    if not upload or upload.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload


def require_upload_status(upload: dict, allowed_statuses: set[str], action: str) -> None:
    status = upload.get("status")
    if status not in allowed_statuses:
        raise HTTPException(
            status_code=409,
            detail=f"Upload not ready for {action} (status={status})",
        )


def require_non_empty_dict(value: dict | None, field_name: str) -> None:
    if not value:
        raise HTTPException(status_code=422, detail=f"{field_name} cannot be empty")


def require_layout_present(state: dict) -> dict:
    layout = (state or {}).get("layout") or {}
    if not layout:
        raise HTTPException(status_code=409, detail="Upload layout missing; parse step not completed")
    return layout


def validate_classification_values(assignments: dict[str, str]) -> None:
    allowed = {"individual", "collaborative"}
    invalid = {k: v for k, v in assignments.items() if v not in allowed}
    if invalid:
        raise HTTPException(status_code=422, detail={"invalid_assignments": invalid})


def validate_classification_keys_against_layout(layout: dict, assignments: dict[str, str]) -> None:
    known_projects = set(layout.get("pending_projects") or []) | set((layout.get("auto_assignments") or {}).keys())
    if not known_projects:
        raise HTTPException(status_code=409, detail="Upload layout missing; parse step not completed")

    unknown = [p for p in assignments.keys() if p not in known_projects]
    if unknown:
        raise HTTPException(
            status_code=422,
            detail={"unknown_projects": unknown, "known_projects": sorted(known_projects)},
        )


def validate_project_types_payload(mixed: set[str], project_types: dict[str, str]) -> None:
    allowed = {"code", "text"}
    bad_vals = {k: v for k, v in project_types.items() if v not in allowed}
    if bad_vals:
        raise HTTPException(status_code=422, detail={"invalid_project_types": bad_vals})

    extra = set(project_types.keys()) - mixed
    missing = mixed - set(project_types.keys())
    if extra:
        raise HTTPException(status_code=422, detail={"unknown_projects": sorted(extra)})
    if missing:
        raise HTTPException(status_code=422, detail={"missing_projects": sorted(missing)})


def validate_dedup_decisions(asks: dict, decisions: dict[str, str]) -> None:
    allowed = {"skip", "new_project", "new_version"}
    bad = {k: v for k, v in decisions.items() if v not in allowed}
    if bad:
        raise HTTPException(status_code=422, detail={"invalid_decisions": bad})

    ask_keys = set(asks.keys())
    decision_keys = set(decisions.keys())

    extra = sorted(list(decision_keys - ask_keys))
    missing = sorted(list(ask_keys - decision_keys))

    if extra:
        raise HTTPException(status_code=422, detail={"unknown_projects": extra})
    if missing:
        raise HTTPException(status_code=422, detail={"missing_projects": missing})
