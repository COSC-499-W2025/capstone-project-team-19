from src.analysis.text_collaborative.drive_collaboration.communication_leadership import compute_communication_leadership
from src.analysis.text_collaborative.drive_collaboration.models import RawUserTextCollabMetrics
import datetime
import pytest


def make_user(comments, replies, questions):
    return RawUserTextCollabMetrics(
        comments_posted=comments,
        replies_posted=replies,
        questions_asked=questions,
        comments_resolved=0,
        comment_texts=[],
        reply_texts=[],
        comment_timestamps=[],
        reply_timestamps=[],
        files_commented_on=[],
    )


def test_communication_leadership_basic():
    user = make_user(comments=2, replies=3, questions=1)
    result = compute_communication_leadership(user)
    
    # initiator = 2*1.2 + 1*1.4 = 2.4 + 1.4 = 3.8
    # responder = 3 * 1.0 = 3.0
    # balance = |3.8 - 3.0| = 0.8
    # leadership_score = 3.8 + 3.0 = 6.8
    
    assert result["initiator_score"] == 3.8
    assert result["responder_score"] == 3.0
    assert result["balance_score"] == pytest.approx(0.8)
    assert result["leadership_score"] == 6.8


def test_communication_leadership_zero_values():
    user = make_user(0, 0, 0)
    result = compute_communication_leadership(user)
    
    assert result["initiator_score"] == 0
    assert result["responder_score"] == 0
    assert result["balance_score"] == 0
    assert result["leadership_score"] == 0


def test_communication_leadership_high_responder():
    user = make_user(comments=0, replies=10, questions=0)
    result = compute_communication_leadership(user)
    
    assert result["initiator_score"] == 0
    assert result["responder_score"] == 10.0
    assert result["balance_score"] == 10.0
    assert result["leadership_score"] == 10.0


def test_communication_leadership_high_initiator():
    user = make_user(comments=5, replies=1, questions=3)
    result = compute_communication_leadership(user)
    
    # initiator = 5*1.2 + 3*1.4 = 6 + 4.2 = 10.2
    # responder = 1
    # balance = 9.2
    # leadership_score = 11.2
    
    assert result["initiator_score"] == 10.2
    assert result["responder_score"] == 1.0
    assert result["balance_score"] == pytest.approx(9.2)
    assert result["leadership_score"] == 11.2


def test_communication_leadership_questions_weighted_higher():
    """Questions should be weighted higher than regular comments"""
    user1 = make_user(comments=3, replies=0, questions=0)
    user2 = make_user(comments=0, replies=0, questions=3)
    
    r1 = compute_communication_leadership(user1)
    r2 = compute_communication_leadership(user2)
    
    # 3 comments: 3 * 1.2 = 3.6
    # 3 questions: 3 * 1.4 = 4.2
    assert r2["initiator_score"] > r1["initiator_score"]