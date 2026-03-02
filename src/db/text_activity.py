"""
src/db/text_activity.py

Handles storage and retrieval of text activity type contribution data.
"""

import sqlite3
import json
from typing import Optional, Dict, Any
from datetime import datetime


def store_text_activity_contribution(
    conn: sqlite3.Connection,
    version_key: int,
    activity_data: Dict[str, Any]
) -> None:
    """
    Store activity type contribution data for a text project.

    Args:
        conn: Database connection
        version_key: Foreign key to project_versions table
        activity_data: Dictionary returned from get_activity_contribution_data()
                      containing timestamp_analysis, activity_classification,
                      timeline, and summary
    """
    if not version_key or not activity_data:
        return

    # Extract data from activity_data structure
    timestamp = activity_data.get('timestamp_analysis', {})
    classification = activity_data.get('activity_classification', {})
    timeline = activity_data.get('timeline', [])
    summary = activity_data.get('summary', {})

    # Serialize datetime objects in timeline
    serialized_timeline = []
    for entry in timeline:
        timeline_entry = entry.copy()
        if isinstance(timeline_entry.get('date'), datetime):
            timeline_entry['date'] = timeline_entry['date'].isoformat()
        serialized_timeline.append(timeline_entry)

    # Convert datetime objects to ISO format strings
    start_date = None
    end_date = None
    if timestamp.get('start_date'):
        if isinstance(timestamp['start_date'], datetime):
            start_date = timestamp['start_date'].isoformat()
        else:
            start_date = timestamp['start_date']

    if timestamp.get('end_date'):
        if isinstance(timestamp['end_date'], datetime):
            end_date = timestamp['end_date'].isoformat()
        else:
            end_date = timestamp['end_date']

    # Prepare JSON fields
    activity_classification_json = json.dumps(classification, ensure_ascii=False)
    timeline_json = json.dumps(serialized_timeline, ensure_ascii=False)
    activity_counts_json = json.dumps(summary.get('activity_counts', {}), ensure_ascii=False)

    # Check if record exists
    existing = conn.execute(
        "SELECT activity_id FROM text_activity_contribution WHERE version_key = ?",
        (version_key,)
    ).fetchone()

    if existing:
        # Update existing record
        conn.execute(
            """
            UPDATE text_activity_contribution
            SET start_date = ?,
                end_date = ?,
                duration_days = ?,
                total_files = ?,
                classified_files = ?,
                activity_classification_json = ?,
                timeline_json = ?,
                activity_counts_json = ?,
                generated_at = datetime('now')
            WHERE version_key = ?
            """,
            (
                start_date,
                end_date,
                timestamp.get('duration_days'),
                summary.get('total_files'),
                summary.get('classified_files'),
                activity_classification_json,
                timeline_json,
                activity_counts_json,
                version_key
            )
        )
    else:
        # Insert new record
        conn.execute(
            """
            INSERT INTO text_activity_contribution (
                version_key,
                start_date,
                end_date,
                duration_days,
                total_files,
                classified_files,
                activity_classification_json,
                timeline_json,
                activity_counts_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_key,
                start_date,
                end_date,
                timestamp.get('duration_days'),
                summary.get('total_files'),
                summary.get('classified_files'),
                activity_classification_json,
                timeline_json,
                activity_counts_json
            )
        )

    conn.commit()


def get_text_activity_contribution(
    conn: sqlite3.Connection,
    version_key: int
) -> Optional[Dict[str, Any]]:
    """
    Retrieve activity type contribution data for a text project.

    Args:
        conn: Database connection
        version_key: Foreign key to project_versions table

    Returns:
        Dictionary with activity contribution data or None if not found
    """
    row = conn.execute(
        """
        SELECT
            activity_id,
            version_key,
            start_date,
            end_date,
            duration_days,
            total_files,
            classified_files,
            activity_classification_json,
            timeline_json,
            activity_counts_json,
            generated_at
        FROM text_activity_contribution
        WHERE version_key = ?
        """,
        (version_key,)
    ).fetchone()

    if not row:
        return None

    # Parse JSON fields
    activity_classification = json.loads(row[7]) if row[7] else {}
    timeline = json.loads(row[8]) if row[8] else []
    activity_counts = json.loads(row[9]) if row[9] else {}

    return {
        'activity_id': row[0],
        'version_key': row[1],
        # Back-compat: callers/tests historically expected `classification_id`
        'classification_id': row[1],
        'timestamp_analysis': {
            'start_date': row[2],
            'end_date': row[3],
            'duration_days': row[4]
        },
        'summary': {
            'total_files': row[5],
            'classified_files': row[6],
            'activity_counts': activity_counts
        },
        'activity_classification': activity_classification,
        'timeline': timeline,
        'generated_at': row[10]
    }
