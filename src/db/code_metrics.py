import sqlite3
import json
from typing import Optional, Dict, Any


def store_code_llm_metrics(
    conn: sqlite3.Connection,
    classification_id: int,
    project_summary: str
) -> None:
    if not classification_id or not project_summary:
        return

    # Check if record exists
    existing = conn.execute(
        """
        SELECT metrics_id
        FROM llm_code_individual
        WHERE classification_id = ?
        """,
        (classification_id,),
    ).fetchone()

    if existing:
        conn.execute(
            """
            UPDATE llm_code_individual
            SET project_summary = ?,
                processed_at = datetime('now')
            WHERE classification_id = ?
            """,
            (project_summary, classification_id),
        )
    else:
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


def store_code_complexity_metrics(
    conn: sqlite3.Connection,
    classification_id: int,
    complexity_summary: Dict[str, Any]
) -> None:
    if not classification_id or not complexity_summary:
        return

    # Extract metrics from summary
    total_files = complexity_summary.get('total_files', 0)
    total_lines = complexity_summary.get('total_lines', 0)
    total_code_lines = complexity_summary.get('total_code', 0)
    total_comments = complexity_summary.get('total_comments', 0)
    comment_ratio = 0
    if total_lines > 0:
        comment_ratio = round((total_comments / total_lines) * 100, 2)

    total_functions = complexity_summary.get('total_functions', 0)
    avg_complexity = complexity_summary.get('avg_complexity', 0)
    avg_maintainability = complexity_summary.get('avg_maintainability', 0)
    functions_needing_refactor = complexity_summary.get('functions_needing_refactor', 0)
    high_complexity_files = complexity_summary.get('high_complexity_files', 0)
    low_maintainability_files = complexity_summary.get('low_maintainability_files', 0)

    radon_details = complexity_summary.get('radon_details', {})
    radon_details_json = json.dumps(radon_details, ensure_ascii=False) if radon_details else json.dumps({})

    lizard_details = complexity_summary.get('lizard_details', {})
    lizard_details_json = json.dumps(lizard_details, ensure_ascii=False) if lizard_details else json.dumps({})

    existing = conn.execute(
        """
        SELECT metrics_id
        FROM non_llm_code_individual
        WHERE classification_id = ?
        """,
        (classification_id,),
    ).fetchone()

    if existing:
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
    else:
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
