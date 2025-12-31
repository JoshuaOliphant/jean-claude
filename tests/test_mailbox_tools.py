# ABOUTME: Integration tests for Agent SDK mailbox tools (ask_user, notify_user)
# ABOUTME: Tests tool integration with InboxWriter, OutboxMonitor, and WorkflowPauseHandler

"""Integration tests for mailbox Agent SDK tools.

This module tests the ask_user and notify_user tools that agents use to
communicate with users through the mailbox system. These tools follow the
Agent SDK pattern and are exposed as MCP tools to running agents.

Tests cover:
- Tool initialization and context injection
- Message writing to INBOX
- Workflow pausing behavior
- Waiting for OUTBOX responses
- Timeout handling
- Error handling and graceful failures
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

import pytest

from jean_claude.tools.mailbox_tools import (
    ask_user,
    notify_user,
    set_workflow_context,
    jean_claude_mailbox_tools,
)
from jean_claude.core.message import Message, MessagePriority
from jean_claude.core.state import WorkflowState


# =============================================================================
# Context Setup Tests
# =============================================================================


def test_set_workflow_context_stores_values(tmp_path):
    """Test that set_workflow_context() stores workflow context correctly."""
    workflow_dir = tmp_path / "agents" / "workflow-123"
    workflow_dir.mkdir(parents=True)

    workflow_state = WorkflowState(
        workflow_id="test-workflow",
        workflow_name="Test Workflow",
        workflow_type="two-agent"
    )

    project_root = tmp_path

    # Set context
    set_workflow_context(workflow_dir, workflow_state, project_root)

    # Context should be stored (we'll verify by calling a tool)
    # This is implicitly tested by other tests that use the tools


# =============================================================================
# ask_user Tool Tests
# =============================================================================


@pytest.mark.asyncio
async def test_ask_user_writes_message_to_inbox(tmp_path):
    """Test that ask_user writes a message to INBOX directory."""
    workflow_dir = tmp_path / "agents" / "workflow-123"
    workflow_state = WorkflowState(
        workflow_id="test-workflow",
        workflow_name="Test Workflow",
        workflow_type="two-agent"
    )
    project_root = tmp_path

    set_workflow_context(workflow_dir, workflow_state, project_root)

    # Mock OutboxMonitor.wait_for_response to return immediately
    with patch('jean_claude.tools.mailbox_tools.OutboxMonitor') as mock_monitor_class:
        mock_monitor = AsyncMock()
        mock_monitor.wait_for_response = AsyncMock(return_value=Message(
            from_agent="user",
            to_agent="coder-agent",
            type="response",
            subject="Re: Test question",
            body="Fix the auth code - 403 is wrong."
        ))
        mock_monitor_class.return_value = mock_monitor

        # Call ask_user
        args = {
            "question": "Test fails expecting 401 but gets 403. Update test or fix code?",
            "context": "Implementing JWT authentication",
            "priority": "normal"
        }

        result = await ask_user.handler(args)

        # Check that message was written to INBOX
        inbox_dir = workflow_dir / "INBOX"
        assert inbox_dir.exists()

        # Find the message file
        message_files = list(inbox_dir.glob("*.json"))
        assert len(message_files) == 1

        # Verify message content
        with open(message_files[0]) as f:
            message_data = json.load(f)

        assert "Test fails expecting 401" in message_data["body"]
        assert "Implementing JWT authentication" in message_data["body"]
        assert message_data["from_agent"] == "coder-agent"
        assert message_data["to_agent"] == "user"
        assert message_data["priority"] == "normal"


@pytest.mark.asyncio
async def test_ask_user_pauses_workflow(tmp_path):
    """Test that ask_user sets waiting_for_response=True and saves state."""
    workflow_dir = tmp_path / "agents" / "workflow-123"
    workflow_state = WorkflowState(
        workflow_id="test-workflow",
        workflow_name="Test Workflow",
        workflow_type="two-agent"
    )
    project_root = tmp_path

    set_workflow_context(workflow_dir, workflow_state, project_root)

    # Mock OutboxMonitor
    with patch('jean_claude.tools.mailbox_tools.OutboxMonitor') as mock_monitor_class:
        mock_monitor = AsyncMock()
        mock_monitor.wait_for_response = AsyncMock(return_value=Message(
            from_agent="user",
            to_agent="coder-agent",
            type="response",
            subject="Re: Question",
            body="Response"
        ))
        mock_monitor_class.return_value = mock_monitor

        # Mock WorkflowPauseHandler
        with patch('jean_claude.tools.mailbox_tools.WorkflowPauseHandler') as mock_pause_class:
            mock_pause_handler = Mock()
            mock_pause_class.return_value = mock_pause_handler

            args = {
                "question": "Need help with this issue?",
                "context": "Working on feature X",
                "priority": "urgent"
            }

            await ask_user.handler(args)

            # Verify pause_workflow was called
            mock_pause_handler.pause_workflow.assert_called_once()
            call_args = mock_pause_handler.pause_workflow.call_args

            # Check that workflow_state was passed
            assert call_args[0][0] == workflow_state

            # Check that reason contains the question
            assert "Need help" in call_args[1]["reason"]


@pytest.mark.asyncio
async def test_ask_user_waits_for_outbox_response(tmp_path):
    """Test that ask_user calls wait_for_response with 30 minute timeout."""
    workflow_dir = tmp_path / "agents" / "workflow-123"
    workflow_state = WorkflowState(
        workflow_id="test-workflow",
        workflow_name="Test Workflow",
        workflow_type="two-agent"
    )
    project_root = tmp_path

    set_workflow_context(workflow_dir, workflow_state, project_root)

    with patch('jean_claude.tools.mailbox_tools.OutboxMonitor') as mock_monitor_class:
        mock_monitor = AsyncMock()
        mock_monitor.wait_for_response = AsyncMock(return_value=Message(
            from_agent="user",
            to_agent="coder-agent",
            type="response",
            subject="Re: Question",
            body="User response here"
        ))
        mock_monitor_class.return_value = mock_monitor

        args = {
            "question": "What should I do?",
            "context": "Context here",
            "priority": "normal"
        }

        result = await ask_user.handler(args)

        # Verify wait_for_response was called with 30 min timeout
        mock_monitor.wait_for_response.assert_called_once()
        call_args = mock_monitor.wait_for_response.call_args
        assert call_args[1]["timeout_seconds"] == 1800  # 30 minutes


@pytest.mark.asyncio
async def test_ask_user_returns_user_response(tmp_path):
    """Test that ask_user returns the user's response text to the agent."""
    workflow_dir = tmp_path / "agents" / "workflow-123"
    workflow_state = WorkflowState(
        workflow_id="test-workflow",
        workflow_name="Test Workflow",
        workflow_type="two-agent"
    )
    project_root = tmp_path

    set_workflow_context(workflow_dir, workflow_state, project_root)

    user_response_text = "Update the test expectations to match 403 status code."

    with patch('jean_claude.tools.mailbox_tools.OutboxMonitor') as mock_monitor_class:
        mock_monitor = AsyncMock()
        mock_monitor.wait_for_response = AsyncMock(return_value=Message(
            from_agent="user",
            to_agent="coder-agent",
            type="response",
            subject="Re: Question",
            body=user_response_text
        ))
        mock_monitor_class.return_value = mock_monitor

        args = {
            "question": "What should I do?",
            "context": "Context",
            "priority": "normal"
        }

        result = await ask_user.handler(args)

        # Verify result structure (Agent SDK tool response format)
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert result["content"][0]["text"] == user_response_text


