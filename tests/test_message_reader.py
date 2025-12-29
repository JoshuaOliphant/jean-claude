"""Tests for message_reader module."""

import json
import pytest
from pathlib import Path
from datetime import datetime

from jean_claude.core.message_reader import read_messages
from jean_claude.core.message import Message, MessagePriority
from jean_claude.core.message_writer import MessageBox
from jean_claude.core.mailbox_paths import MailboxPaths


class TestReadMessages:
    """Test cases for read_messages function."""

    def test_read_messages_from_inbox(self, tmp_path):
        """Test reading messages from inbox.jsonl file."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)
        paths.inbox_path.parent.mkdir(parents=True, exist_ok=True)

        # Create test messages
        messages_data = [
            {
                "id": "msg-1",
                "from_agent": "agent-a",
                "to_agent": "agent-b",
                "type": "request",
                "subject": "Test message 1",
                "body": "This is a test message",
                "priority": "normal",
                "created_at": datetime.now().isoformat(),
                "awaiting_response": True
            },
            {
                "id": "msg-2",
                "from_agent": "agent-c",
                "to_agent": "agent-b",
                "type": "notification",
                "subject": "Test message 2",
                "body": "Another test message",
                "priority": "urgent",
                "created_at": datetime.now().isoformat(),
                "awaiting_response": False
            }
        ]

        # Write messages to inbox
        with open(paths.inbox_path, 'w', encoding='utf-8') as f:
            for msg_data in messages_data:
                f.write(json.dumps(msg_data) + '\n')

        # Act
        messages = read_messages(MessageBox.INBOX, paths)

        # Assert
        assert len(messages) == 2
        assert all(isinstance(msg, Message) for msg in messages)
        assert messages[0].id == "msg-1"
        assert messages[0].from_agent == "agent-a"
        assert messages[1].id == "msg-2"
        assert messages[1].priority == MessagePriority.URGENT

    def test_read_messages_from_outbox(self, tmp_path):
        """Test reading messages from outbox.jsonl file."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)
        paths.outbox_path.parent.mkdir(parents=True, exist_ok=True)

        message_data = {
            "id": "msg-out-1",
            "from_agent": "agent-b",
            "to_agent": "agent-a",
            "type": "response",
            "subject": "Outbox message",
            "body": "Response message",
            "priority": "normal",
            "created_at": datetime.now().isoformat(),
            "awaiting_response": False
        }

        # Write message to outbox
        with open(paths.outbox_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(message_data) + '\n')

        # Act
        messages = read_messages(MessageBox.OUTBOX, paths)

        # Assert
        assert len(messages) == 1
        assert messages[0].id == "msg-out-1"
        assert messages[0].to_agent == "agent-a"

    def test_read_messages_returns_empty_list_when_file_missing(self, tmp_path):
        """Test that read_messages returns empty list when file doesn't exist."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Act
        messages = read_messages(MessageBox.INBOX, paths)

        # Assert
        assert messages == []
        assert isinstance(messages, list)

    def test_read_messages_skips_invalid_json_lines(self, tmp_path):
        """Test that invalid JSON lines are silently skipped."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)
        paths.inbox_path.parent.mkdir(parents=True, exist_ok=True)

        valid_message = {
            "id": "msg-valid",
            "from_agent": "agent-a",
            "to_agent": "agent-b",
            "type": "request",
            "subject": "Valid message",
            "body": "This is valid",
            "priority": "normal",
            "created_at": datetime.now().isoformat(),
            "awaiting_response": False
        }

        # Write valid and invalid JSON
        with open(paths.inbox_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(valid_message) + '\n')
            f.write('{ invalid json }\n')  # Invalid JSON
            f.write('not json at all\n')  # Invalid JSON

        # Act
        messages = read_messages(MessageBox.INBOX, paths)

        # Assert
        assert len(messages) == 1
        assert messages[0].id == "msg-valid"

    def test_read_messages_skips_invalid_message_data(self, tmp_path):
        """Test that lines with invalid message data are silently skipped."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)
        paths.inbox_path.parent.mkdir(parents=True, exist_ok=True)

        valid_message = {
            "id": "msg-valid",
            "from_agent": "agent-a",
            "to_agent": "agent-b",
            "type": "request",
            "subject": "Valid message",
            "body": "This is valid",
            "priority": "normal",
            "created_at": datetime.now().isoformat(),
            "awaiting_response": False
        }

        invalid_message = {
            "id": "msg-invalid",
            # Missing required fields like from_agent, to_agent, etc.
        }

        # Write valid and invalid messages
        with open(paths.inbox_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(valid_message) + '\n')
            f.write(json.dumps(invalid_message) + '\n')  # Invalid message structure

        # Act
        messages = read_messages(MessageBox.INBOX, paths)

        # Assert
        assert len(messages) == 1
        assert messages[0].id == "msg-valid"

    def test_read_messages_skips_empty_lines(self, tmp_path):
        """Test that empty lines are skipped."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)
        paths.inbox_path.parent.mkdir(parents=True, exist_ok=True)

        message1 = {
            "id": "msg-1",
            "from_agent": "agent-a",
            "to_agent": "agent-b",
            "type": "request",
            "subject": "Message 1",
            "body": "First message",
            "priority": "normal",
            "created_at": datetime.now().isoformat(),
            "awaiting_response": False
        }

        message2 = {
            "id": "msg-2",
            "from_agent": "agent-c",
            "to_agent": "agent-d",
            "type": "notification",
            "subject": "Message 2",
            "body": "Second message",
            "priority": "low",
            "created_at": datetime.now().isoformat(),
            "awaiting_response": False
        }

        # Write messages with empty lines
        with open(paths.inbox_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(message1) + '\n')
            f.write('\n')  # Empty line
            f.write('   \n')  # Whitespace only
            f.write(json.dumps(message2) + '\n')
            f.write('\n')  # Empty line at end

        # Act
        messages = read_messages(MessageBox.INBOX, paths)

        # Assert
        assert len(messages) == 2
        assert messages[0].id == "msg-1"
        assert messages[1].id == "msg-2"

    def test_read_messages_handles_io_errors_gracefully(self, tmp_path):
        """Test that IO errors are handled gracefully by returning empty list."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)
        paths.inbox_path.parent.mkdir(parents=True, exist_ok=True)

        # Create a file
        paths.inbox_path.touch()

        # Make it unreadable (permission error)
        paths.inbox_path.chmod(0o000)

        # Act
        try:
            messages = read_messages(MessageBox.INBOX, paths)

            # Assert
            assert messages == []
        finally:
            # Restore permissions for cleanup
            paths.inbox_path.chmod(0o644)

    def test_read_messages_with_invalid_mailbox_type_raises_valueerror(self, tmp_path):
        """Test that passing invalid mailbox type raises ValueError."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            read_messages("inbox", paths)  # String instead of enum

        assert "mailbox must be a MessageBox enum value" in str(exc_info.value)

    def test_read_messages_with_none_mailbox_raises_valueerror(self, tmp_path):
        """Test that passing None as mailbox raises ValueError."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            read_messages(None, paths)

        assert "mailbox must be a MessageBox enum value" in str(exc_info.value)

    def test_read_messages_with_none_paths_raises_typeerror(self):
        """Test that passing None as paths raises TypeError."""
        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            read_messages(MessageBox.INBOX, None)

        assert "paths cannot be None" in str(exc_info.value)

    def test_read_messages_with_integer_mailbox_raises_valueerror(self, tmp_path):
        """Test that passing integer as mailbox raises ValueError."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            read_messages(123, paths)

        assert "mailbox must be a MessageBox enum value" in str(exc_info.value)

    def test_read_messages_returns_list_of_message_objects(self, tmp_path):
        """Test that read_messages returns a list of Message objects."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)
        paths.inbox_path.parent.mkdir(parents=True, exist_ok=True)

        message_data = {
            "id": "msg-1",
            "from_agent": "agent-a",
            "to_agent": "agent-b",
            "type": "request",
            "subject": "Test",
            "body": "Test body",
            "priority": "normal",
            "created_at": datetime.now().isoformat(),
            "awaiting_response": False
        }

        with open(paths.inbox_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(message_data) + '\n')

        # Act
        messages = read_messages(MessageBox.INBOX, paths)

        # Assert
        assert isinstance(messages, list)
        assert len(messages) == 1
        assert isinstance(messages[0], Message)

    def test_read_messages_with_empty_file(self, tmp_path):
        """Test reading an empty file returns empty list."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)
        paths.inbox_path.parent.mkdir(parents=True, exist_ok=True)
        paths.inbox_path.touch()  # Create empty file

        # Act
        messages = read_messages(MessageBox.INBOX, paths)

        # Assert
        assert messages == []

    def test_read_messages_preserves_message_priority(self, tmp_path):
        """Test that message priority is correctly preserved."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)
        paths.inbox_path.parent.mkdir(parents=True, exist_ok=True)

        messages_data = [
            {
                "id": "msg-urgent",
                "from_agent": "agent-a",
                "to_agent": "agent-b",
                "type": "request",
                "subject": "Urgent",
                "body": "Urgent message",
                "priority": "urgent",
                "created_at": datetime.now().isoformat(),
                "awaiting_response": True
            },
            {
                "id": "msg-normal",
                "from_agent": "agent-a",
                "to_agent": "agent-b",
                "type": "request",
                "subject": "Normal",
                "body": "Normal message",
                "priority": "normal",
                "created_at": datetime.now().isoformat(),
                "awaiting_response": False
            },
            {
                "id": "msg-low",
                "from_agent": "agent-a",
                "to_agent": "agent-b",
                "type": "request",
                "subject": "Low",
                "body": "Low priority message",
                "priority": "low",
                "created_at": datetime.now().isoformat(),
                "awaiting_response": False
            }
        ]

        with open(paths.inbox_path, 'w', encoding='utf-8') as f:
            for msg_data in messages_data:
                f.write(json.dumps(msg_data) + '\n')

        # Act
        messages = read_messages(MessageBox.INBOX, paths)

        # Assert
        assert len(messages) == 3
        assert messages[0].priority == MessagePriority.URGENT
        assert messages[1].priority == MessagePriority.NORMAL
        assert messages[2].priority == MessagePriority.LOW

    def test_read_messages_uses_resolve_mailbox_path(self, tmp_path, monkeypatch):
        """Test that read_messages uses resolve_mailbox_path utility."""
        # Arrange
        from jean_claude.core import mailbox_storage

        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)
        paths.inbox_path.parent.mkdir(parents=True, exist_ok=True)

        # Track if resolve_mailbox_path was called
        resolve_called = []
        original_resolve = mailbox_storage.resolve_mailbox_path

        def mock_resolve(mailbox, paths):
            resolve_called.append((mailbox, paths))
            return original_resolve(mailbox, paths)

        monkeypatch.setattr(mailbox_storage, 'resolve_mailbox_path', mock_resolve)

        # Act
        messages = read_messages(MessageBox.INBOX, paths)

        # Assert - verify resolve_mailbox_path was called
        assert len(resolve_called) == 1
        assert resolve_called[0][0] == MessageBox.INBOX
        assert resolve_called[0][1] == paths
