from src.summary.metrics_model import CodeProjectMetrics, TextProjectMetrics
from src.summary.db_access import (
    fetch_all_project_metadata,
    fetch_github_metrics_row
)
import json


def build_all_project_metrics(conn, user_id):
    rows = fetch_all_project_metadata(conn, user_id)
    all_projects = []

    for project_name, classification, project_type in rows:
        if project_type == "code":
            obj = build_code_metrics(conn, user_id, project_name, classification)
        else:
            obj = build_text_metrics(conn, user_id, project_name, classification)

        all_projects.append(obj)

    return all_projects


def build_code_metrics(conn, user_id, project_name, classification):
    obj = CodeProjectMetrics(project_name)
    obj.classification = classification
    obj.is_collaborative = (classification == "collaborative")

    # --- 1. GitHub REST API metrics (only table that exists right now) ---
    gh = fetch_github_metrics_row(conn, user_id, project_name)
    if gh:
        (
            obj.github_total_commits,
            obj.github_commit_days,
            obj.github_first_commit,
            obj.github_last_commit,
            obj.github_issues_opened,
            obj.github_issues_closed,
            obj.github_prs_opened,
            obj.github_prs_merged,
            obj.github_additions,
            obj.github_deletions,
            obj.github_contribution_percent
        ) = gh

    # TODO: the rest of the code metrics are not yet stored in the database, this must be further implemented once they are

    return obj


def build_text_metrics(conn, user_id, project_name, classification):
    obj = TextProjectMetrics(project_name)
    obj.classification = classification
    obj.is_collaborative = (classification == "collaborative")

    # TODO: Populate text metrics

    return obj
