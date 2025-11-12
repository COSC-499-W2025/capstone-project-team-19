import os
import json
import pytest
from unittest.mock import patch, MagicMock
from src.analysis.text_individual import text_llm_analyze
from src.common.helpers import extractfromcsv


@pytest.fixture
def mock_parsed_files():
    # include project folder in file path for new grouping logic
    return [
        {"file_path": "ProjectA/sample.txt", "file_name": "sample.txt", "file_type": "text"}
    ]

@pytest.fixture
def fake_zip_structure(tmp_path):
    return {
        "zip_path": str(tmp_path / "Archive.zip"),
        "zip_dir": tmp_path / "zip_data" / "Archive",
        "project_dir": tmp_path / "zip_data" / "Archive" / "ProjectA",
        "project_name": "ProjectA"
    }

@pytest.fixture
def mock_text_file(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("This is a sample document about AI and ethics.")
    return str(f)


@pytest.fixture(autouse=True)
def patch_extract_text_file_and_metrics(mock_text_file):
    with patch("src.text_llm_analyze.extract_text_file", return_value="Sample text content."), \
         patch("src.text_llm_analyze.analyze_linguistic_complexity", return_value={
             "word_count": 10,
             "sentence_count": 2,
             "reading_level": "High School",
             "flesch_kincaid_grade": 9.5,
             "lexical_diversity": 0.45
         }):
        yield


@pytest.fixture
def mock_llm_responses():
    def fake_completion(content):
        fake_choice = MagicMock()
        fake_choice.message.content = content
        mock_response = MagicMock()
        mock_response.choices = [fake_choice]
        return mock_response
    return fake_completion


@pytest.fixture
def standard_llm_side_effects(mock_llm_responses):
    """Standard LLM API responses for text analysis tests."""
    return [
        mock_llm_responses("A research essay that explores AI ethics."),
        mock_llm_responses("- Analytical thinking\n- Ethical reasoning\n- Research writing"),
        mock_llm_responses('{"strengths": ["clear focus", "strong evidence"], "weaknesses": ["limited depth"], "score": "8.2 / 10 (Strong clarity)"}')
    ]


@patch("builtins.input", return_value="1")
@patch("src.text_llm_analyze.client")
def test_run_llm_analysis_basic(mock_client, mock_input, mock_parsed_files, fake_zip_structure, standard_llm_side_effects, capsys):
    # Use standard LLM responses
    mock_client.chat.completions.create.side_effect = standard_llm_side_effects

    # Create fake zip directory structure
    os.makedirs(fake_zip_structure["project_dir"], exist_ok=True)
    (fake_zip_structure["project_dir"] / "sample.txt").write_text("This is a sample document.")

    results = text_llm_analyze.run_text_llm_analysis(mock_parsed_files, fake_zip_structure["zip_path"], None, None)

    captured = capsys.readouterr()

    # Assertions
    assert "Analyzing 1 file(s)" in captured.out
    assert "→ ProjectA" in captured.out
    assert "Summary:" in captured.out
    assert "Skills Demonstrated:" in captured.out
    assert "Success Factors:" in captured.out
    assert "8.2 / 10" in captured.out

    # Assertions for returned results
    assert len(results) == 1
    assert results[0]["project_name"] == "ProjectA"
    assert results[0]["file_name"] == "sample.txt"
    assert os.path.normpath(results[0]["file_path"]) == os.path.normpath("ProjectA/sample.txt")
    assert "A research essay" in results[0]["summary"]
    assert len(results[0]["skills"]) == 3
    assert "8.2 / 10" in results[0]["success"]["score"]

@patch("builtins.input", return_value="1")
@patch("src.text_llm_analyze.client")
def test_run_llm_analysis_db(mock_client, mock_input, mock_parsed_files, fake_zip_structure, standard_llm_side_effects):
    import src.db as db

    mock_client.chat.completions.create.side_effect = standard_llm_side_effects

    # Create fake zip directory structure
    os.makedirs(fake_zip_structure["project_dir"], exist_ok=True)
    (fake_zip_structure["project_dir"] / "sample.txt").write_text("This is a sample document.")

    conn = db.connect()
    user_id = db.get_or_create_user(conn, "test-user-llm")

    db.record_project_classification(conn=conn, user_id=user_id, zip_path=fake_zip_structure["zip_path"], zip_name="Archive", project_name=fake_zip_structure["project_name"], classification="individual")
    classification_id = db.get_classification_id(conn, user_id, fake_zip_structure["project_name"])

    # Get results from analysis
    results = text_llm_analyze.run_text_llm_analysis(mock_parsed_files, fake_zip_structure["zip_path"], None, None)

    # Store results to database (mimics what project_analysis.py does)
    for result in results:
        db.store_text_llm_metrics(
            conn,
            classification_id,
            result["project_name"],
            result["file_name"],
            result["file_path"],
            result["linguistic"],
            result["summary"],
            result["skills"],
            result["success"]
        )

    # Retrieve and verify stored data
    metrics = db.get_text_llm_metrics(conn, classification_id)

    # Verify scalar fields
    assert metrics["project_name"] == "ProjectA"
    assert metrics["file_name"] == "sample.txt"
    assert os.path.normpath(metrics["file_path"]) == os.path.normpath("ProjectA/sample.txt")
    assert metrics["word_count"] == 10
    assert metrics["sentence_count"] == 2
    assert metrics["flesch_kincaid_grade"] == 9.5
    assert metrics["lexical_diversity"] == 0.45
    assert "A research essay" in metrics["summary"]

    # Verify JSON fields were stored correctly
    import json
    skills = json.loads(metrics["skills_json"])
    strengths = json.loads(metrics["strength_json"])
    weaknesses = json.loads(metrics["weaknesses_json"])

    assert isinstance(skills, list)
    assert len(skills) == 3
    assert "Analytical thinking" in skills
    assert isinstance(strengths, list)
    assert "clear focus" in strengths
    assert isinstance(weaknesses, list)
    assert "limited depth" in weaknesses
    assert "8.2 / 10" in metrics["overall_score"]

# tests if largest file is auto-selected when user presses Enter
@patch("builtins.input", return_value="")
@patch("src.text_llm_analyze.client")
@patch("src.text_llm_analyze.os.path.getsize", side_effect=lambda path: 1000 if "main" in path else 100)
def test_auto_select_largest_file(mock_getsize, mock_client, mock_input, tmp_path, mock_llm_responses):
    mock_client.chat.completions.create.side_effect = [
        mock_llm_responses("Summary text"),
        mock_llm_responses("- Skill 1\n- Skill 2"),
        mock_llm_responses('{"strengths": ["clarity"], "weaknesses": ["depth"], "score": "8.0 / 10"}')
    ]

    project_dir = tmp_path / "zip_data" / "Archive" / "ProjectA"
    os.makedirs(project_dir, exist_ok=True)
    (project_dir / "draft.txt").write_text("short text")
    (project_dir / "main.txt").write_text("longer main text")

    parsed = [
        {"file_path": "ProjectA/draft.txt", "file_name": "draft.txt", "file_type": "text"},
        {"file_path": "ProjectA/main.txt", "file_name": "main.txt", "file_type": "text"},
    ]

    text_llm_analyze.run_text_llm_analysis(parsed, str(tmp_path / "Archive.zip"), None, None)

    captured = mock_client.chat.completions.create.call_args_list[0][1]["messages"][1]["content"]
    assert "main.txt" not in captured  # summary prompt should only see main file’s text
    assert mock_getsize.called
    
    
@patch("builtins.input", return_value="2")
@patch("src.text_llm_analyze.client")

# tests if supporting files are detected and included in skills and success factors prompts
def test_supporting_files_are_detected_and_used(mock_client, mock_input, tmp_path, mock_llm_responses):
    # mock all three LLM calls
    mock_client.chat.completions.create.side_effect = [
        mock_llm_responses("A final research report."),
        mock_llm_responses("- Research synthesis\n- Data interpretation"),
        mock_llm_responses('{"strengths": ["clear analysis"], "weaknesses": ["minor redundancy"], "score": "9.0 / 10"}')
    ]

    # create fake folder and files
    project_dir = tmp_path / "zip_data" / "Archive" / "ProjectA"
    os.makedirs(project_dir, exist_ok=True)
    (project_dir / "final.txt").write_text("Final report on AI ethics.")
    (project_dir / "draft1.txt").write_text("Rough outline and early thoughts.")
    (project_dir / "notes.txt").write_text("Research notes on methodology.")

    parsed_files = [
        {"file_path": "ProjectA/final.txt", "file_name": "final.txt", "file_type": "text"},
        {"file_path": "ProjectA/draft1.txt", "file_name": "draft1.txt", "file_type": "text"},
        {"file_path": "ProjectA/notes.txt", "file_name": "notes.txt", "file_type": "text"},
    ]

    text_llm_analyze.run_text_llm_analysis(parsed_files, str(tmp_path / "Archive.zip"), None, None)

    # grab the arguments passed to the skills or success LLM call
    skills_call = mock_client.chat.completions.create.call_args_list[1][1]
    success_call = mock_client.chat.completions.create.call_args_list[2][1]

    # both prompts should include content from supporting files
    skills_prompt = skills_call["messages"][1]["content"]
    success_prompt = success_call["messages"][1]["content"]

    assert "draft1.txt" in skills_prompt
    assert "notes.txt" in skills_prompt
    assert "draft1.txt" in success_prompt
    assert "notes.txt" in success_prompt


@patch("src.text_llm_analyze.client")
# tests if LLM API errors are handled gracefully (placeholders printed when API fails)
def test_llm_api_error_handling(mock_client):
    mock_client.chat.completions.create.side_effect = Exception("API error")

    result = text_llm_analyze.generate_text_llm_success_factors("text", {"word_count": 5})
    assert "None" in result.values() or "unavailable" in str(result).lower()

# tests if LLM summary generation works as expected
@patch("src.text_llm_analyze.client")
def test_generate_llm_summary(mock_client, mock_llm_responses):
    mock_client.chat.completions.create.return_value = mock_llm_responses(
        "A project proposal that outlines a sustainable design solution."
    )
    result = text_llm_analyze.generate_text_llm_summary("Text about sustainability.")
    assert "project proposal" in result.lower()

# tests if LLM skills generation works as expected
@patch("src.text_llm_analyze.client")
def test_generate_llm_skills(mock_client, mock_llm_responses):
    mock_client.chat.completions.create.return_value = mock_llm_responses(
        "- Research\n- Writing\n- Analysis"
    )
    result = text_llm_analyze.generate_text_llm_skills("Some text about research and writing.")
    assert isinstance(result, list)
    assert "Research" in result[0]

# tests if LLM success factors generation works as expected
@patch("src.text_llm_analyze.client")
def test_generate_llm_success_factors(mock_client, mock_llm_responses):
    fake_json = '{"strengths": "clear structure", "weaknesses": "minor redundancy", "score": "8.1 / 10 (Good clarity)"}'
    mock_client.chat.completions.create.return_value = mock_llm_responses(fake_json)

    linguistic = {"reading_level": "College", "lexical_diversity": 0.4, "word_count": 500}
    result = text_llm_analyze.generate_text_llm_success_factors("Some academic text.", linguistic)
    assert result["strengths"].startswith("clear")
    assert "8.1" in result["score"]

