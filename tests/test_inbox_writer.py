# ABOUTME: Tests for InboxWriter that writes Message objects to INBOX directories
# ABOUTME: Consolidated test suite covering InboxWriter functionality with proper fixtures usage

"""Tests for InboxWriter.

Following the project's testing patterns with consolidated test coverage,
proper fixture usage, and comprehensive testing of message writing to inbox directories.
"""

import json
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from jean_claude.core.message import Message, MessagePriority
from jean_claude.core.inbox_writer import InboxWriter


class TestInboxWriterCreation:
    """Test InboxWriter instantiation and basic functionality."""

    def test_inbox_writer_creation_with_workflow_dir(self, tmp_path):
        """Test creating InboxWriter with workflow directory."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()

        writer = InboxWriter(workflow_dir)
        assert isinstance(writer, InboxWriter)
        assert writer.workflow_dir == workflow_dir

    def test_inbox_writer_creation_with_string_path(self, tmp_path):
        """Test creating InboxWriter with string workflow directory."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()

        writer = InboxWriter(str(workflow_dir))
        assert isinstance(writer, InboxWriter)
        assert writer.workflow_dir == Path(str(workflow_dir))  # Should convert to Path

    def test_inbox_writer_has_write_to_inbox_method(self, tmp_path):
        """Test that InboxWriter has the required write_to_inbox method."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        writer = InboxWriter(workflow_dir)

        assert hasattr(writer, 'write_to_inbox')
        assert callable(getattr(writer, 'write_to_inbox'))


class TestInboxWriterFunctionality:
    """Test InboxWriter message writing functionality."""

    def test_write_to_inbox_creates_inbox_directory_and_writes_message(self, tmp_path, message_factory):
        """Test that write_to_inbox creates INBOX directory and writes message."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        writer = InboxWriter(workflow_dir)

        # Verify INBOX doesn't exist initially
        inbox_dir = workflow_dir / "INBOX"
        assert not inbox_dir.exists()

        # Write message
        message = message_factory(
            from_agent="agent-1",
            to_agent="coordinator",
            type="test_message",
            subject="Test Subject",
            body="Test message body"
        )

        writer.write_to_inbox(message)

        # Verify INBOX directory was created
        assert inbox_dir.exists()
        assert inbox_dir.is_dir()

        # Verify message file was created
        message_files = list(inbox_dir.glob("*.json"))
        assert len(message_files) == 1

        # Verify message content
        message_content = json.loads(message_files[0].read_text())
        assert message_content["from_agent"] == "agent-1"
        assert message_content["to_agent"] == "coordinator"
        assert message_content["subject"] == "Test Subject"
        assert message_content["body"] == "Test message body"

    def test_write_to_inbox_with_different_message_types_and_priorities(self, tmp_path, message_factory):
        """Test writing messages with different types, priorities and flags."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        writer = InboxWriter(workflow_dir)

        # Write messages with different priorities and flags
        test_cases = [
            {
                "type": "blocker_detected",
                "priority": MessagePriority.URGENT,
                "awaiting_response": True,
                "subject": "Test Failure Blocker"
            },
            {
                "type": "status_update",
                "priority": MessagePriority.NORMAL,
                "awaiting_response": False,
                "subject": "Progress Update"
            },
            {
                "type": "help_request",
                "priority": MessagePriority.URGENT,
                "awaiting_response": True,
                "subject": "Need Assistance"
            }
        ]

        for i, case in enumerate(test_cases):
            message = message_factory(
                from_agent=f"agent-{i}",
                to_agent="coordinator",
                type=case["type"],
                subject=case["subject"],
                body=f"Test body {i}",
                priority=case["priority"],
                awaiting_response=case["awaiting_response"]
            )
            writer.write_to_inbox(message)

        # Verify all messages were written
        inbox_dir = workflow_dir / "INBOX"
        message_files = list(inbox_dir.glob("*.json"))
        assert len(message_files) == 3

        # Read all messages and create lookup by type (UUID filenames don't preserve order)
        messages_by_type = {}
        for message_file in message_files:
            content = json.loads(message_file.read_text())
            messages_by_type[content["type"]] = content

        # Verify each expected message type exists with correct properties
        for case in test_cases:
            msg_type = case["type"]
            assert msg_type in messages_by_type, f"Message type {msg_type} not found in inbox"
            message = messages_by_type[msg_type]
            assert message["priority"] == case["priority"].value
            assert message["awaiting_response"] == case["awaiting_response"]

    def test_write_to_inbox_preserves_all_message_fields(self, tmp_path, message_factory):
        """Test that all message fields are preserved when writing to inbox."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        writer = InboxWriter(workflow_dir)

        # Create message with all fields set
        message = message_factory(
            id="test-message-123",
            from_agent="implementation-agent",
            to_agent="coordinator",
            type="blocker_detected",
            subject="Test Failure in Authentication Module",
            body="Tests failed in test_auth.py with 3 failures:\n- test_login_valid_user\n- test_login_invalid_password\n- test_logout_user",
            priority=MessagePriority.URGENT,
            awaiting_response=True
        )

        writer.write_to_inbox(message)

        # Read and verify all fields
        inbox_dir = workflow_dir / "INBOX"
        message_files = list(inbox_dir.glob("*.json"))
        assert len(message_files) == 1

        content = json.loads(message_files[0].read_text())
        assert content["id"] == "test-message-123"
        assert content["from_agent"] == "implementation-agent"
        assert content["to_agent"] == "coordinator"
        assert content["type"] == "blocker_detected"
        assert content["subject"] == "Test Failure in Authentication Module"
        assert "test_auth.py" in content["body"]
        assert content["priority"] == "urgent"
        assert content["awaiting_response"] is True
        assert "created_at" in content  # Should have timestamp


