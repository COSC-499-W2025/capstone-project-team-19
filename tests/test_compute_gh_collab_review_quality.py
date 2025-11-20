from src.analysis.code_collaborative.github_collaboration.review_quality import compute_review_quality


def test_review_quality_empty():
    result = compute_review_quality([])

    assert result["score"] == 0
    assert result["avg_length"] == 0
    assert result["meaningful_ratio"] == 0
    assert result["total_comments"] == 0


def test_review_quality_short_comments():
    comments = ["ok", "nice", "LGTM", "clean"]
    result = compute_review_quality(comments)

    lengths = [len(c.strip()) for c in comments]
    avg = sum(lengths) / len(lengths)
    meaningful_ratio = 0  # none > 40 chars

    assert result["avg_length"] == avg
    assert result["meaningful_ratio"] == meaningful_ratio
    assert result["total_comments"] == 4
    # score > 0, but small (avg_length/200)
    assert result["score"] > 0
    assert result["score"] <= 5


def test_review_quality_meaningful_comments():
    comments = [
        "This function should be refactored because the loop can be simplified.",
        "Consider renaming this variable to improve clarity.",
        "Add documentation for this class describing its responsibilities.",
    ]

    result = compute_review_quality(comments)

    lengths = [len(c) for c in comments]
    avg = sum(lengths) / len(lengths)
    meaningful_ratio = 1.0  # all > 40 chars

    assert result["avg_length"] == avg
    assert result["meaningful_ratio"] == meaningful_ratio
    assert result["total_comments"] == 3

    # score should be > 2 because meaningful_ratio = 1
    assert result["score"] > 2
    assert result["score"] <= 5


def test_review_quality_mixed_comments():
    comments = [
        "LGTM",
        "You should consider splitting this into two functions for readability.",
        "ok",
        "This block is duplicated—extract into a helper.",
    ]

    result = compute_review_quality(comments)

    lengths = [len(c.strip()) for c in comments]
    avg = sum(lengths) / len(lengths)

    # meaningful = comments > 40 chars
    expected_meaningful = [l for l in lengths if l > 40]
    expected_ratio = len(expected_meaningful) / len(comments)

    assert result["avg_length"] == avg
    assert result["meaningful_ratio"] == expected_ratio
    assert result["total_comments"] == 4
    assert 0 <= result["score"] <= 5
