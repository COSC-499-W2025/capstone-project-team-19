from collections import Counter
from datetime import datetime

def compute_consistency(commit_ts, pr_ts, review_ts):
    """
    Measures how consistent the user is:
    - number of active weeks
    - burstiness based on weekly counts
    """

    all_ts = sorted(commit_ts + pr_ts + review_ts)
    if not all_ts:
        return {
            "active_weeks": 0,
            "burstiness": 0,
            "weekly_distribution": {},
        }

    weeks = [ts.isocalendar()[1] for ts in all_ts]
    week_counts = Counter(weeks)

    counts = list(week_counts.values())
    avg = sum(counts) / len(counts)
    std = (sum((c - avg) ** 2 for c in counts) / len(counts)) ** 0.5 if avg > 0 else 0

    burstiness = std / avg if avg > 0 else 0

    return {
        "active_weeks": len(week_counts),
        "burstiness": burstiness,
        "weekly_distribution": dict(week_counts),
    }
