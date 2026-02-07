from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from sqlite3 import Connection
from typing import Any, Dict, List, Literal, Optional, Tuple

from src.db import (
    clear_all_project_dates,
    clear_project_dates,
    get_all_manual_dates,
    get_project_dates,
    get_project_summaries_list,
    get_project_summary_by_id,
    get_project_summary_by_name,
    set_project_dates,
    get_code_collaborative_duration,
    get_code_individual_duration,
    get_text_duration,
)

UNSET = object()
ProjectDateSource = Literal["AUTO", "MANUAL"]

@dataclass(frozen=True)
class ProjectDatesItem:
    project_summary_id: int
    project_name: str
    start_date: Optional[str]
    end_date: Optional[str]
    source: ProjectDateSource
    manual_start_date: Optional[str]
    manual_end_date: Optional[str]

def _is_valid_yyyy_mm_dd(date_str: str) -> bool:
    if not isinstance(date_str, str) or len(date_str) != 10:
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_manual_date(date_str: str) -> None:
    """
    Validate a manual date string.

    Raises ValueError with a human-friendly message on invalid input.
    """
    if not isinstance(date_str, str) or date_str.strip() == "":
        raise ValueError(
            "Date cannot be empty. Omit the field to keep the current value, or use null to clear it."
        )

    date_str = date_str.strip()
    if not _is_valid_yyyy_mm_dd(date_str):
        raise ValueError("Invalid date. Use YYYY-MM-DD with valid month (1-12) and day.")

    entered_date = datetime.strptime(date_str, "%Y-%m-%d")
    if entered_date > datetime.now():
        raise ValueError("Date cannot be in the future.")

def validate_manual_date_range(start_date: Optional[str], end_date: Optional[str]) -> None:
    if start_date is not None:
        validate_manual_date(start_date)
    if end_date is not None:
        validate_manual_date(end_date)

    if start_date and end_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        if start_dt > end_dt:
            raise ValueError("Start date cannot be after end date.")

def _best_project_duration(conn: Connection, user_id: int, project_name: str, project_type: Optional[str], project_mode: Optional[str]) -> Optional[Tuple[Optional[str], Optional[str]]]:
    """
    Return best-effort (start_date, end_date) for this project.

    NOTE: These DB helpers already coalesce manual overrides when present.
    We only call this when there are NO manual overrides, so the result represents automatic dates.
    """
    if project_type == "code":
        if project_mode == "collaborative":
            return get_code_collaborative_duration(conn, user_id, project_name)
        # default to individual when mode missing/unknown
        return get_code_individual_duration(conn, user_id, project_name)

    # default to text when type missing/unknown
    return get_text_duration(conn, user_id, project_name)

def compute_project_dates(conn: Connection, user_id: int, project_summary_id: int, project_name: str, project_type: Optional[str], project_mode: Optional[str]) -> ProjectDatesItem:
    manual = get_project_dates(conn, user_id, project_name)
    manual_start: Optional[str] = None
    manual_end: Optional[str] = None
    if manual is not None:
        manual_start = manual[0]
        manual_end = manual[1]

    has_manual = bool(manual_start or manual_end)
    if has_manual:
        return ProjectDatesItem(
            project_summary_id=project_summary_id,
            project_name=project_name,
            start_date=manual_start,
            end_date=manual_end,
            source="MANUAL",
            manual_start_date=manual_start,
            manual_end_date=manual_end,
        )

    dur = _best_project_duration(conn, user_id, project_name, project_type, project_mode)
    start_date, end_date = (dur if dur is not None else (None, None))
    return ProjectDatesItem(
        project_summary_id=project_summary_id,
        project_name=project_name,
        start_date=start_date,
        end_date=end_date,
        source="AUTO",
        manual_start_date=None,
        manual_end_date=None,
    )

