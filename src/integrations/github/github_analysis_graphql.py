from .github_graphql import gh_graphql
from .graphql_queries import PR_REVIEW_QUERY

def fetch_pr_collaboration_graphql(token, owner, repo, username):
    data = gh_graphql(
        token,
        PR_REVIEW_QUERY,
        {
            "owner": owner,
            "repo": repo
        }
    )

    prs = data["repository"]["pullRequests"]["nodes"]

    prs_opened = 0
    prs_reviewed = 0
    review_comments = []
    review_timestamps = []
    pr_timestamps = []

    user_pr_discussion_comments = 0
    team_pr_discussion_comments = 0

    for pr in prs:
        if pr["author"] and pr["author"]["login"] == username:
            prs_opened += 1
            pr_timestamps.append(pr["createdAt"])

        # PR discussion comments
        for c in pr["comments"]["nodes"]:
            team_pr_discussion_comments += 1
            if c["author"] and c["author"]["login"] == username:
                user_pr_discussion_comments += 1

        # Reviews + inline review comments
        for review in pr["reviews"]["nodes"]:
            if review["author"] and review["author"]["login"] == username:
                prs_reviewed += 1

            if review["submittedAt"]:
                review_timestamps.append(review["submittedAt"])

            for c in review["comments"]["nodes"]:
                if c["author"] and c["author"]["login"] == username:
                    review_comments.append(c["body"])

    return {
        "prs_opened": prs_opened,
        "prs_reviewed": prs_reviewed,
        "review_comments": review_comments,
        "review_timestamps": review_timestamps,
        "pr_timestamps": pr_timestamps,
        "user_pr_discussion_comments": user_pr_discussion_comments,
        "team_pr_discussion_comments": team_pr_discussion_comments,
        "team_total_prs": len(prs)
    }