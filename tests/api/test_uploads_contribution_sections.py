import sqlite3
from pathlib import Path

import pytest

from src.db.uploads import (
    create_upload,
    update_upload_zip_metadata,
    set_upload_state,
    get_upload_by_id,
)
from src.services.uploads_contribution_service import (
    list_main_file_sections,
    set_main_file_contributed_sections,
)
from src.utils.helpers import normalize_pdf_paragraphs
from src.analysis.text_collaborative.text_sections import extract_document_sections


def fake_extract_text_file(path: str, conn, user_id) -> str:
    # Unit-test stub: treat the "main file" as plain text on disk.
    return Path(path).read_text(encoding="utf-8")


def derive_expected_sections_and_titles(raw_text: str):
    normalized_paragraphs = normalize_pdf_paragraphs(raw_text) or []
    normalized_text = "\n\n".join(normalized_paragraphs).strip()

    sections_raw = extract_document_sections(normalized_text) or []

    titles = []
    for i, s in enumerate(sections_raw, start=1):
        header = (s.get("header") or "").strip()
        preview = (s.get("preview") or "").strip()
        titles.append(header or preview or f"Section {i}")

    return sections_raw, titles


@pytest.fixture()
def conn(tmp_path: Path):
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row

    schema_path = Path("src/db/schema/tables.sql")
    db.executescript(schema_path.read_text(encoding="utf-8"))

    db.execute("INSERT INTO users (username) VALUES (?)", ("testuser",))
    db.commit()
    return db


@pytest.fixture()
def user_id(conn: sqlite3.Connection) -> int:
    return conn.execute(
        "SELECT user_id FROM users WHERE username=?",
        ("testuser",),
    ).fetchone()[0]


@pytest.fixture()
def upload_setup(tmp_path: Path, conn: sqlite3.Connection, user_id: int, monkeypatch):
    # Patch module globals used by uploads_contribution_service
    import src.services.uploads_contribution_service as ucs

    zip_data_dir = tmp_path / "zip_data"
    zip_data_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(ucs, "ZIP_DATA_DIR", str(zip_data_dir))
    monkeypatch.setattr(ucs, "extract_text_file", fake_extract_text_file)

    uploads_dir = zip_data_dir / "_uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    zip_path = uploads_dir / "1_mock_upload.zip"
    zip_path.write_bytes(b"")  # dummy zip; only stem is used

    upload_id = create_upload(conn, user_id, status="started", state={})
    update_upload_zip_metadata(conn, upload_id, zip_name=zip_path.name, zip_path=str(zip_path))

    project_name = "MockProject"
    relpath = "mock_projects/MockProject/main_report.txt"

    extract_dir = zip_data_dir / zip_path.stem
    main_file_path = extract_dir / relpath
    main_file_path.parent.mkdir(parents=True, exist_ok=True)

    raw_text = (
        "Title: UX Redesign Notes for Mobile App\n"
        "Abstract: This report summarizes findings from a short usability review.\n"
        "\n"
        "Introduction: We reviewed navigation, content density, and accessibility.\n"
        "The goal was to identify quick wins and longer-term design risks.\n"
        "\n"
        "Methods: We ran a heuristic evaluation and mapped key user flows.\n"
        "We also reviewed analytics for drop-off points.\n"
        "\n"
        "Results and Discussion: Navigation labels were inconsistent across screens.\n"
        "Several critical actions were buried under secondary menus.\n"
        "\n"
        "Conclusion: Prioritize clearer IA and reduce friction for primary tasks.\n"
        "Keywords: ux, navigation, mobile\n"
    )
    main_file_path.write_text(raw_text, encoding="utf-8")

    state = {
        "zip_path": str(zip_path),
        "file_roles": {project_name: {"main_file": relpath}},
    }
    set_upload_state(conn, upload_id, state=state, status="needs_file_roles")

    return {
        "upload_id": upload_id,
        "project_name": project_name,
        "relpath": relpath,
        "raw_text": raw_text,
    }


def test_list_main_file_sections_derives_sections(conn, user_id, upload_setup):
    upload_id = upload_setup["upload_id"]
    project_name = upload_setup["project_name"]
    raw_text = upload_setup["raw_text"]

    expected_sections_raw, expected_titles = derive_expected_sections_and_titles(raw_text)

    result = list_main_file_sections(conn, user_id, upload_id, project_name, max_section_chars=10_000)

    assert result["project_name"] == project_name
    assert result["main_file"]
    assert isinstance(result["sections"], list)

    assert len(result["sections"]) == len(expected_sections_raw)
    assert [s["id"] for s in result["sections"]] == list(range(1, len(result["sections"]) + 1))
    assert [s["title"] for s in result["sections"]] == expected_titles


def test_set_main_file_contributed_sections_persists_ids(conn, user_id, upload_setup):
    upload_id = upload_setup["upload_id"]
    project_name = upload_setup["project_name"]
    raw_text = upload_setup["raw_text"]

    expected_sections_raw, _ = derive_expected_sections_and_titles(raw_text)
    n = len(expected_sections_raw)
    assert n > 0

    selected = [1, n, 1, n]  # includes duplicates / unsorted

    resp = set_main_file_contributed_sections(conn, user_id, upload_id, project_name, selected)

    contrib = (resp["state"].get("contributions") or {}).get(project_name) or {}
    assert contrib.get("main_section_ids") == sorted(set(selected))

    row = get_upload_by_id(conn, upload_id)
    persisted_state = row.get("state") or {}
    persisted = (persisted_state.get("contributions") or {}).get(project_name) or {}
    assert persisted.get("main_section_ids") == sorted(set(selected))