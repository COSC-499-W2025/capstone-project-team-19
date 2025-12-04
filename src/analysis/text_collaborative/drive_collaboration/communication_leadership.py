from .models import RawUserTextCollabMetrics


def compute_communication_leadership(user: RawUserTextCollabMetrics):
    """
    Communication leadership focuses on *how* someone participates, not just how much:

    - Initiative: starting threads and asking questions.
    - Responsiveness: replying to others.
    - Style: proportion of initiative vs responses and how question‑heavy their activity is.

    The final leadership_score is a 0–20 style score derived from ratios, so it is
    intentionally different from the raw volume–based participation score.
    """
    comments = user.comments_posted
    replies = user.replies_posted
    questions = user.questions_asked

    # If there is no activity at all, everything is zero.
    if comments == 0 and replies == 0 and questions == 0:
        return {
            "initiator_score": 0.0,
            "responder_score": 0.0,
            "balance_score": 0.0,
            "leadership_score": 0.0,
        }

    # Initiative: starting or steering discussions (comments + questions).
    # Questions are slightly higher impact than comments.
    initiator = comments * 1.2 + questions * 1.6

    # Responsiveness: replying to others.
    responder = replies * 1.0

    total_activity = initiator + responder

    # Ratios capture *style* of participation, independent of sheer volume.
    initiator_ratio = initiator / total_activity if total_activity > 0 else 0.0

    total_messages = comments + replies + questions
    question_ratio = questions / total_messages if total_messages > 0 else 0.0

    # Balance score: how skewed someone is towards initiating vs responding (0 = perfectly balanced).
    balance = abs(initiator_ratio - (1.0 - initiator_ratio))

    # Leadership score:
    # - 70% from how initiator-heavy they are.
    # - 30% from how question-driven their messages are.
    # Scaled to roughly a 0–20 band to align with classify_level(..., 20).
    style_score = 0.7 * initiator_ratio + 0.3 * question_ratio
    leadership_score = style_score * 20.0

    return {
        "initiator_score": initiator,
        "responder_score": responder,
        "balance_score": balance,
        "leadership_score": leadership_score,
    }