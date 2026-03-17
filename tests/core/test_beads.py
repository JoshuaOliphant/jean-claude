# ABOUTME: Tests for Beads integration module focusing on input validation and security
# ABOUTME: Ensures command injection vulnerabilities are prevented in beads ID handling

"""Tests for beads.py module focusing on security and input validation."""

import json
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
            "beads-123", "gt-abc", "hq-x1y2", "BD-456", "test-a",
            "proj-123abc", "ab-1", "abcd-xyz", "foo-bar123",
        ]
        for task_id in valid_ids:
            validate_beads_id(task_id)

    def test_invalid_and_empty_ids_rejected(self):
        """Empty, None, and malformed IDs should raise ValueError."""
        # Empty / None
        for invalid in ["", "   ", None]:
            with pytest.raises(ValueError, match="task_id cannot be empty"):
                validate_beads_id(invalid)

        # Invalid format
        invalid_ids = [
            "beads_123", "beads.123", "beads 123", "beads", "-123",
            "b-123", "abcdef-123", "abc-", "123-abc", "abc--123",
            "abc-def-123", "beads-!@#",
        ]
        for invalid_id in invalid_ids:
            with pytest.raises(ValueError, match="Invalid beads task ID format"):
                validate_beads_id(invalid_id)

    def test_command_injection_attempts_blocked(self):
        """Command injection attempts should be blocked."""
        malicious_ids = [
            "../etc/passwd", "beads-123; rm -rf /", "beads-123 && echo pwned",
            "beads-123|cat /etc/shadow", "beads-123`whoami`", "beads-123$(whoami)",
            "'; DROP TABLE users--", "../../secrets", "beads-123\nrm -rf",
        ]
        for malicious_id in malicious_ids:
            with pytest.raises(ValueError, match="Invalid beads task ID format"):
                validate_beads_id(malicious_id)

    def test_error_message_is_helpful(self):
        """Error messages should be clear and helpful."""
        with pytest.raises(ValueError) as exc_info:
            validate_beads_id("invalid_format")
        error_message = str(exc_info.value)
        assert "Invalid beads task ID format" in error_message
        assert "invalid_format" in error_message
        assert "<prefix>-<id>" in error_message
        assert "beads-123" in error_message

    def test_case_insensitive_and_boundary_lengths(self):
        """Validation should be case-insensitive and accept boundary lengths."""
        for case_id in ["GT-123", "gt-123", "Gt-123", "gT-123"]:
            validate_beads_id(case_id)

        # Boundary lengths
        validate_beads_id("ab-1")           # min prefix
        validate_beads_id("ab-a")           # min suffix
        validate_beads_id("abcde-123")      # max prefix
        validate_beads_id("ab-123456789abcdefg")  # long suffix

        # Suffix types
        validate_beads_id("gt-123456")      # numeric
        validate_beads_id("gt-abcdef")      # alpha
        validate_beads_id("gt-a1b2c3")      # mixed


class TestBeadsOperationsValidation:
    """Test that all beads operations validate input before subprocess calls."""

    def _mock_fetch_result(self):
        mock_result = Mock()
        mock_result.stdout = json.dumps([{
            "id": "gt-123", "title": "Test task", "description": "Test",
            "status": "open", "acceptance_criteria": []
        }])
        return mock_result

    @patch('jean_claude.core.beads.subprocess.run')
    def test_valid_id_proceeds_to_subprocess_for_all_operations(self, mock_run):
        """Valid IDs should pass validation and call subprocess for fetch/update/close."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = self._mock_fetch_result().stdout
        mock_run.return_value = mock_result

        task = fetch_beads_task("gt-123")
        assert task.id == "gt-123"

        update_beads_status("gt-123", "in_progress")
        close_beads_task("gt-123")
        assert mock_run.call_count == 3

    def test_all_operations_reject_malicious_input(self):
        """All beads functions should reject the same malicious inputs."""
        malicious_id = "beads-123; rm -rf /"
        for fn in [fetch_beads_task, lambda x: update_beads_status(x, "in_progress"), close_beads_task]:
            with pytest.raises(ValueError, match="Invalid beads task ID format"):
                fn(malicious_id)

    def test_invalid_id_blocked_before_subprocess(self):
        """Invalid ID should be blocked before any subprocess call."""
        with patch('jean_claude.core.beads.subprocess.run') as mock_run:
            for fn in [fetch_beads_task, lambda x: update_beads_status(x, "in_progress"), close_beads_task]:
                with pytest.raises(ValueError, match="Invalid beads task ID format"):
                    fn("../../etc/passwd")
            mock_run.assert_not_called()


class TestBeadsTaskModel:
    """Ensure BeadsTask model functionality works."""

    def test_beads_task_creation_and_json_parsing(self):
        """BeadsTask model should work with dict construction and from_json."""
        task = BeadsTask(
            id="gt-123", title="Test task", description="Test description",
            status="open", acceptance_criteria=["Criterion 1", "Criterion 2"]
        )
        assert task.id == "gt-123"
        assert task.status == BeadsTaskStatus.OPEN

        json_str = json.dumps({
            "id": "gt-456", "title": "JSON task", "description": "Desc",
            "status": "open", "acceptance_criteria": []
        })
        task2 = BeadsTask.from_json(json_str)
        assert task2.id == "gt-456"


class TestRunBdCommandHelper:
    """Test the _run_bd_command helper function."""

    @patch('jean_claude.core.beads.subprocess.run')
    def test_prepends_no_daemon_flag_and_passes_kwargs(self, mock_run):
        """Helper should prepend 'bd --no-daemon' and pass through kwargs."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_run.return_value = mock_result

        result = _run_bd_command(
            ['update', '--status', 'done', 'gt-123'],
            capture_output=True, text=True, check=True, timeout=30
        )

        mock_run.assert_called_once_with(
            ['bd', '--no-daemon', 'update', '--status', 'done', 'gt-123'],
            capture_output=True, text=True, check=True, timeout=30
        )
        assert result is mock_result


class TestNoDaemonFlagInOperations:
    """Test that all beads operations use --no-daemon flag."""

    @patch('jean_claude.core.beads.subprocess.run')
    def test_all_operations_use_no_daemon_flag(self, mock_run):
        """All operations should place --no-daemon as first argument after 'bd'."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([{
            "id": "gt-123", "title": "Test", "description": "Desc",
            "status": "open", "acceptance_criteria": []
        }])
        mock_run.return_value = mock_result

        fetch_beads_task("gt-123")
        assert mock_run.call_args[0][0][0:2] == ['bd', '--no-daemon']

        update_beads_status("gt-123", "in_progress")
        assert mock_run.call_args[0][0][0:2] == ['bd', '--no-daemon']

        close_beads_task("gt-123")
        assert mock_run.call_args[0][0][0:2] == ['bd', '--no-daemon']
