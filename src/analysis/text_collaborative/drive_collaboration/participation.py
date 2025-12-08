from .models import RawUserTextCollabMetrics, RawTeamTextCollabMetrics


def compute_participation(user: RawUserTextCollabMetrics, team: RawTeamTextCollabMetrics):
    """
    Compute participation as the ratio of user's total comments (comments + replies + questions)
    to the team's total comments (comments + replies + questions).
    """
    channels_used = sum([
        user.comments_posted > 0,
        user.replies_posted > 0,
        user.questions_asked > 0,
    ])

    # Sum all user comments (comments + replies + questions)
    user_total = user.comments_posted + user.replies_posted + user.questions_asked
    
    # Sum all team comments (comments + replies + questions)
    team_total = team.total_comments + team.total_replies + team.total_questions
    
    # Calculate participation ratio
    if team_total > 0:
        activity_score = user_total / team_total
    else:
        activity_score = 0.0

    return {
        "channels_used": channels_used,
        "activity_score": activity_score,
        "files_engaged": len(user.files_commented_on),
    }