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
    get_user_by_id
)

# Project operations
from .projects import (
    store_parsed_files,
    record_project_classification,
    record_project_classifications,
    get_project_classifications,
    get_classification_id,
    get_project_metadata,
    get_zip_name_for_project,
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

from .skill_preferences import (
    get_user_skill_preferences,
    upsert_skill_preference,
    bulk_upsert_skill_preferences,
    clear_skill_preferences,
    get_all_user_skills,
    has_skill_preferences,
)

# file contributions
from .file_contributions import (
    store_file_contributions,
    get_user_contributed_files,
    get_file_contribution_stats,
    has_contribution_data,
    delete_file_contributions_for_project,
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
    get_all_user_project_summaries,
    set_project_dates,
    get_project_dates,
    clear_project_dates,
    clear_all_project_dates,
    get_all_manual_dates,
    update_project_summary_json,
    get_project_summary_by_id
)

# local git metrics for code collaborative projects
from .code_collaborative import (
    insert_code_collaborative_metrics,
    get_metrics_id,
    insert_code_collaborative_summary,
)

# resume snapshots
from .resumes import (
    insert_resume_snapshot,
    list_resumes,
    get_resume_snapshot,
    update_resume_snapshot,
    delete_resume_snapshot
)

from .delete_project import delete_project_everywhere


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
    get_code_individual_duration,
)

# deduplication
from .deduplication import (
    find_existing_version_by_strict_fp,
    find_existing_version_by_loose_fp,
    get_latest_versions,
    get_hash_set_for_version,
    get_relpath_set_for_version,
    insert_project,
    insert_project_version,
    insert_version_files,
    _lookup_existing_name
)

# project rankings (query-only; mutation logic lives in src/services)
from .project_rankings import (
    get_project_rank,
    get_all_project_ranks,
)

# uploads
from .uploads import (
    create_upload,
    get_upload_by_id,
    list_uploads_for_user,
    update_upload_status,
    update_upload_zip_metadata,
    set_upload_state,
    patch_upload_state,
    mark_upload_failed,
    delete_upload,
)
from .project_thumbnails import (
    upsert_project_thumbnail,
    get_project_thumbnail_path,
    delete_project_thumbnail,
    list_thumbnail_projects,
)

from src.db.project_feedback import (
    upsert_project_feedback,
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
    "delete_file_contributions_for_project",
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
    "update_project_summary_json",
    "insert_code_collaborative_metrics",
    "get_metrics_id",
    "insert_code_collaborative_summary",
    "get_all_user_project_summaries",
    "get_project_summary_row",
    "get_code_activity_percentages",
    "get_code_collaborative_duration",
    "get_code_collaborative_non_llm_summary",
    "get_text_duration",
    "get_code_individual_duration",
    "git_individual_metrics_exists",
    "insert_git_individual_metrics",
    "update_git_individual_metrics",
    "get_git_individual_metrics",
    "extract_git_metrics",
    "set_project_dates",
    "get_project_dates",
    "clear_project_dates",
    "clear_all_project_dates",
    "get_all_manual_dates",
    "find_existing_version_by_strict_fp",
    "find_existing_version_by_loose_fp",
    "get_latest_versions",
    "get_hash_set_for_version",
    "get_relpath_set_for_version",
    "insert_project",
    "insert_project_version",
    "insert_version_files",
    "get_project_rank",
    "get_all_project_ranks",
    "get_user_by_id",
    "get_zip_name_for_project",
    "insert_resume_snapshot",
    "list_resumes",
    "get_resume_snapshot",
    "update_resume_snapshot",
    "delete_resume_snapshot",
    "delete_project_everywhere",
    "create_upload",
    "get_upload_by_id",
    "list_uploads_for_user",
    "update_upload_status",
    "update_upload_zip_metadata",
    "set_upload_state",
    "patch_upload_state",
    "mark_upload_failed",
    "delete_upload",
    "upsert_project_thumbnail",
    "get_project_thumbnail_path",
    "delete_project_thumbnail",
    "list_thumbnail_projects",
    "upsert_project_feedback",
    "get_project_summary_by_id",
    "get_user_skill_preferences",
    "upsert_skill_preference",
    "bulk_upsert_skill_preferences",
    "clear_skill_preferences",
    "get_all_user_skills",
    "has_skill_preferences",
]
