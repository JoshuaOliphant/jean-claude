# ABOUTME: Test suite for PostToolUse hook callback
# ABOUTME: Tests hook that detects mailbox writes and updates inbox_count accordingly

"""Tests for PostToolUse hook functionality.

This module tests the PostToolUse hook that monitors tool usage for writes
to mailbox paths and updates inbox_count.json when inbox.jsonl is modified.
"""

import pytest

from jean_claude.core.mailbox_paths import MailboxPaths
from jean_claude.core.inbox_count_persistence import read_inbox_count, write_inbox_count
from jean_claude.core.inbox_count import InboxCount
from jean_claude.orchestration.post_tool_use_hook import post_tool_use_hook


class TestPostToolUseHookBasics:
    """Tests for basic PostToolUse hook context validation."""

    @pytest.mark.asyncio
    async def test_hook_returns_none_when_context_is_none(self):
        """Test that hook returns None when context is None."""
        result = await post_tool_use_hook(
            hook_context=None,
            tool_name="Write",
            tool_input={"file_path": "/some/path"},
            tool_output={"success": True}
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_returns_none_when_context_is_not_dict(self):
        """Test that hook returns None when context is not a dict."""
        result = await post_tool_use_hook(
            hook_context="not a dict",
            tool_name="Write",
            tool_input={"file_path": "/some/path"},
            tool_output={"success": True}
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_returns_none_when_workflow_id_missing(self, tmp_path):
        """Test that hook returns None when workflow_id is missing."""
        result = await post_tool_use_hook(
            hook_context={"base_dir": tmp_path},
            tool_name="Write",
            tool_input={"file_path": "/some/path"},
            tool_output={"success": True}
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_returns_none_when_tool_input_is_none(self, tmp_path):
        """Test that hook returns None when tool_input is None."""
        result = await post_tool_use_hook(
            hook_context={"workflow_id": "test-workflow", "base_dir": tmp_path},
            tool_name="Write",
            tool_input=None,
            tool_output={"success": True}
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_returns_none_when_tool_input_not_dict(self, tmp_path):
        """Test that hook returns None when tool_input is not a dict."""
        result = await post_tool_use_hook(
            hook_context={"workflow_id": "test-workflow", "base_dir": tmp_path},
            tool_name="Write",
            tool_input="not a dict",
            tool_output={"success": True}
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_returns_none_when_file_path_missing(self, tmp_path):
        """Test that hook returns None when file_path is missing from tool_input."""
        result = await post_tool_use_hook(
            hook_context={"workflow_id": "test-workflow", "base_dir": tmp_path},
            tool_name="Write",
            tool_input={"content": "some content"},
            tool_output={"success": True}
        )
        assert result is None


class TestPostToolUseHookInboxWrites:
    """Tests for PostToolUse hook inbox write detection."""

    @pytest.mark.asyncio
    async def test_hook_increments_inbox_count_on_inbox_write(self, tmp_path):
        """Test that hook increments inbox_count when inbox.jsonl is written."""
        workflow_id = "test-workflow"
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)
        paths.ensure_mailbox_dir()

        # Initialize inbox_count to 0
        inbox_count = InboxCount(unread=0)
        write_inbox_count(inbox_count, paths)

        # Simulate a write to inbox.jsonl
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        tool_input = {"file_path": str(paths.inbox_path)}

        await post_tool_use_hook(
            hook_context=context,
            tool_name="Write",
            tool_input=tool_input,
            tool_output={"success": True}
        )

        # Verify inbox_count was incremented
        updated_count = read_inbox_count(paths)
        assert updated_count.unread == 1

    @pytest.mark.asyncio
    async def test_hook_increments_multiple_times(self, tmp_path):
        """Test that hook increments inbox_count correctly on multiple writes."""
        workflow_id = "test-workflow"
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)
        paths.ensure_mailbox_dir()

        # Initialize inbox_count to 0
        inbox_count = InboxCount(unread=0)
        write_inbox_count(inbox_count, paths)

        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        tool_input = {"file_path": str(paths.inbox_path)}

        # Simulate 3 writes to inbox
        for _ in range(3):
            await post_tool_use_hook(
                hook_context=context,
                tool_name="Write",
                tool_input=tool_input,
                tool_output={"success": True}
            )

        # Verify inbox_count is now 3
        updated_count = read_inbox_count(paths)
        assert updated_count.unread == 3

    @pytest.mark.asyncio
    async def test_hook_creates_inbox_count_if_missing(self, tmp_path):
        """Test that hook creates inbox_count.json if it doesn't exist."""
        workflow_id = "test-workflow"
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)
        paths.ensure_mailbox_dir()

        # Don't initialize inbox_count - let hook create it
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        tool_input = {"file_path": str(paths.inbox_path)}

        await post_tool_use_hook(
            hook_context=context,
            tool_name="Write",
            tool_input=tool_input,
            tool_output={"success": True}
        )

        # Verify inbox_count was created and incremented
        updated_count = read_inbox_count(paths)
        assert updated_count.unread == 1


class TestPostToolUseHookNoOps:
    """Tests for PostToolUse hook no-op scenarios."""

    @pytest.mark.asyncio
    async def test_hook_noop_on_outbox_write(self, tmp_path):
        """Test that hook does not increment on outbox.jsonl write."""
        workflow_id = "test-workflow"
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)
        paths.ensure_mailbox_dir()

        # Initialize inbox_count to 5
        inbox_count = InboxCount(unread=5)
        write_inbox_count(inbox_count, paths)

        # Simulate a write to outbox.jsonl
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        tool_input = {"file_path": str(paths.outbox_path)}

        await post_tool_use_hook(
            hook_context=context,
            tool_name="Write",
            tool_input=tool_input,
            tool_output={"success": True}
        )

        # Verify inbox_count was NOT changed
        updated_count = read_inbox_count(paths)
        assert updated_count.unread == 5

    @pytest.mark.asyncio
    async def test_hook_noop_on_inbox_count_write(self, tmp_path):
        """Test that hook does not modify on inbox_count.json write."""
        workflow_id = "test-workflow"
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)
        paths.ensure_mailbox_dir()

        # Initialize inbox_count to 5
        inbox_count = InboxCount(unread=5)
        write_inbox_count(inbox_count, paths)

        # Simulate a write to inbox_count.json
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        tool_input = {"file_path": str(paths.inbox_count_path)}

        await post_tool_use_hook(
            hook_context=context,
            tool_name="Write",
            tool_input=tool_input,
            tool_output={"success": True}
        )

        # Verify inbox_count was NOT changed (still 5)
        updated_count = read_inbox_count(paths)
        assert updated_count.unread == 5

    @pytest.mark.asyncio
    async def test_hook_noop_on_unrelated_file_write(self, tmp_path):
        """Test that hook does not act on writes to non-mailbox files."""
        workflow_id = "test-workflow"
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)
        paths.ensure_mailbox_dir()

        # Initialize inbox_count to 5
        inbox_count = InboxCount(unread=5)
        write_inbox_count(inbox_count, paths)

        # Simulate a write to some other file
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        tool_input = {"file_path": str(tmp_path / "some_other_file.txt")}

        await post_tool_use_hook(
            hook_context=context,
            tool_name="Write",
            tool_input=tool_input,
            tool_output={"success": True}
        )

        # Verify inbox_count was NOT changed
        updated_count = read_inbox_count(paths)
        assert updated_count.unread == 5


