import sqlite3
import json
from typing import Optional, Dict, Any


def update_code_complexity_metrics(
    conn: sqlite3.Connection,
    classification_id: int,
    total_files: int,
    total_lines: int,
    total_code_lines: int,
    total_comments: int,
    comment_ratio: float,
    total_functions: int,
    avg_complexity: float,
    avg_maintainability: float,
    functions_needing_refactor: int,
    high_complexity_files: int,
    low_maintainability_files: int,
    radon_details_json: str,
    lizard_details_json: str        
)-> None:
        version_key = classification_id
        conn.execute(
            """
            UPDATE non_llm_code_individual
            SET total_files = ?,
                total_lines = ?,
                total_code_lines = ?,
                total_comments = ?,
                comment_ratio = ?,
                total_functions = ?,
                avg_complexity = ?,
                avg_maintainability = ?,
                functions_needing_refactor = ?,
                high_complexity_files = ?,
                low_maintainability_files = ?,
                radon_details_json = ?,
                lizard_details_json = ?,
                generated_at = datetime('now')
            WHERE version_key = ?
            """,
            (
                total_files,
                total_lines,
                total_code_lines,
                total_comments,
                comment_ratio,
                total_functions,
                avg_complexity,
                avg_maintainability,
                functions_needing_refactor,
                high_complexity_files,
                low_maintainability_files,
                radon_details_json,
                lizard_details_json,
                version_key,
            ),
        )
        conn.commit()

def insert_code_complexity_metrics(
    conn: sqlite3.Connection,
    classification_id: int,
    total_files: int,
    total_lines: int,
    total_code_lines: int,
    total_comments: int,
    comment_ratio: float,
    total_functions: int,
    avg_complexity: float,
    avg_maintainability: float,
    functions_needing_refactor: int,
    high_complexity_files: int,
    low_maintainability_files: int,
    radon_details_json: str,
    lizard_details_json: str        
)-> None:
        version_key = classification_id
        conn.execute(
            """
            INSERT INTO non_llm_code_individual (
                version_key,
                total_files,
                total_lines,
                total_code_lines,
                total_comments,
                comment_ratio,
                total_functions,
                avg_complexity,
                avg_maintainability,
                functions_needing_refactor,
                high_complexity_files,
                low_maintainability_files,
                radon_details_json,
                lizard_details_json,
                generated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                version_key,
                total_files,
                total_lines,
                total_code_lines,
                total_comments,
                comment_ratio,
                total_functions,
                avg_complexity,
                avg_maintainability,
                functions_needing_refactor,
                high_complexity_files,
                low_maintainability_files,
                radon_details_json,
                lizard_details_json,
            ),
        )
        conn.commit()
    

def get_code_complexity_metrics(
    conn: sqlite3.Connection,
    classification_id: int
) -> Optional[Dict[str, Any]]:
    # Back-compat: parameter is named `classification_id` but is now a `version_key`.
    version_key = classification_id
    row = conn.execute(
        """
        SELECT metrics_id,
               version_key,
               total_files,
               total_lines,
               total_code_lines,
               total_comments,
               comment_ratio,
               total_functions,
               avg_complexity,
               avg_maintainability,
               functions_needing_refactor,
               high_complexity_files,
               low_maintainability_files,
               radon_details_json,
               lizard_details_json,
               generated_at
        FROM non_llm_code_individual
        WHERE version_key = ?
        """,
        (version_key,),
    ).fetchone()

    if not row:
        return None

    # Parse JSON fields
    radon_details = json.loads(row[13]) if row[13] else {}
    lizard_details = json.loads(row[14]) if row[14] else {}

    return {
        "metrics_id": row[0],
        "version_key": row[1],
        "classification_id": row[1],
        "total_files": row[2],
        "total_lines": row[3],
        "total_code_lines": row[4],
        "total_comments": row[5],
        "comment_ratio": row[6],
        "total_functions": row[7],
        "avg_complexity": row[8],
        "avg_maintainability": row[9],
        "functions_needing_refactor": row[10],
        "high_complexity_files": row[11],
        "low_maintainability_files": row[12],
        "radon_details": radon_details,
        "lizard_details": lizard_details,
        "generated_at": row[15],
    }


def code_complexity_metrics_exists(
    conn: sqlite3.Connection,
    classification_id: int
) -> bool:
    version_key = classification_id
    result = conn.execute(
        """
        SELECT 1
        FROM non_llm_code_individual
        WHERE version_key = ?
        """,
        (version_key,),
    ).fetchone()
    return result is not None
