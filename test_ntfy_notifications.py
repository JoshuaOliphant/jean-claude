#!/usr/bin/env python3
"""Test script for ntfy.sh push notifications.

SETUP INSTRUCTIONS:
1. Install ntfy app on your phone:
   - iOS: https://apps.apple.com/us/app/ntfy/id1625396347
   - Android: https://play.google.com/store/apps/details?id=io.heckel.ntfy

2. Choose a unique topic name (this is your "channel"):
   Example: jean-claude-la-boeuf-secret-abc123
   (Make it unique and hard to guess for privacy!)

3. Subscribe to your topic in the ntfy app:
   - Open app → "+" button → Enter your topic name

4. Set environment variable:
   export JEAN_CLAUDE_NTFY_TOPIC="your-topic-name-here"

5. Run this test script:
   uv run python test_ntfy_notifications.py

You should get push notifications on your phone!
"""

import asyncio
import os
import sys
from pathlib import Path
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jean_claude.tools.mailbox_tools import (
    ask_user,
    notify_user,
    set_workflow_context,
)
from jean_claude.core.state import WorkflowState


async def test_ntfy_notifications():
    """Test ntfy.sh push notifications."""
    print("🧪 Testing Jean Claude ntfy.sh Push Notifications\n")

    # Check if topic is configured
    topic = os.environ.get("JEAN_CLAUDE_NTFY_TOPIC")
    if not topic:
        print("❌ ERROR: JEAN_CLAUDE_NTFY_TOPIC environment variable not set!")
        print("\nTo set it, run:")
        print('  export JEAN_CLAUDE_NTFY_TOPIC="your-unique-topic-name"')
        print("\nExample:")
        print('  export JEAN_CLAUDE_NTFY_TOPIC="jean-claude-la-boeuf-abc123"')
        print("\nThen run this script again.")
        return

    print(f"✅ Topic configured: {topic}")
    print(f"📱 Make sure you're subscribed to '{topic}' in the ntfy app!\n")

    # Create temporary workflow directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        workflow_dir = tmp_path / "agents" / "test-workflow-123"
        workflow_dir.mkdir(parents=True)

        # Create mock workflow state
        workflow_state = WorkflowState(
            workflow_id="test-workflow-123",
            workflow_name="ntfy Test",
            workflow_type="two-agent"
        )

        # Set workflow context
        set_workflow_context(workflow_dir, workflow_state, tmp_path)

        # Test 1: Informational notification
        print("Test 1: Sending informational notification to your phone...")
        notify_args = {
            "message": "Jean Claude test notification! If you see this on your phone, it's working! 🎉",
            "priority": "low"
        }

        result = await notify_user.handler(notify_args)
        print(f"✓ notify_user result: {result['content'][0]['text']}")
        print("  → Check your phone! You should see: 'ℹ️ Jean Claude Agent Update'\n")

        print("Waiting 8 seconds before sending urgent notification...\n")
        await asyncio.sleep(8)

        # Test 2: Urgent help request
        print("Test 2: Sending URGENT help request to your phone...")

        # Mock the OutboxMonitor
        from unittest.mock import AsyncMock, patch
        from jean_claude.core.message import Message

        mock_response = Message(
            from_agent="user",
            to_agent="coder-agent",
            type="response",
            subject="Re: Test",
            body="Test response from phone"
        )

        with patch('jean_claude.tools.mailbox_tools.OutboxMonitor') as mock_monitor_class:
            mock_monitor = AsyncMock()
            mock_monitor.wait_for_response = AsyncMock(return_value=mock_response)
            mock_monitor_class.return_value = mock_monitor

            ask_args = {
                "question": "URGENT TEST: Tests failing! Should I update the test expectations or fix the code? This is a test of the emergency notification system!",
                "context": "Testing ntfy.sh integration - you should get this on your phone with MAX priority!",
                "priority": "urgent"
            }

            result = await ask_user.handler(ask_args)
            print(f"✓ ask_user result: {result['content'][0]['text'][:80]}...")
            print("  → Check your phone! You should see: '🤖 Jean Claude Agent Needs Help'")
            print("  → It should be HIGH PRIORITY with warning emojis! 🚨\n")

        print("=" * 60)
        print("✅ Test complete!")
        print(f"📬 Messages written to: {workflow_dir / 'INBOX'}")
        print(f"📱 Push notifications sent to topic: {topic}")
        print("=" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("Jean Claude ntfy.sh Push Notification Test")
    print("=" * 60)
    print()

    asyncio.run(test_ntfy_notifications())

    print("\n" + "=" * 60)
    print("Did you receive the notifications on your phone?")
    print("- First: Informational update (normal priority)")
    print("- Second: Urgent help request (MAX priority + warning tags)")
    print("=" * 60)
