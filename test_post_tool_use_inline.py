#!/usr/bin/env python3
"""Quick inline test for post_tool_use_hook."""

import asyncio
import tempfile
from pathlib import Path

from jean_claude.core.mailbox_api import Mailbox
from jean_claude.core.mailbox_paths import MailboxPaths
from jean_claude.core.message import Message, MessagePriority
from jean_claude.orchestration.post_tool_use_hook import post_tool_use_hook


async def test_post_tool_use_hook():
    """Test post_tool_use_hook functionality."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        workflow_id = "test-workflow"

        # Create mailbox
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)

        # Verify initial count is 0
        assert mailbox.get_unread_count() == 0, "Initial count should be 0"

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Test 1: Write to inbox should increment count
        await post_tool_use_hook(
            hook_context=context,
            tool_name="Write",
            tool_input={"file_path": str(paths.inbox_path)},
            tool_output={"success": True}
        )

        assert mailbox.get_unread_count() == 1, "Count should be 1 after inbox write"
        print("✓ Test 1 passed: Inbox write increments count")

        # Test 2: Write to outbox should NOT increment count
        await post_tool_use_hook(
            hook_context=context,
            tool_name="Write",
            tool_input={"file_path": str(paths.outbox_path)},
            tool_output={"success": True}
        )

        assert mailbox.get_unread_count() == 1, "Count should still be 1 after outbox write"
        print("✓ Test 2 passed: Outbox write does not increment count")

        # Test 3: Multiple inbox writes
        await post_tool_use_hook(
            hook_context=context,
            tool_name="Write",
            tool_input={"file_path": str(paths.inbox_path)},
            tool_output={"success": True}
        )

        assert mailbox.get_unread_count() == 2, "Count should be 2 after second inbox write"
        print("✓ Test 3 passed: Multiple inbox writes increment correctly")

        # Test 4: Write to non-mailbox file should NOT increment
        other_file = tmp_path / "other.txt"
        await post_tool_use_hook(
            hook_context=context,
            tool_name="Write",
            tool_input={"file_path": str(other_file)},
            tool_output={"success": True}
        )

        assert mailbox.get_unread_count() == 2, "Count should still be 2 after non-mailbox write"
        print("✓ Test 4 passed: Non-mailbox write does not increment count")

        # Test 5: Missing workflow_id should not crash
        result = await post_tool_use_hook(
            hook_context={},
            tool_name="Write",
            tool_input={"file_path": str(paths.inbox_path)},
            tool_output={"success": True}
        )

        assert result is None, "Should return None for missing workflow_id"
        assert mailbox.get_unread_count() == 2, "Count should still be 2"
        print("✓ Test 5 passed: Missing workflow_id handled gracefully")

        # Test 6: None context should not crash
        result = await post_tool_use_hook(
            hook_context=None,
            tool_name="Write",
            tool_input={"file_path": str(paths.inbox_path)},
            tool_output={"success": True}
        )

        assert result is None, "Should return None for None context"
        print("✓ Test 6 passed: None context handled gracefully")

        # Test 7: Write to inbox_count.json should NOT increment (no-op)
        await post_tool_use_hook(
            hook_context=context,
            tool_name="Write",
            tool_input={"file_path": str(paths.inbox_count_path)},
            tool_output={"success": True}
        )

        assert mailbox.get_unread_count() == 2, "Count should still be 2 after inbox_count write"
        print("✓ Test 7 passed: inbox_count.json write is no-op")

        print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_post_tool_use_hook())
