# ABOUTME: Test suite for write_message function
# ABOUTME: Consolidated tests for message writing to JSONL files

"""Tests for message writer functionality.

Consolidated from 29 separate tests to focused tests covering essential
behaviors without per-field or per-priority redundancy.
"""

import json
from pathlib import Path

import pytest

from jean_claude.core.message import Message, MessagePriority
from jean_claude.core.message_writer import write_message, MessageBox
from jean_claude.core.mailbox_paths import MailboxPaths


class TestWriteMessageBasics:
    """Tests for basic write_message functionality - consolidated from 4 tests to 1."""

    def test_write_message_to_inbox_outbox_creates_dir_and_appends(self, tmp_path, message_factory):
        """Test writing to inbox, outbox, directory creation, and appending."""
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Verify directory doesn't exist
        assert not paths.mailbox_dir.exists()

        # Write to inbox (creates directory)
        inbox_msg = message_factory(subject="Inbox message", body="Test body")
        write_message(inbox_msg, MessageBox.INBOX, paths)

        # Directory and file should exist
        assert paths.mailbox_dir.exists()
        assert paths.inbox_path.exists()

        # Verify content
        content = paths.inbox_path.read_text()
        parsed = json.loads(content.strip())
        assert parsed["subject"] == "Inbox message"

        # Write to outbox
        outbox_msg = message_factory(type="notification", subject="Outbox message")
        write_message(outbox_msg, MessageBox.OUTBOX, paths)
        assert paths.outbox_path.exists()

        # Verify appending
        second_msg = message_factory(
            from_agent="agent-3", to_agent="agent-4", subject="Second message"
        )
        write_message(second_msg, MessageBox.INBOX, paths)

        lines = paths.inbox_path.read_text().strip().split('\n')
        assert len(lines) == 2


class TestWriteMessageJSONLSerialization:
    """Tests for JSONL serialization - consolidated from 4 tests to 1."""

    def test_write_message_jsonl_format_and_field_preservation(self, tmp_path, message_factory):
        """Test JSONL format and all field preservation including special chars."""
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Write multiple messages
        for i in range(3):
            msg = message_factory(
                from_agent=f"agent-{i}", to_agent="agent-x",
                subject=f"Message {i}", body=f"Body {i}"
            )
            write_message(msg, MessageBox.INBOX, paths)

        # Verify JSONL format
        lines = paths.inbox_path.read_text().strip().split('\n')
        assert len(lines) == 3
        for i, line in enumerate(lines):
            parsed = json.loads(line)
            assert parsed["subject"] == f"Message {i}"

        # Write message with all fields
        full_msg = Message(
            id="msg-123", from_agent="coordinator", to_agent="worker-1",
            type="help_request", subject="Need help", body="I need assistance",
            priority=MessagePriority.URGENT, awaiting_response=True
        )
        write_message(full_msg, MessageBox.OUTBOX, paths)

        parsed = json.loads(paths.outbox_path.read_text().strip())
        assert parsed["id"] == "msg-123"
        assert parsed["priority"] == "urgent"
        assert parsed["awaiting_response"] is True
        assert "created_at" in parsed

        # Special characters and multiline
        special_msg = Message(
            from_agent="agent-1", to_agent="agent-2", type="test",
            subject="Special chars: \"quotes\", <tags>",
            body="Body with\nnewlines and\ttabs and @#$%"
        )
        write_message(special_msg, MessageBox.OUTBOX, paths)

        lines = paths.outbox_path.read_text().strip().split('\n')
        parsed = json.loads(lines[-1])
        assert '"quotes"' in parsed["subject"]
        assert "\n" in parsed["body"]


class TestWriteMessageErrorHandling:
    """Tests for error handling - consolidated from 4 tests to 1."""

    def test_write_message_handles_errors_gracefully(self, tmp_path, message_factory):
        """Test error handling for invalid inputs and permissions."""
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Invalid message type
        with pytest.raises((TypeError, AttributeError)):
            write_message("not a message", MessageBox.INBOX, paths)

        # Invalid mailbox type
        msg = message_factory(subject="Test", body="Body")
        with pytest.raises((ValueError, AttributeError)):
            write_message(msg, "invalid_mailbox", paths)

        # Permission error
        paths.ensure_mailbox_dir()
        paths.inbox_path.touch()
        paths.inbox_path.chmod(0o444)  # Read-only
        with pytest.raises(PermissionError):
            write_message(msg, MessageBox.INBOX, paths)
        paths.inbox_path.chmod(0o644)  # Cleanup


