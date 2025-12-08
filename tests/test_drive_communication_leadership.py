from src.analysis.text_collaborative.drive_collaboration.communication_leadership import compute_communication_leadership
from src.analysis.text_collaborative.drive_collaboration.models import RawUserTextCollabMetrics
import datetime
import pytest

#HELPER
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
#TESTS 
def test_communication_leadership_basic():
    user = make_user(comments=2, replies=3, questions=1)
    result = compute_communication_leadership(user)

    assert result["initiator_score"] == 10.0
    assert result["responder_score"] == 1.5
    assert result["leadership_score"] == 11.5


def test_communication_leadership_zero_values():
    user = make_user(0, 0, 0)
    result = compute_communication_leadership(user)
    
    assert result["initiator_score"] == 0
    assert result["responder_score"] == 0
    assert result["leadership_score"] == 0


def test_communication_leadership_high_responder():
    user = make_user(comments=0, replies=10, questions=0)
    result = compute_communication_leadership(user)
    assert result["initiator_score"] == 0
    assert result["responder_score"] == 5.0
    assert result["leadership_score"] == 5.0


def test_communication_leadership_high_initiator():
    user = make_user(comments=5, replies=1, questions=3)
    result = compute_communication_leadership(user)
    assert result["initiator_score"] == 27.0
    assert result["responder_score"] == 0.5
    assert result["leadership_score"] == 27.5


def test_communication_leadership_questions_weighted_higher():
    """Questions should be weighted higher than regular comments"""
    user1 = make_user(comments=3, replies=0, questions=0)
    user2 = make_user(comments=0, replies=0, questions=3)
    r1 = compute_communication_leadership(user1)
    r2 = compute_communication_leadership(user2)
    assert r2["initiator_score"] > r1["initiator_score"]
    assert r2["initiator_score"] == 12.0
    assert r1["initiator_score"] == 9.0