# ABOUTME: ValidationOutputFormatter for formatting validation results
# ABOUTME: Formats validation warnings and errors into user-friendly console output

"""Validation output formatting for Beads task validation.

This module provides formatting capabilities to display validation results
in a user-friendly way with colors, numbered lists, and interactive options.
"""

import sys
from typing import Optional

from jean_claude.core.task_validator import ValidationResult


class ValidationOutputFormatter:
    """Formats validation results for console output.

    Features:
    - Colored output (warnings in yellow, errors in red)
    - Numbered list of issues
    - Interactive options menu (proceed/edit/cancel)
    - Customizable formatting
    """

    # ANSI color codes
    COLOR_RESET = "\033[0m"
    COLOR_RED = "\033[31m"
    COLOR_YELLOW = "\033[33m"
    COLOR_GREEN = "\033[32m"
    COLOR_CYAN = "\033[36m"
    COLOR_BOLD = "\033[1m"

    def __init__(
        self,
        use_color: bool = True,
        indent: str = "  ",
        use_numbering: bool = True,
        number_style: str = "{n}."
    ):
        """Initialize the formatter.

        Args:
            use_color: Whether to use ANSI color codes (default: True)
            indent: Indentation string for list items (default: "  ")
            use_numbering: Whether to number items (default: True)
            number_style: Format string for numbers, e.g., "{n}." or "{n})" (default: "{n}.")
        """
        self.use_color = use_color
        self.indent = indent
        self.use_numbering = use_numbering
        self.number_style = number_style

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled.

        Args:
            text: Text to colorize
            color: ANSI color code

        Returns:
            Colored text if use_color is True, plain text otherwise
        """
        if not self.use_color:
            return text
        return f"{color}{text}{self.COLOR_RESET}"

    def _format_list_item(self, index: int, text: str) -> str:
        """Format a single list item with numbering.

        Args:
            index: Item index (0-based)
            text: Item text

        Returns:
            Formatted list item
        """
        if self.use_numbering:
            number = self.number_style.format(n=index + 1)
            return f"{self.indent}{number} {text}"
        else:
            return f"{self.indent}- {text}"

    def format(self, result: ValidationResult) -> str:
        """Format validation result as a string.

        Args:
            result: ValidationResult to format

        Returns:
            Formatted string with warnings and errors
        """
        lines = []

        # Handle no issues case
        if not result.has_warnings() and not result.has_errors():
            return self._colorize("✓ No issues found. Task validation passed.", self.COLOR_GREEN)

        # Format errors first (if any)
        if result.has_errors():
            header = self._colorize("ERRORS:", self.COLOR_RED + self.COLOR_BOLD)
            lines.append(header)
            for i, error in enumerate(result.errors):
                if error:  # Skip empty strings
                    error_line = self._format_list_item(i, error)
                    lines.append(self._colorize(error_line, self.COLOR_RED))

        # Format warnings
        if result.has_warnings():
            if lines:  # Add spacing if we already have errors
                lines.append("")
            header = self._colorize("WARNINGS:", self.COLOR_YELLOW + self.COLOR_BOLD)
            lines.append(header)
            for i, warning in enumerate(result.warnings):
                if warning:  # Skip empty strings
                    warning_line = self._format_list_item(i, warning)
                    lines.append(self._colorize(warning_line, self.COLOR_YELLOW))

        return "\n".join(lines)

    def format_with_options(self, result: ValidationResult) -> str:
        """Format validation result with interactive options menu.

        Args:
            result: ValidationResult to format

        Returns:
            Formatted string with warnings/errors and options menu
        """
        lines = []

        # Add the formatted validation result
        formatted_result = self.format(result)
        lines.append(formatted_result)

        # Add spacing
        lines.append("")

        # Add options menu
        if result.has_errors():
            # With errors, show all options but emphasize that errors are serious
            lines.append(self._colorize("Validation found errors. What would you like to do?", self.COLOR_BOLD))
        else:
            # With only warnings
            lines.append(self._colorize("Validation found warnings. What would you like to do?", self.COLOR_BOLD))

        lines.append("")

        # Format the three options
        option_1 = self._colorize("[1]", self.COLOR_CYAN) + " Proceed anyway"
        option_2 = self._colorize("[2]", self.COLOR_CYAN) + " Open task for editing"
        option_3 = self._colorize("[3]", self.COLOR_CYAN) + " Cancel"

        lines.append(option_1)
        lines.append(option_2)
        lines.append(option_3)

        return "\n".join(lines)

    def print_formatted(self, result: ValidationResult) -> None:
        """Print formatted validation result to stdout.

        Args:
            result: ValidationResult to format and print
        """
        output = self.format(result)
        print(output)

    def print_with_options(self, result: ValidationResult) -> None:
        """Print formatted validation result with options menu to stdout.

        Args:
            result: ValidationResult to format and print
        """
        output = self.format_with_options(result)
        print(output)
