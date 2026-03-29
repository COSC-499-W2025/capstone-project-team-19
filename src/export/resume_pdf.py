# src/export/resume_pdf.py
"""
Export a saved resume snapshot (stored JSON) directly to a PDF using ReportLab (Platypus).

Layout:
- Name (largest)
- line between name and contact
- Contact line
- Profile (only shown if populated)
- Education
- Skills
- Experience
- Projects
- Certificates

Sections are only shown when they have content.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from xml.sax.saxutils import escape

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

from src.export.resume_helpers import (
    format_date_range,
    parse_date,
    clean_languages_above_threshold,
    filter_skills_by_highlighted,
)

from src.db import (
    get_contact_parts,
    get_visible_profile_text,
    get_resume_name,
)


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


def _clean_str(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _resume_key_role(p: Dict[str, Any]) -> str | None:
    resume_role = _clean_str(p.get("resume_key_role_override"))
    if resume_role:
        return resume_role
    manual_role = _clean_str(p.get("manual_key_role"))
    if manual_role:
        return manual_role
    return _clean_str(p.get("key_role"))


def _pdf_contact_html(profile: Dict[str, Any]) -> str | None:
    parts = get_contact_parts(profile)
    chunks: List[str] = []

    if parts["phone"]:
        chunks.append(escape(parts["phone"]))
    if parts["email"]:
        chunks.append(escape(parts["email"]))
    if parts["linkedin"]:
        chunks.append(f'<link href="{escape(parts["linkedin"])}">LinkedIn</link>')
    if parts["github"]:
        chunks.append(f'<link href="{escape(parts["github"])}">GitHub</link>')
    if parts["location"]:
        chunks.append(escape(parts["location"]))

    if not chunks:
        return None

    return " | ".join(chunks)


def _render_education_block(
    story: List[Any],
    entries: List[Dict[str, Any]],
    project_title_style: ParagraphStyle,
    meta_italic: ParagraphStyle,
    body: ParagraphStyle,
) -> None:
    for entry in entries:
        title = entry.get("title") or "Untitled"
        story.append(Paragraph(escape(str(title)), project_title_style))

        details = []
        if entry.get("organization"):
            details.append(str(entry["organization"]).strip())
        if entry.get("date_text"):
            details.append(str(entry["date_text"]).strip())

        if details:
            story.append(Paragraph(escape(" | ".join(details)), meta_italic))

        description = _clean_str(entry.get("description"))
        if description:
            story.append(Paragraph(escape(description), body))

        story.append(Spacer(1, 10))


def _render_experience_block(
    story: List[Any],
    entries: List[Dict[str, Any]],
    project_title_style: ParagraphStyle,
    meta_italic: ParagraphStyle,
    body: ParagraphStyle,
) -> None:
    for entry in entries:
        role = entry.get("role") or "Untitled role"
        story.append(Paragraph(escape(str(role)), project_title_style))

        details = []
        if entry.get("company"):
            details.append(str(entry["company"]).strip())
        if entry.get("date_text"):
            details.append(str(entry["date_text"]).strip())

        if details:
            story.append(Paragraph(escape(" | ".join(details)), meta_italic))

        description = _clean_str(entry.get("description"))
        if description:
            story.append(Paragraph(escape(description), body))

        story.append(Spacer(1, 10))


def export_resume_record_to_pdf(
    *,
    username: str,
    record: Dict[str, Any],
    out_dir: str = "./out",
    highlighted_skills: Optional[List[str]] = None,
    highlighted_skills_by_project: Optional[Dict[str, List[str]]] = None,
    user_profile: Optional[Dict[str, Any]] = None,
    education_entries: Optional[List[Dict[str, Any]]] = None,
    experience_entries: Optional[List[Dict[str, Any]]] = None,
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

    profile = user_profile or {}
    education_entries = education_entries or []
    experience_entries = experience_entries or []
    display_name = get_resume_name(profile, username)

    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=LETTER,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
        title=f"Resume - {display_name}",
        author=display_name,
    )

    styles = getSampleStyleSheet()

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

    def rule() -> HRFlowable:
        return HRFlowable(width="100%", thickness=0.8, lineCap="round", spaceBefore=6, spaceAfter=10)

    def section_gap() -> Spacer:
        return Spacer(1, 14)

    story: List[Any] = []

    story.append(Paragraph(display_name.upper(), NameStyle))
    story.append(rule())

    contact_html = _pdf_contact_html(profile)
    if contact_html:
        story.append(Paragraph(contact_html, ContactStyle))

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

    profile_text = get_visible_profile_text(profile)
    if profile_text:
        story.append(section_gap())
        story.append(Paragraph("PROFILE", SectionStyle))
        story.append(Paragraph(escape(profile_text), Body))

    education_only = [e for e in education_entries if e.get("entry_type") == "education"]
    certificate_only = [e for e in education_entries if e.get("entry_type") == "certificate"]

    if education_only:
        story.append(section_gap())
        story.append(Paragraph("EDUCATION", SectionStyle))
        _render_education_block(story, education_only, ProjectTitleStyle, MetaItalic, Body)

    def add_skill_line(label: str, items: Any) -> None:
        clean = sorted(set(_clean_list(items)))
        if not clean:
            return
        story.append(Paragraph(f"<b>{label}:</b> {', '.join(clean)}", Body))

    languages = clean_languages_above_threshold(
        agg.get("languages") or [],
        min_pct=10,
    )

    effective_highlighted = highlighted_skills
    if highlighted_skills_by_project is not None:
        all_hl: set = set()
        for sl in highlighted_skills_by_project.values():
            all_hl.update(sl)
        effective_highlighted = list(all_hl)

    tech_skills = filter_skills_by_highlighted(
        agg.get("technical_skills") or [],
        effective_highlighted,
    )
    writing_skills = filter_skills_by_highlighted(
        agg.get("writing_skills") or [],
        effective_highlighted,
    )

    story.append(section_gap())
    story.append(Paragraph("TECHNICAL SKILLS", SectionStyle))
    add_skill_line("Languages", languages)
    add_skill_line("Technical", tech_skills)
    add_skill_line("Writing", writing_skills)

    if experience_entries:
        story.append(section_gap())
        story.append(Paragraph("EXPERIENCE", SectionStyle))
        _render_experience_block(story, experience_entries, ProjectTitleStyle, MetaItalic, Body)

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
        role = _resume_key_role(p) or "[Role]"
        date_line = format_date_range(p.get("start_date"), p.get("end_date"))
        meta = f"{role} | {date_line}" if date_line else role

        story.append(Paragraph(str(title), ProjectTitleStyle))
        story.append(Paragraph(meta, MetaItalic))

        bullets = _clean_bullets(
            p.get("resume_contributions_override")
            or p.get("manual_contribution_bullets")
            or p.get("contribution_bullets")
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

    if certificate_only:
        story.append(section_gap())
        story.append(Paragraph("CERTIFICATES", SectionStyle))
        _render_education_block(story, certificate_only, ProjectTitleStyle, MetaItalic, Body)

    doc.build(story)
    return filepath