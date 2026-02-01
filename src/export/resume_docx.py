"""
Export a saved resume snapshot (stored JSON) to a Word (.docx) document.

Output format:
- Name
- Contact
- Profile 
- Skills 
- Projects 
- Education & certificates

Some items are placeholders for now and will be updated later.

Saves to ./out/ (created if missing).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import re
from typing import Any, Dict, List, Optional

from docx import Document

from src.export.resume_helpers import (
    format_date_range,
    add_section_heading,
    add_placeholder,
    add_bullet,
    add_role_date_line,
    _project_sort_key,
    clean_languages_above_threshold
)

def _clean_str(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _clean_bullets(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    cleaned: List[str] = []
    for item in values:
        text = str(item).strip()
        if not text:
            continue
        if text.startswith(("-", "•")):
            text = text.lstrip("-•").strip()
        if text:
            cleaned.append(text)
    return cleaned


def _resume_display_name(p: Dict[str, Any]) -> str:
    resume_name = _clean_str(p.get("resume_display_name_override"))
    if resume_name:
        return resume_name
    manual_name = _clean_str(p.get("manual_display_name"))
    if manual_name:
        return manual_name
    return p.get("project_name") or "Unnamed project"


def _resume_summary_text(p: Dict[str, Any]) -> str | None:
    summary_override = _clean_str(p.get("resume_summary_override"))
    if summary_override:
        return summary_override
    manual_summary = _clean_str(p.get("manual_summary_text"))
    if manual_summary:
        return manual_summary
    return _clean_str(p.get("summary_text"))


def _resume_contribution_bullets(p: Dict[str, Any]) -> List[str]:
    resume_bullets = _clean_bullets(p.get("resume_contributions_override"))
    if resume_bullets:
        return resume_bullets
    manual_bullets = _clean_bullets(p.get("manual_contribution_bullets"))
    if manual_bullets:
        return manual_bullets
    return []


def _resume_key_role(p: Dict[str, Any]) -> str | None:
    """Resolve key role with priority: resume override → manual override → base."""
    resume_role = _clean_str(p.get("resume_key_role_override"))
    if resume_role:
        return resume_role
    manual_role = _clean_str(p.get("manual_key_role"))
    if manual_role:
        return manual_role
    return _clean_str(p.get("key_role"))


def _safe_slug(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "user"


def _add_bullet(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text, style="List Bullet")
    p.paragraph_format.space_after = 0


def export_resume_record_to_docx(
    *,
    username: str,
    record: Dict[str, Any],
    out_dir: str = "./out",
) -> Path:
    """
    record is the dict returned by get_resume_snapshot(...).
    Must contain resume_json (preferred) or rendered_text (fallback).
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    stamp_filename = now.strftime("%Y-%m-%d_%H-%M-%S")   
    stamp_display = now.strftime("%Y-%m-%d at %H:%M:%S") 
    
    filename = f"resume_{_safe_slug(username)}_{stamp_filename}.docx"
    filepath = out_path / filename

    doc = Document()
    # doc.add_heading(f"Resume — {username}", level=0)
    # doc.add_paragraph(f"Generated on {stamp_display}")

    doc.add_heading(username.upper(), level=0)
    doc.add_paragraph("Phone | Email | LinkedIn | Location")

    resume_json = record.get("resume_json")
    rendered_text = record.get("rendered_text")

    snapshot: Optional[Dict[str, Any]] = None
    if isinstance(resume_json, str) and resume_json.strip():
        try:
            snapshot = json.loads(resume_json)
        except Exception:
            snapshot = None

    # If JSON is broken, fall back to dumping rendered_text as plain paragraphs.
    if snapshot is None:
        doc.add_heading("Resume Snapshot", level=1)
        if isinstance(rendered_text, str) and rendered_text.strip():
            for line in rendered_text.splitlines():
                doc.add_paragraph(line)
        else:
            doc.add_paragraph("Resume data is missing or unreadable.")
        doc.save(str(filepath))
        return filepath

    projects: List[Dict[str, Any]] = snapshot.get("projects") or []
    agg: Dict[str, Any] = snapshot.get("aggregated_skills") or {}

    # ---------------------------
    # Skills Summary (FIRST)
    # ---------------------------

    # PROFILE (placeholder)
    add_section_heading(doc, "Profile")
    add_placeholder(doc, "To be updated later.")

    # SKILLS (same logic as before)
    add_section_heading(doc, "Skills")

    def add_skill_line(label: str, items: List[str]) -> None:
        clean = [str(x).strip() for x in items if str(x).strip()]
        if not clean:
            return
        doc.add_paragraph(f"{label}: {', '.join(sorted(set(clean)))}")

    languages = clean_languages_above_threshold(
        agg.get("languages") or [],
        min_pct=10,
    )

    add_skill_line("Languages", languages)

    add_skill_line("Frameworks", agg.get("frameworks") or [])
    add_skill_line("Technical skills", agg.get("technical_skills") or [])
    add_skill_line("Writing skills", agg.get("writing_skills") or [])

    projects_sorted = sorted(
        projects,
        key=_project_sort_key,
        reverse=True,  # most recent first
    )

    # PROJECTS (no code/text/individual/collaborative labels)
    add_section_heading(doc, "Projects")

    for p in projects_sorted:
        project_name = _resume_display_name(p)
        doc.add_heading(project_name, level=2)

        # Resolve key role with priority: resume override → manual override → base
        role = _resume_key_role(p) or "[Role]"

        date_line = format_date_range(p.get("start_date"), p.get("end_date"))
        add_role_date_line(doc, role, date_line)

        # bullets - priority: overrides first, then base contribution_bullets
        custom_bullets = _resume_contribution_bullets(p)
        contrib_bullets = _clean_bullets(p.get("contribution_bullets") or [])

        bullets_to_use: List[str] = []
        if custom_bullets:
            bullets_to_use = custom_bullets
        elif contrib_bullets:
            bullets_to_use = contrib_bullets
        else:
            if p.get("project_type") == "code":
                activities = p.get("activities") or []
                for act in activities:
                    name = act.get("name") or "activity"
                    top = act.get("top_file")
                    top_info = f" (top: {top})" if top else ""
                    bullets_to_use.append(f"{name}{top_info}")
            else:
                pct = p.get("contribution_percent")
                if isinstance(pct, (int, float)):
                    bullets_to_use.append(f"Contributed to {pct:.1f}% of document")

        for b in bullets_to_use:
            add_bullet(doc, str(b))

        doc.add_paragraph("")

    # Education & Certificates (placeholder)
    add_section_heading(doc, "Education & Certificates")
    add_placeholder(doc, "To be updated later.")

    doc.save(str(filepath))
    return filepath
