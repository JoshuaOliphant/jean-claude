#!/usr/bin/env python
"""Quick verification script for Mailbox API implementation."""

import tempfile
from pathlib import Path

# Test imports
print("Testing imports...")
try:
    from jean_claude.core.mailbox_api import Mailbox
    from jean_claude.core.message import Message, MessagePriority
    from jean_claude.core.mailbox_paths import MailboxPaths
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    exit(1)

# Test basic functionality
print("\nTesting basic functionality...")

with tempfile.TemporaryDirectory() as tmp_dir:
    tmp_path = Path(tmp_dir)

    # Test 1: Initialize mailbox
    print("  1. Initializing mailbox...")
    mailbox = Mailbox(workflow_id="test-workflow", base_dir=tmp_path)
    assert mailbox.workflow_id == "test-workflow"
    print("     ✓ Mailbox initialized")

    # Test 2: Send message to outbox
    print("  2. Sending message to outbox...")
    msg = Message(
        from_agent="agent-1",
        to_agent="agent-2",
        type="test",
        subject="Test message",
        body="Test body"
    )
    mailbox.send_message(msg, to_inbox=False)
    assert mailbox.paths.outbox_path.exists()
    print("     ✓ Message sent to outbox")

    # Test 3: Send message to inbox
    print("  3. Sending message to inbox...")
    inbox_msg = Message(
        from_agent="agent-2",
        to_agent="agent-1",
        type="response",
        subject="Response",
        body="Response body"
    )
    mailbox.send_message(inbox_msg, to_inbox=True)
    assert mailbox.paths.inbox_path.exists()
    print("     ✓ Message sent to inbox")

    # Test 4: Check unread count
    print("  4. Checking unread count...")
    unread = mailbox.get_unread_count()
    assert unread == 1, f"Expected 1 unread, got {unread}"
    print(f"     ✓ Unread count: {unread}")

    # Test 5: Get inbox messages
    print("  5. Getting inbox messages...")
    inbox_messages = mailbox.get_inbox_messages()
    assert len(inbox_messages) == 1
    assert inbox_messages[0].subject == "Response"
    print(f"     ✓ Retrieved {len(inbox_messages)} inbox message(s)")

    # Test 6: Get outbox messages
    print("  6. Getting outbox messages...")
    outbox_messages = mailbox.get_outbox_messages()
    assert len(outbox_messages) == 1
    assert outbox_messages[0].subject == "Test message"
    print(f"     ✓ Retrieved {len(outbox_messages)} outbox message(s)")

    # Test 7: Mark as read
    print("  7. Marking messages as read...")
    mailbox.mark_as_read()
    unread = mailbox.get_unread_count()
    assert unread == 0, f"Expected 0 unread after marking as read, got {unread}"
    print("     ✓ Messages marked as read")

    # Test 8: Send multiple messages and mark some as read
    print("  8. Testing partial mark as read...")
    for i in range(3):
        msg = Message(
            from_agent=f"agent-{i}",
            to_agent="me",
            type="test",
            subject=f"Message {i}",
            body=f"Body {i}"
        )
        mailbox.send_message(msg, to_inbox=True)

    unread = mailbox.get_unread_count()
    assert unread == 3, f"Expected 3 unread, got {unread}"

    mailbox.mark_as_read(count=2)
    unread = mailbox.get_unread_count()
    assert unread == 1, f"Expected 1 unread after marking 2 as read, got {unread}"
    print("     ✓ Partial mark as read works correctly")

    # Test 9: Test with urgent priority
    print("  9. Testing urgent priority message...")
    urgent_msg = Message(
        from_agent="coordinator",
        to_agent="worker",
        type="help_request",
        subject="Urgent help",
        body="Need immediate assistance",
        priority=MessagePriority.URGENT,
        awaiting_response=True
    )
    mailbox.send_message(urgent_msg, to_inbox=True)

    messages = mailbox.get_inbox_messages()
    # Find the urgent message
    urgent = [m for m in messages if m.priority == MessagePriority.URGENT]
    assert len(urgent) == 1
    assert urgent[0].awaiting_response is True
    print("     ✓ Urgent message handling works")

print("\n" + "="*50)
print("All basic tests passed! ✓")
print("="*50)
print("\nThe Mailbox API implementation appears to be working correctly.")
print("Run the full test suite with: python -m pytest tests/core/test_mailbox_api.py -v")
