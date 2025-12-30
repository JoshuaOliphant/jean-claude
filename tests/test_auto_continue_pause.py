# ABOUTME: Tests for auto_continue.py pause logic that checks waiting_for_response flag and outbox monitoring
# ABOUTME: Consolidated test suite covering auto-continue pause functionality with proper fixtures usage

"""Tests for auto-continue pause logic.

Following the project's testing patterns with consolidated test coverage,
proper fixture usage, and comprehensive testing of auto-continue pause functionality.
Tests the waiting_for_response flag checking and outbox monitoring integration.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from jean_claude.core.agent import ExecutionResult
from jean_claude.core.message import Message, MessagePriority
from jean_claude.core.response_parser import UserDecision, DecisionType
from jean_claude.core.state import WorkflowState
from jean_claude.orchestration.auto_continue import run_auto_continue


class TestAutoContinuePauseLogic:
    """Test auto-continue pause logic functionality."""

    @pytest.mark.asyncio
    async def test_auto_continue_skips_when_waiting_for_response_true(self, tmp_path, mock_workflow_state_instance, message_factory):
        """Test that auto_continue skips continuation when waiting_for_response=True."""
        # Setup workflow state with waiting_for_response=True
        mock_workflow_state = mock_workflow_state_instance
        mock_workflow_state.waiting_for_response = True
        mock_workflow_state.get_next_feature.return_value = None  # No more features
        mock_workflow_state.iteration_count = 0
        mock_workflow_state.max_iterations = 10
        mock_workflow_state.should_verify.return_value = False

        # Create project directory structure
        project_root = tmp_path / "project"
        project_root.mkdir()
        agents_dir = project_root / "agents" / mock_workflow_state.workflow_id
        agents_dir.mkdir(parents=True)

        # Save state file
        state_file = agents_dir / "state.json"
        state_file.write_text('{"waiting_for_response": true}')

        # Mock save method
        mock_workflow_state.save = Mock()

        # Run auto_continue - should exit early due to waiting_for_response=True
        result = await run_auto_continue(
            state=mock_workflow_state,
            project_root=project_root,
            verify_first=False
        )

        # Verify workflow exited without processing features
        assert result == mock_workflow_state
        # Verify get_next_feature was NOT called since workflow was paused
        mock_workflow_state.get_next_feature.assert_not_called()

    @pytest.mark.asyncio
    async def test_auto_continue_continues_when_waiting_for_response_false(self, tmp_path, mock_workflow_state_instance):
        """Test that auto_continue continues normally when waiting_for_response=False."""
        # Setup workflow state with waiting_for_response=False
        mock_workflow_state = mock_workflow_state_instance
        mock_workflow_state.waiting_for_response = False
        mock_workflow_state.get_next_feature.return_value = None  # No more features
        mock_workflow_state.iteration_count = 0
        mock_workflow_state.max_iterations = 10
        mock_workflow_state.should_verify.return_value = False

        # Create project directory structure
        project_root = tmp_path / "project"
        project_root.mkdir()
        agents_dir = project_root / "agents" / mock_workflow_state.workflow_id
        agents_dir.mkdir(parents=True)

        # Mock save method
        mock_workflow_state.save = Mock()

        # Run auto_continue - should proceed normally
        result = await run_auto_continue(
            state=mock_workflow_state,
            project_root=project_root,
            verify_first=False
        )

        # Verify workflow proceeded normally
        assert result == mock_workflow_state
        mock_workflow_state.get_next_feature.assert_called()

    @pytest.mark.asyncio
    async def test_auto_continue_checks_outbox_for_response(self, tmp_path, mock_workflow_state_instance, message_factory):
        """Test that auto_continue monitors outbox when waiting_for_response=True."""
        # Setup workflow state
        mock_workflow_state = mock_workflow_state_instance
        mock_workflow_state.waiting_for_response = True
        mock_workflow_state.iteration_count = 0
        mock_workflow_state.max_iterations = 10
        mock_workflow_state.should_verify.return_value = False

        # Create project directory structure
        project_root = tmp_path / "project"
        project_root.mkdir()
        agents_dir = project_root / "agents" / mock_workflow_state.workflow_id
        agents_dir.mkdir(parents=True)
        outbox_dir = agents_dir / "OUTBOX"
        outbox_dir.mkdir(parents=True)

        # Create a response message in OUTBOX
        response_message = message_factory(
            from_agent="user",
            to_agent="coordinator",
            type="response",
            subject="Decision",
            body="continue"
        )

        # Write message to outbox
        message_file = outbox_dir / f"{response_message.id}.json"
        message_file.write_text(response_message.model_dump_json())

        # Mock save method
        mock_workflow_state.save = Mock()

        # Mock get_next_feature to return None (no more features)
        mock_workflow_state.get_next_feature.return_value = None

        # Mock OutboxMonitor and ResponseParser
        with patch('jean_claude.orchestration.auto_continue.OutboxMonitor') as mock_outbox_monitor_class, \
             patch('jean_claude.orchestration.auto_continue.ResponseParser') as mock_response_parser_class, \
             patch('jean_claude.orchestration.auto_continue.WorkflowResumeHandler') as mock_resume_handler_class:

            # Setup mock instances
            mock_outbox_monitor = Mock()
            mock_outbox_monitor_class.return_value = mock_outbox_monitor
            mock_outbox_monitor.poll_for_new_messages.return_value = [response_message]

            mock_response_parser = Mock()
            mock_response_parser_class.return_value = mock_response_parser
            mock_user_decision = UserDecision(
                decision_type=DecisionType.CONTINUE,
                message="User chose to continue",
                context={}
            )
            mock_response_parser.parse_response.return_value = mock_user_decision

            mock_resume_handler = Mock()
            mock_resume_handler_class.return_value = mock_resume_handler

            # Run auto_continue
            result = await run_auto_continue(
                state=mock_workflow_state,
                project_root=project_root,
                verify_first=False
            )

            # Verify OutboxMonitor was created and used
            mock_outbox_monitor_class.assert_called_once_with(agents_dir)
            mock_outbox_monitor.poll_for_new_messages.assert_called()

            # Verify ResponseParser was used
            mock_response_parser_class.assert_called_once()
            mock_response_parser.parse_response.assert_called_once_with(response_message.body)

            # Verify WorkflowResumeHandler was used
            mock_resume_handler_class.assert_called_once_with(project_root)
            mock_resume_handler.resume_workflow.assert_called_once_with(mock_workflow_state, mock_user_decision)

    @pytest.mark.asyncio
    async def test_auto_continue_waits_when_no_outbox_response(self, tmp_path, mock_workflow_state_instance):
        """Test that auto_continue waits when waiting_for_response=True but no outbox messages."""
        # Setup workflow state
        mock_workflow_state = mock_workflow_state_instance
        mock_workflow_state.waiting_for_response = True
        mock_workflow_state.iteration_count = 0
        mock_workflow_state.max_iterations = 10
        mock_workflow_state.should_verify.return_value = False
        mock_workflow_state.get_next_feature.return_value = None

        # Create project directory structure without outbox messages
        project_root = tmp_path / "project"
        project_root.mkdir()
        agents_dir = project_root / "agents" / mock_workflow_state.workflow_id
        agents_dir.mkdir(parents=True)
        outbox_dir = agents_dir / "OUTBOX"
        outbox_dir.mkdir(parents=True)

        # Mock save method
        mock_workflow_state.save = Mock()

        # Mock OutboxMonitor to return empty list (no messages)
        with patch('jean_claude.orchestration.auto_continue.OutboxMonitor') as mock_outbox_monitor_class:
            mock_outbox_monitor = Mock()
            mock_outbox_monitor_class.return_value = mock_outbox_monitor
            mock_outbox_monitor.poll_for_new_messages.return_value = []

            # Run auto_continue
            result = await run_auto_continue(
                state=mock_workflow_state,
                project_root=project_root,
                verify_first=False
            )

            # Verify OutboxMonitor was created and used
            mock_outbox_monitor_class.assert_called_once_with(agents_dir)
            mock_outbox_monitor.poll_for_new_messages.assert_called()

            # Verify workflow remained in waiting state
            assert result == mock_workflow_state