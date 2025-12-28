"""Tests for edit task integration.

This module tests the integration of 'bd edit' command invocation from the
validation prompt. When a user selects option [2], the task should be opened
in an editor and then re-validated after editing.
"""

import pytest
from unittest.mock import Mock, patch, call
from io import StringIO

from jean_claude.core.task_validator import ValidationResult, TaskValidator
from jean_claude.core.interactive_prompt_handler import InteractivePromptHandler, PromptAction
from jean_claude.core.beads import BeadsTask, BeadsTaskStatus, BeadsTaskPriority, BeadsTaskType
from jean_claude.core.edit_task_handler import EditTaskHandler


class TestEditTaskHandler:
    """Test EditTaskHandler for invoking bd edit command."""

    def test_init_creates_handler(self):
        """Test that handler can be initialized."""
        handler = EditTaskHandler()
        assert handler is not None

    @patch('subprocess.run')
    def test_edit_task_calls_bd_edit(self, mock_run):
        """Test that edit_task invokes 'bd edit <task_id>'."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        handler = EditTaskHandler()
        handler.edit_task("test-task-1")

        # Verify subprocess.run was called with correct arguments
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == ['bd', 'edit', 'test-task-1']

    @patch('subprocess.run')
    def test_edit_task_with_empty_task_id_raises_error(self, mock_run):
        """Test that edit_task raises ValueError for empty task_id."""
        handler = EditTaskHandler()

        with pytest.raises(ValueError, match="task_id cannot be empty"):
            handler.edit_task("")

    @patch('subprocess.run')
    def test_edit_task_with_whitespace_task_id_raises_error(self, mock_run):
        """Test that edit_task raises ValueError for whitespace-only task_id."""
        handler = EditTaskHandler()

        with pytest.raises(ValueError, match="task_id cannot be empty"):
            handler.edit_task("   ")

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

    @patch('subprocess.run')
    def test_edit_task_returns_successfully(self, mock_run):
        """Test that edit_task returns without error on success."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        handler = EditTaskHandler()
        # Should not raise any exception
        handler.edit_task("test-task-1")

    @patch('subprocess.run')
    def test_edit_task_waits_for_editor_to_close(self, mock_run):
        """Test that edit_task waits for editor to close (check=True)."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        handler = EditTaskHandler()
        handler.edit_task("test-task-1")

        # Verify that check=True was passed (so it waits for completion)
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get('check') == True


class TestEditAndRevalidateFlow:
    """Test the complete edit and re-validate flow."""

    @patch('jean_claude.core.edit_task_handler.EditTaskHandler.edit_task')
    @patch('jean_claude.core.edit_and_revalidate.fetch_beads_task')  # Patch where it's USED
    def test_edit_and_revalidate_flow(self, mock_fetch, mock_edit, mock_beads_task_factory):
        """Test complete flow of editing task and re-validating."""
        from jean_claude.core.edit_and_revalidate import edit_and_revalidate

        # Create mock task after editing (uses factory with priority/task_type)
        task_after = mock_beads_task_factory(
            id="test-1",
            title="Test",
            description="Much longer description with lots of detail about what needs to be done",
            priority=BeadsTaskPriority.MEDIUM,
            task_type=BeadsTaskType.FEATURE
        )

        # Mock edit_task to do nothing (user edited the task)
        mock_edit.return_value = None

        # Mock fetch to return updated task after edit
        mock_fetch.return_value = task_after

        # Run the edit and revalidate flow
        result = edit_and_revalidate("test-1")

        # Verify edit_task was called
        mock_edit.assert_called_once_with("test-1")

        # Verify task was fetched after edit
        mock_fetch.assert_called_once_with("test-1")

        # Verify result is a ValidationResult
        assert isinstance(result, ValidationResult)

    @patch('jean_claude.core.edit_task_handler.EditTaskHandler.edit_task')
    @patch('jean_claude.core.edit_and_revalidate.fetch_beads_task')  # Patch where it's USED
    def test_edit_and_revalidate_with_validator(self, mock_fetch, mock_edit, mock_beads_task_factory):
        """Test edit and revalidate using TaskValidator."""
        from jean_claude.core.edit_and_revalidate import edit_and_revalidate

        # Create improved task (uses factory with priority/task_type)
        task_after = mock_beads_task_factory(
            id="test-1",
            title="Test Task",
            description="A detailed description with more than fifty characters to pass validation checks",
            priority=BeadsTaskPriority.HIGH,
            task_type=BeadsTaskType.FEATURE
        )

        mock_edit.return_value = None
        mock_fetch.return_value = task_after

        # Run edit and revalidate
        result = edit_and_revalidate("test-1")

        # Result should have fewer warnings (or none)
        assert isinstance(result, ValidationResult)
        # The improved task should pass validation better
        assert result.is_valid or len(result.warnings) < 3


class TestInteractivePromptWithEdit:
    """Test interactive prompt integration with edit functionality."""

    @patch('builtins.input', side_effect=['2', '1'])  # Choose edit, then proceed
    @patch('sys.stdout', new_callable=StringIO)
    @patch('jean_claude.core.edit_and_revalidate.edit_and_revalidate')
    def test_prompt_edit_action_triggers_edit(self, mock_edit_revalidate, mock_stdout, mock_input):
        """Test that selecting edit option triggers edit and revalidate."""
        # Create a handler and result
        handler = InteractivePromptHandler()
        result = ValidationResult(warnings=["Test warning"])

        # Mock edit_and_revalidate to return improved result
        mock_edit_revalidate.return_value = ValidationResult()  # No warnings

        # Prompt should return EDIT on first call
        action = handler.prompt(result)
        assert action == PromptAction.EDIT

    @patch('jean_claude.core.edit_task_handler.EditTaskHandler.edit_task')
    @patch('jean_claude.core.edit_and_revalidate.fetch_beads_task')  # Patch where it's USED
    def test_edit_and_revalidate_handles_no_improvement(self, mock_fetch, mock_edit, mock_beads_task_factory):
        """Test that edit_and_revalidate handles case where task is not improved."""
        from jean_claude.core.edit_and_revalidate import edit_and_revalidate

        # Task remains short even after editing
        task = mock_beads_task_factory(
            title="Test",
            description="Still short"
        )

        mock_edit.return_value = None
        mock_fetch.return_value = task

        # Should still return a result with warnings
        result = edit_and_revalidate("test-1")

        assert isinstance(result, ValidationResult)
        assert len(result.warnings) > 0


class TestEditTaskValidation:
    """Test validation of edit_task parameters."""

    @patch('subprocess.run')
    def test_edit_task_validates_task_id_type(self, mock_run):
        """Test that edit_task validates task_id is a string."""
        handler = EditTaskHandler()

        # Should handle None
        with pytest.raises((ValueError, TypeError)):
            handler.edit_task(None)

    @patch('subprocess.run')
    def test_edit_task_handles_special_characters(self, mock_run):
        """Test that edit_task handles task IDs with special characters."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        handler = EditTaskHandler()
        # Should work with hyphens and underscores
        handler.edit_task("task-123_abc")

        call_args = mock_run.call_args[0][0]
        assert 'task-123_abc' in call_args


