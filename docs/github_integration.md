# GitHub Integration Documentation

This document explains how the system currently interacts with the GitHub REST API to supplement collaborative code analysis with GitHub contribution data.

The integration supports GitHub OAuth login, repository selection, and retrieval and storage of contribution metrics for linked projects.

---

## API Endpoints Used

The following GitHub REST API endpoints are used in this implementation:

| Purpose | Endpoint | Method | Notes |
|--------|---------|--------|-------|
Get authenticated user info | `https://api.github.com/user` | GET | Retrieves GitHub username and account metadata |
List user repositories | `https://api.github.com/user/repos?per_page=200` | GET | Lists repos user can access for linking |
List organization repositories | `https://api.github.com/orgs/{org}/repos?per_page=200` | GET | Includes repos from orgs user belongs to |
Get repository metadata | `https://api.github.com/repos/{owner}/{repo}` | GET | Used to retrieve repo ID and default branch |
Get commit activity by user | `https://api.github.com/repos/{owner}/{repo}/commits?author={username}&per_page=100&page={page}` | GET | Counts commits by user |
Get issues | `https://api.github.com/repos/{owner}/{repo}/issues?state=all&per_page=100&page={page}` | GET | Filters to issues, excluding pull requests |
Get pull requests | `https://api.github.com/repos/{owner}/{repo}/pulls?state=all&per_page=100&page={page}` | GET | Counts opened and merged PRs |
Get contribution stats | `https://api.github.com/repos/{owner}/{repo}/stats/contributors` | GET | Provides commits, additions, deletions; may return 202 while processing |

GitHub's `/stats/contributors` endpoint may return `202 Accepted`. The system retries for a short period before returning a processing state.

---

## Data Stored

Metrics are stored in the local SQLite database as raw JSON for now.

**Table:** `github_repo_metrics`

| Column | Description |
|--------|-------------|
user_id | Local system user ID |
project_name | Name of project in system |
repo_owner | GitHub repository owner |
repo_name | GitHub repository name |
metrics_json | Raw JSON blob containing fetched GitHub metrics |
created_at | Timestamp of storage |

This table ensures one row per user per project per repository.

---

## Authentication Flow

1. User is prompted to enhance analysis with GitHub data
2. If no GitHub token exists, OAuth login is triggered
3. Authenticated GitHub user info is stored locally
4. User selects a repository to link to the project
5. Linked repository owner and name are stored

OAuth scope required:

- `read:user`
- `repo`

The token is stored locally in the application's database and reused until revoked.

---

## Data Retrieved

The following metrics are retrieved and stored:

- Commit activity by date
- Issues opened/closed by user
- Pull requests opened/merged by user
- Total commits, additions, deletions
- Contribution percentage in repo

These metrics are currently stored for future use after parsing and aggregation.

---

## Control Flow Summary

User runs code analysis
- Detect local Git repo
- Prompt user to enable GitHub enhancement
- If enabled:
   - Authenticate (if needed)
   - Retrieve user GitHub identity
   - List and select repository
   - Fetch metrics from GitHub API
   - Store raw metrics JSON
- Continue normal code analysis

If user chooses not to enable GitHub enhancement, analysis runs without GitHub data.

---

## Error Handling

The system handles:

- Invalid/missing token (triggers OAuth)
- Empty repo list
- Repository selection errors
- GitHub stats endpoint processing delay (202 responses)

Errors do not halt analysis; the system falls back cleanly.

---

## References

GitHub REST API Docs:  
https://docs.github.com/en/rest