class TestWriteMessagePrioritiesAndFlags:
    """Tests for priorities and awaiting_response - consolidated from 5 tests to 1."""

    def test_write_message_preserves_all_priorities_and_flags(self, tmp_path, message_factory):
        """Test all priority levels and awaiting_response flag are preserved."""
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # All priority levels and awaiting_response combinations
        for priority in [MessagePriority.LOW, MessagePriority.NORMAL, MessagePriority.URGENT]:
            for awaiting in [True, False]:
                msg = message_factory(
                    subject=f"{priority.value}-{awaiting}",
                    priority=priority, awaiting_response=awaiting
                )
                write_message(msg, MessageBox.INBOX, paths)

        # Verify all are saved correctly
        lines = paths.inbox_path.read_text().strip().split('\n')
        assert len(lines) == 6

        priorities_found = set()
        awaiting_found = {True: False, False: False}
        for line in lines:
            parsed = json.loads(line)
            priorities_found.add(parsed["priority"])
            awaiting_found[parsed["awaiting_response"]] = True

        assert "low" in priorities_found
        assert "normal" in priorities_found
        assert "urgent" in priorities_found
        assert awaiting_found[True] is True
        assert awaiting_found[False] is True


class TestWriteMessageEdgeCases:
    """Tests for edge cases - consolidated from 5 tests to 1."""

    def test_write_message_edge_cases(self, tmp_path):
        """Test edge cases: long body, unicode, custom ID, timestamp."""
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Long body
        long_body = "A" * 10000
        msg_long = Message(
            from_agent="agent-1", to_agent="agent-2", type="test",
            subject="Long", body=long_body
        )
        write_message(msg_long, MessageBox.INBOX, paths)
        parsed = json.loads(paths.inbox_path.read_text().strip())
        assert len(parsed["body"]) == 10000

        # Unicode
        msg_unicode = Message(
            from_agent="agent-1", to_agent="agent-2", type="test",
            subject="Unicode: 你好 🚀 café",
            body="Emojis: 😀 and chars: ñ"
        )
        write_message(msg_unicode, MessageBox.OUTBOX, paths)
        parsed = json.loads(paths.outbox_path.read_text().strip())
        assert "你好" in parsed["subject"]
        assert "🚀" in parsed["subject"]

        # Custom ID preserved
        msg_id = Message(
            id="custom-id-12345", from_agent="agent-1", to_agent="agent-2",
            type="test", subject="Test", body="Body"
        )
        write_message(msg_id, MessageBox.OUTBOX, paths)
        lines = paths.outbox_path.read_text().strip().split('\n')
        parsed = json.loads(lines[-1])
        assert parsed["id"] == "custom-id-12345"


class TestMessageBoxEnum:
    """Tests for MessageBox enum - consolidated from 4 tests to 1."""

    def test_messagebox_enum_maps_to_correct_paths(self, tmp_path, sample_message):
        """Test that INBOX and OUTBOX map to correct file paths."""
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        assert hasattr(MessageBox, 'INBOX')
        assert hasattr(MessageBox, 'OUTBOX')

        # INBOX maps to inbox.jsonl
        write_message(sample_message, MessageBox.INBOX, paths)
        assert paths.inbox_path.exists()
        assert not paths.outbox_path.exists()

        # OUTBOX maps to outbox.jsonl
        paths2 = MailboxPaths(workflow_id="test-workflow-2", base_dir=tmp_path)
        write_message(sample_message, MessageBox.OUTBOX, paths2)
        assert paths2.outbox_path.exists()
        assert not paths2.inbox_path.exists()


class TestWriteMessageIntegration:
    """Integration tests - consolidated from 2 tests to 1."""

    def test_write_message_realistic_workflow(self, tmp_path):
        """Test realistic workflow with inbox and outbox."""
        paths = MailboxPaths(workflow_id="coordinator-workflow", base_dir=tmp_path)

        # Coordinator receives help request
        help_request = Message(
            from_agent="worker-1", to_agent="coordinator",
            type="help_request", subject="Need assistance",
            body="I'm stuck", priority=MessagePriority.URGENT,
            awaiting_response=True
        )
        write_message(help_request, MessageBox.INBOX, paths)

        # Coordinator sends response
        response = Message(
            from_agent="coordinator", to_agent="worker-1",
            type="help_response", subject="Re: Need assistance",
            body="Try approach X", priority=MessagePriority.URGENT
        )
        write_message(response, MessageBox.OUTBOX, paths)

        # Coordinator receives status update
        status = Message(
            from_agent="worker-2", to_agent="coordinator",
            type="status_update", subject="Done",
            body="Finished", priority=MessagePriority.NORMAL
        )
        write_message(status, MessageBox.INBOX, paths)

        # Verify counts
        inbox_lines = paths.inbox_path.read_text().strip().split('\n')
        outbox_lines = paths.outbox_path.read_text().strip().split('\n')
        assert len(inbox_lines) == 2
        assert len(outbox_lines) == 1
