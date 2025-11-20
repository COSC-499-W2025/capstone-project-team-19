from .models import RawUserCollabMetrics

def compute_participation(user: RawUserCollabMetrics):
    """
    Compute how broadly and actively the user participates across project surfaces.
    """

    channels_used = sum([
        user.prs_opened > 0,
        user.prs_reviewed > 0,
        user.issues_opened > 0,
        user.issue_comments > 0,
        len(user.review_comments) > 0,
    ])

    # weighted activity score
    activity_score = (
        user.prs_opened * 1.2 +
        user.prs_reviewed * 1.0 +
        user.issues_opened * 1.3 +
        user.issue_comments * 0.7
    )

    return {
        "channels_used": channels_used,
        "activity_score": activity_score,
    }
