import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import pytest
import src.export.resume_docx as exp
import src.menu.resume.flow as flow


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


def test_resume_export_happy_json_structure_and_order(monkeypatch, tmp_path):
    """
    Covers:
    - deterministic filename via frozen datetime
    - structure/order:
      Name -> Contact -> PROFILE -> EDUCATION -> SKILLS -> EXPERIENCE -> PROJECTS -> CERTIFICATES
    - projects sorted by most-recent end_date/start_date first
    - LinkedIn/GitHub shown as labels, with real hyperlink targets in the docx
    - education, experience, and certificate entries render in the correct sections
    """
    class _FakeDatetime:
        @staticmethod
        def now():
            class _DT:
                def strftime(self, fmt: str) -> str:
                    if fmt == "%Y-%m-%d_%H-%M-%S":
                        return "2026-01-10_15-36-58"
                    if fmt == "%Y-%m-%d at %H:%M:%S":
                        return "2026-01-10 at 15:36:58"
                    return "2026-01-10_15-36-58"
            return _DT()

    monkeypatch.setattr(exp, "datetime", _FakeDatetime)

    snapshot = {
        "aggregated_skills": {
            "languages": ["Python 88%", "SQL 12%"],
            "frameworks": ["FastAPI"],
            "technical_skills": ["Algorithms"],
            "writing_skills": ["Clear communication"],
        },
        "projects": [
            {
                "project_name": "older_project",
                "role": "[Role]",
                "start_date": "2024-12-01",
                "end_date": "2024-12-31",
                "contribution_bullets": ["Old bullet A"],
            },
            {
                "project_name": "newer_project",
                "role": "[Role]",
                "start_date": "2025-08-01",
                "end_date": "2025-11-01",
                "contribution_bullets": ["New bullet A", "New bullet B"],
            },
        ],
    }

    record = {"resume_json": json.dumps(snapshot), "rendered_text": "fallback"}
    out_dir = tmp_path / "out"

    user_profile = {
        "full_name": None,
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
        username="john",
        record=record,
        out_dir=str(out_dir),
        user_profile=user_profile,
        education_entries=education_entries,
        experience_entries=experience_entries,
    )

    assert out_dir.exists()
    assert path.exists()
    assert path.name == "resume_john_2026-01-10_15-36-58.docx"

    txt = _doc_text(path)
    hyperlink_targets = _docx_hyperlink_targets(path)

    assert "john" in txt.lower()

    # Contact line pieces appear as visible text
    assert "1234567890" in txt
    assert "john@example.com" in txt
    assert "LinkedIn" in txt
    assert "GitHub" in txt
    assert "Kelowna, BC" in txt

    # URLs should be hyperlink targets, not visible text
    assert "https://linkedin.com/in/john" in hyperlink_targets
    assert "https://github.com/john" in hyperlink_targets
    assert "https://linkedin.com/in/john" not in txt
    assert "https://github.com/john" not in txt

    # Required sections exist
    assert "PROFILE" in txt
    assert "EDUCATION" in txt
    assert "SKILLS" in txt
    assert "EXPERIENCE" in txt
    assert "PROJECTS" in txt
    assert "CERTIFICATES" in txt
    assert "EDUCATION & CERTIFICATES" not in txt

    # Order: PROFILE -> EDUCATION -> SKILLS -> EXPERIENCE -> PROJECTS -> CERTIFICATES
    idx_profile = txt.find("PROFILE")
    idx_education = txt.find("EDUCATION")
    idx_skills = txt.find("SKILLS")
    idx_experience = txt.find("EXPERIENCE")
    idx_projects = txt.find("PROJECTS")
    idx_certificates = txt.find("CERTIFICATES")
    assert -1 not in (idx_profile, idx_education, idx_skills, idx_experience, idx_projects, idx_certificates)
    assert idx_profile < idx_education < idx_skills < idx_experience < idx_projects < idx_certificates

    # Profile paragraph rendered
    assert "Software and data student building practical tools." in txt

    # Skills lines rendered
    assert "Languages:" in txt
    assert ("Python" in txt) and ("SQL" in txt)
    assert "Frameworks:" in txt
    assert "FastAPI" in txt
    assert "Technical skills:" in txt
    assert "Algorithms" in txt
    assert "Writing skills:" in txt
    assert "Clear communication" in txt

    # Experience content
    assert "Data Science Intern" in txt
    assert "PETRONAS" in txt
    assert "May 2025 - Aug 2025" in txt
    assert "Built analytics workflows and dashboards." in txt

    # Projects content
    assert "newer_project" in txt
    assert "older_project" in txt
    assert "[Role]" in txt

    # Contributions bullets appear
    assert "New bullet A" in txt
    assert "New bullet B" in txt
    assert "Old bullet A" in txt

    # Sorting check: newer should appear before older
    assert txt.find("newer_project") < txt.find("older_project")

    # Education + certificate content
    assert "BSc in Computer Science" in txt
    assert "UBCO" in txt
    assert "2022 - 2026" in txt
    assert "Major in data science." in txt

    assert "AWS Cloud Practitioner" in txt
    assert "Amazon Web Services" in txt
    assert "Foundational cloud certification." in txt

    # Optional: verify years appear somewhere
    assert "2025" in txt and "2024" in txt


