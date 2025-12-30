# ABOUTME: Tests for WorkflowResumeHandler that updates WorkflowState based on user decision and logs resume events
# ABOUTME: Consolidated test suite for workflow resume functionality

"""Tests for WorkflowResumeHandler.

Following the project's testing patterns with consolidated test coverage,
proper fixture usage, and comprehensive testing of resume functionality.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

import pytest

from jean_claude.core.workflow_resume_handler import WorkflowResumeHandler
from jean_claude.core.state import WorkflowState
from jean_claude.core.events import EventLogger, EventType
from jean_claude.core.response_parser import UserDecision, DecisionType


class TestWorkflowResumeHandlerCreation:
    """Test WorkflowResumeHandler instantiation and basic functionality."""

    def test_resume_handler_creation_with_project_root(self, tmp_path):
        """Test creating WorkflowResumeHandler with project root."""
        handler = WorkflowResumeHandler(tmp_path)
        assert isinstance(handler, WorkflowResumeHandler)
        assert handler.project_root == tmp_path

    def test_resume_handler_creation_with_string_path(self, tmp_path):
        """Test creating WorkflowResumeHandler with string project root."""
        handler = WorkflowResumeHandler(str(tmp_path))
        assert isinstance(handler, WorkflowResumeHandler)
        assert handler.project_root == Path(str(tmp_path))

    def test_resume_handler_has_resume_workflow_method(self, tmp_path):
        """Test that WorkflowResumeHandler has the required resume_workflow method."""
        handler = WorkflowResumeHandler(tmp_path)

        assert hasattr(handler, 'resume_workflow')
        assert callable(getattr(handler, 'resume_workflow'))


class TestWorkflowResumeHandlerFunctionality:
    """Test WorkflowResumeHandler resume functionality."""

    @patch.object(WorkflowState, 'save')
    def test_resume_workflow_sets_waiting_for_response_false(self, mock_save, tmp_path, mock_workflow_state):
        """Test that resume_workflow sets waiting_for_response=False in WorkflowState."""
        handler = WorkflowResumeHandler(tmp_path)

        # Set initial state to paused
        mock_workflow_state.waiting_for_response = True

        # Create user decision
        user_decision = UserDecision(
            decision_type=DecisionType.CONTINUE,
            message="User wants to continue with current approach",
            context={"original_content": "Please continue with the implementation"}
        )

        # Resume workflow
        handler.resume_workflow(mock_workflow_state, user_decision)

        # Verify state was updated
        assert mock_workflow_state.waiting_for_response is False
        # Verify save was called
        mock_save.assert_called_once_with(tmp_path)

    @patch.object(WorkflowState, 'save')
    def test_resume_workflow_logs_resume_event_to_events_jsonl(self, mock_save, tmp_path, mock_workflow_state):
        """Test that resume_workflow logs resume event to events.jsonl file."""
        handler = WorkflowResumeHandler(tmp_path)
        mock_workflow_state.waiting_for_response = True

        # Create user decision
        user_decision = UserDecision(
            decision_type=DecisionType.FIX,
            message="User wants to fix this issue",
            context={"original_content": "Please fix the authentication logic"}
        )

        # Mock EventLogger
        with patch('jean_claude.core.workflow_resume_handler.EventLogger') as mock_event_logger:
            mock_logger_instance = Mock()
            mock_event_logger.return_value = mock_logger_instance

            # Resume workflow
            handler.resume_workflow(mock_workflow_state, user_decision)

            # Verify EventLogger was created with correct project root
            mock_event_logger.assert_called_once_with(tmp_path)

            # Verify event was emitted
            mock_logger_instance.emit.assert_called_once_with(
                workflow_id=mock_workflow_state.workflow_id,
                event_type=EventType.WORKFLOW_RESUMED,
                data={
                    "user_decision": {
                        "decision_type": DecisionType.FIX.value,
                        "message": "User wants to fix this issue",
                        "context": {"original_content": "Please fix the authentication logic"}
                    },
                    "waiting_for_response": False
                }
            )

    @patch.object(WorkflowState, 'save')
    def test_resume_workflow_with_different_decision_types(self, mock_save, tmp_path, mock_workflow_state):
        """Test resuming workflow with different user decision types."""
        handler = WorkflowResumeHandler(tmp_path)

        test_decisions = [
            UserDecision(
                decision_type=DecisionType.SKIP,
                message="User decided to skip this blocker",
                context={"original_content": "Skip this test for now"}
            ),
            UserDecision(
                decision_type=DecisionType.FIX,
                message="User wants to fix this issue",
                context={"original_content": "Fix the authentication error"}
            ),
            UserDecision(
                decision_type=DecisionType.CONTINUE,
                message="User wants to continue with current approach",
                context={"original_content": "Continue with implementation"}
            ),
            UserDecision(
                decision_type=DecisionType.ABORT,
                message="User wants to abort the workflow",
                context={"original_content": "Abort this workflow"}
            ),
        ]

        with patch('jean_claude.core.workflow_resume_handler.EventLogger') as mock_event_logger:
            mock_logger_instance = Mock()
            mock_event_logger.return_value = mock_logger_instance

            for decision in test_decisions:
                # Reset mocks
                mock_logger_instance.reset_mock()
                mock_workflow_state.waiting_for_response = True

                # Resume with this decision
                handler.resume_workflow(mock_workflow_state, decision)

                # Verify state was set
                assert mock_workflow_state.waiting_for_response is False

                # Verify event was logged with correct decision
                mock_logger_instance.emit.assert_called_once_with(
                    workflow_id=mock_workflow_state.workflow_id,
                    event_type=EventType.WORKFLOW_RESUMED,
                    data={
                        "user_decision": {
                            "decision_type": decision.decision_type.value,
                            "message": decision.message,
                            "context": decision.context
                        },
                        "waiting_for_response": False
                    }
                )

    @patch.object(WorkflowState, 'save')
    def test_resume_workflow_preserves_other_state_fields(self, mock_save, tmp_path, mock_workflow_state):
        """Test that resume_workflow doesn't modify other WorkflowState fields."""
        handler = WorkflowResumeHandler(tmp_path)

        # Capture original state values
        original_workflow_id = mock_workflow_state.workflow_id
        original_phase = mock_workflow_state.phase
        mock_workflow_state.waiting_for_response = True

        user_decision = UserDecision(
            decision_type=DecisionType.CONTINUE,
            message="Continue workflow",
            context={}
        )

        with patch('jean_claude.core.workflow_resume_handler.EventLogger'):
            handler.resume_workflow(mock_workflow_state, user_decision)

            # Verify other fields weren't changed
            assert mock_workflow_state.workflow_id == original_workflow_id
            assert mock_workflow_state.phase == original_phase
            # Only waiting_for_response should be modified
            assert mock_workflow_state.waiting_for_response is False


