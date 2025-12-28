# ABOUTME: Test suite for Mailbox API class
# ABOUTME: Tests high-level mailbox API with consolidated test coverage

"""Tests for Mailbox API functionality.

Consolidated test suite focusing on essential behaviors rather than testing
each method variation separately.
"""

from datetime import datetime
from pathlib import Path

import pytest

from jean_claude.core.message import Message, MessagePriority
from jean_claude.core.mailbox_paths import MailboxPaths
from jean_claude.core.mailbox_api import Mailbox


class TestMailboxInitialization:
    """Tests for Mailbox initialization."""

    def test_mailbox_init_creates_paths_and_validates(self, tmp_path):
        """Test that Mailbox initializes with paths and validates workflow_id."""
        # Valid initialization
        mailbox = Mailbox(workflow_id="test-workflow", base_dir=tmp_path)
        assert mailbox.workflow_id == "test-workflow"
        assert hasattr(mailbox, 'paths')
        assert mailbox.paths.workflow_id == "test-workflow"

        # Invalid workflow IDs should raise
        with pytest.raises((ValueError, TypeError)):
            Mailbox(workflow_id="", base_dir=tmp_path)
        with pytest.raises(TypeError):
            Mailbox(workflow_id=None, base_dir=tmp_path)


class TestMailboxSendMessage:
    """Tests for send_message method - consolidated from 6 tests to 2."""

    def test_send_message_to_inbox_and_outbox(self, tmp_path, message_factory):
        """Test sending messages to both inbox and outbox."""
        mailbox = Mailbox(workflow_id="test-workflow", base_dir=tmp_path)

        # Create test messages
        inbox_msg = message_factory(subject="Inbox message", body="In inbox")
        outbox_msg = message_factory(
            from_agent="agent-2", to_agent="agent-1",
            subject="Outbox message", body="In outbox"
        )

        # Send to inbox - should increment unread count
        mailbox.send_message(inbox_msg, to_inbox=True)
        assert mailbox.paths.inbox_path.exists()
        assert "Inbox message" in mailbox.paths.inbox_path.read_text()
        assert mailbox.get_unread_count() == 1

        # Send to outbox - should NOT increment unread count
        mailbox.send_message(outbox_msg, to_inbox=False)
        assert mailbox.paths.outbox_path.exists()
        assert "Outbox message" in mailbox.paths.outbox_path.read_text()
        assert mailbox.get_unread_count() == 1  # Still 1

        # Default should go to outbox
        mailbox2 = Mailbox(workflow_id="test-workflow-2", base_dir=tmp_path)
        mailbox2.send_message(outbox_msg)
        assert mailbox2.paths.outbox_path.exists()
        assert not mailbox2.paths.inbox_path.exists()

    def test_send_multiple_messages(self, tmp_path, message_factory):
        """Test sending multiple messages to inbox."""
        mailbox = Mailbox(workflow_id="test-workflow", base_dir=tmp_path)

        for i in range(3):
            msg = message_factory(
                from_agent=f"agent-{i}", to_agent="agent-x",
                subject=f"Message {i}", body=f"Body {i}"
            )
            mailbox.send_message(msg, to_inbox=True)

        assert mailbox.get_unread_count() == 3
        messages = mailbox.get_inbox_messages()
        assert len(messages) == 3


class TestMailboxGetMessages:
    """Tests for get_inbox_messages and get_outbox_messages - consolidated from 8 tests to 2."""

    def test_get_messages_returns_correct_type_and_order(self, tmp_path, message_factory):
        """Test that get_inbox/outbox_messages returns correct messages in order."""
        mailbox = Mailbox(workflow_id="test-workflow", base_dir=tmp_path)

        # Empty initially
        assert mailbox.get_inbox_messages() == []
        assert mailbox.get_outbox_messages() == []

        # Send messages
        for i in range(3):
            inbox_msg = message_factory(
                from_agent=f"agent-{i}", to_agent="me",
                subject=f"Inbox {i}", body=f"Body {i}"
            )
            outbox_msg = message_factory(
                from_agent="me", to_agent=f"agent-{i}",
                subject=f"Outbox {i}", body=f"Body {i}"
            )
            mailbox.send_message(inbox_msg, to_inbox=True)
            mailbox.send_message(outbox_msg, to_inbox=False)

        # Check inbox
        inbox = mailbox.get_inbox_messages()
        assert len(inbox) == 3
        assert all(isinstance(m, Message) for m in inbox)
        assert inbox[0].subject == "Inbox 0"
        assert inbox[2].subject == "Inbox 2"

        # Check outbox
        outbox = mailbox.get_outbox_messages()
        assert len(outbox) == 3
        assert outbox[0].subject == "Outbox 0"

    def test_inbox_and_outbox_are_isolated(self, tmp_path, message_factory):
        """Test that inbox and outbox don't mix."""
        mailbox = Mailbox(workflow_id="test-workflow", base_dir=tmp_path)

        inbox_msg = message_factory(subject="Inbox only")
        outbox_msg = message_factory(
            from_agent="me", to_agent="agent-1", subject="Outbox only"
        )
        mailbox.send_message(inbox_msg, to_inbox=True)
        mailbox.send_message(outbox_msg, to_inbox=False)

        inbox = mailbox.get_inbox_messages()
        outbox = mailbox.get_outbox_messages()

        assert len(inbox) == 1
        assert inbox[0].subject == "Inbox only"
        assert len(outbox) == 1
        assert outbox[0].subject == "Outbox only"


