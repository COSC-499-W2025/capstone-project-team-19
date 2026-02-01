import os
import sqlite3
from pathlib import Path

import pytest
from docx import Document


def _extract_docx_text(docx_path: Path) -> str:
    doc = Document(str(docx_path))
    return "\n".join(p.text or "" for p in doc.paragraphs)


@pytest.fixture()
def conn():
    # Real connection not used because we monkeypatch data fetchers,
    # but keep signature consistent.
    return sqlite3.connect(":memory:")


def test_export_portfolio_docx_no_projects(monkeypatch, tmp_path, conn):
    """
    When there are no projects, we still produce a DOCX with header + message.
    """
    from src.export import portfolio_docx as mod

    monkeypatch.setattr(mod, "collect_project_data", lambda _conn, _user_id: [])
    monkeypatch.setattr(mod, "get_project_summary_row", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(mod, "get_project_thumbnail_path", lambda *_args, **_kwargs: None)

    docx_path = mod.export_portfolio_to_docx(
        conn=conn,
        user_id=1,
        username="Jordan",
        out_dir=str(tmp_path),
    )

    assert docx_path.exists()
    assert docx_path.suffix.lower() == ".docx"
    assert docx_path.stat().st_size > 0

    text = _extract_docx_text(docx_path)
    assert "Portfolio — Jordan" in text
    assert "Generated on" in text
    assert "No projects found. Please analyze some projects first." in text


def test_export_portfolio_docx_happy_path_includes_project_text_and_long_summary(monkeypatch, tmp_path, conn):
    """
    One project: ensures header, project line, and long summary content appear in extracted text.
    """
    from src.export import portfolio_docx as mod

    monkeypatch.setattr(mod, "collect_project_data", lambda _conn, _user_id: [("proj_a", 0.1234)])

    fake_summary = {"display_name": "My Fiction Project"}
    fake_row = {
        "summary": fake_summary,
        "project_type": "code",
        "project_mode": "individual",
        "created_at": "2025-01-01",
    }
    monkeypatch.setattr(mod, "get_project_summary_row", lambda *_args, **_kwargs: fake_row)
    monkeypatch.setattr(mod, "get_project_thumbnail_path", lambda *_args, **_kwargs: None)

    monkeypatch.setattr(mod, "resolve_portfolio_display_name", lambda summary, project_name: "My Fiction Project")
    monkeypatch.setattr(mod, "format_duration", lambda *_args, **_kwargs: "Duration: 2025-01-01 — 2025-02-01")
    monkeypatch.setattr(mod, "format_languages", lambda _summary: "Languages: Python, SQL")
    monkeypatch.setattr(mod, "format_frameworks", lambda _summary: "Frameworks: FastAPI")
    monkeypatch.setattr(mod, "format_activity_line", lambda *_args, **_kwargs: "Activity: 10 commits")
    monkeypatch.setattr(mod, "format_skills_block", lambda _summary: ["Skills:", "  - data analysis", "  - APIs"])

    long_tail = " ".join(["verylongtext"] * 50)
    monkeypatch.setattr(mod, "format_summary_block", lambda *_args, **_kwargs: [f"Summary: {long_tail}"])

    docx_path = mod.export_portfolio_to_docx(
        conn=conn,
        user_id=1,
        username="Jordan",
        out_dir=str(tmp_path),
    )

    assert docx_path.exists()
    assert docx_path.stat().st_size > 0

    text = _extract_docx_text(docx_path)

    assert "Portfolio — Jordan" in text
    assert "Generated on" in text

    # Project title + score + type
    assert "My Fiction Project" in text
    assert "Score: 0.123" in text
    assert "Type: code (individual)" in text

    # Metadata + skills
    assert "Duration: 2025-01-01" in text
    assert "Languages: Python, SQL" in text
    assert "Frameworks: FastAPI" in text
    assert "Activity: 10 commits" in text
    assert "Skills" in text
    assert "data analysis" in text
    assert "APIs" in text

    # Long summary content present
    assert "Summary:" in text
    assert "verylongtext" in text


def test_export_portfolio_docx_with_thumbnail_does_not_crash(monkeypatch, tmp_path, conn):
    """
    If a thumbnail path exists, export should still succeed.
    We don't test Word image decoding in depth—only that our code attempts to include it.
    """
    from src.export import portfolio_docx as mod

    monkeypatch.setattr(mod, "collect_project_data", lambda _conn, _user_id: [("proj_a", 0.5)])

    fake_row = {
        "summary": {},
        "project_type": "text",
        "project_mode": "individual",
        "created_at": "2025-01-01",
    }
    monkeypatch.setattr(mod, "get_project_summary_row", lambda *_args, **_kwargs: fake_row)

    # Write a real tiny valid PNG
    thumb_path = tmp_path / "thumb.png"
    png = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\x0bIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    thumb_path.write_bytes(png)

    monkeypatch.setattr(mod, "get_project_thumbnail_path", lambda *_args, **_kwargs: str(thumb_path))

    monkeypatch.setattr(mod, "resolve_portfolio_display_name", lambda *_args, **_kwargs: "Project With Thumb")
    monkeypatch.setattr(mod, "format_duration", lambda *_args, **_kwargs: "Duration: N/A")
    monkeypatch.setattr(mod, "format_activity_line", lambda *_args, **_kwargs: "Activity: N/A")
    monkeypatch.setattr(mod, "format_skills_block", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(mod, "format_summary_block", lambda *_args, **_kwargs: ["Summary: ok"])

    docx_path = mod.export_portfolio_to_docx(
        conn=conn,
        user_id=1,
        username="Jordan",
        out_dir=str(tmp_path),
    )

    assert docx_path.exists()
    assert docx_path.stat().st_size > 0

    # Check the docx package has at least one image part
    doc = Document(str(docx_path))
    assert len(doc.part.package.image_parts) >= 1

    text = _extract_docx_text(docx_path)
    assert "Project With Thumb" in text
    assert "Summary: ok" in text


def test_export_portfolio_docx_thumbnail_removed_still_exports(monkeypatch, tmp_path, conn):
    """
    Simulate thumbnail existing, then being removed (path returns None).
    Both exports should succeed.
    """
    from src.export import portfolio_docx as mod

    monkeypatch.setattr(mod, "collect_project_data", lambda _conn, _user_id: [("proj_a", 0.5)])
    fake_row = {
        "summary": {},
        "project_type": "text",
        "project_mode": "individual",
        "created_at": "2025-01-01",
    }
    monkeypatch.setattr(mod, "get_project_summary_row", lambda *_args, **_kwargs: fake_row)

    monkeypatch.setattr(mod, "resolve_portfolio_display_name", lambda *_args, **_kwargs: "Thumb Project")
    monkeypatch.setattr(mod, "format_duration", lambda *_args, **_kwargs: "Duration: N/A")
    monkeypatch.setattr(mod, "format_activity_line", lambda *_args, **_kwargs: "Activity: N/A")
    monkeypatch.setattr(mod, "format_skills_block", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(mod, "format_summary_block", lambda *_args, **_kwargs: ["Summary: ok"])

    # 1) With thumbnail
    thumb_path = tmp_path / "thumb.png"
    thumb_path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\x0bIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    monkeypatch.setattr(mod, "get_project_thumbnail_path", lambda *_args, **_kwargs: str(thumb_path))

    docx1 = mod.export_portfolio_to_docx(conn=conn, user_id=1, username="Jordan", out_dir=str(tmp_path))
    assert docx1.exists() and docx1.stat().st_size > 0

    # 2) Thumbnail removed
    monkeypatch.setattr(mod, "get_project_thumbnail_path", lambda *_args, **_kwargs: None)

    docx2 = mod.export_portfolio_to_docx(conn=conn, user_id=1, username="Jordan", out_dir=str(tmp_path))
    assert docx2.exists() and docx2.stat().st_size > 0

    text2 = _extract_docx_text(docx2)
    assert "Thumb Project" in text2
    assert "Summary: ok" in text2


def test_export_portfolio_docx_reflects_edited_summary_text(monkeypatch, tmp_path, conn):
    """
    If the portfolio summary wording was edited (via overrides),
    the exporter should reflect whatever the CLI formatters output.
    """
    from src.export import portfolio_docx as mod

    monkeypatch.setattr(mod, "collect_project_data", lambda _conn, _user_id: [("proj_a", 0.9)])
    fake_row = {
        "summary": {"portfolio_overrides": {"summary_text": "NEW SUMMARY HERE"}},
        "project_type": "text",
        "project_mode": "individual",
        "created_at": "2025-01-01",
    }
    monkeypatch.setattr(mod, "get_project_summary_row", lambda *_args, **_kwargs: fake_row)
    monkeypatch.setattr(mod, "get_project_thumbnail_path", lambda *_args, **_kwargs: None)

    monkeypatch.setattr(mod, "resolve_portfolio_display_name", lambda *_args, **_kwargs: "Edited Summary Project")
    monkeypatch.setattr(mod, "format_duration", lambda *_args, **_kwargs: "Duration: N/A")
    monkeypatch.setattr(mod, "format_activity_line", lambda *_args, **_kwargs: "Activity: N/A")
    monkeypatch.setattr(mod, "format_skills_block", lambda *_args, **_kwargs: [])

    monkeypatch.setattr(mod, "format_summary_block", lambda *_args, **_kwargs: ["Summary: NEW SUMMARY HERE"])

    docx_path = mod.export_portfolio_to_docx(conn=conn, user_id=1, username="Jordan", out_dir=str(tmp_path))
    text = _extract_docx_text(docx_path)

    assert "Edited Summary Project" in text
    assert "Summary: NEW SUMMARY HERE" in text


def test_export_portfolio_docx_reflects_edited_contribution_bullets(monkeypatch, tmp_path, conn):
    """
    If contribution bullets were edited, and your CLI summary block includes them,
    ensure the DOCX contains the edited bullets.
    """
    from src.export import portfolio_docx as mod

    monkeypatch.setattr(mod, "collect_project_data", lambda _conn, _user_id: [("proj_a", 0.7)])
    fake_row = {
        "summary": {"portfolio_overrides": {"contribution_bullets": ["Did X", "Did Y"]}},
        "project_type": "code",
        "project_mode": "individual",
        "created_at": "2025-01-01",
    }
    monkeypatch.setattr(mod, "get_project_summary_row", lambda *_args, **_kwargs: fake_row)
    monkeypatch.setattr(mod, "get_project_thumbnail_path", lambda *_args, **_kwargs: None)

    monkeypatch.setattr(mod, "resolve_portfolio_display_name", lambda *_args, **_kwargs: "Edited Bullets Project")
    monkeypatch.setattr(mod, "format_duration", lambda *_args, **_kwargs: "Duration: N/A")
    monkeypatch.setattr(mod, "format_languages", lambda *_args, **_kwargs: "Languages: Python")
    monkeypatch.setattr(mod, "format_frameworks", lambda *_args, **_kwargs: "Frameworks: None")
    monkeypatch.setattr(mod, "format_activity_line", lambda *_args, **_kwargs: "Activity: N/A")
    monkeypatch.setattr(mod, "format_skills_block", lambda *_args, **_kwargs: [])

    monkeypatch.setattr(
        mod,
        "format_summary_block",
        lambda *_args, **_kwargs: [
            "Summary:",
            "  - Project: Something",
            "  - My contribution: Did X",
            "  - My contribution: Did Y",
        ],
    )

    docx_path = mod.export_portfolio_to_docx(conn=conn, user_id=1, username="Jordan", out_dir=str(tmp_path))
    text = _extract_docx_text(docx_path)

    assert "Edited Bullets Project" in text
    assert "My contribution: Did X" in text
    assert "My contribution: Did Y" in text
