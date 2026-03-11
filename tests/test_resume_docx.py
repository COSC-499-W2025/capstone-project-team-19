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


def test_resume_docx_profile_happy_path(monkeypatch, tmp_path):
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
            "languages": ["Python 88%"],
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

    path = exp.export_resume_record_to_docx(
        username="john123",
        record=record,
        out_dir=str(tmp_path / "out"),
        user_profile=user_profile,
    )

    txt = _doc_text(path)
    hyperlink_targets = _docx_hyperlink_targets(path)

    assert "JOHN TAN" in txt
    assert "john@example.com" in txt
    assert "1234567890" in txt
    assert "LinkedIn" in txt
    assert "GitHub" in txt
    assert "Kelowna, BC" in txt
    assert "PROFILE" in txt
    assert "Software and data student building practical tools." in txt

    assert "https://linkedin.com/in/john" in hyperlink_targets
    assert "https://github.com/john" in hyperlink_targets
    assert "https://linkedin.com/in/john" not in txt
    assert "https://github.com/john" not in txt


def test_resume_docx_profile_omits_empty_fields(monkeypatch, tmp_path):
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

    path = exp.export_resume_record_to_docx(
        username="john123",
        record=record,
        out_dir=str(tmp_path / "out"),
        user_profile=empty_profile,
    )

    txt = _doc_text(path)
    hyperlink_targets = _docx_hyperlink_targets(path)

    assert "JOHN123" in txt
    assert "PROFILE" not in txt
    assert "john@example.com" not in txt
    assert "1234567890" not in txt
    assert "LinkedIn" not in txt
    assert "GitHub" not in txt
    assert "Kelowna, BC" not in txt

    assert all("linkedin.com" not in target for target in hyperlink_targets)
    assert all("github.com" not in target for target in hyperlink_targets)