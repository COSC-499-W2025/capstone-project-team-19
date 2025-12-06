from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any


@dataclass
class RawUserCollabMetrics:
    """
    Raw collaboration-related metrics for a single GitHub user.
    Filled by your GitHub REST collector.
    """
    commits: int
    prs_opened: int
    prs_reviewed: int
    issues_opened: int
    issue_comments: int
    pr_discussion_comments: int
    review_comments: List[str]

    additions: int
    deletions: int

    commit_timestamps: List[datetime]
    pr_timestamps: List[datetime]
    review_timestamps: List[datetime]


@dataclass
class RawTeamCollabMetrics:
    """
    Aggregated totals for the entire team.
    Used to compute contribution percentages.
    """
    total_commits: int
    total_prs: int
    total_reviews: int
    total_issues: int
    total_issue_comments: int
    total_pr_discussion_comments: int
    total_review_comments: int
    total_additions: int
    total_deletions: int


@dataclass
class CollaborationProfile:
    """
    A structured return type for your profile.
    Helps with typing, validation, DB storage, and testing.
    """
    normalized: Dict[str, float]
    skills: Dict[str, Any]   # review_quality, participation, consistency, leadership

    def to_json(self) -> Dict[str, Any]:
        """
        Convert the dataclass into a JSON-serializable dict.
        """
        return {
            "normalized": self.normalized,
            "skills": self.skills
        }
