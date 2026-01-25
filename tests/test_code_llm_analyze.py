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

    # New signature: (project_context, readme_tech_ok)
    result = code_llm_analyze.generate_code_llm_project_summary(
        "TECH STACK (evidence-based):\n- Languages: C++\n- Frameworks: Unknown\n\n"
        "### main.cpp ###\n// headers: load_weather_data, compute_summary\n",
        readme_tech_ok=False,
    )

    # Sanitizer should remove role preamble and collapse newlines
    assert not re.match(r"^As\s+an?\s", result, flags=re.IGNORECASE)
    assert "\n" not in result.strip()


@patch("src.analysis.code_individual.code_llm_analyze.client")
@patch("src.analysis.code_individual.code_llm_analyze.extract_readme_file", return_value=None)
@patch("src.analysis.code_individual.code_llm_analyze.extract_code_file", return_value=None)
def test_run_code_llm_analysis_no_readable_context(
    mock_extract_code, mock_extract_readme, mock_client, mock_parsed_files_single_project, capsys, tmp_path, mock_llm_response_factory
):
    """
    Updated behavior: even if README + code snippets are unreadable,
    the function still runs using the TECH STACK block as minimal context.
    """
    mock_client.chat.completions.create.return_value = mock_llm_response_factory(
        "An application that summarizes a project based on minimal context."
    )

    zip_path = str(tmp_path / "code_projects.zip")

    code_llm_analyze.run_code_llm_analysis(mock_parsed_files_single_project, zip_path)
    out = capsys.readouterr().out

    # It should NOT skip anymore (tech stack block keeps project_context non-empty)
    assert "No readable code context found. Skipping LLM analysis." not in out

    # LLM should be called twice: project summary + contribution summary
    assert mock_client.chat.completions.create.call_count == 2

    # Project summary prompt should include TECH STACK evidence block
    _, kwargs0 = mock_client.chat.completions.create.call_args_list[0]
    prompt0 = kwargs0["messages"][1]["content"]
    assert "TECH STACK (evidence-based):" in prompt0


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
@patch("src.analysis.code_individual.code_llm_analyze.extract_readme_file", return_value=None)
@patch("src.analysis.code_individual.code_llm_analyze.extract_code_file", return_value="# header comment\nimport os\n")
def test_contribution_summary_uses_top_files_only(
    mock_extract_code, mock_extract_readme, mock_client, mock_llm_response_factory, tmp_path, capsys
):
    """
    Ensures that when focus_file_paths is provided (simulating .git top_files),
    ONLY those files are included in the contribution context passed to the LLM.
    """

    parsed_files = [
        {"file_path": "proj/a.py", "file_name": "a.py", "file_type": "code"},
        {"file_path": "proj/b.py", "file_name": "b.py", "file_type": "code"},
        {"file_path": "proj/c.py", "file_name": "c.py", "file_type": "code"},
    ]

    focus_paths = ["proj/b.py"]

    def fake_read(path):
        if path.replace("\\", "/").endswith("proj/b.py"):
            return "print('B FILE CONTENT')"
        return "SHOULD NOT APPEAR"

    with patch(
        "src.analysis.code_individual.code_llm_analyze.read_file_content",
        side_effect=fake_read,
    ):
        # Return value doesn't matter; we just need calls to happen.
        mock_client.chat.completions.create.return_value = mock_llm_response_factory(
            "Implemented logic in b.py"
        )

        zip_path = str(tmp_path / "proj.zip")

        code_llm_analyze.run_code_llm_analysis(
            parsed_files,
            zip_path,
            project_name="proj",
            focus_file_paths=focus_paths,
        )

        # LLM called twice: [0]=project summary, [1]=contribution summary
        assert mock_client.chat.completions.create.call_count == 2

        # Check contribution call specifically (second call)
        _, kwargs = mock_client.chat.completions.create.call_args_list[1]
        prompt_text = kwargs["messages"][1]["content"]

        assert "B FILE CONTENT" in prompt_text
        assert "SHOULD NOT APPEAR" not in prompt_text
        assert "a.py" not in prompt_text
        assert "c.py" not in prompt_text


@patch("src.analysis.code_individual.code_llm_analyze.client")
@patch("src.analysis.code_individual.code_llm_analyze.extract_code_file", return_value="// code header\n")
def test_no_project_readme_does_not_fallback_to_zip_root_readme(
    mock_extract_code, mock_client, mock_llm_response_factory, tmp_path
):
    """
    If the project folder has no README, we must NOT fall back to zip-root README,
    otherwise project summaries get contaminated by other projects.
    """

    parsed_files = [
        {"file_path": "portfolio-site/index.html", "file_name": "index.html", "file_type": "code"},
        {"file_path": "portfolio-site/style.css", "file_name": "style.css", "file_type": "code"},
    ]

    # Simulate:
    # - no README in project folder
    # - but a README exists at zip root (should NOT be used)
    def fake_extract_readme(path):
        p = path.replace("\\", "/")
        if p.endswith("/portfolio-site") or p.endswith("/portfolio-site/"):
            return None
        if p.endswith("/code_projects") or p.endswith("/code_projects/"):
            return "ROOT README SHOULD NOT BE USED"
        return None

    with patch(
        "src.analysis.code_individual.code_llm_analyze.extract_readme_file",
        side_effect=fake_extract_readme,
    ):
        mock_client.chat.completions.create.return_value = mock_llm_response_factory(
            "An application that showcases a simple portfolio site."
        )

        zip_path = str(tmp_path / "code_projects.zip")

        code_llm_analyze.run_code_llm_analysis(
            parsed_files,
            zip_path,
            project_name="portfolio-site",
        )

        # First LLM call = project summary
        _, kwargs = mock_client.chat.completions.create.call_args_list[0]
        prompt_text = kwargs["messages"][1]["content"]

        # Ensure zip-root README is NOT used
        assert "ROOT README SHOULD NOT BE USED" not in prompt_text
        # Ensure we fell back to code context (new prompt doesn't include "Source (CODE_CONTEXT)")
        assert "Context (README if available + TECH STACK + code context):" in prompt_text
        # and confirms no README section is present in context
        assert "README:" not in prompt_text
