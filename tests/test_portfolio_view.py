import json
import sqlite3
import pytest
from src.db import get_project_summary_by_name, init_schema, save_project_summary
from src.menu.portfolio import _handle_edit_portfolio_wording, _display_portfolio, view_portfolio_menu


def _make_portfolio_summary(
    project_name: str,
    project_type: str = "code",
    project_mode: str = "individual",
    summary_text: str | None = None,
) -> str:
    return json.dumps(
        {
            "project_name": project_name,
            "project_type": project_type,
            "project_mode": project_mode,
            "languages": [],
            "frameworks": [],
            "summary_text": summary_text or f"{project_name} summary",
            "skills": [],
            "metrics": {},
            "contributions": {},
        }
    )


@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    return conn


@pytest.fixture(autouse=True)
def stub_portfolio_db_helpers(monkeypatch):
    """
    Keep portfolio tests small by stubbing all the "extra" data sources once.

    These functions normally pull from other tables (git metrics, activity, etc.),
    but for high-level menu tests we just want them to return something sensible.
    """
    mp = monkeypatch.setattr

    # Activity: always say 100% feature_coding for any project
    mp(
        "src.insights.portfolio.formatters.get_code_activity_percentages",
        lambda *a, **k: [("feature_coding", 100.0)],
        raising=False,
    )

    # Durations: return a dummy date range for any project/mode
    mp(
        "src.insights.portfolio.formatters.get_text_duration",
        lambda *a, **k: ("2025-01-01", "2025-01-31"),
        raising=False,
    )
    mp(
        "src.insights.portfolio.formatters.get_code_collaborative_duration",
        lambda *a, **k: ("2025-02-01", "2025-02-28"),
        raising=False,
    )
    mp(
        "src.insights.portfolio.formatters.get_code_individual_duration",
        lambda *a, **k: ("2025-03-01", "2025-03-31"),
        raising=False,
    )

    # Non-LLM summary: default to None unless overridden in a specific test
    mp(
        "src.insights.portfolio.formatters.get_code_collaborative_non_llm_summary",
        lambda *a, **k: None,
        raising=False,
    )


def test_portfolio_no_projects(conn, capsys, monkeypatch):
    monkeypatch.setattr(
        "src.services.portfolio_service.collect_project_data",
        lambda *_: [],
        raising=False,
    )

    _display_portfolio(conn, user_id=1, username="Kevin")
    out = capsys.readouterr().out

    assert "No projects found" in out
    assert "[1]" not in out


def test_portfolio_single_basic_project(conn, capsys, monkeypatch):
    user_id = 1
    save_project_summary(conn, user_id, "proj1", _make_portfolio_summary("proj1"))

    monkeypatch.setattr(
        "src.services.portfolio_service.collect_project_data",
        lambda c, uid: [("proj1", 0.8)],
        raising=False,
    )

    _display_portfolio(conn, user_id, "Kevin")
    out = capsys.readouterr().out

    assert "[1] proj1" in out
    assert "Score 0.800" in out
    assert "Type: code (individual)" in out

    # Comes from the stubbed duration helpers
    assert "Duration:" in out

    # Stubbed activity helper
    assert "Activity: feature_coding 100%" in out

    # Summary from project_summaries JSON
    assert "Summary: proj1 summary" in out


def test_portfolio_multiple_projects_order(conn, capsys, monkeypatch):
    user_id = 1
    for name in ["A", "B", "C"]:
        save_project_summary(conn, user_id, name, _make_portfolio_summary(name))

    # Ranking: C > B > A
    monkeypatch.setattr(
        "src.services.portfolio_service.collect_project_data",
        lambda c, uid: [("C", 0.9), ("B", 0.8), ("A", 0.7)],
        raising=False,
    )

    _display_portfolio(conn, user_id, "Kevin")
    out = capsys.readouterr().out

    assert "[1] C" in out
    assert "[2] B" in out
    assert "[3] A" in out
    assert "Score 0.900" in out

def test_portfolio_missing_fields(conn, capsys, monkeypatch):
    save_project_summary(conn, 1, "Bare", json.dumps({}))   # totally empty summary JSON

    monkeypatch.setattr(
        "src.services.portfolio_service.collect_project_data",
        lambda *_: [("Bare", 0.5)],
        raising=False,
    )

    _display_portfolio(conn, 1, "Kevin")
    out = capsys.readouterr().out

    assert "[1] Bare" in out
    assert "Duration:" in out
    assert "Activity:" in out
    assert "Summary:" in out        


