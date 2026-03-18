# ABOUTME: Test suite for UserPromptSubmit hook callback
# ABOUTME: Tests hook that reads unread inbox messages and injects them as additionalContext

"""Tests for UserPromptSubmit hook functionality."""

import pytest

from jean_claude.core.message import MessagePriority
from jean_claude.core.mailbox_api import Mailbox
from jean_claude.orchestration.user_prompt_submit_hook import user_prompt_submit_hook


class TestUserPromptSubmitHookErrorHandling:
    """Tests for error handling in UserPromptSubmit hook."""

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


class TestUserPromptSubmitHookIntegration:
    """Integration tests for UserPromptSubmit hook."""

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
