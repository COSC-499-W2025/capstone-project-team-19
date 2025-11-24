import datetime
import pytest
from unittest.mock import patch

from src.analysis.text_collaborative.drive_collaboration.compute_drive_collab_profile import (
    compute_text_collaboration_profile,
)
from src.analysis.text_collaborative.drive_collaboration.models import (
    RawUserTextCollabMetrics,
    RawTeamTextCollabMetrics,
)


def patch_all_metrics(
    mock_comment_quality,
    mock_participation,
    mock_leadership,
):
    patch_base = "src.analysis.text_collaborative.drive_collaboration.compute_drive_collab_profile"
    return (
        patch(f"{patch_base}.compute_comment_quality", mock_comment_quality),
        patch(f"{patch_base}.compute_participation", mock_participation),
        patch(f"{patch_base}.compute_communication_leadership", mock_leadership),
    )


@pytest.fixture
def fake_user():
    return RawUserTextCollabMetrics(
        comments_posted=5,
        replies_posted=3,
        questions_asked=2,
        comments_resolved=1,
        comment_texts=["comment1", "comment2"],
        reply_texts=["reply1"],
        comment_timestamps=[datetime.datetime(2025, 1, 1)],
        reply_timestamps=[datetime.datetime(2025, 1, 2)],
        files_commented_on=["file1", "file2"],
    )


@pytest.fixture
def fake_team():
    return RawTeamTextCollabMetrics(
        total_comments=20,
        total_replies=15,
        total_files=5,
        total_questions=8,
    )


def test_compute_text_collaboration_profile_calls_all_metrics(fake_user, fake_team):
    def mock_quality(c): return {"score": 3}
    def mock_part(u): return {"activity_score": 10}
    def mock_lead(u): return {"leadership_score": 8}

    patches = patch_all_metrics(mock_quality, mock_part, mock_lead)

    with patches[0], patches[1], patches[2]:
        result = compute_text_collaboration_profile(fake_user, fake_team)

        assert "normalized" in result
        assert result["skills"]["comment_quality"] == {"score": 3}
        assert result["skills"]["participation"] == {"activity_score": 10}
        assert result["skills"]["communication_leadership"] == {"leadership_score": 8}


def test_compute_text_collaboration_profile_empty():
    empty_user = RawUserTextCollabMetrics(
        comments_posted=0,
        replies_posted=0,
        questions_asked=0,
        comments_resolved=0,
        comment_texts=[],
        reply_texts=[],
        comment_timestamps=[],
        reply_timestamps=[],
        files_commented_on=[],
    )
    empty_team = RawTeamTextCollabMetrics(
        total_comments=0,
        total_replies=0,
        total_files=0,
        total_questions=0,
    )

    result = compute_text_collaboration_profile(empty_user, empty_team)
    
    assert "normalized" in result
    assert "skills" in result
    assert "comment_quality" in result["skills"]
    assert "participation" in result["skills"]
    assert "communication_leadership" in result["skills"]
    # Should NOT have responsiveness
    assert "responsiveness" not in result["skills"]


def test_compute_text_collaboration_profile_integration(fake_user, fake_team, monkeypatch):
    monkeypatch.setattr(
        "src.analysis.text_collaborative.drive_collaboration.compute_drive_collab_profile.compute_comment_quality",
        lambda c: {"quality": 1},
    )
    monkeypatch.setattr(
        "src.analysis.text_collaborative.drive_collaboration.compute_drive_collab_profile.compute_participation",
        lambda u: {"part": 3},
    )
    monkeypatch.setattr(
        "src.analysis.text_collaborative.drive_collaboration.compute_drive_collab_profile.compute_communication_leadership",
        lambda u: {"lead": 4},
    )

    result = compute_text_collaboration_profile(fake_user, fake_team)

    assert result["skills"]["comment_quality"] == {"quality": 1}
    assert result["skills"]["participation"] == {"part": 3}
    assert result["skills"]["communication_leadership"] == {"lead": 4}