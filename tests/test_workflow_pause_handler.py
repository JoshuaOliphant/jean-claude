# ABOUTME: Tests for WorkflowPauseHandler that sets waiting_for_response=True and logs pause events
# ABOUTME: Consolidated test suite for workflow pause functionality

"""Tests for WorkflowPauseHandler.

Following the project's testing patterns with consolidated test coverage,
proper fixture usage, and comprehensive testing of pause functionality.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

import pytest

from jean_claude.core.workflow_pause_handler import WorkflowPauseHandler
from jean_claude.core.state import WorkflowState
from jean_claude.core.events import EventLogger, EventType


class TestWorkflowPauseHandlerCreation:
    """Test WorkflowPauseHandler instantiation and basic functionality."""

    def test_pause_handler_creation_with_project_root(self, tmp_path):
        """Test creating WorkflowPauseHandler with project root."""
        handler = WorkflowPauseHandler(tmp_path)
        assert isinstance(handler, WorkflowPauseHandler)
        assert handler.project_root == tmp_path

    def test_pause_handler_creation_with_string_path(self, tmp_path):
        """Test creating WorkflowPauseHandler with string project root."""
        handler = WorkflowPauseHandler(str(tmp_path))
        assert isinstance(handler, WorkflowPauseHandler)
        assert handler.project_root == Path(str(tmp_path))

    def test_pause_handler_has_pause_workflow_method(self, tmp_path):
        """Test that WorkflowPauseHandler has the required pause_workflow method."""
        handler = WorkflowPauseHandler(tmp_path)

        assert hasattr(handler, 'pause_workflow')
        assert callable(getattr(handler, 'pause_workflow'))


class TestWorkflowPauseHandlerFunctionality:
    """Test WorkflowPauseHandler pause functionality."""

    @patch.object(WorkflowState, 'save')
    def test_pause_workflow_sets_waiting_for_response_true(self, mock_save, tmp_path, mock_workflow_state):
        """Test that pause_workflow sets waiting_for_response=True in WorkflowState."""
        handler = WorkflowPauseHandler(tmp_path)

        # Verify initial state
        assert mock_workflow_state.waiting_for_response is False

        # Pause workflow
        handler.pause_workflow(mock_workflow_state, "Test pause reason")

        # Verify state was updated
        assert mock_workflow_state.waiting_for_response is True
        # Verify save was called
        mock_save.assert_called_once_with(tmp_path)

    @patch.object(WorkflowState, 'save')
    def test_pause_workflow_logs_pause_event_to_events_jsonl(self, mock_save, tmp_path, mock_workflow_state):
        """Test that pause_workflow logs pause event to events.jsonl file."""
        handler = WorkflowPauseHandler(tmp_path)

        # Mock EventLogger
        with patch('jean_claude.core.workflow_pause_handler.EventLogger') as mock_event_logger:
            mock_logger_instance = Mock()
            mock_event_logger.return_value = mock_logger_instance

            # Pause workflow with reason
            pause_reason = "Test failure detected - waiting for user response"
            handler.pause_workflow(mock_workflow_state, pause_reason)

            # Verify EventLogger was created with correct project root
            mock_event_logger.assert_called_once_with(tmp_path)

            # Verify event was emitted
            mock_logger_instance.emit.assert_called_once_with(
                workflow_id=mock_workflow_state.workflow_id,
                event_type=EventType.WORKFLOW_PAUSED,
                data={
                    "reason": pause_reason,
                    "waiting_for_response": True
                }
            )

    @patch.object(WorkflowState, 'save')
    def test_pause_workflow_with_different_pause_reasons(self, mock_save, tmp_path, mock_workflow_state):
        """Test pausing workflow with different types of pause reasons."""
        handler = WorkflowPauseHandler(tmp_path)

        test_reasons = [
            "Test failure detected in authentication module",
            "Agent encountered unexpected error during implementation",
            "Ambiguous requirements detected - need user clarification",
            "Build failure in CI pipeline"
        ]

        with patch('jean_claude.core.workflow_pause_handler.EventLogger') as mock_event_logger:
            mock_logger_instance = Mock()
            mock_event_logger.return_value = mock_logger_instance

            for reason in test_reasons:
                # Reset mocks
                mock_logger_instance.reset_mock()
                mock_workflow_state.waiting_for_response = False

                # Pause with this reason
                handler.pause_workflow(mock_workflow_state, reason)

                # Verify state was set
                assert mock_workflow_state.waiting_for_response is True

                # Verify event was logged with correct reason
                mock_logger_instance.emit.assert_called_once_with(
                    workflow_id=mock_workflow_state.workflow_id,
                    event_type=EventType.WORKFLOW_PAUSED,
                    data={
                        "reason": reason,
                        "waiting_for_response": True
                    }
                )

    @patch.object(WorkflowState, 'save')
    def test_pause_workflow_preserves_other_state_fields(self, mock_save, tmp_path, mock_workflow_state):
        """Test that pause_workflow doesn't modify other WorkflowState fields."""
        handler = WorkflowPauseHandler(tmp_path)

        # Capture original state values
        original_workflow_id = mock_workflow_state.workflow_id
        original_phase = mock_workflow_state.phase

        with patch('jean_claude.core.workflow_pause_handler.EventLogger'):
            handler.pause_workflow(mock_workflow_state, "Test pause")

            # Verify other fields weren't changed
            assert mock_workflow_state.workflow_id == original_workflow_id
            assert mock_workflow_state.phase == original_phase
            # Only waiting_for_response should be modified
            assert mock_workflow_state.waiting_for_response is True


