# ABOUTME: InteractivePromptHandler for handling user input during validation
# ABOUTME: Displays validation warnings and offers options to proceed, edit, or cancel

"""Interactive prompt handler for Beads task validation.

This module provides interactive prompting capabilities to display validation
results and collect user input for how to proceed.
"""

from enum import Enum
from typing import Optional

from jean_claude.core.task_validator import ValidationResult
from jean_claude.core.validation_output_formatter import ValidationOutputFormatter


class PromptAction(Enum):
    """User actions in response to validation warnings."""

    PROCEED = "proceed"  # Continue with work despite warnings
    EDIT = "edit"  # Open task for editing
    CANCEL = "cancel"  # Cancel the operation


class InteractivePromptHandler:
    """Handles interactive prompts for validation warnings.

    Features:
    - Displays validation results with formatting
    - Presents three options: Proceed, Edit, Cancel
    - Validates user input
    - Returns chosen action
    """

    def __init__(self, formatter: Optional[ValidationOutputFormatter] = None):
        """Initialize the prompt handler.

        Args:
            formatter: Optional ValidationOutputFormatter for formatting output.
                      If not provided, creates a default formatter.
        """
        self.formatter = formatter if formatter is not None else ValidationOutputFormatter()

    def prompt(self, result: ValidationResult) -> PromptAction:
        """Display validation results and prompt user for action.

        Args:
            result: ValidationResult to display

        Returns:
            PromptAction chosen by the user

        Raises:
            EOFError: If running in non-interactive environment
            KeyboardInterrupt: If user cancels with Ctrl+C
        """
        # Display the formatted validation results with options
        output = self.formatter.format_with_options(result)
        print(output)
        print()  # Extra line for spacing

        # Prompt for user input
        while True:
            try:
                user_input = input("Choose an option (1-3): ").strip()

                # Try to parse the input
                action = self._parse_input(user_input)

                if action is not None:
                    return action
                else:
                    # Invalid input, show error and try again
                    print("Invalid choice. Please enter 1, 2, 3, or the option name (proceed/edit/cancel).")
                    print()

            except KeyboardInterrupt:
                # User pressed Ctrl+C - treat as cancel
                print("\n")
                return PromptAction.CANCEL

            except EOFError:
                # Non-interactive environment - raise the error
                raise

    def _parse_input(self, user_input: str) -> Optional[PromptAction]:
        """Parse user input into a PromptAction.

        Args:
            user_input: Raw user input string

        Returns:
            PromptAction if input is valid, None otherwise
        """
        # Normalize input (lowercase, strip whitespace)
        normalized = user_input.lower().strip()

        # Check numeric input
        if normalized == "1":
            return PromptAction.PROCEED
        elif normalized == "2":
            return PromptAction.EDIT
        elif normalized == "3":
            return PromptAction.CANCEL

        # Check text input
        if normalized in ["proceed", "continue", "go"]:
            return PromptAction.PROCEED
        elif normalized in ["edit", "open", "modify"]:
            return PromptAction.EDIT
        elif normalized in ["cancel", "abort", "quit", "exit"]:
            return PromptAction.CANCEL

        # Invalid input
        return None
