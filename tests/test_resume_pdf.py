import json
from pathlib import Path

import pytest
from pypdf import PdfReader

import src.export.resume_pdf as exp
import src.menu.resume.flow as flow


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


def test_resume_pdf_export_creates_valid_pdf(monkeypatch, tmp_path):
    class _FakeDatetime:
        @staticmethod
        def now():
            class _DT:
                def strftime(self, fmt: str) -> str:
                    if fmt == "%Y-%m-%d_%H-%M-%S":
                        return "2026-01-10_15-36-58"
                    return "2026-01-10_15-36-58"
            return _DT()

    monkeypatch.setattr(exp, "datetime", _FakeDatetime)

    snapshot = {
        "aggregated_skills": {
            "languages": ["Python"],
            "frameworks": [],
            "technical_skills": [],
            "writing_skills": [],
        },
        "projects": [
            {
                "project_name": "projA",
                "start_date": "2025-08-01",
                "end_date": "2025-11-01",
                "role": "[Role]",
                "contribution_bullets": ["Bullet A"],
            }
        ],
    }
    record = {"resume_json": json.dumps(snapshot), "rendered_text": "fallback"}

    out_dir = tmp_path / "out"
    path = exp.export_resume_record_to_pdf(username="john", record=record, out_dir=str(out_dir))

    assert path.exists()
    assert path.name == "resume_john_2026-01-10_15-36-58.pdf"

    raw = Path(path).read_bytes()
    assert raw[:4] == b"%PDF"
    assert len(raw) > 1000


