import os
import sqlite3
from collections import defaultdict
from typing import Dict

EXTENSION_TO_LANGUAGE = {
    ".py": "Python",
    ".java": "Java",
    ".js": "JavaScript",
    ".html": "HTML",
    ".css": "CSS",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header"
}

def detect_languages(db_path: str) -> Dict[str, list[str]]:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT file_path, extension FROM files")
    rows = cursor.fetchall()
    conn.close()

    languages_by_project = defaultdict(set)

    for file_path, ext in rows:
        if ext not in EXTENSION_TO_LANGUAGE:
            continue

        # Extract just the first folder as the project name
        normalized_path = file_path.replace("\\", "/")  # handle Windows paths
        parts = normalized_path.split("/")
        proj_name = parts[0] if parts else "unknown"

        languages_by_project[proj_name].add(EXTENSION_TO_LANGUAGE[ext])

    # Convert sets to sorted lists
    return {proj: sorted(list(langs)) for proj, langs in languages_by_project.items()}
