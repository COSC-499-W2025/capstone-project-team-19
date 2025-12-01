"""
src/db/__init__.py

Database module exports.

All database operations are organized by domain:
- users.py: User operations (read and write)
- projects.py: Project operations (read and write)
- github_repositories.py: GitHub repository operations (read and write)
- github_accounts.py: GitHub account write operations
- drive_files.py: Google Drive file operations (read and write)
- consent.py: Consent operations (read)
- text_metrics.py: Text metrics operations (read and write)
- contributions.py: Contribution write operations
- tokens.py: Token write operations
- connection.py: Connection and schema management
- code_activity.py: Code activity metrics (read and write)
"""

# Connection and schema
from .connection import connect, init_schema

# User operations
from .users import (
    get_user_by_username,
    get_or_create_user,
)

# Project operations
from .projects import (
    store_parsed_files,
    record_project_classification,
    record_project_classifications,
    get_project_classifications,
    get_classification_id,
    get_project_metadata
)

# GitHub repository operations
from .github_repositories import (
    save_project_repo,
    get_project_repo,
    store_collaboration_profile
)

# GitHub account operations
from .github_accounts import store_github_account, has_github_account

# Drive file operations
from .drive_files import (
    store_file_link,
    get_project_drive_files,
    get_unlinked_project_files,
)

# Consent operations
from .consent import (
    get_latest_consent,
    get_latest_external_consent,
)

# Text metrics operations
from .text_metrics import (
    store_text_offline_metrics,
    get_text_non_llm_metrics,
)

# Code metrics operations
from .code_metrics import (
    code_complexity_metrics_exists,
    insert_code_complexity_metrics,
    update_code_complexity_metrics,
    get_code_complexity_metrics,
)
# Code metrics helpers (data extraction/transformation)
from .code_metrics_helpers import (
    extract_complexity_metrics,
)

# Contribution operations
from .contributions import (
    store_text_contribution_revision,
    store_text_contribution_summary,
)

# Token operations
from .tokens import save_token_placeholder

# skills
from .skills import insert_project_skill, get_skill_events

# file contributions
from .file_contributions import (
    store_file_contributions,
    get_user_contributed_files,
    get_file_contribution_stats,
    has_contribution_data,
)

# files
from .files import get_files_for_project, get_files_with_timestamps

# text activity type contribution
from .text_activity import (
    store_text_activity_contribution,
    get_text_activity_contribution,
)

# code activity type
from .code_activity import (
    delete_code_activity_metrics_for_project,
    insert_code_activity_metric,
    store_code_activity_metrics,
)

# github prs
from .github_pull_requests import get_pull_requests_for_project

# project summaries
from .project_summaries import (
    save_project_summary,
    get_project_summaries_list,
    get_project_summary_by_name,
    get_all_projects_with_dates,
    get_all_user_project_summaries
)

# local git metrics for code collaborative projects
from .code_collaborative import (
    insert_code_collaborative_metrics,
    get_metrics_id,
    insert_code_collaborative_summary,
)

# resume snapshots
from .resumes import insert_resume_snapshot, list_resumes, get_resume_snapshot

# git individual metrics
from .git_individual_metrics import (
    git_individual_metrics_exists,
    insert_git_individual_metrics,
    update_git_individual_metrics,
    get_git_individual_metrics
)

# git metrics helpers (data extraction/transformation)
from .git_metrics_helpers import extract_git_metrics

# portfolio
from .portfolio import (
    get_project_summary_row,
    get_code_activity_percentages,
    get_code_collaborative_duration,
    get_code_collaborative_non_llm_summary,
    get_text_duration,
)

__all__ = [
    "connect",
    "init_schema",
    "get_user_by_username",
    "get_or_create_user",
    "store_parsed_files",
    "record_project_classification",
    "record_project_classifications",
    "get_project_classifications",
    "get_classification_id",
    "get_project_metadata",
    "save_project_repo",
    "get_project_repo",
    "store_collaboration_profile",
    "store_github_account",
    "has_github_account",
    "store_file_link",
    "get_project_drive_files",
    "get_unlinked_project_files",
    "get_latest_consent",
    "get_latest_external_consent",
    "store_text_offline_metrics",
    "get_text_non_llm_metrics",
    "code_complexity_metrics_exists",
    "insert_code_complexity_metrics",
    "update_code_complexity_metrics",
    "get_code_complexity_metrics",
    "extract_complexity_metrics",
    "store_text_contribution_revision",
    "store_text_contribution_summary",
    "save_token_placeholder",
    "insert_project_skill",
    "get_project_skills",
    "store_file_contributions",
    "get_user_contributed_files",
    "get_file_contribution_stats",
    "has_contribution_data",
    "delete_code_activity_metrics_for_project",
    "insert_code_activity_metric",
    "store_code_activity_metrics",
    "get_pull_requests_for_project",
    "get_files_for_project",
    "get_files_with_timestamps",
    "store_text_activity_contribution",
    "get_text_activity_contribution",
    "save_project_summary",
    "get_project_summaries_list",
    "get_project_summary_by_name",
    "get_all_projects_with_dates", 
    "get_skill_events",
    "insert_code_collaborative_metrics",
    "get_metrics_id",
    "insert_code_collaborative_summary",
    "get_all_user_project_summaries",
    "get_project_summary_row",
    "get_code_activity_percentages",
    "get_code_collaborative_duration",
    "get_code_collaborative_non_llm_summary",
    "get_text_duration,"
    "git_individual_metrics_exists",
    "insert_git_individual_metrics",
    "update_git_individual_metrics",
    "get_git_individual_metrics",
    "extract_git_metrics"
]
