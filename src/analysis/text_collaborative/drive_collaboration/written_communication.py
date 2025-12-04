from typing import List

def _has_word_diversity(comment: str) -> bool:
    """
    Check if a comment has sufficient word diversity to be considered meaningful.
    Prevents spam like repeated "ok" or single-word repetition.
    
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
    max_word_frequency = max(word_counts.values()) / total_words if total_words > 0 else 0
    
    # If any single word makes up more than 40% of the comment, it's likely spam
    return max_word_frequency <= 0.4


def _is_constructive(comment: str) -> bool:
    """
    Check if comment contains constructive feedback keywords.
    """
    constructive_keywords = [
        "suggest", "consider", "improve", "better", "what if",
        "maybe", "could", "might want to", "perhaps", "instead",
        "alternative", "recommend", "propose", "think about"
    ]
    comment_lower = comment.lower()
    return any(keyword in comment_lower for keyword in constructive_keywords)


def compute_written_communication(comment_texts: List[str]):
    """
    Assess written communication skill through comment analysis:
    - average comment length
    - ratio of meaningful (non-trivial) comments
    - word diversity to prevent spam
    - constructive feedback ratio
    """
    if not comment_texts:
        return {
            "score": 0,
            "avg_length": 0,
            "meaningful_ratio": 0,
            "constructive_ratio": 0,
            "total_comments": 0,
        }

    total_comments = len(comment_texts)
    lengths = [len(c.strip()) for c in comment_texts]

    avg_length = sum(lengths) / total_comments
    
    # 40-character threshold filters out trivial comments like "ok", "thanks", or
    # single-word responses. Additionally, we check word diversity to prevent spam.
    meaningful = [
        l for i, l in enumerate(lengths) 
        if l > 40 and _has_word_diversity(comment_texts[i])
    ]
    meaningful_ratio = len(meaningful) / total_comments if total_comments > 0 else 0
    
    # Constructive feedback ratio
    constructive_count = sum(1 for c in comment_texts if _is_constructive(c))
    constructive_ratio = constructive_count / total_comments if total_comments > 0 else 0

    # Scoring formula: Combines average length (normalized by 200 chars) and meaningful ratio
    raw_score = (avg_length / 200 + meaningful_ratio) / 2
    
    # Boost score if constructive ratio is high
    if constructive_ratio > 0.3:
        raw_score *= 1.2

    # normalize to 0–5
    score = min(max(raw_score * 5, 0), 5)

    return {
        "score": score,
        "avg_length": avg_length,
        "meaningful_ratio": meaningful_ratio,
        "constructive_ratio": constructive_ratio,
        "total_comments": total_comments,
    }

