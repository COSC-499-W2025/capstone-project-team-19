import datetime
from src.analysis.code_collaborative.github_collaboration.consistency import compute_consistency


# helper to make dt(year, week_number)
def ts(week):
    return datetime.datetime.fromisocalendar(2025, week, 1)


def test_consistency_empty():
    result = compute_consistency([], [], [])
    assert result["active_weeks"] == 0
    assert result["burstiness"] == 0
    assert result["weekly_distribution"] == {}


def test_consistency_single_week():
    commits = [ts(5), ts(5), ts(5)]
    prs = []
    reviews = []

    result = compute_consistency(commits, prs, reviews)

    assert result["active_weeks"] == 1
    assert result["weekly_distribution"] == {5: 3}
    assert result["burstiness"] == 0  # all activity in one week → no variance


def test_consistency_multiple_weeks_balanced():
    commits = [ts(10)]
    prs = [ts(11)]
    reviews = [ts(12)]

    result = compute_consistency(commits, prs, reviews)

    assert result["active_weeks"] == 3
    # one event per week → distribution is even → burstiness = 0
    assert result["burstiness"] == 0
    assert result["weekly_distribution"] == {10: 1, 11: 1, 12: 1}


def test_consistency_multiple_weeks_unbalanced():
    # 5 events in week 20, one in week 21
    commits = [ts(20), ts(20), ts(20)]
    prs = [ts(20), ts(21)]
    reviews = [ts(20)]

    result = compute_consistency(commits, prs, reviews)

    assert result["active_weeks"] == 2
    assert result["weekly_distribution"] == {20: 5, 21: 1}

    # avg = (5+1)/2 = 3
    # std = sqrt( ((5-3)^2 + (1-3)^2) / 2 ) = sqrt( (4+4)/2 ) = sqrt(4) = 2
    # burstiness = std/avg = 2/3
    assert round(result["burstiness"], 3) == round(2/3, 3)
