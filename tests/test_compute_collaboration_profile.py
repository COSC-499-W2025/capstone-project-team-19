import datetime
import pytest
from unittest.mock import patch

from src.analysis.code_collaborative.github_collaboration.compute_gh_collaboration_profile import (
    compute_collaboration_profile,
)
from src.analysis.code_collaborative.github_collaboration.models import (
    RawUserCollabMetrics,
    RawTeamCollabMetrics,
)

# helper: patches all metric functions at once
def patch_all_metrics(
    mock_normalized,
    mock_review_quality,
    mock_participation,
    mock_consistency,
    mock_leadership,
):
    patch_base = "src.analysis.code_collaborative.github_collaboration.compute_gh_collaboration_profile"
    return (
        patch(f"{patch_base}.compute_normalized_contribution", mock_normalized),
        patch(f"{patch_base}.compute_review_quality", mock_review_quality),
        patch(f"{patch_base}.compute_participation", mock_participation),
        patch(f"{patch_base}.compute_consistency", mock_consistency),
        patch(f"{patch_base}.compute_leadership", mock_leadership),
    )

@pytest.fixture
def fake_user():
    return RawUserCollabMetrics(
        commits=10,
        prs_opened=3,
        prs_reviewed=5,
        issues_opened=2,
        issue_comments=4,
        pr_discussion_comments=0,
        review_comments=["Nice work", "Please rename this"],
        additions=120,
        deletions=30,
        commit_timestamps=[datetime.datetime(2025, 1, 1)],
        pr_timestamps=[datetime.datetime(2025, 1, 2)],
        review_timestamps=[datetime.datetime(2025, 1, 3)],
    )

@pytest.fixture
def fake_team():
    return RawTeamCollabMetrics(
        total_commits=50,
        total_prs=25,
        total_reviews=20,
        total_issues=10,
        total_issue_comments=0,
        total_pr_discussion_comments=0,
        total_review_comments=0,
        total_additions=600,
        total_deletions=200,
    )

def test_compute_collaboration_profile_calls_all_metrics(fake_user, fake_team):
    def mock_norm(u, t): return {"commit_share": 0.2}
    def mock_rev(q): return {"score": 3}
    def mock_part(u): return {"channels_used": 3}
    def mock_cons(c, p, r): return {"active_weeks": 2}
    def mock_lead(u): return {"leadership_score": 5}

    patches = patch_all_metrics(
        mock_norm,
        mock_rev,
        mock_part,
        mock_cons,
        mock_lead
    )

    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        result = compute_collaboration_profile(fake_user, fake_team)

        assert result["normalized"] == {"commit_share": 0.2}
        assert result["skills"]["review_quality"] == {"score": 3}
        assert result["skills"]["participation"] == {"channels_used": 3}
        assert result["skills"]["consistency"] == {"active_weeks": 2}
        assert result["skills"]["leadership"] == {"leadership_score": 5}

def test_compute_collaboration_profile_empty():
    empty_user = RawUserCollabMetrics(
        commits=0,
        prs_opened=0,
        prs_reviewed=0,
        issues_opened=0,
        issue_comments=0,
        pr_discussion_comments=0,
        review_comments=[],
        additions=0,
        deletions=0,
        commit_timestamps=[],
        pr_timestamps=[],
        review_timestamps=[],
    )
    empty_team = RawTeamCollabMetrics(
        total_commits=0,
        total_prs=0,
        total_reviews=0,
        total_issues=0,
        total_issue_comments=0,
        total_pr_discussion_comments=0,
        total_review_comments=0,
        total_additions=0,
        total_deletions=0,
    )

    result = compute_collaboration_profile(empty_user, empty_team)
    assert "normalized" in result
    assert "skills" in result

def test_compute_collaboration_profile_integration(fake_user, fake_team, monkeypatch):
    monkeypatch.setattr(
        "src.analysis.code_collaborative.github_collaboration.compute_gh_collaboration_profile.compute_normalized_contribution",
        lambda u, t: {"test": 1},
    )
    monkeypatch.setattr(
        "src.analysis.code_collaborative.github_collaboration.compute_gh_collaboration_profile.compute_review_quality",
        lambda c: {"review": 2},
    )
    monkeypatch.setattr(
        "src.analysis.code_collaborative.github_collaboration.compute_gh_collaboration_profile.compute_participation",
        lambda u: {"part": 3},
    )
    monkeypatch.setattr(
        "src.analysis.code_collaborative.github_collaboration.compute_gh_collaboration_profile.compute_consistency",
        lambda c, p, r: {"cons": 4},
    )
    monkeypatch.setattr(
        "src.analysis.code_collaborative.github_collaboration.compute_gh_collaboration_profile.compute_leadership",
        lambda u: {"lead": 5},
    )

    result = compute_collaboration_profile(fake_user, fake_team)

    assert result["normalized"] == {"test": 1}
    assert result["skills"]["review_quality"] == {"review": 2}
    assert result["skills"]["participation"] == {"part": 3}
    assert result["skills"]["consistency"] == {"cons": 4}
    assert result["skills"]["leadership"] == {"lead": 5}
