import sqlite3
from unittest.mock import patch, Mock
from src.analysis.skills.flows.skill_extraction import extract_skills

# helpers
def _mock_meta(project_type="code", classification="individual"):
    return classification, project_type

def run_with_patches(
    project_type,
    files,
    *,
    code_mock=None,
    text_mock=None,
):
    conn = sqlite3.connect(":memory:")

    with patch("src.analysis.skills.flows.skill_extraction.get_project_metadata",
               return_value=_mock_meta(project_type)) as meta_mock, \
         patch("src.analysis.skills.flows.skill_extraction._fetch_files",
               return_value=files) as fetch_mock, \
         patch("src.analysis.skills.flows.skill_extraction.extract_code_skills",
               new=code_mock or Mock()) as code_extractor, \
         patch("src.analysis.skills.flows.skill_extraction.extract_text_skills",
               new=text_mock or Mock()) as text_extractor:

        extract_skills(conn, 1, "proj")

    return {
        "meta": meta_mock,
        "fetch": fetch_mock,
        "code": code_extractor,
        "text": text_extractor,
    }

# tests
def test_happy_path_code():
    mocks = run_with_patches("code", ["file.py"])

    mocks["meta"].assert_called_once()
    mocks["fetch"].assert_called_once()
    mocks["code"].assert_called_once_with(
        ANY_CONN := mocks["code"].call_args.args[0],   # conn, but irrelevant
        1,
        "proj",
        "individual",
        ["file.py"]
    )
    mocks["text"].assert_not_called()


def test_happy_path_text():
    mocks = run_with_patches("text", ["doc.txt"])

    mocks["meta"].assert_called_once()
    mocks["fetch"].assert_called_once()
    mocks["text"].assert_called_once_with(
        ANY_CONN := mocks["text"].call_args.args[0],
        1,
        "proj",
        "individual",
        ["doc.txt"]
    )
    mocks["code"].assert_not_called()


def test_missing_metadata_skips_extraction():
    conn = sqlite3.connect(":memory:")

    with patch("src.analysis.skills.flows.skill_extraction.get_project_metadata",
               return_value=(None, None)), \
         patch("src.analysis.skills.flows.skill_extraction.extract_code_skills") as code_mock, \
         patch("src.analysis.skills.flows.skill_extraction.extract_text_skills") as text_mock:

        extract_skills(conn, 1, "proj")

    code_mock.assert_not_called()
    text_mock.assert_not_called()


def test_no_files_skips_extraction():
    mocks = run_with_patches("code", [])

    mocks["code"].assert_not_called()
    mocks["text"].assert_not_called()


def test_invalid_project_type_skips_both_extractors():
    # project_type="weird" triggers the "else" clause
    mocks = run_with_patches("weird", ["somefile"])

    # metadata + fetch should still be called
    mocks["meta"].assert_called_once()
    mocks["fetch"].assert_called_once()

    # but NO extractor should run
    mocks["code"].assert_not_called()
    mocks["text"].assert_not_called()
