import os
import re
import pytest
from unittest.mock import patch, MagicMock
from src.analysis.code_individual import code_llm_analyze


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


@patch("src.analysis.code_individual.code_llm_analyze.client")
@patch("src.analysis.code_individual.code_llm_analyze.extract_readme_file", return_value="# Portfolio Site\nSimple portfolio.")
@patch("src.analysis.code_individual.code_llm_analyze.extract_code_file", return_value="<!-- header --><script>// nav</script>")
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


@patch("src.analysis.code_individual.code_llm_analyze.client")
def test_generate_code_llm_summary_sanitization(mock_client, mock_llm_response_factory):
    # LLM returns something with role preamble + file/function names
    mock_client.chat.completions.create.return_value = mock_llm_response_factory(
        "As a software developer, I implemented a data pipeline in main.cpp using load_weather_data "
        "and compute_summary from data_utils.py to process CSV inputs."
    )
    ctx = "README + headers: load_weather_data, compute_summary, Matplotlib mentioned."

    result = code_llm_analyze.generate_code_llm_project_summary("", ctx)

    # Sanitizer should remove role preamble and replace file names
    assert not re.match(r"^As\s+an?\s", result, flags=re.IGNORECASE)
    assert "main.cpp" not in result
    assert "data_utils.py" not in result
    assert "the codebase" in result
    assert "\n" not in result.strip()


@patch("src.analysis.code_individual.code_llm_analyze.client")
@patch("src.analysis.code_individual.code_llm_analyze.extract_readme_file", return_value=None)
@patch("src.analysis.code_individual.code_llm_analyze.extract_code_file", return_value=None)
def test_run_code_llm_analysis_no_readable_context(
    mock_extract_code, mock_extract_readme, mock_client, mock_parsed_files_single_project, capsys, tmp_path
):
    zip_path = str(tmp_path / "code_projects.zip")
    code_llm_analyze.run_code_llm_analysis(mock_parsed_files_single_project, zip_path)
    out = capsys.readouterr().out

    assert "No readable code context found. Skipping LLM analysis." in out
    # LLM should not be called
    assert mock_client.chat.completions.create.call_count == 0


@patch("src.analysis.code_individual.code_llm_analyze.client")
@patch("src.analysis.code_individual.code_llm_analyze.extract_readme_file", return_value="Root README")
@patch("src.analysis.code_individual.code_llm_analyze.extract_code_file", return_value="// comment\ndef foo(){}")
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
    
    
@patch("src.analysis.code_individual.code_llm_analyze.client")
def test_contribution_summary_uses_top_files_only(
    mock_client, mock_llm_response_factory, tmp_path, capsys
):
    """
    Ensures that when focus_file_paths is provided (simulating .git top_files),
    ONLY those files are included in the contribution context passed to the LLM.
    """

    # Simulated parsed_files: 3 code files
    parsed_files = [
        {"file_path": "proj/a.py", "file_name": "a.py", "file_type": "code"},
        {"file_path": "proj/b.py", "file_name": "b.py", "file_type": "code"},
        {"file_path": "proj/c.py", "file_name": "c.py", "file_type": "code"},
    ]

    # Fake top 5 files (here only 1)
    focus_paths = ["proj/b.py"]

    # Fake full file contents
    def fake_read(path):
        if path.endswith("b.py"):
            return "print('B FILE CONTENT')"
        return "SHOULD NOT APPEAR"

    # Patch read_file_content so only b.py returns the expected content
    with patch(
        "src.analysis.code_individual.code_llm_analyze.read_file_content",
        side_effect=fake_read,
    ):

        # Returned LLM content doesn't matter; we just need it to run.
        mock_client.chat.completions.create.return_value = \
            mock_llm_response_factory("Implemented logic in b.py")

        zip_path = str(tmp_path / "proj.zip")

        code_llm_analyze.run_code_llm_analysis(
            parsed_files,
            zip_path,
            project_name="proj",
            focus_file_paths=focus_paths,
        )

        # Get LLM prompt input
        args, kwargs = mock_client.chat.completions.create.call_args
        prompt_text = kwargs["messages"][1]["content"]

        # Ensure contribution context includes ONLY the expected file
        assert "B FILE CONTENT" in prompt_text
        assert "SHOULD NOT APPEAR" not in prompt_text
        assert "a.py" not in prompt_text
        assert "c.py" not in prompt_text

