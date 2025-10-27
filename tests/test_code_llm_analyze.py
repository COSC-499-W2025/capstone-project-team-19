import os
import re
import pytest
from unittest.mock import patch, MagicMock
from src import code_llm_analyze


@pytest.fixture
def mock_parsed_files_single_project():
    # Simulate files under a project folder inside the zip, e.g. "portfolio-site/"
    return [
        {"file_path": "portfolio-site/index.html", "file_name": "index.html", "file_type": "code"},
        {"file_path": "portfolio-site/style.css", "file_name": "style.css", "file_type": "code"},
        {"file_path": "portfolio-site/script.js", "file_name": "script.js", "file_type": "code"},
    ]


@pytest.fixture
def mock_parsed_files_empty():
    # No code-type files
    return [
        {"file_path": "docs/readme.txt", "file_name": "readme.txt", "file_type": "text"}
    ]


@pytest.fixture
def mock_llm_response_factory():
    def _make(content: str):
        fake_choice = MagicMock()
        fake_choice.message.content = content
        mock_response = MagicMock()
        mock_response.choices = [fake_choice]
        return mock_response
    return _make


@patch("src.code_llm_analyze.client")
@patch("src.code_llm_analyze.extract_readme_file", return_value="# Portfolio Site\nSimple portfolio.")
@patch("src.code_llm_analyze.extract_code_file", return_value="<!-- header --><script>// nav</script>")
def test_run_code_llm_analysis_basic(
    mock_extract_code, mock_extract_readme, mock_client, mock_parsed_files_single_project, mock_llm_response_factory, capsys, tmp_path
):
    mock_client.chat.completions.create.return_value = mock_llm_response_factory(
        "Built a responsive, single-page portfolio site using HTML, CSS, and JavaScript, "
        "implementing interactive navigation and clean layout to showcase work and contact details. "
        "I optimized structure and behavior for clarity and usability, improving how visitors discover projects and reach out."
    )

    zip_path = str(tmp_path / "code_projects.zip")

    code_llm_analyze.run_code_llm_analysis(mock_parsed_files_single_project, zip_path)
    out = capsys.readouterr().out

    assert "Analyzing 3 file(s) using LLM-based analysis" in out
    assert "Project: portfolio-site" in out
    assert "Project: code_projects" not in out
    assert "Summary:" in out
    assert "**" not in out
    assert "-" * 80 in out
    assert "responsive, single-page portfolio site" in out


@patch("src.code_llm_analyze.client")
def test_generate_code_llm_summary_sanitization(mock_client, mock_llm_response_factory):
    # LLM returns something with role preamble + file/function names
    mock_client.chat.completions.create.return_value = mock_llm_response_factory(
        "As a software developer, I implemented a data pipeline in main.cpp using load_weather_data "
        "and compute_summary from data_utils.py to process CSV inputs."
    )
    ctx = "README + headers: load_weather_data, compute_summary, Matplotlib mentioned."

    result = code_llm_analyze.generate_code_llm_summary(ctx)

    # Sanitizer should remove role preamble and replace file names
    assert not re.match(r"^As\s+an?\s", result, flags=re.IGNORECASE)
    assert "main.cpp" not in result
    assert "data_utils.py" not in result
    assert "the codebase" in result
    assert "\n" not in result.strip()


@patch("src.code_llm_analyze.client")
@patch("src.code_llm_analyze.extract_readme_file", return_value=None)
@patch("src.code_llm_analyze.extract_code_file", return_value=None)
def test_run_code_llm_analysis_no_readable_context(
    mock_extract_code, mock_extract_readme, mock_client, mock_parsed_files_single_project, capsys, tmp_path
):
    zip_path = str(tmp_path / "code_projects.zip")
    code_llm_analyze.run_code_llm_analysis(mock_parsed_files_single_project, zip_path)
    out = capsys.readouterr().out

    assert "No readable code context found. Skipping LLM analysis." in out
    # LLM should not be called
    assert mock_client.chat.completions.create.call_count == 0


@patch("src.code_llm_analyze.client")
@patch("src.code_llm_analyze.extract_readme_file", return_value="Root README")
@patch("src.code_llm_analyze.extract_code_file", return_value="// comment\ndef foo(){}")
def test_project_name_comes_from_folder(
    mock_extract_code, mock_extract_readme, mock_client, mock_parsed_files_single_project, mock_llm_response_factory, capsys, tmp_path
):
    mock_client.chat.completions.create.return_value = mock_llm_response_factory(
        "Developed a lightweight web application, leveraging HTML/CSS/JS to showcase projects with interactive navigation and clean layout."
    )
    zip_path = str(tmp_path / "code_projects.zip")
    code_llm_analyze.run_code_llm_analysis(mock_parsed_files_single_project, zip_path)
    out = capsys.readouterr().out

    # Assert we used the folder "portfolio-site" rather than the zip name
    assert "Project: portfolio-site" in out
    assert "Project: code_projects" not in out
