from .models import RawUserTextCollabMetrics


def compute_participation(user: RawUserTextCollabMetrics):
    """
    Compute how broadly and actively the user participates across project surfaces.
    Measures participation quantity and breadth, independent of communication quality.
    """
    channels_used = sum([
        user.comments_posted > 0,
        user.replies_posted > 0,
        user.questions_asked > 0,
    ])
    
    # Weighted activity score: Questions (1.3) weighted higher as they drive discussion.
    # Comments (1.2) weighted higher than replies (1.0) as they initiate conversation.
    activity_score = (
        user.comments_posted * 1.2 +
        user.replies_posted * 1.0 +
        user.questions_asked * 1.3
    )

    return {
        "channels_used": channels_used,
        "activity_score": activity_score,
        "files_engaged": len(user.files_commented_on),
    }