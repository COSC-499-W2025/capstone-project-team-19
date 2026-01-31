"""
Tests for the key role extraction feature.

Tests cover:
1. LLM-based role extraction (extract_key_role_llm)
2. Manual role prompt (prompt_key_role)
3. Integration with project summaries
"""

import builtins
import pytest
from unittest.mock import patch, MagicMock


# -----------------------------
# Test helpers
# -----------------------------
def _create_summary(project_name: str, project_type: str, project_mode: str):
    """Create a ProjectSummary for testing."""
    from src.models.project_summary import ProjectSummary
    return ProjectSummary(
        project_name=project_name,
        project_type=project_type,
        project_mode=project_mode
    )


def _setup_text_analysis_mocks(monkeypatch):
    """Set up common mocks for run_text_analysis tests."""
    monkeypatch.setattr(
        "src.project_analysis._fetch_files",
        lambda *args, **kwargs: [{"file_name": "doc.txt", "content": "Sample text content"}]
    )
    monkeypatch.setattr(
        "src.project_analysis.analyze_files",
        lambda *args, **kwargs: None
    )


def _setup_code_analysis_mocks(monkeypatch):
    """Set up common mocks for run_code_analysis tests."""
    monkeypatch.setattr("src.project_analysis.detect_languages", lambda *args: ["Python"])
    monkeypatch.setattr("src.project_analysis.detect_frameworks", lambda *args: [])
    monkeypatch.setattr(
        "src.project_analysis._fetch_files",
        lambda *args, **kwargs: [{"file_name": "main.py", "content": "x=1"}]
    )
    monkeypatch.setattr("src.project_analysis.analyze_files", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "src.project_analysis.build_activity_summary",
        lambda *args, **kwargs: MagicMock(per_activity={})
    )
    monkeypatch.setattr("src.project_analysis.format_activity_summary", lambda x: "")
    monkeypatch.setattr("src.project_analysis.store_code_activity_metrics", lambda *args: None)
    monkeypatch.setattr("src.project_analysis.extract_skills", lambda *args: None)
    monkeypatch.setattr(
        "src.project_analysis.prompt_manual_code_project_summary",
        lambda proj: "Manual summary"
    )


