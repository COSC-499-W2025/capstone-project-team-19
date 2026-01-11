# src/export/portfolio_docx.py

"""
Export the user's portfolio view to a Word (.docx) document.

This module converts the same formatted portfolio data shown in the terminal
into a structured, recruiter-ready document saved in ./out/.
It reuses the existing portfolio formatters to ensure consistency between
CLI output and exported files.
"""


from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import sqlite3
from typing import Any, Dict, List, Tuple

from docx import Document

from src.insights.rank_projects.rank_project_importance import collect_project_data
from src.db import get_project_summary_row
from src.insights.portfolio import (
    format_duration,
    format_languages,
    format_frameworks,
    format_activity_line,
    format_skills_block,
    format_summary_block,
)


def _safe_slug(s: str) -> str:
    """Make a filename-safe slug."""
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "user"


def _add_bullet(doc: Document, text: str) -> None:
    """
    Add a real bullet paragraph in Word.
    Word default style name is usually "List Bullet".
    """
    p = doc.add_paragraph(text, style="List Bullet")
    # Optional: tighten spacing a bit (nice for portfolios)
    p.paragraph_format.space_after = 0


def export_portfolio_to_docx(
    conn: sqlite3.Connection,
    user_id: int,
    username: str,
    out_dir: str = "./out",
) -> Path:
    """
    Export the user's portfolio (same content as terminal view) to a .docx in ./out/.

    Returns the output Path.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    stamp_filename = now.strftime("%Y-%m-%d_%H-%M-%S")   
    stamp_display = now.strftime("%Y-%m-%d at %H:%M:%S") 
    
    filename = f"portfolio_{_safe_slug(username)}_{stamp_filename}.docx"
    filepath = out_path / filename

    project_scores: List[Tuple[str, float]] = collect_project_data(conn, user_id)

    doc = Document()

    # Title
    doc.add_heading(f"Portfolio — {username}", level=0)
    doc.add_paragraph(f"Generated on {stamp_display}")

    if not project_scores:
        doc.add_paragraph("No projects found. Please analyze some projects first.")
        doc.save(str(filepath))
        return filepath

    # One "card" per project
    for rank, (project_name, score) in enumerate(project_scores, start=1):
        row = get_project_summary_row(conn, user_id, project_name)
        if row is None:
            continue

        summary: Dict[str, Any] = row["summary"] or {}
        project_type = row.get("project_type") or summary.get("project_type") or "unknown"
        project_mode = row.get("project_mode") or summary.get("project_mode") or "individual"
        created_at = row.get("created_at") or ""

        # Heading for project
        doc.add_heading(f"{project_name}", level=1)

        # Metadata lines
        doc.add_paragraph(f"Score: {score:.3f}")
        doc.add_paragraph(f"Type: {project_type} ({project_mode})")
        doc.add_paragraph(
            format_duration(project_type, project_mode, created_at, user_id, project_name, conn)
        )

        if project_type == "code":
            doc.add_paragraph(format_languages(summary))
            doc.add_paragraph(format_frameworks(summary))

        doc.add_paragraph(
            format_activity_line(project_type, project_mode, conn, user_id, project_name, summary)
        )

        # Skills block
        skill_lines = format_skills_block(summary)
        if skill_lines:
            # If it returns ["Skills: N/A"], keep as paragraph
            if len(skill_lines) == 1 and "N/A" in skill_lines[0]:
                doc.add_paragraph(skill_lines[0])
            else:
                # First line is "Skills:"
                doc.add_paragraph("Skills")
                for line in skill_lines[1:]:
                    # expected: "  - skill_name"
                    bullet_text = line.strip()
                    if bullet_text.startswith("-"):
                        bullet_text = bullet_text[1:].strip()
                    elif bullet_text.startswith("•"):
                        bullet_text = bullet_text[1:].strip()
                    # your format is "  - xxx" so after strip it's "- xxx"
                    if bullet_text.startswith("-"):
                        bullet_text = bullet_text[1:].strip()
                    _add_bullet(doc, bullet_text)

        # Summary block
        summary_lines = format_summary_block(project_type, project_mode, summary, conn, user_id, project_name)

        # Two possible shapes:
        # A) ["Summary:", "  - Project: ...", "  - My contribution: ..."]
        # B) ["Summary: ..."]
        if summary_lines:
            if summary_lines[0].strip() == "Summary:":
                doc.add_paragraph("")
                doc.add_paragraph("Summary")
                for line in summary_lines[1:]:
                    bullet_text = line.strip()
                    # line is "  - Project: ..." so strip => "- Project: ..."
                    if bullet_text.startswith("-"):
                        bullet_text = bullet_text[1:].strip()
                    _add_bullet(doc, bullet_text)
            else:
                # Single-line summary
                doc.add_paragraph(summary_lines[0])

        # Spacing between projects
        doc.add_paragraph("")

    doc.save(str(filepath))
    return filepath
