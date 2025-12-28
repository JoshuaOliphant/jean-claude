# ABOUTME: EditTaskHandler for invoking bd edit command
# ABOUTME: Opens Beads tasks in editor for modification

"""Edit task handler for Beads integration.

This module provides functionality to invoke the 'bd edit' command to open
Beads tasks in an editor for modification.
"""

import subprocess
from typing import Optional


class EditTaskHandler:
    """Handles editing of Beads tasks via bd CLI.

    Features:
    - Invokes 'bd edit <task_id>' to open task in editor
    - Waits for editor to close before returning
    - Handles errors gracefully
    """

    def __init__(self, bd_path: str = "bd"):
        """Initialize the edit task handler.

        Args:
            bd_path: Path to the bd CLI executable (defaults to "bd")
        """
        self.bd_path = bd_path

    def edit_task(self, task_id: str) -> None:
        """Open a Beads task in editor for modification.

        Runs 'bd edit <task_id>' subprocess to open the task in the user's
        default editor. This is a blocking call that waits for the editor
        to close before returning.

        Args:
            task_id: The ID of the task to edit

        Raises:
            ValueError: If task_id is empty or None
            RuntimeError: If the subprocess fails with non-zero exit code
        """
        # Validate task_id
        if task_id is None:
            raise ValueError("task_id cannot be empty")

        if not isinstance(task_id, str):
            raise TypeError("task_id must be a string")

        if not task_id.strip():
            raise ValueError("task_id cannot be empty")

        try:
            # Run the bd edit command
            # This will open the task in the user's editor and wait for it to close
            subprocess.run(
                [self.bd_path, 'edit', task_id],
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            # Handle subprocess errors
            error_msg = f"Failed to edit task {task_id}: {e.stderr if e.stderr else str(e)}"
            raise RuntimeError(error_msg) from e