# -----------------------------
# Tests for extract_key_role_llm
# -----------------------------
class TestExtractKeyRoleLLM:
    """Tests for the LLM-based key role extraction function."""

    def test_extract_key_role_llm_returns_role_from_description(self):
        """Test that LLM extracts a role from a contribution description."""
        from src.analysis.text_individual.llm_summary import extract_key_role_llm

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Backend Developer"

        with patch("src.analysis.text_individual.llm_summary.client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_completion

            result = extract_key_role_llm("I implemented the REST API endpoints and database models")

            assert result == "Backend Developer"
            mock_client.chat.completions.create.assert_called_once()

    def test_extract_key_role_llm_strips_quotes_and_punctuation(self):
        """Test that extracted role is cleaned of quotes and punctuation."""
        from src.analysis.text_individual.llm_summary import extract_key_role_llm

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = '"Lead Author".'

        with patch("src.analysis.text_individual.llm_summary.client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_completion

            result = extract_key_role_llm("I wrote the main thesis chapters")

            assert result == "Lead Author"

    def test_extract_key_role_llm_returns_empty_for_empty_input(self):
        """Test that empty input returns empty string without calling LLM."""
        from src.analysis.text_individual.llm_summary import extract_key_role_llm

        with patch("src.analysis.text_individual.llm_summary.client") as mock_client:
            result = extract_key_role_llm("")
            assert result == ""
            mock_client.chat.completions.create.assert_not_called()

            result = extract_key_role_llm("   ")
            assert result == ""
            mock_client.chat.completions.create.assert_not_called()

    def test_extract_key_role_llm_returns_empty_on_exception(self):
        """Test that exceptions are handled gracefully and return empty string."""
        from src.analysis.text_individual.llm_summary import extract_key_role_llm

        with patch("src.analysis.text_individual.llm_summary.client") as mock_client:
            mock_client.chat.completions.create.side_effect = Exception("API Error")

            result = extract_key_role_llm("Some contribution description")

            assert result == ""

    def test_extract_key_role_llm_truncates_long_input(self):
        """Test that very long input is truncated to 2000 characters."""
        from src.analysis.text_individual.llm_summary import extract_key_role_llm

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Data Analyst"

        long_description = "A" * 5000  # 5000 characters

        with patch("src.analysis.text_individual.llm_summary.client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_completion

            result = extract_key_role_llm(long_description)

            # Verify the call was made
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args.kwargs["messages"]
            user_content = messages[1]["content"]

            # The truncated description should be at most 2000 chars in the prompt
            assert "A" * 2000 in user_content
            assert "A" * 2001 not in user_content


# -----------------------------
# Tests for prompt_key_role
# -----------------------------
class TestPromptKeyRole:
    """Tests for the manual key role prompt function."""

    def test_prompt_key_role_returns_user_input(self):
        """Test that prompt_key_role returns the user's input."""
        from src.analysis.code_collaborative.code_collaborative_analysis_helper import prompt_key_role

        with patch.object(builtins, "input", return_value="Frontend Developer"):
            result = prompt_key_role("MyProject")
            assert result == "Frontend Developer"

    def test_prompt_key_role_strips_whitespace(self):
        """Test that whitespace is stripped from input."""
        from src.analysis.code_collaborative.code_collaborative_analysis_helper import prompt_key_role

        with patch.object(builtins, "input", return_value="  Data Scientist  "):
            result = prompt_key_role("MyProject")
            assert result == "Data Scientist"

    def test_prompt_key_role_returns_empty_on_eof(self):
        """Test that EOFError returns empty string."""
        from src.analysis.code_collaborative.code_collaborative_analysis_helper import prompt_key_role

        with patch.object(builtins, "input", side_effect=EOFError):
            result = prompt_key_role("MyProject")
            assert result == ""

    def test_prompt_key_role_returns_empty_for_blank_input(self):
        """Test that blank input returns empty string."""
        from src.analysis.code_collaborative.code_collaborative_analysis_helper import prompt_key_role

        with patch.object(builtins, "input", return_value=""):
            result = prompt_key_role("MyProject")
            assert result == ""


# -----------------------------
# Integration tests for key role storage
# -----------------------------
class TestKeyRoleIntegration:
    """Integration tests for key role storage via actual analysis entrypoints."""

    def test_key_role_set_via_llm_in_individual_text_analysis(self, monkeypatch):
        """Test that key_role is set via LLM when consent accepted in run_text_analysis."""
        from src.project_analysis import run_text_analysis

        summary = _create_summary("TestProject", "text", "individual")
        _setup_text_analysis_mocks(monkeypatch)

        inputs = iter(["I wrote the research methodology section"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        monkeypatch.setattr("src.project_analysis.extract_key_role_llm", lambda desc: "Lead Researcher")

        run_text_analysis(
            conn=MagicMock(),
            user_id=1,
            project_name="TestProject",
            current_ext_consent="accepted",
            zip_path="/fake/path.zip",
            summary=summary
        )

        assert summary.contributions["key_role"] == "Lead Researcher"
        assert summary.contributions["manual_contribution_summary"] == "I wrote the research methodology section"

    def test_key_role_set_via_manual_prompt_in_individual_code_analysis(self, monkeypatch):
        """Test that key_role is set via manual prompt when consent rejected in run_code_analysis."""
        from src.project_analysis import run_code_analysis

        summary = _create_summary("CodeProject", "code", "individual")
        _setup_code_analysis_mocks(monkeypatch)

        inputs = iter([""])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        monkeypatch.setattr("src.project_analysis.prompt_key_role", lambda proj: "Backend Developer")

        run_code_analysis(
            conn=MagicMock(),
            user_id=1,
            project_name="CodeProject",
            current_ext_consent="rejected",
            zip_path="/fake/path.zip",
            summary=summary
        )

        assert summary.contributions["key_role"] == "Backend Developer"

    def test_key_role_not_set_when_empty_in_individual_text_analysis(self, monkeypatch):
        """Test that key_role is not set when user provides empty role."""
        from src.project_analysis import run_text_analysis

        summary = _create_summary("TestProject", "text", "individual")
        _setup_text_analysis_mocks(monkeypatch)

        inputs = iter([""])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        monkeypatch.setattr("src.project_analysis.prompt_key_role", lambda proj: "")

        run_text_analysis(
            conn=MagicMock(),
            user_id=1,
            project_name="TestProject",
            current_ext_consent="rejected",
            zip_path="/fake/path.zip",
            summary=summary
        )

        assert "key_role" not in summary.contributions

    def test_key_role_serializes_to_json_after_analysis(self, monkeypatch):
        """Test that key_role from analysis is properly serialized to JSON."""
        import json
        from src.project_analysis import run_text_analysis

        summary = _create_summary("TestProject", "text", "individual")
        _setup_text_analysis_mocks(monkeypatch)

        inputs = iter(["Set up CI/CD pipeline"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        monkeypatch.setattr("src.project_analysis.extract_key_role_llm", lambda desc: "DevOps Engineer")

        run_text_analysis(
            conn=MagicMock(),
            user_id=1,
            project_name="TestProject",
            current_ext_consent="accepted",
            zip_path="/fake/path.zip",
            summary=summary
        )

        json_data = json.dumps(summary.__dict__, default=str)
        parsed = json.loads(json_data)

        assert parsed["contributions"]["key_role"] == "DevOps Engineer"


# -----------------------------
# Tests for LLM vs Manual selection logic
# -----------------------------
class TestKeyRoleSelectionLogic:
    """Tests for the actual LLM vs manual selection logic in analysis functions."""

    def test_llm_called_when_consent_accepted_and_description_exists(self, monkeypatch):
        """Test that extract_key_role_llm is called when consent accepted and description exists."""
        from src.project_analysis import run_text_analysis

        summary = _create_summary("TestProject", "text", "individual")
        _setup_text_analysis_mocks(monkeypatch)

        inputs = iter(["I implemented the authentication system"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        llm_called = {"value": False}

        def mock_extract_key_role_llm(desc):
            llm_called["value"] = True
            return "Auth Developer"

        monkeypatch.setattr("src.project_analysis.extract_key_role_llm", mock_extract_key_role_llm)
        monkeypatch.setattr("src.project_analysis.prompt_key_role", lambda proj: "Should Not Be Called")

        run_text_analysis(
            conn=MagicMock(),
            user_id=1,
            project_name="TestProject",
            current_ext_consent="accepted",
            zip_path="/fake/path.zip",
            summary=summary
        )

        assert llm_called["value"] is True
        assert summary.contributions["key_role"] == "Auth Developer"

    def test_manual_prompt_called_when_consent_rejected(self, monkeypatch):
        """Test that prompt_key_role is called when consent is rejected."""
        from src.project_analysis import run_code_analysis

        summary = _create_summary("TestProject", "code", "individual")
        _setup_code_analysis_mocks(monkeypatch)

        inputs = iter(["I built the backend"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        prompt_called = {"value": False}

        def mock_prompt_key_role(proj):
            prompt_called["value"] = True
            return "Backend Dev"

        monkeypatch.setattr("src.project_analysis.extract_key_role_llm", lambda desc: "Should Not Be Called")
        monkeypatch.setattr("src.project_analysis.prompt_key_role", mock_prompt_key_role)

        run_code_analysis(
            conn=MagicMock(),
            user_id=1,
            project_name="TestProject",
            current_ext_consent="rejected",
            zip_path="/fake/path.zip",
            summary=summary
        )

        assert prompt_called["value"] is True
        assert summary.contributions["key_role"] == "Backend Dev"

    def test_manual_prompt_called_when_description_empty(self, monkeypatch):
        """Test that prompt_key_role is called when description is empty (even with consent)."""
        from src.project_analysis import run_text_analysis

        summary = _create_summary("TestProject", "text", "individual")
        _setup_text_analysis_mocks(monkeypatch)

        inputs = iter([""])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        prompt_called = {"value": False}

        def mock_prompt_key_role(proj):
            prompt_called["value"] = True
            return "Manual Role"

        monkeypatch.setattr("src.project_analysis.extract_key_role_llm", lambda desc: "LLM Should Not Be Called")
        monkeypatch.setattr("src.project_analysis.prompt_key_role", mock_prompt_key_role)

        run_text_analysis(
            conn=MagicMock(),
            user_id=1,
            project_name="TestProject",
            current_ext_consent="accepted",  # consent accepted but no description
            zip_path="/fake/path.zip",
            summary=summary
        )

        assert prompt_called["value"] is True
        assert summary.contributions["key_role"] == "Manual Role"

    def test_manual_prompt_called_when_consent_none(self, monkeypatch):
        """Test that prompt_key_role is called when consent is None."""
        from src.project_analysis import run_text_analysis

        summary = _create_summary("TestProject", "text", "individual")
        _setup_text_analysis_mocks(monkeypatch)

        inputs = iter(["Some description"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        prompt_called = {"value": False}

        def mock_prompt_key_role(proj):
            prompt_called["value"] = True
            return "Prompted Role"

        monkeypatch.setattr("src.project_analysis.extract_key_role_llm", lambda desc: "LLM Should Not Be Called")
        monkeypatch.setattr("src.project_analysis.prompt_key_role", mock_prompt_key_role)

        run_text_analysis(
            conn=MagicMock(),
            user_id=1,
            project_name="TestProject",
            current_ext_consent=None,  # consent is None
            zip_path="/fake/path.zip",
            summary=summary
        )

        assert prompt_called["value"] is True
        assert summary.contributions["key_role"] == "Prompted Role"
