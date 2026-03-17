# ABOUTME: Consolidated tests for SubagentStop and UserPromptSubmit hooks
# ABOUTME: Merges shared error handling patterns and keeps hook-specific behavior tests

"""Consolidated tests for SubagentStop and UserPromptSubmit hooks.

Both hooks share similar error handling patterns (missing context, corrupted files,
graceful degradation). Shared patterns are parametrized; hook-specific behavior
is tested individually.
"""

import pytest

from jean_claude.core.message import MessagePriority
from jean_claude.core.mailbox_api import Mailbox
from jean_claude.core.mailbox_paths import MailboxPaths
from jean_claude.orchestration.subagent_stop_hook import subagent_stop_hook
from jean_claude.orchestration.user_prompt_submit_hook import user_prompt_submit_hook


# ── Shared error handling (parametrized over both hooks) ─────────────────


async def _call_hook(hook_name, context):
    """Call the appropriate hook with the given context."""
    if hook_name == "subagent_stop":
        return await subagent_stop_hook(hook_context=context)
    else:
        return await user_prompt_submit_hook(hook_context=context, user_prompt="Test prompt")


@pytest.mark.parametrize("hook_name", ["subagent_stop", "user_prompt_submit"])
class TestHookSharedErrorHandling:
    """Error handling patterns shared by both hooks."""

    @pytest.mark.asyncio
    async def test_handles_missing_workflow_id_gracefully(self, tmp_path, hook_name):
        context = {"base_dir": tmp_path}
        result = await _call_hook(hook_name, context)
        assert result is None

    @pytest.mark.asyncio
    async def test_handles_missing_base_dir_gracefully(self, hook_name):
        context = {"workflow_id": "test-workflow"}
        result = await _call_hook(hook_name, context)
        assert result is None or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_handles_none_context_gracefully(self, hook_name):
        result = await _call_hook(hook_name, None)
        assert result is None

    @pytest.mark.asyncio
    async def test_handles_empty_context_gracefully(self, hook_name):
        result = await _call_hook(hook_name, {})
        assert result is None


# ── SubagentStop hook tests ──────────────────────────────────────────────


