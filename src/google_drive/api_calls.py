def analyze_google_doc(service, drive_file_id, user_email):
    """
    Analyze a Google Doc file for all revisions by a single user.
    Returns:
      - list of user revisions with revision_id, raw_text, word_count, timestamp
      - total_revision_count (all users)
      - user_revision_count (for user_email)
    """
    from googleapiclient.errors import HttpError

    try:
        revisions = service.revisions().list(fileId=drive_file_id).execute().get("revisions", [])
        total_revision_count = len(revisions)
        user_revisions = []

        for rev in revisions:
            rev_id = rev.get("id")
            rev_user_email = rev.get("lastModifyingUser", {}).get("emailAddress")
            rev_timestamp = rev.get("modifiedTime")

            if rev_user_email == user_email:
                # Get current document content (Docs API gives current text)
                doc_content = service.documents().get(documentId=drive_file_id).execute().get("body", {}).get("content", [])
                revision_text = ""
                for element in doc_content:
                    if "paragraph" in element:
                        for e in element["paragraph"]["elements"]:
                            if "textRun" in e:
                                revision_text += e["textRun"].get("content", "")

                revision_size = len(revision_text)

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