def list_project_dates(conn: Connection, user_id: int) -> List[ProjectDatesItem]:
    """
    List all projects with their effective (manual or automatic) dates.
    """
    projects = get_project_summaries_list(conn, user_id)
    items: List[ProjectDatesItem] = []
    for p in projects:
        items.append(
            compute_project_dates(
                conn=conn,
                user_id=user_id,
                project_summary_id=p["project_summary_id"],
                project_name=p["project_name"],
                project_type=p.get("project_type"),
                project_mode=p.get("project_mode"),
            )
        )
    return items

def set_project_manual_dates(conn: Connection, user_id: int, project_id: int, *, start_date: object = UNSET, end_date: object = UNSET) -> ProjectDatesItem:
    """
    Set manual dates for a project by ID.

    - Omit a field (UNSET) to keep that side unchanged.
    - Provide None to clear that side.
    - Provide a YYYY-MM-DD string to set that side.
    """
    row = get_project_summary_by_id(conn, user_id, project_id)
    if not row: raise KeyError(f"Project not found: {project_id}")

    if start_date is UNSET and end_date is UNSET:
        raise ValueError("At least one of start_date or end_date must be provided.")

    project_name = row["project_name"]
    current = get_project_dates(conn, user_id, project_name)
    current_start = current[0] if current else None
    current_end = current[1] if current else None

    # Normalize string inputs (trim whitespace). Reject empty strings.
    if isinstance(start_date, str):
        start_date = start_date.strip()
        if start_date == "":
            raise ValueError(
                "start_date cannot be an empty string. Omit the field to keep the current value, or use null to clear it."
            )
    if isinstance(end_date, str):
        end_date = end_date.strip()
        if end_date == "":
            raise ValueError(
                "end_date cannot be an empty string. Omit the field to keep the current value, or use null to clear it."
            )

    new_start = current_start if start_date is UNSET else start_date
    new_end = current_end if end_date is UNSET else end_date


    validate_manual_date_range(new_start, new_end)
    set_project_dates(conn, user_id, project_name, new_start, new_end)

    return compute_project_dates(
        conn=conn,
        user_id=user_id,
        project_summary_id=row["project_summary_id"],
        project_name=project_name,
        project_type=row.get("project_type"),
        project_mode=row.get("project_mode"),
    )

def set_project_manual_dates_by_name(conn: Connection, user_id: int, project_name: str, *, start_date: object = UNSET, end_date: object = UNSET) -> ProjectDatesItem:
    row = get_project_summary_by_name(conn, user_id, project_name)
    if not row: raise KeyError(f"Project not found: {project_name}")

    return set_project_manual_dates(
        conn,
        user_id,
        row["project_summary_id"],
        start_date=start_date,
        end_date=end_date,
    )

def clear_project_manual_dates_by_name(conn: Connection, user_id: int, project_name: str) -> ProjectDatesItem:
    row = get_project_summary_by_name(conn, user_id, project_name)
    if not row: raise KeyError(f"Project not found: {project_name}")

    clear_project_dates(conn, user_id, project_name)
    return compute_project_dates(
        conn=conn,
        user_id=user_id,
        project_summary_id=row["project_summary_id"],
        project_name=project_name,
        project_type=row.get("project_type"),
        project_mode=row.get("project_mode"),
    )

def clear_project_manual_dates(conn: Connection, user_id: int, project_id: int) -> ProjectDatesItem:
    row = get_project_summary_by_id(conn, user_id, project_id)
    if not row: raise KeyError(f"Project not found: {project_id}")

    project_name = row["project_name"]
    clear_project_dates(conn, user_id, project_name)

    return compute_project_dates(
        conn=conn,
        user_id=user_id,
        project_summary_id=row["project_summary_id"],
        project_name=project_name,
        project_type=row.get("project_type"),
        project_mode=row.get("project_mode"),
    )

def clear_all_manual_project_dates(conn: Connection, user_id: int) -> int:
    """
    Clear all manual dates for this user.
    Returns the number of projects that had manual overrides before clearing.
    """
    before = get_all_manual_dates(conn, user_id)
    cleared_count = len(before)
    clear_all_project_dates(conn, user_id)
    return cleared_count
