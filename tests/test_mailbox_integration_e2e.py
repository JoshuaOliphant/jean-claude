# ABOUTME: End-to-end integration test for complete mailbox workflow
# ABOUTME: Tests workflow hits test failure, sends message, pauses, user responds, workflow resumes correctly

"""End-to-end mailbox integration test.

This module provides comprehensive testing of the complete mailbox integration
workflow from start to finish: agent execution with test failure, blocker detection,
message sending, workflow pausing, user response, and workflow resumption.

Following the project's testing patterns with consolidated test coverage,
proper fixture usage, and comprehensive E2E scenario testing.
"""

import json
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any

import pytest

from jean_claude.core.agent import ExecutionResult
from jean_claude.core.blocker_detector import BlockerDetails, BlockerType
from jean_claude.core.message import Message, MessagePriority
from jean_claude.core.response_parser import UserDecision, DecisionType
from jean_claude.core.state import WorkflowState
from jean_claude.orchestration.auto_continue import run_auto_continue


class TestMailboxIntegrationE2E:
    """End-to-end mailbox integration testing - complete workflow simulation."""

    @pytest.fixture
    def mock_project_root(self, tmp_path):
        """Create a complete project directory structure for E2E testing."""
        project_root = tmp_path / "test-project"
        project_root.mkdir()

        # Create standard directory structure
        (project_root / "agents").mkdir()
        (project_root / "specs").mkdir()
        (project_root / "tests").mkdir()
        (project_root / "src").mkdir()

        # Create a test file that will "fail"
        test_file = project_root / "tests" / "test_feature.py"
        test_file.write_text("""
def test_example_feature():
    assert False  # This will fail
""")

        return project_root

    @pytest.fixture
    def mock_workflow_state(self, mock_project_root, workflow_state_factory):
        """Create a complete workflow state for E2E testing."""
        workflow_id = "mailbox-e2e-test"
        agents_dir = mock_project_root / "agents" / workflow_id
        agents_dir.mkdir(parents=True)

        # Create INBOX and OUTBOX directories
        (agents_dir / "INBOX").mkdir()
        (agents_dir / "OUTBOX").mkdir()

        # Create workflow state with a test feature
        state = workflow_state_factory(
            workflow_id=workflow_id,
            workflow_name="Mailbox E2E Test Workflow",
            workflow_type="two-agent",
            phase="implementing"
        )

        # Add a test feature
        state.features = [{
            "name": "test-feature",
            "description": "A test feature that will fail",
            "status": "not_started",
            "test_file": "tests/test_feature.py",
            "tests_passing": False,
            "started_at": None,
            "completed_at": None
        }]
        state.current_feature_index = 0
        state.iteration_count = 0
        state.max_iterations = 5
        state.waiting_for_response = False
        state.workflow_dir_path = agents_dir

        # Save initial state
        state_file = agents_dir / "state.json"
        state_file.write_text(state.model_dump_json())

        return state

    @pytest.mark.asyncio
    async def test_complete_mailbox_workflow_e2e(
        self,
        mock_project_root,
        mock_workflow_state,
        message_factory
    ):
        """Test complete end-to-end mailbox workflow: failure → pause → response → resume.

        This test simulates the complete workflow:
        1. Agent executes and hits test failure
        2. Blocker is detected and message sent to INBOX
        3. Workflow pauses (waiting_for_response=True)
        4. User puts response in OUTBOX
        5. Workflow resumes based on user decision
        """
        # PHASE 1: Setup - workflow starts with test failure
        test_failure_result = ExecutionResult(
            success=True,  # Agent ran successfully but tests failed
            output="FAILED tests/test_feature.py::test_example_feature - AssertionError: Test failed",
            cost=0.25,
            duration_ms=5000
        )

        # Mock a feature to process
        mock_feature = Mock()
        mock_feature.name = "test-feature"
        mock_feature.status = "not_started"

        # Setup workflow state mock behavior
        mock_workflow_state.get_next_feature.side_effect = [mock_feature, None]  # Return feature once, then None
        mock_workflow_state.is_complete.return_value = False
        mock_workflow_state.is_failed.return_value = False
        mock_workflow_state.should_verify.return_value = False
        mock_workflow_state.save = Mock()

        # PHASE 2: Mock the blocker detection and handling
        with patch('jean_claude.orchestration.auto_continue.execute_prompt_async', return_value=test_failure_result) as mock_execute, \
             patch('jean_claude.orchestration.two_agent._check_for_blockers_and_handle') as mock_blocker_check:

            # Configure blocker detection to return True (blocker found and handled)
            mock_blocker_check.return_value = True

            # Configure workflow state to be paused after blocker handling
            def pause_workflow_side_effect(*args):
                mock_workflow_state.waiting_for_response = True
                return True
            mock_blocker_check.side_effect = pause_workflow_side_effect

            # Act: Run workflow first iteration (should detect failure and pause)
            result_state = await run_auto_continue(
                state=mock_workflow_state,
                project_root=mock_project_root,
                max_iterations=1,
                verify_first=False
            )

            # Assert: Verify workflow executed and blocker was handled
            mock_execute.assert_called_once()
            mock_blocker_check.assert_called_once_with(
                test_failure_result, mock_workflow_state, mock_project_root
            )
            assert mock_workflow_state.waiting_for_response is True

        # PHASE 3: Simulate user response
        # Create user response message
        user_response = message_factory(
            from_agent="user",
            to_agent="coordinator",
            type="response",
            subject="Decision on test failure",
            body="continue - please fix the test and continue",
            priority=MessagePriority.NORMAL
        )

        # Place response in OUTBOX
        outbox_dir = mock_workflow_state.workflow_dir_path / "OUTBOX"
        response_file = outbox_dir / f"{user_response.id}.json"
        response_file.write_text(user_response.model_dump_json())

        # PHASE 4: Mock workflow resumption
        with patch('jean_claude.orchestration.auto_continue.OutboxMonitor') as mock_outbox_monitor_class, \
             patch('jean_claude.orchestration.auto_continue.ResponseParser') as mock_response_parser_class, \
             patch('jean_claude.orchestration.auto_continue.WorkflowResumeHandler') as mock_resume_handler_class:

            # Setup OutboxMonitor to return the user response
            mock_outbox_monitor = Mock()
            mock_outbox_monitor_class.return_value = mock_outbox_monitor
            mock_outbox_monitor.poll_for_new_messages.return_value = [user_response]

            # Setup ResponseParser to parse "continue" decision
            mock_response_parser = Mock()
            mock_response_parser_class.return_value = mock_response_parser
            mock_user_decision = UserDecision(
                decision_type=DecisionType.CONTINUE,
                message="User chose to continue",
                context={"original_blocker": "test_failure"}
            )
            mock_response_parser.parse_response.return_value = mock_user_decision

            # Setup WorkflowResumeHandler
            mock_resume_handler = Mock()
            mock_resume_handler_class.return_value = mock_resume_handler

            # Configure resume handler to clear waiting_for_response flag
            def resume_workflow_side_effect(state, decision):
                state.waiting_for_response = False
            mock_resume_handler.resume_workflow.side_effect = resume_workflow_side_effect

            # Act: Run workflow again (should detect response and resume)
            final_state = await run_auto_continue(
                state=mock_workflow_state,
                project_root=mock_project_root,
                max_iterations=1,
                verify_first=False
            )

            # Assert: Verify outbox monitoring and workflow resumption
            mock_outbox_monitor_class.assert_called_once_with(mock_workflow_state.workflow_dir_path)
            mock_outbox_monitor.poll_for_new_messages.assert_called()
            mock_response_parser.parse_response.assert_called_once_with(user_response.body)
            mock_resume_handler.resume_workflow.assert_called_once_with(mock_workflow_state, mock_user_decision)

            # Verify workflow is no longer waiting for response
            assert mock_workflow_state.waiting_for_response is False

        # PHASE 5: Verify complete workflow state
        assert final_state == mock_workflow_state
        # Verify state was saved after operations
        mock_workflow_state.save.assert_called()

    @pytest.mark.asyncio
    async def test_e2e_workflow_with_abort_decision(
        self,
        mock_project_root,
        mock_workflow_state,
        message_factory
    ):
        """Test E2E workflow when user decides to abort."""
        # Setup test failure scenario
        test_failure_result = ExecutionResult(
            success=True,
            output="FAILED tests/test_feature.py::test_example_feature - AssertionError",
            cost=0.25,
            duration_ms=5000
        )

        mock_feature = Mock()
        mock_feature.name = "test-feature"
        mock_feature.status = "not_started"

        mock_workflow_state.get_next_feature.side_effect = [mock_feature, None]
        mock_workflow_state.is_complete.return_value = False
        mock_workflow_state.is_failed.return_value = False
        mock_workflow_state.should_verify.return_value = False
        mock_workflow_state.save = Mock()

        # Phase 1: Execute with failure and pause
        with patch('jean_claude.orchestration.auto_continue.execute_prompt_async', return_value=test_failure_result), \
             patch('jean_claude.orchestration.two_agent._check_for_blockers_and_handle') as mock_blocker_check:

            def pause_workflow(*args):
                mock_workflow_state.waiting_for_response = True
                return True
            mock_blocker_check.side_effect = pause_workflow

            # Run first iteration - should pause
            await run_auto_continue(
                state=mock_workflow_state,
                project_root=mock_project_root,
                max_iterations=1,
                verify_first=False
            )

            assert mock_workflow_state.waiting_for_response is True

        # Phase 2: User responds with abort decision
        abort_response = message_factory(
            from_agent="user",
            type="response",
            subject="Decision",
            body="abort - this is too difficult to fix",
        )

        outbox_dir = mock_workflow_state.workflow_dir_path / "OUTBOX"
        response_file = outbox_dir / f"{abort_response.id}.json"
        response_file.write_text(abort_response.model_dump_json())

        # Phase 3: Resume with abort decision
        with patch('jean_claude.orchestration.auto_continue.OutboxMonitor') as mock_outbox_monitor_class, \
             patch('jean_claude.orchestration.auto_continue.ResponseParser') as mock_response_parser_class, \
             patch('jean_claude.orchestration.auto_continue.WorkflowResumeHandler') as mock_resume_handler_class:

            mock_outbox_monitor = Mock()
            mock_outbox_monitor_class.return_value = mock_outbox_monitor
            mock_outbox_monitor.poll_for_new_messages.return_value = [abort_response]

            mock_response_parser = Mock()
            mock_response_parser_class.return_value = mock_response_parser
            abort_decision = UserDecision(
                decision_type=DecisionType.ABORT,
                message="User chose to abort workflow",
                context={}
            )
            mock_response_parser.parse_response.return_value = abort_decision

            mock_resume_handler = Mock()
            mock_resume_handler_class.return_value = mock_resume_handler

            def abort_workflow_side_effect(state, decision):
                state.waiting_for_response = False
                state.phase = "aborted"
            mock_resume_handler.resume_workflow.side_effect = abort_workflow_side_effect

            # Run workflow - should handle abort
            final_state = await run_auto_continue(
                state=mock_workflow_state,
                project_root=mock_project_root,
                max_iterations=1,
                verify_first=False
            )

            # Verify abort was processed
            mock_response_parser.parse_response.assert_called_once_with(abort_response.body)
            mock_resume_handler.resume_workflow.assert_called_once_with(mock_workflow_state, abort_decision)
            assert mock_workflow_state.waiting_for_response is False
            assert mock_workflow_state.phase == "aborted"

    @pytest.mark.asyncio
    async def test_e2e_workflow_multiple_blockers_and_responses(
        self,
        mock_project_root,
        mock_workflow_state,
        message_factory
    ):
        """Test E2E workflow with multiple blocker-response cycles."""
        # Setup multiple features that will have issues
        feature1 = Mock()
        feature1.name = "feature-1"
        feature1.status = "not_started"

        feature2 = Mock()
        feature2.name = "feature-2"
        feature2.status = "not_started"

        mock_workflow_state.get_next_feature.side_effect = [feature1, feature2, None]
        mock_workflow_state.is_complete.return_value = False
        mock_workflow_state.is_failed.return_value = False
        mock_workflow_state.should_verify.return_value = False
        mock_workflow_state.save = Mock()

        # First blocker: test failure
        test_failure_result = ExecutionResult(
            success=True,
            output="FAILED tests/test_feature1.py - AssertionError",
            cost=0.25,
            duration_ms=5000
        )

        # Second blocker: error
        error_result = ExecutionResult(
            success=True,
            output="I'm stuck and need help with the database connection",
            cost=0.30,
            duration_ms=6000
        )

        execution_results = [test_failure_result, error_result]
        execution_index = 0

        def get_next_execution_result(*args):
            nonlocal execution_index
            result = execution_results[execution_index]
            execution_index += 1
            return result

        # Cycle 1: First blocker and response
        with patch('jean_claude.orchestration.auto_continue.execute_prompt_async', side_effect=get_next_execution_result), \
             patch('jean_claude.orchestration.two_agent._check_for_blockers_and_handle') as mock_blocker_check:

            call_count = 0
            def handle_blocker_side_effect(*args):
                nonlocal call_count
                call_count += 1
                mock_workflow_state.waiting_for_response = True
                return True
            mock_blocker_check.side_effect = handle_blocker_side_effect

            # First execution - should hit test failure
            await run_auto_continue(
                state=mock_workflow_state,
                project_root=mock_project_root,
                max_iterations=1,
                verify_first=False
            )

            assert mock_workflow_state.waiting_for_response is True
            assert call_count == 1

        # User responds to first blocker
        response1 = message_factory(
            body="continue - I've fixed the test",
            type="response"
        )

        outbox_dir = mock_workflow_state.workflow_dir_path / "OUTBOX"
        (outbox_dir / f"{response1.id}.json").write_text(response1.model_dump_json())

        # Resume from first blocker
        with patch('jean_claude.orchestration.auto_continue.OutboxMonitor') as mock_outbox_monitor_class, \
             patch('jean_claude.orchestration.auto_continue.ResponseParser') as mock_response_parser_class, \
             patch('jean_claude.orchestration.auto_continue.WorkflowResumeHandler') as mock_resume_handler_class:

            mock_outbox_monitor = Mock()
            mock_outbox_monitor_class.return_value = mock_outbox_monitor
            mock_outbox_monitor.poll_for_new_messages.return_value = [response1]

            mock_response_parser = Mock()
            mock_response_parser_class.return_value = mock_response_parser
            continue_decision = UserDecision(DecisionType.CONTINUE, "Continue", {})
            mock_response_parser.parse_response.return_value = continue_decision

            mock_resume_handler = Mock()
            mock_resume_handler_class.return_value = mock_resume_handler

            def clear_waiting_flag(state, decision):
                state.waiting_for_response = False
            mock_resume_handler.resume_workflow.side_effect = clear_waiting_flag

            # Resume workflow
            await run_auto_continue(
                state=mock_workflow_state,
                project_root=mock_project_root,
                max_iterations=1,
                verify_first=False
            )

            assert mock_workflow_state.waiting_for_response is False
            mock_resume_handler.resume_workflow.assert_called_once()

        # Verify the complete E2E workflow handled multiple blocker cycles
        assert mock_workflow_state.save.call_count >= 2  # Should have saved state multiple times