class TestWorkflowPauseHandlerValidation:
    """Test WorkflowPauseHandler input validation and error handling."""

    def test_pause_workflow_validates_workflow_state_type(self, tmp_path):
        """Test that pause_workflow validates workflow_state is a WorkflowState object."""
        handler = WorkflowPauseHandler(tmp_path)

        # Test with invalid workflow_state type
        with pytest.raises((TypeError, ValueError)):
            handler.pause_workflow("not a workflow state", "reason")

        with pytest.raises((TypeError, ValueError)):
            handler.pause_workflow({"workflow_id": "test"}, "reason")

        with pytest.raises((TypeError, ValueError)):
            handler.pause_workflow(None, "reason")

    @patch.object(WorkflowState, 'save')
    def test_pause_workflow_validates_reason_type(self, mock_save, tmp_path, mock_workflow_state):
        """Test that pause_workflow validates reason is a string."""
        handler = WorkflowPauseHandler(tmp_path)

        # Test with invalid reason type
        with pytest.raises((TypeError, ValueError)):
            handler.pause_workflow(mock_workflow_state, None)

        with pytest.raises((TypeError, ValueError)):
            handler.pause_workflow(mock_workflow_state, 123)

        with pytest.raises((TypeError, ValueError)):
            handler.pause_workflow(mock_workflow_state, ["reason", "list"])

    @patch.object(WorkflowState, 'save')
    def test_pause_workflow_validates_reason_not_empty(self, mock_save, tmp_path, mock_workflow_state):
        """Test that pause_workflow validates reason is not empty."""
        handler = WorkflowPauseHandler(tmp_path)

        # Test with empty reason
        with pytest.raises((ValueError, TypeError)):
            handler.pause_workflow(mock_workflow_state, "")

        with pytest.raises((ValueError, TypeError)):
            handler.pause_workflow(mock_workflow_state, "   ")  # whitespace only

    def test_pause_handler_creation_validates_project_root(self, tmp_path):
        """Test that WorkflowPauseHandler validates project root."""
        # Test with None
        with pytest.raises((TypeError, ValueError)):
            WorkflowPauseHandler(None)

        # Test with empty string
        with pytest.raises((TypeError, ValueError)):
            WorkflowPauseHandler("")

        # Test with non-existent directory (should work - EventLogger will handle)
        non_existent = tmp_path / "does-not-exist"
        handler = WorkflowPauseHandler(non_existent)
        assert handler.project_root == non_existent

    @patch.object(WorkflowState, 'save')
    def test_pause_workflow_handles_save_errors_gracefully(self, mock_save, tmp_path, mock_workflow_state):
        """Test that pause_workflow handles state save errors gracefully."""
        handler = WorkflowPauseHandler(tmp_path)

        # Mock save to raise error
        mock_save.side_effect = PermissionError("Permission denied")

        with patch('jean_claude.core.workflow_pause_handler.EventLogger'):
            with pytest.raises(PermissionError):
                handler.pause_workflow(mock_workflow_state, "Test pause")


