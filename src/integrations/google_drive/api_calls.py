from typing import Optional

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
                    except Exception:
                        revision_text = None

                if revision_text is None:
                    # Fallback to current document content
                    doc_content = docs_service.documents().get(documentId=drive_file_id).execute().get("body", {}).get("content", [])
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


def fetch_drive_comments(drive_service, file_id, user_email, user_display_name=None):
    """
    Fetch all comments and replies from a Google Drive file.
    Matches by email if available, otherwise by displayName.
    Returns comments, replies, and questions for both user and team.
    """
    from googleapiclient.errors import HttpError
    from datetime import datetime
        
    try:
        # Fetch all comments for the file
        comments_response = drive_service.comments().list(
            fileId=file_id,
            fields="comments(id,content,author(displayName,emailAddress),createdTime,replies(id,content,author(displayName,emailAddress),createdTime),resolved)"
        ).execute()
        
        comments = comments_response.get("comments", [])
        target_email = (user_email or "").strip().lower()
        target_display_name = (user_display_name or "").strip()
        
        user_comments = []
        user_replies = []
        user_questions = []
        user_comment_timestamps = []
        user_reply_timestamps = []
        team_comments = []
        team_replies = []
        team_questions = []
        
        for comment in comments:
            author = comment.get("author", {})
            comment_author_email = (author.get("emailAddress") or "").strip().lower()
            comment_author_name = (author.get("displayName") or "").strip()
            
            # Match by email OR displayName (case-insensitive)
            is_user_comment = False
            if comment_author_email and comment_author_email == target_email:
                is_user_comment = True
            elif comment_author_name and target_display_name:
                # Try exact match first
                if comment_author_name == target_display_name:
                    is_user_comment = True
                # Try case-insensitive match
                elif comment_author_name.lower() == target_display_name.lower():
                    is_user_comment = True            
            comment_content = comment.get("content", "")
            comment_created = comment.get("createdTime")
            is_resolved = comment.get("resolved", False)
            
            is_question = "?" in comment_content
            
            comment_timestamp = None
            if comment_created:
                try:
                    comment_timestamp = datetime.fromisoformat(comment_created.replace("Z", "+00:00"))
                except:
                    pass
            
            team_comments.append(comment_content)
            if is_question:
                team_questions.append(comment_content)
            
            if is_user_comment:
                user_comments.append(comment_content)
                user_comment_timestamps.append(comment_timestamp)
                if is_question:
                    user_questions.append(comment_content)
            
            # Process replies
            replies = comment.get("replies", [])
            for reply in replies:
                reply_author = reply.get("author", {})
                reply_author_email = (reply_author.get("emailAddress") or "").strip().lower()
                reply_author_name = (reply_author.get("displayName") or "").strip()
                
                # Match by email OR displayName (case-insensitive)
                is_user_reply = False
                if reply_author_email and reply_author_email == target_email:
                    is_user_reply = True
                elif reply_author_name and target_display_name:
                    # Try exact match first
                    if reply_author_name == target_display_name:
                        is_user_reply = True
                    # Try case-insensitive match
                    elif reply_author_name.lower() == target_display_name.lower():
                        is_user_reply = True
                
                reply_content = reply.get("content", "")
                reply_created = reply.get("createdTime")
                
                reply_timestamp = None
                if reply_created:
                    try:
                        reply_timestamp = datetime.fromisoformat(reply_created.replace("Z", "+00:00"))
                    except:
                        pass
                
                team_replies.append(reply_content)
                
                if is_user_reply:
                    user_replies.append(reply_content)
                    user_reply_timestamps.append(reply_timestamp)
                
        return {
            "status": "success",
            "user": {
                "comments": user_comments,
                "replies": user_replies,
                "questions": user_questions,
                "comment_timestamps": user_comment_timestamps,
                "reply_timestamps": user_reply_timestamps,
            },
            "team": {
                "comments": team_comments,
                "replies": team_replies,
                "questions": team_questions,
            }
        }
    
    except HttpError as e:
        return {"status": "failed", "error": str(e)}
    except Exception as e:
        return {"status": "failed", "error": str(e)}