@pytest.mark.pdf_text
def test_resume_pdf_contains_sections_and_orders_projects(monkeypatch, tmp_path):
    class _FakeDatetime:
        @staticmethod
        def now():
            class _DT:
                def strftime(self, fmt: str) -> str:
                    if fmt == "%Y-%m-%d_%H-%M-%S":
                        return "2026-01-10_15-36-58"
                    return "2026-01-10_15-36-58"
            return _DT()

    monkeypatch.setattr(exp, "datetime", _FakeDatetime)

    snapshot = {
        "aggregated_skills": {
            "languages": ["Python"],
            "frameworks": [],
            "technical_skills": [],
            "writing_skills": [],
        },
        "projects": [
            {
                "project_name": "older",
                "start_date": "2024-01-01",
                "end_date": "2024-02-01",
                "role": "[Role]",
                "contribution_bullets": ["Old bullet"],
            },
            {
                "project_name": "newer",
                "start_date": "2025-08-01",
                "end_date": "2025-11-01",
                "role": "[Role]",
                "contribution_bullets": ["New bullet"],
            },
        ],
    }
    record = {"resume_json": json.dumps(snapshot), "rendered_text": "fallback"}

    user_profile = {
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

    out_dir = tmp_path / "out"
    path = exp.export_resume_record_to_pdf(
        username="john",
        record=record,
        out_dir=str(out_dir),
        user_profile=user_profile,
        education_entries=education_entries,
    )

    text = _pdf_text(path)
    link_targets = _pdf_link_targets(path)

    # section headings
    assert "PROFILE" in text
    assert "SKILLS" in text
    assert "PROJECTS" in text
    assert "EDUCATION" in text
    assert "CERTIFICATES" in text
    assert "EDUCATION & CERTIFICATES" not in text

    # profile/contact info
    assert "1234567890" in text
    assert "john@example.com" in text
    assert "LinkedIn" in text
    assert "GitHub" in text
    assert "Kelowna, BC" in text
    assert "Software and data student building practical tools." in text

    # education content
    assert "BSc in Computer Science" in text
    assert "UBCO" in text
    assert "AWS Cloud Practitioner" in text
    assert "Amazon Web Services" in text

    # URLs should exist as real PDF links, not as visible text
    assert "https://linkedin.com/in/john" in link_targets
    assert "https://github.com/john" in link_targets
    assert "https://linkedin.com/in/john" not in text
    assert "https://github.com/john" not in text

    # ordering by recency: newer should appear before older
    assert text.find("newer") < text.find("older")


@pytest.mark.pdf_text
def test_resume_pdf_omits_contact_profile_and_education_sections_when_empty(monkeypatch, tmp_path):
    class _FakeDatetime:
        @staticmethod
        def now():
            class _DT:
                def strftime(self, fmt: str) -> str:
                    if fmt == "%Y-%m-%d_%H-%M-%S":
                        return "2026-01-10_15-36-58"
                    return "2026-01-10_15-36-58"
            return _DT()

    monkeypatch.setattr(exp, "datetime", _FakeDatetime)

    snapshot = {
        "aggregated_skills": {
            "languages": ["Python"],
            "frameworks": [],
            "technical_skills": [],
            "writing_skills": [],
        },
        "projects": [
            {
                "project_name": "projA",
                "start_date": "2025-08-01",
                "end_date": "2025-11-01",
                "contribution_bullets": ["Bullet A"],
            }
        ],
    }
    record = {"resume_json": json.dumps(snapshot), "rendered_text": "fallback"}

    empty_profile = {
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
        "location": None,
        "profile_text": None,
    }

    out_dir = tmp_path / "out"
    path = exp.export_resume_record_to_pdf(
        username="john",
        record=record,
        out_dir=str(out_dir),
        user_profile=empty_profile,
        education_entries=[],
    )

    text = _pdf_text(path)
    link_targets = _pdf_link_targets(path)

    assert "SKILLS" in text
    assert "PROJECTS" in text

    assert "PROFILE" not in text
    assert "EDUCATION" not in text
    assert "CERTIFICATES" not in text
    assert "john@example.com" not in text
    assert "1234567890" not in text
    assert "LinkedIn" not in text
    assert "GitHub" not in text
    assert "Kelowna, BC" not in text

    assert all("linkedin.com" not in target for target in link_targets)
    assert all("github.com" not in target for target in link_targets)


@pytest.mark.pdf_text
def test_resume_pdf_shows_only_education_section_when_only_education_entries_exist(monkeypatch, tmp_path):
    class _FakeDatetime:
        @staticmethod
        def now():
            class _DT:
                def strftime(self, fmt: str) -> str:
                    return "2026-01-10_15-36-58"
            return _DT()

    monkeypatch.setattr(exp, "datetime", _FakeDatetime)

    snapshot = {
        "aggregated_skills": {},
        "projects": [],
    }
    record = {"resume_json": json.dumps(snapshot), "rendered_text": ""}

    education_entries = [
        {
            "entry_id": 1,
            "entry_type": "education",
            "title": "BSc in Computer Science",
            "organization": "UBCO",
            "date_text": "2022 - 2026",
            "description": "Major in data science.",
        },
    ]

    out_dir = tmp_path / "out"
    path = exp.export_resume_record_to_pdf(
        username="john",
        record=record,
        out_dir=str(out_dir),
        education_entries=education_entries,
    )

    text = _pdf_text(path)

    assert "EDUCATION" in text
    assert "BSc in Computer Science" in text
    assert "CERTIFICATES" not in text


def test_resume_export_pdf_cancel_invalid_selection(monkeypatch, capsys):
    """
    Covers:
    - Cancel on Enter
    - Invalid index selection
    - Ensures PDF export is not called
    """
    resumes = [
        {"id": 1, "name": "Resume A", "created_at": "2026-01-01"},
        {"id": 2, "name": "Resume B", "created_at": "2026-01-02"},
    ]

    monkeypatch.setattr(flow, "list_resumes", lambda conn, user_id: resumes)
    monkeypatch.setattr(
        flow,
        "get_resume_snapshot",
        lambda conn, user_id, rid: {"resume_json": "{}", "rendered_text": ""},
    )

    def fail_export(**kwargs):
        raise AssertionError("PDF export should not be called")

    monkeypatch.setattr(flow, "export_resume_record_to_pdf", fail_export)

    # cancel
    monkeypatch.setattr("builtins.input", lambda _: "")
    ok = flow._handle_export_resume_pdf(conn=None, user_id=1, username="john")
    out = capsys.readouterr().out

    assert ok is False
    assert "Cancelled" in out

    # invalid index
    monkeypatch.setattr("builtins.input", lambda _: "999")
    ok = flow._handle_export_resume_pdf(conn=None, user_id=1, username="john")
    out = capsys.readouterr().out

    assert ok is False
    assert "Invalid selection" in out


@pytest.mark.pdf_text
def test_resume_pdf_export_uses_key_role(monkeypatch, tmp_path):
    """Test that PDF export uses resolved key_role instead of [Role] placeholder."""
    class _FakeDatetime:
        @staticmethod
        def now():
            class _DT:
                def strftime(self, fmt: str) -> str:
                    return "2026-01-10_15-36-58"
            return _DT()

    monkeypatch.setattr(exp, "datetime", _FakeDatetime)

    snapshot = {
        "aggregated_skills": {},
        "projects": [
            {
                "project_name": "test_project",
                "key_role": "Backend Developer",
                "start_date": "2025-01-01",
                "end_date": "2025-06-01",
                "contribution_bullets": ["Built API endpoints"],
            },
        ],
    }

    record = {"resume_json": json.dumps(snapshot), "rendered_text": ""}
    out_dir = tmp_path / "out"
    path = exp.export_resume_record_to_pdf(username="jane", record=record, out_dir=str(out_dir))

    text = _pdf_text(path)
    assert "Backend Developer" in text
    assert "[Role]" not in text


@pytest.mark.pdf_text
def test_resume_pdf_export_key_role_override_priority(monkeypatch, tmp_path):
    """Test that resume_key_role_override takes priority over base key_role in PDF."""
    class _FakeDatetime:
        @staticmethod
        def now():
            class _DT:
                def strftime(self, fmt: str) -> str:
                    return "2026-01-10_15-36-58"
            return _DT()

    monkeypatch.setattr(exp, "datetime", _FakeDatetime)

    snapshot = {
        "aggregated_skills": {},
        "projects": [
            {
                "project_name": "test_project",
                "key_role": "Developer",
                "manual_key_role": "Senior Developer",
                "resume_key_role_override": "Lead Developer",
                "start_date": "2025-01-01",
                "end_date": "2025-06-01",
                "contribution_bullets": ["Led team"],
            },
        ],
    }

    record = {"resume_json": json.dumps(snapshot), "rendered_text": ""}
    out_dir = tmp_path / "out"
    path = exp.export_resume_record_to_pdf(username="jane", record=record, out_dir=str(out_dir))

    text = _pdf_text(path)
    assert "Lead Developer" in text
    assert "[Role]" not in text