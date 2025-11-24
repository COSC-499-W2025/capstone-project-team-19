from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any


@dataclass
class RawUserTextCollabMetrics:
    """
    Raw collaboration-related metrics for a single user in text projects.
    Filled by Google Drive API collector.
    """
    comments_posted: int
    replies_posted: int
    questions_asked: int
    comments_resolved: int
    
    comment_texts: List[str]  # all comment bodies
    reply_texts: List[str]     # all reply bodies
    
    comment_timestamps: List[datetime]
    reply_timestamps: List[datetime]
    files_commented_on: List[str]  # file_ids


@dataclass
class RawTeamTextCollabMetrics:
    """
    Aggregated totals for the entire team.
    Used to compute contribution percentages.
    """
    total_comments: int
    total_replies: int
    total_files: int
    total_questions: int


@dataclass
class TextCollaborationProfile:
    """
    A structured return type for text collaboration profile.
    """
    normalized: Dict[str, float]
    skills: Dict[str, Any]  # comment_quality, participation, communication_leadership

    def to_json(self) -> Dict[str, Any]:
        """
        Convert the dataclass into a JSON-serializable dict.
        """
        return {
            "normalized": self.normalized,
            "skills": self.skills
        }