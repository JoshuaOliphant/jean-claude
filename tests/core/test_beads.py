# ABOUTME: Tests for Beads integration module focusing on input validation and security
# ABOUTME: Ensures command injection vulnerabilities are prevented in beads ID handling

"""Tests for beads.py module focusing on security and input validation."""

import json
import subprocess
from unittest.mock import Mock, patch

import pytest

from jean_claude.core.beads import (
    BeadsTask,
    BeadsTaskPriority,
    BeadsTaskStatus,
    BeadsTaskType,
    _run_bd_command,
    close_beads_task,
    fetch_beads_task,
    update_beads_status,
    validate_beads_id,
)


class TestValidateBeadsId:
    """Test suite for validate_beads_id function - command injection prevention."""

    def test_valid_ids_pass_validation(self):
        """Valid beads IDs should pass validation without raising errors."""
        valid_ids = [
            "beads-123",      # Standard format
            "gt-abc",         # Short prefix
            "hq-x1y2",        # Mixed alphanumeric
            "BD-456",         # Case insensitive
            "test-a",         # Single character suffix
            "proj-123abc",    # Long suffix
            "ab-1",           # Minimum 2-char prefix
            "abcd-xyz",       # Maximum 4-char prefix
            "foo-bar123",     # Mixed letters and numbers
        ]

        for task_id in valid_ids:
            # Should not raise any exception
            validate_beads_id(task_id)

    def test_empty_id_raises_error(self):
        """Empty or whitespace-only IDs should raise ValueError."""
        with pytest.raises(ValueError, match="task_id cannot be empty"):
            validate_beads_id("")

        with pytest.raises(ValueError, match="task_id cannot be empty"):
            validate_beads_id("   ")

    def test_none_id_raises_error(self):
        """None task_id should raise ValueError."""
        with pytest.raises(ValueError, match="task_id cannot be empty"):
            validate_beads_id(None)

    def test_command_injection_attempts_blocked(self):
        """Command injection attempts should be blocked."""
        malicious_ids = [
            "../etc/passwd",           # Path traversal
            "beads-123; rm -rf /",     # Command chaining
            "beads-123 && echo pwned", # Command chaining
            "beads-123|cat /etc/shadow", # Pipe operator
            "beads-123`whoami`",       # Command substitution
            "beads-123$(whoami)",      # Command substitution
            "'; DROP TABLE users--",   # SQL injection attempt
            "../../secrets",           # Path traversal
            "beads-123\nrm -rf",       # Newline injection
        ]

        for malicious_id in malicious_ids:
            with pytest.raises(ValueError, match="Invalid beads task ID format"):
                validate_beads_id(malicious_id)

    def test_invalid_format_blocked(self):
        """IDs not matching the expected pattern should be blocked."""
        invalid_ids = [
            "beads_123",        # Underscore instead of hyphen
            "beads.123",        # Dot instead of hyphen
            "beads 123",        # Space instead of hyphen
            "beads",            # Missing suffix
            "-123",             # Missing prefix
            "b-123",            # Prefix too short (1 char)
            "abcdef-123",       # Prefix too long (6 chars)
            "abc-",             # Missing suffix after hyphen
            "123-abc",          # Numeric prefix
            "abc--123",         # Double hyphen
            "abc-def-123",      # Multiple hyphens
            "beads-!@#",        # Special characters in suffix
        ]

        for invalid_id in invalid_ids:
            with pytest.raises(ValueError, match="Invalid beads task ID format"):
                validate_beads_id(invalid_id)

    def test_error_message_is_helpful(self):
        """Error messages should be clear and helpful."""
        with pytest.raises(ValueError) as exc_info:
            validate_beads_id("invalid_format")

        error_message = str(exc_info.value)
        assert "Invalid beads task ID format" in error_message
        assert "invalid_format" in error_message
        assert "<prefix>-<id>" in error_message
        assert "beads-123" in error_message  # Example


class TestFetchBeadsTaskValidation:
    """Test that fetch_beads_task validates input before subprocess call."""

    @patch('jean_claude.core.beads.subprocess.run')
    def test_valid_id_proceeds_to_subprocess(self, mock_run):
        """Valid ID should pass validation and proceed to subprocess call."""
        # Setup mock
        mock_result = Mock()
        mock_result.stdout = json.dumps([{
            "id": "gt-123",
            "title": "Test task",
            "description": "Test description",
            "status": "open",
            "acceptance_criteria": []
        }])
        mock_run.return_value = mock_result

        # Should not raise
        task = fetch_beads_task("gt-123")

        # Verify subprocess was called
        mock_run.assert_called_once()
        assert task.id == "gt-123"

    def test_invalid_id_blocked_before_subprocess(self):
        """Invalid ID should be blocked before any subprocess call."""
        with patch('jean_claude.core.beads.subprocess.run') as mock_run:
            with pytest.raises(ValueError, match="Invalid beads task ID format"):
                fetch_beads_task("../../etc/passwd")

            # Subprocess should never be called
            mock_run.assert_not_called()

    def test_command_injection_blocked_before_subprocess(self):
        """Command injection attempts should be blocked before subprocess."""
        with patch('jean_claude.core.beads.subprocess.run') as mock_run:
            with pytest.raises(ValueError, match="Invalid beads task ID format"):
                fetch_beads_task("beads-123; rm -rf /")

            # Subprocess should never be called
            mock_run.assert_not_called()


