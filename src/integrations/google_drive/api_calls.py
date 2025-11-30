from typing import Optional


def _count_words(text: Optional[str]) -> int:
    if not text:
        return 0
    return len([tok for tok in text.split() if tok.strip()])


def _fetch_current_doc_text(docs_service, drive_file_id: str) -> str:
    """
    Best-effort fallback to fetch the current document content when a specific
    revision export is unavailable. Returns an empty string on failure.
    """
    try:
        doc_content = docs_service.documents().get(documentId=drive_file_id).execute().get("body", {}).get("content", [])
    except Exception:
        return ""

    text_chunks = []
    for element in doc_content:
        if "paragraph" in element:
            for e in element["paragraph"]["elements"]:
                if "textRun" in e:
                    text_chunks.append(e["textRun"].get("content", ""))
    return "".join(text_chunks)


def analyze_google_doc(drive_service, docs_service, drive_file_id, user_email, creds: Optional[object] = None):
    """
    Analyze a Google Doc file for all revisions by a single user.
    Returns:
      - list of user revisions with revision_id, raw_text, word_count, timestamp
      - total_revision_count (all users)
      - user_revision_count (for user_email)
    """
    from googleapiclient.errors import HttpError

    try:
        revisions = drive_service.revisions().list(
            fileId=drive_file_id,
            fields="revisions(id,modifiedTime,lastModifyingUser(emailAddress,displayName))"
        ).execute().get("revisions", [])
        total_revision_count = len(revisions)
        user_revisions = []

        target_email = (user_email or "").strip().lower()

        session = None
        if creds is not None:
            try:
                from google.auth.transport.requests import AuthorizedSession
                session = AuthorizedSession(creds)
            except Exception:
                session = None
        
        for rev in revisions:
            rev_id = rev.get("id")
            rev_timestamp = rev.get("modifiedTime")
            rev_user_email = (rev.get("lastModifyingUser", {}).get("emailAddress") or "").strip().lower()

            if rev_user_email == target_email:
                revision_text = None
                text_source = "no_export_session"

                if session:
                    try:
                        rev_details = drive_service.revisions().get(
                            fileId=drive_file_id,
                            revisionId=rev_id,
                            fields="exportLinks"
                        ).execute()
                        export_url = rev_details.get("exportLinks", {}).get("text/plain")
                        if export_url:
                            response = session.get(export_url)
                            response.raise_for_status()
                            revision_text = response.text
                            text_source = "export_links"
                    except Exception:
                        revision_text = None

                if revision_text is None:
                    revision_text = _fetch_current_doc_text(docs_service, drive_file_id)
                    text_source = "current_doc_fallback"

                revision_text = revision_text or ""
                char_count = len(revision_text)
                revision_size = _count_words(revision_text)

                user_revisions.append({
                    "revision_id": rev_id,
                    "raw_text": revision_text,
                    "word_count": revision_size,
                    "timestamp": rev_timestamp
                })

        return {
            "status": "analyzed",
            "revisions": user_revisions,       # all of this user’s revisions
            "revision_count": len(user_revisions),
            "total_revision_count": total_revision_count
        }

    except HttpError as e:
        return {"status": "failed", "error": str(e)}
