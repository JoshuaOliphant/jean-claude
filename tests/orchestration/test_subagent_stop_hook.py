# ABOUTME: Test suite for SubagentStop hook callback
# ABOUTME: Tests hook that checks outbox for urgent/awaiting_response messages and notifies orchestrator

"""Tests for SubagentStop hook functionality."""

import pytest

from jean_claude.core.message import MessagePriority
from jean_claude.core.mailbox_api import Mailbox
from jean_claude.orchestration.subagent_stop_hook import subagent_stop_hook


class TestSubagentStopHookBasics:
    """Tests for basic SubagentStop hook functionality."""

    @pytest.mark.asyncio
    async def test_hook_returns_none_when_no_messages(self, tmp_path):
        """Test that hook returns None when outbox is empty."""
        workflow_id = "test-workflow"

        # Create context with workflow_id
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await subagent_stop_hook(hook_context=context)

        # Should return None (no notification needed)
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_returns_none_when_only_normal_messages(self, tmp_path, message_factory):
        """Test that hook returns None when outbox has only normal priority messages."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send a normal priority message
        msg = message_factory(
            to_agent="coordinator", type="status",
            subject="Status update", body="Work is progressing",
            priority=MessagePriority.NORMAL
        )
        mailbox.send_message(msg, to_inbox=False)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await subagent_stop_hook(hook_context=context)

        # Should return None (no urgent messages)
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_returns_none_when_messages_not_awaiting_response(self, tmp_path, message_factory):
        """Test that hook returns None when messages are not awaiting response."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send a message that's not awaiting response
        msg = message_factory(
            to_agent="coordinator",
            type="notification",
            subject="FYI",
            body="Just letting you know",
            awaiting_response=False
        )
        mailbox.send_message(msg, to_inbox=False)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await subagent_stop_hook(hook_context=context)

        # Should return None (not awaiting response)
        assert result is None


class TestSubagentStopHookUrgentMessages:
    """Tests for SubagentStop hook with urgent messages."""

    @pytest.mark.asyncio
    async def test_hook_notifies_on_urgent_message(self, tmp_path, message_factory):
        """Test that hook returns systemMessage for urgent messages."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send an urgent message
        msg = message_factory(
            to_agent="coordinator",
            type="help_request",
            subject="Need help",
            body="I'm stuck on a problem",
            priority=MessagePriority.URGENT
        )
        mailbox.send_message(msg, to_inbox=False)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await subagent_stop_hook(hook_context=context)

        # Should return a system message notification
        assert result is not None
        assert "systemMessage" in result
        assert "urgent" in result["systemMessage"].lower()
        assert "Need help" in result["systemMessage"]

    @pytest.mark.asyncio
    async def test_hook_notifies_on_awaiting_response_message(self, tmp_path, message_factory):
        """Test that hook returns systemMessage for messages awaiting response."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send a message awaiting response
        msg = message_factory(
            to_agent="coordinator",
            type="question",
            subject="Question about approach",
            body="Should I use approach A or B?",
            awaiting_response=True
        )
        mailbox.send_message(msg, to_inbox=False)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await subagent_stop_hook(hook_context=context)

        # Should return a system message notification
        assert result is not None
        assert "systemMessage" in result
        assert "awaiting response" in result["systemMessage"].lower()
        assert "Question about approach" in result["systemMessage"]

    @pytest.mark.asyncio
    async def test_hook_notifies_on_urgent_and_awaiting_response(self, tmp_path, message_factory):
        """Test that hook handles messages that are both urgent AND awaiting response."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send a message that's both urgent and awaiting response
        msg = message_factory(
            to_agent="coordinator",
            type="help_request",
            subject="Urgent question",
            body="Need immediate guidance",
            priority=MessagePriority.URGENT,
            awaiting_response=True
        )
        mailbox.send_message(msg, to_inbox=False)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await subagent_stop_hook(hook_context=context)

        # Should return a system message notification
        assert result is not None
        assert "systemMessage" in result
        # Should mention both urgent and awaiting response
        msg_lower = result["systemMessage"].lower()
        assert "urgent" in msg_lower or "awaiting response" in msg_lower

    @pytest.mark.asyncio
    async def test_hook_includes_message_details(self, tmp_path, message_factory):
        """Test that hook includes relevant message details in notification."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send an urgent message
        msg = message_factory(
            from_agent="subagent-x",
            to_agent="coordinator",
            type="help_request",
            subject="Critical issue",
            body="The database connection failed",
            priority=MessagePriority.URGENT
        )
        mailbox.send_message(msg, to_inbox=False)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await subagent_stop_hook(hook_context=context)

        # Should include message details
        system_msg = result["systemMessage"]
        assert "Critical issue" in system_msg
        assert "The database connection failed" in system_msg


