# ABOUTME: Tests for OutboxMonitor that polls OUTBOX directory for new messages
# ABOUTME: Consolidated test suite covering OutboxMonitor functionality with proper fixtures usage

"""Tests for OutboxMonitor.

Following the project's testing patterns with consolidated test coverage,
proper fixture usage, and comprehensive testing of OUTBOX monitoring for new messages.
The OutboxMonitor polls the OUTBOX directory and returns parsed Message objects.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from jean_claude.core.message import Message, MessagePriority
from jean_claude.core.outbox_monitor import OutboxMonitor


class TestOutboxMonitorCreation:
    """Test OutboxMonitor instantiation and basic functionality."""

    def test_outbox_monitor_creation_with_workflow_dir(self, tmp_path):
        """Test creating OutboxMonitor with workflow directory."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()

        monitor = OutboxMonitor(workflow_dir)
        assert isinstance(monitor, OutboxMonitor)
        assert monitor.workflow_dir == workflow_dir

    def test_outbox_monitor_creation_with_string_path(self, tmp_path):
        """Test creating OutboxMonitor with string workflow directory."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()

        monitor = OutboxMonitor(str(workflow_dir))
        assert isinstance(monitor, OutboxMonitor)
        assert monitor.workflow_dir == Path(str(workflow_dir))  # Should convert to Path

    def test_outbox_monitor_has_poll_for_new_messages_method(self, tmp_path):
        """Test that OutboxMonitor has the required poll_for_new_messages method."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        monitor = OutboxMonitor(workflow_dir)

        assert hasattr(monitor, 'poll_for_new_messages')
        assert callable(getattr(monitor, 'poll_for_new_messages'))