class TestUpdateBeadsStatusValidation:
    """Test that update_beads_status validates input before subprocess call."""

    @patch('jean_claude.core.beads.subprocess.run')
    def test_valid_id_proceeds_to_subprocess(self, mock_run):
        """Valid ID should pass validation and proceed to subprocess call."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Should not raise
        update_beads_status("gt-123", "in_progress")

        # Verify subprocess was called
        mock_run.assert_called_once()

    def test_invalid_id_blocked_before_subprocess(self):
        """Invalid ID should be blocked before any subprocess call."""
        with patch('jean_claude.core.beads.subprocess.run') as mock_run:
            with pytest.raises(ValueError, match="Invalid beads task ID format"):
                update_beads_status("beads-123|whoami", "in_progress")

            # Subprocess should never be called
            mock_run.assert_not_called()

    def test_command_injection_blocked_before_subprocess(self):
        """Command injection attempts should be blocked before subprocess."""
        with patch('jean_claude.core.beads.subprocess.run') as mock_run:
            with pytest.raises(ValueError, match="Invalid beads task ID format"):
                update_beads_status("beads-123 && echo pwned", "done")

            # Subprocess should never be called
            mock_run.assert_not_called()


class TestCloseBeadsTaskValidation:
    """Test that close_beads_task validates input before subprocess call."""

    @patch('jean_claude.core.beads.subprocess.run')
    def test_valid_id_proceeds_to_subprocess(self, mock_run):
        """Valid ID should pass validation and proceed to subprocess call."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Should not raise
        close_beads_task("gt-123")

        # Verify subprocess was called
        mock_run.assert_called_once()

    def test_invalid_id_blocked_before_subprocess(self):
        """Invalid ID should be blocked before any subprocess call."""
        with patch('jean_claude.core.beads.subprocess.run') as mock_run:
            with pytest.raises(ValueError, match="Invalid beads task ID format"):
                close_beads_task("beads-123`cat /etc/passwd`")

            # Subprocess should never be called
            mock_run.assert_not_called()

    def test_command_injection_blocked_before_subprocess(self):
        """Command injection attempts should be blocked before subprocess."""
        with patch('jean_claude.core.beads.subprocess.run') as mock_run:
            with pytest.raises(ValueError, match="Invalid beads task ID format"):
                close_beads_task("beads-123$(rm -rf /)")

            # Subprocess should never be called
            mock_run.assert_not_called()


class TestBeadsIntegrationScenarios:
    """Integration-style tests for complete workflows."""

    @patch('jean_claude.core.beads.subprocess.run')
    def test_workflow_with_all_operations(self, mock_run):
        """Test complete workflow: fetch → update → close."""
        # Setup mocks
        fetch_result = Mock()
        fetch_result.stdout = json.dumps([{
            "id": "gt-123",
            "title": "Test task",
            "description": "Test description",
            "status": "open",
            "acceptance_criteria": []
        }])

        update_result = Mock()
        update_result.returncode = 0

        close_result = Mock()
        close_result.returncode = 0

        mock_run.side_effect = [fetch_result, update_result, close_result]

        # Execute workflow
        task = fetch_beads_task("gt-123")
        assert task.id == "gt-123"

        update_beads_status("gt-123", "in_progress")
        close_beads_task("gt-123")

        # Verify all calls were made
        assert mock_run.call_count == 3

    def test_all_operations_reject_same_malicious_input(self):
        """All beads functions should reject the same malicious inputs."""
        malicious_id = "beads-123; rm -rf /"

        with pytest.raises(ValueError, match="Invalid beads task ID format"):
            fetch_beads_task(malicious_id)

        with pytest.raises(ValueError, match="Invalid beads task ID format"):
            update_beads_status(malicious_id, "in_progress")

        with pytest.raises(ValueError, match="Invalid beads task ID format"):
            close_beads_task(malicious_id)


