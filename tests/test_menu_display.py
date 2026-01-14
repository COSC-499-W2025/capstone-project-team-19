import pytest
from unittest.mock import patch
from src.menu.display import show_start_menu


class TestShowStartMenu:
    """Tests for the main menu display functionality."""

    @pytest.mark.parametrize("choice", [str(i) for i in range(1, 12)])
    def test_valid_menu_choices(self, choice):
        """Test that valid menu choices (1-11) are accepted and returned as integers."""
        username = "testuser"

        with patch("builtins.input", return_value=choice):
            result = show_start_menu(username)
            assert result == int(choice)

    @pytest.mark.parametrize("invalid_input,valid_input", [
        ("0", "1"),    # Number out of range (too low)
        ("12", "2"),   # Number out of range (too high)
        ("99", "3"),   # Number out of range (way too high)
        ("-1", "4"),   # Negative number
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
                error_calls = [
                    call for call in mock_print.call_args_list
                    if "Invalid choice" in str(call)
                ]
                assert len(error_calls) >= 1

    @pytest.mark.parametrize("invalid_input,valid_input", [
        ("a", "1"),       # Letter
        ("abc", "2"),     # Multiple letters
        ("", "3"),        # Empty string
        (" ", "4"),       # Whitespace only
        ("1.5", "5"),     # Decimal number
        ("one", "10"),    # Word
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
                error_calls = [
                    call for call in mock_print.call_args_list
                    if "Invalid choice" in str(call)
                ]
                assert len(error_calls) >= 1

    def test_menu_displays_username(self):
        """Test that the menu displays the provided username."""
        username = "alice"

        with patch("builtins.input", return_value="1"):
            with patch("builtins.print") as mock_print:
                show_start_menu(username)

                welcome_calls = [
                    call for call in mock_print.call_args_list
                    if "alice" in str(call)
                ]
                assert len(welcome_calls) >= 1

    def test_menu_displays_all_options(self):
        """Test that all menu options are displayed."""
        username = "testuser"
        expected_options = [
            "1. Analyze new project",
            "2. View old project summaries",
            "3. View resume items",
            "4. View portfolio items",
            "5. View project feedback",
            "6. Delete old insights",
            "7. View all projects ranked",
            "8. View chronological skills",
            "9. Edit project dates",
            "10. View all projects",
            "11. Exit",
        ]

        with patch("builtins.input", return_value="1"):
            with patch("builtins.print") as mock_print:
                show_start_menu(username)

                all_prints = [str(call) for call in mock_print.call_args_list]
                combined_output = " ".join(all_prints)

                for option in expected_options:
                    assert option in combined_output

    def test_input_whitespace_is_stripped(self):
        """Test that whitespace around input is properly stripped."""
        username = "testuser"

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

