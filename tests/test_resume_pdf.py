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
def test_resume_pdf_profile_happy_path(monkeypatch, tmp_path):
    """
    Covers PR 1 happy path:
    - full_name is used instead of username
    - profile/contact info render
    - LinkedIn/GitHub render as labels with hyperlink targets
    - profile section shows when populated
    """
    monkeypatch.setattr(exp, "datetime", _FakeDatetime)

    snapshot = {
        "aggregated_skills": {
            "languages": ["Python"],
            "frameworks": ["FastAPI"],
            "technical_skills": ["Algorithms"],
            "writing_skills": [],
        },
        "projects": [
            {
                "project_name": "test_project",
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

    path = exp.export_resume_record_to_pdf(
        username="john123",
        record=record,
        out_dir=str(tmp_path / "out"),
        user_profile=user_profile,
    )

    text = _pdf_text(path)
    link_targets = _pdf_link_targets(path)

    assert "JOHN TAN" in text
    assert "john@example.com" in text
    assert "1234567890" in text
    assert "LinkedIn" in text
    assert "GitHub" in text
    assert "Kelowna, BC" in text
    assert "PROFILE" in text
    assert "Software and data student building practical tools." in text

    assert "https://linkedin.com/in/john" in link_targets
    assert "https://github.com/john" in link_targets
    assert "https://linkedin.com/in/john" not in text
    assert "https://github.com/john" not in text


@pytest.mark.pdf_text
def test_resume_pdf_profile_omits_empty_fields(monkeypatch, tmp_path):
    """
    Covers PR 1 omission behavior:
    - falls back to username when full_name missing
    - contact line is omitted when fields are empty
    - profile section is omitted when profile_text is empty
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
    )

    text = _pdf_text(path)
    link_targets = _pdf_link_targets(path)

    assert "JOHN123" in text
    assert "PROFILE" not in text
    assert "john@example.com" not in text
    assert "1234567890" not in text
    assert "LinkedIn" not in text
    assert "GitHub" not in text
    assert "Kelowna, BC" not in text

    assert all("linkedin.com" not in target for target in link_targets)
    assert all("github.com" not in target for target in link_targets)