# src/export/portfolio_pdf.py
"""
Export the user's portfolio view to a PDF document (ReportLab Platypus).

Structure:
- Resume-like styling (Helvetica, readable sizing)
- NO rank/score/type lines
- Reformat duration to "Mon YYYY – Mon YYYY / Present"
- Languages/frameworks: remove % (optionally threshold languages)
- Activity: remove % token (e.g., "Final 100%" -> "Final")
- Skills: one line
- Project summary + My contribution:
    - NOT bold labels
    - Proper bullets (NO double bullets)
    - Labels NOT indented; only content is nested
- Thumbnails included after project title (left aligned)
- Portfolio edits (add/rewrite) must reflect in export:
    -> use the same resolver used by the menu:
       resolve_portfolio_display_name / resolve_portfolio_summary_text /
       resolve_portfolio_contribution_bullets
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import sqlite3
from typing import Any, Dict, List, Tuple

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib import utils

from src.insights.rank_projects.rank_project_importance import collect_project_data
from src.db import get_project_summary_row, get_project_thumbnail_path
from src.insights.portfolio import (
    format_duration,
    format_activity_line,
    resolve_portfolio_display_name,
    resolve_portfolio_summary_text,
    resolve_portfolio_contribution_bullets,
    get_all_skills_from_summary,
)
from src.services.skill_preferences_service import get_highlighted_skills_for_display
from src.db.projects import get_project_key

# use shared helpers
from src.export.shared_helpers import (
    format_date_range,
    strip_percent_tokens,
)
from src.export.portfolio_helpers import reformat_duration_line, _skills_one_line,  _frameworks_clean, _languages_clean
from src.insights.portfolio.formatters import _clean_bullets

# -------------------------
# Local helpers (PDF-only)
# -------------------------

def _safe_slug(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "user"


def _rule() -> HRFlowable:
    return HRFlowable(
        width="100%",
        thickness=0.8,
        lineCap="round",
        spaceBefore=6,
        spaceAfter=10,
    )


def _load_image_preserve_aspect(path: str, max_width: float) -> Image | None:
    try:
        p = Path(path)
        if not p.exists():
            return None
        img = utils.ImageReader(str(p))
        w, h = img.getSize()
        if not w or not h:
            return None
        scale = max_width / float(w)
        flow = Image(str(p), width=max_width, height=float(h) * scale)
        flow.hAlign = "LEFT"
        return flow
    except Exception:
        return None

# -------------------------
# Export
# -------------------------

def export_portfolio_to_pdf(
    conn: sqlite3.Connection,
    user_id: int,
    username: str,
    out_dir: str = "./out",
) -> Path:
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
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
        title=f"Portfolio - {username}",
        author=username,
    )

    styles = getSampleStyleSheet()

    TitleStyle = ParagraphStyle(
        "TitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        alignment=TA_LEFT,
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

    ProjectTitleStyle = ParagraphStyle(
        "ProjectTitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=20,
        alignment=TA_LEFT,
        spaceBefore=12,
        spaceAfter=6,
    )

    Body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=2,
    )

    # OUTER bullet: same level for Duration/Activity/Skills/labels
    OuterBullet = ParagraphStyle(
        "OuterBullet",
        parent=Body,
        bulletIndent=18,
        leftIndent=34,
        spaceBefore=0,
        spaceAfter=2,
    )

    # NESTED bullet: only for summary content + contribution bullets
    NestedBullet = ParagraphStyle(
        "NestedBullet",
        parent=Body,
        alignment=TA_JUSTIFY,
        bulletIndent=44,
        leftIndent=60,
        firstLineIndent=0,
        spaceBefore=0,
        spaceAfter=2,
    )

    def add_outer(text: str) -> None:
        story.append(Paragraph(text, OuterBullet, bulletText="•"))

    def add_nested(text: str) -> None:
        story.append(Paragraph(text, NestedBullet, bulletText="o"))

    story: List[Any] = []

    # Header
    story.append(Paragraph(f"Portfolio - {username}", TitleStyle))
    story.append(_rule())
    story.append(Paragraph(f"Generated on {stamp_display}", MetaStyle))

    if not project_scores:
        story.append(Paragraph("No projects found. Please analyze some projects first.", Body))
        doc.build(story)
        return filepath

    for project_name, _score in project_scores:
        row = get_project_summary_row(conn, user_id, project_name)
        if row is None:
            continue

        summary: Dict[str, Any] = row.get("summary") or {}
        project_type = row.get("project_type") or summary.get("project_type") or "unknown"
        project_mode = row.get("project_mode") or summary.get("project_mode") or "individual"
        created_at = row.get("created_at") or ""

        # Resolvers (respects portfolio_overrides)
        display_name = resolve_portfolio_display_name(summary, project_name)

        # Duration:
        # 1) Prefer explicit start/end (DB truth) -> shared format_date_range
        # 2) Else fallback to existing format_duration output -> normalize with reformat_duration_line
        date_line = format_date_range(summary.get("start_date"), summary.get("end_date"))
        if not date_line:
            raw_duration = (
                format_duration(project_type, project_mode, created_at, user_id, project_name, conn) or ""
            )
            date_line = reformat_duration_line(raw_duration)
        if not date_line:
            date_line = "N/A"

        # Activity: remove percent token
        activity_line = format_activity_line(
            project_type, project_mode, conn, user_id, project_name, summary
        ) or ""
        activity_line = strip_percent_tokens(activity_line)
        if activity_line.lower().startswith("activity:"):
            activity_line = activity_line.split(":", 1)[1].strip()

        # Skills: one line (filtered by per-project skill preferences)
        all_project_skills = get_all_skills_from_summary(summary)
        pk = get_project_key(conn, user_id, project_name)
        highlighted_skills = get_highlighted_skills_for_display(
            conn=conn, user_id=user_id, context="portfolio", project_key=pk,
        ) if pk else None
        if highlighted_skills:
            filtered_skills = [s for s in highlighted_skills if s in all_project_skills]
        else:
            filtered_skills = all_project_skills
        skills = ", ".join(filtered_skills) if filtered_skills else ""

        # Summary + contribution from portfolio resolvers
        project_summary_text = (resolve_portfolio_summary_text(summary) or "").strip()
        contrib_bullets = resolve_portfolio_contribution_bullets(
            summary,
            project_type,
            project_mode,
            conn,
            user_id,
            project_name,
        ) or []
        contrib_bullets = _clean_bullets(contrib_bullets)

        if not project_summary_text:
            project_summary_text = "[No summary provided]"
        if not contrib_bullets:
            contrib_bullets = ["[No manual contribution summary provided]"]

        # ---------------------------
        # Project header + image
        # ---------------------------
        story.append(Paragraph(str(display_name), ProjectTitleStyle))

        thumb = get_project_thumbnail_path(conn, user_id, project_name)
        if thumb:
            img = _load_image_preserve_aspect(thumb, max_width=2.6 * inch)
            if img:
                story.append(Spacer(1, 4))
                story.append(img)
                story.append(Spacer(1, 10))

        # ---------------------------
        # OUTER bullets (consistent)
        # ---------------------------
        add_outer(f"Duration: {date_line}")

        if project_type == "code":
            add_outer(f"Languages: {_languages_clean(summary)}")
            add_outer(f"Frameworks: {_frameworks_clean(summary)}")

        add_outer(f"Activity: {activity_line or 'N/A'}")

        if skills:
            add_outer(f"Skills: {skills}")

        # Labels are OUTER; content is nested
        add_outer("Project summary:")
        add_nested(project_summary_text)

        add_outer("My contribution:")
        for b in contrib_bullets:
            add_nested(str(b))

        story.append(Spacer(1, 14))

    doc.build(story)
    return filepath
