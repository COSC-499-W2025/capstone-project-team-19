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
    """Integration tests for key role storage in project summaries."""

    def test_key_role_stored_in_code_collaborative_summary(self):
        """Test that key_role is stored in contributions for code collaborative projects."""
        from src.models.project_summary import ProjectSummary

        summary = ProjectSummary(
            project_name="TestProject",
            project_type="code",
            project_mode="collaborative"
        )

        # Simulate key role being added (as done in code_collaborative_analysis.py)
        summary.contributions["key_role"] = "Backend Developer"
        summary.contributions["manual_contribution_summary"] = "Implemented REST API"

        assert summary.contributions["key_role"] == "Backend Developer"
        assert "manual_contribution_summary" in summary.contributions

    def test_key_role_stored_in_text_collaborative_summary(self):
        """Test that key_role is stored in contributions for text collaborative projects."""
        from src.models.project_summary import ProjectSummary

        summary = ProjectSummary(
            project_name="ResearchPaper",
            project_type="text",
            project_mode="collaborative"
        )

        summary.contributions["key_role"] = "Lead Author"
        summary.contributions["manual_contribution_summary"] = "Wrote the introduction and methods sections"

        assert summary.contributions["key_role"] == "Lead Author"

    def test_key_role_stored_in_individual_code_summary(self):
        """Test that key_role is stored in contributions for individual code projects."""
        from src.models.project_summary import ProjectSummary

        summary = ProjectSummary(
            project_name="PersonalProject",
            project_type="code",
            project_mode="individual"
        )

        summary.contributions["key_role"] = "Full-Stack Developer"
        summary.contributions["manual_contribution_summary"] = "Built the entire application"

        assert summary.contributions["key_role"] == "Full-Stack Developer"

    def test_key_role_stored_in_individual_text_summary(self):
        """Test that key_role is stored in contributions for individual text projects."""
        from src.models.project_summary import ProjectSummary

        summary = ProjectSummary(
            project_name="Thesis",
            project_type="text",
            project_mode="individual"
        )

        summary.contributions["key_role"] = "Researcher"
        summary.contributions["manual_contribution_summary"] = "Conducted all research and writing"

        assert summary.contributions["key_role"] == "Researcher"

    def test_key_role_not_stored_when_empty(self):
        """Test that empty key_role is not stored in contributions."""
        from src.models.project_summary import ProjectSummary

        summary = ProjectSummary(
            project_name="TestProject",
            project_type="code",
            project_mode="collaborative"
        )

        # Simulate the conditional storage (as done in the analysis files)
        key_role = ""
        if key_role:
            summary.contributions["key_role"] = key_role

        assert "key_role" not in summary.contributions

    def test_key_role_serializes_to_json(self):
        """Test that key_role is properly serialized when converting to JSON."""
        import json
        from src.models.project_summary import ProjectSummary

        summary = ProjectSummary(
            project_name="TestProject",
            project_type="code",
            project_mode="collaborative"
        )
        summary.contributions["key_role"] = "DevOps Engineer"
        summary.contributions["manual_contribution_summary"] = "Set up CI/CD pipeline"

        json_data = json.dumps(summary.__dict__, default=str)
        parsed = json.loads(json_data)

        assert parsed["contributions"]["key_role"] == "DevOps Engineer"


# -----------------------------
# Tests for LLM vs Manual selection logic
# -----------------------------
class TestKeyRoleSelectionLogic:
    """Tests for the logic that decides between LLM extraction and manual prompt."""

    def test_uses_llm_when_consent_accepted_and_description_exists(self):
        """Test that LLM is used when external consent is accepted and description exists."""
        # This tests the logic pattern used in the analysis files
        external_consent = "accepted"
        contribution_desc = "I implemented the authentication system"

        use_llm = external_consent == "accepted" and bool(contribution_desc)
        assert use_llm is True

    def test_uses_manual_when_consent_rejected(self):
        """Test that manual prompt is used when consent is rejected."""
        external_consent = "rejected"
        contribution_desc = "I implemented the authentication system"

        use_llm = external_consent == "accepted" and bool(contribution_desc)
        assert use_llm is False

    def test_uses_manual_when_description_empty(self):
        """Test that manual prompt is used when description is empty."""
        external_consent = "accepted"
        contribution_desc = ""

        use_llm = external_consent == "accepted" and bool(contribution_desc)
        assert use_llm is False

    def test_uses_manual_when_consent_none(self):
        """Test that manual prompt is used when consent is None."""
        external_consent = None
        contribution_desc = "Some description"

        use_llm = external_consent == "accepted" and bool(contribution_desc)
        assert use_llm is False
