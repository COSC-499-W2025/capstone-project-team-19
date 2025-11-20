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
    meaningful = [l for l in lengths if l > 40]  # NOT nitpicks or “LGTM”
    meaningful_ratio = len(meaningful) / total_comments

    # Construct a score out of two signals
    raw_score = (avg_length / 200 + meaningful_ratio) / 2

    # normalize to 0–5
    score = min(max(raw_score * 5, 0), 5)

    return {
        "score": score,
        "avg_length": avg_length,
        "meaningful_ratio": meaningful_ratio,
        "total_comments": total_comments,
    }