@pytest.mark.asyncio
async def test_ask_user_handles_timeout_gracefully(tmp_path):
    """Test that ask_user returns helpful message when user doesn't respond."""
    workflow_dir = tmp_path / "agents" / "workflow-123"
    workflow_state = WorkflowState(
        workflow_id="test-workflow",
        workflow_name="Test Workflow",
        workflow_type="two-agent"
    )
    project_root = tmp_path

    set_workflow_context(workflow_dir, workflow_state, project_root)

    with patch('jean_claude.tools.mailbox_tools.OutboxMonitor') as mock_monitor_class:
        mock_monitor = AsyncMock()
        # Simulate timeout by returning None
        mock_monitor.wait_for_response = AsyncMock(return_value=None)
        mock_monitor_class.return_value = mock_monitor

        args = {
            "question": "What should I do?",
            "context": "Context",
            "priority": "normal"
        }

        result = await ask_user.handler(args)

        # Should return message telling agent to proceed
        assert "content" in result
        assert "No response received" in result["content"][0]["text"]
        assert "proceed with your best judgment" in result["content"][0]["text"]


@pytest.mark.asyncio
async def test_ask_user_handles_priority_levels(tmp_path):
    """Test that ask_user correctly maps priority strings to MessagePriority."""
    workflow_dir = tmp_path / "agents" / "workflow-123"
    workflow_state = WorkflowState(
        workflow_id="test-workflow",
        workflow_name="Test Workflow",
        workflow_type="two-agent"
    )
    project_root = tmp_path

    set_workflow_context(workflow_dir, workflow_state, project_root)

    with patch('jean_claude.tools.mailbox_tools.OutboxMonitor') as mock_monitor_class:
        mock_monitor = AsyncMock()
        mock_monitor.wait_for_response = AsyncMock(return_value=Message(
            from_agent="user",
            to_agent="coder-agent",
            type="response",
            subject="Re: Question",
            body="Response"
        ))
        mock_monitor_class.return_value = mock_monitor

        # Test each priority level
        for priority_str in ["low", "normal", "urgent"]:
            args = {
                "question": f"Question with {priority_str} priority",
                "context": "Context",
                "priority": priority_str
            }

            await ask_user.handler(args)

            # Check message was written with correct priority
            inbox_dir = workflow_dir / "INBOX"
            message_files = list(inbox_dir.glob("*.json"))

            # Find the message for this priority
            for msg_file in message_files:
                with open(msg_file) as f:
                    data = json.load(f)
                    if priority_str in data["body"]:
                        assert data["priority"] == priority_str
                        break


