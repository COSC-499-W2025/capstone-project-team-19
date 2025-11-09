import os
import pytest
from unittest.mock import patch, MagicMock
from src import text_llm_analyze


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
@patch("src.text_llm_analyze.connect")
@patch("src.text_llm_analyze.store_text_llm_metrics")
@patch("src.text_llm_analyze.client")
def test_run_llm_analysis_basic(mock_client, mock_store_metrics, mock_connect, mock_input, mock_parsed_files, fake_zip_structure, standard_llm_side_effects, capsys):
    # Use standard LLM responses
    mock_client.chat.completions.create.side_effect = standard_llm_side_effects

    # Mock database connection
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn


    text_llm_analyze.run_text_llm_analysis(mock_parsed_files, fake_zip_structure["zip_path"], classification_id=1)

    captured = capsys.readouterr()

    # Assertions
    assert "Analyzing 1 file(s)" in captured.out
    assert "→ ProjectA" in captured.out
    assert "Summary:" in captured.out
    assert "Skills Demonstrated:" in captured.out
    assert "Success Factors:" in captured.out
    assert "8.2 / 10" in captured.out
    assert "[Main File]" in captured.out

    mock_connect.assert_called_once()
    mock_store_metrics.assert_called_once()
    mock_conn.close.assert_called_once()

@patch("builtins.input", return_value="1")
@patch("src.text_llm_analyze.client")
def test_run_llm_analysis_db(mock_client, mock_input, mock_parsed_files, fake_zip_structure, standard_llm_side_effects):
    import src.db as db

    mock_client.chat.completions.create.side_effect = standard_llm_side_effects

    conn = db.connect()
    user_id = db.get_or_create_user(conn, "test-user-llm")

    db.record_project_classification(conn=conn, user_id=user_id, zip_path=fake_zip_structure["zip_path"], zip_name="Archive", project_name=fake_zip_structure["project_name"], classification="individual")
    classification_id = db.get_classification_id(conn, user_id, fake_zip_structure["project_name"])

    text_llm_analyze.run_text_llm_analysis(mock_parsed_files, fake_zip_structure["zip_path"], classification_id)
    metrics = db.get_text_llm_metrics(conn, classification_id)

    # Verify scalar fields
    assert metrics["project_name"] == "ProjectA"
    assert metrics["file_name"] == "sample.txt"
    assert metrics["file_path"] == "ProjectA/sample.txt"
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

@patch("src.text_llm_analyze.client")
def test_generate_llm_summary(mock_client, mock_llm_responses):
    mock_client.chat.completions.create.return_value = mock_llm_responses(
        "A project proposal that outlines a sustainable design solution."
    )
    result = text_llm_analyze.generate_text_llm_summary("Text about sustainability.")
    assert "project proposal" in result.lower()


@patch("src.text_llm_analyze.client")
def test_generate_llm_skills(mock_client, mock_llm_responses):
    mock_client.chat.completions.create.return_value = mock_llm_responses(
        "- Research\n- Writing\n- Analysis"
    )
    result = text_llm_analyze.generate_text_llm_skills("Some text about research and writing.")
    assert isinstance(result, list)
    assert "Research" in result[0]


@patch("src.text_llm_analyze.client")
def test_generate_llm_success_factors(mock_client, mock_llm_responses):
    fake_json = '{"strengths": "clear structure", "weaknesses": "minor redundancy", "score": "8.1 / 10 (Good clarity)"}'
    mock_client.chat.completions.create.return_value = mock_llm_responses(fake_json)

    linguistic = {"reading_level": "College", "lexical_diversity": 0.4, "word_count": 500}
    result = text_llm_analyze.generate_text_llm_success_factors("Some academic text.", linguistic)
    assert result["strengths"].startswith("clear")
    assert "8.1" in result["score"]
