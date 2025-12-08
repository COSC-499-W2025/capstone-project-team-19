import sqlite3
from typing import Any, Dict
import src.db as db
from .api_calls import analyze_google_doc
try:
    from src import constants
except ModuleNotFoundError:
    import constants

from src.analysis.text_collaborative.drive_collaboration.build_drive_collab_metrics import run_drive_collaboration_analysis

# Set to False to skip revision history analysis (code is preserved but won't run)
ENABLE_REVISION_HISTORY = False

def process_project_files(conn: sqlite3.Connection, creds, drive_service, docs_service, user_id: int, project_name: str, user_email: str, user_display_name: str = None):
    """ Process all linked Google Drive files for a given text project."""
    files = db.get_project_drive_files(conn, user_id, project_name)

    doc_file_ids = []  # Collect only Google Docs file IDs for collaboration analysis

    for f in files:
        file_id = f["drive_file_id"]
        mime_type = f["mime_type"]
        
        # Only track Google Docs for collaboration (only they support comments)
        if mime_type == "application/vnd.google-apps.document":
            doc_file_ids.append(file_id)
        
        # Skip revision history analysis if disabled
        if not ENABLE_REVISION_HISTORY:
            print(f"Collecting file: {f['drive_file_name']} ({file_id})")
            continue
        
        # REVISION HISTORY ANALYSIS (disabled by default)
        print(f"Analyzing file: {f['drive_file_name']} ({file_id})")

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

      
    #Run collaboration analysis after processing all files (only Google Docs support comments)
    if doc_file_ids and drive_service:
        print("\n[TEXT-COLLAB] Analyzing collaboration metrics from comments...")
        try:
            collab_profile = run_drive_collaboration_analysis(
                drive_service=drive_service,
                file_ids=doc_file_ids,
                user_email=user_email,
                user_display_name=user_display_name
            )
            return {
                "status": "success",
                "collaboration_profile": collab_profile
            }
        except Exception as e:
            print(f"[TEXT-COLLAB] Failed to analyze collaboration: {e}")
            return {"status": "partial", "error": str(e)}
    return {"status": "success"}


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