class TestPostToolUseHookErrorHandling:
    """Tests for error handling in PostToolUse hook."""

    @pytest.mark.asyncio
    async def test_hook_handles_invalid_path_gracefully(self, tmp_path):
        """Test that hook handles invalid file paths gracefully."""
        workflow_id = "test-workflow"

        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        # Invalid path with null bytes
        tool_input = {"file_path": "/path/with/\x00null/bytes"}

        # Should not raise, just return None
        result = await post_tool_use_hook(
            hook_context=context,
            tool_name="Write",
            tool_input=tool_input,
            tool_output={"success": True}
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_handles_nonexistent_base_dir_gracefully(self, tmp_path):
        """Test that hook handles nonexistent base_dir gracefully."""
        workflow_id = "test-workflow"

        # Use a base_dir that doesn't exist
        nonexistent = tmp_path / "does_not_exist"
        context = {"workflow_id": workflow_id, "base_dir": nonexistent}
        tool_input = {"file_path": str(nonexistent / "agents" / workflow_id / "mailbox" / "inbox.jsonl")}

        # Should not raise, just return None
        result = await post_tool_use_hook(
            hook_context=context,
            tool_name="Write",
            tool_input=tool_input,
            tool_output={"success": True}
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_handles_permission_errors_gracefully(self, tmp_path):
        """Test that hook handles errors gracefully without crashing."""
        workflow_id = "test-workflow"

        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        # Path that will cause issues during resolution
        tool_input = {"file_path": ""}

        # Should not raise, just return None
        result = await post_tool_use_hook(
            hook_context=context,
            tool_name="Write",
            tool_input=tool_input,
            tool_output={"success": True}
        )
        assert result is None


class TestPostToolUseHookIntegration:
    """Integration tests for PostToolUse hook with realistic scenarios."""

    @pytest.mark.asyncio
    async def test_hook_with_realistic_workflow_id(self, tmp_path):
        """Test hook with realistic beads workflow_id."""
        workflow_id = "beads-jean_claude-abc123"
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)
        paths.ensure_mailbox_dir()

        # Initialize inbox_count
        inbox_count = InboxCount(unread=0)
        write_inbox_count(inbox_count, paths)

        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        tool_input = {"file_path": str(paths.inbox_path)}

        await post_tool_use_hook(
            hook_context=context,
            tool_name="Write",
            tool_input=tool_input,
            tool_output={"success": True}
        )

        # Verify inbox_count was incremented
        updated_count = read_inbox_count(paths)
        assert updated_count.unread == 1

    @pytest.mark.asyncio
    async def test_hook_returns_none_always(self, tmp_path):
        """Test that hook always returns None (silent background operation)."""
        workflow_id = "test-workflow"
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)
        paths.ensure_mailbox_dir()

        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # All paths should return None
        for path in [paths.inbox_path, paths.outbox_path, paths.inbox_count_path]:
            result = await post_tool_use_hook(
                hook_context=context,
                tool_name="Write",
                tool_input={"file_path": str(path)},
                tool_output={"success": True}
            )
            assert result is None, f"Expected None for {path.name}"

    @pytest.mark.asyncio
    async def test_hook_with_absolute_vs_relative_paths(self, tmp_path):
        """Test that hook correctly resolves both absolute and relative paths."""
        workflow_id = "test-workflow"
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)
        paths.ensure_mailbox_dir()

        # Initialize inbox_count
        inbox_count = InboxCount(unread=0)
        write_inbox_count(inbox_count, paths)

        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Use absolute path
        await post_tool_use_hook(
            hook_context=context,
            tool_name="Write",
            tool_input={"file_path": str(paths.inbox_path.resolve())},
            tool_output={"success": True}
        )

        # Verify inbox_count was incremented
        updated_count = read_inbox_count(paths)
        assert updated_count.unread == 1
