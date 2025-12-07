from .github_graphql import gh_graphql
from .graphql_queries import PR_REVIEW_QUERY

def fetch_pr_collaboration_graphql(token, owner, repo, username):
    """
    Fetch PR collaboration data via GraphQL.
    
    NOTE: Distinguishes PR comments (regular discussion) from PR reviews
    (formal submissions: approve/comment/request-changes).
    """
    all_prs = []
    cursor = None
    
    # Paginate through all PRs
    while True:
        variables = {
            "owner": owner,
            "repo": repo
        }
        if cursor:
            variables["cursor"] = cursor
        
        data = gh_graphql(token, PR_REVIEW_QUERY, variables)
        
        pr_data = data["repository"]["pullRequests"]
        prs = pr_data["nodes"]
        all_prs.extend(prs)
        
        page_info = pr_data["pageInfo"]
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")

    prs = all_prs

    prs_opened = 0
    prs_reviewed = 0
    review_comments = []
    review_timestamps = []
    pr_timestamps = []

    user_pr_discussion_comments = 0
    team_pr_discussion_comments = 0
    
    user_prs = []
    reviews = {}
    team_total_reviews = 0

    for pr in prs:
        pr_author = pr.get("author", {}).get("login") if pr.get("author") else None
        
        # Collect user PRs for detailed storage
        if pr_author == username:
            prs_opened += 1
            pr_timestamps.append(pr["createdAt"])
            labels = [l.get("name", "") for l in pr.get("labels", {}).get("nodes", [])]
            user_prs.append({
                "number": pr.get("number"),
                "title": pr.get("title", ""),
                "body": pr.get("body", "") or "",
                "labels": labels,
                "created_at": pr.get("createdAt", "").split("T")[0] if pr.get("createdAt") else None,
                "merged_at": pr.get("mergedAt", "").split("T")[0] if pr.get("mergedAt") else None,
                "state": pr.get("state", "").lower(),
                "merged": pr.get("merged", False)
            })
        
        # PR discussion comments
        for c in pr.get("comments", {}).get("nodes", []):
            team_pr_discussion_comments += 1
            if c.get("author", {}).get("login") == username:
                user_pr_discussion_comments += 1

        # Reviews + inline review comments
        pr_number = pr.get("number")
        pr_reviews = []
        pr_review_comments = []
        
        for review in pr.get("reviews", {}).get("nodes", []):
            review_author = review.get("author", {}).get("login") if review.get("author") else None
            
            # Count all reviews for team metrics
            team_total_reviews += 1
            
            if review_author == username:
                prs_reviewed += 1
                pr_reviews.append(review)
                # Only add timestamps for user's reviews
                if review.get("submittedAt"):
                    review_timestamps.append(review["submittedAt"])

            for c in review.get("comments", {}).get("nodes", []):
                if c.get("author", {}).get("login") == username:
                    review_comments.append(c.get("body", ""))
                    pr_review_comments.append(c)
        
        if pr_reviews or pr_review_comments:
            reviews[pr_number] = {
                "reviews": pr_reviews,
                "review_comments": pr_review_comments
            }

    return {
        "prs_opened": prs_opened,
        "prs_reviewed": prs_reviewed,
        "review_comments": review_comments,
        "review_timestamps": review_timestamps,
        "pr_timestamps": pr_timestamps,
        "user_pr_discussion_comments": user_pr_discussion_comments,
        "team_pr_discussion_comments": team_pr_discussion_comments,
        "team_total_prs": len(prs),
        "team_total_reviews": team_total_reviews,
        "user_prs": user_prs,
        "reviews": reviews
    }