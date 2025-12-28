# ABOUTME: Edit and revalidate flow for Beads tasks
# ABOUTME: Combines task editing with automatic re-validation

"""Edit and revalidate flow for Beads tasks.

This module provides the complete flow of editing a task and then re-validating
it to check if the edits improved the task quality.
"""

from jean_claude.core.edit_task_handler import EditTaskHandler
from jean_claude.core.beads import fetch_beads_task
from jean_claude.core.task_validator import TaskValidator, ValidationResult


def edit_and_revalidate(task_id: str, strict: bool = False) -> ValidationResult:
    """Edit a Beads task and re-validate after editing.

    This function performs the complete edit and revalidate flow:
    1. Opens the task in an editor using 'bd edit'
    2. Waits for the user to finish editing
    3. Fetches the updated task from Beads
    4. Validates the updated task
    5. Returns the validation result

    Args:
        task_id: The ID of the task to edit
        strict: Whether to use strict validation mode (converts warnings to errors)

    Returns:
        ValidationResult with the validation status of the edited task

    Raises:
        ValueError: If task_id is empty or None
        RuntimeError: If editing or fetching the task fails
    """
    # Step 1: Open task in editor
    editor = EditTaskHandler()
    editor.edit_task(task_id)

    # Step 2: Fetch the updated task
    task = fetch_beads_task(task_id)

    # Step 3: Validate the updated task
    validator = TaskValidator()
    result = validator.validate(task)

    # Step 4: Apply strict mode if requested
    if strict and result.has_warnings():
        result = result.to_strict()

    return result
