# ABOUTME: Test suite for UserPromptSubmit hook callback
# ABOUTME: Tests hook that reads unread inbox messages and injects them as additionalContext

"""Tests for UserPromptSubmit hook functionality."""

import pytest

from jean_claude.core.message import MessagePriority
from jean_claude.core.mailbox_api import Mailbox
from jean_claude.orchestration.user_prompt_submit_hook import user_prompt_submit_hook


class TestUserPromptSubmitHookBasics:
    """Tests for basic UserPromptSubmit hook functionality."""

    @pytest.mark.asyncio
    async def test_hook_returns_none_when_no_messages(self, tmp_path):
        """Test that hook returns None when inbox is empty."""
        workflow_id = "test-workflow"

        # Create context with workflow_id
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook with empty prompt
        result = await user_prompt_submit_hook(
            hook_context=context,
            user_prompt="Test prompt"
        )

        # Should return None (no messages to inject)
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_returns_none_when_unread_count_is_zero(self, tmp_path, message_factory):
        """Test that hook returns None when unread count is 0."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send a message to inbox
        msg = message_factory(
            from_agent="coordinator",
            to_agent="agent-1",
            type="response",
            subject="Reply",
            body="Here's the answer",
            priority=MessagePriority.NORMAL
        )
        mailbox.send_message(msg, to_inbox=True)

        # Mark all messages as read
        mailbox.mark_as_read()

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await user_prompt_submit_hook(
            hook_context=context,
            user_prompt="Test prompt"
        )

        # Should return None (no unread messages)
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_injects_unread_message_as_additional_context(self, tmp_path, message_factory):
        """Test that hook injects unread message as additionalContext."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send an unread message to inbox
        msg = message_factory(
            from_agent="coordinator",
            to_agent="agent-1",
            type="response",
            subject="Important update",
            body="Here's the information you need",
            priority=MessagePriority.NORMAL
        )
        mailbox.send_message(msg, to_inbox=True)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await user_prompt_submit_hook(
            hook_context=context,
            user_prompt="Test prompt"
        )

        # Should return additionalContext
        assert result is not None
        assert "additionalContext" in result
        assert "Important update" in result["additionalContext"]
        assert "Here's the information you need" in result["additionalContext"]