class TestMailboxUnreadCount:
    """Tests for unread count - consolidated from 4 tests to 1."""

    def test_unread_count_behavior(self, tmp_path, message_factory):
        """Test complete unread count behavior in one test."""
        mailbox = Mailbox(workflow_id="test-workflow", base_dir=tmp_path)

        # Initially zero
        assert mailbox.get_unread_count() == 0

        # Inbox messages increment count
        for i in range(3):
            msg = message_factory(
                from_agent=f"agent-{i}", to_agent="me",
                subject=f"Inbox {i}", body=f"Body {i}"
            )
            mailbox.send_message(msg, to_inbox=True)
        assert mailbox.get_unread_count() == 3

        # Outbox messages don't affect count
        for i in range(5):
            msg = message_factory(
                from_agent="me", to_agent=f"agent-{i}",
                subject=f"Outbox {i}", body=f"Body {i}"
            )
            mailbox.send_message(msg, to_inbox=False)
        assert mailbox.get_unread_count() == 3  # Still 3


class TestMailboxMarkAsRead:
    """Tests for mark_as_read - consolidated from 5 tests to 1."""

    def test_mark_as_read_behavior(self, tmp_path, message_factory):
        """Test complete mark_as_read behavior in one test."""
        mailbox = Mailbox(workflow_id="test-workflow", base_dir=tmp_path)

        # Send 5 messages
        for i in range(5):
            msg = message_factory(
                from_agent=f"agent-{i}", to_agent="me",
                subject=f"Message {i}", body=f"Body {i}"
            )
            mailbox.send_message(msg, to_inbox=True)

        assert mailbox.get_unread_count() == 5

        # Mark 3 as read
        mailbox.mark_as_read(count=3)
        assert mailbox.get_unread_count() == 2

        # Mark all remaining as read
        mailbox.mark_as_read()
        assert mailbox.get_unread_count() == 0

        # Mark as read when already zero - should not error
        mailbox.mark_as_read()
        assert mailbox.get_unread_count() == 0


class TestMailboxIntegration:
    """Integration tests for complete mailbox workflows - kept essential tests."""

    def test_mailbox_complete_workflow(self, tmp_path, message_factory):
        """Test a complete mailbox workflow."""
        mailbox = Mailbox(workflow_id="test-workflow", base_dir=tmp_path)

        # Initial state
        assert mailbox.get_unread_count() == 0
        assert mailbox.get_inbox_messages() == []
        assert mailbox.get_outbox_messages() == []

        # Receive 2 messages in inbox
        for i in range(2):
            msg = message_factory(
                from_agent=f"agent-{i}", to_agent="me", type="request",
                subject=f"Request {i}", body=f"Please help with {i}"
            )
            mailbox.send_message(msg, to_inbox=True)

        assert mailbox.get_unread_count() == 2
        assert len(mailbox.get_inbox_messages()) == 2

        # Send 3 responses in outbox
        for i in range(3):
            msg = message_factory(
                from_agent="me", to_agent=f"agent-{i}", type="response",
                subject=f"Re: Request {i}", body=f"Here's help for {i}"
            )
            mailbox.send_message(msg, to_inbox=False)

        assert mailbox.get_unread_count() == 2  # Unchanged
        assert len(mailbox.get_outbox_messages()) == 3

        # Mark as read
        mailbox.mark_as_read()
        assert mailbox.get_unread_count() == 0
        assert len(mailbox.get_inbox_messages()) == 2  # Still there

    def test_mailbox_handles_urgent_messages(self, tmp_path, message_factory):
        """Test mailbox with urgent priority messages."""
        mailbox = Mailbox(workflow_id="test-workflow", base_dir=tmp_path)

        # Urgent message with specific priority - use factory with priority param
        urgent_msg = message_factory(
            type="help_request", subject="Urgent help needed",
            body="Need immediate assistance",
            priority=MessagePriority.URGENT, awaiting_response=True
        )
        mailbox.send_message(urgent_msg, to_inbox=True)

        messages = mailbox.get_inbox_messages()
        assert len(messages) == 1
        assert messages[0].priority == MessagePriority.URGENT
        assert messages[0].awaiting_response is True


