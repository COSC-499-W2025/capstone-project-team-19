# src/summaries/metrics_model.py

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any


@dataclass
class CodeProjectMetrics:
    """
    A unified container for *all* code-project metrics:
    - GitHub REST data
    - Local Git analysis (collaborative or individual)
    - Complexity analysis results
    - Language + framework detection
    - Optional LLM summaries
    """

    project_name: str

    # Project metadata
    classification: Optional[str] = None # "individual" or "collaborative"
    is_collaborative: bool = False # convenience flag

    # GitHub REST API metrics
    github_total_commits: Optional[int] = None
    github_commit_days: Optional[int] = None
    github_first_commit: Optional[str] = None
    github_last_commit: Optional[str] = None
    github_issues_opened: Optional[int] = None
    github_issues_closed: Optional[int] = None
    github_prs_opened: Optional[int] = None
    github_prs_merged: Optional[int] = None
    github_additions: Optional[int] = None
    github_deletions: Optional[int] = None
    github_contribution_percent: Optional[float] = None

    # Local Git metrics (full dict)
    local_git: Optional[Dict[str, Any]] = None

    # Complexity metrics (full dict)
    complexity: Optional[Dict[str, Any]] = None

    # Languages + frameworks detected
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)

    # LLM summaries (only populated if external consent)
    llm_project_summary: Optional[str] = None
    llm_contribution_summary: Optional[str] = None

    # Helper methods
    def add_languages(self, langs: List[str]):
        if langs:
            for lang in langs:
                if lang not in self.languages:
                    self.languages.append(lang)

    def add_frameworks(self, fws: List[str]):
        if fws:
            for fw in fws:
                if fw not in self.frameworks:
                    self.frameworks.append(fw)

    def has_github_data(self) -> bool:
        return self.github_total_commits is not None

    def has_local_git(self) -> bool:
        return bool(self.local_git)

    def has_complexity(self) -> bool:
        return bool(self.complexity)

    def is_individual(self) -> bool:
        return self.classification == "individual"

    def is_collab(self) -> bool:
        return self.classification == "collaborative"


class TextProjectMetrics:
    # TODO: complete this model once all text metrics are completed, for now this is a skeleton and is subject to change
    
    def __init__(self, project_name):
        self.project_name = project_name

        # Identification
        self.classification = None # "individual" or "collaborative"
        self.is_collaborative = False

        # Core text-analysis placeholders (to be filled in later)
        self.summary = None
        self.skills = None
        self.linguistic_features = None

        # CSV / dataset analysis (optional)
        self.csv_results = None

        # Collaborative text (Google Docs) contributions
        self.revision_history = None
