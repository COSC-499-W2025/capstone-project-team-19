import sqlite3
from typing import Any, Dict
import pytest
from src.menu.portfolio import view_portfolio_items

# --- Helpers --------------------------------------------------------------
def _make_basic_summary(
    project_type: str,
    project_mode: str,
    summary_text: str = "Basic summary",
    extra: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    base = {
        "project_type": project_type,
        "project_mode": project_mode,
        "summary_text": summary_text,
        "languages": [],
        "frameworks": [],
        "metrics": {},
        "contributions": {},
        "skills": [],
    }
    if extra:
        base.update(extra)
    return base

@pytest.fixture
def conn():
    """Dummy sqlite connection (schema is initialized by app code)."""
    return sqlite3.connect(":memory:")


# --- 1) No projects at all -----------------------------------------------
def test_portfolio_no_projects(monkeypatch, conn, capsys):
    def fake_collect_project_data(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "src.menu.portfolio.collect_project_data",
        fake_collect_project_data,
        raising=False,
    )

    view_portfolio_items(conn, user_id=1, username="Salma")
    out = capsys.readouterr().out

    assert "No projects found. Please analyze some projects first." in out
    assert "[1]" not in out


# --- 2) Single project – basic happy path ---------------------------------
def test_portfolio_single_project_basic(monkeypatch, conn, capsys):
    def fake_collect_project_data(*args, **kwargs):
        # [(project_name, score)]
        return [("proj1", 0.8)]

    def fake_get_project_summary_row(*args, **kwargs):
        # Extract project_name from kwargs or args
        if "project_name" in kwargs:
            project_name = kwargs["project_name"]
        elif len(args) >= 3:
            project_name = args[2]
        else:
            raise AssertionError("project_name not provided")

        assert project_name == "proj1"

        summary = _make_basic_summary(
            project_type="code",
            project_mode="individual",
            summary_text="A simple code project.",
            extra={
                "languages": ["Python 100%"],
                "frameworks": ["pytest"],
                "metrics": {
                    "skills_detailed": [
                        {"skill_name": "testing_and_ci", "score": 0.8},
                    ]
                },
            },
        )
        return {
            "project_summary_id": 1,
            "user_id": 1,
            "project_name": "proj1",
            "project_type": "code",
            "project_mode": "individual",
            "created_at": "2025-11-30 10:00:00",
            "summary_json": "{}",
            "summary": summary,
        }

    def fake_get_code_activity_percentages(*args, **kwargs):
        project_name = kwargs.get("project_name") or (
            len(args) >= 3 and args[2] or None
        )
        scope = kwargs.get("scope")
        source = kwargs.get("source")
        assert project_name == "proj1"
        assert scope in (None, "individual", "collaborative")
        # We only care that this returns something non-empty
        return [("feature_coding", 90.0), ("testing", 10.0)]

    # Patch
    monkeypatch.setattr(
        "src.menu.portfolio.collect_project_data",
        fake_collect_project_data,
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_project_summary_row",
        fake_get_project_summary_row,
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_code_activity_percentages",
        fake_get_code_activity_percentages,
        raising=False,
    )
    # Duration helpers: not needed for individual code, but patch to avoid surprises
    monkeypatch.setattr(
        "src.menu.portfolio.get_code_collaborative_duration",
        lambda *args, **kwargs: None,
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_text_duration",
        lambda *args, **kwargs: None,
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_code_collaborative_non_llm_summary",
        lambda *args, **kwargs: None,
        raising=False,
    )

    view_portfolio_items(conn, user_id=1, username="Salma")
    out = capsys.readouterr().out

    # Header + basic info
    assert "[1] proj1" in out
    assert "Score 0.800" in out
    assert "Type: code (individual)" in out

    # Just check that a Duration line exists (do not assume exact format)
    assert "Duration:" in out

    # Code-specific fields
    assert "Languages: Python 100%" in out
    assert "Frameworks: pytest" in out

    # Activity from DB helper
    assert "Activity:" in out
    assert "feature_coding" in out

    # Skills
    assert "Skills:" in out
    assert "- testing_and_ci" in out

    # Summary
    assert "Summary:" in out
    assert "A simple code project." in out


# --- 3) Multiple projects – order + code/text formatting ------------------
def test_portfolio_multiple_projects_order_and_format(monkeypatch, conn, capsys):
    def fake_collect_project_data(*args, **kwargs):
        # Already ranked: ProjA first, then ProjB
        return [("ProjA", 0.9), ("ProjB", 0.6)]

    def fake_get_project_summary_row(*args, **kwargs):
        if "project_name" in kwargs:
            project_name = kwargs["project_name"]
        elif len(args) >= 3:
            project_name = args[2]
        else:
            raise AssertionError("project_name not provided")

        if project_name == "ProjA":
            # code collaborative
            summary = _make_basic_summary(
                "code",
                "collaborative",
                summary_text="Code collab project.",
                extra={
                    "languages": ["Python 70%", "SQL 30%"],
                    "frameworks": ["FastAPI"],
                    "metrics": {
                        "skills_detailed": [
                            {"skill_name": "architecture_and_design", "score": 0.7}
                        ]
                    },
                },
            )
            return {
                "project_summary_id": 1,
                "user_id": 1,
                "project_name": "ProjA",
                "project_type": "code",
                "project_mode": "collaborative",
                "created_at": "2025-11-01 09:00:00",
                "summary_json": "{}",
                "summary": summary,
            }
        elif project_name == "ProjB":
            # text individual
            summary = _make_basic_summary(
                "text",
                "individual",
                summary_text="Text individual project.",
                extra={
                    "metrics": {
                        "activity_type": {
                            "Drafting": {"count": 2, "top_file": None},
                            "Final": {"count": 1, "top_file": None},
                        },
                        "skills_detailed": [
                            {"skill_name": "clarity", "score": 0.5}
                        ],
                    },
                },
            )
            return {
                "project_summary_id": 2,
                "user_id": 1,
                "project_name": "ProjB",
                "project_type": "text",
                "project_mode": "individual",
                "created_at": "2025-10-20 09:00:00",
                "summary_json": "{}",
                "summary": summary,
            }
        raise AssertionError(f"Unexpected project_name {project_name}")

    def fake_get_code_activity_percentages(*args, **kwargs):
        project_name = kwargs.get("project_name") or (len(args) >= 3 and args[2] or None)
        if project_name == "ProjA":
            return [("feature_coding", 80.0), ("testing", 20.0)]
        return []

    def fake_get_text_duration(*args, **kwargs):
        project_name = kwargs.get("project_name") or (len(args) >= 3 and args[2] or None)
        if project_name == "ProjB":
            return ("2025-10-01", "2025-10-15")
        return None

    monkeypatch.setattr(
        "src.menu.portfolio.collect_project_data",
        fake_collect_project_data,
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_project_summary_row",
        fake_get_project_summary_row,
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_code_activity_percentages",
        fake_get_code_activity_percentages,
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_code_collaborative_duration",
        lambda *args, **kwargs: ("2025-11-01", "2025-11-10"),
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_text_duration",
        fake_get_text_duration,
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_code_collaborative_non_llm_summary",
        lambda *args, **kwargs: None,
        raising=False,
    )

    view_portfolio_items(conn, user_id=1, username="Salma")
    out = capsys.readouterr().out

    # Order + score presence
    assert "[1] ProjA" in out
    assert "Score 0.900" in out
    assert "[2] ProjB" in out
    assert "Score 0.600" in out

    # Code project should have Languages/Frameworks
    assert "Languages: Python 70%, SQL 30%" in out
    assert "Frameworks: FastAPI" in out

    # Text project should NOT have Languages/Frameworks
    # We expect only one Languages/Frameworks (for ProjA)
    assert out.count("Languages:") == 1
    assert out.count("Frameworks:") == 1

    # Duration for text project via text_activity_contribution
    assert "Duration: 2025-10-01 – 2025-10-15" in out

    # Activity for code from DB
    assert "Activity: feature_coding 80%, testing 20%" in out

    # Activity for text from JSON (Drafting vs Final)
    # total = 3 → Drafting 67%, Final 33% (rounded)
    assert "Activity: Drafting 67%, Final 33%" in out


# --- 4) Missing optional data ---------------------------------------------
def test_portfolio_handles_missing_optional_data(monkeypatch, conn, capsys):
    def fake_collect_project_data(*args, **kwargs):
        return [("BareProj", 0.5)]

    def fake_get_project_summary_row(*args, **kwargs):
        if "project_name" in kwargs:
            project_name = kwargs["project_name"]
        elif len(args) >= 3:
            project_name = args[2]
        else:
            raise AssertionError("project_name not provided")

        assert project_name == "BareProj"

        summary = {
            "project_type": "code",
            "project_mode": "individual",
            "summary_text": "",
            "languages": [],
            "frameworks": [],
            "metrics": {},        # no skills_detailed
            "contributions": {},  # no activity
            "skills": [],         # no skills
        }
        return {
            "project_summary_id": 1,
            "user_id": 1,
            "project_name": "BareProj",
            "project_type": "code",
            "project_mode": "individual",
            "created_at": "",  # no created_at fallback
            "summary_json": "{}",
            "summary": summary,
        }

    monkeypatch.setattr(
        "src.menu.portfolio.collect_project_data",
        fake_collect_project_data,
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_project_summary_row",
        fake_get_project_summary_row,
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_code_activity_percentages",
        lambda *args, **kwargs: [],
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_code_collaborative_duration",
        lambda *args, **kwargs: None,
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_text_duration",
        lambda *args, **kwargs: None,
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_code_collaborative_non_llm_summary",
        lambda *args, **kwargs: None,
        raising=False,
    )

    view_portfolio_items(conn, user_id=1, username="Salma")
    out = capsys.readouterr().out

    assert "[1] BareProj" in out
    assert "Score 0.500" in out

    assert "Duration: N/A" in out
    assert "Activity: N/A" in out
    assert "Skills: N/A" in out
    assert "Summary:" in out  # still prints a summary line


# --- 5) Summary variants: LLM, non-LLM, missing ---------------------------
def test_portfolio_summary_variants(monkeypatch, conn, capsys):
    def fake_collect_project_data(*args, **kwargs):
        return [
            ("LLMProj", 0.9),
            ("NonLLMProj", 0.8),
            ("NoSummaryProj", 0.7),
        ]

    def fake_get_project_summary_row(*args, **kwargs):
        if "project_name" in kwargs:
            project_name = kwargs["project_name"]
        elif len(args) >= 3:
            project_name = args[2]
        else:
            raise AssertionError("project_name not provided")

        if project_name == "LLMProj":
            # Code project with LLM contribution summary
            summary = _make_basic_summary(
                "code",
                "individual",
                summary_text="LLM-style project summary.",
                extra={
                    "contributions": {
                        "llm_contribution_summary": "I built the main pipeline."
                    }
                },
            )
            return {
                "project_summary_id": 1,
                "user_id": 1,
                "project_name": "LLMProj",
                "project_type": "code",
                "project_mode": "individual",
                "created_at": "2025-11-01 00:00:00",
                "summary_json": "{}",
                "summary": summary,
            }

        if project_name == "NonLLMProj":
            # Collaborative code with non-LLM summary from DB
            summary = _make_basic_summary(
                "code",
                "collaborative",
                summary_text="Non-LLM project summary.",
            )
            return {
                "project_summary_id": 2,
                "user_id": 1,
                "project_name": "NonLLMProj",
                "project_type": "code",
                "project_mode": "collaborative",
                "created_at": "2025-11-02 00:00:00",
                "summary_json": "{}",
                "summary": summary,
            }

        if project_name == "NoSummaryProj":
            # Missing summary_text and no LLM / non-LLM
            summary = _make_basic_summary(
                "code",
                "individual",
                summary_text="",
            )
            return {
                "project_summary_id": 3,
                "user_id": 1,
                "project_name": "NoSummaryProj",
                "project_type": "code",
                "project_mode": "individual",
                "created_at": "2025-11-03 00:00:00",
                "summary_json": "{}",
                "summary": summary,
            }

        raise AssertionError(f"Unexpected project_name {project_name}")

    def fake_get_code_collaborative_non_llm_summary(*args, **kwargs):
        project_name = kwargs.get("project_name") or (len(args) >= 3 and args[2] or None)
        if project_name == "NonLLMProj":
            return "Manual non-LLM contribution summary."
        return None

    def fake_get_code_activity_percentages(*args, **kwargs):
        # Not important for this test; just avoid Activity: N/A everywhere
        return [("feature_coding", 100.0)]

    monkeypatch.setattr(
        "src.menu.portfolio.collect_project_data",
        fake_collect_project_data,
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_project_summary_row",
        fake_get_project_summary_row,
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_code_collaborative_non_llm_summary",
        fake_get_code_collaborative_non_llm_summary,
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_code_activity_percentages",
        fake_get_code_activity_percentages,
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_code_collaborative_duration",
        lambda *args, **kwargs: None,
        raising=False,
    )
    monkeypatch.setattr(
        "src.menu.portfolio.get_text_duration",
        lambda *args, **kwargs: None,
        raising=False,
    )

    view_portfolio_items(conn, user_id=1, username="Salma")
    out = capsys.readouterr().out

    # 1) LLM project: should show project + contribution bullets
    assert "[1] LLMProj" in out
    assert "Summary:" in out
    assert "Project: LLM-style project summary." in out
    assert "My contribution: I built the main pipeline." in out

    # 2) Non-LLM project: Summary line from code_collaborative_summary helper
    assert "[2] NonLLMProj" in out
    assert "Summary: Manual non-LLM contribution summary." in out

    # 3) NoSummaryProj: still a Summary line, but no LLM/non-LLM details
    assert "[3] NoSummaryProj" in out
    assert "Summary:" in out