class TestMailboxIsolation:
    """Tests for workflow isolation - consolidated from 2 tests to 1."""

    def test_different_workflows_are_isolated(self, tmp_path, message_factory):
        """Test that different workflows have isolated mailboxes."""
        mailbox1 = Mailbox(workflow_id="workflow-1", base_dir=tmp_path)
        mailbox2 = Mailbox(workflow_id="workflow-2", base_dir=tmp_path)

        # Send to each
        msg1 = message_factory(subject="Workflow 1", body="Body 1")
        msg2 = message_factory(
            from_agent="agent-2", subject="Workflow 2", body="Body 2"
        )
        mailbox1.send_message(msg1, to_inbox=True)
        mailbox2.send_message(msg2, to_inbox=True)

        # Each should only see their own
        assert mailbox1.get_unread_count() == 1
        assert mailbox2.get_unread_count() == 1
        assert mailbox1.get_inbox_messages()[0].subject == "Workflow 1"
        assert mailbox2.get_inbox_messages()[0].subject == "Workflow 2"

        # Same workflow with different instances should share
        mailbox1_copy = Mailbox(workflow_id="workflow-1", base_dir=tmp_path)
        assert mailbox1_copy.get_unread_count() == 1


class TestMailboxErrorHandling:
    """Tests for error handling - consolidated from 3 tests to 1."""

    def test_mailbox_handles_corrupted_files_gracefully(self, tmp_path):
        """Test that Mailbox handles corrupted files gracefully."""
        mailbox = Mailbox(workflow_id="test-workflow", base_dir=tmp_path)

        # Create corrupted files
        mailbox.paths.ensure_mailbox_dir()
        mailbox.paths.inbox_path.write_text("not valid json\n")
        mailbox.paths.outbox_path.write_text("not valid json\n")
        mailbox.paths.inbox_count_path.write_text("not valid json")

        # Should return empty/zero, not crash
        assert mailbox.get_inbox_messages() == []
        assert mailbox.get_outbox_messages() == []
        assert mailbox.get_unread_count() == 0


class TestMailboxEdgeCases:
    """Tests for edge cases - consolidated from 3 tests to 1."""

    def test_edge_case_behaviors(self, tmp_path, message_factory):
        """Test edge case behaviors in one test."""
        mailbox = Mailbox(workflow_id="test-workflow", base_dir=tmp_path)

        # Send 2 messages
        for i in range(2):
            msg = message_factory(
                from_agent=f"agent-{i}", to_agent="me",
                subject=f"Message {i}", body=f"Body {i}"
            )
            mailbox.send_message(msg, to_inbox=True)

        # Mark more as read than available - should go to 0
        mailbox.mark_as_read(count=10)
        assert mailbox.get_unread_count() == 0

        # Mark 0 as read - should not change
        mailbox2 = Mailbox(workflow_id="test-workflow-2", base_dir=tmp_path)
        for i in range(3):
            msg = message_factory(
                from_agent=f"agent-{i}", to_agent="me",
                subject=f"Message {i}", body=f"Body {i}"
            )
            mailbox2.send_message(msg, to_inbox=True)
        mailbox2.mark_as_read(count=0)
        assert mailbox2.get_unread_count() == 3

    def test_very_long_message(self, tmp_path):
        """Test mailbox with very long message."""
        mailbox = Mailbox(workflow_id="test-workflow", base_dir=tmp_path)

        # Very long body - edge case, keep inline for clarity
        long_body = "A" * 100000  # 100KB message
        msg = Message(
            from_agent="agent-1", to_agent="agent-2", type="test",
            subject="Long message", body=long_body
        )
        mailbox.send_message(msg, to_inbox=True)

        messages = mailbox.get_inbox_messages()
        assert len(messages) == 1
        assert len(messages[0].body) == 100000
