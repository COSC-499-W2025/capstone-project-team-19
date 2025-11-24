from src.analysis.text_collaborative.drive_collaboration.participation import compute_participation
from src.analysis.text_collaborative.drive_collaboration.models import RawUserTextCollabMetrics
import datetime


def make_user(comments, replies, questions, comment_texts, files):
    return RawUserTextCollabMetrics(
        comments_posted=comments,
        replies_posted=replies,
        questions_asked=questions,
        comments_resolved=0,
        comment_texts=comment_texts,
        reply_texts=[],
        comment_timestamps=[],
        reply_timestamps=[],
        files_commented_on=files,
    )


def test_participation_no_activity():
    user = make_user(0, 0, 0, [], [])
    result = compute_participation(user)
    
    assert result["channels_used"] == 0
    assert result["activity_score"] == 0
    assert result["files_engaged"] == 0


def test_participation_single_channel():
    # Comments only
    u1 = make_user(3, 0, 0, ["comment1", "comment2", "comment3"], ["file1"])
    r1 = compute_participation(u1)
    assert r1["channels_used"] == 1
    assert r1["activity_score"] > 0  # 3 * 1.2 * quality_multiplier
    assert r1["files_engaged"] == 1
    
    # Replies only
    u2 = make_user(0, 2, 0, [], ["file1"])
    r2 = compute_participation(u2)
    assert r2["channels_used"] == 1
    assert r2["activity_score"] == 2 * 1.0  # 2.0
    assert r2["files_engaged"] == 1
    
    # Questions only
    u3 = make_user(0, 0, 4, [], ["file1", "file2"])
    r3 = compute_participation(u3)
    assert r3["channels_used"] == 1
    assert r3["activity_score"] == 4 * 1.3  # 5.2
    assert r3["files_engaged"] == 2


def test_participation_multiple_channels():
    user = make_user(
        comments=2,
        replies=3,
        questions=1,
        comment_texts=["This is a good point", "Consider improving this"],
        files=["file1", "file2"]
    )
    
    result = compute_participation(user)
    
    # channels: comments, replies, questions = 3
    assert result["channels_used"] == 3
    assert result["files_engaged"] == 2
    # activity = (2*1.2*quality) + (3*1.0) + (1*1.3)
    assert result["activity_score"] > 0


def test_participation_high_quality_comments_boost():
    """High-quality comments should boost participation score"""
    high_quality = [
        "This section could be improved by adding more examples and clearer explanations.",
        "Consider restructuring this paragraph for better flow and readability.",
    ]
    user = make_user(
        comments=2,
        replies=0,
        questions=0,
        comment_texts=high_quality,
        files=["file1"]
    )
    
    result = compute_participation(user)
    
    # High quality should give multiplier > 1.0
    # Base: 2 * 1.2 = 2.4
    # With quality boost, should be higher
    assert result["activity_score"] > 2.4
    
    # Compare to low quality
    low_quality_user = make_user(
        comments=2,
        replies=0,
        questions=0,
        comment_texts=["ok", "nice"],
        files=["file1"]
    )
    low_result = compute_participation(low_quality_user)
    
    assert result["activity_score"] > low_result["activity_score"]