# ABOUTME: Tests for mailbox integration hooks in two_agent.py
# ABOUTME: Tests blocker detection, message sending, and workflow pausing integration

"""Tests for mailbox workflow hooks in two_agent.py.

This module tests the integration of mailbox functionality into the two-agent
workflow, including blocker detection after agent responses, message sending
to INBOX, and workflow pausing when blockers are detected.

Following the project's testing patterns for complex integration testing with
consolidated test coverage and proper fixture usage.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from jean_claude.core.blocker_detector import BlockerDetails, BlockerType
from jean_claude.core.message import Message, MessagePriority
from jean_claude.core.state import WorkflowState
from jean_claude.core.agent import ExecutionResult
from jean_claude.orchestration.auto_continue import run_auto_continue


class TestMailboxWorkflowHooks:
    """Test mailbox integration hooks in two_agent workflow - consolidated testing."""

    @pytest.fixture
    def mock_workflow_dir(self, tmp_path):
        """Provide a mock workflow directory structure."""
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        (workflow_dir / "INBOX").mkdir()
        (workflow_dir / "OUTBOX").mkdir()
        return workflow_dir

    @pytest.fixture
    def mock_workflow_state(self, mock_workflow_dir):
        """Provide a mock WorkflowState for testing."""
        state = Mock(spec=WorkflowState)
        state.workflow_id = "test-workflow-123"
        state.workflow_name = "Test Workflow"
        state.workflow_type = "two-agent"
        state.workflow_dir_path = mock_workflow_dir
        state.waiting_for_response = False
        state.save = Mock()
        return state

    @pytest.fixture
    def mock_execution_result_success(self):
        """Mock successful agent execution result."""
        return ExecutionResult(
            success=True,
            output="Tests passed successfully. Feature implemented correctly.",
            cost=0.25,
            duration_ms=5000
        )

    @pytest.fixture
    def mock_execution_result_with_test_failure(self):
        """Mock agent execution result with test failure."""
        return ExecutionResult(
            success=True,
            output="FAILED tests/test_feature.py::test_something - AssertionError: expected 1 but got 2",
            cost=0.30,
            duration_ms=7000
        )

    @pytest.fixture
    def mock_execution_result_with_error(self):
        """Mock agent execution result with error."""
        return ExecutionResult(
            success=True,
            output="I'm encountering an error and I'm stuck. The API is not responding as expected.",
            cost=0.20,
            duration_ms=3000
        )

    def test_mailbox_hooks_detect_no_blockers_continues_workflow(
        self,
        mock_workflow_state,
        mock_execution_result_success,
        tmp_path
    ):
        """Test that workflow continues normally when no blockers are detected."""
        # Arrange - Mock all the detector classes to return no blockers
        with patch('jean_claude.orchestration.two_agent.FailureDetector') as mock_failure_detector, \
             patch('jean_claude.orchestration.two_agent.ErrorDetector') as mock_error_detector, \
             patch('jean_claude.orchestration.two_agent.AmbiguityDetector') as mock_ambiguity_detector, \
             patch('jean_claude.orchestration.two_agent.execute_prompt_async', return_value=mock_execution_result_success) as mock_execute:

            # Configure detectors to return NONE (no blockers)
            mock_failure_instance = Mock()
            mock_failure_instance.detect_blocker.return_value = BlockerDetails(
                blocker_type=BlockerType.NONE,
                message="No test failures detected"
            )
            mock_failure_detector.return_value = mock_failure_instance

            mock_error_instance = Mock()
            mock_error_instance.detect_blocker.return_value = BlockerDetails(
                blocker_type=BlockerType.NONE,
                message="No errors detected"
            )
            mock_error_detector.return_value = mock_error_instance

            mock_ambiguity_instance = Mock()
            mock_ambiguity_instance.detect_blocker.return_value = BlockerDetails(
                blocker_type=BlockerType.NONE,
                message="No ambiguity detected"
            )
            mock_ambiguity_detector.return_value = mock_ambiguity_instance

            # Act - This would be called within the two-agent workflow
            # We're testing the hook integration, so we simulate the hook being called
            from jean_claude.orchestration.two_agent import _check_for_blockers_and_handle

            result = _check_for_blockers_and_handle(
                agent_result=mock_execution_result_success,
                workflow_state=mock_workflow_state,
                project_root=tmp_path
            )

            # Assert - No blockers means workflow should continue
            assert result is False  # False means "don't pause workflow"
            assert not mock_workflow_state.waiting_for_response
            mock_workflow_state.save.assert_not_called()

    def test_mailbox_hooks_detect_test_failure_sends_message_and_pauses(
        self,
        mock_workflow_state,
        mock_execution_result_with_test_failure,
        tmp_path
    ):
        """Test that test failure blocker triggers message sending and workflow pause."""
        # Arrange
        test_failure_details = BlockerDetails(
            blocker_type=BlockerType.TEST_FAILURE,
            message="Test failure detected in test_feature.py",
            context={"failed_tests": ["test_something"]},
            suggestions=["Fix the assertion in test_something", "Check the expected value"]
        )

        with patch('jean_claude.orchestration.two_agent.FailureDetector') as mock_failure_detector, \
             patch('jean_claude.orchestration.two_agent.ErrorDetector') as mock_error_detector, \
             patch('jean_claude.orchestration.two_agent.AmbiguityDetector') as mock_ambiguity_detector, \
             patch('jean_claude.orchestration.two_agent.BlockerMessageBuilder') as mock_message_builder, \
             patch('jean_claude.orchestration.two_agent.InboxWriter') as mock_inbox_writer, \
             patch('jean_claude.orchestration.two_agent.WorkflowPauseHandler') as mock_pause_handler:

            # Configure failure detector to detect test failure
            mock_failure_instance = Mock()
            mock_failure_instance.detect_blocker.return_value = test_failure_details
            mock_failure_detector.return_value = mock_failure_instance

            # Configure other detectors to return NONE
            mock_error_instance = Mock()
            mock_error_instance.detect_blocker.return_value = BlockerDetails(
                blocker_type=BlockerType.NONE, message="No errors"
            )
            mock_error_detector.return_value = mock_error_instance

            mock_ambiguity_instance = Mock()
            mock_ambiguity_instance.detect_blocker.return_value = BlockerDetails(
                blocker_type=BlockerType.NONE, message="No ambiguity"
            )
            mock_ambiguity_detector.return_value = mock_ambiguity_instance

            # Configure message builder
            mock_message = Message(
                from_agent="coder-agent",
                to_agent="user",
                type="blocker_detected",
                subject="Test Failure Detected",
                body="Test failure detected in test_feature.py",
                priority=MessagePriority.URGENT,
                awaiting_response=True
            )
            mock_builder_instance = Mock()
            mock_builder_instance.build_message.return_value = mock_message
            mock_message_builder.return_value = mock_builder_instance

            # Configure inbox writer and pause handler
            mock_writer_instance = Mock()
            mock_inbox_writer.return_value = mock_writer_instance

            mock_pause_instance = Mock()
            mock_pause_handler.return_value = mock_pause_instance

            # Act
            from jean_claude.orchestration.two_agent import _check_for_blockers_and_handle

            result = _check_for_blockers_and_handle(
                agent_result=mock_execution_result_with_test_failure,
                workflow_state=mock_workflow_state,
                project_root=tmp_path
            )

            # Assert - Blockers detected means workflow should pause
            assert result is True  # True means "pause workflow"

            # Verify blocker detection was called
            mock_failure_instance.detect_blocker.assert_called_once_with(
                mock_execution_result_with_test_failure.output
            )

            # Verify message was built and sent
            mock_builder_instance.build_message.assert_called_once_with(
                blocker_details=test_failure_details,
                from_agent="coder-agent",
                to_agent="user"
            )
            mock_writer_instance.write_to_inbox.assert_called_once_with(mock_message)

            # Verify workflow was paused
            mock_pause_instance.pause_workflow.assert_called_once_with(
                mock_workflow_state,
                reason="Test failure blocker detected"
            )

    def test_mailbox_hooks_detect_error_sends_urgent_message_and_pauses(
        self,
        mock_workflow_state,
        mock_execution_result_with_error,
        tmp_path
    ):
        """Test that error blocker triggers urgent message sending and workflow pause."""
        # Arrange
        error_details = BlockerDetails(
            blocker_type=BlockerType.ERROR,
            message="Agent reported being stuck with API issues",
            suggestions=["Check API configuration", "Verify API endpoint"]
        )

        with patch('jean_claude.orchestration.two_agent.FailureDetector') as mock_failure_detector, \
             patch('jean_claude.orchestration.two_agent.ErrorDetector') as mock_error_detector, \
             patch('jean_claude.orchestration.two_agent.AmbiguityDetector') as mock_ambiguity_detector, \
             patch('jean_claude.orchestration.two_agent.BlockerMessageBuilder') as mock_message_builder, \
             patch('jean_claude.orchestration.two_agent.InboxWriter') as mock_inbox_writer, \
             patch('jean_claude.orchestration.two_agent.WorkflowPauseHandler') as mock_pause_handler:

            # Configure error detector to detect error
            mock_error_instance = Mock()
            mock_error_instance.detect_blocker.return_value = error_details
            mock_error_detector.return_value = mock_error_instance

            # Configure other detectors to return NONE
            mock_failure_instance = Mock()
            mock_failure_instance.detect_blocker.return_value = BlockerDetails(
                blocker_type=BlockerType.NONE, message="No test failures"
            )
            mock_failure_detector.return_value = mock_failure_instance

            mock_ambiguity_instance = Mock()
            mock_ambiguity_instance.detect_blocker.return_value = BlockerDetails(
                blocker_type=BlockerType.NONE, message="No ambiguity"
            )
            mock_ambiguity_detector.return_value = mock_ambiguity_instance

            # Configure message builder
            mock_urgent_message = Message(
                from_agent="coder-agent",
                to_agent="user",
                type="blocker_detected",
                subject="Agent Error - Immediate Attention Required",
                body="Agent reported being stuck with API issues",
                priority=MessagePriority.URGENT,
                awaiting_response=True
            )
            mock_builder_instance = Mock()
            mock_builder_instance.build_message.return_value = mock_urgent_message
            mock_message_builder.return_value = mock_builder_instance

            # Configure inbox writer and pause handler
            mock_writer_instance = Mock()
            mock_inbox_writer.return_value = mock_writer_instance

            mock_pause_instance = Mock()
            mock_pause_handler.return_value = mock_pause_instance

            # Act
            from jean_claude.orchestration.two_agent import _check_for_blockers_and_handle

            result = _check_for_blockers_and_handle(
                agent_result=mock_execution_result_with_error,
                workflow_state=mock_workflow_state,
                project_root=tmp_path
            )

            # Assert
            assert result is True  # True means "pause workflow"

            # Verify error detection
            mock_error_instance.detect_blocker.assert_called_once_with(
                mock_execution_result_with_error.output
            )

            # Verify urgent message was built and sent
            mock_builder_instance.build_message.assert_called_once_with(
                blocker_details=error_details,
                from_agent="coder-agent",
                to_agent="user"
            )
            mock_writer_instance.write_to_inbox.assert_called_once_with(mock_urgent_message)

            # Verify workflow was paused with appropriate reason
            mock_pause_instance.pause_workflow.assert_called_once_with(
                mock_workflow_state,
                reason="Agent error blocker detected"
            )

    def test_mailbox_hooks_prioritize_blockers_test_failure_over_error(
        self,
        mock_workflow_state,
        tmp_path
    ):
        """Test that when multiple blockers are detected, test failures take priority."""
        # Arrange - Agent result that could trigger both test failure and error detection
        mixed_result = ExecutionResult(
            success=True,
            output="I'm having trouble with this feature. FAILED tests/test_feature.py::test_something - AssertionError",
            cost=0.35,
            duration_ms=8000
        )

        test_failure_details = BlockerDetails(
            blocker_type=BlockerType.TEST_FAILURE,
            message="Test failure detected",
        )

        error_details = BlockerDetails(
            blocker_type=BlockerType.ERROR,
            message="Agent reported difficulties",
        )

        with patch('jean_claude.orchestration.two_agent.FailureDetector') as mock_failure_detector, \
             patch('jean_claude.orchestration.two_agent.ErrorDetector') as mock_error_detector, \
             patch('jean_claude.orchestration.two_agent.AmbiguityDetector') as mock_ambiguity_detector, \
             patch('jean_claude.orchestration.two_agent.BlockerMessageBuilder') as mock_message_builder, \
             patch('jean_claude.orchestration.two_agent.InboxWriter') as mock_inbox_writer, \
             patch('jean_claude.orchestration.two_agent.WorkflowPauseHandler') as mock_pause_handler:

            # Configure both detectors to detect blockers
            mock_failure_instance = Mock()
            mock_failure_instance.detect_blocker.return_value = test_failure_details
            mock_failure_detector.return_value = mock_failure_instance

            mock_error_instance = Mock()
            mock_error_instance.detect_blocker.return_value = error_details
            mock_error_detector.return_value = mock_error_instance

            mock_ambiguity_instance = Mock()
            mock_ambiguity_instance.detect_blocker.return_value = BlockerDetails(
                blocker_type=BlockerType.NONE, message="No ambiguity"
            )
            mock_ambiguity_detector.return_value = mock_ambiguity_instance

            # Configure message builder
            mock_test_failure_message = Message(
                from_agent="coder-agent",
                to_agent="user",
                type="blocker_detected",
                subject="Test Failure Detected",
                body="Test failure detected",
                priority=MessagePriority.URGENT,
                awaiting_response=True
            )
            mock_builder_instance = Mock()
            mock_builder_instance.build_message.return_value = mock_test_failure_message
            mock_message_builder.return_value = mock_builder_instance

            # Configure writer and pause handler
            mock_writer_instance = Mock()
            mock_inbox_writer.return_value = mock_writer_instance

            mock_pause_instance = Mock()
            mock_pause_handler.return_value = mock_pause_instance

            # Act
            from jean_claude.orchestration.two_agent import _check_for_blockers_and_handle

            result = _check_for_blockers_and_handle(
                agent_result=mixed_result,
                workflow_state=mock_workflow_state,
                project_root=tmp_path
            )

            # Assert - Should prioritize test failure over error
            assert result is True

            # Verify test failure message was sent (not error message)
            mock_builder_instance.build_message.assert_called_once_with(
                blocker_details=test_failure_details,
                from_agent="coder-agent",
                to_agent="user"
            )
            mock_writer_instance.write_to_inbox.assert_called_once_with(mock_test_failure_message)

    def test_mailbox_hooks_integration_with_auto_continue_workflow(
        self,
        mock_workflow_state,
        tmp_path
    ):
        """Test integration of mailbox hooks within the auto-continue workflow loop."""
        # Arrange - This tests the actual integration point in run_auto_continue
        # Create a mock feature to return
        mock_feature = Mock(status="not_started", name="test-feature")
        mock_workflow_state.features = [mock_feature]
        mock_workflow_state.current_feature_index = 0
        mock_workflow_state.max_iterations = 5
        mock_workflow_state.iteration_count = 0
        mock_workflow_state.is_complete.return_value = False
        mock_workflow_state.is_failed.return_value = False
        # Return feature first time, None second time (to end loop)
        mock_workflow_state.get_next_feature.side_effect = [mock_feature, None]
        mock_workflow_state.get_summary.return_value = {
            'completed_features': 0,
            'total_features': 1,
            'failed_features': 0,
            'progress_percentage': 0.0,
            'iteration_count': 1,
            'total_cost_usd': 0.25,
            'total_duration_ms': 5000
        }

        test_failure_result = ExecutionResult(
            success=True,
            output="FAILED tests/test_feature.py::test_method - AssertionError",
            cost=0.25,
            duration_ms=5000
        )

        with patch('jean_claude.orchestration.auto_continue.execute_prompt_async', return_value=test_failure_result), \
             patch('jean_claude.orchestration.two_agent._check_for_blockers_and_handle', return_value=True) as mock_blocker_check:

            # Act
            import asyncio
            result_state = asyncio.run(run_auto_continue(
                state=mock_workflow_state,
                project_root=tmp_path,
                max_iterations=1,  # Limit to one iteration for testing
                model="sonnet",
                verify_first=False
            ))

            # Assert - Verify that blocker checking was called
            mock_blocker_check.assert_called()

            # The workflow should have detected blockers and paused
            # (The exact behavior depends on how the integration is implemented in run_auto_continue)

    def test_mailbox_hooks_handle_directory_creation_errors(
        self,
        mock_workflow_state,
        mock_execution_result_with_test_failure,
        tmp_path
    ):
        """Test that mailbox hooks handle directory creation errors gracefully."""
        # Arrange
        test_failure_details = BlockerDetails(
            blocker_type=BlockerType.TEST_FAILURE,
            message="Test failure detected"
        )

        with patch('jean_claude.orchestration.two_agent.FailureDetector') as mock_failure_detector, \
             patch('jean_claude.orchestration.two_agent.ErrorDetector') as mock_error_detector, \
             patch('jean_claude.orchestration.two_agent.AmbiguityDetector') as mock_ambiguity_detector, \
             patch('jean_claude.orchestration.two_agent.InboxWriter') as mock_inbox_writer:

            # Configure failure detector
            mock_failure_instance = Mock()
            mock_failure_instance.detect_blocker.return_value = test_failure_details
            mock_failure_detector.return_value = mock_failure_instance

            # Configure other detectors
            mock_error_instance = Mock()
            mock_error_instance.detect_blocker.return_value = BlockerDetails(
                blocker_type=BlockerType.NONE, message="No errors"
            )
            mock_error_detector.return_value = mock_error_instance

            mock_ambiguity_instance = Mock()
            mock_ambiguity_instance.detect_blocker.return_value = BlockerDetails(
                blocker_type=BlockerType.NONE, message="No ambiguity"
            )
            mock_ambiguity_detector.return_value = mock_ambiguity_instance

            # Configure inbox writer to raise permission error
            mock_writer_instance = Mock()
            mock_writer_instance.write_message.side_effect = PermissionError("Permission denied")
            mock_inbox_writer.return_value = mock_writer_instance

            # Act & Assert - Should handle the error gracefully, not crash
            from jean_claude.orchestration.two_agent import _check_for_blockers_and_handle

            # Should not raise exception, but may log error and continue
            result = _check_for_blockers_and_handle(
                agent_result=mock_execution_result_with_test_failure,
                workflow_state=mock_workflow_state,
                project_root=tmp_path
            )

            # The function should handle the error gracefully
            # Exact behavior depends on implementation (may still return True to pause)
            assert isinstance(result, bool)