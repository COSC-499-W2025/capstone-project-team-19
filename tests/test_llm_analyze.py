import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from src import llm_analyze

@pytest.fixture
def mock_parsed_files():
    """Return a fake parsed_files list similar to what parse_zip_file produces."""
    return [
        {"file_path": "sample.txt", "file_name": "sample.txt", "file_type": "text"}
    ]

@pytest.fixture
def mock_text_file(tmp_path):
    """Create a temporary text file to simulate extracted text input."""
    f = tmp_path / "sample.txt"
    f.write_text("This is a sample document about AI and ethics.")
    return str(f)

@pytest.fixture(autouse=True)
def patch_extractfile_and_metrics(mock_text_file):
    """Patch extractfile() and analyze_linguistic_complexity() for predictable behavior."""
    with patch("src.llm_analyze.extractfile", return_value="Sample text content."), \
         patch("src.llm_analyze.analyze_linguistic_complexity", return_value={
             "word_count": 10,
             "sentence_count": 2,
             "reading_level": "High School",
             "flesch_kincaid_grade": 9.5,
             "lexical_diversity": 0.45
         }):
        yield

@pytest.fixture
def mock_llm_responses():
    """Mock responses for Groq completions."""
    def fake_completion(content):
        fake_choice = MagicMock()
        fake_choice.message.content = content
        mock_response = MagicMock()
        mock_response.choices = [fake_choice]
        return mock_response
    return fake_completion

@patch("src.llm_analyze.client")
def test_run_llm_analysis_basic(mock_client, mock_parsed_files, tmp_path, mock_llm_responses, capsys):
    """Ensure run_llm_analysis runs end-to-end with mocked LLM outputs."""
    # Fake the Groq API responses
    mock_client.chat.completions.create.side_effect = [
        mock_llm_responses("A research essay that explores AI ethics."),
        mock_llm_responses("- Analytical thinking\n- Ethical reasoning\n- Research writing"),
        mock_llm_responses('{"strengths": "clear focus, strong evidence", "weaknesses": "limited depth", "score": "8.2 / 10 (Strong clarity)"}')
    ]

    # Create fake zip directory structure
    zip_dir = tmp_path / "zip_data" / "Archive"
    os.makedirs(zip_dir, exist_ok=True)
    (zip_dir / "sample.txt").write_text("This is a sample document.")

    # Run the analysis
    llm_analyze.run_llm_analysis(mock_parsed_files, str(tmp_path / "Archive.zip"))

    captured = capsys.readouterr()

    # Assertions: ensure each major output section appears
    assert "Analyzing 1 file(s) using LLM-based analysis" in captured.out
    assert "Summary:" in captured.out
    assert "Skills Demonstrated:" in captured.out
    assert "Success Factors:" in captured.out
    assert "8.2 / 10" in captured.out

@patch("src.llm_analyze.client")
def test_generate_llm_summary(mock_client, mock_llm_responses):
    """Test summary generation function directly."""
    mock_client.chat.completions.create.return_value = mock_llm_responses("A project proposal that outlines a sustainable design solution.")
    result = llm_analyze.generate_llm_summary("Text about sustainability.")
    assert "project proposal" in result.lower()

@patch("src.llm_analyze.client")
def test_generate_llm_skills(mock_client, mock_llm_responses):
    """Test skills generation returns list of phrases."""
    mock_client.chat.completions.create.return_value = mock_llm_responses("- Research\n- Writing\n- Analysis")
    result = llm_analyze.generate_llm_skills("Some text about research and writing.")
    assert isinstance(result, list)
    assert "Research" in result[0]

@patch("src.llm_analyze.client")
def test_generate_llm_success_factors(mock_client, mock_llm_responses):
    """Test success factor JSON parsing."""
    fake_json = '{"strengths": "clear structure", "weaknesses": "minor redundancy", "score": "8.1 / 10 (Good clarity)"}'
    mock_client.chat.completions.create.return_value = mock_llm_responses(fake_json)

    linguistic = {"reading_level": "College", "lexical_diversity": 0.4, "word_count": 500}
    result = llm_analyze.generate_llm_success_factors("Some academic text.", linguistic)
    assert result["strengths"].startswith("clear")
    assert "8.1" in result["score"]
