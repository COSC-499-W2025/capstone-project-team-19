import builtins
import pytest
from unittest.mock import patch, MagicMock

from src.analysis.text_collaborative.text_collab_analysis import analyze_collaborative_text_project


# -----------------------------
# Fake Summary Object
# -----------------------------
class FakeSummary:
    def __init__(self):
        self.summary_text = None
        self.contributions = {"text_collab": {}}


# -----------------------------
# TEST: Core collaborative flow
# -----------------------------
@pytest.fixture
def mock_parsed_files():
    """
    Pretend we have:
    - main_report.pdf (main)
    - first_draft.docx (supporting)
    - outline.docx (supporting)
    - data.csv (supporting CSV)
    """
    return [
        {"file_name": "main_report.pdf", "file_type": "text", "file_path": "project/main_report.pdf"},
        {"file_name": "first_draft.docx", "file_type": "text", "file_path": "project/first_draft.docx"},
        {"file_name": "outline.docx", "file_type": "text", "file_path": "project/outline.docx"},
        {"file_name": "data.csv", "file_type": "csv", "file_path": "project/data.csv"},
    ]


@pytest.fixture
def mock_pipeline_result():
    return {
        "project_summary": "Mock summary",
        "skills": {},
        "buckets": {},
        "overall_score": 0.5,
        "main_file": "main_report.pdf",
        "csv_metadata": {
            "files": [
                {"file_name": "data.csv", "file_path": "project/data.csv"}
            ]
        }
    }


@pytest.fixture
def mock_skill_output():
    return {
        "skills": ["mock_skill"],
        "buckets": {
            "process": {"score": 0.5, "description": "Revision & editing"}
        },
        "overall_score": 0.77
    }


# -----------------------------
# MAIN TEST: Everything works
# -----------------------------
def test_analyze_collaborative_text_project(
    mock_parsed_files, mock_pipeline_result, mock_skill_output
):
    summary_obj = FakeSummary()

    # Fake extracted text for each file
    def fake_extract_text_file(path, conn, user_id):
        if "main_report" in path:
            return "Introduction\nThis is intro.\nMethods\nThis is methods."
        if "first_draft" in path:
            return "Draft content here."
        if "outline" in path:
            return "Outline content here."
        return ""

    # Simulated user inputs in order:
    # 1) sections selected → "1,2"
    # 2) contribution description → "My contribution"
    # 3) supporting text files → "1" (first_draft)
    # 4) CSV files → "1"
    # 5) manual contribution summary type → "1"
    # 6) key role → "Developer"
    fake_inputs = iter(["1,2", "My contribution", "1", "1", "1", "Developer"])

    with (
        patch("src.analysis.text_collaborative.text_collab_analysis.run_text_pipeline",
              return_value=mock_pipeline_result),

        patch("src.analysis.text_collaborative.text_collab_analysis.extract_text_skills",
              return_value=mock_skill_output),

        patch("src.analysis.text_collaborative.text_collab_analysis._load_main_text",
              side_effect=lambda pf, fn, zp, c, u: fake_extract_text_file(fn, c, u)),

        patch("src.utils.helpers.extract_text_file", side_effect=fake_extract_text_file),

        patch.object(builtins, "input", lambda _: next(fake_inputs)),
    ):
        analyze_collaborative_text_project(
            conn=None,
            user_id=123,
            project_name="PlantGrowth",
            parsed_files=mock_parsed_files,
            zip_path="/fake/zip/path.zip",
            external_consent="rejected",
            summary_obj=summary_obj
        )

    # -------------------------
    # ASSERTIONS
    # -------------------------
    result = summary_obj.contributions["text_collab"]

    # contributed_text was removed to reduce verbosity
    assert "contributed_text" not in result

    assert result["percent_of_document"] > 0

    assert "skills" in result
    assert "buckets" in result
    assert result["overall_score"] == mock_skill_output["overall_score"]

    print("\n[Test Completed] Collaborative text pipeline passed!\n")
