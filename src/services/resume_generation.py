from typing import Iterable, List, Optional, Tuple
import json

from src.db import get_all_user_project_summaries
from src.db.project_summaries import get_project_summary_by_id
from src.db.resumes import insert_resume_snapshot
from src.menu.resume.helpers import (
    build_resume_snapshot,
    enrich_snapshot_with_contributions,
    load_project_summaries,
    render_snapshot,
)
from src.models.project_summary import ProjectSummary


def load_project_summaries_by_ids(
    conn,
    user_id: int,
    project_ids: Iterable[int],
) -> List[ProjectSummary]:
    summaries: List[ProjectSummary] = []

    for project_id in project_ids:
        row = get_project_summary_by_id(conn, user_id, project_id)
        if not row or not row.get("summary_json"):
            continue
        try:
            summary_dict = json.loads(row["summary_json"])
            summaries.append(ProjectSummary.from_dict(summary_dict))
        except Exception:
            continue

    return summaries


def load_all_project_summaries(conn, user_id: int) -> List[ProjectSummary]:
    return load_project_summaries(conn, user_id, get_all_user_project_summaries)


def select_ranked_summaries(
    summaries: List[ProjectSummary],
    ranked: List[tuple[str, float]],
    selected_indices: Optional[Iterable[int]] = None,
    max_projects: int = 5,
) -> Tuple[List[ProjectSummary], List[str]]:
    ranked_names = [name for name, _score in ranked]
    ranked_dict = {name: score for name, score in ranked}

    selected_names: List[str] = []
    if selected_indices:
        valid = [idx for idx in set(selected_indices) if 1 <= idx <= len(ranked_names)]
        for idx in sorted(valid)[:max_projects]:
            selected_names.append(ranked_names[idx - 1])
    if not selected_names:
        selected_names = ranked_names[:max_projects]

    selected_summaries = [s for s in summaries if s.project_name in selected_names]
    selected_summaries.sort(key=lambda s: ranked_dict.get(s.project_name, 0.0), reverse=True)
    return selected_summaries, selected_names


def build_resume_snapshot_data(
    conn,
    user_id: int,
    summaries: List[ProjectSummary],
    print_output: bool = False,
) -> Optional[Tuple[dict, str]]:
    if not summaries:
        return None

    snapshot = build_resume_snapshot(summaries)
    snapshot = enrich_snapshot_with_contributions(conn, user_id, snapshot)
    rendered = render_snapshot(conn, user_id, snapshot, print_output=print_output)
    return snapshot, rendered


def insert_resume_snapshot_record(
    conn,
    user_id: int,
    name: str,
    snapshot: dict,
    rendered: str,
) -> int:
    resume_json = json.dumps(snapshot, default=str)
    return insert_resume_snapshot(conn, user_id, name, resume_json, rendered)
