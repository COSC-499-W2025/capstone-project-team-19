# src/export/portfolio_pdf.py
"""
Export the user's portfolio view to a PDF document (ReportLab Platypus).

Design goal:
- Match CLI output structure/wording (line-based “card”)
- Preserve indentation (leading spaces) but STILL wrap long lines (Summary, etc.)
- Include thumbnails if present and valid
- Thumbnail should be LEFT-aligned and placed AFTER the project title line

Key approach:
- Render each CLI line as a Paragraph in Courier (wraps automatically)
- Preserve only leading indentation by converting leading spaces to NBSP
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import sqlite3
from typing import Any, Dict, List, Tuple
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Image,
)
from reportlab.lib import utils
from reportlab.platypus.flowables import HRFlowable

from src.insights.rank_projects.rank_project_importance import collect_project_data
from src.db import get_project_summary_row, get_project_thumbnail_path
from src.insights.portfolio import (
    format_duration,
    format_languages,
    format_frameworks,
    format_activity_line,
    format_skills_block,
    format_summary_block,
    resolve_portfolio_display_name,
)


def _safe_slug(s: str) -> str:
    """Make a filename-safe slug."""
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "user"


def _load_image_preserve_aspect(path: str, max_width: float) -> Image | None:
    """
    Load an image and scale it to max_width while preserving aspect ratio.
    Returns a Platypus Image or None if anything fails.

    Also forces LEFT alignment.
    """
    try:
        p = Path(path)
        if not p.exists():
            return None

        img = utils.ImageReader(str(p))
        w, h = img.getSize()
        if not w or not h:
            return None

        scale = max_width / float(w)
        new_w = max_width
        new_h = float(h) * scale

        flow = Image(str(p), width=new_w, height=new_h)
        flow.hAlign = "LEFT"  # ✅ left align inside the frame
        return flow
    except Exception:
        return None


def _cli_line_to_paragraph(line: str, style: ParagraphStyle) -> Paragraph:
    """
    Render a single CLI line as a wrapping Paragraph, preserving indentation.

    - Convert ONLY leading spaces to NBSP to preserve indentation.
    - Escape markup chars so ReportLab doesn't treat text as XML.
    - Internal spaces remain normal so wrapping can occur.
    """
    if not line:
        return Paragraph("", style)

    stripped = line.lstrip(" ")
    n_leading = len(line) - len(stripped)

    indent = "\u00A0" * n_leading  # NBSP
    safe = escape(stripped)

    return Paragraph(indent + safe, style)


def export_portfolio_to_pdf(
    conn: sqlite3.Connection,
    user_id: int,
    username: str,
    out_dir: str = "./out",
) -> Path:
    """
    Export the user's portfolio (same content as terminal view) to a .pdf in ./out/.

    Returns the output Path.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    stamp_filename = now.strftime("%Y-%m-%d_%H-%M-%S")
    stamp_display = now.strftime("%Y-%m-%d at %H:%M:%S")

    filename = f"portfolio_{_safe_slug(username)}_{stamp_filename}.pdf"
    filepath = out_path / filename

    project_scores: List[Tuple[str, float]] = collect_project_data(conn, user_id)

    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=LETTER,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
        title=f"Portfolio - {username}",
        author=username,
    )

    styles = getSampleStyleSheet()

    TitleStyle = ParagraphStyle(
        "TitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        alignment=TA_CENTER,
        spaceAfter=10, 
    )

    MetaStyle = ParagraphStyle(
        "MetaStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=10,
    )

    # Monospace line style that WRAPS
    CliLineStyle = ParagraphStyle(
        "CliLineStyle",
        parent=styles["Normal"],
        fontName="Helvetica",   
        fontSize=11,           
        leading=14,             
        alignment=TA_LEFT,
        spaceAfter=0,
        spaceBefore=0,
        splitLongWords=True,
    )

    ProjectTitleStyle = ParagraphStyle(
        "ProjectTitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",  # ✅ bold
        fontSize=12.5,              # ✅ slightly larger than body
        leading=15,
        spaceBefore=8,
        spaceAfter=4,
    )

    story: List[Any] = []

    # Header
    story.append(Paragraph(f"Portfolio - {username}", TitleStyle))
    story.append(_rule())
    story.append(Paragraph(f"Generated on {stamp_display}", MetaStyle))

    if not project_scores:
        story.append(_cli_line_to_paragraph("No projects found. Please analyze some projects first.", CliLineStyle))
        doc.build(story)
        return filepath

    for rank, (project_name, score) in enumerate(project_scores, start=1):
        row = get_project_summary_row(conn, user_id, project_name)
        if row is None:
            continue

        summary: Dict[str, Any] = row.get("summary") or {}
        project_type = row.get("project_type") or summary.get("project_type") or "unknown"
        project_mode = row.get("project_mode") or summary.get("project_mode") or "individual"
        created_at = row.get("created_at") or ""

        display_name = resolve_portfolio_display_name(summary, project_name)

        # Build lines exactly like CLI output
        lines: List[str] = []
        lines.append(f"[{rank}] {display_name} — Score {score:.3f}")
        lines.append(f"  Type: {project_type} ({project_mode})")
        lines.append(f"  {format_duration(project_type, project_mode, created_at, user_id, project_name, conn)}")

        if project_type == "code":
            lines.append(f"  {format_languages(summary)}")
            lines.append(f"  {format_frameworks(summary)}")

        lines.append(f"  {format_activity_line(project_type, project_mode, conn, user_id, project_name, summary)}")

        for line in format_skills_block(summary):
            lines.append(f"  {line}")

        for line in format_summary_block(project_type, project_mode, summary, conn, user_id, project_name):
            lines.append(f"  {line}")

        # 1) Project title line
        story.append(
            _cli_line_to_paragraph(lines[0], ProjectTitleStyle)
        )

        # 2) Thumbnail after title line (left-aligned)
        thumb = get_project_thumbnail_path(conn, user_id, project_name)
        if thumb:
            img = _load_image_preserve_aspect(thumb, max_width=2.0 * inch)
            if img:
                story.append(Spacer(1, 0.08 * inch))
                story.append(img)
                story.append(Spacer(1, 0.12 * inch))

        # 3) Remaining lines
        for line in lines[1:]:
            story.append(_cli_line_to_paragraph(line, CliLineStyle))

        story.append(Spacer(1, 0.25 * inch))

    doc.build(story)
    return filepath

def _rule() -> HRFlowable:
    """Horizontal rule separating header from content."""
    return HRFlowable(
        width="100%",
        thickness=0.8,
        lineCap="round",
        spaceBefore=6,
        spaceAfter=14,
    )