class TestSubagentStopHookBasics:
    """Tests for basic SubagentStop hook functionality."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_messages(self, tmp_path):
        context = {"workflow_id": "test-workflow", "base_dir": tmp_path}
        result = await subagent_stop_hook(hook_context=context)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_only_normal_messages(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg = message_factory(
            to_agent="coordinator", type="status",
            subject="Status update", body="Work is progressing",
            priority=MessagePriority.NORMAL
        )
        mailbox.send_message(msg, to_inbox=False)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await subagent_stop_hook(hook_context=context)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_not_awaiting_response(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg = message_factory(
            to_agent="coordinator", type="notification",
            subject="FYI", body="Just letting you know",
            awaiting_response=False
        )
        mailbox.send_message(msg, to_inbox=False)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await subagent_stop_hook(hook_context=context)
        assert result is None


class TestSubagentStopHookUrgentMessages:
    """Tests for SubagentStop hook with urgent/awaiting messages."""

    @pytest.mark.asyncio
    async def test_notifies_on_urgent_message(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg = message_factory(
            to_agent="coordinator", type="help_request",
            subject="Need help", body="I'm stuck on a problem",
            priority=MessagePriority.URGENT
        )
        mailbox.send_message(msg, to_inbox=False)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await subagent_stop_hook(hook_context=context)
        assert result is not None
        assert "systemMessage" in result
        assert "urgent" in result["systemMessage"].lower()
        assert "Need help" in result["systemMessage"]

    @pytest.mark.asyncio
    async def test_notifies_on_awaiting_response_message(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg = message_factory(
            to_agent="coordinator", type="question",
            subject="Question about approach", body="Should I use approach A or B?",
            awaiting_response=True
        )
        mailbox.send_message(msg, to_inbox=False)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await subagent_stop_hook(hook_context=context)
        assert result is not None
        assert "systemMessage" in result
        assert "awaiting response" in result["systemMessage"].lower()

    @pytest.mark.asyncio
    async def test_notifies_on_urgent_and_awaiting_response(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg = message_factory(
            to_agent="coordinator", type="help_request",
            subject="Urgent question", body="Need immediate guidance",
            priority=MessagePriority.URGENT, awaiting_response=True
        )
        mailbox.send_message(msg, to_inbox=False)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await subagent_stop_hook(hook_context=context)
        assert result is not None
        msg_lower = result["systemMessage"].lower()
        assert "urgent" in msg_lower or "awaiting response" in msg_lower

    @pytest.mark.asyncio
    async def test_includes_message_details(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg = message_factory(
            from_agent="subagent-x", to_agent="coordinator",
            type="help_request", subject="Critical issue",
            body="The database connection failed",
            priority=MessagePriority.URGENT
        )
        mailbox.send_message(msg, to_inbox=False)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await subagent_stop_hook(hook_context=context)
        system_msg = result["systemMessage"]
        assert "Critical issue" in system_msg
        assert "The database connection failed" in system_msg


class TestSubagentStopHookMultipleMessages:
    """Tests for SubagentStop hook with multiple messages."""

    @pytest.mark.asyncio
    async def test_handles_multiple_urgent_messages(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        for i in range(3):
            msg = message_factory(
                to_agent="coordinator", type="help_request",
                subject=f"Issue {i}", body=f"Problem {i}",
                priority=MessagePriority.URGENT
            )
            mailbox.send_message(msg, to_inbox=False)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await subagent_stop_hook(hook_context=context)
        assert result is not None
        system_msg = result["systemMessage"]
        assert "Issue 0" in system_msg or "Issue 1" in system_msg or "Issue 2" in system_msg

    @pytest.mark.asyncio
    async def test_ignores_normal_messages_when_urgent_present(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        for i in range(3):
            msg = message_factory(
                to_agent="coordinator", type="status",
                subject=f"Status {i}", body=f"Normal message {i}",
                priority=MessagePriority.NORMAL
            )
            mailbox.send_message(msg, to_inbox=False)
        urgent_msg = message_factory(
            to_agent="coordinator", type="help_request",
            subject="Urgent help", body="Need assistance",
            priority=MessagePriority.URGENT
        )
        mailbox.send_message(urgent_msg, to_inbox=False)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await subagent_stop_hook(hook_context=context)
        assert result is not None
        assert "Urgent help" in result["systemMessage"]
        assert "Status 0" not in result["systemMessage"]


class TestSubagentStopHookCorruptedData:
    """Test corrupted data handling specific to subagent stop hook."""

    @pytest.mark.asyncio
    async def test_handles_corrupted_outbox_gracefully(self, tmp_path):
        workflow_id = "test-workflow"
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)
        paths.ensure_mailbox_dir()
        paths.outbox_path.write_text("not valid json\n")
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await subagent_stop_hook(hook_context=context)
        assert result is None


class TestSubagentStopHookIntegration:
    """Integration tests for SubagentStop hook."""

    @pytest.mark.asyncio
    async def test_workflow_with_coordinator_workflow_id(self, tmp_path, message_factory):
        workflow_id = "beads-jean_claude-abc123"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg = message_factory(
            from_agent=workflow_id, to_agent="coordinator",
            type="help_request", subject="Need clarification",
            body="User requirements are ambiguous",
            priority=MessagePriority.URGENT, awaiting_response=True
        )
        mailbox.send_message(msg, to_inbox=False)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await subagent_stop_hook(hook_context=context)
        assert result is not None
        assert "Need clarification" in result["systemMessage"]

    @pytest.mark.asyncio
    async def test_notification_format(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg = message_factory(
            to_agent="coordinator", type="help_request",
            subject="Test subject", body="Test body",
            priority=MessagePriority.URGENT
        )
        mailbox.send_message(msg, to_inbox=False)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await subagent_stop_hook(hook_context=context)
        assert isinstance(result, dict)
        assert isinstance(result["systemMessage"], str)
        assert len(result["systemMessage"]) > 0


# ── UserPromptSubmit hook tests ──────────────────────────────────────────


class TestUserPromptSubmitHookBasics:
    """Tests for basic UserPromptSubmit hook functionality."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_messages(self, tmp_path):
        context = {"workflow_id": "test-workflow", "base_dir": tmp_path}
        result = await user_prompt_submit_hook(hook_context=context, user_prompt="Test prompt")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_unread_count_is_zero(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg = message_factory(
            from_agent="coordinator", to_agent="agent-1",
            type="response", subject="Reply", body="Here's the answer",
            priority=MessagePriority.NORMAL
        )
        mailbox.send_message(msg, to_inbox=True)
        mailbox.mark_as_read()
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await user_prompt_submit_hook(hook_context=context, user_prompt="Test prompt")
        assert result is None

    @pytest.mark.asyncio
    async def test_injects_unread_message_as_additional_context(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg = message_factory(
            from_agent="coordinator", to_agent="agent-1",
            type="response", subject="Important update",
            body="Here's the information you need",
            priority=MessagePriority.NORMAL
        )
        mailbox.send_message(msg, to_inbox=True)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await user_prompt_submit_hook(hook_context=context, user_prompt="Test prompt")
        assert result is not None
        assert "additionalContext" in result
        assert "Important update" in result["additionalContext"]
        assert "Here's the information you need" in result["additionalContext"]


class TestUserPromptSubmitHookFormatting:
    """Tests for message formatting in UserPromptSubmit hook."""

    @pytest.mark.asyncio
    async def test_formats_message_with_priority(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg = message_factory(
            from_agent="coordinator", to_agent="agent-1",
            type="help", subject="Urgent issue",
            body="This needs immediate attention",
            priority=MessagePriority.URGENT
        )
        mailbox.send_message(msg, to_inbox=True)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await user_prompt_submit_hook(hook_context=context, user_prompt="Test prompt")
        assert result is not None
        context_text = result["additionalContext"]
        assert "URGENT" in context_text or "urgent" in context_text.lower()

    @pytest.mark.asyncio
    async def test_formats_message_with_subject_and_body(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg = message_factory(
            from_agent="coordinator", to_agent="agent-1",
            type="instruction", subject="Test Subject",
            body="Test Body Content", priority=MessagePriority.NORMAL
        )
        mailbox.send_message(msg, to_inbox=True)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await user_prompt_submit_hook(hook_context=context, user_prompt="Test prompt")
        assert result is not None
        context_text = result["additionalContext"]
        assert "Test Subject" in context_text
        assert "Test Body Content" in context_text

    @pytest.mark.asyncio
    async def test_formats_multiple_messages_clearly(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        for i in range(3):
            msg = message_factory(
                from_agent="coordinator", to_agent="agent-1",
                type="info", subject=f"Message {i}", body=f"Body {i}",
                priority=MessagePriority.NORMAL if i % 2 == 0 else MessagePriority.URGENT
            )
            mailbox.send_message(msg, to_inbox=True)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await user_prompt_submit_hook(hook_context=context, user_prompt="Test prompt")
        assert result is not None
        context_text = result["additionalContext"]
        for i in range(3):
            assert f"Message {i}" in context_text


class TestUserPromptSubmitHookInboxCount:
    """Tests for inbox count update after reading messages."""

    @pytest.mark.asyncio
    async def test_updates_inbox_count_after_reading(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        for i in range(3):
            msg = message_factory(
                from_agent="coordinator", to_agent="agent-1",
                type="info", subject=f"Message {i}", body=f"Body {i}",
                priority=MessagePriority.NORMAL
            )
            mailbox.send_message(msg, to_inbox=True)
        assert mailbox.get_unread_count() == 3
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await user_prompt_submit_hook(hook_context=context, user_prompt="Test prompt")
        assert result is not None
        assert mailbox.get_unread_count() == 0

    @pytest.mark.asyncio
    async def test_only_marks_unread_messages_as_read(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg1 = message_factory(
            from_agent="coordinator", to_agent="agent-1",
            type="info", subject="Old message", body="Already read",
            priority=MessagePriority.NORMAL
        )
        mailbox.send_message(msg1, to_inbox=True)
        mailbox.mark_as_read()
        for i in range(2):
            msg = message_factory(
                from_agent="coordinator", to_agent="agent-1",
                type="info", subject=f"New message {i}", body=f"Unread {i}",
                priority=MessagePriority.NORMAL
            )
            mailbox.send_message(msg, to_inbox=True)
        assert mailbox.get_unread_count() == 2
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await user_prompt_submit_hook(hook_context=context, user_prompt="Test prompt")
        assert result is not None
        context_text = result["additionalContext"]
        assert "New message 0" in context_text
        assert "New message 1" in context_text
        assert mailbox.get_unread_count() == 0

    @pytest.mark.asyncio
    async def test_only_injects_unread_messages(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        for i in range(5):
            msg = message_factory(
                from_agent="coordinator", to_agent="agent-1",
                type="info", subject=f"Old {i}", body=f"Old body {i}",
                priority=MessagePriority.NORMAL
            )
            mailbox.send_message(msg, to_inbox=True)
        mailbox.mark_as_read(count=3)
        assert mailbox.get_unread_count() == 2
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await user_prompt_submit_hook(hook_context=context, user_prompt="Test prompt")
        assert result is not None
        context_text = result["additionalContext"]
        assert "Old 3" in context_text
        assert "Old 4" in context_text
        assert "Old 0" not in context_text


class TestUserPromptSubmitHookCorruptedData:
    """Test corrupted data handling specific to user prompt submit hook."""

    @pytest.mark.asyncio
    async def test_handles_corrupted_inbox_gracefully(self, tmp_path):
        workflow_id = "test-workflow"
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)
        paths.ensure_mailbox_dir()
        paths.inbox_path.write_text("not valid json\n")
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await user_prompt_submit_hook(hook_context=context, user_prompt="Test prompt")
        assert result is None

    @pytest.mark.asyncio
    async def test_handles_corrupted_inbox_count_gracefully(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg = message_factory(
            from_agent="coordinator", to_agent="agent-1",
            type="info", subject="Test", body="Test body",
            priority=MessagePriority.NORMAL
        )
        mailbox.send_message(msg, to_inbox=True)
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=tmp_path)
        paths.inbox_count_path.write_text("not valid json")
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await user_prompt_submit_hook(hook_context=context, user_prompt="Test prompt")
        assert result is None or isinstance(result, dict)


class TestUserPromptSubmitHookIntegration:
    """Integration tests for UserPromptSubmit hook."""

    @pytest.mark.asyncio
    async def test_workflow_with_realistic_workflow_id(self, tmp_path, message_factory):
        workflow_id = "beads-jean_claude-abc123"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg = message_factory(
            from_agent="coordinator", to_agent=workflow_id,
            type="response", subject="Re: Need clarification",
            body="Use approach A because it's more maintainable",
            priority=MessagePriority.URGENT, awaiting_response=False
        )
        mailbox.send_message(msg, to_inbox=True)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await user_prompt_submit_hook(hook_context=context, user_prompt="Continue")
        assert result is not None
        assert "Re: Need clarification" in result["additionalContext"]
        assert mailbox.get_unread_count() == 0

    @pytest.mark.asyncio
    async def test_context_format(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg = message_factory(
            from_agent="coordinator", to_agent="agent-1",
            type="response", subject="Answer",
            body="Detailed answer", priority=MessagePriority.NORMAL
        )
        mailbox.send_message(msg, to_inbox=True)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await user_prompt_submit_hook(hook_context=context, user_prompt="Test prompt")
        assert isinstance(result, dict)
        assert isinstance(result["additionalContext"], str)
        assert len(result["additionalContext"]) > 0

    @pytest.mark.asyncio
    async def test_with_mixed_priority_messages(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        priorities = [MessagePriority.URGENT, MessagePriority.NORMAL, MessagePriority.LOW]
        for i, priority in enumerate(priorities):
            msg = message_factory(
                from_agent="coordinator", to_agent="agent-1",
                type="info", subject=f"{priority.value} message",
                body=f"Message with {priority.value} priority",
                priority=priority
            )
            mailbox.send_message(msg, to_inbox=True)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        result = await user_prompt_submit_hook(hook_context=context, user_prompt="Test prompt")
        assert result is not None
        context_text = result["additionalContext"]
        assert "urgent message" in context_text
        assert "normal message" in context_text
        assert "low message" in context_text
        assert mailbox.get_unread_count() == 0

    @pytest.mark.asyncio
    async def test_preserves_user_prompt(self, tmp_path, message_factory):
        workflow_id = "test-workflow"
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=tmp_path)
        msg = message_factory(
            from_agent="coordinator", to_agent="agent-1",
            type="info", subject="Test", body="Test body",
            priority=MessagePriority.NORMAL
        )
        mailbox.send_message(msg, to_inbox=True)
        context = {"workflow_id": workflow_id, "base_dir": tmp_path}
        original_prompt = "This is the user's original prompt"
        result = await user_prompt_submit_hook(hook_context=context, user_prompt=original_prompt)
        assert result is not None
        assert "additionalContext" in result
        assert "prompt" not in result or result.get("prompt") == original_prompt
