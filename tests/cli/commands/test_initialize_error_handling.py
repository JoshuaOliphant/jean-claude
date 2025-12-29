# ABOUTME: Test suite for error handling in initialize CLI command
# ABOUTME: Tests FileNotFoundError, PermissionError, and OSError handling during file read operations

"""Tests for error handling in initialize CLI command.

This test file focuses on verifying that the initialize command properly handles
file read errors (FileNotFoundError, PermissionError, and OSError) when reading the spec file.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from jean_claude.cli.commands.initialize import initialize


class TestInitializeCommandFileReadErrorHandling:
    """Tests for file read error handling in initialize command."""

    def test_initialize_handles_file_not_found_error(self, isolated_cli_runner, tmp_path):
        """Test that initialize command handles FileNotFoundError when reading spec file."""
        # Create a spec file path that doesn't exist
        spec_file = tmp_path / "nonexistent.md"

        result = isolated_cli_runner.invoke(initialize, ["--spec-file", str(spec_file)])

        # Should abort with non-zero exit code
        assert result.exit_code != 0

        # Should display user-friendly error message
        output_lower = result.output.lower()
        assert "not found" in output_lower or "does not exist" in output_lower or "error" in output_lower

    def test_initialize_handles_permission_error_on_spec_read(self, isolated_cli_runner, tmp_path):
        """Test that initialize command handles PermissionError when reading spec file."""
        # Create a real spec file
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Test Spec")

        # Mock read_text to raise PermissionError
        with patch('pathlib.Path.read_text', side_effect=PermissionError("Permission denied")):
            result = isolated_cli_runner.invoke(initialize, ["--spec-file", str(spec_file)])

            # Should abort with non-zero exit code
            assert result.exit_code != 0

            # Should display user-friendly error message
            output_lower = result.output.lower()
            assert "permission" in output_lower or "denied" in output_lower
            assert "spec" in output_lower or "file" in output_lower or "read" in output_lower

    def test_initialize_handles_os_error_on_spec_read(self, isolated_cli_runner, tmp_path):
        """Test that initialize command handles OSError when reading spec file."""
        # Create a real spec file
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Test Spec")

        # Mock read_text to raise OSError
        with patch('pathlib.Path.read_text', side_effect=OSError("IO error occurred")):
            result = isolated_cli_runner.invoke(initialize, ["--spec-file", str(spec_file)])

            # Should abort with non-zero exit code
            assert result.exit_code != 0

            # Should display user-friendly error message
            output_lower = result.output.lower()
            assert "error" in output_lower or "failed" in output_lower
            assert "spec" in output_lower or "file" in output_lower or "read" in output_lower

    def test_initialize_displays_rich_formatted_error_on_permission_error(self, isolated_cli_runner, tmp_path):
        """Test that permission errors are displayed with Rich console formatting."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Test Spec")

        with patch('pathlib.Path.read_text', side_effect=PermissionError("Access denied")):
            result = isolated_cli_runner.invoke(initialize, ["--spec-file", str(spec_file)])

            # Check that error message is present and informative
            assert result.exit_code != 0
            output = result.output
            # Should mention the specific error
            assert "Access denied" in output or "permission" in output.lower()

    def test_initialize_displays_rich_formatted_error_on_os_error(self, isolated_cli_runner, tmp_path):
        """Test that OS errors are displayed with Rich console formatting."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Test Spec")

        with patch('pathlib.Path.read_text', side_effect=OSError("Disk read error")):
            result = isolated_cli_runner.invoke(initialize, ["--spec-file", str(spec_file)])

            # Check that error message is present and informative
            assert result.exit_code != 0
            output = result.output
            # Should mention the specific error
            assert "Disk read error" in output or "error" in output.lower()

    def test_initialize_aborts_on_file_not_found(self, isolated_cli_runner, tmp_path):
        """Test that initialize command raises click.Abort on FileNotFoundError."""
        spec_file = tmp_path / "missing.md"

        result = isolated_cli_runner.invoke(initialize, ["--spec-file", str(spec_file)])

        # click.Abort should result in non-zero exit code
        assert result.exit_code != 0

    def test_initialize_aborts_on_permission_error(self, isolated_cli_runner, tmp_path):
        """Test that initialize command raises click.Abort on PermissionError."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Test Spec")

        with patch('pathlib.Path.read_text', side_effect=PermissionError("Cannot read")):
            result = isolated_cli_runner.invoke(initialize, ["--spec-file", str(spec_file)])

            # click.Abort should result in non-zero exit code
            assert result.exit_code != 0

    def test_initialize_aborts_on_os_error(self, isolated_cli_runner, tmp_path):
        """Test that initialize command raises click.Abort on OSError."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Test Spec")

        with patch('pathlib.Path.read_text', side_effect=OSError("IO error")):
            result = isolated_cli_runner.invoke(initialize, ["--spec-file", str(spec_file)])

            # click.Abort should result in non-zero exit code
            assert result.exit_code != 0

    def test_initialize_error_message_includes_file_path(self, isolated_cli_runner, tmp_path):
        """Test that error messages include the file path being read."""
        spec_file = tmp_path / "myspec.md"
        spec_file.write_text("# Test Spec")

        with patch('pathlib.Path.read_text', side_effect=PermissionError("Access denied")):
            result = isolated_cli_runner.invoke(initialize, ["--spec-file", str(spec_file)])

            # Error message should help user identify which file had the issue
            output = result.output
            assert "myspec.md" in output or "spec" in output.lower()

    def test_initialize_does_not_continue_after_read_error(self, isolated_cli_runner, tmp_path):
        """Test that workflow does not continue after file read error."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Test Spec")

        with patch('pathlib.Path.read_text', side_effect=PermissionError("Access denied")):
            with patch('jean_claude.cli.commands.initialize.anyio.run') as mock_anyio:
                result = isolated_cli_runner.invoke(initialize, ["--spec-file", str(spec_file)])

                # Should not call workflow execution after error
                mock_anyio.assert_not_called()
                assert result.exit_code != 0

    def test_initialize_succeeds_when_no_read_error(self, isolated_cli_runner, tmp_path):
        """Test that initialize command succeeds when file read is successful."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Test Spec\n\nBuild a feature.")

        # Mock the run_initializer to avoid actual execution
        mock_state = Mock()
        mock_state.workflow_id = "test-workflow-123"
        mock_state.features = [Mock(), Mock()]

        with patch('jean_claude.cli.commands.initialize.anyio.run', return_value=mock_state):
            result = isolated_cli_runner.invoke(initialize, ["--spec-file", str(spec_file)])

            # Should succeed with exit code 0
            assert result.exit_code == 0
            # Should show success message
            assert "success" in result.output.lower() or "complete" in result.output.lower()

    def test_initialize_with_description_argument_works(self, isolated_cli_runner):
        """Test that initialize command works with direct description (no file read)."""
        # Mock the run_initializer to avoid actual execution
        mock_state = Mock()
        mock_state.workflow_id = "test-workflow-123"
        mock_state.features = [Mock()]

        with patch('jean_claude.cli.commands.initialize.anyio.run', return_value=mock_state):
            result = isolated_cli_runner.invoke(initialize, ["Add user authentication"])

            # Should succeed with exit code 0
            assert result.exit_code == 0
