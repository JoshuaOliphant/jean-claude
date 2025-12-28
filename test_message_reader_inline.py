#!/usr/bin/env python3
"""Inline test for message_reader to verify basic functionality."""

import tempfile
from pathlib import Path

# Import the modules
from src.jean_claude.core.message import Message, MessagePriority
from src.jean_claude.core.message_reader import read_messages
from src.jean_claude.core.message_writer import write_message, MessageBox
from src.jean_claude.core.mailbox_paths import MailboxPaths

def test_basic_functionality():
    """Test basic read_messages functionality."""
    print("Testing message_reader basic functionality...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Test 1: Reading from non-existent file should return empty list
        messages = read_messages(MessageBox.INBOX, paths)
        assert messages == [], f"Expected empty list, got {messages}"
        print("✓ Test 1 passed: Non-existent file returns empty list")

        # Test 2: Write and read a single message
        msg = Message(
            from_agent="agent-1",
            to_agent="agent-2",
            type="test",
            subject="Test message",
            body="Test body"
        )
        write_message(msg, MessageBox.INBOX, paths)

        messages = read_messages(MessageBox.INBOX, paths)
        assert len(messages) == 1, f"Expected 1 message, got {len(messages)}"
        assert messages[0].from_agent == "agent-1"
        assert messages[0].subject == "Test message"
        print("✓ Test 2 passed: Can write and read a single message")

        # Test 3: Write and read multiple messages
        for i in range(3):
            msg = Message(
                from_agent=f"agent-{i}",
                to_agent="agent-x",
                type="test",
                subject=f"Message {i}",
                body=f"Body {i}"
            )
            write_message(msg, MessageBox.INBOX, paths)

        messages = read_messages(MessageBox.INBOX, paths)
        assert len(messages) == 4, f"Expected 4 messages, got {len(messages)}"  # 1 from test 2 + 3 new ones
        print("✓ Test 3 passed: Can write and read multiple messages")

        # Test 4: Read from outbox
        outbox_msg = Message(
            from_agent="agent-x",
            to_agent="agent-y",
            type="notification",
            subject="Outbox test",
            body="Outbox body"
        )
        write_message(outbox_msg, MessageBox.OUTBOX, paths)

        outbox_messages = read_messages(MessageBox.OUTBOX, paths)
        assert len(outbox_messages) == 1
        assert outbox_messages[0].subject == "Outbox test"
        print("✓ Test 4 passed: Can read from outbox")

        # Test 5: Preserve message fields
        urgent_msg = Message(
            id="msg-123",
            from_agent="coordinator",
            to_agent="worker-1",
            type="help_request",
            subject="Need help",
            body="I need assistance",
            priority=MessagePriority.URGENT,
            awaiting_response=True
        )

        paths2 = MailboxPaths(workflow_id="test-workflow-2", base_dir=tmp_path)
        write_message(urgent_msg, MessageBox.INBOX, paths2)

        messages2 = read_messages(MessageBox.INBOX, paths2)
        assert len(messages2) == 1
        assert messages2[0].id == "msg-123"
        assert messages2[0].priority == MessagePriority.URGENT
        assert messages2[0].awaiting_response is True
        print("✓ Test 5 passed: All message fields are preserved")

        # Test 6: Handle corrupted data gracefully
        paths3 = MailboxPaths(workflow_id="test-workflow-3", base_dir=tmp_path)
        paths3.ensure_mailbox_dir()

        # Write valid message
        valid_msg = Message(
            from_agent="agent-1",
            to_agent="agent-2",
            type="test",
            subject="Valid",
            body="Body"
        )
        write_message(valid_msg, MessageBox.INBOX, paths3)

        # Append invalid JSON
        with open(paths3.inbox_path, 'a') as f:
            f.write("This is not valid JSON\n")
            f.write('{"incomplete": "message"}\n')  # Missing required fields

        # Should only get the valid message
        messages3 = read_messages(MessageBox.INBOX, paths3)
        assert len(messages3) == 1
        assert messages3[0].subject == "Valid"
        print("✓ Test 6 passed: Corrupted data handled gracefully")

    print("\n✅ All tests passed!")

if __name__ == "__main__":
    try:
        test_basic_functionality()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
