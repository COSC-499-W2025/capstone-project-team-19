import json
import os
import sqlite3
from pathlib import Path

import pytest
from docx import Document

# Use an in-memory SQLite database to test real SQL + JSON behavior without touching production data.
@pytest.fixture()
def mem_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE project_summaries (
            project_summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_name TEXT NOT NULL,
            project_type TEXT,
            project_mode TEXT,
            summary_json TEXT NOT NULL,
            created_at TEXT
        )
        """
    )
    conn.commit()
    return conn


def _doc_text(path: Path) -> str:
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text is not None)


def test_portfolio_export_happy_creates_out_and_contains_fields(monkeypatch, tmp_path, mem_conn):
    """
    Covers: P1 + P5 + P6 + X1 (deterministic path via frozen date)
    """
    # --- freeze date inside exporter module ---
    import src.export.portfolio_docx as exp

    class _FakeDate:
        @staticmethod
        def today():
            class _D:
                def isoformat(self):
                    return "2026-01-10"
            return _D()

    monkeypatch.setattr(exp, "date", _FakeDate)

    # --- patch ranking to avoid pipeline ---
    monkeypatch.setattr(exp, "collect_project_data", lambda conn, user_id: [("paper", 0.708), ("codeproj", 0.641)])

    # --- patch formatters to avoid extra DB tables ---
    monkeypatch.setattr(exp, "format_duration", lambda *a, **k: "Duration: 2025-07-09 – 2025-10-31")
    monkeypatch.setattr(exp, "format_activity_line", lambda *a, **k: "Activity: Data 50%, Final 50%")
    monkeypatch.setattr(exp, "format_skills_block", lambda summary: ["Skills:", "  - data_analysis", "  - planning"])
    monkeypatch.setattr(
        exp,
        "format_summary_block",
        lambda *a, **k: ["Summary:", "  - Project: test project", "  - My contribution: did stuff"],
    )
    # keep languages/frameworks real (uses summary)
    # exp.format_languages / exp.format_frameworks already imported in module

    # --- insert two project summaries (one text, one code) ---
    mem_conn.execute(
        "INSERT INTO project_summaries(user_id, project_name, project_type, project_mode, summary_json, created_at) VALUES(?,?,?,?,?,?)",
        (1, "paper", "text", "collaborative", json.dumps({"summary_text": "x"}), "2026-01-01"),
    )
    mem_conn.execute(
        "INSERT INTO project_summaries(user_id, project_name, project_type, project_mode, summary_json, created_at) VALUES(?,?,?,?,?,?)",
        (
            1,
            "codeproj",
            "code",
            "individual",
            json.dumps({"languages": ["Python"], "frameworks": ["LightGBM"], "summary_text": "y"}),
            "2026-01-01",
        ),
    )
    mem_conn.commit()

    out_dir = tmp_path / "out"  # does not exist
    path = exp.export_portfolio_to_docx(mem_conn, 1, "salma", out_dir=str(out_dir))

    assert out_dir.exists()
    assert path.name == "portfolio_salma_2026-01-10.docx"
    assert path.exists()

    txt = _doc_text(path)
    assert "Portfolio — salma" in txt
    assert "paper" in txt and "Score: 0.708" in txt
    assert "Type: text (collaborative)" in txt
    assert "codeproj" in txt
    assert "Languages: Python" in txt
    assert "Frameworks: LightGBM" in txt
    assert "Skills" in txt
    assert "Summary" in txt
    assert "Project: test project" in txt


def test_portfolio_view_decline_export(monkeypatch, mem_conn, capsys):
    """
    Covers: P2 (user answers 'n' -> no export call)
    """
    import src.menu.portfolio as menu

    # make portfolio view think there is a project
    monkeypatch.setattr(menu, "collect_project_data", lambda conn, user_id: [("paper", 0.1)])
    monkeypatch.setattr(menu, "get_project_summary_row", lambda conn, user_id, name: {
        "summary": {"summary_text": "x"},
        "project_type": "text",
        "project_mode": "individual",
        "created_at": "2026-01-01",
    })
    monkeypatch.setattr(menu, "format_duration", lambda *a, **k: "Duration: N/A")
    monkeypatch.setattr(menu, "format_activity_line", lambda *a, **k: "Activity: N/A")
    monkeypatch.setattr(menu, "format_skills_block", lambda s: ["Skills: N/A"])
    monkeypatch.setattr(menu, "format_summary_block", lambda *a, **k: ["Summary: x"])

    called = {"export": False}
    def _fake_export(*a, **k):
        called["export"] = True

    monkeypatch.setattr(menu, "export_portfolio_to_docx", _fake_export)
    monkeypatch.setattr("builtins.input", lambda _: "n")

    menu.view_portfolio_items(mem_conn, user_id=1, username="salma")
    out = capsys.readouterr().out
    assert "Returning to main menu" in out
    assert called["export"] is False


def test_portfolio_export_no_projects_creates_doc_with_message(monkeypatch, tmp_path, mem_conn):
    """
    Covers: P3 (no projects) — exporter produces a docx with 'No projects found...'
    """
    import src.export.portfolio_docx as exp

    class _FakeDate:
        @staticmethod
        def today():
            class _D:
                def isoformat(self):
                    return "2026-01-10"
            return _D()

    monkeypatch.setattr(exp, "date", _FakeDate)
    monkeypatch.setattr(exp, "collect_project_data", lambda conn, user_id: [])

    out_dir = tmp_path / "out"
    path = exp.export_portfolio_to_docx(mem_conn, 1, "salma", out_dir=str(out_dir))
    assert path.exists()

    txt = _doc_text(path)
    assert "Portfolio — salma" in txt
    assert "No projects found" in txt


def test_portfolio_export_skips_missing_summary_row(monkeypatch, tmp_path, mem_conn):
    """
    Covers: P4 (ranked project exists but row missing) — should not crash, doc still created.
    """
    import src.export.portfolio_docx as exp

    class _FakeDate:
        @staticmethod
        def today():
            class _D:
                def isoformat(self):
                    return "2026-01-10"
            return _D()

    monkeypatch.setattr(exp, "date", _FakeDate)
    monkeypatch.setattr(exp, "collect_project_data", lambda conn, user_id: [("missing_proj", 0.5)])

    # no DB row inserted => get_project_summary_row returns None naturally
    out_dir = tmp_path / "out"
    path = exp.export_portfolio_to_docx(mem_conn, 1, "salma", out_dir=str(out_dir))
    assert path.exists()

    txt = _doc_text(path)
    assert "Portfolio — salma" in txt
    assert "missing_proj" not in txt  # skipped
