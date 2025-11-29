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

    # When this summary was generated
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Optional: reference to DB project ID (useful for Save/Retrieve)
    project_id: Optional[int] = None