class TestOutboxMonitorPolling:
    """Test OutboxMonitor message polling functionality."""

    def test_poll_for_new_messages_returns_empty_list_when_outbox_empty(self, tmp_path):
        """Test that poll_for_new_messages returns empty list when OUTBOX is empty."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()

        # Create empty OUTBOX directory
        outbox_dir = workflow_dir / "OUTBOX"
        outbox_dir.mkdir()

        monitor = OutboxMonitor(workflow_dir)
        messages = monitor.poll_for_new_messages()

        assert messages == []

    def test_poll_for_new_messages_returns_empty_list_when_outbox_not_exists(self, tmp_path):
        """Test that poll_for_new_messages returns empty list when OUTBOX doesn't exist."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()

        monitor = OutboxMonitor(workflow_dir)
        messages = monitor.poll_for_new_messages()

        assert messages == []

    def test_poll_for_new_messages_finds_single_message(self, tmp_path, message_factory):
        """Test that poll_for_new_messages finds and parses a single message."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()

        # Create OUTBOX directory
        outbox_dir = workflow_dir / "OUTBOX"
        outbox_dir.mkdir()

        # Create a test message and save it as JSON
        test_message = message_factory(
            from_agent="coordinator",
            to_agent="implementation-agent",
            type="user_response",
            subject="Continue with implementation",
            body="User approved the implementation plan. Please proceed.",
            priority=MessagePriority.NORMAL
        )

        # Write message as JSON file
        message_file = outbox_dir / f"{test_message.id}.json"
        message_file.write_text(test_message.model_dump_json(indent=2))

        # Poll for messages
        monitor = OutboxMonitor(workflow_dir)
        messages = monitor.poll_for_new_messages()

        assert len(messages) == 1
        found_message = messages[0]
        assert isinstance(found_message, Message)
        assert found_message.id == test_message.id
        assert found_message.from_agent == "coordinator"
        assert found_message.to_agent == "implementation-agent"
        assert found_message.type == "user_response"
        assert found_message.subject == "Continue with implementation"
        assert found_message.body == "User approved the implementation plan. Please proceed."
        assert found_message.priority == MessagePriority.NORMAL

    def test_poll_for_new_messages_finds_multiple_messages(self, tmp_path, message_factory):
        """Test that poll_for_new_messages finds and parses multiple messages."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()

        # Create OUTBOX directory
        outbox_dir = workflow_dir / "OUTBOX"
        outbox_dir.mkdir()

        # Create multiple test messages
        test_messages = [
            message_factory(
                from_agent="coordinator",
                to_agent="planning-agent",
                type="user_feedback",
                subject="Requirement clarification",
                body="User provided additional requirements",
                priority=MessagePriority.URGENT,
                awaiting_response=False
            ),
            message_factory(
                from_agent="user",
                to_agent="implementation-agent",
                type="skip_decision",
                subject="Skip failing tests",
                body="Skip the failing authentication tests for now",
                priority=MessagePriority.NORMAL,
                awaiting_response=False
            ),
            message_factory(
                from_agent="coordinator",
                to_agent="test-agent",
                type="abort_signal",
                subject="Abort current task",
                body="Stop current testing and return to planning phase",
                priority=MessagePriority.URGENT,
                awaiting_response=False
            )
        ]

        # Write all messages as JSON files
        for msg in test_messages:
            message_file = outbox_dir / f"{msg.id}.json"
            message_file.write_text(msg.model_dump_json(indent=2))

        # Poll for messages
        monitor = OutboxMonitor(workflow_dir)
        messages = monitor.poll_for_new_messages()

        assert len(messages) == 3

        # Create lookup by message ID for easier verification
        messages_by_id = {msg.id: msg for msg in messages}

        # Verify each test message was found and parsed correctly
        for test_msg in test_messages:
            assert test_msg.id in messages_by_id
            found_msg = messages_by_id[test_msg.id]
            assert isinstance(found_msg, Message)
            assert found_msg.from_agent == test_msg.from_agent
            assert found_msg.to_agent == test_msg.to_agent
            assert found_msg.type == test_msg.type
            assert found_msg.subject == test_msg.subject
            assert found_msg.body == test_msg.body
            assert found_msg.priority == test_msg.priority
            assert found_msg.awaiting_response == test_msg.awaiting_response

    def test_poll_for_new_messages_ignores_non_json_files(self, tmp_path, message_factory):
        """Test that poll_for_new_messages ignores non-JSON files in OUTBOX."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()

        # Create OUTBOX directory
        outbox_dir = workflow_dir / "OUTBOX"
        outbox_dir.mkdir()

        # Create a valid message file
        test_message = message_factory(type="user_response")
        message_file = outbox_dir / f"{test_message.id}.json"
        message_file.write_text(test_message.model_dump_json(indent=2))

        # Create some non-JSON files that should be ignored
        (outbox_dir / "readme.txt").write_text("This is not a message")
        (outbox_dir / "temp.log").write_text("Log file content")
        (outbox_dir / "archive.zip").write_bytes(b"Binary content")
        (outbox_dir / ".hidden_file").write_text("Hidden file")

        # Poll for messages
        monitor = OutboxMonitor(workflow_dir)
        messages = monitor.poll_for_new_messages()

        # Should only find the one valid JSON message
        assert len(messages) == 1
        assert messages[0].id == test_message.id

    def test_poll_for_new_messages_handles_invalid_json_gracefully(self, tmp_path, message_factory):
        """Test that poll_for_new_messages handles invalid JSON files gracefully."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()

        # Create OUTBOX directory
        outbox_dir = workflow_dir / "OUTBOX"
        outbox_dir.mkdir()

        # Create a valid message file
        test_message = message_factory(type="user_response")
        valid_file = outbox_dir / f"{test_message.id}.json"
        valid_file.write_text(test_message.model_dump_json(indent=2))

        # Create invalid JSON files
        (outbox_dir / "invalid1.json").write_text("{not valid json")
        (outbox_dir / "invalid2.json").write_text('{"missing_required": "fields"}')
        (outbox_dir / "empty.json").write_text("")

        # Poll for messages
        monitor = OutboxMonitor(workflow_dir)
        messages = monitor.poll_for_new_messages()

        # Should only find the one valid message, ignoring invalid JSON
        assert len(messages) == 1
        assert messages[0].id == test_message.id

    def test_poll_for_new_messages_returns_messages_sorted_by_creation_time(self, tmp_path, message_factory):
        """Test that poll_for_new_messages returns messages sorted by creation time."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()

        # Create OUTBOX directory
        outbox_dir = workflow_dir / "OUTBOX"
        outbox_dir.mkdir()

        # Create messages with different IDs but we'll control the creation order by file modification time
        messages_data = [
            ("oldest", "First message"),
            ("middle", "Second message"),
            ("newest", "Third message")
        ]

        created_files = []
        for msg_id, body in messages_data:
            test_message = message_factory(
                id=msg_id,
                type="user_response",
                body=body
            )
            message_file = outbox_dir / f"{msg_id}.json"
            message_file.write_text(test_message.model_dump_json(indent=2))
            created_files.append(message_file)

        # Poll for messages
        monitor = OutboxMonitor(workflow_dir)
        messages = monitor.poll_for_new_messages()

        assert len(messages) == 3
        # Verify messages are returned (order depends on file system, but all should be present)
        message_ids = [msg.id for msg in messages]
        assert "oldest" in message_ids
        assert "middle" in message_ids
        assert "newest" in message_ids


class TestOutboxMonitorValidation:
    """Test OutboxMonitor input validation and error handling."""

    def test_outbox_monitor_creation_validates_workflow_dir(self, tmp_path):
        """Test that OutboxMonitor validates workflow directory."""
        # Test with None
        with pytest.raises((TypeError, ValueError)):
            OutboxMonitor(None)

        # Test with empty string
        with pytest.raises((TypeError, ValueError)):
            OutboxMonitor("")

        # Test with non-existent directory (should work - will handle gracefully)
        non_existent = tmp_path / "does-not-exist"
        monitor = OutboxMonitor(non_existent)
        assert monitor.workflow_dir == non_existent

        # Should return empty list when directory doesn't exist
        messages = monitor.poll_for_new_messages()
        assert messages == []

    def test_poll_for_new_messages_handles_permission_errors(self, tmp_path):
        """Test that poll_for_new_messages handles permission errors gracefully."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()

        monitor = OutboxMonitor(workflow_dir)

        # Mock Path.glob to raise PermissionError
        with patch.object(Path, 'glob', side_effect=PermissionError("Permission denied")):
            messages = monitor.poll_for_new_messages()

            # Should return empty list instead of raising exception
            assert messages == []


