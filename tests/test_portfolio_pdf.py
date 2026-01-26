import os
import re
import sqlite3
from pathlib import Path

import pytest
from pypdf import PdfReader
from reportlab.platypus import Spacer


# --- Tiny 1x1 PNG (valid) as raw bytes so we don't need Pillow ---
# This is a standard minimal PNG file (transparent).
_ONE_BY_ONE_PNG = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\x0bIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    chunks = []
    for page in reader.pages:
        t = page.extract_text() or ""
        chunks.append(t)
    return "\n".join(chunks)


@pytest.fixture()
def conn():
    # Real connection not used because we monkeypatch data fetchers,
    # but keep signature consistent.
    return sqlite3.connect(":memory:")


def test_export_portfolio_pdf_no_projects(monkeypatch, tmp_path, conn):
    """
    When there are no projects, we still produce a PDF with header + message.
    """
    from src.export import portfolio_pdf as mod

    # No projects
    monkeypatch.setattr(mod, "collect_project_data", lambda _conn, _user_id: [])

    # DB getters won't be called, but safe to patch anyway
    monkeypatch.setattr(mod, "get_project_summary_row", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(mod, "get_project_thumbnail_path", lambda *_args, **_kwargs: None)

    pdf_path = mod.export_portfolio_to_pdf(
        conn=conn,
        user_id=1,
        username="Salma",
        out_dir=str(tmp_path),
    )

    assert pdf_path.exists()
    assert pdf_path.suffix.lower() == ".pdf"
    assert pdf_path.stat().st_size > 0

    text = _extract_pdf_text(pdf_path)
    assert "Portfolio - Salma" in text
    assert "Generated on" in text
    assert "No projects found. Please analyze some projects first." in text


def test_export_portfolio_pdf_happy_path_includes_project_text_and_long_summary(monkeypatch, tmp_path, conn):
    """
    One project: ensures header, project line, and long summary content appear in extracted text.
    """
    from src.export import portfolio_pdf as mod

    # One ranked project
    monkeypatch.setattr(mod, "collect_project_data", lambda _conn, _user_id: [("proj_a", 0.1234)])

    # Fake row shape used by portfolio_pdf.py
    fake_summary = {"display_name": "My Project"}  # display name resolved by patched function below
    fake_row = {
        "summary": fake_summary,
        "project_type": "code",
        "project_mode": "individual",
        "created_at": "2025-01-01",
    }
    monkeypatch.setattr(mod, "get_project_summary_row", lambda *_args, **_kwargs: fake_row)

    # No thumbnail
    monkeypatch.setattr(mod, "get_project_thumbnail_path", lambda *_args, **_kwargs: None)

    # Make formatting deterministic
    monkeypatch.setattr(mod, "resolve_portfolio_display_name", lambda summary, project_name: "My Project")
    monkeypatch.setattr(mod, "format_duration", lambda *_args, **_kwargs: "Duration: 2025-01-01 — 2025-02-01")
    monkeypatch.setattr(mod, "format_languages", lambda _summary: "Languages: Python, SQL")
    monkeypatch.setattr(mod, "format_frameworks", lambda _summary: "Frameworks: FastAPI")
    monkeypatch.setattr(mod, "format_activity_line", lambda *_args, **_kwargs: "Activity: 10 commits")

    monkeypatch.setattr(mod, "format_skills_block", lambda _summary: ["Skills:", "  - data analysis", "  - APIs"])

    # Very long summary line to ensure it's not lost (wrapping shouldn't drop content)
    long_tail = " ".join(["verylongtext"] * 50)
    monkeypatch.setattr(
        mod,
        "format_summary_block",
        lambda *_args, **_kwargs: [f"Summary: {long_tail}"],
    )

    pdf_path = mod.export_portfolio_to_pdf(
        conn=conn,
        user_id=1,
        username="Salma",
        out_dir=str(tmp_path),
    )

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0

    text = _extract_pdf_text(pdf_path)

    # Header
    assert "Portfolio - Salma" in text
    assert "Generated on" in text

    # Project title line with score (rounded to 3 decimals in your code)
    assert "[1] My Project" in text
    assert "Score 0.123" in text

    # Some metadata + skills
    assert "Type: code (individual)" in text
    assert "Duration: 2025-01-01" in text
    assert "Languages: Python, SQL" in text
    assert "Frameworks: FastAPI" in text
    assert "Activity: 10 commits" in text
    assert "Skills:" in text
    assert "data analysis" in text
    assert "APIs" in text

    # Long summary content present (we just check a distinctive chunk)
    assert "Summary:" in text
    assert "verylongtext" in text

def test_export_portfolio_pdf_with_thumbnail_does_not_crash(monkeypatch, tmp_path, conn):
    """
    If a thumbnail path exists, export should still succeed.
    We don't test ReportLab image decoding here—only that our code attempts to include it.
    """
    from src.export import portfolio_pdf as mod

    # One ranked project
    monkeypatch.setattr(mod, "collect_project_data", lambda _conn, _user_id: [("proj_a", 0.5)])

    fake_row = {
        "summary": {},
        "project_type": "text",
        "project_mode": "individual",
        "created_at": "2025-01-01",
    }
    monkeypatch.setattr(mod, "get_project_summary_row", lambda *_args, **_kwargs: fake_row)

    # Pretend a thumbnail exists
    thumb_path = tmp_path / "thumb.png"
    thumb_path.write_text("not-a-real-image")  # doesn't matter; we won't decode it
    monkeypatch.setattr(mod, "get_project_thumbnail_path", lambda *_args, **_kwargs: str(thumb_path))

    # Track that the loader is called
    called = {"n": 0}

    def fake_loader(path: str, max_width: float):
        called["n"] += 1
        # Return a valid Flowable that won't error
        return Spacer(1, 1)

    monkeypatch.setattr(mod, "_load_image_preserve_aspect", fake_loader)

    # Minimal formatter patches
    monkeypatch.setattr(mod, "resolve_portfolio_display_name", lambda *_args, **_kwargs: "Project With Thumb")
    monkeypatch.setattr(mod, "format_duration", lambda *_args, **_kwargs: "Duration: N/A")
    monkeypatch.setattr(mod, "format_activity_line", lambda *_args, **_kwargs: "Activity: N/A")
    monkeypatch.setattr(mod, "format_skills_block", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(mod, "format_summary_block", lambda *_args, **_kwargs: ["Summary: ok"])

    pdf_path = mod.export_portfolio_to_pdf(
        conn=conn,
        user_id=1,
        username="Salma",
        out_dir=str(tmp_path),
    )

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
    assert called["n"] == 1  # ✅ we attempted to include the thumbnail

    text = _extract_pdf_text(pdf_path)
    assert "Project With Thumb" in text
    assert "Summary: ok" in text

def test_export_portfolio_pdf_thumbnail_removed_still_exports(monkeypatch, tmp_path, conn):
    """
    Simulate thumbnail existing, then being removed (path returns None).
    Both exports should succeed.
    """
    from src.export import portfolio_pdf as mod

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

    # Make thumbnail loader safe
    called = {"n": 0}

    def fake_loader(path: str, max_width: float):
        called["n"] += 1
        return Spacer(1, 1)

    monkeypatch.setattr(mod, "_load_image_preserve_aspect", fake_loader)

    # 1) With thumbnail
    thumb_path = tmp_path / "thumb.png"
    thumb_path.write_text("not-a-real-image")
    monkeypatch.setattr(mod, "get_project_thumbnail_path", lambda *_args, **_kwargs: str(thumb_path))

    pdf1 = mod.export_portfolio_to_pdf(conn=conn, user_id=1, username="Salma", out_dir=str(tmp_path))
    assert pdf1.exists() and pdf1.stat().st_size > 0
    assert called["n"] == 1

    # 2) Thumbnail removed
    monkeypatch.setattr(mod, "get_project_thumbnail_path", lambda *_args, **_kwargs: None)

    pdf2 = mod.export_portfolio_to_pdf(conn=conn, user_id=1, username="Salma", out_dir=str(tmp_path))
    assert pdf2.exists() and pdf2.stat().st_size > 0
    assert called["n"] == 1  # ✅ not called again

    text2 = _extract_pdf_text(pdf2)
    assert "Thumb Project" in text2
    assert "Summary: ok" in text2


def test_export_portfolio_pdf_reflects_edited_summary_text(monkeypatch, tmp_path, conn):
    """
    If the portfolio summary wording was edited (via overrides),
    the exporter should reflect whatever the CLI formatters output.
    """
    from src.export import portfolio_pdf as mod

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

    # Simulate formatter honoring the override (your real formatter likely does this internally)
    monkeypatch.setattr(mod, "format_summary_block", lambda *_args, **_kwargs: ["Summary: NEW SUMMARY HERE"])

    pdf_path = mod.export_portfolio_to_pdf(conn=conn, user_id=1, username="Salma", out_dir=str(tmp_path))
    text = _extract_pdf_text(pdf_path)

    assert "Edited Summary Project" in text
    assert "Summary: NEW SUMMARY HERE" in text


def test_export_portfolio_pdf_reflects_edited_contribution_bullets(monkeypatch, tmp_path, conn):
    """
    If contribution bullets were edited, and your CLI summary block includes them,
    ensure the PDF contains the edited bullets.
    """
    from src.export import portfolio_pdf as mod

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

    # Simulate CLI’s summary formatter output including the edited bullets
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

    pdf_path = mod.export_portfolio_to_pdf(conn=conn, user_id=1, username="Salma", out_dir=str(tmp_path))
    text = _extract_pdf_text(pdf_path)

    assert "Edited Bullets Project" in text
    assert "My contribution: Did X" in text
    assert "My contribution: Did Y" in text
