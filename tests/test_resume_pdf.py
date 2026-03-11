import json
from pathlib import Path

import pytest
from pypdf import PdfReader

import src.export.resume_pdf as exp


def _pdf_text(path):
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _pdf_link_targets(path):
    reader = PdfReader(str(path))
    targets = []

    for page in reader.pages:
        annots = page.get("/Annots") or []
        for annot_ref in annots:
            annot = annot_ref.get_object()
            action = annot.get("/A")
            if action and action.get("/URI"):
                targets.append(str(action["/URI"]))

    return targets


class _FakeDatetime:
    @staticmethod
    def now():
        class _DT:
            def strftime(self, fmt: str) -> str:
                return "2026-01-10_15-36-58"
        return _DT()


@pytest.mark.pdf_text
def test_resume_pdf_sections_happy_path(monkeypatch, tmp_path):
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
            "languages": ["Python"],
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

    path = exp.export_resume_record_to_pdf(
        username="john123",
        record=record,
        out_dir=str(tmp_path / "out"),
        user_profile=user_profile,
        education_entries=education_entries,
        experience_entries=experience_entries,
    )

    text = _pdf_text(path)
    link_targets = _pdf_link_targets(path)

    assert "JOHN TAN" in text
    assert "john@example.com" in text
    assert "LinkedIn" in text
    assert "GitHub" in text
    assert "PROFILE" in text
    assert "EDUCATION" in text
    assert "SKILLS" in text
    assert "EXPERIENCE" in text
    assert "PROJECTS" in text
    assert "CERTIFICATES" in text

    idx_profile = text.find("PROFILE")
    idx_education = text.find("EDUCATION")
    idx_skills = text.find("SKILLS")
    idx_experience = text.find("EXPERIENCE")
    idx_projects = text.find("PROJECTS")
    idx_certificates = text.find("CERTIFICATES")
    assert idx_profile < idx_education < idx_skills < idx_experience < idx_projects < idx_certificates

    assert "https://linkedin.com/in/john" in link_targets
    assert "https://github.com/john" in link_targets
    assert "https://linkedin.com/in/john" not in text
    assert "https://github.com/john" not in text

    assert "BSc in Computer Science" in text
    assert "UBCO" in text
    assert "Data Science Intern" in text
    assert "PETRONAS" in text
    assert "Capstone Project" in text
    assert "AWS Cloud Practitioner" in text


@pytest.mark.pdf_text
def test_resume_pdf_omits_empty_sections(monkeypatch, tmp_path):
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

    path = exp.export_resume_record_to_pdf(
        username="john123",
        record=record,
        out_dir=str(tmp_path / "out"),
        user_profile=empty_profile,
        education_entries=[],
        experience_entries=[],
    )

    text = _pdf_text(path)

    assert "JOHN123" in text
    assert "PROFILE" not in text
    assert "EDUCATION" not in text
    assert "EXPERIENCE" not in text
    assert "CERTIFICATES" not in text