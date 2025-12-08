from .models import RawUserTextCollabMetrics


def compute_communication_leadership(user: RawUserTextCollabMetrics):
    """
    Communication leadership is calculated using a weighted sum approach:
    - Comments and questions (initiative) get high weight
    - Replies get lower weight
    
    Leadership score is the weighted sum, where high scores indicate leadership.
    """
    comments = user.comments_posted
    replies = user.replies_posted
    questions = user.questions_asked

    # If there is no activity at all, everything is zero.
    if comments == 0 and replies == 0 and questions == 0:
        return {
            "initiator_score": 0.0,
            "responder_score": 0.0,
            "leadership_score": 0.0,
        }

    # High weight on comments and questions (initiative/leadership activities)
    # Questions get slightly higher weight than comments as they drive discussion
    initiator_score = comments * 3.0 + questions * 4.0

    # Lower weight on replies (reactive rather than proactive)
    responder_score = replies * 0.5

    # Leadership score is the weighted sum
    leadership_score = initiator_score + responder_score

    return {
        "initiator_score": initiator_score,
        "responder_score": responder_score,
        "leadership_score": leadership_score,
    }