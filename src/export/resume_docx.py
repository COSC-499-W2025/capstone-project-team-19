"""
Export a saved resume snapshot (stored JSON) to a Word (.docx) document.

Output format:
- Title
- Skills Summary (first)
- Projects grouped by: code/text × individual/collaborative
- Each project rendered in a consistent block with bullets for contributions and skills.
Saves to ./out/ (created if missing).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import re
from typing import Any, Dict, List, Optional

from docx import Document


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
    doc.add_heading(f"Resume — {username}", level=0)
    doc.add_paragraph(f"Generated on {stamp_display}")

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
    doc.add_heading("Skills Summary", level=1)

    def add_skill_line(label: str, items: List[str]) -> None:
        clean = [str(x).strip() for x in items if str(x).strip()]
        if not clean:
            return
        # Render as a single line
        doc.add_paragraph(f"{label}: {', '.join(sorted(set(clean)))}")

    add_skill_line("Languages", agg.get("languages") or [])
    add_skill_line("Frameworks", agg.get("frameworks") or [])
    add_skill_line("Technical skills", agg.get("technical_skills") or [])
    add_skill_line("Writing skills", agg.get("writing_skills") or [])

    doc.add_paragraph("")  # spacing before projects

    # ---------------------------
    # Projects grouped
    # ---------------------------
    groups = [
        ("code", "individual", "Code — Individual"),
        ("code", "collaborative", "Code — Collaborative"),
        ("text", "individual", "Text — Individual"),
        ("text", "collaborative", "Text — Collaborative"),
    ]

    for ptype, pmode, header in groups:
        group_entries = [
            p for p in projects
            if p.get("project_type") == ptype and p.get("project_mode") == pmode
        ]
        if not group_entries:
            continue

        doc.add_heading(header, level=1)

        for p in group_entries:
            project_name = _resume_display_name(p)
            doc.add_heading(project_name, level=2)

            # Languages / Frameworks
            langs = p.get("languages") or []
            fws = p.get("frameworks") or []
            if langs:
                doc.add_paragraph(f"Languages: {', '.join(sorted(set(langs)))}")
            if fws:
                doc.add_paragraph(f"Frameworks: {', '.join(sorted(set(fws)))}")

            # Text type line
            if ptype == "text":
                doc.add_paragraph(f"Type: {p.get('text_type', 'Text')}")

            # Summary
            summary_text = _resume_summary_text(p)
            if summary_text:
                doc.add_paragraph(f"Summary: {summary_text}")

            # Contributions
            contrib_bullets = p.get("contribution_bullets") or []
            if contrib_bullets:
                doc.add_paragraph("Contributions:")
                for b in contrib_bullets:
                    _add_bullet(doc, str(b))
            custom_bullets = _resume_contribution_bullets(p)
            if custom_bullets:
                doc.add_paragraph("Contributions:")
                for bullet in custom_bullets:
                    _add_bullet(doc, bullet)
            elif ptype == "code":
                activities = p.get("activities") or []
                if activities:
                    doc.add_paragraph("Contributions:")
                    for act in activities:
                        name = act.get("name") or "activity"
                        top = act.get("top_file")
                        top_info = f" (top: {top})" if top else ""
                        _add_bullet(doc, f"{name}{top_info}")
                else:
                    doc.add_paragraph("Contributions: (no activity data)")
            else:
                # Fallback for older snapshots (no contribution_bullets saved)
                if ptype == "code":
                    activities = p.get("activities") or []
                    if activities:
                        doc.add_paragraph("Contributions:")
                        for act in activities:
                            name = act.get("name") or "activity"
                            top = act.get("top_file")
                            top_info = f" (top: {top})" if top else ""
                            _add_bullet(doc, f"{name}{top_info}")
                    else:
                        doc.add_paragraph("Contributions: (no activity data)")
                else:
                    pct = p.get("contribution_percent")
                    if isinstance(pct, (int, float)):
                        doc.add_paragraph(f"Contribution: {pct:.1f}% of document")

            # Skills
            skills = p.get("skills") or []
            clean_skills = [str(s).strip() for s in skills if str(s).strip()]
            if clean_skills:
                doc.add_paragraph("Skills:")
                # render as bullets (cleaner than one long comma line)
                for s in clean_skills:
                    _add_bullet(doc, s)

            doc.add_paragraph("")  # spacing between projects

    doc.save(str(filepath))
    return filepath
