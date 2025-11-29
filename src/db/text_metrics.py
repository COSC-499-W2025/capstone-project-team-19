import sqlite3
import json
from typing import Optional

import numpy as np

def sanitize_for_json(obj):
    """Recursively convert numpy types to python builtins."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(i) for i in obj]
    elif isinstance(obj, tuple):
        return tuple(sanitize_for_json(i) for i in obj)
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


def store_text_offline_metrics(
    conn: sqlite3.Connection,
    classification_id: int,
    project_metrics: dict | None,
    csv_metadata: dict | list | None = None
) -> None:

    if not classification_id or not project_metrics:
        return

    # Extract summary values
    summary_block = project_metrics.get("summary") or {}
    keywords = project_metrics.get("keywords") or []

    doc_count = summary_block.get("total_documents")
    total_words = summary_block.get("total_words")
    reading_level_avg = summary_block.get("reading_level_average")
    reading_level_label = summary_block.get("reading_level_label")

    # Sanitize everything BEFORE serialization
    clean_metrics = sanitize_for_json(project_metrics)
    summary_json = json.dumps(clean_metrics, ensure_ascii=False)

    keywords_json = json.dumps(
        sanitize_for_json(keywords), ensure_ascii=False
    )

    csv_metadata_json = json.dumps(
        sanitize_for_json(csv_metadata), ensure_ascii=False
    ) if csv_metadata is not None else None

    # Check existing row
    existing = conn.execute(
        """
        SELECT 
            doc_count,
            total_words,
            reading_level_avg,
            reading_level_label,
            keywords_json,
            summary_json,
            csv_metadata
        FROM non_llm_text
        WHERE classification_id = ?
        """,
        (classification_id,)
    ).fetchone()

    # ---------- UPDATE ----------
    if existing:
        if csv_metadata_json is None:
            csv_metadata_json = existing[6]

        conn.execute(
            """
            UPDATE non_llm_text
            SET
                doc_count = ?,
                total_words = ?,
                reading_level_avg = ?,
                reading_level_label = ?,
                keywords_json = ?,
                summary_json = ?,
                csv_metadata = ?,
                generated_at = datetime('now')
            WHERE classification_id = ?
            """,
            (
                doc_count,
                total_words,
                reading_level_avg,
                reading_level_label,
                keywords_json,
                summary_json,
                csv_metadata_json,
                classification_id,
            ),
        )

    # ---------- INSERT ----------
    else:
        conn.execute(
            """
            INSERT INTO non_llm_text (
                classification_id,
                doc_count,
                total_words,
                reading_level_avg,
                reading_level_label,
                keywords_json,
                summary_json,
                csv_metadata,
                generated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                classification_id,
                doc_count,
                total_words,
                reading_level_avg,
                reading_level_label,
                keywords_json,
                summary_json,
                csv_metadata_json,
            ),
        )

    conn.commit()



def get_text_non_llm_metrics(conn: sqlite3.Connection, classification_id: int) -> Optional[dict]:
    """Retrieve non-LLM metrics for a project classification."""

    row = conn.execute("""
        SELECT 
            doc_count,
            total_words,
            reading_level_avg,
            reading_level_label,
            keywords_json,
            summary_json,
            csv_metadata
        FROM non_llm_text
        WHERE classification_id = ?
    """, (classification_id,)).fetchone()

    if not row:
        return None

    keywords = json.loads(row[4]) if row[4] else []
    summary = json.loads(row[5]) if row[5] else {}
    csv_metadata = json.loads(row[6]) if row[6] else None

    return {
        "doc_count": row[0],
        "total_words": row[1],
        "reading_level_avg": row[2],
        "reading_level_label": row[3],
        "keywords": keywords,
        "summary": summary,
        "csv_metadata": csv_metadata
    }
