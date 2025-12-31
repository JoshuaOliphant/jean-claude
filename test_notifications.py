#!/usr/bin/env python3
"""Test script for mailbox notification system.

This script simulates agent behavior to test desktop notifications
when agents send messages via ask_user and notify_user tools.
"""

import asyncio
from pathlib import Path
import tempfile

# Add src to path so we can import jean_claude modules
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jean_claude.tools.mailbox_tools import (
    ask_user,
    notify_user,
    set_workflow_context,
)
from jean_claude.core.state import WorkflowState


async def test_notifications():
    """Test desktop notifications from mailbox tools."""
    print("🧪 Testing Jean Claude Mailbox Notifications\n")

    # Create temporary workflow directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        workflow_dir = tmp_path / "agents" / "test-workflow-123"
        workflow_dir.mkdir(parents=True)

        # Create mock workflow state
        workflow_state = WorkflowState(
            workflow_id="test-workflow-123",
            workflow_name="Notification Test",
            workflow_type="two-agent"
        )

        # Set workflow context
        set_workflow_context(workflow_dir, workflow_state, tmp_path)

        print("✅ Workflow context initialized")
        print(f"📁 Workflow directory: {workflow_dir}\n")

        # Test 1: notify_user (informational notification)
        print("Test 1: Sending informational notification...")
        notify_args = {
            "message": "Successfully completed feature implementation. Now running tests...",
            "priority": "low"
        }

        result = await notify_user.handler(notify_args)
        print(f"✓ notify_user result: {result['content'][0]['text']}")
        print("  → Check your screen! You should see a notification with sound\n")
        print("Waiting 5 seconds before next notification...\n")

        await asyncio.sleep(5)  # Give you time to see the notification

        # Test 2: ask_user (urgent notification)
        print("Test 2: Sending urgent help request notification...")

        # Mock the OutboxMonitor to avoid actually waiting
        from unittest.mock import AsyncMock, patch
        from jean_claude.core.message import Message

        mock_response = Message(
            from_agent="user",
            to_agent="coder-agent",
            type="response",
            subject="Re: Test question",
            body="This is a test response - in real usage, you'd write to OUTBOX"
        )

        with patch('jean_claude.tools.mailbox_tools.OutboxMonitor') as mock_monitor_class:
            mock_monitor = AsyncMock()
            mock_monitor.wait_for_response = AsyncMock(return_value=mock_response)
            mock_monitor_class.return_value = mock_monitor

            ask_args = {
                "question": "Test fails with status 403 but expects 401. Should I update the test or fix the auth code?",
                "context": "Implementing JWT authentication feature",
                "priority": "urgent"
            }

            result = await ask_user.handler(ask_args)
            print(f"✓ ask_user result: {result['content'][0]['text'][:80]}...")
            print("  → Check your notifications! You should see: '🤖 Agent Needs Help'\n")

        # Check the INBOX directory
        inbox_dir = workflow_dir / "INBOX"
        if inbox_dir.exists():
            message_count = len(list(inbox_dir.glob("*.json")))
            print(f"✅ Test complete! {message_count} messages written to INBOX")
            print(f"📬 INBOX location: {inbox_dir}")

            # Show the messages
            for msg_file in inbox_dir.glob("*.json"):
                print(f"\n📨 Message: {msg_file.name}")
                import json
                with open(msg_file) as f:
                    msg_data = json.load(f)
                    print(f"   Subject: {msg_data['subject']}")
                    print(f"   Priority: {msg_data['priority']}")
                    print(f"   Awaiting response: {msg_data['awaiting_response']}")
        else:
            print("❌ No INBOX directory created")


if __name__ == "__main__":
    print("=" * 60)
    print("Jean Claude Mailbox Notification Test")
    print("=" * 60)
    print()

    asyncio.run(test_notifications())

    print("\n" + "=" * 60)
    print("Did you see the desktop notifications?")
    print("- Informational: 'ℹ️  Agent Update'")
    print("- Help Request: '🤖 Agent Needs Help'")
    print("=" * 60)
