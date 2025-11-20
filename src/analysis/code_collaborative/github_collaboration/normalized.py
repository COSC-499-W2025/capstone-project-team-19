from .models import RawUserCollabMetrics, RawTeamCollabMetrics

def compute_normalized_contribution(user: RawUserCollabMetrics, team: RawTeamCollabMetrics):
    """
    Compute relative contribution shares across different activity types.
    """

    # handle divide-by-zero gracefully
    def ratio(x, total):
        return x / total if total > 0 else 0

    commit_share = ratio(user.commits, team.total_commits)
    pr_share = ratio(user.prs_opened, team.total_prs)
    review_share = ratio(user.prs_reviewed, team.total_reviews)
    issue_share = ratio(user.issues_opened, team.total_issues)
    addition_share = ratio(user.additions, team.total_additions)
    deletion_share = ratio(user.deletions, team.total_deletions)

    shares = {
        "commits": commit_share,
        "prs": pr_share,
        "reviews": review_share,
        "issues": issue_share,
        "additions": addition_share,
        "deletions": deletion_share,
    }

    # Identify main type of contribution (where the user contributes the most)
    dominant_activity = max(
        ["commits", "prs", "reviews", "issues"],
        key=lambda k: shares[k]
    )

    # A combined contribution score
    total_behavior_score = (
        commit_share + pr_share + review_share + issue_share
    )

    return {
        "commit_share": commit_share,
        "pr_share": pr_share,
        "review_share": review_share,
        "issue_share": issue_share,
        "addition_share": addition_share,
        "deletion_share": deletion_share,
        "dominant_activity": dominant_activity,
        "total_behavior_score": total_behavior_score,
    }
