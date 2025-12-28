#!/usr/bin/env python
"""Quick test of subagent_stop_hook implementation."""

import asyncio
import tempfile
from pathlib import Path

from jean_claude.core.message import Message, MessagePriority
from jean_claude.core.mailbox_api import Mailbox
from jean_claude.orchestration.subagent_stop_hook import subagent_stop_hook


async def test_basic():
    """Test basic functionality."""
    print("Testing subagent_stop_hook...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        workflow_id = "test-workflow"

        # Test 1: No messages
        print("\n1. Testing with no messages...")
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await subagent_stop_hook(hook_context=context)
        assert result is None, f"Expected None, got {result}"
        print("✓ Returns None when no messages")

        # Test 2: Normal message (should be ignored)
        print("\n2. Testing with normal message...")
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg = Message(
            from_agent="agent-1",
            to_agent="coordinator",
            type="status",
            subject="Status update",
            body="Work is progressing",
            priority=MessagePriority.NORMAL
        )
        mailbox.send_message(msg, to_inbox=False)
        result = await subagent_stop_hook(hook_context=context)
        assert result is None, f"Expected None for normal message, got {result}"
        print("✓ Returns None for normal priority messages")

        # Test 3: Urgent message
        print("\n3. Testing with urgent message...")
        urgent_msg = Message(
            from_agent="agent-1",
            to_agent="coordinator",
            type="help_request",
            subject="Need help",
            body="I'm stuck on a problem",
            priority=MessagePriority.URGENT
        )
        mailbox.send_message(urgent_msg, to_inbox=False)
        result = await subagent_stop_hook(hook_context=context)
        assert result is not None, "Expected notification for urgent message"
        assert "systemMessage" in result, f"Expected systemMessage key, got {result}"
        assert "Need help" in result["systemMessage"], f"Expected subject in message"
        print(f"✓ Returns notification for urgent message:")
        print(f"  {result['systemMessage'][:100]}...")

        # Test 4: Awaiting response message
        print("\n4. Testing with awaiting response message...")
        # Clear outbox
        from jean_claude.core.mailbox_paths import MailboxPaths
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)
        if paths.outbox_path.exists():
            paths.outbox_path.unlink()

        await_msg = Message(
            from_agent="agent-1",
            to_agent="coordinator",
            type="question",
            subject="Question about approach",
            body="Should I use approach A or B?",
            awaiting_response=True
        )
        mailbox.send_message(await_msg, to_inbox=False)
        result = await subagent_stop_hook(hook_context=context)
        assert result is not None, "Expected notification for awaiting_response message"
        assert "systemMessage" in result
        assert "Question about approach" in result["systemMessage"]
        print(f"✓ Returns notification for awaiting_response message:")
        print(f"  {result['systemMessage'][:100]}...")

        # Test 5: Error handling - corrupted outbox
        print("\n5. Testing error handling with corrupted outbox...")
        paths.outbox_path.write_text("not valid json\n")
        result = await subagent_stop_hook(hook_context=context)
        assert result is None, f"Expected None for corrupted outbox, got {result}"
        print("✓ Handles corrupted outbox gracefully")

        # Test 6: Error handling - None context
        print("\n6. Testing error handling with None context...")
        result = await subagent_stop_hook(hook_context=None)
        assert result is None, f"Expected None for None context, got {result}"
        print("✓ Handles None context gracefully")

        # Test 7: Error handling - missing workflow_id
        print("\n7. Testing error handling with missing workflow_id...")
        result = await subagent_stop_hook(hook_context={"base_dir": tmp_path})
        assert result is None, f"Expected None for missing workflow_id, got {result}"
        print("✓ Handles missing workflow_id gracefully")

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_basic())
