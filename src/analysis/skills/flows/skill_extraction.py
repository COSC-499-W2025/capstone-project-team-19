"""
This file must:
- load metadata from the database
- Decide which skill extraction function to run
- Route to the correct skill extraction function
- Handle missing data safely
"""

import sqlite3
from src.db import get_project_metadata
from src.utils.helpers import _fetch_files
from src.analysis.skills.flows.code_skill_extraction import extract_code_skills
from src.analysis.skills.flows.text_skill_extraction import extract_text_skills

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
    
    print(f"[SKILLS] Extracting skills for {project_name} ({classification}, {project_type})")

    if project_type == "code":
        extract_code_skills(conn, user_id, project_name, classification, files)
    elif project_type == "text":
        extract_text_skills(conn, user_id, project_name, classification, files)
    else:
        print(f"[SKILLS] Project type is not valid, skipping skill extraction for '{project_name}'")

    print(f"[SKILLS] Done extracting skills for {project_name}")