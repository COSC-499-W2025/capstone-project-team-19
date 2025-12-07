# NOTE: PR comments (pr.comments) are regular discussion messages.
# PR reviews (pr.reviews) are formal submissions (approve/comment/request-changes).
PR_REVIEW_QUERY = """
query RepoPRs($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequests(first: 100, after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        body
        createdAt
        mergedAt
        state
        merged
        author {
          login
        }
        labels(first: 10) {
          nodes {
            name
          }
        }
        comments(first: 50) {
          nodes {
            author {
              login
            }
          }
        }

        reviews(first: 50) {
          nodes {
            author {
              login
            }
            submittedAt
            comments(first: 20) {
              nodes {
                author {
                  login
                }
                body
              }
            }
          }
        }
      }
    }
  }
}
"""