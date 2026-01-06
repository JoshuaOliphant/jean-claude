# ABOUTME: Security tests for notes tools error sanitization
# ABOUTME: Validates that error messages don't leak sensitive information

"""Security tests for notes tools.

This module tests the security-focused aspects of notes tools, particularly
error message sanitization to prevent information leakage.
"""

import pytest

from jean_claude.tools.notes_tools import _sanitize_error


class TestErrorSanitization:
    """Test error message sanitization."""

    def test_sanitize_value_error(self):
        """ValueError should be sanitized to generic message."""
        error = ValueError("Invalid workflow_id: /etc/passwd")
        sanitized = _sanitize_error(error)

        assert sanitized == "ValueError: Invalid input"
        assert "/etc/passwd" not in sanitized

    def test_sanitize_type_error(self):
        """TypeError should be sanitized to generic message."""
        error = TypeError("workflow_id cannot be None at /path/to/file.py:123")
        sanitized = _sanitize_error(error)

        assert sanitized == "TypeError: Invalid input"
        assert "/path/to/file.py" not in sanitized

    def test_sanitize_permission_error(self):
        """PermissionError should be sanitized to generic message."""
        error = PermissionError(
            "Permission denied: '/Users/user/.jc/events.db'"
        )
        sanitized = _sanitize_error(error)

        assert sanitized == "PermissionError: Unable to access notes storage"
        assert "/Users/user" not in sanitized
        assert "events.db" not in sanitized

    def test_sanitize_os_error(self):
        """OSError should be sanitized to generic message."""
        error = OSError("No such file or directory: '/tmp/secret/path'")
        sanitized = _sanitize_error(error)

        assert sanitized == "OSError: Unable to access notes storage"
        assert "/tmp/secret" not in sanitized

    def test_sanitize_generic_exception(self):
        """Generic exceptions should show type only."""
        error = RuntimeError("Internal error at module.function:456")
        sanitized = _sanitize_error(error)

        assert sanitized == "RuntimeError: Operation failed"
        assert "module.function" not in sanitized
        assert "456" not in sanitized

    def test_sanitize_does_not_leak_stack_traces(self):
        """Sanitized errors should not contain stack trace info."""
        error = Exception("Error\nTraceback (most recent call last):\n  File...")
        sanitized = _sanitize_error(error)

        assert "Traceback" not in sanitized
        assert "File" not in sanitized
        assert sanitized == "Exception: Operation failed"
