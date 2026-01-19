from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict, Literal
from datetime import datetime, UTC

@dataclass
class ProjectSummary:
    # Basic identification
    project_name: str
    project_type: Literal["code", "text"]
    project_mode: Literal["individual", "collaborative"]

    # Static properties
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)

    # Dynamic analysis results
    summary_text: Optional[str] = None
    skills: List[str] = field(default_factory=list)

    # Metrics: code metrics, text metrics, git metrics, readability metrics, etc.
    metrics: Dict[str, Any] = field(default_factory=dict)

    # Contributions for collaborative projects
    contributions: Dict[str, Any] = field(default_factory=dict)

    # Optional: manual wording overrides shared by resume + portfolio
    manual_overrides: Dict[str, Any] = field(default_factory=dict)

    # When this summary was generated
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Optional: reference to DB project ID (useful for Save/Retrieve)
    project_id: Optional[int] = None

    @staticmethod
    def from_dict(data: dict) -> "ProjectSummary":
        return ProjectSummary(
            project_name = data["project_name"],
            project_type = data["project_type"],
            project_mode = data["project_mode"],
            languages = data.get("languages", []),
            frameworks = data.get("frameworks", []),
            summary_text = data.get("summary_text"),
            skills = data.get("skills", []),
            metrics = data.get("metrics", {}),
            contributions = data.get("contributions", {}),
            manual_overrides = data.get("manual_overrides", {}) or {},
            created_at = datetime.fromisoformat(data["created_at"])
                if isinstance(data.get("created_at"), str)
                else data.get("created_at", datetime.now(UTC)),
            project_id = data.get("project_id")
        )
