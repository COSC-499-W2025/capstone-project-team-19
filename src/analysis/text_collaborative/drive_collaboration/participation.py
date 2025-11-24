from .models import RawUserTextCollabMetrics
from .comment_quality import compute_comment_quality


def compute_participation(user: RawUserTextCollabMetrics):
    """
    Compute how broadly and actively the user participates across project surfaces.
    """
    channels_used = sum([
        user.comments_posted > 0,
        user.replies_posted > 0,
        user.questions_asked > 0,
    ])

    # Compute comment quality to adjust weight
    comment_quality = compute_comment_quality(user.comment_texts)
    quality_multiplier = 0.5 + (comment_quality["score"] / 5) * 1.0  # Range: 0.5 to 1.5
    
    # Weighted activity score: Questions (1.3) weighted higher as they drive discussion.
    # Comments (1.2) weighted higher than replies (1.0) as they initiate conversation.
    activity_score = (
        user.comments_posted * 1.2 * quality_multiplier +
        user.replies_posted * 1.0 +
        user.questions_asked * 1.3
    )

    return {
        "channels_used": channels_used,
        "activity_score": activity_score,
        "files_engaged": len(user.files_commented_on),
    }