def compute_review_quality(review_comments: list[str]):
    """
    Estimate review helpfulness using simple heuristics:
    - average comment length
    - ratio of meaningful (non-trivial) comments
    """

    if not review_comments:
        return {
            "score": 0,
            "avg_length": 0,
            "meaningful_ratio": 0,
            "total_comments": 0,
        }

    total_comments = len(review_comments)
    lengths = [len(c.strip()) for c in review_comments]

    avg_length = sum(lengths) / total_comments
    # 40-character threshold filters out trivial comments like "LGTM", "Looks good", or
    # single-word responses. This helps distinguish substantive feedback from quick approvals.
    meaningful = [l for l in lengths if l > 40]
    meaningful_ratio = len(meaningful) / total_comments

    # Scoring formula: Combines average length (normalized by 200 chars as a reasonable
    # threshold for substantial comments) and meaningful ratio. The average of these two
    # balances both comment depth and consistency of meaningful contributions.
    raw_score = (avg_length / 200 + meaningful_ratio) / 2

    # normalize to 0–5
    score = min(max(raw_score * 5, 0), 5)

    return {
        "score": score,
        "avg_length": avg_length,
        "meaningful_ratio": meaningful_ratio,
        "total_comments": total_comments,
    }
