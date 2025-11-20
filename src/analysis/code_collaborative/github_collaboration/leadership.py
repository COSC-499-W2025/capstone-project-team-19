from .models import RawUserCollabMetrics

def compute_leadership(user: RawUserCollabMetrics):
    """
    Leadership = initiative + ability to review others' work.
    """

    initiator = user.prs_opened * 1.2 + user.issues_opened * 1.4
    reviewer = user.prs_reviewed * 1.0

    balance = abs(initiator - reviewer)

    return {
        "initiator_score": initiator,
        "reviewer_score": reviewer,
        "balance_score": balance,
        "leadership_score": initiator + reviewer,
    }
