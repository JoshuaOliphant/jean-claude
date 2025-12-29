# ABOUTME: Test suite for error handling in work CLI command
# ABOUTME: Tests PermissionError and OSError handling during file write operations

"""Tests for error handling in work CLI command.

This test file focuses on verifying that the work command properly handles
file write errors (PermissionError and OSError) when writing the spec file.
"""

from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest
from click.testing import CliRunner

from jean_claude.cli.commands.work import work
from jean_claude.core.beads import BeadsTask, BeadsTaskStatus


class TestWorkCommandFileWriteErrorHandling:
    """Tests for file write error handling in work command."""

    def test_work_handles_permission_error_on_spec_write(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that work command handles PermissionError when writing spec file."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test Spec"):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    with patch('pathlib.Path.write_text', side_effect=PermissionError("Permission denied")):
                        result = isolated_cli_runner.invoke(work, ["test-task.1"])

                        # Should abort with non-zero exit code
                        assert result.exit_code != 0

                        # Should display user-friendly error message
                        output_lower = result.output.lower()
                        assert "permission" in output_lower or "denied" in output_lower
                        assert "spec" in output_lower or "file" in output_lower

    def test_work_handles_os_error_on_spec_write(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that work command handles OSError when writing spec file."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test Spec"):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    with patch('pathlib.Path.write_text', side_effect=OSError("Disk full")):
                        result = isolated_cli_runner.invoke(work, ["test-task.1"])

                        # Should abort with non-zero exit code
                        assert result.exit_code != 0

                        # Should display user-friendly error message
                        output_lower = result.output.lower()
                        assert "error" in output_lower or "failed" in output_lower
                        assert "spec" in output_lower or "file" in output_lower

    def test_work_displays_rich_formatted_error_on_permission_error(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that permission errors are displayed with Rich console formatting."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test Spec"):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    with patch('pathlib.Path.write_text', side_effect=PermissionError("Access denied")):
                        result = isolated_cli_runner.invoke(work, ["test-task.1"])

                        # Check that error message is present and informative
                        assert result.exit_code != 0
                        output = result.output
                        # Should mention the specific error
                        assert "Access denied" in output or "permission" in output.lower()

    def test_work_displays_rich_formatted_error_on_os_error(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that OS errors are displayed with Rich console formatting."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test Spec"):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    with patch('pathlib.Path.write_text', side_effect=OSError("No space left on device")):
                        result = isolated_cli_runner.invoke(work, ["test-task.1"])

                        # Check that error message is present and informative
                        assert result.exit_code != 0
                        output = result.output
                        # Should mention the specific error
                        assert "No space left on device" in output or "error" in output.lower()

    def test_work_aborts_on_permission_error(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that work command raises click.Abort on PermissionError."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test Spec"):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    with patch('pathlib.Path.write_text', side_effect=PermissionError("Cannot write")):
                        result = isolated_cli_runner.invoke(work, ["test-task.1"])

                        # click.Abort should result in non-zero exit code
                        assert result.exit_code != 0

    def test_work_aborts_on_os_error(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that work command raises click.Abort on OSError."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test Spec"):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    with patch('pathlib.Path.write_text', side_effect=OSError("IO error")):
                        result = isolated_cli_runner.invoke(work, ["test-task.1"])

                        # click.Abort should result in non-zero exit code
                        assert result.exit_code != 0

    def test_work_succeeds_when_no_write_error(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that work command succeeds when file write is successful."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test Spec"):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    # Default behavior: file write succeeds (dry-run mode to avoid workflow execution)
                    result = isolated_cli_runner.invoke(work, ["test-task.1", "--dry-run"])

                    # Should succeed with exit code 0
                    assert result.exit_code == 0
                    # Should create the spec file
                    spec_path = Path("specs/beads-test-task.1.md")
                    assert spec_path.exists()

    def test_work_error_message_includes_file_path(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that error messages include the file path being written."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test Spec"):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    with patch('pathlib.Path.write_text', side_effect=PermissionError("Access denied")):
                        result = isolated_cli_runner.invoke(work, ["test-task.1"])

                        # Error message should help user identify which file had the issue
                        output = result.output
                        assert "specs" in output.lower() or "beads-test-task.1.md" in output

    def test_work_does_not_continue_after_write_error(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that workflow does not continue after file write error."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test Spec"):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    with patch('pathlib.Path.write_text', side_effect=PermissionError("Access denied")):
                        with patch('jean_claude.cli.commands.work.anyio.run') as mock_anyio:
                            result = isolated_cli_runner.invoke(work, ["test-task.1"])

                            # Should not call workflow execution after error
                            mock_anyio.assert_not_called()
                            assert result.exit_code != 0