def test_portfolio_prefers_manual_contribution_for_collab_code(conn, capsys, monkeypatch):
    user_id = 1
    summary = {
        "project_name": "proj1",
        "project_type": "code",
        "project_mode": "collaborative",
        "languages": [],
        "frameworks": [],
        "summary_text": "LLM project summary",
        "skills": [],
        "metrics": {},
        "contributions": {
            "manual_contribution_summary": "Manual contribution summary",
            "llm_contribution_summary": "LLM contribution summary"
        },
    }
    save_project_summary(conn, user_id, "proj1", json.dumps(summary))

    monkeypatch.setattr(
        "src.services.portfolio_service.collect_project_data",
        lambda c, uid: [("proj1", 0.8)],
        raising=False,
    )

    _display_portfolio(conn, user_id, "Kevin")
    out = capsys.readouterr().out

    assert "Project: LLM project summary" in out
    assert "My contribution: Manual contribution summary" in out
    assert "LLM contribution summary" not in out


def test_portfolio_uses_manual_overrides(conn, capsys, monkeypatch):
    user_id = 1
    summary = {
        "project_name": "proj1",
        "project_type": "code",
        "project_mode": "individual",
        "languages": [],
        "frameworks": [],
        "summary_text": "Original summary",
        "skills": [],
        "metrics": {},
        "contributions": {
            "manual_contribution_summary": "Should be ignored",
        },
        "manual_overrides": {
            "display_name": "Manual Name",
            "summary_text": "Manual summary",
            "contribution_bullets": ["Did X", "Did Y"],
        },
    }
    save_project_summary(conn, user_id, "proj1", json.dumps(summary))

    monkeypatch.setattr(
        "src.services.portfolio_service.collect_project_data",
        lambda c, uid: [("proj1", 0.8)],
        raising=False,
    )
    monkeypatch.setattr("builtins.input", lambda _: "n")

    _display_portfolio(conn, user_id, "Kevin")
    out = capsys.readouterr().out

    assert "[1] Manual Name" in out
    assert "Project: Manual summary" in out
    assert "My contributions:" in out
    assert "- Did X" in out
    assert "- Did Y" in out
    assert "Original summary" not in out


def test_portfolio_portfolio_overrides_take_priority(conn, capsys, monkeypatch):
    user_id = 1
    summary = {
        "project_name": "proj1",
        "project_type": "code",
        "project_mode": "individual",
        "languages": [],
        "frameworks": [],
        "summary_text": "Original summary",
        "skills": [],
        "metrics": {},
        "contributions": {},
        "manual_overrides": {
            "display_name": "Manual Name",
            "summary_text": "Manual summary",
            "contribution_bullets": ["Manual X"],
        },
        "portfolio_overrides": {
            "display_name": "Portfolio Name",
            "summary_text": "Portfolio summary",
            "contribution_bullets": ["Portfolio A", "Portfolio B"],
        },
    }
    save_project_summary(conn, user_id, "proj1", json.dumps(summary))

    monkeypatch.setattr(
        "src.services.portfolio_service.collect_project_data",
        lambda c, uid: [("proj1", 0.8)],
        raising=False,
    )

    _display_portfolio(conn, user_id, "Kevin")
    out = capsys.readouterr().out

    assert "[1] Portfolio Name" in out
    assert "Project: Portfolio summary" in out
    assert "My contributions:" in out
    assert "- Portfolio A" in out
    assert "- Portfolio B" in out
    assert "Manual summary" not in out


def test_portfolio_edit_portfolio_only_updates_overrides(conn, monkeypatch):
    user_id = 1
    summary = {
        "project_name": "proj1",
        "project_type": "text",
        "project_mode": "individual",
        "summary_text": "Original summary",
        "skills": [],
        "metrics": {},
        "contributions": {},
    }
    save_project_summary(conn, user_id, "proj1", json.dumps(summary))

    monkeypatch.setattr(
        "src.services.portfolio_service.collect_project_data",
        lambda c, uid: [("proj1", 0.8)],
        raising=False,
    )

    inputs = iter(["1", "1", "1", "Updated summary"])
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))

    assert _handle_edit_portfolio_wording(conn, user_id, "Kevin") is True

    row = get_project_summary_by_name(conn, user_id, "proj1")
    summary_dict = json.loads(row["summary_json"])
    assert summary_dict["portfolio_overrides"]["summary_text"] == "Updated summary"


