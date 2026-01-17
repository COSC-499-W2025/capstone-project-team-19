import json
from pathlib import Path

import pytest
from docx import Document


def _doc_text(path: Path) -> str:
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text is not None)


def test_resume_export_happy_json_structure_and_order(monkeypatch, tmp_path):
    """
    Covers: R1 + X1 (deterministic filename via frozen datetime) + structure/order:
    Skills Summary first, then grouped sections, with project blocks.
    """
    import src.export.resume_docx as exp

    # Freeze datetime.now() used by exporter
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
            "languages": ["Python", "SQL"],
            "frameworks": ["LightGBM"],
            "technical_skills": ["Algorithms"],
            "writing_skills": ["Clear communication"],
        },
        "projects": [
            {
                "project_name": "code_ind",
                "project_type": "code",
                "project_mode": "individual",
                "languages": ["Python"],
                "frameworks": ["LightGBM"],
                "summary_text": "code summary",
                "activities": [{"name": "feature_coding", "top_file": "a.py"}],
                "contribution_bullets": [
                    "Contributed 12.3% of total repository commits (4 commits) across testing workflows."
                ],
                "skills": ["Algorithms"],
            },
            {
                "project_name": "text_collab",
                "project_type": "text",
                "project_mode": "collaborative",
                "text_type": "Academic writing",
                "summary_text": "text summary",
                "contribution_percent": 91.0,
                "contribution_bullets": [
                    "Contributed to 91.0% of the project deliverables."
                ],
                "skills": ["Clear communication"],
            },
        ],
    }

    record = {"resume_json": json.dumps(snapshot), "rendered_text": "fallback"}
    out_dir = tmp_path / "out"
    path = exp.export_resume_record_to_docx(username="salma", record=record, out_dir=str(out_dir))

    assert out_dir.exists()
    assert path.exists()
    assert path.name == "resume_salma_2026-01-10_15-36-58.docx"

    txt = _doc_text(path)

    assert "Resume — salma" in txt
    assert "Generated on 2026-01-10 at 15:36:58" in txt

    # Title + skills first
    assert "Skills Summary" in txt
    assert "Languages: Python, SQL" in txt or "Languages: SQL, Python" in txt

    # Order check (Skills Summary appears before projects)
    idx_skills = txt.find("Skills Summary")
    idx_code = txt.find("Code — Individual")
    assert idx_skills != -1 and idx_code != -1
    assert idx_skills < idx_code

    # Project block content
    assert "code_ind" in txt
    assert "Summary: code summary" in txt
    assert "Contributions:" in txt
    assert "Contributed 12.3% of total repository commits" in txt
    assert "Skills:" in txt

    assert "Text — Collaborative" in txt
    assert "text_collab" in txt
    assert "Type: Academic writing" in txt
    assert "Contributed to 91.0% of the project deliverables." in txt


def test_resume_export_nonhappy_no_saved_resumes(monkeypatch, capsys):
    """
    Covers: R2 (flow handler: list_resumes empty)
    """
    import src.menu.resume.flow as flow

    monkeypatch.setattr(flow, "list_resumes", lambda conn, user_id: [])
    ok = flow._handle_export_resume_docx(conn=None, user_id=1, username="salma")
    out = capsys.readouterr().out
    assert ok is False
    assert "No saved resumes yet" in out


def test_resume_export_nonhappy_cancel_invalid_selection(monkeypatch, capsys):
    """
    Covers: R3 + R4 (cancel, invalid index)
    """
    import src.menu.resume.flow as flow

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
    ok = flow._handle_export_resume_docx(conn=None, user_id=1, username="salma")
    out = capsys.readouterr().out
    assert ok is False
    assert "Cancelled" in out

    # invalid index (999)
    monkeypatch.setattr("builtins.input", lambda _: "999")
    ok = flow._handle_export_resume_docx(conn=None, user_id=1, username="salma")
    out = capsys.readouterr().out
    assert ok is False
    assert "Invalid selection" in out


def test_resume_export_nonhappy_record_missing(monkeypatch, capsys):
    """
    Covers: R5 (get_resume_snapshot returns None)
    """
    import src.menu.resume.flow as flow

    resumes = [{"id": 11, "name": "Resume A", "created_at": "2026-01-01"}]
    monkeypatch.setattr(flow, "list_resumes", lambda conn, user_id: resumes)
    monkeypatch.setattr(flow, "get_resume_snapshot", lambda conn, user_id, rid: None)
    monkeypatch.setattr("builtins.input", lambda _: "1")

    ok = flow._handle_export_resume_docx(conn=None, user_id=1, username="salma")
    out = capsys.readouterr().out
    assert ok is False
    assert "Unable to load the selected resume" in out


def test_resume_export_fallback_to_rendered_text(monkeypatch, tmp_path):
    """
    Covers: R6 + R7 (malformed JSON -> fallback; missing rendered_text -> message)
    """
    import src.export.resume_docx as exp

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
    path = exp.export_resume_record_to_docx(username="salma", record=record, out_dir=str(out_dir))
    txt = _doc_text(path)
    assert "Resume Snapshot" in txt
    assert "LINE1" in txt and "LINE2" in txt

    # R7: bad JSON + missing rendered_text
    record2 = {"resume_json": "{not json", "rendered_text": ""}
    path2 = exp.export_resume_record_to_docx(username="salma", record=record2, out_dir=str(out_dir))
    txt2 = _doc_text(path2)
    assert "Resume data is missing or unreadable" in txt2
