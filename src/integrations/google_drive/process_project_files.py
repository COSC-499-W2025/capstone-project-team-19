import sqlite3
from typing import Any, Dict
import src.db as db
from .api_calls import analyze_google_doc
import src.constants as constants

def process_project_files(conn: sqlite3.Connection, creds, drive_service, docs_service, user_id: int, project_name: str, user_email: str):
    """ Process all linked Google Drive files for a given text project."""
    files = db.get_project_drive_files(conn, user_id, project_name)

    for f in files:
        file_id = f["drive_file_id"]
        mime_type = f["mime_type"]

        if constants.VERBOSE:
            print(f"Analyzing file: {f['drive_file_name']} ({file_id})")

        result = analyze_drive_file(
            creds=creds,
            drive_service=drive_service,
            docs_service=docs_service,
            conn=conn,
            user_id=user_id,
            project_name=project_name,
            drive_file_id=file_id,
            drive_file_name=f["drive_file_name"],
            mime_type=mime_type,
            user_email=user_email,
        )

        if result.get("status") == "failed":
            print(f"Failed to analyze {f['drive_file_name']}: {result.get('error')}")
            continue

        # Store all user revisions
        for rev in result.get("revisions", []):
            revision_entry = {
                "user_id": user_id,
                "drive_file_id": file_id,
                "revision_id": rev.get("revision_id", "unknown"),
                "words_added": rev.get("word_count", 0),
                "revision_text": rev.get("raw_text"),
                "revision_timestamp": rev.get("timestamp"),
            }
            db.store_text_contribution_revision(conn, revision_entry)

        total_words = sum(rev.get("word_count", 0) for rev in result.get("revisions", []))
        summary_entry = {
            "user_id": user_id,
            "project_name": project_name,
            "drive_file_id": file_id,
            "user_revision_count": result.get("revision_count", 0),
            "total_word_count": total_words,
            "total_revision_count": result.get("total_revision_count", 0),
        }
        db.store_text_contribution_summary(conn, summary_entry)

        if constants.VERBOSE:
            print(f"Stored text contributation metrics for {file_id}")

        # Add Store SUMMARY later


def analyze_drive_file(creds, drive_service, docs_service, conn, user_id, project_name, drive_file_id, drive_file_name, mime_type, user_email) -> Dict[str, Any]:
    """
    Analyze a single linked Drive file.
    Routes to Google Doc analysis or non-Google Doc analysis.
    """
    _ = (conn, user_id, project_name, drive_file_name)
    if mime_type == "application/vnd.google-apps.document":
        return analyze_google_doc(
            creds=creds,
            drive_service=drive_service,
            docs_service=docs_service,
            drive_file_id=drive_file_id,
            user_email=user_email
        )
    # Unsupported mime type ( Add pdf, txt,docx analysis later)
    return {
        "status": "skipped",
        "error": f"Unsupported mime type: {mime_type}",
        "revisions": [],
        "revision_count": 0,
        "total_revision_count": 0,
    }