class TestEditTaskSubprocessOptions:
    """Test subprocess execution options for edit_task."""

    @patch('subprocess.run')
    def test_edit_task_uses_text_mode(self, mock_run):
        """Test that edit_task uses text mode for subprocess."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        handler = EditTaskHandler()
        handler.edit_task("test-1")

        # Check that text=True was passed
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get('text') == True

    @patch('subprocess.run')
    def test_edit_task_captures_output(self, mock_run):
        """Test that edit_task captures subprocess output."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        handler = EditTaskHandler()
        handler.edit_task("test-1")

        # Check that capture_output=True was passed
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get('capture_output') == True


class TestEditAndRevalidateErrorHandling:
    """Test error handling in edit_and_revalidate flow."""

    @patch('jean_claude.core.edit_task_handler.EditTaskHandler.edit_task')
    @patch('jean_claude.core.beads.fetch_beads_task')
    def test_edit_and_revalidate_handles_edit_failure(self, mock_fetch, mock_edit):
        """Test that edit_and_revalidate handles edit failures."""
        from jean_claude.core.edit_and_revalidate import edit_and_revalidate

        # Edit fails
        mock_edit.side_effect = RuntimeError("Failed to edit task")

        # Should propagate the error
        with pytest.raises(RuntimeError, match="Failed to edit task"):
            edit_and_revalidate("test-1")

    @patch('jean_claude.core.edit_task_handler.EditTaskHandler.edit_task')
    @patch('jean_claude.core.edit_and_revalidate.fetch_beads_task')
    def test_edit_and_revalidate_handles_fetch_failure(self, mock_fetch, mock_edit):
        """Test that edit_and_revalidate handles fetch failures after edit."""
        from jean_claude.core.edit_and_revalidate import edit_and_revalidate

        mock_edit.return_value = None
        # Fetch fails after edit
        mock_fetch.side_effect = RuntimeError("Failed to fetch task")

        # Should propagate the error
        with pytest.raises(RuntimeError, match="Failed to fetch task"):
            edit_and_revalidate("test-1")


class TestEditTaskHandlerCustomBdPath:
    """Test EditTaskHandler with custom bd CLI path."""

    def test_init_with_custom_bd_path(self):
        """Test initialization with custom bd path."""
        handler = EditTaskHandler(bd_path="/custom/path/to/bd")
        assert handler.bd_path == "/custom/path/to/bd"

    def test_init_with_default_bd_path(self):
        """Test initialization uses default 'bd' path."""
        handler = EditTaskHandler()
        assert handler.bd_path == "bd"

    @patch('subprocess.run')
    def test_edit_task_uses_custom_bd_path(self, mock_run):
        """Test that edit_task uses custom bd path if provided."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        handler = EditTaskHandler(bd_path="/usr/local/bin/bd")
        handler.edit_task("test-1")

        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "/usr/local/bin/bd"
        assert call_args[1] == "edit"
        assert call_args[2] == "test-1"
