"""
Converts raw Google Drive API comment data into RawUserTextCollabMetrics + RawTeamTextCollabMetrics
objects expected by the collaboration-skill pipeline.
"""
from datetime import datetime
from typing import List, Dict
from src.integrations.google_drive.api_calls import fetch_drive_comments
from src.analysis.text_collaborative.drive_collaboration.compute_drive_collab_profile import (
    compute_text_collaboration_profile, 
    compute_skill_levels
)
from .models import RawUserTextCollabMetrics, RawTeamTextCollabMetrics


def build_drive_collaboration_metrics(
    drive_service, 
    file_ids: List[str], 
    user_email: str,
    user_display_name: str = None
) -> tuple[RawUserTextCollabMetrics, RawTeamTextCollabMetrics]:
    """
    Fetch comments from all Drive files and build metrics objects.
    """
    # Aggregate data across all files
    all_user_comments = []
    all_user_replies = []
    all_user_questions = []
    all_user_comment_timestamps = []
    all_user_reply_timestamps = []
    all_user_files_commented_on = set()
    
    all_team_comments = []
    all_team_replies = []
    all_team_questions = []
    all_team_files = set()
    
    for file_id in file_ids:
        result = fetch_drive_comments(drive_service, file_id, user_email, user_display_name)
        
        if result.get("status") != "success":
            continue
        
        user_data = result["user"]
        team_data = result["team"]
        
        # User data
        if user_data["comments"] or user_data["replies"]:
            all_user_files_commented_on.add(file_id)
        all_user_comments.extend(user_data["comments"])
        all_user_replies.extend(user_data["replies"])
        all_user_questions.extend(user_data["questions"])
        all_user_comment_timestamps.extend(user_data["comment_timestamps"])
        all_user_reply_timestamps.extend(user_data["reply_timestamps"])
        
        # Team data
        if team_data["comments"] or team_data["replies"]:
            all_team_files.add(file_id)
        all_team_comments.extend(team_data["comments"])
        all_team_replies.extend(team_data["replies"])
        all_team_questions.extend(team_data["questions"])
    
    # Build user metrics
    user = RawUserTextCollabMetrics(
        comments_posted=len(all_user_comments),
        replies_posted=len(all_user_replies),
        questions_asked=len(all_user_questions),
        comments_resolved=0,  # TODO: Track resolved comments if needed
        comment_texts=all_user_comments,
        reply_texts=all_user_replies,
        comment_timestamps=[ts for ts in all_user_comment_timestamps if ts is not None],
        reply_timestamps=[ts for ts in all_user_reply_timestamps if ts is not None],
        files_commented_on=list(all_user_files_commented_on),
    )
    
    # Build team metrics
    team = RawTeamTextCollabMetrics(
        total_comments=len(all_team_comments),
        total_replies=len(all_team_replies),
        total_files=len(all_team_files),
        total_questions=len(all_team_questions),
    )
    
    return user, team


def run_drive_collaboration_analysis(
    drive_service,
    file_ids: List[str],
    user_email: str,
    user_display_name: str = None
) -> Dict:
    """
    Run full collaboration analysis pipeline for Google Drive files.
    """
    user, team = build_drive_collaboration_metrics(drive_service, file_ids, user_email, user_display_name)
    profile = compute_text_collaboration_profile(user, team)
    
    skill_levels = compute_skill_levels(profile)
    profile["skill_levels"] = skill_levels
    
    return profile