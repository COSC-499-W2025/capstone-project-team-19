from itertools import groupby
from typing import List, Dict, Any, Optional

from src.db.skills import get_skill_events, get_project_skill_pairs
from src.db.project_summaries import get_project_summaries_list
from src.insights.chronological_skills import get_skill_timeline

def get_user_skills(conn, user_id: int) -> List[Dict[str, Any]]:
    rows = get_skill_events(conn, user_id)
    return [
        {
            "skill_name": row[0],
            "level": row[1],
            "score": row[2],
            "project_name": row[3],
            "actual_activity_date": row[4],
            "recorded_at": row[5]
        }
        for row in rows
    ]

def _diminishing_return(current: float, new_score: float) -> float:
    """Apply diminishing returns: 1 - (1 - current) * (1 - new_score)"""
    return 1.0 - (1.0 - current) * (1.0 - new_score)

def get_skill_timeline_data(conn, user_id: int) -> Dict[str, Any]:
    dated, undated = get_skill_timeline(conn, user_id)

    # Running state: cumulative score, contributing projects, and skill type per skill
    cumulative: Dict[str, float] = {}
    projects_by_skill: Dict[str, List[str]] = {}
    skill_type_by_skill: Dict[str, str] = {}

    # Group dated events by date and compute cumulative scores
    date_groups = []
    for date_key, events_iter in groupby(dated, key=lambda e: e["date"]):
        events = list(events_iter)

        # Apply each event's score using diminishing returns
        for e in events:
            skill = e["skill_name"]
            cumulative[skill] = _diminishing_return(
                cumulative.get(skill, 0.0), e["score"]
            )
            if skill not in projects_by_skill:
                projects_by_skill[skill] = []
            if e["project_name"] not in projects_by_skill[skill]:
                projects_by_skill[skill].append(e["project_name"])
            if skill not in skill_type_by_skill and "skill_type" in e:
                skill_type_by_skill[skill] = e["skill_type"]

        date_groups.append({
            "date": date_key,
            "events": [
                {
                    "skill_name": e["skill_name"],
                    "level": e["level"],
                    "score": e["score"],
                    "project_name": e["project_name"],
                    "skill_type": e.get("skill_type", "unknown"),
                }
                for e in events
            ],
            "cumulative_skills": {
                skill: {
                    "cumulative_score": round(score, 4),
                    "projects": list(projects_by_skill[skill]),
                }
                for skill, score in cumulative.items()
            },
        })

    undated_events = [
        {
            "skill_name": e["skill_name"],
            "level": e["level"],
            "score": e["score"],
            "project_name": e["project_name"],
            "skill_type": e.get("skill_type", "unknown"),
        }
        for e in undated
    ]

    # Compute current totals: dated cumulative + undated folded in
    current_totals = dict(cumulative)
    current_projects = {s: list(p) for s, p in projects_by_skill.items()}

    for e in undated:
        skill = e["skill_name"]
        current_totals[skill] = _diminishing_return(
            current_totals.get(skill, 0.0), e["score"]
        )
        if skill not in current_projects:
            current_projects[skill] = []
        if e["project_name"] not in current_projects[skill]:
            current_projects[skill].append(e["project_name"])
        if skill not in skill_type_by_skill and "skill_type" in e:
            skill_type_by_skill[skill] = e["skill_type"]

    current_totals_dto = {
        skill: {
            "cumulative_score": round(score, 4),
            "projects": current_projects[skill],
            "skill_type": skill_type_by_skill.get(skill, "unknown"),
        }
        for skill, score in current_totals.items()
    }

    # Compute summary
    all_events = dated + undated
    skill_names = sorted(set(e["skill_name"] for e in all_events))
    project_names = set(e["project_name"] for e in all_events)
    dates = [e["date"] for e in dated]

    summary = {
        "total_skills": len(skill_names),
        "total_projects": len(project_names),
        "date_range": {
            "earliest": dates[0] if dates else None,
            "latest": dates[-1] if dates else None,
        },
        "skill_names": skill_names,
    }

    return {
        "dated": date_groups,
        "undated": undated_events,
        "current_totals": current_totals_dto,
        "summary": summary,
    }


