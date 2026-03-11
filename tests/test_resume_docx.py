import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import src.export.resume_docx as exp


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def _doc_text(path: Path) -> str:
    with zipfile.ZipFile(path, "r") as zf:
        xml_bytes = zf.read("word/document.xml")

    root = ET.fromstring(xml_bytes)
    paragraphs = []
    for p in root.iter(f"{{{W_NS}}}p"):
        text = "".join(node.text or "" for node in p.iter(f"{{{W_NS}}}t")).strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def _docx_hyperlink_targets(path: Path) -> list[str]:
    with zipfile.ZipFile(path, "r") as zf:
        rels_bytes = zf.read("word/_rels/document.xml.rels")

    root = ET.fromstring(rels_bytes)
    targets = []
    for rel in root.iter(f"{{{R_NS}}}Relationship"):
        target = rel.attrib.get("Target")
        if target:
            targets.append(target)
    return targets


class _FakeDatetime:
    @staticmethod
    def now():
        class _DT:
            def strftime(self, fmt: str) -> str:
                return "2026-01-10_15-36-58"
        return _DT()


def test_resume_docx_sections_happy_path(monkeypatch, tmp_path):
    """
    Covers PR 2 happy path:
    - full_name still used
    - hyperlinks still work
    - section order is:
      Profile -> Education -> Skills -> Experience -> Projects -> Certificates
    - education / experience / certificate content render
    """
    monkeypatch.setattr(exp, "datetime", _FakeDatetime)

    snapshot = {
        "aggregated_skills": {
            "languages": ["Python 88%"],
            "frameworks": ["FastAPI"],
            "technical_skills": ["Algorithms"],
            "writing_skills": ["Clear communication"],
        },
        "projects": [
            {
                "project_name": "Capstone Project",
                "start_date": "2025-01-01",
                "end_date": "2025-06-01",
                "contribution_bullets": ["Built API endpoints"],
            },
        ],
    }

    record = {"resume_json": json.dumps(snapshot), "rendered_text": ""}
    user_profile = {
        "full_name": "John Tan",
        "email": "john@example.com",
        "phone": "1234567890",
        "linkedin": "https://linkedin.com/in/john",
        "github": "https://github.com/john",
        "location": "Kelowna, BC",
        "profile_text": "Software and data student building practical tools.",
    }
    education_entries = [
        {
            "entry_id": 1,
            "entry_type": "education",
            "title": "BSc in Computer Science",
            "organization": "UBCO",
            "date_text": "2022 - 2026",
            "description": "Major in data science.",
        },
        {
            "entry_id": 2,
            "entry_type": "certificate",
            "title": "AWS Cloud Practitioner",
            "organization": "Amazon Web Services",
            "date_text": "2025",
            "description": "Foundational cloud certification.",
        },
    ]
    experience_entries = [
        {
            "entry_id": 10,
            "role": "Data Science Intern",
            "company": "PETRONAS",
            "date_text": "May 2025 - Aug 2025",
            "description": "Built analytics workflows and dashboards.",
        }
    ]

    path = exp.export_resume_record_to_docx(
        username="john123",
        record=record,
        out_dir=str(tmp_path / "out"),
        user_profile=user_profile,
        education_entries=education_entries,
        experience_entries=experience_entries,
    )

    txt = _doc_text(path)
    hyperlink_targets = _docx_hyperlink_targets(path)

    assert "JOHN TAN" in txt
    assert "john@example.com" in txt
    assert "LinkedIn" in txt
    assert "GitHub" in txt
    assert "PROFILE" in txt
    assert "EDUCATION" in txt
    assert "SKILLS" in txt
    assert "EXPERIENCE" in txt
    assert "PROJECTS" in txt
    assert "CERTIFICATES" in txt

    idx_profile = txt.find("PROFILE")
    idx_education = txt.find("EDUCATION")
    idx_skills = txt.find("SKILLS")
    idx_experience = txt.find("EXPERIENCE")
    idx_projects = txt.find("PROJECTS")
    idx_certificates = txt.find("CERTIFICATES")
    assert idx_profile < idx_education < idx_skills < idx_experience < idx_projects < idx_certificates

    assert "https://linkedin.com/in/john" in hyperlink_targets
    assert "https://github.com/john" in hyperlink_targets
    assert "https://linkedin.com/in/john" not in txt
    assert "https://github.com/john" not in txt

    assert "BSc in Computer Science" in txt
    assert "UBCO" in txt
    assert "Data Science Intern" in txt
    assert "PETRONAS" in txt
    assert "Capstone Project" in txt
    assert "AWS Cloud Practitioner" in txt


def test_resume_docx_omits_empty_sections(monkeypatch, tmp_path):
    """
    Covers omission behavior:
    - falls back to username
    - hides profile / education / experience / certificates when empty
    """
    monkeypatch.setattr(exp, "datetime", _FakeDatetime)

    snapshot = {
        "aggregated_skills": {},
        "projects": [],
    }

    record = {"resume_json": json.dumps(snapshot), "rendered_text": ""}
    empty_profile = {
        "full_name": None,
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
        "location": None,
        "profile_text": None,
    }

    path = exp.export_resume_record_to_docx(
        username="john123",
        record=record,
        out_dir=str(tmp_path / "out"),
        user_profile=empty_profile,
        education_entries=[],
        experience_entries=[],
    )

    txt = _doc_text(path)

    assert "JOHN123" in txt
    assert "PROFILE" not in txt
    assert "EDUCATION" not in txt
    assert "EXPERIENCE" not in txt
    assert "CERTIFICATES" not in txt