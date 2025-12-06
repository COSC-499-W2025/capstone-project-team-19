PR_REVIEW_QUERY = """
query RepoPRs($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    pullRequests(first: 50, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        number
        createdAt
        author {
          login
        }
        merged

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