def test_resume_export_omits_contact_line_profile_education_experience_and_certificate_sections_when_empty(monkeypatch, tmp_path):
    """
    Covers:
    - empty standalone profile should not render contact info
    - PROFILE section should be omitted when profile_text is empty
    - EDUCATION / EXPERIENCE / CERTIFICATES should be omitted when no entries exist
    """
    class _FakeDatetime:
        @staticmethod
        def now():
            class _DT:
                def strftime(self, fmt: str) -> str:
                    if fmt == "%Y-%m-%d_%H-%M-%S":
                        return "2026-01-10_15-36-58"
                    if fmt == "%Y-%m-%d at %H:%M:%S":
                        return "2026-01-10 at 15:36:58"
                    return "2026-01-10_15-36-58"
            return _DT()

    monkeypatch.setattr(exp, "datetime", _FakeDatetime)

    snapshot = {
        "aggregated_skills": {
            "languages": ["Python 88%"],
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
    out_dir = tmp_path / "out"

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
        username="john",
        record=record,
        out_dir=str(out_dir),
        user_profile=empty_profile,
        education_entries=[],
        experience_entries=[],
    )

    txt = _doc_text(path)
    hyperlink_targets = _docx_hyperlink_targets(path)

    assert "john" in txt.lower()
    assert "SKILLS" in txt
    assert "PROJECTS" in txt

    assert "PROFILE" not in txt
    assert "EDUCATION" not in txt
    assert "EXPERIENCE" not in txt
    assert "CERTIFICATES" not in txt
    assert "john@example.com" not in txt
    assert "1234567890" not in txt
    assert "LinkedIn" not in txt
    assert "GitHub" not in txt
    assert "Kelowna, BC" not in txt

    assert all("linkedin.com" not in target for target in hyperlink_targets)
    assert all("github.com" not in target for target in hyperlink_targets)


def test_resume_export_shows_only_certificate_section_when_only_certificates_exist(monkeypatch, tmp_path):
    """
    Covers:
    - separate section rendering when only certificate entries exist
    - certificates appear after projects
    """
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
    out_dir = tmp_path / "out"

    education_entries = [
        {
            "entry_id": 2,
            "entry_type": "certificate",
            "title": "AWS Cloud Practitioner",
            "organization": "Amazon Web Services",
            "date_text": "2025",
            "description": "Foundational cloud certification.",
        },
    ]

    path = exp.export_resume_record_to_docx(
        username="john",
        record=record,
        out_dir=str(out_dir),
        education_entries=education_entries,
        experience_entries=[],
    )

    txt = _doc_text(path)

    assert "CERTIFICATES" in txt
    assert "AWS Cloud Practitioner" in txt
    assert "EDUCATION" not in txt
    assert "PROJECTS" in txt
    assert txt.find("PROJECTS") < txt.find("CERTIFICATES")


def test_resume_export_nonhappy_no_saved_resumes(monkeypatch, capsys):
    """
    Covers: R2 (flow handler: list_resumes empty)
    """
    monkeypatch.setattr(flow, "list_resumes", lambda conn, user_id: [])
    ok = flow._handle_export_resume_docx(conn=None, user_id=1, username="john")
    out = capsys.readouterr().out
    assert ok is False
    assert "No saved resumes yet" in out


def test_resume_export_nonhappy_cancel_invalid_selection(monkeypatch, capsys):
    """
    Covers: R3 + R4 (cancel, invalid index)
    """
    resumes = [{"id": 11, "name": "Resume A", "created_at": "2026-01-01"}]
    monkeypatch.setattr(flow, "list_resumes", lambda conn, user_id: resumes)
    monkeypatch.setattr(
        flow,
        "get_resume_snapshot",
        lambda conn, user_id, rid: {"resume_json": "{}", "rendered_text": ""},
    )
    monkeypatch.setattr(flow, "export_resume_record_to_docx", lambda **k: Path("./out/fake.docx"))

    # cancel (Enter)
    monkeypatch.setattr("builtins.input", lambda _: "")
    ok = flow._handle_export_resume_docx(conn=None, user_id=1, username="john")
    out = capsys.readouterr().out
    assert ok is False
    assert "Cancelled" in out

    # invalid index (999)
    monkeypatch.setattr("builtins.input", lambda _: "999")
    ok = flow._handle_export_resume_docx(conn=None, user_id=1, username="john")
    out = capsys.readouterr().out
    assert ok is False
    assert "Invalid selection" in out


def test_resume_export_nonhappy_record_missing(monkeypatch, capsys):
    """
    Covers: R5 (get_resume_snapshot returns None)
    """
    resumes = [{"id": 11, "name": "Resume A", "created_at": "2026-01-01"}]
    monkeypatch.setattr(flow, "list_resumes", lambda conn, user_id: resumes)
    monkeypatch.setattr(flow, "get_resume_snapshot", lambda conn, user_id, rid: None)
    monkeypatch.setattr("builtins.input", lambda _: "1")

    ok = flow._handle_export_resume_docx(conn=None, user_id=1, username="john")
    out = capsys.readouterr().out
    assert ok is False
    assert "Unable to load the selected resume" in out


def test_resume_export_fallback_to_rendered_text(monkeypatch, tmp_path):
    """
    Covers: R6 + R7 (malformed JSON -> fallback; missing rendered_text -> message)
    """
    class _FakeDatetime:
        @staticmethod
        def now():
            class _DT:
                def strftime(self, fmt: str) -> str:
                    if fmt == "%Y-%m-%d_%H-%M-%S":
                        return "2026-01-10_15-36-58"
                    if fmt == "%Y-%m-%d at %H:%M:%S":
                        return "2026-01-10 at 15:36:58"
                    return "2026-01-10_15-36-58"
            return _DT()

    monkeypatch.setattr(exp, "datetime", _FakeDatetime)

    out_dir = tmp_path / "out"

    # R6: bad JSON + good rendered_text
    record = {"resume_json": "{not json", "rendered_text": "LINE1\nLINE2\n"}
    path = exp.export_resume_record_to_docx(username="john", record=record, out_dir=str(out_dir))
    txt = _doc_text(path)
    assert "Resume Snapshot" in txt
    assert "LINE1" in txt and "LINE2" in txt

    # R7: bad JSON + missing rendered_text
    record2 = {"resume_json": "{not json", "rendered_text": ""}
    path2 = exp.export_resume_record_to_docx(username="john", record=record2, out_dir=str(out_dir))
    txt2 = _doc_text(path2)
    assert "Resume data is missing or unreadable" in txt2


def test_resume_export_uses_key_role(monkeypatch, tmp_path):
    """Test that export uses resolved key_role instead of [Role] placeholder."""
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
    path = exp.export_resume_record_to_docx(username="jane", record=record, out_dir=str(out_dir))

    txt = _doc_text(path)
    assert "Backend Developer" in txt
    assert "[Role]" not in txt


def test_resume_export_key_role_override_priority(monkeypatch, tmp_path):
    """Test that resume_key_role_override takes priority over base key_role."""
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
                "contribution_bullets": ["Led team"],
            },
        ],
    }

    record = {"resume_json": json.dumps(snapshot), "rendered_text": ""}
    out_dir = tmp_path / "out"
    path = exp.export_resume_record_to_docx(username="jane", record=record, out_dir=str(out_dir))

    txt = _doc_text(path)
    assert "Lead Developer" in txt
    assert "Senior Developer" not in txt
    assert "[Role]" not in txt


def test_resume_export_fallback_to_role_placeholder(monkeypatch, tmp_path):
    """Test that export falls back to [Role] when no key_role is set."""
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
                "contribution_bullets": ["Did stuff"],
            },
        ],
    }

    record = {"resume_json": json.dumps(snapshot), "rendered_text": ""}
    out_dir = tmp_path / "out"
    path = exp.export_resume_record_to_docx(username="jane", record=record, out_dir=str(out_dir))

    txt = _doc_text(path)
    assert "[Role]" in txt

    

def test_resume_export_uses_full_name_when_present(monkeypatch, tmp_path):
    """Test that DOCX export uses full_name instead of username when present."""
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
    out_dir = tmp_path / "out"

    user_profile = {
        "full_name": "John Tan",
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
        out_dir=str(out_dir),
        user_profile=user_profile,
    )

    txt = _doc_text(path)
    assert "JOHN TAN" in txt