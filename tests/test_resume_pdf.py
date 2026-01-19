import json
from pathlib import Path
import json
import pytest
from pypdf import PdfReader

def test_resume_pdf_export_creates_valid_pdf(monkeypatch, tmp_path):
    import src.export.resume_pdf as exp

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

def _pdf_text(path):
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)

@pytest.mark.pdf_text
def test_resume_pdf_contains_sections_and_orders_projects(monkeypatch, tmp_path):
    import src.export.resume_pdf as exp

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

    out_dir = tmp_path / "out"
    path = exp.export_resume_record_to_pdf(username="john", record=record, out_dir=str(out_dir))

    text = _pdf_text(path)

    # section headings
    assert "PROFILE" in text
    assert "SKILLS" in text
    assert "PROJECTS" in text
    assert "EDUCATION" in text

    # ordering by recency: newer should appear before older
    assert text.find("newer") < text.find("older")

def test_resume_export_pdf_cancel_invalid_selection(monkeypatch, capsys):
    """
    Covers:
    - Cancel on Enter
    - Invalid index selection
    - Ensures PDF export is not called
    """
    import src.menu.resume.flow as flow

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

    # Guard: export must NOT be called
    def fail_export(**kwargs):
        raise AssertionError("PDF export should not be called")

    monkeypatch.setattr(flow, "export_resume_record_to_pdf", fail_export)

    # ---- Case 1: Cancel (Enter) ----
    monkeypatch.setattr("builtins.input", lambda _: "")
    ok = flow._handle_export_resume_pdf(conn=None, user_id=1, username="john")
    out = capsys.readouterr().out

    assert ok is False
    assert "Cancelled" in out

    # ---- Case 2: Invalid index ----
    monkeypatch.setattr("builtins.input", lambda _: "999")
    ok = flow._handle_export_resume_pdf(conn=None, user_id=1, username="john")
    out = capsys.readouterr().out

    assert ok is False
    assert "Invalid selection" in out