class TestWorkflowPauseHandlerIntegration:
    """Integration tests for WorkflowPauseHandler with realistic scenarios."""

    def test_pause_workflow_blocker_detected_scenario(self, tmp_path, workflow_state_factory):
        """Test complete workflow pause from blocker detection scenario."""
        # Create workflow state for implementation workflow
        workflow_state = workflow_state_factory(
            workflow_id="implementation-workflow",
            workflow_name="User Authentication Implementation",
            workflow_type="feature",
            phase="implementing"
        )

        handler = WorkflowPauseHandler(tmp_path)

        # Simulate test failure blocker requiring pause
        pause_reason = ("Test failures detected during authentication module implementation: "
                       "3 tests failed in test_auth.py - awaiting user guidance on resolution")

        with patch('jean_claude.core.workflow_pause_handler.EventLogger') as mock_event_logger:
            mock_logger_instance = Mock()
            mock_event_logger.return_value = mock_logger_instance

            handler.pause_workflow(workflow_state, pause_reason)

            # Verify workflow is now paused
            assert workflow_state.waiting_for_response is True

            # Verify pause event was logged correctly
            mock_logger_instance.emit.assert_called_once_with(
                workflow_id="implementation-workflow",
                event_type=EventType.WORKFLOW_PAUSED,
                data={
                    "reason": pause_reason,
                    "waiting_for_response": True
                }
            )

    def test_pause_workflow_with_real_event_logger(self, tmp_path, workflow_state_factory):
        """Test pause workflow with real EventLogger to verify integration."""
        # Create workflow state
        workflow_state = workflow_state_factory(
            workflow_id="test-workflow",
            workflow_name="Test Workflow",
            workflow_type="feature"
        )

        # Save state to disk so we can test the real save operation
        workflow_state.save(tmp_path)

        handler = WorkflowPauseHandler(tmp_path)

        # Pause the workflow
        pause_reason = "Integration test pause"
        handler.pause_workflow(workflow_state, pause_reason)

        # Verify state was updated and saved
        assert workflow_state.waiting_for_response is True

        # Verify event was written to JSONL file
        events_file = tmp_path / "agents" / "test-workflow" / "events.jsonl"
        assert events_file.exists()

        # Read and verify the event
        with open(events_file, 'r') as f:
            events = [json.loads(line.strip()) for line in f if line.strip()]

        # Should have at least one pause event
        pause_events = [e for e in events if e.get('event_type') == 'workflow.paused']
        assert len(pause_events) >= 1

        latest_pause_event = pause_events[-1]
        assert latest_pause_event['workflow_id'] == 'test-workflow'
        assert latest_pause_event['data']['reason'] == pause_reason
        assert latest_pause_event['data']['waiting_for_response'] is True

    def test_multiple_pause_resume_cycle(self, tmp_path, workflow_state_factory):
        """Test multiple pause operations on the same workflow."""
        workflow_state = workflow_state_factory(
            workflow_id="cyclic-workflow",
            phase="implementing"
        )

        handler = WorkflowPauseHandler(tmp_path)

        pause_reasons = [
            "First pause - test failure",
            "Second pause - build error",
            "Third pause - clarification needed"
        ]

        with patch('jean_claude.core.workflow_pause_handler.EventLogger') as mock_event_logger:
            mock_logger_instance = Mock()
            mock_event_logger.return_value = mock_logger_instance

            for i, reason in enumerate(pause_reasons):
                # Simulate workflow being resumed between pauses
                if i > 0:
                    workflow_state.waiting_for_response = False

                handler.pause_workflow(workflow_state, reason)

                # Verify state is paused
                assert workflow_state.waiting_for_response is True

            # Verify all pause events were logged
            assert mock_logger_instance.emit.call_count == len(pause_reasons)

            # Verify the calls had correct event types and data
            calls = mock_logger_instance.emit.call_args_list
            for i, reason in enumerate(pause_reasons):
                call_args = calls[i]
                assert call_args[1]['event_type'] == EventType.WORKFLOW_PAUSED
                assert call_args[1]['data']['reason'] == reason
                assert call_args[1]['data']['waiting_for_response'] is True