class TestWorkflowResumeHandlerValidation:
    """Test WorkflowResumeHandler input validation and error handling."""

    def test_resume_workflow_validates_workflow_state_type(self, tmp_path):
        """Test that resume_workflow validates workflow_state is a WorkflowState object."""
        handler = WorkflowResumeHandler(tmp_path)

        user_decision = UserDecision(
            decision_type=DecisionType.CONTINUE,
            message="Continue",
            context={}
        )

        # Test with invalid workflow_state type
        with pytest.raises((TypeError, ValueError)):
            handler.resume_workflow("not a workflow state", user_decision)

        with pytest.raises((TypeError, ValueError)):
            handler.resume_workflow({"workflow_id": "test"}, user_decision)

        with pytest.raises((TypeError, ValueError)):
            handler.resume_workflow(None, user_decision)

    @patch.object(WorkflowState, 'save')
    def test_resume_workflow_validates_user_decision_type(self, mock_save, tmp_path, mock_workflow_state):
        """Test that resume_workflow validates user_decision is a UserDecision object."""
        handler = WorkflowResumeHandler(tmp_path)
        mock_workflow_state.waiting_for_response = True

        # Test with invalid user_decision type
        with pytest.raises((TypeError, ValueError)):
            handler.resume_workflow(mock_workflow_state, "not a user decision")

        with pytest.raises((TypeError, ValueError)):
            handler.resume_workflow(mock_workflow_state, {"decision": "continue"})

        with pytest.raises((TypeError, ValueError)):
            handler.resume_workflow(mock_workflow_state, None)

    def test_resume_handler_creation_validates_project_root(self, tmp_path):
        """Test that WorkflowResumeHandler validates project root."""
        # Test with None
        with pytest.raises((TypeError, ValueError)):
            WorkflowResumeHandler(None)

        # Test with empty string
        with pytest.raises((TypeError, ValueError)):
            WorkflowResumeHandler("")

        # Test with non-existent directory (should work - EventLogger will handle)
        non_existent = tmp_path / "does-not-exist"
        handler = WorkflowResumeHandler(non_existent)
        assert handler.project_root == non_existent

    @patch.object(WorkflowState, 'save')
    def test_resume_workflow_handles_save_errors_gracefully(self, mock_save, tmp_path, mock_workflow_state):
        """Test that resume_workflow handles state save errors gracefully."""
        handler = WorkflowResumeHandler(tmp_path)
        mock_workflow_state.waiting_for_response = True

        # Mock save to raise error
        mock_save.side_effect = PermissionError("Permission denied")

        user_decision = UserDecision(
            decision_type=DecisionType.CONTINUE,
            message="Continue",
            context={}
        )

        with patch('jean_claude.core.workflow_resume_handler.EventLogger'):
            with pytest.raises(PermissionError):
                handler.resume_workflow(mock_workflow_state, user_decision)


