# src/export/resume_pdf.py
"""
Export a saved resume snapshot (stored JSON) directly to a PDF using ReportLab (Platypus).

Layout (requested):
- Name (largest)
- line between name and contact
- Contact line
- PROFILE (placeholder)
- SKILLS
- PROJECTS (experience-style per project)
- EDUCATION & CERTIFICATES (placeholder)
- Add spacing BETWEEN sections (Profile/Skills/Projects/Education)

Notes:
- Uses snapshot JSON from get_resume_snapshot(...). No external converters needed.
- Long lines/bullets wrap automatically (Platypus Paragraph + ListFlowable).
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
)
from reportlab.platypus.flowables import HRFlowable

from src.export.resume_helpers import format_date_range, parse_date, clean_languages_above_threshold


def _safe_slug(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "user"


def _clean_bullets(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    out: List[str] = []
    for item in values:
        t = str(item).strip()
        if not t:
            continue
        if t.startswith(("-", "•")):
            t = t.lstrip("-•").strip()
        if t:
            out.append(t)
    return out


def _clean_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    out: List[str] = []
    for item in values:
        t = str(item).strip()
        if t:
            out.append(t)
    return out


def export_resume_record_to_pdf(
    *,
    username: str,
    record: Dict[str, Any],
    out_dir: str = "./out",
) -> Path:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    stamp_filename = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"resume_{_safe_slug(username)}_{stamp_filename}.pdf"
    filepath = out_path / filename

    resume_json = record.get("resume_json")
    rendered_text = record.get("rendered_text")

    snapshot: Optional[Dict[str, Any]] = None
    if isinstance(resume_json, str) and resume_json.strip():
        try:
            snapshot = json.loads(resume_json)
        except Exception:
            snapshot = None

    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=LETTER,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
        title=f"Resume - {username}",
        author=username,
    )

    styles = getSampleStyleSheet()

    # --- Sizing order requested: Name (biggest) > Section > Project title ---
    NameStyle = ParagraphStyle(
        "NameStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        alignment=TA_LEFT,
        spaceAfter=4,
    )

    ContactStyle = ParagraphStyle(
        "ContactStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        spaceAfter=6,
    )

    SectionStyle = ParagraphStyle(
        "SectionStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        spaceBefore=0,
        spaceAfter=6,
    )

    ProjectTitleStyle = ParagraphStyle(
        "ProjectTitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        spaceBefore=8,
        spaceAfter=2,
    )

    MetaItalic = ParagraphStyle(
        "MetaItalic",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10.5,
        leading=13,
        spaceAfter=6,
    )

    Body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        spaceAfter=2,
    )

    PlaceholderItalic = ParagraphStyle(
        "PlaceholderItalic",
        parent=Body,
        fontName="Helvetica-Oblique",
        spaceAfter=0,
    )

    def rule() -> HRFlowable:
        # Only used for name->contact separator now
        return HRFlowable(width="100%", thickness=0.8, lineCap="round", spaceBefore=6, spaceAfter=10)

    def section_gap() -> Spacer:
        # spacing BETWEEN sections (requested)
        return Spacer(1, 14)

    story: List[Any] = []

    # ---------------------------
    # Header
    # ---------------------------
    story.append(Paragraph(username.upper(), NameStyle))
    story.append(rule())  # line between name and contact
    story.append(Paragraph("Phone | Email | LinkedIn | Location", ContactStyle))

    # If JSON is broken, dump rendered_text as paragraphs
    if snapshot is None:
        story.append(section_gap())
        story.append(Paragraph("RESUME SNAPSHOT", SectionStyle))
        if isinstance(rendered_text, str) and rendered_text.strip():
            for line in rendered_text.splitlines():
                line = line.strip()
                if line:
                    story.append(Paragraph(line, Body))
        else:
            story.append(Paragraph("Resume data is missing or unreadable.", Body))
        doc.build(story)
        return filepath

    projects: List[Dict[str, Any]] = snapshot.get("projects") or []
    agg: Dict[str, Any] = snapshot.get("aggregated_skills") or {}

    # ---------------------------
    # PROFILE
    # ---------------------------
    story.append(section_gap())
    story.append(Paragraph("PROFILE", SectionStyle))
    story.append(Paragraph("To be updated later.", PlaceholderItalic))

    # ---------------------------
    # SKILLS
    # ---------------------------
    story.append(section_gap())
    story.append(Paragraph("SKILLS", SectionStyle))

    def add_skill_line(label: str, items: Any) -> None:
        clean = sorted(set(_clean_list(items)))
        if not clean:
            return
        story.append(Paragraph(f"<b>{label}:</b> {', '.join(clean)}", Body))

    languages = clean_languages_above_threshold(
        agg.get("languages") or [],
        min_pct=10,
    )

    add_skill_line("Languages", languages)

    add_skill_line("Frameworks", agg.get("frameworks") or [])
    add_skill_line("Technical skills", agg.get("technical_skills") or [])
    add_skill_line("Writing skills", agg.get("writing_skills") or [])

    # ---------------------------
    # PROJECTS
    # ---------------------------
    story.append(section_gap())
    story.append(Paragraph("PROJECTS", SectionStyle))

    def sort_key(p: Dict[str, Any]):
        return parse_date(p.get("end_date")) or parse_date(p.get("start_date")) or datetime.min

    projects_sorted = sorted(projects, key=sort_key, reverse=True)

    for p in projects_sorted:
        title = (
            p.get("resume_display_name_override")
            or p.get("manual_display_name")
            or p.get("project_name")
            or "Unnamed project"
        )
        role = (p.get("role") or "[Role]").strip()
        date_line = format_date_range(p.get("start_date"), p.get("end_date"))
        meta = f"{role} | {date_line}" if date_line else role

        story.append(Paragraph(str(title), ProjectTitleStyle))
        story.append(Paragraph(meta, MetaItalic))

        bullets = _clean_bullets(
            p.get("contribution_bullets")
            or p.get("resume_contributions_override")
            or p.get("manual_contribution_bullets")
            or []
        )

        if bullets:
            story.append(
                ListFlowable(
                    [ListItem(Paragraph(b, Body)) for b in bullets],
                    bulletType="bullet",
                    leftIndent=18,
                    bulletFontName="Helvetica",
                    bulletFontSize=10,
                )
            )
        else:
            story.append(
                ListFlowable(
                    [ListItem(Paragraph("(no contribution bullets available)", Body))],
                    bulletType="bullet",
                    leftIndent=18,
                )
            )

        story.append(Spacer(1, 10))

    # ---------------------------
    # EDUCATION & CERTIFICATES
    # ---------------------------
    story.append(section_gap())
    story.append(Paragraph("EDUCATION & CERTIFICATES", SectionStyle))
    story.append(Paragraph("To be updated later.", PlaceholderItalic))

    doc.build(story)
    return filepath