def get_activity_by_date_grid(conn, user_id: int, year: Optional[int] = None) -> Dict[str, Any]:
    """
    Build a GitHub-style contribution grid: rows = days of week (Sun-Sat),
    cols = weeks, chronological order (oldest left, most recent right).

    When year is None: spans from earliest activity through current week.
    When year is set: shows only that calendar year (Jan 1 - Dec 31).
    Returns available_years (years that contain data) for the year selector.
    """
    from src.db.activity_by_date import get_activity_counts_by_date
    from datetime import date, datetime, timedelta

    counts, projects_by_date = get_activity_counts_by_date(conn, user_id)
    if not counts:
        return {
            "title": "Activity by Date",
            "row_labels": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
            "col_labels": [],
            "matrix": [],
            "available_years": [],
            "projects_by_date": {},
        }

    # Derive available years from dates that have data
    all_dates = list(counts.keys())
    available_years = sorted(set(int(d[:4]) for d in all_dates if len(d) >= 4))

    row_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    if year is not None:
        # Filter to single calendar year
        start_sunday = date(year, 1, 1)
        days_back = (start_sunday.weekday() + 1) % 7
        start_sunday = start_sunday - timedelta(days=days_back)

        end_sunday = date(year, 12, 31)
        days_forward = (6 - end_sunday.weekday()) % 7
        if days_forward:
            end_sunday = end_sunday + timedelta(days=days_forward)

        num_weeks = max(1, (end_sunday - start_sunday).days // 7 + 1)
    else:
        # All data: earliest activity through current week
        end = date.today()
        days_since_sun = (end.weekday() + 1) % 7
        end_sunday = end - timedelta(days=days_since_sun)

        min_date_str = min(all_dates)
        start = datetime.strptime(min_date_str[:10], "%Y-%m-%d").date()
        days_back = (start.weekday() + 1) % 7
        start_sunday = start - timedelta(days=days_back)

        total_weeks = max(1, (end_sunday - start_sunday).days // 7 + 1)
        max_weeks = 522
        num_weeks = min(total_weeks, max_weeks)
        if total_weeks > max_weeks:
            start_sunday = end_sunday - timedelta(weeks=max_weeks - 1)

    col_labels = []
    matrix = [[0] * num_weeks for _ in range(7)]

    for w in range(num_weeks):
        week_start = start_sunday + timedelta(weeks=w)
        col_labels.append(week_start.strftime("%Y-%m-%d")[:10])
        for d in range(7):
            day_date = week_start + timedelta(days=d)
            key = day_date.strftime("%Y-%m-%d")
            matrix[d][w] = counts.get(key, 0)

    return {
        "title": "Activity by Date",
        "row_labels": row_labels,
        "col_labels": col_labels,
        "matrix": matrix,
        "available_years": available_years,
        "projects_by_date": projects_by_date,
    }


def get_project_skill_matrix_data(conn, user_id: int) -> Dict[str, Any]:
    """Build a matrix of skills (rows) x projects (columns) for the cross-project heatmap."""
    summaries = get_project_summaries_list(conn, user_id)
    if not summaries:
        return {
            "title": "Skills Across Projects",
            "row_labels": [],
            "col_labels": [],
            "matrix": [],
        }

    # Project order from summaries (created_at desc, display_name)
    col_labels = [s["project_name"] for s in summaries]
    project_idx = {name: i for i, name in enumerate(col_labels)}

    pairs = get_project_skill_pairs(conn, user_id)
    skill_to_col_scores: Dict[str, Dict[int, float]] = {}
    for project_name, skill_name, score in pairs:
        if project_name not in project_idx:
            continue
        j = project_idx[project_name]
        if skill_name not in skill_to_col_scores:
            skill_to_col_scores[skill_name] = {}
        # Use max score if skill appears multiple times for same project (shouldn't happen)
        skill_to_col_scores[skill_name][j] = max(
            skill_to_col_scores[skill_name].get(j, 0), float(score)
        )

    row_labels = sorted(skill_to_col_scores.keys())
    matrix = []
    for skill in row_labels:
        row = [skill_to_col_scores[skill].get(j, 0.0) for j in range(len(col_labels))]
        matrix.append(row)

    return {
        "title": "Skills Across Projects",
        "row_labels": row_labels,
        "col_labels": col_labels,
        "matrix": matrix,
    }