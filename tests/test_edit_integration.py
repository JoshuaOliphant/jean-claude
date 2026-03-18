"""Tests for edit task integration.

This module tests the integration of 'bd edit' command invocation from the
validation prompt. When a user selects option [2], the task should be opened
in an editor and then re-validated after editing.
"""

import pytest
from unittest.mock import Mock, patch

from jean_claude.core.edit_task_handler import EditTaskHandler


class TestEditTaskHandler:
    """Test EditTaskHandler for invoking bd edit command."""

    @patch('subprocess.run')
    def test_edit_task_handles_subprocess_error(self, mock_run):
        """Test that edit_task handles subprocess errors gracefully."""
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=['bd', 'edit', 'test-task-1'],
            stderr="Task not found"
        )

        handler = EditTaskHandler()

        with pytest.raises(RuntimeError, match="Failed to edit task"):
            handler.edit_task("test-task-1")


class TestEditTaskValidation:
    """Test validation of edit_task parameters."""

    @patch('subprocess.run')
    def test_edit_task_validates_task_id_type(self, mock_run):
        """Test that edit_task validates task_id is a string."""
        handler = EditTaskHandler()

        # Should handle None
        with pytest.raises((ValueError, TypeError)):
            handler.edit_task(None)
