from typing import Any, Dict, Iterable, Optional
import json

from src.db import get_project_summary_by_name, update_project_summary_json
from src.db.resumes import list_resumes, get_resume_snapshot, update_resume_snapshot
from src.menu.resume.helpers import apply_resume_only_updates, resume_only_override_fields, render_snapshot


def update_project_manual_overrides(
    conn,
    user_id: int,
    project_name: str,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Update manual overrides in project_summaries table."""
    summary_row = get_project_summary_by_name(conn, user_id, project_name)
    if not summary_row:
        return None

    try:
        summary_dict = json.loads(summary_row["summary_json"])
    except Exception:
        return None

    overrides = summary_dict.get("manual_overrides") or {}
    if not isinstance(overrides, dict):
        overrides = {}

    for key, value in updates.items():
        if value:
            overrides[key] = value
        else:
            overrides.pop(key, None)

    if overrides:
        summary_dict["manual_overrides"] = overrides
    else:
        summary_dict.pop("manual_overrides", None)

    updated = update_project_summary_json(conn, user_id, project_name, json.dumps(summary_dict))
    if not updated:
        return None
    return overrides


def apply_manual_overrides_to_resumes(
    conn,
    user_id: int,
    project_name: str,
    overrides: Dict[str, Any],
    fields: Iterable[str],
    force_resume_id: Optional[int] = None,
    log_summary: bool = False,
) -> None:
    """Apply global overrides to all saved resumes containing this project."""
    resumes = list_resumes(conn, user_id)
    updated = 0
    skipped_fields = 0

    field_set = set(fields)

    for r in resumes:
        record = get_resume_snapshot(conn, user_id, r["id"])
        if not record:
            continue
        try:
            snapshot = json.loads(record["resume_json"])
        except Exception:
            continue

        projects = snapshot.get("projects") or []
        changed = False

        for entry in projects:
            if entry.get("project_name") != project_name:
                continue

            resume_only_fields = resume_only_override_fields(entry)
            force_update = force_resume_id == r["id"]

            # If this is the selected resume, clear resume-only overrides so global applies.
            if force_update and resume_only_fields:
                clear_updates = {field: None for field in field_set}
                apply_resume_only_updates(entry, clear_updates)
                resume_only_fields = resume_only_override_fields(entry)

            if "display_name" in field_set:
                if "display_name" in resume_only_fields and not force_update:
                    skipped_fields += 1
                else:
                    if overrides.get("display_name"):
                        entry["manual_display_name"] = overrides["display_name"]
                    else:
                        entry.pop("manual_display_name", None)
                    changed = True

            if "summary_text" in field_set:
                if "summary_text" in resume_only_fields and not force_update:
                    skipped_fields += 1
                else:
                    if overrides.get("summary_text"):
                        entry["manual_summary_text"] = overrides["summary_text"]
                    else:
                        entry.pop("manual_summary_text", None)
                    changed = True

            if "contribution_bullets" in field_set:
                if "contribution_bullets" in resume_only_fields and not force_update:
                    skipped_fields += 1
                else:
                    if overrides.get("contribution_bullets"):
                        entry["manual_contribution_bullets"] = overrides["contribution_bullets"]
                    else:
                        entry.pop("manual_contribution_bullets", None)
                    changed = True

            if "key_role" in field_set:
                if "key_role" in resume_only_fields and not force_update:
                    skipped_fields += 1
                else:
                    if overrides.get("key_role"):
                        entry["manual_key_role"] = overrides["key_role"]
                    else:
                        entry.pop("manual_key_role", None)
                    changed = True

        if changed:
            rendered = render_snapshot(conn, user_id, snapshot, print_output=False)
            updated_json = json.dumps(snapshot, default=str)
            update_resume_snapshot(conn, user_id, r["id"], updated_json, rendered)
            updated += 1

    if log_summary and (updated or skipped_fields):
        print(
            f"[Resume] Updated {updated} resume(s); "
            f"skipped {skipped_fields} field update(s) due to resume-only overrides."
        )
