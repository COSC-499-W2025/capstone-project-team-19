from .models import RawUserTextCollabMetrics


def compute_communication_leadership(user: RawUserTextCollabMetrics):
    """
    Leadership = initiative (comments/questions) + responsiveness (replies).
    """
    # Weighting rationale: Questions (1.4) weighted higher than comments (1.2) because
    # asking questions demonstrates stronger engagement and drives discussion.
    initiator = user.comments_posted * 1.2 + user.questions_asked * 1.4
    responder = user.replies_posted * 1.0

    balance = abs(initiator - responder)

    return {
        "initiator_score": initiator,
        "responder_score": responder,
        "balance_score": balance,
        "leadership_score": initiator + responder,
    }