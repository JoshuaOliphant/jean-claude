# ABOUTME: Test suite for read_messages function
# ABOUTME: Consolidated tests for reading messages from JSONL files

"""Tests for message reader functionality.

Consolidated from 30 separate tests to focused tests covering essential
behaviors without per-field or per-priority redundancy.
"""

import json
from pathlib import Path

import pytest

from jean_claude.core.message import Message, MessagePriority
from jean_claude.core.message_reader import read_messages
from jean_claude.core.message_writer import write_message, MessageBox
from jean_claude.core.mailbox_paths import MailboxPaths


class TestReadMessagesBasics:
    """Tests for basic read_messages functionality - consolidated from 4 tests to 1."""

    def test_read_messages_from_inbox_outbox_and_multiple(self, tmp_path, message_factory):
        """Test reading from inbox, outbox, and multiple messages."""
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Write to inbox and verify reading
        inbox_msg = message_factory(subject="Inbox message", body="Test body")
        write_message(inbox_msg, MessageBox.INBOX, paths)
        inbox_messages = read_messages(MessageBox.INBOX, paths)
        assert len(inbox_messages) == 1
        assert inbox_messages[0].subject == "Inbox message"

        # Write to outbox and verify reading
        outbox_msg = message_factory(type="notification", subject="Outbox message")
        write_message(outbox_msg, MessageBox.OUTBOX, paths)
        outbox_messages = read_messages(MessageBox.OUTBOX, paths)
        assert len(outbox_messages) == 1
        assert outbox_messages[0].subject == "Outbox message"

        # Write more to inbox and verify multiple messages
        for i in range(3):
            msg = message_factory(
                from_agent=f"agent-{i+10}", to_agent="agent-x",
                subject=f"Message {i}", body=f"Body {i}"
            )
            write_message(msg, MessageBox.INBOX, paths)

        all_inbox = read_messages(MessageBox.INBOX, paths)
        assert len(all_inbox) == 4  # Original + 3 new

    def test_read_messages_preserves_all_fields(self, tmp_path, message_factory):
        """Test that all message fields including priority and awaiting_response are preserved."""
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        for priority in [MessagePriority.LOW, MessagePriority.NORMAL, MessagePriority.URGENT]:
            for awaiting in [True, False]:
                msg = message_factory(
                    from_agent="coordinator", to_agent="worker-1",
                    type="help_request", subject="Test",
                    priority=priority, awaiting_response=awaiting
                )
                write_message(msg, MessageBox.INBOX, paths)

        messages = read_messages(MessageBox.INBOX, paths)
        assert len(messages) == 6

        # Verify all priority/awaiting combinations are preserved
        priorities_found = {m.priority for m in messages}
        assert MessagePriority.LOW in priorities_found
        assert MessagePriority.URGENT in priorities_found
        assert any(m.awaiting_response is True for m in messages)
        assert any(m.awaiting_response is False for m in messages)


class TestReadMessagesEmptyAndMissing:
    """Tests for empty and missing files - consolidated from 3 tests to 1."""

    def test_read_messages_handles_missing_empty_and_whitespace_files(self, tmp_path):
        """Test reading from missing, empty, and whitespace-only files."""
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Missing file returns empty list
        assert read_messages(MessageBox.INBOX, paths) == []

        # Empty file returns empty list
        paths.ensure_mailbox_dir()
        paths.inbox_path.touch()
        assert read_messages(MessageBox.INBOX, paths) == []

        # Whitespace-only file returns empty list
        paths.inbox_path.write_text("\n\n  \n\t\n")
        assert read_messages(MessageBox.INBOX, paths) == []


class TestReadMessagesCorruptedData:
    """Tests for corrupted data handling - consolidated from 3 tests to 1."""

    def test_read_messages_handles_corrupted_and_invalid_json(self, tmp_path, message_factory):
        """Test that invalid JSON lines and incomplete messages are skipped."""
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)
        paths.ensure_mailbox_dir()

        # Write a valid message
        msg1 = message_factory(subject="Valid message")
        write_message(msg1, MessageBox.INBOX, paths)

        # Append invalid JSON and incomplete message
        with open(paths.inbox_path, 'a') as f:
            f.write("This is not valid JSON\n")
            f.write('{"from_agent": "agent-x"}\n')  # Missing required fields

        # Write another valid message
        msg2 = message_factory(
            from_agent="agent-3", to_agent="agent-4", subject="Second valid"
        )
        write_message(msg2, MessageBox.INBOX, paths)

        # Should get only valid messages
        messages = read_messages(MessageBox.INBOX, paths)
        assert len(messages) == 2
        assert messages[0].subject == "Valid message"
        assert messages[1].subject == "Second valid"

        # Completely corrupted file returns empty
        paths.outbox_path.write_text("<<< CORRUPTED FILE >>>")
        assert read_messages(MessageBox.OUTBOX, paths) == []