class TestWorkflowResumeHandlerIntegration:
    """Integration tests for WorkflowResumeHandler with realistic scenarios."""

    def test_resume_workflow_from_test_failure_scenario(self, tmp_path, workflow_state_factory):
        """Test complete workflow resume from test failure blocker scenario."""
        # Create workflow state for implementation workflow that was paused
        workflow_state = workflow_state_factory(
            workflow_id="implementation-workflow",
            workflow_name="User Authentication Implementation",
            workflow_type="feature",
            phase="implementing"
        )
        workflow_state.waiting_for_response = True

        handler = WorkflowResumeHandler(tmp_path)

        # Simulate user decision to fix the test failures
        user_decision = UserDecision(
            decision_type=DecisionType.FIX,
            message="User wants to fix this issue",
            context={
                "original_content": ("I reviewed the test failures. Please fix the authentication logic "
                                   "in src/auth.py. Focus on the password validation issues."),
                "decision_confidence": "high"
            }
        )

        with patch('jean_claude.core.workflow_resume_handler.EventLogger') as mock_event_logger:
            mock_logger_instance = Mock()
            mock_event_logger.return_value = mock_logger_instance

            handler.resume_workflow(workflow_state, user_decision)

            # Verify workflow is now resumed
            assert workflow_state.waiting_for_response is False

            # Verify resume event was logged correctly
            mock_logger_instance.emit.assert_called_once_with(
                workflow_id="implementation-workflow",
                event_type=EventType.WORKFLOW_RESUMED,
                data={
                    "user_decision": {
                        "decision_type": "fix",
                        "message": "User wants to fix this issue",
                        "context": {
                            "original_content": ("I reviewed the test failures. Please fix the authentication logic "
                                               "in src/auth.py. Focus on the password validation issues."),
                            "decision_confidence": "high"
                        }
                    },
                    "waiting_for_response": False
                }
            )

    def test_resume_workflow_with_real_event_logger(self, tmp_path, workflow_state_factory):
        """Test resume workflow with real EventLogger to verify integration."""
        # Create workflow state
        workflow_state = workflow_state_factory(
            workflow_id="test-workflow",
            workflow_name="Test Workflow",
            workflow_type="feature"
        )
        workflow_state.waiting_for_response = True

        # Save state to disk so we can test the real save operation
        workflow_state.save(tmp_path)

        handler = WorkflowResumeHandler(tmp_path)

        # Create user decision
        user_decision = UserDecision(
            decision_type=DecisionType.SKIP,
            message="User decided to skip this blocker",
            context={"original_content": "Skip this test for now and continue"}
        )

        # Resume the workflow
        handler.resume_workflow(workflow_state, user_decision)

        # Verify state was updated and saved
        assert workflow_state.waiting_for_response is False

        # Verify event was written to JSONL file
        events_file = tmp_path / "agents" / "test-workflow" / "events.jsonl"
        assert events_file.exists()

        # Read and verify the event
        with open(events_file, 'r') as f:
            events = [json.loads(line.strip()) for line in f if line.strip()]

        # Should have at least one resume event
        resume_events = [e for e in events if e.get('event_type') == 'workflow.resumed']
        assert len(resume_events) >= 1

        latest_resume_event = resume_events[-1]
        assert latest_resume_event['workflow_id'] == 'test-workflow'
        assert latest_resume_event['data']['user_decision']['decision_type'] == 'skip'
        assert latest_resume_event['data']['waiting_for_response'] is False

    def test_multiple_pause_resume_cycle(self, tmp_path, workflow_state_factory):
        """Test multiple pause/resume operations on the same workflow."""
        workflow_state = workflow_state_factory(
            workflow_id="cyclic-workflow",
            phase="implementing"
        )

        handler = WorkflowResumeHandler(tmp_path)

        resume_decisions = [
            UserDecision(
                decision_type=DecisionType.FIX,
                message="Fix first issue",
                context={"original_content": "Fix the test failure"}
            ),
            UserDecision(
                decision_type=DecisionType.SKIP,
                message="Skip second issue",
                context={"original_content": "Skip the build warning"}
            ),
            UserDecision(
                decision_type=DecisionType.CONTINUE,
                message="Continue third issue",
                context={"original_content": "Continue with implementation"}
            ),
        ]

        with patch('jean_claude.core.workflow_resume_handler.EventLogger') as mock_event_logger:
            mock_logger_instance = Mock()
            mock_event_logger.return_value = mock_logger_instance

            for i, decision in enumerate(resume_decisions):
                # Simulate workflow being paused before each resume
                workflow_state.waiting_for_response = True

                handler.resume_workflow(workflow_state, decision)

                # Verify state is resumed
                assert workflow_state.waiting_for_response is False

            # Verify all resume events were logged
            assert mock_logger_instance.emit.call_count == len(resume_decisions)

            # Verify the calls had correct event types and data
            calls = mock_logger_instance.emit.call_args_list
            for i, decision in enumerate(resume_decisions):
                call_args = calls[i]
                assert call_args[1]['event_type'] == EventType.WORKFLOW_RESUMED
                assert call_args[1]['data']['user_decision']['decision_type'] == decision.decision_type.value
                assert call_args[1]['data']['waiting_for_response'] is False

    def test_resume_workflow_with_unclear_decision(self, tmp_path, workflow_state_factory):
        """Test resuming workflow when user decision is unclear."""
        workflow_state = workflow_state_factory(
            workflow_id="unclear-decision-workflow"
        )
        workflow_state.waiting_for_response = True

        handler = WorkflowResumeHandler(tmp_path)

        # Create unclear decision
        unclear_decision = UserDecision(
            decision_type=DecisionType.UNCLEAR,
            message="User decision is unclear or ambiguous",
            context={
                "original_content": "I'm not sure what to do here",
                "decision_confidence": "low"
            }
        )

        with patch('jean_claude.core.workflow_resume_handler.EventLogger') as mock_event_logger:
            mock_logger_instance = Mock()
            mock_event_logger.return_value = mock_logger_instance

            handler.resume_workflow(workflow_state, unclear_decision)

            # Even unclear decisions should resume the workflow
            assert workflow_state.waiting_for_response is False

            # Verify event was logged with unclear decision
            mock_logger_instance.emit.assert_called_once_with(
                workflow_id=workflow_state.workflow_id,
                event_type=EventType.WORKFLOW_RESUMED,
                data={
                    "user_decision": {
                        "decision_type": "unclear",
                        "message": "User decision is unclear or ambiguous",
                        "context": {
                            "original_content": "I'm not sure what to do here",
                            "decision_confidence": "low"
                        }
                    },
                    "waiting_for_response": False
                }
            )

    def test_end_to_end_pause_resume_workflow(self, tmp_path, workflow_state_factory):
        """Test complete end-to-end pause and resume cycle."""
        from jean_claude.core.workflow_pause_handler import WorkflowPauseHandler

        # Create workflow state
        workflow_state = workflow_state_factory(
            workflow_id="e2e-test-workflow",
            workflow_name="End-to-End Test",
            workflow_type="feature"
        )

        pause_handler = WorkflowPauseHandler(tmp_path)
        resume_handler = WorkflowResumeHandler(tmp_path)

        # Step 1: Pause the workflow
        pause_reason = "Test failures detected - requires user intervention"
        pause_handler.pause_workflow(workflow_state, pause_reason)
        assert workflow_state.waiting_for_response is True

        # Step 2: User provides decision
        user_decision = UserDecision(
            decision_type=DecisionType.FIX,
            message="User wants to fix this issue",
            context={
                "original_content": "Please fix the authentication tests",
                "decision_confidence": "high"
            }
        )

        # Step 3: Resume the workflow
        resume_handler.resume_workflow(workflow_state, user_decision)
        assert workflow_state.waiting_for_response is False

        # Verify events were written to disk
        events_file = tmp_path / "agents" / "e2e-test-workflow" / "events.jsonl"
        assert events_file.exists()

        with open(events_file, 'r') as f:
            events = [json.loads(line.strip()) for line in f if line.strip()]

        # Should have both pause and resume events
        pause_events = [e for e in events if e.get('event_type') == 'workflow.paused']
        resume_events = [e for e in events if e.get('event_type') == 'workflow.resumed']

        assert len(pause_events) >= 1
        assert len(resume_events) >= 1

        # Verify pause event
        latest_pause = pause_events[-1]
        assert latest_pause['data']['reason'] == pause_reason
        assert latest_pause['data']['waiting_for_response'] is True

        # Verify resume event
        latest_resume = resume_events[-1]
        assert latest_resume['data']['user_decision']['decision_type'] == 'fix'
        assert latest_resume['data']['waiting_for_response'] is False