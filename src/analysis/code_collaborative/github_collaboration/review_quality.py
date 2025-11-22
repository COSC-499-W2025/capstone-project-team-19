def _has_word_diversity(comment: str) -> bool:
    """
    Check if a comment has sufficient word diversity to be considered meaningful.
    Prevents spam like repeated "lgtm" or single-word repetition.
    
    Returns True if:
    - Has at least 3 unique words, AND
    - No single word makes up more than 40% of the comment (by word count)
    """
    import re
    from collections import Counter
    
    # Extract words (alphanumeric sequences, case-insensitive)
    words = re.findall(r'\b\w+\b', comment.lower())
    
    if len(words) < 3:
        return False
    
    # Check for excessive repetition of a single word
    word_counts = Counter(words)
    total_words = len(words)
    max_word_frequency = max(word_counts.values()) / total_words
    
    # If any single word makes up more than 40% of the comment, it's likely spam
    return max_word_frequency <= 0.4


def compute_review_quality(review_comments: list[str]):
    """
    Estimate review helpfulness using simple heuristics:
    - average comment length
    - ratio of meaningful (non-trivial) comments
    - word diversity to prevent spam (e.g., repeated "lgtm")
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
    # Additionally, we check word diversity to prevent spam like repeated "lgtm lgtm lgtm..."
    meaningful = [
        l for i, l in enumerate(lengths) 
        if l > 40 and _has_word_diversity(review_comments[i])
    ]
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
