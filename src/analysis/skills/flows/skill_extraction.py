"""
This file must:
- load metadata from the database
- Decide which skill extraction function to run
- Route to the correct skill extraction function
- Handle missing data safely
"""

import sqlite3
import os
from src.db import get_project_metadata, has_contribution_data, get_user_contributed_files
from src.utils.helpers import _fetch_files
from src.analysis.skills.flows.code_skill_extraction import extract_code_skills

def extract_skills(conn: sqlite3.Connection, user_id: int, project_name: str):
    """
    Unified entry point for extracting skills from any project.
    Determines project type + classification and routes to the appropriate skill extractor.
    """

    classification, project_type = get_project_metadata(conn, user_id, project_name)

    if not project_type or not classification:
        print(f"[SKILLS] Cannot extract skills for '{project_name}' (missing metadata).")
        return

    files = _fetch_files(conn, user_id, project_name, only_text=(project_type == "text"))
    if not files:
        print(f"[SKILLS] No files found for '{project_name}'. Skipping skill extraction.")
        return

    # For collaborative projects, filter files based on user contributions
    if classification == "collaborative" and has_contribution_data(conn, user_id, project_name):
        contributed_files = get_user_contributed_files(conn, user_id, project_name)

        if contributed_files:
            # Filter files to only include those the user contributed to
            original_count = len(files)

            # Match by filename (basename) since file_path formats might differ
            files = [
                f for f in files
                if any(os.path.basename(f.get("file_path", "")) == os.path.basename(contrib_path)
                       for contrib_path in contributed_files)
            ]

            filtered_count = len(files)
            print(f"[SKILLS] Filtered to {filtered_count}/{original_count} files based on your contributions")
        else:
            print(f"[SKILLS] Warning: No contributions found for '{project_name}', using all files")

    if not files:
        print(f"[SKILLS] No contributed files found for '{project_name}'. Skipping skill extraction.")
        return

    print(f"[SKILLS] Extracting skills for {project_name} ({classification}, {project_type})")

    if project_type == "code":
        extract_code_skills(conn, user_id, project_name, classification, files)
    else:
        print(f"[SKILLS] Project type is not valid, skipping skill extraction for '{project_name}'")

    print(f"[SKILLS] Done extracting skills for {project_name}")