class TestInboxWriterValidation:
    """Test InboxWriter input validation and error handling."""

    def test_write_to_inbox_validates_message_type(self, tmp_path):
        """Test that write_to_inbox validates message is a Message object."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        writer = InboxWriter(workflow_dir)

        # Test with invalid message type
        with pytest.raises((TypeError, ValueError)):
            writer.write_to_inbox("not a message")

        with pytest.raises((TypeError, ValueError)):
            writer.write_to_inbox({"from_agent": "test"})

        with pytest.raises((TypeError, ValueError)):
            writer.write_to_inbox(None)

    def test_inbox_writer_creation_validates_workflow_dir(self, tmp_path):
        """Test that InboxWriter validates workflow directory."""
        # Test with None
        with pytest.raises((TypeError, ValueError)):
            InboxWriter(None)

        # Test with empty string
        with pytest.raises((TypeError, ValueError)):
            InboxWriter("")

        # Test with non-existent directory (should work - will create)
        non_existent = tmp_path / "does-not-exist"
        writer = InboxWriter(non_existent)
        assert writer.workflow_dir == non_existent

    def test_write_to_inbox_handles_directory_creation_errors(self, tmp_path):
        """Test that write_to_inbox handles directory creation errors gracefully."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        writer = InboxWriter(workflow_dir)

        # Mock MailboxDirectoryManager.ensure_directories to raise error
        with patch('jean_claude.core.inbox_writer.MailboxDirectoryManager.ensure_directories') as mock_ensure:
            mock_ensure.side_effect = PermissionError("Permission denied")

            message = Message(
                from_agent="agent-1",
                to_agent="coordinator",
                type="test",
                subject="Test",
                body="Test body"
            )

            with pytest.raises(PermissionError):
                writer.write_to_inbox(message)