class TestSubagentStopHookMultipleMessages:
    """Tests for SubagentStop hook with multiple messages."""

    @pytest.mark.asyncio
    async def test_hook_handles_multiple_urgent_messages(self, tmp_path, message_factory):
        """Test that hook handles multiple urgent messages."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send multiple urgent messages
        for i in range(3):
            msg = message_factory(
                to_agent="coordinator",
                type="help_request",
                subject=f"Issue {i}",
                body=f"Problem {i}",
                priority=MessagePriority.URGENT
            )
            mailbox.send_message(msg, to_inbox=False)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await subagent_stop_hook(hook_context=context)

        # Should return notification mentioning multiple messages
        assert result is not None
        assert "systemMessage" in result
        # Should mention count or list of messages
        system_msg = result["systemMessage"]
        assert "Issue 0" in system_msg or "Issue 1" in system_msg or "Issue 2" in system_msg

    @pytest.mark.asyncio
    async def test_hook_ignores_normal_messages_when_urgent_present(self, tmp_path, message_factory):
        """Test that hook focuses on urgent/awaiting messages when mixed."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send normal messages
        for i in range(3):
            msg = message_factory(
                to_agent="coordinator",
                type="status",
                subject=f"Status {i}",
                body=f"Normal message {i}",
                priority=MessagePriority.NORMAL
            )
            mailbox.send_message(msg, to_inbox=False)

        # Send one urgent message
        urgent_msg = message_factory(
            to_agent="coordinator",
            type="help_request",
            subject="Urgent help",
            body="Need assistance",
            priority=MessagePriority.URGENT
        )
        mailbox.send_message(urgent_msg, to_inbox=False)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await subagent_stop_hook(hook_context=context)

        # Should notify about urgent message
        assert result is not None
        assert "Urgent help" in result["systemMessage"]
        # Should not mention normal status messages
        assert "Status 0" not in result["systemMessage"]


class TestSubagentStopHookErrorHandling:
    """Tests for error handling in SubagentStop hook."""

    @pytest.mark.asyncio
    async def test_hook_handles_missing_workflow_id_gracefully(self, tmp_path):
        """Test that hook handles missing workflow_id gracefully."""
        # Create context without workflow_id
        context = {"base_dir": tmp_path}

        # Call hook - should not crash
        result = await subagent_stop_hook(hook_context=context)

        # Should return None (graceful degradation)
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_handles_corrupted_outbox_gracefully(self, tmp_path):
        """Test that hook handles corrupted outbox files gracefully."""
        workflow_id = "test-workflow"

        # Create corrupted outbox manually
        from jean_claude.core.mailbox_paths import MailboxPaths
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)
        paths.ensure_mailbox_dir()
        paths.outbox_path.write_text("not valid json\n")

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook - should not crash
        result = await subagent_stop_hook(hook_context=context)

        # Should return None (graceful degradation)
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_handles_missing_base_dir_gracefully(self, tmp_path):
        """Test that hook handles missing base_dir in context."""
        workflow_id = "test-workflow"

        # Create context without base_dir (will use default)
        context = {"workflow_id": workflow_id}

        # Call hook - should not crash
        result = await subagent_stop_hook(hook_context=context)

        # Should return None or handle gracefully
        assert result is None or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_hook_handles_none_context_gracefully(self):
        """Test that hook handles None context gracefully."""
        # Call hook with None context
        result = await subagent_stop_hook(hook_context=None)

        # Should return None (graceful degradation)
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_handles_empty_context_gracefully(self):
        """Test that hook handles empty context gracefully."""
        # Call hook with empty context
        result = await subagent_stop_hook(hook_context={})

        # Should return None (graceful degradation)
        assert result is None


class TestSubagentStopHookIntegration:
    """Integration tests for SubagentStop hook."""

    @pytest.mark.asyncio
    async def test_hook_workflow_with_coordinator_workflow_id(self, tmp_path, message_factory):
        """Test hook with realistic coordinator workflow_id."""
        workflow_id = "beads-jean_claude-abc123"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Subagent sends urgent help request
        msg = message_factory(
            from_agent=workflow_id,
            to_agent="coordinator",
            type="help_request",
            subject="Need clarification",
            body="User requirements are ambiguous",
            priority=MessagePriority.URGENT,
            awaiting_response=True
        )
        mailbox.send_message(msg, to_inbox=False)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await subagent_stop_hook(hook_context=context)

        # Should notify coordinator
        assert result is not None
        assert "systemMessage" in result
        assert "Need clarification" in result["systemMessage"]
        assert "ambiguous" in result["systemMessage"]

    @pytest.mark.asyncio
    async def test_hook_notification_format(self, tmp_path, message_factory):
        """Test that notification has proper format for orchestrator."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send urgent message
        msg = message_factory(
            to_agent="coordinator",
            type="help_request",
            subject="Test subject",
            body="Test body",
            priority=MessagePriority.URGENT
        )
        mailbox.send_message(msg, to_inbox=False)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await subagent_stop_hook(hook_context=context)

        # Validate notification structure
        assert isinstance(result, dict)
        assert "systemMessage" in result
        assert isinstance(result["systemMessage"], str)
        assert len(result["systemMessage"]) > 0
