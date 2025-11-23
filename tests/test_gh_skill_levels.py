import pytest
from src.analysis.code_collaborative.github_collaboration.compute_gh_collaboration_profile import (
    classify_level,
    compute_skill_levels,
)

# Tests for classify_level()
def test_classify_level_beginner():
    assert classify_level(0, 5) == "Beginner"
    assert classify_level(1, 10) == "Beginner"  # ratio = 0.1
    assert classify_level(2.9, 10) == "Beginner"  # ratio = 0.29

def test_classify_level_intermediate():
    # ratio between 0.33 and 0.66
    assert classify_level(0.4 * 10, 10) == "Intermediate"
    assert classify_level(0.5 * 10, 10) == "Intermediate"
    assert classify_level(0.65 * 10, 10) == "Intermediate"

def test_classify_level_advanced():
    # ratio >= 0.66
    assert classify_level(0.66 * 10, 10) == "Advanced"
    assert classify_level(9, 10) == "Advanced"
    assert classify_level(10, 10) == "Advanced"

def test_classify_level_invalid_max():
    # If max_value <= 0 -> always Beginner
    assert classify_level(5, 0) == "Beginner"
    assert classify_level(5, -1) == "Beginner"

# Tests for compute_skill_levels()
def test_compute_skill_levels_basic():
    profile = {
        "skills": {
            "review_quality": {
                "score": 4.0  # /5
            },
            "participation": {
                "activity_score": 10  # /20
            },
            "consistency": {
                "active_weeks": 8,
                "burstiness": 2,
            },
            "leadership": {
                "leadership_score": 15,  # /20
            }
        }
    }

    levels = compute_skill_levels(profile)

    assert levels["review_quality"] == "Advanced" # 4/5 = 0.8
    assert levels["participation"] == "Intermediate" # 10/20 = 0.5
    assert levels["consistency"] == "Intermediate" # (8 - 2) = 6 → 6/12 = 0.5
    assert levels["leadership"] == "Advanced" # 15/20 = 0.75

def test_compute_skill_levels_low_scores():
    profile = {
        "skills": {
            "review_quality": {"score": 0.5}, # Beginner
            "participation": {"activity_score": 1}, # Beginner
            "consistency": {
                "active_weeks": 2,
                "burstiness": 1.5, # score = 0.5 so Beginner
            },
            "leadership": {"leadership_score": 1}, # Beginner
        }
    }

    levels = compute_skill_levels(profile)

    assert levels["review_quality"] == "Beginner"
    assert levels["participation"] == "Beginner"
    assert levels["consistency"] == "Beginner"
    assert levels["leadership"] == "Beginner"

def test_compute_skill_levels_high_scores():
    profile = {
        "skills": {
            "review_quality": {"score": 5},
            "participation": {"activity_score": 20},
            "consistency": {
                "active_weeks": 12,
                "burstiness": 0,
            },
            "leadership": {"leadership_score": 20},
        }
    }

    levels = compute_skill_levels(profile)

    assert all(v == "Advanced" for v in levels.values())
