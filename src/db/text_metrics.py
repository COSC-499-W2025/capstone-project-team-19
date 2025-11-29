"""
src/db/text_metrics.py

Handles metrics storage and retrieval for text analysis:
 - Storing offline (non-LLM) metrics
 - Storing and retrieving LLM-based metrics
"""

import sqlite3
import json
from typing import Optional, Dict, Any


def store_text_offline_metrics(
    conn: sqlite3.Connection,
    classification_id: int,
    project_metrics: dict | None,
) -> None:
    if not classification_id or not project_metrics:
        return

    summary_block = project_metrics.get("summary") or {}
    keywords = project_metrics.get("keywords")

    doc_count = summary_block.get("total_documents")
    total_words = summary_block.get("total_words")
    reading_level_avg = summary_block.get("reading_level_average")
    reading_level_label = summary_block.get("reading_level_label")

    summary_json = json.dumps(project_metrics, ensure_ascii=False)
    keywords_json = json.dumps(keywords, ensure_ascii=False) if keywords is not None else None

    existing = conn.execute(
        """
        SELECT doc_count,
               total_words,
               reading_level_avg,
               reading_level_label,
               keywords_json,
               summary_json
        FROM non_llm_text
        WHERE classification_id = ?
        """,
        (classification_id,),
    ).fetchone()

    if existing:
        doc_count = doc_count if doc_count is not None else existing[0]
        total_words = total_words if total_words is not None else existing[1]
        reading_level_avg = reading_level_avg if reading_level_avg is not None else existing[2]
        reading_level_label = reading_level_label if reading_level_label is not None else existing[3]
        keywords_json = keywords_json if keywords_json is not None else existing[4]
        summary_json = summary_json if summary_json is not None else existing[5]

        conn.execute(
            """
            UPDATE non_llm_text
            SET doc_count = ?,
                total_words = ?,
                reading_level_avg = ?,
                reading_level_label = ?,
                keywords_json = ?,
                summary_json = ?,
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
                classification_id,
            ),
        )
    else:
        if keywords_json is None:
            keywords_json = json.dumps([], ensure_ascii=False)
        if summary_json is None:
            summary_json = json.dumps({}, ensure_ascii=False)

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
                generated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                classification_id,
                doc_count,
                total_words,
                reading_level_avg,
                reading_level_label,
                keywords_json,
                summary_json,
            ),
        )
    conn.commit()
    

def store_text_llm_metrics(conn: sqlite3.Connection, classification_id: int, project_name: str, file_name:str, file_path:str, linguistic:dict, summary: str, skills: list, success: dict )-> None:
    skills_json=json.dumps(skills)
    strength_json=json.dumps(success.get("strengths", []))
    weaknesses_json=json.dumps(success.get("weaknesses", []))
    conn.execute(
        """
        INSERT INTO llm_text(
        classification_id, file_path, file_name, project_name, word_count, sentence_count, flesch_kincaid_grade, lexical_diversity, summary, skills_json, strength_json, weaknesses_json, overall_score)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (classification_id, file_path, file_name, project_name, linguistic.get("word_count"), linguistic.get("sentence_count"), linguistic.get("flesch_kincaid_grade"), linguistic.get("lexical_diversity"), summary, skills_json, strength_json, weaknesses_json, success.get("score"))
        )
    conn.commit()


def get_text_llm_metrics(conn: sqlite3.Connection, classification_id: int) -> Optional[dict]:
    row = conn.execute("""
        SELECT text_metric_id, classification_id, project_name, file_name, file_path, word_count, sentence_count, flesch_kincaid_grade, lexical_diversity,
        summary, skills_json, strength_json, weaknesses_json, overall_score, processed_at
        FROM llm_text
        WHERE classification_id = ?
    """, (classification_id,)).fetchone()

    if not row:
        return None

    return {
        "text_metric_id": row[0],
        "classification_id": row[1],
        "project_name": row[2],
        "file_name": row[3],
        "file_path": row[4],
        "word_count": row[5],
        "sentence_count": row[6],
        "flesch_kincaid_grade": row[7],
        "lexical_diversity": row[8],
        "summary": row[9],
        "skills_json": row[10],
        "strength_json": row[11],
        "weaknesses_json": row[12],
        "overall_score": row[13],
        "processed_at": row[14]
    }

<<<<<<< HEAD
def get_text_non_llm_metrics(conn: sqlite3.Connection, classification_id: int) -> Optional[dict]:
    """
    Retrieve non-LLM text metrics for a project by classification_id.
    Returns:
    - doc_count
    - total_words
    - reading_level_avg
    - reading_level_label
    - keywords (parsed from JSON)
    """
=======

def get_text_non_llm_metrics(conn: sqlite3.Connection, classification_id: int) -> Optional[dict]:
>>>>>>> 15ebc4d648b2c7c2ba9005fddd5f6848dfc31fc0
    row = conn.execute("""
        SELECT doc_count, total_words, reading_level_avg, reading_level_label, keywords_json
        FROM non_llm_text
        WHERE classification_id = ?
    """, (classification_id,)).fetchone()

    if not row:
        return None

    keywords = json.loads(row[4]) if row[4] else []
    
    return {
        "doc_count": row[0],
        "total_words": row[1],
        "reading_level_avg": row[2],
        "reading_level_label": row[3],
        "keywords": keywords
    }