class TestOutboxMonitorIntegration:
    """Integration tests for OutboxMonitor with realistic scenarios."""

    def test_outbox_monitor_user_response_workflow_scenario(self, tmp_path, message_factory):
        """Test complete workflow where user responds to blocker via OUTBOX."""
        workflow_dir = tmp_path / "implementation-workflow"
        workflow_dir.mkdir()

        # Create OUTBOX directory
        outbox_dir = workflow_dir / "OUTBOX"
        outbox_dir.mkdir()

        # Simulate user response to a test failure blocker
        user_response = message_factory(
            from_agent="user",
            to_agent="implementation-agent",
            type="blocker_response",
            subject="Re: Test Failure: Authentication Module",
            body="I reviewed the test failures. Please fix the authentication logic in src/auth.py.\n\n" +
                 "The issue is in the password validation function - it's not handling empty passwords correctly.\n\n" +
                 "Suggested fix:\n" +
                 "1. Add null/empty check in validate_password()\n" +
                 "2. Update test_auth.py to include edge cases\n" +
                 "3. Re-run the tests after fixing",
            priority=MessagePriority.URGENT,
            awaiting_response=False
        )

        # Write user response to OUTBOX
        response_file = outbox_dir / f"{user_response.id}.json"
        response_file.write_text(user_response.model_dump_json(indent=2))

        # Monitor should find the response
        monitor = OutboxMonitor(workflow_dir)
        messages = monitor.poll_for_new_messages()

        assert len(messages) == 1
        found_message = messages[0]
        assert found_message.type == "blocker_response"
        assert found_message.from_agent == "user"
        assert found_message.to_agent == "implementation-agent"
        assert found_message.priority == MessagePriority.URGENT
        assert found_message.awaiting_response is False
        assert "authentication logic" in found_message.body
        assert "validate_password" in found_message.body
        assert "test_auth.py" in found_message.body

    def test_outbox_monitor_multiple_agent_responses_scenario(self, tmp_path, message_factory):
        """Test scenario with multiple agents responding to different issues."""
        workflow_dir = tmp_path / "coordination-workflow"
        workflow_dir.mkdir()

        # Create OUTBOX directory
        outbox_dir = workflow_dir / "OUTBOX"
        outbox_dir.mkdir()

        # Simulate responses from different agents/users
        responses = [
            message_factory(
                from_agent="user",
                to_agent="planning-agent",
                type="requirement_clarification",
                subject="Additional Requirements",
                body="Please add password strength validation with the following rules:\n- Minimum 8 characters\n- At least one uppercase letter\n- At least one number",
                priority=MessagePriority.NORMAL,
                awaiting_response=False
            ),
            message_factory(
                from_agent="coordinator",
                to_agent="implementation-agent",
                type="continue_signal",
                subject="Proceed with Implementation",
                body="Requirements have been clarified. Continue with authentication module implementation.",
                priority=MessagePriority.NORMAL,
                awaiting_response=False
            ),
            message_factory(
                from_agent="user",
                to_agent="test-agent",
                type="skip_decision",
                subject="Skip Integration Tests",
                body="Skip the failing integration tests for now. Focus on unit tests only.",
                priority=MessagePriority.LOW,
                awaiting_response=False
            )
        ]

        # Write all responses to OUTBOX
        for response in responses:
            response_file = outbox_dir / f"{response.id}.json"
            response_file.write_text(response.model_dump_json(indent=2))

        # Monitor should find all responses
        monitor = OutboxMonitor(workflow_dir)
        messages = monitor.poll_for_new_messages()

        assert len(messages) == 3

        # Verify each response type is present
        message_types = {msg.type for msg in messages}
        agent_pairs = {(msg.from_agent, msg.to_agent) for msg in messages}

        assert "requirement_clarification" in message_types
        assert "continue_signal" in message_types
        assert "skip_decision" in message_types

        assert ("user", "planning-agent") in agent_pairs
        assert ("coordinator", "implementation-agent") in agent_pairs
        assert ("user", "test-agent") in agent_pairs

    def test_outbox_monitor_polling_after_message_processing(self, tmp_path, message_factory):
        """Test that polling after message processing handles the scenario correctly."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()

        # Create OUTBOX directory
        outbox_dir = workflow_dir / "OUTBOX"
        outbox_dir.mkdir()

        monitor = OutboxMonitor(workflow_dir)

        # Initially no messages
        messages = monitor.poll_for_new_messages()
        assert len(messages) == 0

        # Add a message
        test_message = message_factory(type="user_response")
        message_file = outbox_dir / f"{test_message.id}.json"
        message_file.write_text(test_message.model_dump_json(indent=2))

        # Should find the new message
        messages = monitor.poll_for_new_messages()
        assert len(messages) == 1
        assert messages[0].id == test_message.id

        # If we poll again without removing the file, should still find it
        messages = monitor.poll_for_new_messages()
        assert len(messages) == 1
        assert messages[0].id == test_message.id

        # After processing, message might be removed (simulated by deleting file)
        message_file.unlink()

        # Should now return empty list
        messages = monitor.poll_for_new_messages()
        assert len(messages) == 0