import os
import json
import pytest
from unittest.mock import patch, MagicMock
from src import text_llm_analyze
from src.helpers import extractfromcsv


@pytest.fixture
def mock_parsed_files():
    # include project folder in file path for new grouping logic
    return [
        {"file_path": "ProjectA/sample.txt", "file_name": "sample.txt", "file_type": "text"}
    ]


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


@patch("builtins.input", return_value="1")
@patch("src.text_llm_analyze.client")
def test_run_llm_analysis_basic(mock_client, mock_input, mock_parsed_files, tmp_path, mock_llm_responses, capsys):
    # Fake the Groq API responses
    mock_client.chat.completions.create.side_effect = [
        mock_llm_responses("A research essay that explores AI ethics."),
        mock_llm_responses("- Analytical thinking\n- Ethical reasoning\n- Research writing"),
        mock_llm_responses('{"strengths": ["clear focus", "strong evidence"], "weaknesses": ["limited depth"], "score": "8.2 / 10 (Strong clarity)"}')
    ]

    # Create fake zip directory structure
    zip_dir = tmp_path / "zip_data" / "Archive"
    project_dir = zip_dir / "ProjectA"
    os.makedirs(project_dir, exist_ok=True)
    (project_dir / "sample.txt").write_text("This is a sample document.")

    text_llm_analyze.run_text_llm_analysis(mock_parsed_files, str(tmp_path / "Archive.zip"))

    captured = capsys.readouterr()

    # Assertions
    assert "Analyzing 1 file(s)" in captured.out
    assert "→ ProjectA" in captured.out
    assert "Summary:" in captured.out
    assert "Skills Demonstrated:" in captured.out
    assert "Success Factors:" in captured.out
    assert "8.2 / 10" in captured.out

# tests if csv files return metadata (headers, missing data pct, etc.) -> if csv included
def test_extract_text_file_csv_metadata(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("a,b,c\n1,2,3\n4,,6\n7,8,9")

    result = extractfromcsv(str(csv_path))

    assert isinstance(result, dict)
    assert "headers" in result
    assert "missing_pct" in result
    assert result["row_count"] == 3

# tests if csv summaries are included in llm prompt (if csv included)
@patch("src.text_llm_analyze.client")
def test_generate_llm_success_factors_includes_csv_summary(mock_client, mock_llm_responses):
    mock_client.chat.completions.create.return_value = mock_llm_responses(
        '{"strengths": ["good data use"], "weaknesses": ["missing rows"], "score": "8.0 / 10"}'
    )

    csv_summary = {
        "filename": "data.csv",
        "text": {
            "headers": ["a", "b", "c"],
            "row_count": 3,
            "col_count": 3,
            "missing_pct": 12.5,
            "dtypes": {"a": "int", "b": "float", "c": "int"}
        }
    }

    linguistic = {"reading_level": "College", "lexical_diversity": 0.4, "word_count": 500}
    _ = text_llm_analyze.generate_text_llm_success_factors("Academic text", linguistic, [csv_summary])

    prompt_arg = mock_client.chat.completions.create.call_args[1]["messages"][1]["content"]
    assert "[CSV DATA SUMMARY]" in prompt_arg or "Columns:" in prompt_arg


@patch("builtins.input", return_value="")
@patch("os.path.getsize", side_effect=lambda path: 200 if "main" in path else 100)
@patch("src.text_llm_analyze.client")

# tests if largest file is auto-selected when user presses Enter
def test_auto_select_largest_file(mock_client, mock_getsize, mock_input, tmp_path, mock_llm_responses):
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

    text_llm_analyze.run_text_llm_analysis(parsed, str(tmp_path / "Archive.zip"))

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

    text_llm_analyze.run_text_llm_analysis(parsed_files, str(tmp_path / "Archive.zip"))

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

# tests if LLM skills generation works as expected (no csv)
@patch("src.text_llm_analyze.client")
def test_generate_llm_skills(mock_client, mock_llm_responses):
    mock_client.chat.completions.create.return_value = mock_llm_responses(
        "- Research\n- Writing\n- Analysis"
    )
    result = text_llm_analyze.generate_text_llm_skills("Some text about research and writing.")
    assert isinstance(result, list)
    assert "Research" in result[0]

# tests if LLM success factors generation works as expected (no csv)
@patch("src.text_llm_analyze.client")
def test_generate_llm_success_factors(mock_client, mock_llm_responses):
    fake_json = '{"strengths": "clear structure", "weaknesses": "minor redundancy", "score": "8.1 / 10 (Good clarity)"}'
    mock_client.chat.completions.create.return_value = mock_llm_responses(fake_json)

    linguistic = {"reading_level": "College", "lexical_diversity": 0.4, "word_count": 500}
    result = text_llm_analyze.generate_text_llm_success_factors("Some academic text.", linguistic)
    assert result["strengths"].startswith("clear")
    assert "8.1" in result["score"]
    
# tests if output prints the right project_name
def test_project_name_extraction_correctness(tmp_path, capsys):
    base = tmp_path / "zip_data" / "Archive" / "projects-root" / "Study Notes"
    os.makedirs(base, exist_ok=True)
    (base / "essay.txt").write_text("Essay content here.")

    parsed_files = [
        {"file_path": "projects-root/Study Notes/essay.txt", "file_name": "essay.txt", "file_type": "text"},
    ]

    # patch extract_text_file so it doesn’t actually read files (not necessary for this test)
    with patch("src.text_llm_analyze.extract_text_file", return_value="Dummy text"):
        text_llm_analyze.run_text_llm_analysis(parsed_files, str(tmp_path / "Archive.zip"))

    captured = capsys.readouterr().out

    assert "→ Study Notes" in captured or "Project: Study Notes" in captured
    assert "projects-root" not in captured

