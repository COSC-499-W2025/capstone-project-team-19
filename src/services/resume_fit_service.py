import json
from copy import deepcopy
from typing import Any, Dict, List, Optional

from src.db.user_education import list_user_education_entries
from src.db.user_experience import list_user_experience_entries
from src.db.user_profile import get_user_profile
from src.db.users import get_user_by_id
from src.export.resume_pdf import get_resume_record_pdf_page_count
from src.menu.resume.helpers import recompute_aggregated_skills

PROJECT_TEXT_FIELDS = {"display_name", "summary_text", "contribution_bullets", "key_role"}
SKILL_LIMIT_VARIANTS = (
    {"frameworks": 6, "technical_skills": 8, "writing_skills": 4},
    {"frameworks": 4, "technical_skills": 6, "writing_skills": 3},
)
BULLET_LIMIT_VARIANTS = (4, 3, 2)


def _clean_str(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _clean_bullets(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    cleaned: List[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            cleaned.append(text)
    return cleaned


def _parse_snapshot(record: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return json.loads(record.get("resume_json") or "{}")
    except json.JSONDecodeError:
        return {}


def _get_username(conn, user_id: int) -> str:
    user = get_user_by_id(conn, user_id)
    if not user:
        return "user"
    if hasattr(user, "keys"):
        return str(user["username"])
    return str(user[1])


def _has_manual_value(project: Dict[str, Any], field: str) -> bool:
    if field == "display_name":
        return bool(
            _clean_str(project.get("resume_display_name_override"))
            or _clean_str(project.get("manual_display_name"))
        )
    if field == "summary_text":
        return bool(
            _clean_str(project.get("resume_summary_override"))
            or _clean_str(project.get("manual_summary_text"))
        )
    if field == "contribution_bullets":
        return bool(
            _clean_bullets(project.get("resume_contributions_override"))
            or _clean_bullets(project.get("manual_contribution_bullets"))
        )
    if field == "key_role":
        return bool(
            _clean_str(project.get("resume_key_role_override"))
            or _clean_str(project.get("manual_key_role"))
        )
    return False


def has_manual_project_text_edits(snapshot: Dict[str, Any]) -> bool:
    for project in snapshot.get("projects") or []:
        if any(_has_manual_value(project, field) for field in PROJECT_TEXT_FIELDS):
            return True
    return False


def _fit_status_from_page_count(page_count: int, has_manual_edits: bool) -> Dict[str, Any]:
    fits_one_page = page_count <= 1
    if fits_one_page:
        return {
            "fits_one_page": True,
            "page_count": page_count,
            "overflow_detected": False,
            "overflow_mode": "none",
            "overflow_reason": None,
            "has_manual_project_edits": has_manual_edits,
        }

    overflow_reason = (
        "This resume exceeds one page because of manual project edits. Export is still allowed."
        if has_manual_edits
        else "This resume exceeds one page and must be shortened before exporting."
    )
    return {
        "fits_one_page": False,
        "page_count": page_count,
        "overflow_detected": True,
        "overflow_mode": "warn" if has_manual_edits else "block",
        "overflow_reason": overflow_reason,
        "has_manual_project_edits": has_manual_edits,
    }


def build_resume_fit_status(
    *,
    username: str,
    record: Dict[str, Any],
    user_profile: Optional[Dict[str, Any]] = None,
    education_entries: Optional[List[Dict[str, Any]]] = None,
    experience_entries: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    snapshot = _parse_snapshot(record)
    has_manual_edits = has_manual_project_text_edits(snapshot)
    page_count = get_resume_record_pdf_page_count(
        username=username,
        record=record,
        user_profile=user_profile,
        education_entries=education_entries,
        experience_entries=experience_entries,
    )
    return _fit_status_from_page_count(page_count, has_manual_edits)


def compute_resume_fit_status(conn, user_id: int, record: Dict[str, Any]) -> Dict[str, Any]:
    username = _get_username(conn, user_id)
    user_profile = get_user_profile(conn, user_id)
    education_entries = list_user_education_entries(conn, user_id)
    experience_entries = list_user_experience_entries(conn, user_id)
    return build_resume_fit_status(
        username=username,
        record=record,
        user_profile=user_profile,
        education_entries=education_entries,
        experience_entries=experience_entries,
    )


def _limit_project_bullets(snapshot: Dict[str, Any], max_bullets: int) -> Dict[str, Any]:
    updated = deepcopy(snapshot)
    for project in updated.get("projects") or []:
        bullets = _clean_bullets(project.get("contribution_bullets"))
        if bullets:
            project["contribution_bullets"] = bullets[:max_bullets]
    return updated


def _limit_skill_lists(snapshot: Dict[str, Any], limits: Dict[str, int]) -> Dict[str, Any]:
    updated = deepcopy(snapshot)
    agg = updated.get("aggregated_skills") or {}
    for field, max_items in limits.items():
        values = agg.get(field) or []
        agg[field] = list(values)[:max_items]
    updated["aggregated_skills"] = agg
    return updated


def _limit_project_count(snapshot: Dict[str, Any], max_projects: int) -> Dict[str, Any]:
    updated = deepcopy(snapshot)
    projects = list(updated.get("projects") or [])[:max_projects]
    updated["projects"] = projects
    updated["aggregated_skills"] = recompute_aggregated_skills(projects)
    return updated


def tighten_generated_resume_snapshot(conn,user_id: int,snapshot: Dict[str, Any],) -> Dict[str, Any]:
    username = _get_username(conn, user_id)
    user_profile = get_user_profile(conn, user_id)
    education_entries = list_user_education_entries(conn, user_id)
    experience_entries = list_user_experience_entries(conn, user_id)

    def fits(candidate_snapshot: Dict[str, Any]) -> bool:
        record = {"resume_json": json.dumps(candidate_snapshot, default=str), "rendered_text": ""}
        status = build_resume_fit_status(
            username=username,
            record=record,
            user_profile=user_profile,
            education_entries=education_entries,
            experience_entries=experience_entries,
        )
        return bool(status["fits_one_page"])

    if fits(snapshot):
        return snapshot

    candidates: List[Dict[str, Any]] = []
    for bullet_limit in BULLET_LIMIT_VARIANTS:
        bullet_trimmed = _limit_project_bullets(snapshot, bullet_limit)
        candidates.append(bullet_trimmed)
        for skill_limits in SKILL_LIMIT_VARIANTS:
            candidates.append(_limit_skill_lists(bullet_trimmed, skill_limits))

    projects = snapshot.get("projects") or []
    for max_projects in range(min(len(projects), 4), 1, -1):
        project_limited = _limit_project_count(snapshot, max_projects)
        for bullet_limit in BULLET_LIMIT_VARIANTS:
            bullet_trimmed = _limit_project_bullets(project_limited, bullet_limit)
            candidates.append(bullet_trimmed)
            for skill_limits in SKILL_LIMIT_VARIANTS:
                candidates.append(_limit_skill_lists(bullet_trimmed, skill_limits))

    for candidate in candidates:
        if fits(candidate):
            return candidate

    return snapshot
