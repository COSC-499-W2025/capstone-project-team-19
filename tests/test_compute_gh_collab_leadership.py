from src.analysis.code_collaborative.github_collaboration.leadership import compute_leadership
from src.analysis.code_collaborative.github_collaboration.models import RawUserCollabMetrics
import datetime
import pytest

def make_user(prs_opened, prs_reviewed, issues_opened):
    return RawUserCollabMetrics(
        commits=0,
        prs_opened=prs_opened,
        prs_reviewed=prs_reviewed,
        issues_opened=issues_opened,
        issue_comments=0,
        review_comments=[],
        additions=0,
        deletions=0,
        commit_timestamps=[],
        pr_timestamps=[],
        review_timestamps=[],
    )


def test_leadership_basic():
    user = make_user(prs_opened=2, prs_reviewed=3, issues_opened=1)
    result = compute_leadership(user)

    # initiator = 2*1.2 + 1*1.4 = 2.4 + 1.4 = 3.8
    # reviewer = 3 * 1.0 = 3
    # balance = |3.8 - 3| = 0.8
    # leadership_score = 3.8 + 3 = 6.8

    assert result["initiator_score"] == 3.8
    assert result["reviewer_score"] == 3
    assert result["balance_score"] == pytest.approx(0.8)
    assert result["leadership_score"] == 6.8


def test_leadership_zero_values():
    user = make_user(0, 0, 0)
    result = compute_leadership(user)

    assert result["initiator_score"] == 0
    assert result["reviewer_score"] == 0
    assert result["balance_score"] == 0
    assert result["leadership_score"] == 0


def test_leadership_high_reviewer_low_initiator():
    user = make_user(prs_opened=0, prs_reviewed=10, issues_opened=0)
    result = compute_leadership(user)

    assert result["initiator_score"] == 0
    assert result["reviewer_score"] == 10
    assert result["balance_score"] == pytest.approx(10)
    assert result["leadership_score"] == 10


def test_leadership_high_initiator_low_reviewer():
    user = make_user(prs_opened=5, prs_reviewed=1, issues_opened=3)
    result = compute_leadership(user)

    # initiator = 5*1.2 + 3*1.4 = 6 + 4.2 = 10.2
    # reviewer = 1
    # balance = 9.2
    # leadership_score = 11.2

    assert result["initiator_score"] == 10.2
    assert result["reviewer_score"] == 1
    assert result["balance_score"] == pytest.approx(9.2)
    assert result["leadership_score"] == 11.2