def test_portfolio_edit_global_updates_manual_overrides(conn, monkeypatch):
    user_id = 1
    summary = {
        "project_name": "proj1",
        "project_type": "text",
        "project_mode": "individual",
        "summary_text": "Original summary",
        "skills": [],
        "metrics": {},
        "contributions": {},
    }
    save_project_summary(conn, user_id, "proj1", json.dumps(summary))

    monkeypatch.setattr(
        "src.services.portfolio_service.collect_project_data",
        lambda c, uid: [("proj1", 0.8)],
        raising=False,
    )

    called = {"applied": False}

    def _fake_apply(*args, **kwargs):
        called["applied"] = True

    monkeypatch.setattr("src.services.resume_overrides.apply_manual_overrides_to_resumes", _fake_apply)

    inputs = iter(["1", "2", "1", "Global summary"])
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))

    assert _handle_edit_portfolio_wording(conn, user_id, "Kevin") is True
    assert called["applied"] is True

    row = get_project_summary_by_name(conn, user_id, "proj1")
    summary_dict = json.loads(row["summary_json"])
    assert summary_dict["manual_overrides"]["summary_text"] == "Global summary"


def test_portfolio_edit_cancel_selection_is_noop(conn, monkeypatch):
    user_id = 1
    summary = {
        "project_name": "proj1",
        "project_type": "text",
        "project_mode": "individual",
        "summary_text": "Original summary",
        "skills": [],
        "metrics": {},
        "contributions": {},
    }
    save_project_summary(conn, user_id, "proj1", json.dumps(summary))

    monkeypatch.setattr(
        "src.services.portfolio_service.collect_project_data",
        lambda c, uid: [("proj1", 0.8)],
        raising=False,
    )
    monkeypatch.setattr("builtins.input", lambda _="": "")

    assert _handle_edit_portfolio_wording(conn, user_id, "Kevin") is False

    row = get_project_summary_by_name(conn, user_id, "proj1")
    summary_dict = json.loads(row["summary_json"])
    assert summary_dict.get("portfolio_overrides") is None


def test_portfolio_global_edit_clears_portfolio_override(conn, capsys, monkeypatch):
    """
    Bug fix test: When a user first edits portfolio-only, then edits globally,
    the portfolio_overrides for that field should be cleared so the global
    manual_overrides take effect (since portfolio_overrides has higher priority).
    """
    user_id = 1
    # Start with a project that has existing portfolio_overrides
    summary = {
        "project_name": "proj1",
        "project_type": "text",
        "project_mode": "individual",
        "summary_text": "Original summary",
        "skills": [],
        "metrics": {},
        "contributions": {},
        "portfolio_overrides": {
            "summary_text": "Portfolio-only summary",
        },
    }
    save_project_summary(conn, user_id, "proj1", json.dumps(summary))

    monkeypatch.setattr(
        "src.services.portfolio_service.collect_project_data",
        lambda c, uid: [("proj1", 0.8)],
        raising=False,
    )

    # Mock _apply_manual_overrides_to_resumes to avoid resume-related side effects
    monkeypatch.setattr(
        "src.services.resume_overrides.apply_manual_overrides_to_resumes",
        lambda *args, **kwargs: None,
    )

    # Simulate: select project 1, scope 2 (global), edit section 1 (summary_text)
    inputs = iter(["1", "2", "1", "Global summary"])
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))

    assert _handle_edit_portfolio_wording(conn, user_id, "Kevin") is True

    row = get_project_summary_by_name(conn, user_id, "proj1")
    summary_dict = json.loads(row["summary_json"])

    # Global override should be set
    assert summary_dict["manual_overrides"]["summary_text"] == "Global summary"

    # Portfolio override should be cleared for this field
    portfolio_overrides = summary_dict.get("portfolio_overrides") or {}
    assert "summary_text" not in portfolio_overrides

    # Verify the portfolio now uses the global override by displaying it
    _display_portfolio(conn, user_id, "Kevin")
    out = capsys.readouterr().out
    assert "Summary: Global summary" in out
    # The old portfolio-only summary should no longer appear in the final display
    assert "Summary: Portfolio-only summary" not in out