class TestUserPromptSubmitHookMessageFormatting:
    """Tests for message formatting in UserPromptSubmit hook."""

    @pytest.mark.asyncio
    async def test_hook_formats_message_with_priority(self, tmp_path, message_factory):
        """Test that hook includes priority in formatted message."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send an urgent message
        msg = message_factory(
            from_agent="coordinator",
            to_agent="agent-1",
            type="help",
            subject="Urgent issue",
            body="This needs immediate attention",
            priority=MessagePriority.URGENT
        )
        mailbox.send_message(msg, to_inbox=True)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await user_prompt_submit_hook(
            hook_context=context,
            user_prompt="Test prompt"
        )

        # Should include priority
        assert result is not None
        context_text = result["additionalContext"]
        assert "URGENT" in context_text or "urgent" in context_text.lower()

    @pytest.mark.asyncio
    async def test_hook_formats_message_with_subject_and_body(self, tmp_path, message_factory):
        """Test that hook includes both subject and body in formatted message."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send a message
        msg = message_factory(
            from_agent="coordinator",
            to_agent="agent-1",
            type="instruction",
            subject="Test Subject",
            body="Test Body Content",
            priority=MessagePriority.NORMAL
        )
        mailbox.send_message(msg, to_inbox=True)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await user_prompt_submit_hook(
            hook_context=context,
            user_prompt="Test prompt"
        )

        # Should include both subject and body
        assert result is not None
        context_text = result["additionalContext"]
        assert "Test Subject" in context_text
        assert "Test Body Content" in context_text

    @pytest.mark.asyncio
    async def test_hook_formats_multiple_messages_clearly(self, tmp_path, message_factory):
        """Test that hook formats multiple messages in a clear, readable way."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send multiple messages
        for i in range(3):
            msg = message_factory(
                from_agent="coordinator",
                to_agent="agent-1",
                type="info",
                subject=f"Message {i}",
                body=f"Body {i}",
                priority=MessagePriority.NORMAL if i % 2 == 0 else MessagePriority.URGENT
            )
            mailbox.send_message(msg, to_inbox=True)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await user_prompt_submit_hook(
            hook_context=context,
            user_prompt="Test prompt"
        )

        # Should include all messages
        assert result is not None
        context_text = result["additionalContext"]
        assert "Message 0" in context_text
        assert "Message 1" in context_text
        assert "Message 2" in context_text


class TestUserPromptSubmitHookInboxCountUpdate:
    """Tests for inbox count update after reading messages."""

    @pytest.mark.asyncio
    async def test_hook_updates_inbox_count_after_reading(self, tmp_path, message_factory):
        """Test that hook marks messages as read and updates inbox_count."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send messages to inbox
        for i in range(3):
            msg = message_factory(
                from_agent="coordinator",
                to_agent="agent-1",
                type="info",
                subject=f"Message {i}",
                body=f"Body {i}",
                priority=MessagePriority.NORMAL
            )
            mailbox.send_message(msg, to_inbox=True)

        # Verify unread count before hook
        assert mailbox.get_unread_count() == 3

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await user_prompt_submit_hook(
            hook_context=context,
            user_prompt="Test prompt"
        )

        # Should have injected messages
        assert result is not None

        # Verify unread count after hook is 0
        assert mailbox.get_unread_count() == 0

    @pytest.mark.asyncio
    async def test_hook_only_marks_unread_messages_as_read(self, tmp_path, message_factory):
        """Test that hook only affects unread messages."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send first batch and mark as read
        msg1 = message_factory(
            from_agent="coordinator",
            to_agent="agent-1",
            type="info",
            subject="Old message",
            body="Already read",
            priority=MessagePriority.NORMAL
        )
        mailbox.send_message(msg1, to_inbox=True)
        mailbox.mark_as_read()

        # Send new unread messages
        for i in range(2):
            msg = message_factory(
                from_agent="coordinator",
                to_agent="agent-1",
                type="info",
                subject=f"New message {i}",
                body=f"Unread {i}",
                priority=MessagePriority.NORMAL
            )
            mailbox.send_message(msg, to_inbox=True)

        # Verify unread count
        assert mailbox.get_unread_count() == 2

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await user_prompt_submit_hook(
            hook_context=context,
            user_prompt="Test prompt"
        )

        # Should have injected only the 2 new messages
        assert result is not None
        context_text = result["additionalContext"]
        assert "New message 0" in context_text
        assert "New message 1" in context_text

        # Unread count should now be 0
        assert mailbox.get_unread_count() == 0


class TestUserPromptSubmitHookUnreadMessageSelection:
    """Tests for selecting only unread messages."""

    @pytest.mark.asyncio
    async def test_hook_only_injects_unread_messages(self, tmp_path, message_factory):
        """Test that hook only injects unread messages, not all inbox messages."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send old messages (total 5)
        for i in range(5):
            msg = message_factory(
                from_agent="coordinator",
                to_agent="agent-1",
                type="info",
                subject=f"Old {i}",
                body=f"Old body {i}",
                priority=MessagePriority.NORMAL
            )
            mailbox.send_message(msg, to_inbox=True)

        # Mark first 3 as read (leaving 2 unread)
        mailbox.mark_as_read(count=3)

        # Verify unread count
        assert mailbox.get_unread_count() == 2

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await user_prompt_submit_hook(
            hook_context=context,
            user_prompt="Test prompt"
        )

        # Should inject only the last 2 unread messages
        assert result is not None
        context_text = result["additionalContext"]
        # The last 2 messages (indices 3 and 4) should be present
        assert "Old 3" in context_text
        assert "Old 4" in context_text
        # Earlier messages should not be present
        assert "Old 0" not in context_text
        assert "Old 1" not in context_text
        assert "Old 2" not in context_text


