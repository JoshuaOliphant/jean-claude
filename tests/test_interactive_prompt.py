# ABOUTME: Tests for InteractivePromptHandler
# ABOUTME: Consolidated test suite covering prompting, input parsing, and display

"""Tests for InteractivePromptHandler.

Consolidated test suite - combined from 34 separate tests into focused tests
that cover all essential behaviors without redundant per-input-type testing.
"""

import pytest
from unittest.mock import Mock, patch
from io import StringIO

from jean_claude.core.task_validator import ValidationResult
from jean_claude.core.interactive_prompt_handler import InteractivePromptHandler, PromptAction


class TestPromptAction:
    """Test PromptAction enum - minimal validation."""

    def test_prompt_action_values_are_distinct(self):
        """Test that PromptAction has distinct values."""
        assert PromptAction.PROCEED is not None
        assert PromptAction.EDIT is not None
        assert PromptAction.CANCEL is not None
        assert len({PromptAction.PROCEED, PromptAction.EDIT, PromptAction.CANCEL}) == 3


class TestInteractivePromptHandlerInit:
    """Test initialization - consolidated from 3 tests to 1."""

    def test_init_with_and_without_formatter(self):
        """Test handler initialization with default and custom formatter."""
        from jean_claude.core.validation_output_formatter import ValidationOutputFormatter

        # Default formatter
        handler = InteractivePromptHandler()
        assert handler is not None
        assert handler.formatter is not None

        # Custom formatter
        custom_formatter = ValidationOutputFormatter()
        handler2 = InteractivePromptHandler(formatter=custom_formatter)
        assert handler2.formatter is custom_formatter


class TestInteractivePromptHandlerPromptReturns:
    """Test that prompt() returns correct actions - consolidated from 5 tests to 1."""

    @pytest.mark.parametrize("input_value,expected_action", [
        ("1", PromptAction.PROCEED),
        ("2", PromptAction.EDIT),
        ("3", PromptAction.CANCEL),
        ("proceed", PromptAction.PROCEED),
        ("edit", PromptAction.EDIT),
        ("cancel", PromptAction.CANCEL),
        ("PROCEED", PromptAction.PROCEED),  # Case insensitive
        (" 1 ", PromptAction.PROCEED),  # Handles whitespace
    ])
    @patch('sys.stdout', new_callable=StringIO)
    def test_prompt_returns_correct_action(self, mock_stdout, input_value, expected_action):
        """Test that prompt returns correct action for various inputs."""
        with patch('builtins.input', return_value=input_value):
            handler = InteractivePromptHandler()
            result = ValidationResult(warnings=["Warning"])
            action = handler.prompt(result)
            assert action == expected_action


class TestInteractivePromptHandlerDisplay:
    """Test display behavior - consolidated from 3 tests to 1."""

    @patch('builtins.input', return_value='1')
    @patch('sys.stdout', new_callable=StringIO)
    def test_prompt_displays_warnings_errors_and_options(self, mock_stdout, mock_input):
        """Test that prompt displays all validation information and options."""
        handler = InteractivePromptHandler()
        result = ValidationResult(
            is_valid=False,
            warnings=["Test warning"],
            errors=["Test error"]
        )

        handler.prompt(result)

        output = mock_stdout.getvalue()
        # Should show warnings and errors
        assert "Test warning" in output
        assert "Test error" in output
        # Should show options
        output_lower = output.lower()
        assert any(word in output_lower for word in ["proceed", "[1]"])
        assert any(word in output_lower for word in ["edit", "[2]"])
        assert any(word in output_lower for word in ["cancel", "[3]"])


class TestInteractivePromptHandlerInvalidInput:
    """Test invalid input handling - consolidated from multiple tests to 1."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_prompt_reprompts_on_invalid_input(self, mock_stdout):
        """Test that invalid inputs cause reprompting."""
        # Test various invalid inputs followed by valid input
        invalid_inputs = ['invalid', '0', '4', '-1', '99', '', 'abc']
        with patch('builtins.input', side_effect=[*invalid_inputs, '2']):
            handler = InteractivePromptHandler()
            result = ValidationResult(warnings=["Warning"])
            action = handler.prompt(result)

            assert action == PromptAction.EDIT

        output = mock_stdout.getvalue().lower()
        # Should show some kind of error/reprompt message
        assert any(word in output for word in ["invalid", "please", "try again", "choose"])


class TestInteractivePromptHandlerEdgeCases:
    """Test edge cases - consolidated from 3 tests to 1."""

    @patch('builtins.input', return_value='1')
    @patch('sys.stdout', new_callable=StringIO)
    def test_prompt_handles_various_validation_states(self, mock_stdout, mock_input):
        """Test prompt with empty, single, and multiple warnings."""
        handler = InteractivePromptHandler()

        # Empty result
        result1 = ValidationResult()
        action1 = handler.prompt(result1)
        assert action1 in [PromptAction.PROCEED, PromptAction.EDIT, PromptAction.CANCEL]

        # Multiple warnings
        result2 = ValidationResult(warnings=[f"Warning {i}" for i in range(5)])
        action2 = handler.prompt(result2)
        output = mock_stdout.getvalue()
        assert "Warning 0" in output
        assert "Warning 4" in output


class TestInteractivePromptHandlerIntegration:
    """Integration tests - consolidated from 3 tests to 1."""

    @patch('builtins.input', return_value='1')
    @patch('sys.stdout', new_callable=StringIO)
    def test_realistic_warning_scenario(self, mock_stdout, mock_input):
        """Test realistic scenario with task validation warnings."""
        handler = InteractivePromptHandler()
        result = ValidationResult(
            warnings=[
                "Task description is short (25 chars). Consider adding more detail.",
                "No acceptance criteria found.",
                "No mention of testing or verification found."
            ]
        )

        action = handler.prompt(result)

        output = mock_stdout.getvalue()
        assert "Task description is short" in output
        assert "No acceptance criteria" in output
        assert action == PromptAction.PROCEED


class TestInteractivePromptHandlerCustomFormatter:
    """Test custom formatter - kept as single test."""

    @patch('builtins.input', return_value='1')
    @patch('sys.stdout', new_callable=StringIO)
    def test_prompt_uses_custom_formatter(self, mock_stdout, mock_input):
        """Test that prompt uses custom formatter if provided."""
        from jean_claude.core.validation_output_formatter import ValidationOutputFormatter

        formatter = ValidationOutputFormatter(use_color=False)
        handler = InteractivePromptHandler(formatter=formatter)
        result = ValidationResult(warnings=["Warning"])

        handler.prompt(result)

        output = mock_stdout.getvalue()
        assert "\033[" not in output  # No ANSI color codes
        assert "Warning" in output


class TestInteractivePromptHandlerNonInteractive:
    """Test non-interactive mode - consolidated from 2 tests to 1."""

    def test_prompt_handles_eof_and_keyboard_interrupt(self):
        """Test that prompt handles non-interactive scenarios."""
        handler = InteractivePromptHandler()
        result = ValidationResult(warnings=["Warning"])

        # Test EOFError
        with patch('builtins.input', side_effect=EOFError()):
            try:
                action = handler.prompt(result)
                assert action in [PromptAction.PROCEED, PromptAction.EDIT, PromptAction.CANCEL]
            except EOFError:
                pass  # OK to raise

        # Test KeyboardInterrupt
        with patch('builtins.input', side_effect=KeyboardInterrupt()):
            try:
                action = handler.prompt(result)
                assert action == PromptAction.CANCEL
            except KeyboardInterrupt:
                pass  # OK to raise
