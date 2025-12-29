# ABOUTME: Test suite for PostToolUse hook logging functionality
# ABOUTME: Tests that exceptions in the hook are properly logged with stack traces

"""Tests for PostToolUse hook logging.

This module tests that the PostToolUse hook properly logs exceptions
that occur during execution, including full stack trace information.
"""

import pytest
from unittest.mock import patch, MagicMock

from jean_claude.orchestration.post_tool_use_hook import post_tool_use_hook


class TestPostToolUseHookLogging:
    """Tests for error logging in PostToolUse hook."""

    @pytest.mark.asyncio
    async def test_hook_logs_exception_with_exc_info(self, tmp_path, caplog):
        """Test that hook logs exceptions with full stack trace (exc_info=True)."""
        import logging
        caplog.set_level(logging.ERROR)

        workflow_id = "test-workflow"
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        tool_input = {"file_path": "/some/path/inbox.jsonl"}

        # Mock MailboxPaths to raise an exception
        with patch("jean_claude.orchestration.post_tool_use_hook.MailboxPaths") as mock_paths:
            mock_paths.side_effect = RuntimeError("Test error in MailboxPaths")

            # Call hook - should catch exception and log it
            result = await post_tool_use_hook(
                hook_context=context,
                tool_name="Write",
                tool_input=tool_input,
                tool_output={"success": True}
            )

            # Hook should still return None even on error
            assert result is None

            # Verify error was logged
            assert len(caplog.records) == 1
            log_record = caplog.records[0]

            # Check log level
            assert log_record.levelname == "ERROR"

            # Check that exc_info was included (stack trace)
            assert log_record.exc_info is not None

            # Check the error message contains relevant info
            assert "Test error in MailboxPaths" in log_record.message or \
                   "Error in post_tool_use_hook" in log_record.message

            # Verify the exception type in exc_info
            assert log_record.exc_info[0] == RuntimeError

    @pytest.mark.asyncio
    async def test_hook_logs_with_hook_name_in_extra(self, tmp_path, caplog):
        """Test that hook logs with 'hook' field in extra data."""
        import logging
        from jean_claude.core.mailbox_paths import MailboxPaths

        caplog.set_level(logging.ERROR)

        workflow_id = "test-workflow"
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Create actual mailbox paths to get the real inbox path
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)
        paths.ensure_mailbox_dir()

        # Use the actual inbox path so the hook will try to call read_inbox_count
        tool_input = {"file_path": str(paths.inbox_path)}

        # Mock read_inbox_count to raise an exception
        with patch("jean_claude.orchestration.post_tool_use_hook.read_inbox_count") as mock_read:
            mock_read.side_effect = ValueError("Test error in read_inbox_count")

            # Call hook
            result = await post_tool_use_hook(
                hook_context=context,
                tool_name="Write",
                tool_input=tool_input,
                tool_output={"success": True}
            )

            # Hook should still return None
            assert result is None

            # Verify error was logged with extra hook info
            assert len(caplog.records) >= 1
            log_record = caplog.records[-1]

            # Check that 'hook' field exists in extra data
            # The hook name should be the module name
            assert hasattr(log_record, 'hook')
            assert 'post_tool_use_hook' in log_record.hook

    @pytest.mark.asyncio
    async def test_hook_logs_path_resolution_errors(self, tmp_path, caplog):
        """Test that hook logs errors during path resolution."""
        import logging
        caplog.set_level(logging.ERROR)

        workflow_id = "test-workflow"
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        # Invalid path with null bytes that will cause path resolution to fail
        tool_input = {"file_path": "/path/with/\x00null/bytes"}

        # Call hook - should catch exception and log it
        result = await post_tool_use_hook(
            hook_context=context,
            tool_name="Write",
            tool_input=tool_input,
            tool_output={"success": True}
        )

        # Hook should return None
        assert result is None

        # Verify error was logged with stack trace
        assert len(caplog.records) >= 1
        log_record = caplog.records[-1]
        assert log_record.levelname == "ERROR"
        assert log_record.exc_info is not None

    @pytest.mark.asyncio
    async def test_hook_does_not_log_when_no_error(self, tmp_path, caplog):
        """Test that hook does not log when operating normally (no errors)."""
        import logging
        caplog.set_level(logging.ERROR)

        workflow_id = "test-workflow"
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        # Non-mailbox path - should be no-op without error
        tool_input = {"file_path": str(tmp_path / "other_file.txt")}

        # Call hook - should complete without logging
        result = await post_tool_use_hook(
            hook_context=context,
            tool_name="Write",
            tool_input=tool_input,
            tool_output={"success": True}
        )

        # Hook should return None
        assert result is None

        # Verify no errors were logged
        assert len(caplog.records) == 0