class TestUserPromptSubmitHookErrorHandling:
    """Tests for error handling in UserPromptSubmit hook."""

    @pytest.mark.asyncio
    async def test_hook_handles_missing_workflow_id_gracefully(self, tmp_path):
        """Test that hook handles missing workflow_id gracefully."""
        # Create context without workflow_id
        context = {"base_dir": tmp_path}

        # Call hook - should not crash
        result = await user_prompt_submit_hook(
            hook_context=context,
            user_prompt="Test prompt"
        )

        # Should return None (graceful degradation)
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_handles_corrupted_inbox_gracefully(self, tmp_path):
        """Test that hook handles corrupted inbox files gracefully."""
        workflow_id = "test-workflow"

        # Create corrupted inbox manually
        from jean_claude.core.mailbox_paths import MailboxPaths
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)
        paths.ensure_mailbox_dir()
        paths.inbox_path.write_text("not valid json\n")

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook - should not crash
        result = await user_prompt_submit_hook(
            hook_context=context,
            user_prompt="Test prompt"
        )

        # Should return None (graceful degradation)
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_handles_missing_base_dir_gracefully(self, tmp_path):
        """Test that hook handles missing base_dir in context."""
        workflow_id = "test-workflow"

        # Create context without base_dir (will use default)
        context = {"workflow_id": workflow_id}

        # Call hook - should not crash
        result = await user_prompt_submit_hook(
            hook_context=context,
            user_prompt="Test prompt"
        )

        # Should return None or handle gracefully
        assert result is None or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_hook_handles_none_context_gracefully(self):
        """Test that hook handles None context gracefully."""
        # Call hook with None context
        result = await user_prompt_submit_hook(
            hook_context=None,
            user_prompt="Test prompt"
        )

        # Should return None (graceful degradation)
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_handles_empty_context_gracefully(self):
        """Test that hook handles empty context gracefully."""
        # Call hook with empty context
        result = await user_prompt_submit_hook(
            hook_context={},
            user_prompt="Test prompt"
        )

        # Should return None (graceful degradation)
        assert result is None

    @pytest.mark.asyncio
    async def test_hook_handles_corrupted_inbox_count_gracefully(self, tmp_path, message_factory):
        """Test that hook handles corrupted inbox_count.json gracefully."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send a message
        msg = message_factory(
            from_agent="coordinator",
            to_agent="agent-1",
            type="info",
            subject="Test",
            body="Test body",
            priority=MessagePriority.NORMAL
        )
        mailbox.send_message(msg, to_inbox=True)

        # Corrupt inbox_count.json
        from jean_claude.core.mailbox_paths import MailboxPaths
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)
        paths.inbox_count_path.write_text("not valid json")

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook - should not crash
        result = await user_prompt_submit_hook(
            hook_context=context,
            user_prompt="Test prompt"
        )

        # Should handle gracefully (may return None or handle with default count)
        assert result is None or isinstance(result, dict)


class TestUserPromptSubmitHookIntegration:
    """Integration tests for UserPromptSubmit hook."""

    @pytest.mark.asyncio
    async def test_hook_workflow_with_realistic_workflow_id(self, tmp_path, message_factory):
        """Test hook with realistic beads workflow_id."""
        workflow_id = "beads-jean_claude-abc123"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Coordinator sends response to subagent
        msg = message_factory(
            from_agent="coordinator",
            to_agent=workflow_id,
            type="response",
            subject="Re: Need clarification",
            body="Use approach A because it's more maintainable",
            priority=MessagePriority.URGENT,
            awaiting_response=False
        )
        mailbox.send_message(msg, to_inbox=True)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await user_prompt_submit_hook(
            hook_context=context,
            user_prompt="Continue with the task"
        )

        # Should inject the response
        assert result is not None
        assert "additionalContext" in result
        assert "Re: Need clarification" in result["additionalContext"]
        assert "approach A" in result["additionalContext"]

        # Should mark as read
        assert mailbox.get_unread_count() == 0

    @pytest.mark.asyncio
    async def test_hook_context_format(self, tmp_path, message_factory):
        """Test that additionalContext has proper format."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send message
        msg = message_factory(
            from_agent="coordinator",
            to_agent="agent-1",
            type="response",
            subject="Answer to your question",
            body="Here's the detailed answer",
            priority=MessagePriority.NORMAL
        )
        mailbox.send_message(msg, to_inbox=True)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await user_prompt_submit_hook(
            hook_context=context,
            user_prompt="Test prompt"
        )

        # Validate structure
        assert isinstance(result, dict)
        assert "additionalContext" in result
        assert isinstance(result["additionalContext"], str)
        assert len(result["additionalContext"]) > 0

    @pytest.mark.asyncio
    async def test_hook_with_mixed_priority_messages(self, tmp_path, message_factory):
        """Test hook with messages of different priorities."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send messages with different priorities
        priorities = [MessagePriority.URGENT, MessagePriority.NORMAL, MessagePriority.LOW]
        for i, priority in enumerate(priorities):
            msg = message_factory(
                from_agent="coordinator",
                to_agent="agent-1",
                type="info",
                subject=f"{priority.value} message",
                body=f"Message with {priority.value} priority",
                priority=priority
            )
            mailbox.send_message(msg, to_inbox=True)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        # Call hook
        result = await user_prompt_submit_hook(
            hook_context=context,
            user_prompt="Test prompt"
        )

        # Should inject all messages
        assert result is not None
        context_text = result["additionalContext"]
        assert "urgent message" in context_text
        assert "normal message" in context_text
        assert "low message" in context_text

        # All should be marked as read
        assert mailbox.get_unread_count() == 0

    @pytest.mark.asyncio
    async def test_hook_preserves_user_prompt(self, tmp_path, message_factory):
        """Test that hook doesn't modify the original user prompt."""
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)

        # Send a message
        msg = message_factory(
            from_agent="coordinator",
            to_agent="agent-1",
            type="info",
            subject="Test",
            body="Test body",
            priority=MessagePriority.NORMAL
        )
        mailbox.send_message(msg, to_inbox=True)

        # Create context
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}

        original_prompt = "This is the user's original prompt"

        # Call hook
        result = await user_prompt_submit_hook(
            hook_context=context,
            user_prompt=original_prompt
        )

        # Hook should only add additionalContext, not modify prompt
        assert result is not None
        assert "additionalContext" in result
        # The result should not contain a modified prompt
        assert "prompt" not in result or result.get("prompt") == original_prompt
