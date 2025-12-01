import json
import sqlite3
import pytest
from src.db import init_schema, save_project_summary
from src.menu.portfolio import view_portfolio_items


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
        "src.menu.portfolio.collect_project_data",
        lambda *_: [],
        raising=False,
    )

    view_portfolio_items(conn, user_id=1, username="Kevin")
    out = capsys.readouterr().out

    assert "No projects found" in out
    assert "[1]" not in out


def test_portfolio_single_basic_project(conn, capsys, monkeypatch):
    user_id = 1
    save_project_summary(conn, user_id, "proj1", _make_portfolio_summary("proj1"))

    monkeypatch.setattr(
        "src.menu.portfolio.collect_project_data",
        lambda c, uid: [("proj1", 0.8)],
        raising=False,
    )

    view_portfolio_items(conn, user_id, "Kevin")
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
        "src.menu.portfolio.collect_project_data",
        lambda c, uid: [("C", 0.9), ("B", 0.8), ("A", 0.7)],
        raising=False,
    )

    view_portfolio_items(conn, user_id, "Kevin")
    out = capsys.readouterr().out

    assert "[1] C" in out
    assert "[2] B" in out
    assert "[3] A" in out
    assert "Score 0.900" in out

def test_portfolio_missing_fields(conn, capsys, monkeypatch):
    save_project_summary(conn, 1, "Bare", json.dumps({}))   # totally empty summary JSON

    monkeypatch.setattr(
        "src.menu.portfolio.collect_project_data",
        lambda *_: [("Bare", 0.5)],
        raising=False,
    )

    view_portfolio_items(conn, 1, "Kevin")
    out = capsys.readouterr().out

    assert "[1] Bare" in out
    assert "Duration:" in out
    assert "Activity:" in out
    assert "Summary:" in out        
