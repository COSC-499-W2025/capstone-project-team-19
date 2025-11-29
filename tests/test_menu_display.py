import pytest
from unittest.mock import patch
from src.menu.display import show_start_menu


class TestShowStartMenu:
    """Tests for the main menu display functionality."""

    @pytest.mark.parametrize("choice", ["1", "2", "3", "4", "5", "7", "8"])
    def test_valid_menu_choices(self, choice):
        """Test that valid menu choices (1-8) are accepted and returned as integers."""
        username = "testuser"

        with patch("builtins.input", return_value=choice):
            result = show_start_menu(username)
            assert result == int(choice)

    @pytest.mark.parametrize("invalid_input,valid_input", [
        ("0", "1"),  # Number out of range (too low)
        ("9", "2"),  # Number out of range (too high, 6 is reserved)
        ("99", "3"),  # Number out of range (way too high)
        ("-1", "4"),  # Negative number
    ])
    def test_invalid_number_choices(self, invalid_input, valid_input):
        """Test that invalid number choices are rejected and prompt again."""
        username = "testuser"

        with patch("builtins.input", side_effect=[invalid_input, valid_input]):
            with patch("builtins.print") as mock_print:
                result = show_start_menu(username)

                # Should eventually return the valid input
                assert result == int(valid_input)

                # Should print error message for invalid input
                error_calls = [call for call in mock_print.call_args_list
                             if "Invalid choice" in str(call)]
                assert len(error_calls) >= 1

    @pytest.mark.parametrize("invalid_input,valid_input", [
        ("a", "1"),  # Letter
        ("abc", "2"),  # Multiple letters
        ("", "3"),  # Empty string
        (" ", "4"),  # Whitespace only
        ("1.5", "5"),  # Decimal number
        ("one", "8"),  # Word
    ])
    def test_invalid_non_numeric_choices(self, invalid_input, valid_input):
        """Test that non-numeric choices are rejected and prompt again."""
        username = "testuser"

        with patch("builtins.input", side_effect=[invalid_input, valid_input]):
            with patch("builtins.print") as mock_print:
                result = show_start_menu(username)

                # Should eventually return the valid input
                assert result == int(valid_input)

                # Should print error message for invalid input
                error_calls = [call for call in mock_print.call_args_list
                             if "Invalid choice" in str(call)]
                assert len(error_calls) >= 1

    def test_menu_displays_username(self):
        """Test that the menu displays the provided username."""
        username = "alice"

        with patch("builtins.input", return_value="1"):
            with patch("builtins.print") as mock_print:
                show_start_menu(username)

                # Check that welcome message with username was printed
                welcome_calls = [call for call in mock_print.call_args_list
                               if "alice" in str(call)]
                assert len(welcome_calls) >= 1

    def test_menu_displays_all_options(self):
        """Test that all menu options are displayed."""
        username = "testuser"
        expected_options = [
            "1. Analyze new project",
            "2. View old project summaries",
            "3. View resume items",
            "4. View portfolio items",
            "5. Delete old insights",
            "7. View chronological skills",
            "8. Exit"
        ]

        with patch("builtins.input", return_value="1"):
            with patch("builtins.print") as mock_print:
                show_start_menu(username)

                # Get all print calls as strings
                all_prints = [str(call) for call in mock_print.call_args_list]
                combined_output = " ".join(all_prints)

                # Check that all options are mentioned
                for option in expected_options:
                    assert option in combined_output

    def test_input_whitespace_is_stripped(self):
        """Test that whitespace around input is properly stripped."""
        username = "testuser"

        # Input with leading/trailing whitespace
        with patch("builtins.input", return_value="  3  "):
            result = show_start_menu(username)
            assert result == 3

    def test_choice_returns_integer_not_string(self):
        """Test that the function returns an integer, not a string."""
        username = "testuser"

        with patch("builtins.input", return_value="5"):
            result = show_start_menu(username)
            assert isinstance(result, int)
            assert result == 5
            assert not isinstance(result, str)
