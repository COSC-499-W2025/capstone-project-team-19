import sqlite3
import json
from typing import Optional, Dict, Any

def insert_code_llm_metrics(
        conn: sqlite3.Connection,
        classification_id: int,
        project_summary: str
)->None:
    conn.execute(
        """
        INSERT INTO llm_code_individual (
        classification_id,
        project_summary,
        processed_at
        ) VALUES (?, ?, datetime('now'))
        """,
        (classification_id, project_summary),
        )
    conn.commit()

def update_code_llm_metrics(
        conn: sqlite3.Connection,
        classification_id: int,
        project_summary: str
)->None:
    conn.execute(
        """
        UPDATE llm_code_individual
        SET project_summary = ?,
        processed_at = datetime('now')
        WHERE classification_id = ?
        """,
        (project_summary, classification_id),
        )
    conn.commit()

def get_code_llm_metrics(
    conn: sqlite3.Connection,
    classification_id: int
) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        """
        SELECT metrics_id,
               classification_id,
               project_summary,
               processed_at
        FROM llm_code_individual
        WHERE classification_id = ?
        """,
        (classification_id,),
    ).fetchone()

    if not row:
        return None

    return {
        "metrics_id": row[0],
        "classification_id": row[1],
        "project_summary": row[2],
        "processed_at": row[3],
    }


def code_llm_metrics_exists(
    conn: sqlite3.Connection,
    classification_id: int
) -> bool:
    result = conn.execute(
        """
        SELECT 1
        FROM llm_code_individual
        WHERE classification_id = ?
        """,
        (classification_id,),
    ).fetchone()
    return result is not None

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
            WHERE classification_id = ?
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
                classification_id,
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
        conn.execute(
            """
            INSERT INTO non_llm_code_individual (
                classification_id,
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
                classification_id,
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
    row = conn.execute(
        """
        SELECT metrics_id,
               classification_id,
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
        WHERE classification_id = ?
        """,
        (classification_id,),
    ).fetchone()

    if not row:
        return None

    # Parse JSON fields
    radon_details = json.loads(row[13]) if row[13] else {}
    lizard_details = json.loads(row[14]) if row[14] else {}

    return {
        "metrics_id": row[0],
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
    result = conn.execute(
        """
        SELECT 1
        FROM non_llm_code_individual
        WHERE classification_id = ?
        """,
        (classification_id,),
    ).fetchone()
    return result is not None
