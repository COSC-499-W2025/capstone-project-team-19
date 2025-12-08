from src.analysis.text_collaborative.drive_collaboration.participation import compute_participation
from src.analysis.text_collaborative.drive_collaboration.models import RawUserTextCollabMetrics, RawTeamTextCollabMetrics
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


def make_team(total_comments, total_replies, total_questions, total_files=1):
    return RawTeamTextCollabMetrics(
        total_comments=total_comments,
        total_replies=total_replies,
        total_questions=total_questions,
        total_files=total_files,
    )


def test_participation_no_activity():
    user = make_user(0, 0, 0, [], [])
    team = make_team(10, 5, 2)  # Team has activity, user doesn't
    result = compute_participation(user, team)
    
    assert result["channels_used"] == 0
    assert result["activity_score"] == 0.0  # 0 / 17 = 0
    assert result["files_engaged"] == 0


def test_participation_no_team_activity():
    """When team has no activity, participation should be 0"""
    user = make_user(3, 2, 1, ["comment1", "comment2", "comment3"], ["file1"])
    team = make_team(0, 0, 0)  # No team activity
    result = compute_participation(user, team)
    
    assert result["channels_used"] == 3
    assert result["activity_score"] == 0.0  # Division by zero protection
    assert result["files_engaged"] == 1


def test_participation_single_channel():
    # Comments only: user has 3 comments, team has 10 total
    u1 = make_user(3, 0, 0, ["comment1", "comment2", "comment3"], ["file1"])
    t1 = make_team(10, 0, 0)  # 10 total comments
    r1 = compute_participation(u1, t1)
    assert r1["channels_used"] == 1
    assert r1["activity_score"] == 3 / 10  # 0.3
    assert r1["files_engaged"] == 1
    
    # Replies only: user has 2 replies, team has 5 total
    u2 = make_user(0, 2, 0, [], ["file1"])
    t2 = make_team(0, 5, 0)  # 5 total replies
    r2 = compute_participation(u2, t2)
    assert r2["channels_used"] == 1
    assert r2["activity_score"] == 2 / 5  # 0.4
    assert r2["files_engaged"] == 1
    
    # Questions only: user has 4 questions, team has 8 total
    u3 = make_user(0, 0, 4, [], ["file1", "file2"])
    t3 = make_team(0, 0, 8)  # 8 total questions
    r3 = compute_participation(u3, t3)
    assert r3["channels_used"] == 1
    assert r3["activity_score"] == 4 / 8  # 0.5
    assert r3["files_engaged"] == 2


def test_participation_multiple_channels():
    # User: 2 comments + 3 replies + 1 question = 6 total
    # Team: 10 comments + 5 replies + 2 questions = 17 total
    user = make_user(
        comments=2,
        replies=3,
        questions=1,
        comment_texts=["This is a good point", "Consider improving this"],
        files=["file1", "file2"]
    )
    team = make_team(10, 5, 2)
    
    result = compute_participation(user, team)
    
    # channels: comments, replies, questions = 3
    assert result["channels_used"] == 3
    assert result["files_engaged"] == 2
    # activity = (2 + 3 + 1) / (10 + 5 + 2) = 6 / 17 ≈ 0.3529
    assert abs(result["activity_score"] - 6 / 17) < 0.0001


def test_participation_independent_of_quality():
    """Participation score should be independent of comment quality"""
    high_quality = [
        "This section could be improved by adding more examples and clearer explanations.",
        "Consider restructuring this paragraph for better flow and readability.",
    ]
    user1 = make_user(
        comments=2,
        replies=0,
        questions=0,
        comment_texts=high_quality,
        files=["file1"]
    )
    team = make_team(10, 0, 0)  # 10 total comments
    
    result = compute_participation(user1, team)
    
    # User: 2 comments, Team: 10 comments = 2/10 = 0.2
    assert result["activity_score"] == 2 / 10  # 0.2
    
    # Low quality should have same participation score (same counts)
    low_quality_user = make_user(
        comments=2,
        replies=0,
        questions=0,
        comment_texts=["ok", "nice"],
        files=["file1"]
    )
    low_result = compute_participation(low_quality_user, team)
    
    # Participation should be the same regardless of quality (same counts)
    assert result["activity_score"] == low_result["activity_score"]


def test_participation_full_contribution():
    """User who made all comments should have participation = 1.0"""
    user = make_user(5, 3, 2, ["comment1", "comment2"], ["file1"])
    team = make_team(5, 3, 2)  # User made all of them
    result = compute_participation(user, team)
    
    # User: 5+3+2=10, Team: 5+3+2=10, ratio = 10/10 = 1.0
    assert result["activity_score"] == 1.0


def test_participation_partial_contribution():
    """User who made half the comments should have participation = 0.5"""
    user = make_user(3, 2, 1, ["comment1"], ["file1"])
    team = make_team(6, 4, 2)  # User made half
    result = compute_participation(user, team)
    
    # User: 3+2+1=6, Team: 6+4+2=12, ratio = 6/12 = 0.5
    assert result["activity_score"] == 0.5