class TestReadMessagesSpecialCharacters:
    """Tests for special characters - consolidated from 3 tests to 1."""

    def test_read_messages_with_special_unicode_and_multiline(self, tmp_path):
        """Test reading messages with special chars, unicode, and multiline content."""
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Special characters
        msg1 = Message(
            from_agent="agent-1", to_agent="agent-2", type="test",
            subject="Special chars: \"quotes\", 'apostrophes', <tags>",
            body="Body with\nnewlines and\ttabs and symbols: @#$%^&*()"
        )
        write_message(msg1, MessageBox.INBOX, paths)

        # Unicode and emojis
        msg2 = Message(
            from_agent="agent-1", to_agent="agent-2", type="test",
            subject="Unicode test: 你好 🚀 café",
            body="Message with emojis: 😀 🎉 and special chars: ñ é ü"
        )
        write_message(msg2, MessageBox.INBOX, paths)

        # Multiline body
        multiline_body = """Line 1
Line 2
Line 3"""
        msg3 = Message(
            from_agent="agent-1", to_agent="agent-2", type="test",
            subject="Multiline", body=multiline_body
        )
        write_message(msg3, MessageBox.INBOX, paths)

        messages = read_messages(MessageBox.INBOX, paths)
        assert len(messages) == 3

        assert '"quotes"' in messages[0].subject
        assert "\n" in messages[0].body
        assert "你好" in messages[1].subject
        assert "🚀" in messages[1].subject
        assert messages[2].body.count('\n') == 2


class TestReadMessagesReturnType:
    """Tests for return type - consolidated from 3 tests to 1."""

    def test_read_messages_returns_list_of_message_objects(self, tmp_path, message_factory):
        """Test that read_messages returns list of independent Message objects."""
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Empty returns list
        assert isinstance(read_messages(MessageBox.INBOX, paths), list)

        # With messages returns Message objects
        for i in range(2):
            msg = message_factory(
                from_agent=f"agent-{i}", to_agent="agent-x",
                subject=f"Message {i}", body=f"Body {i}"
            )
            write_message(msg, MessageBox.INBOX, paths)

        messages = read_messages(MessageBox.INBOX, paths)
        assert len(messages) == 2
        assert all(isinstance(m, Message) for m in messages)
        assert messages[0] is not messages[1]
        assert messages[0].subject != messages[1].subject


class TestReadMessagesEdgeCases:
    """Tests for edge cases - consolidated from 4 tests to 1."""

    def test_read_messages_edge_cases(self, tmp_path, message_factory):
        """Test edge cases: long body, many messages, empty lines."""
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Very long body - edge case, keep inline for clarity
        long_body = "A" * 10000
        msg_long = Message(
            from_agent="agent-1", to_agent="agent-2", type="test",
            subject="Long", body=long_body
        )
        write_message(msg_long, MessageBox.INBOX, paths)

        messages = read_messages(MessageBox.INBOX, paths)
        assert len(messages[0].body) == 10000

        # Many messages and order preserved
        for i in range(50):
            msg = message_factory(
                from_agent=f"agent-{i}", to_agent="agent-x",
                subject=f"Message {i}", body=f"Body {i}"
            )
            write_message(msg, MessageBox.INBOX, paths)

        all_messages = read_messages(MessageBox.INBOX, paths)
        assert len(all_messages) == 51  # 1 long + 50 new
        # First message is the long one, then ordered 0-49
        for i, m in enumerate(all_messages[1:]):
            assert m.subject == f"Message {i}"


class TestReadMessagesValidation:
    """Tests for input validation - consolidated from 3 tests to 1."""

    def test_read_messages_validates_inputs(self, tmp_path):
        """Test that read_messages validates mailbox type and paths."""
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        with pytest.raises((ValueError, AttributeError)):
            read_messages("invalid_mailbox", paths)

        with pytest.raises((TypeError, ValueError, AttributeError)):
            read_messages(None, paths)

        with pytest.raises((TypeError, AttributeError)):
            read_messages(MessageBox.INBOX, None)


class TestReadMessagesIntegration:
    """Integration tests - consolidated from 2 tests to 1."""

    def test_read_messages_realistic_workflow(self, tmp_path):
        """Test realistic workflow with both inbox and outbox."""
        paths = MailboxPaths(workflow_id="coordinator-workflow", base_dir=tmp_path)

        # Coordinator receives help request
        help_request = Message(
            from_agent="worker-1", to_agent="coordinator",
            type="help_request", subject="Need assistance",
            body="I'm stuck", priority=MessagePriority.URGENT,
            awaiting_response=True
        )
        write_message(help_request, MessageBox.INBOX, paths)

        # Coordinator receives status update
        status_update = Message(
            from_agent="worker-2", to_agent="coordinator",
            type="status_update", subject="Task completed",
            body="Finished", priority=MessagePriority.NORMAL
        )
        write_message(status_update, MessageBox.INBOX, paths)

        # Coordinator sends response
        response = Message(
            from_agent="coordinator", to_agent="worker-1",
            type="help_response", subject="Re: Need assistance",
            body="Try this", priority=MessagePriority.URGENT
        )
        write_message(response, MessageBox.OUTBOX, paths)

        # Verify messages in each mailbox
        inbox = read_messages(MessageBox.INBOX, paths)
        outbox = read_messages(MessageBox.OUTBOX, paths)

        assert len(inbox) == 2
        assert len(outbox) == 1
        assert inbox[0].priority == MessagePriority.URGENT
        assert inbox[0].awaiting_response is True
        assert inbox[1].priority == MessagePriority.NORMAL