class TestExistingBeadsTaskModel:
    """Ensure existing BeadsTask model functionality still works."""

    def test_beads_task_creation_from_dict(self):
        """BeadsTask model should still work with valid data."""
        task_data = {
            "id": "gt-123",
            "title": "Test task",
            "description": "Test description",
            "status": "open",
            "acceptance_criteria": ["Criterion 1", "Criterion 2"]
        }

        task = BeadsTask(**task_data)
        assert task.id == "gt-123"
        assert task.status == BeadsTaskStatus.OPEN

    def test_beads_task_from_json(self):
        """BeadsTask.from_json should still work correctly."""
        json_str = json.dumps({
            "id": "gt-123",
            "title": "Test task",
            "description": "Test description",
            "status": "open",
            "acceptance_criteria": []
        })

        task = BeadsTask.from_json(json_str)
        assert task.id == "gt-123"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_case_insensitive_validation(self):
        """Validation should be case-insensitive."""
        # These should all pass
        validate_beads_id("GT-123")
        validate_beads_id("gt-123")
        validate_beads_id("Gt-123")
        validate_beads_id("gT-123")

    def test_minimum_valid_lengths(self):
        """Test minimum valid lengths for prefix and suffix."""
        validate_beads_id("ab-1")    # Minimum prefix (2 chars)
        validate_beads_id("ab-a")    # Minimum suffix (1 char)

    def test_maximum_valid_lengths(self):
        """Test maximum valid lengths for prefix."""
        validate_beads_id("abcde-123")  # Maximum prefix (5 chars)
        # No maximum for suffix, these should pass
        validate_beads_id("ab-123456789abcdefg")

    def test_numeric_suffix_only(self):
        """Suffix can be purely numeric."""
        validate_beads_id("gt-123456")

    def test_alpha_suffix_only(self):
        """Suffix can be purely alphabetic."""
        validate_beads_id("gt-abcdef")

    def test_mixed_suffix(self):
        """Suffix can be mixed alphanumeric."""
        validate_beads_id("gt-a1b2c3")
        validate_beads_id("gt-123abc456def")


class TestRunBdCommandHelper:
    """Test the _run_bd_command helper function for --no-daemon flag usage."""

    @patch('jean_claude.core.beads.subprocess.run')
    def test_prepends_no_daemon_flag(self, mock_run):
        """Helper should prepend 'bd --no-daemon' to all commands."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        _run_bd_command(['show', '--json', 'gt-123'], capture_output=True)

        # Verify subprocess.run was called with bd --no-daemon prepended
        mock_run.assert_called_once_with(
            ['bd', '--no-daemon', 'show', '--json', 'gt-123'],
            capture_output=True
        )

    @patch('jean_claude.core.beads.subprocess.run')
    def test_passes_through_kwargs(self, mock_run):
        """Helper should pass through all subprocess kwargs."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        _run_bd_command(
            ['update', '--status', 'done', 'gt-123'],
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )

        # Verify all kwargs were passed through
        mock_run.assert_called_once_with(
            ['bd', '--no-daemon', 'update', '--status', 'done', 'gt-123'],
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )

    @patch('jean_claude.core.beads.subprocess.run')
    def test_returns_completed_process(self, mock_run):
        """Helper should return the CompletedProcess from subprocess.run."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_run.return_value = mock_result

        result = _run_bd_command(['show', 'gt-123'])

        assert result is mock_result
        assert result.returncode == 0
        assert result.stdout == "test output"


class TestNoDaemonFlagInOperations:
    """Test that all beads operations use --no-daemon flag."""

    @patch('jean_claude.core.beads.subprocess.run')
    def test_fetch_beads_task_uses_no_daemon(self, mock_run):
        """fetch_beads_task should use --no-daemon flag."""
        mock_result = Mock()
        mock_result.stdout = json.dumps([{
            "id": "gt-123",
            "title": "Test",
            "description": "Desc",
            "status": "open",
            "acceptance_criteria": []
        }])
        mock_run.return_value = mock_result

        fetch_beads_task("gt-123")

        # Verify --no-daemon is in the command
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'bd'
        assert call_args[1] == '--no-daemon'
        assert 'show' in call_args
        assert '--json' in call_args
        assert 'gt-123' in call_args

    @patch('jean_claude.core.beads.subprocess.run')
    def test_update_beads_status_uses_no_daemon(self, mock_run):
        """update_beads_status should use --no-daemon flag."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        update_beads_status("gt-123", "in_progress")

        # Verify --no-daemon is in the command
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'bd'
        assert call_args[1] == '--no-daemon'
        assert 'update' in call_args
        assert '--status' in call_args
        assert 'in_progress' in call_args
        assert 'gt-123' in call_args

    @patch('jean_claude.core.beads.subprocess.run')
    def test_close_beads_task_uses_no_daemon(self, mock_run):
        """close_beads_task should use --no-daemon flag."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        close_beads_task("gt-123")

        # Verify --no-daemon is in the command
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'bd'
        assert call_args[1] == '--no-daemon'
        assert 'close' in call_args
        assert 'gt-123' in call_args

    @patch('jean_claude.core.beads.subprocess.run')
    def test_all_operations_use_consistent_flag_position(self, mock_run):
        """All operations should place --no-daemon as first argument after 'bd'."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([{
            "id": "gt-123",
            "title": "Test",
            "description": "Desc",
            "status": "open",
            "acceptance_criteria": []
        }])
        mock_run.return_value = mock_result

        # Test fetch
        fetch_beads_task("gt-123")
        assert mock_run.call_args[0][0][0:2] == ['bd', '--no-daemon']

        # Test update
        update_beads_status("gt-123", "in_progress")
        assert mock_run.call_args[0][0][0:2] == ['bd', '--no-daemon']

        # Test close
        close_beads_task("gt-123")
        assert mock_run.call_args[0][0][0:2] == ['bd', '--no-daemon']