class TestInboxWriterIntegration:
    """Integration tests for InboxWriter with realistic scenarios."""

    def test_inbox_writer_workflow_blocker_scenario(self, tmp_path, message_factory):
        """Test complete workflow from blocker detection to inbox writing."""
        workflow_dir = tmp_path / "implementation-workflow"
        workflow_dir.mkdir()
        writer = InboxWriter(workflow_dir)

        # Simulate test failure blocker message
        blocker_message = message_factory(
            from_agent="implementation-agent",
            to_agent="coordinator",
            type="blocker_detected",
            subject="Test Failure: Authentication Module",
            body="Test failures detected during authentication module implementation:\n\n" +
                 "Failed Tests:\n" +
                 "- test_auth.py::test_login_valid_user\n" +
                 "- test_auth.py::test_login_invalid_password\n" +
                 "- test_auth.py::test_logout_user\n\n" +
                 "Error Summary: AssertionError: Expected True but got False\n\n" +
                 "Suggested Actions:\n" +
                 "- Review authentication logic in src/auth.py\n" +
                 "- Check test data setup in conftest.py\n" +
                 "- Verify database connection in test environment",
            priority=MessagePriority.URGENT,
            awaiting_response=True
        )

        writer.write_to_inbox(blocker_message)

        # Verify message was written correctly
        inbox_dir = workflow_dir / "INBOX"
        assert inbox_dir.exists()

        message_files = list(inbox_dir.glob("*.json"))
        assert len(message_files) == 1

        content = json.loads(message_files[0].read_text())
        assert content["type"] == "blocker_detected"
        assert content["priority"] == "urgent"
        assert content["awaiting_response"] is True
        assert "authentication module" in content["body"].lower()
        assert "test_auth.py" in content["body"]
        assert "AssertionError" in content["body"]
        assert "Review authentication logic" in content["body"]

    def test_inbox_writer_multiple_messages_different_agents(self, tmp_path, message_factory):
        """Test writing multiple messages from different agents to same inbox."""
        workflow_dir = tmp_path / "coordinator-workflow"
        workflow_dir.mkdir()
        writer = InboxWriter(workflow_dir)

        # Multiple agents sending different types of messages
        messages = [
            message_factory(
                from_agent="planning-agent",
                to_agent="coordinator",
                type="clarification_needed",
                subject="Requirements Clarification",
                body="Need clarification on user authentication requirements",
                priority=MessagePriority.URGENT,
                awaiting_response=True
            ),
            message_factory(
                from_agent="implementation-agent",
                to_agent="coordinator",
                type="status_update",
                subject="Progress Update",
                body="Completed user registration module",
                priority=MessagePriority.NORMAL,
                awaiting_response=False
            ),
            message_factory(
                from_agent="test-agent",
                to_agent="coordinator",
                type="blocker_detected",
                subject="Test Environment Issue",
                body="Unable to connect to test database",
                priority=MessagePriority.URGENT,
                awaiting_response=True
            )
        ]

        # Write all messages
        for message in messages:
            writer.write_to_inbox(message)

        # Verify all messages are in inbox
        inbox_dir = workflow_dir / "INBOX"
        message_files = list(inbox_dir.glob("*.json"))
        assert len(message_files) == 3

        # Verify each message type is present
        agents_found = set()
        types_found = set()
        for message_file in message_files:
            content = json.loads(message_file.read_text())
            agents_found.add(content["from_agent"])
            types_found.add(content["type"])

        assert "planning-agent" in agents_found
        assert "implementation-agent" in agents_found
        assert "test-agent" in agents_found
        assert "clarification_needed" in types_found
        assert "status_update" in types_found
        assert "blocker_detected" in types_found

    def test_inbox_writer_idempotent_directory_creation(self, tmp_path, message_factory):
        """Test that InboxWriter can be used multiple times safely."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()

        # Create writer and write message
        writer = InboxWriter(workflow_dir)
        message1 = message_factory(subject="First message", body="First body")
        writer.write_to_inbox(message1)

        # Create another writer instance for same workflow
        writer2 = InboxWriter(workflow_dir)
        message2 = message_factory(subject="Second message", body="Second body")
        writer2.write_to_inbox(message2)

        # Verify both messages are present
        inbox_dir = workflow_dir / "INBOX"
        message_files = list(inbox_dir.glob("*.json"))
        assert len(message_files) == 2

        subjects = []
        for message_file in message_files:
            content = json.loads(message_file.read_text())
            subjects.append(content["subject"])

        assert "First message" in subjects
        assert "Second message" in subjects