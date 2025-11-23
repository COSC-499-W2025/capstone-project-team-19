import os
import pytest
from unittest.mock import patch, MagicMock
from src.analysis.text_individual.text_analyze import run_text_pipeline


@pytest.fixture
def mock_parsed_files():
    return [
        {"file_path": "ProjectA/main.txt", "file_name": "main.txt", "file_type": "text"},
        {"file_path": "ProjectA/support.txt", "file_name": "support.txt", "file_type": "text"},
        {"file_path": "ProjectA/data1.csv", "file_name": "data1.csv", "file_type": "csv"},
    ]


@pytest.fixture
def fake_zip_structure(tmp_path):
    zip_path = tmp_path / "Archive.zip"
    zip_dir = tmp_path / "zip_data" / "Archive"
    project_dir = zip_dir / "ProjectA"

    os.makedirs(project_dir, exist_ok=True)

    # Create text files
    (project_dir / "main.txt").write_text("Main document text.")
    (project_dir / "support.txt").write_text("Supporting document text.")

    # Create CSV file
    (project_dir / "data1.csv").write_text("col1,col2\n1,2\n3,4")

    return {
        "zip_path": str(zip_path),
        "zip_dir": zip_dir,
        "project_dir": project_dir,
    }


# MAIN PIPELINE TESTS
@patch("src.analysis.text_individual.text_analyze.extract_text_file")
@patch("src.analysis.text_individual.text_analyze.analyze_all_csv")
@patch("src.analysis.text_individual.text_analyze.prompt_manual_summary")
@patch("src.analysis.text_individual.text_analyze.extract_text_skills")
@patch("builtins.input", return_value="1")
def test_run_text_pipeline_basic(
    mock_input,
    mock_extract_skills,
    mock_prompt_summary,
    mock_csv_meta,
    mock_extract_text,
    mock_parsed_files,
    fake_zip_structure
):
    # Mock return values
    mock_extract_text.return_value = "Mock text content."
    mock_prompt_summary.return_value = "Manual summary text."
    mock_csv_meta.return_value = {
        "files": [{"file_name": "data1.csv", "file_path": "ProjectA/data1.csv"}],
        "growth_trend_present": False,
        "growth_trends": {}
    }
    mock_extract_skills.return_value = {
        "skills": ["Critical Thinking", "Research"],
        "buckets": {
            "clarity": {"score": 0.8, "description": "Sentence clarity"},
            "depth": {"score": 0.7, "description": "Content depth"},
        },
        "overall_score": 0.75
    }

    result = run_text_pipeline(
        parsed_files=mock_parsed_files,
        zip_path=fake_zip_structure["zip_path"],
        conn=None,
        user_id=1,
        project_name="ProjectA",
        consent="rejected"
    )

    # ---------------- Assertions -----------------

    # Main return keys
    assert "project_summary" in result
    assert "skills" in result
    assert "buckets" in result
    assert "overall_score" in result
    assert "main_file" in result

    # Correct summary
    assert result["project_summary"] == "Manual summary text."

    # Skills passed through
    assert result["skills"] == ["Critical Thinking", "Research"]
    assert result["buckets"]["clarity"]["score"] == 0.8

    # Verify correct file detected as main
    assert result["main_file"] == "main.txt"

    # CSV metadata was used
    mock_csv_meta.assert_called_once()


# EDGE CASE: No TEXT files
def test_run_text_pipeline_no_text_files(capsys):
    parsed_files = [{"file_path": "ProjectA/data1.csv", "file_name": "data1.csv", "file_type": "csv"}]

    result = run_text_pipeline(
        parsed_files=parsed_files,
        zip_path="fake.zip",
        conn=None,
        user_id=1,
        project_name="ProjectA"
    )

    captured = capsys.readouterr()
    assert "No non-CSV text files found" in captured.out
    assert result == []


# EDGE CASE: Multiple text files → user selects main file
@patch("builtins.input", return_value="2")
@patch("src.analysis.text_individual.text_analyze.extract_text_file", return_value="Some content")
@patch("src.analysis.text_individual.text_analyze.analyze_all_csv", return_value={"files": [], "growth_trend_present": False, "growth_trends": {}})
@patch("src.analysis.text_individual.text_analyze.prompt_manual_summary", return_value="Summary.")
@patch("src.analysis.text_individual.text_analyze.extract_text_skills", return_value={"skills": [], "buckets": {}, "overall_score": 0})
def test_user_selects_second_main_file(
    mock_skills, mock_summary, mock_csv, mock_extract, mock_input,
    tmp_path
):
    parsed = [
        {"file_path": "ProjectA/a.txt", "file_name": "a.txt", "file_type": "text"},
        {"file_path": "ProjectA/b.txt", "file_name": "b.txt", "file_type": "text"},
    ]

    # Fake zip structure
    base = tmp_path / "zip_data" / "Archive" / "ProjectA"
    os.makedirs(base, exist_ok=True)
    (base / "a.txt").write_text("aaa")
    (base / "b.txt").write_text("bbb")

    result = run_text_pipeline(
        parsed_files=parsed,
        zip_path=str(tmp_path / "Archive.zip"),
        conn=None,
        user_id=1,
        project_name="ProjectA",
    )

    assert result["main_file"] == "b.txt"   # user selected option 2


# EDGE CASE: Missing text extraction
@patch("builtins.input", return_value="1")
@patch("src.analysis.text_individual.text_analyze.extract_text_file", return_value=None)
@patch("src.analysis.text_individual.text_analyze.analyze_all_csv", return_value={"files": []})
def test_main_file_extraction_fails(mock_csv, mock_extract, mock_input,
                                   mock_parsed_files, fake_zip_structure, capsys):
    run_text_pipeline(
    parsed_files=mock_parsed_files,
    zip_path=fake_zip_structure["zip_path"],
    conn=None,
    user_id=1,
    project_name="ProjectA"
    )
    
    captured = capsys.readouterr()
    assert "Could not extract text" in captured.out

