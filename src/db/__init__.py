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
)

# GitHub repository operations
from .github_repositories import (
    save_project_repo,
    get_project_repo,
)

# GitHub account operations
from .github_accounts import store_github_account

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
    store_text_llm_metrics,
    get_text_llm_metrics,
)

# Contribution operations
from .contributions import (
    store_text_contribution_revision,
    store_text_contribution_summary,
)

# Token operations
from .tokens import save_token_placeholder

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
    "save_project_repo",
    "get_project_repo",
    "store_github_account",
    "store_file_link",
    "get_project_drive_files",
    "get_unlinked_project_files",
    "get_latest_consent",
    "get_latest_external_consent",
    "store_text_offline_metrics",
    "store_text_llm_metrics",
    "get_text_llm_metrics",
    "store_text_contribution_revision",
    "store_text_contribution_summary",
    "save_token_placeholder",
]