@pytest.mark.asyncio
async def test_ask_user_returns_error_when_not_initialized(tmp_path):
    """Test that ask_user returns error if context not set."""
    # Reset workflow context
    from jean_claude.tools.mailbox_tools import _workflow_context
    _workflow_context["workflow_dir"] = None
    _workflow_context["workflow_state"] = None
    _workflow_context["project_root"] = None

    args = {
        "question": "Test question",
        "context": "Test context",
        "priority": "normal"
    }

    result = await ask_user.handler(args)

    # Should return error message
    assert "content" in result
    assert "Error" in result["content"][0]["text"]
    assert "not initialized" in result["content"][0]["text"]


# =============================================================================
# notify_user Tool Tests
# =============================================================================


@pytest.mark.asyncio
async def test_notify_user_writes_message_to_inbox(tmp_path):
    """Test that notify_user writes informational message to INBOX."""
    workflow_dir = tmp_path / "agents" / "workflow-123"
    workflow_state = WorkflowState(
        workflow_id="test-workflow",
        workflow_name="Test Workflow",
        workflow_type="two-agent"
    )
    project_root = tmp_path

    set_workflow_context(workflow_dir, workflow_state, project_root)

    args = {
        "message": "Successfully completed 3 of 5 features. Next: database migration.",
        "priority": "low"
    }

    result = await notify_user.handler(args)

    # Check that message was written to INBOX
    inbox_dir = workflow_dir / "INBOX"
    assert inbox_dir.exists()

    message_files = list(inbox_dir.glob("*.json"))
    assert len(message_files) >= 1

    # Find our notification message
    found = False
    for msg_file in message_files:
        with open(msg_file) as f:
            data = json.load(f)
            if "Successfully completed 3 of 5 features" in data["body"]:
                found = True
                assert data["from_agent"] == "coder-agent"
                assert data["to_agent"] == "user"
                assert data["priority"] == "low"
                assert data["awaiting_response"] is False  # Key difference from ask_user
                break

    assert found, "Notification message not found in INBOX"


@pytest.mark.asyncio
async def test_notify_user_does_not_pause_workflow(tmp_path):
    """Test that notify_user does NOT pause the workflow."""
    workflow_dir = tmp_path / "agents" / "workflow-123"
    workflow_state = WorkflowState(
        workflow_id="test-workflow",
        workflow_name="Test Workflow",
        workflow_type="two-agent"
    )
    project_root = tmp_path

    set_workflow_context(workflow_dir, workflow_state, project_root)

    # Mock WorkflowPauseHandler to verify it's NOT called
    with patch('jean_claude.tools.mailbox_tools.WorkflowPauseHandler') as mock_pause_class:
        mock_pause_handler = Mock()
        mock_pause_class.return_value = mock_pause_handler

        args = {
            "message": "Progress update: Completed feature 1",
            "priority": "low"
        }

        result = await notify_user.handler(args)

        # Verify pause_workflow was NOT called
        mock_pause_handler.pause_workflow.assert_not_called()


@pytest.mark.asyncio
async def test_notify_user_returns_success_confirmation(tmp_path):
    """Test that notify_user returns success message to agent."""
    workflow_dir = tmp_path / "agents" / "workflow-123"
    workflow_state = WorkflowState(
        workflow_id="test-workflow",
        workflow_name="Test Workflow",
        workflow_type="two-agent"
    )
    project_root = tmp_path

    set_workflow_context(workflow_dir, workflow_state, project_root)

    args = {
        "message": "Status update",
        "priority": "low"
    }

    result = await notify_user.handler(args)

    # Verify success response
    assert "content" in result
    assert result["content"][0]["type"] == "text"
    assert "Message sent" in result["content"][0]["text"]
    assert "successfully" in result["content"][0]["text"]


@pytest.mark.asyncio
async def test_notify_user_returns_error_when_not_initialized(tmp_path):
    """Test that notify_user returns error if context not set."""
    # Reset workflow context
    from jean_claude.tools.mailbox_tools import _workflow_context
    _workflow_context["workflow_dir"] = None

    args = {
        "message": "Test message",
        "priority": "low"
    }

    result = await notify_user.handler(args)

    # Should return error message
    assert "content" in result
    assert "Error" in result["content"][0]["text"]
    assert "not initialized" in result["content"][0]["text"]


# =============================================================================
# MCP Server Configuration Tests
# =============================================================================


def test_mailbox_tools_server_configuration():
    """Test that jean_claude_mailbox_tools server is configured correctly."""
    # Verify server structure
    assert jean_claude_mailbox_tools is not None
    assert "name" in jean_claude_mailbox_tools
    assert jean_claude_mailbox_tools["name"] == "jean-claude-mailbox"
    assert "type" in jean_claude_mailbox_tools
    assert jean_claude_mailbox_tools["type"] == "sdk"
    assert "instance" in jean_claude_mailbox_tools

    # The SDK MCP server is created and tools are registered with it
    # Just verify the basic structure is correct
    assert jean_claude_mailbox_tools["instance"] is not None
