#!/usr/bin/env python3
"""Quick inline test of message_writer functionality."""

import json
import tempfile
from pathlib import Path

from jean_claude.core.message import Message, MessagePriority
from jean_claude.core.message_writer import write_message, MessageBox
from jean_claude.core.mailbox_paths import MailboxPaths


def test_write_to_inbox():
    """Test writing a message to inbox."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create message
        message = Message(
            from_agent="agent-1",
            to_agent="agent-2",
            type="test",
            subject="Test message",
            body="Test body"
        )

        # Set up paths
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=Path(tmp_dir))

        # Write message
        write_message(message, MessageBox.INBOX, paths)

        # Verify
        assert paths.inbox_path.exists(), "Inbox file should exist"

        content = paths.inbox_path.read_text()
        parsed = json.loads(content.strip())

        assert parsed["from_agent"] == "agent-1"
        assert parsed["to_agent"] == "agent-2"
        assert parsed["type"] == "test"
        assert parsed["subject"] == "Test message"
        assert parsed["body"] == "Test body"

        print("✓ test_write_to_inbox passed")


def test_write_to_outbox():
    """Test writing a message to outbox."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create message
        message = Message(
            from_agent="agent-1",
            to_agent="agent-2",
            type="notification",
            subject="Test notification",
            body="Notification body"
        )

        # Set up paths
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=Path(tmp_dir))

        # Write message
        write_message(message, MessageBox.OUTBOX, paths)

        # Verify
        assert paths.outbox_path.exists(), "Outbox file should exist"

        content = paths.outbox_path.read_text()
        parsed = json.loads(content.strip())

        assert parsed["type"] == "notification"
        assert parsed["subject"] == "Test notification"

        print("✓ test_write_to_outbox passed")


def test_append_messages():
    """Test appending multiple messages."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=Path(tmp_dir))

        # Write first message
        msg1 = Message(
            from_agent="agent-1",
            to_agent="agent-2",
            type="test",
            subject="First",
            body="First body"
        )
        write_message(msg1, MessageBox.INBOX, paths)

        # Write second message
        msg2 = Message(
            from_agent="agent-3",
            to_agent="agent-4",
            type="test",
            subject="Second",
            body="Second body"
        )
        write_message(msg2, MessageBox.INBOX, paths)

        # Verify both messages
        content = paths.inbox_path.read_text()
        lines = content.strip().split('\n')

        assert len(lines) == 2, "Should have 2 messages"

        parsed1 = json.loads(lines[0])
        parsed2 = json.loads(lines[1])

        assert parsed1["subject"] == "First"
        assert parsed2["subject"] == "Second"

        print("✓ test_append_messages passed")


def test_directory_creation():
    """Test that directory is created if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        paths = MailboxPaths(workflow_id="new-workflow", base_dir=Path(tmp_dir))

        # Ensure directory doesn't exist
        assert not paths.mailbox_dir.exists(), "Directory should not exist initially"

        # Write message
        message = Message(
            from_agent="agent-1",
            to_agent="agent-2",
            type="test",
            subject="Test",
            body="Body"
        )
        write_message(message, MessageBox.INBOX, paths)

        # Directory should now exist
        assert paths.mailbox_dir.exists(), "Directory should be created"
        assert paths.inbox_path.exists(), "Inbox file should exist"

        print("✓ test_directory_creation passed")


def test_all_fields_preserved():
    """Test that all message fields are preserved."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=Path(tmp_dir))

        message = Message(
            id="msg-123",
            from_agent="coordinator",
            to_agent="worker-1",
            type="help_request",
            subject="Need help",
            body="I need assistance",
            priority=MessagePriority.URGENT,
            awaiting_response=True
        )

        write_message(message, MessageBox.OUTBOX, paths)

        content = paths.outbox_path.read_text()
        parsed = json.loads(content.strip())

        assert parsed["id"] == "msg-123"
        assert parsed["from_agent"] == "coordinator"
        assert parsed["to_agent"] == "worker-1"
        assert parsed["type"] == "help_request"
        assert parsed["priority"] == "urgent"
        assert parsed["awaiting_response"] is True

        print("✓ test_all_fields_preserved passed")


def main():
    """Run all inline tests."""
    print("Running message_writer inline tests...")
    print("=" * 80)

    try:
        test_write_to_inbox()
        test_write_to_outbox()
        test_append_messages()
        test_directory_creation()
        test_all_fields_preserved()

        print("=" * 80)
        print("✓ All inline tests passed!")
        print("=" * 80)
        return 0

    except AssertionError as e:
        print("=" * 80)
        print(f"✗ Test failed: {e}")
        print("=" * 80)
        return 1
    except Exception as e:
        print("=" * 80)
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 80)
        return 1


if __name__ == "__main__":
    exit(main())
