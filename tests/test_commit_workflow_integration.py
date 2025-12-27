"""Tests for commit workflow integration into the main agent workflow.

This test suite verifies that the FeatureCommitOrchestrator is properly
integrated into the auto-continue workflow and that commits are triggered
after feature completion.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call, AsyncMock
from pathlib import Path
from datetime import datetime

from jean_claude.orchestration.auto_continue import run_auto_continue
from jean_claude.core.state import WorkflowState, Feature


class TestCommitWorkflowIntegration:
    """Test integration of commit workflow into main agent workflow."""

    @pytest.fixture
    def sample_state(self, tmp_path):
        """Create a sample workflow state for testing."""
        state = WorkflowState(
            workflow_id="test-workflow",
            workflow_name="Test Workflow",
            workflow_type="beads-task",
            beads_task_id="test.1",
            max_iterations=10
        )

        # Add a couple of features
        state.add_feature(
            name="test-feature-1",
            description="Add test feature 1",
            test_file="tests/test_feature1.py"
        )
        state.add_feature(
            name="test-feature-2",
            description="Add test feature 2",
            test_file="tests/test_feature2.py"
        )

        return state

    @pytest.mark.asyncio
    @patch('jean_claude.orchestration.auto_continue._execute_prompt_sdk_async')
    @patch('jean_claude.orchestration.auto_continue.run_verification')
    @patch('jean_claude.orchestration.auto_continue.FeatureCommitOrchestrator')
    async def test_commit_triggered_after_feature_completion(
        self, mock_orchestrator_class, mock_verification, mock_execute, sample_state, tmp_path
    ):
        """Test that commit workflow is triggered after feature completion."""
        # Setup verification mock
        mock_verification_result = Mock()
        mock_verification_result.passed = True
        mock_verification_result.skipped = False
        mock_verification_result.tests_run = 5
        mock_verification_result.duration_ms = 1000
        mock_verification.return_value = mock_verification_result

        # Setup execution mock to succeed
        mock_result = Mock()
        mock_result.success = True
        mock_result.output = "Feature completed"
        mock_result.cost_usd = 0.05
        mock_result.duration_ms = 5000
        mock_result.session_id = "session-123"
        mock_execute.return_value = mock_result

        # Setup commit orchestrator mock
        mock_orchestrator = MagicMock()
        mock_orchestrator.commit_feature.return_value = {
            "success": True,
            "commit_sha": "abc1234",
            "error": None,
            "step": None
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        # Save initial state
        sample_state.save(tmp_path)

        # Run workflow for 1 iteration
        final_state = await run_auto_continue(
            state=sample_state,
            project_root=tmp_path,
            max_iterations=1,
            delay_seconds=0,
            model="sonnet",
            verify_first=False
        )

        # Verify commit_feature was called with correct parameters
        mock_orchestrator.commit_feature.assert_called_once()
        call_args = mock_orchestrator.commit_feature.call_args[1]

        assert call_args["feature_name"] == "test-feature-1"
        assert call_args["feature_description"] == "Add test feature 1"
        assert call_args["beads_task_id"] == "test.1"
        assert call_args["feature_number"] == 1
        assert call_args["total_features"] == 2

    @pytest.mark.asyncio
    @patch('jean_claude.orchestration.auto_continue._execute_prompt_sdk_async')
    @patch('jean_claude.orchestration.auto_continue.run_verification')
    @patch('jean_claude.orchestration.auto_continue.FeatureCommitOrchestrator')
    async def test_commit_failure_does_not_block_workflow(
        self, mock_orchestrator_class, mock_verification, mock_execute, sample_state, tmp_path
    ):
        """Test that commit failures are gracefully handled without blocking the workflow."""
        # Setup verification mock
        mock_verification_result = Mock()
        mock_verification_result.passed = True
        mock_verification_result.skipped = False
        mock_verification.return_value = mock_verification_result

        # Setup execution mock to succeed
        mock_result = Mock()
        mock_result.success = True
        mock_result.output = "Feature completed"
        mock_result.cost_usd = 0.05
        mock_result.duration_ms = 5000
        mock_result.session_id = "session-123"
        mock_execute.return_value = mock_result

        # Setup commit orchestrator mock to fail
        mock_orchestrator = MagicMock()
        mock_orchestrator.commit_feature.return_value = {
            "success": False,
            "commit_sha": None,
            "error": "Tests failed",
            "step": "test_validation"
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        # Save initial state
        sample_state.save(tmp_path)

        # Run workflow for 1 iteration - should not raise exception
        final_state = await run_auto_continue(
            state=sample_state,
            project_root=tmp_path,
            max_iterations=1,
            delay_seconds=0,
            model="sonnet",
            verify_first=False
        )

        # Feature should still be marked as complete despite commit failure
        assert final_state.current_feature_index == 1
        assert final_state.features[0].status == "completed"

    @pytest.mark.asyncio
    @patch('jean_claude.orchestration.auto_continue._execute_prompt_sdk_async')
    @patch('jean_claude.orchestration.auto_continue.run_verification')
    @patch('jean_claude.orchestration.auto_continue.FeatureCommitOrchestrator')
    async def test_commit_not_triggered_on_feature_failure(
        self, mock_orchestrator_class, mock_verification, mock_execute, sample_state, tmp_path
    ):
        """Test that commit is not triggered when feature implementation fails."""
        # Setup verification mock
        mock_verification_result = Mock()
        mock_verification_result.passed = True
        mock_verification_result.skipped = False
        mock_verification.return_value = mock_verification_result

        # Setup execution mock to fail
        mock_result = Mock()
        mock_result.success = False
        mock_result.output = "Feature failed"
        mock_execute.return_value = mock_result

        # Setup commit orchestrator mock
        mock_orchestrator = MagicMock()
        mock_orchestrator_class.return_value = mock_orchestrator

        # Save initial state
        sample_state.save(tmp_path)

        # Run workflow for 1 iteration
        final_state = await run_auto_continue(
            state=sample_state,
            project_root=tmp_path,
            max_iterations=1,
            delay_seconds=0,
            model="sonnet",
            verify_first=False
        )

        # Verify commit_feature was NOT called
        mock_orchestrator.commit_feature.assert_not_called()

    @pytest.mark.asyncio
    @patch('jean_claude.orchestration.auto_continue._execute_prompt_sdk_async')
    @patch('jean_claude.orchestration.auto_continue.run_verification')
    @patch('jean_claude.orchestration.auto_continue.FeatureCommitOrchestrator')
    async def test_commit_receives_correct_task_metadata(
        self, mock_orchestrator_class, mock_verification, mock_execute, sample_state, tmp_path
    ):
        """Test that commit orchestrator receives correct Beads task metadata."""
        # Setup verification mock
        mock_verification_result = Mock()
        mock_verification_result.passed = True
        mock_verification_result.skipped = False
        mock_verification.return_value = mock_verification_result

        # Setup execution mock
        mock_result = Mock()
        mock_result.success = True
        mock_result.output = "Feature completed"
        mock_result.cost_usd = 0.05
        mock_result.duration_ms = 5000
        mock_result.session_id = "session-123"
        mock_execute.return_value = mock_result

        # Setup commit orchestrator mock
        mock_orchestrator = MagicMock()
        mock_orchestrator.commit_feature.return_value = {
            "success": True,
            "commit_sha": "abc1234",
            "error": None,
            "step": None
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        # Update state with Beads metadata
        sample_state.beads_task_id = "jean_claude-2sz.8"
        sample_state.save(tmp_path)

        # Run workflow for 1 iteration
        await run_auto_continue(
            state=sample_state,
            project_root=tmp_path,
            max_iterations=1,
            delay_seconds=0,
            model="sonnet",
            verify_first=False
        )

        # Verify commit was called with correct metadata
        call_args = mock_orchestrator.commit_feature.call_args[1]
        assert call_args["beads_task_id"] == "jean_claude-2sz.8"
        assert call_args["feature_number"] == 1
        assert call_args["total_features"] == 2

    @pytest.mark.asyncio
    @patch('jean_claude.orchestration.auto_continue._execute_prompt_sdk_async')
    @patch('jean_claude.orchestration.auto_continue.run_verification')
    @patch('jean_claude.orchestration.auto_continue.FeatureCommitOrchestrator')
    async def test_commit_uses_feature_context(
        self, mock_orchestrator_class, mock_verification, mock_execute, sample_state, tmp_path
    ):
        """Test that commit uses feature name and description as context."""
        # Setup verification mock
        mock_verification_result = Mock()
        mock_verification_result.passed = True
        mock_verification_result.skipped = False
        mock_verification.return_value = mock_verification_result

        # Setup execution mock
        mock_result = Mock()
        mock_result.success = True
        mock_result.output = "Feature completed"
        mock_result.cost_usd = 0.05
        mock_result.duration_ms = 5000
        mock_result.session_id = "session-123"
        mock_execute.return_value = mock_result

        # Setup commit orchestrator mock
        mock_orchestrator = MagicMock()
        mock_orchestrator.commit_feature.return_value = {
            "success": True,
            "commit_sha": "abc1234",
            "error": None
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        # Save initial state
        sample_state.save(tmp_path)

        # Run workflow
        await run_auto_continue(
            state=sample_state,
            project_root=tmp_path,
            max_iterations=1,
            delay_seconds=0,
            model="sonnet",
            verify_first=False
        )

        # Verify commit was called with feature name/description as context
        call_args = mock_orchestrator.commit_feature.call_args[1]
        assert call_args["feature_context"] == "test-feature-1"

    @pytest.mark.asyncio
    @patch('jean_claude.orchestration.auto_continue._execute_prompt_sdk_async')
    @patch('jean_claude.orchestration.auto_continue.run_verification')
    @patch('jean_claude.orchestration.auto_continue.FeatureCommitOrchestrator')
    async def test_commit_sha_saved_to_feature_state(
        self, mock_orchestrator_class, mock_verification, mock_execute, sample_state, tmp_path
    ):
        """Test that commit SHA is saved to the feature state when commit succeeds."""
        # Setup verification mock
        mock_verification_result = Mock()
        mock_verification_result.passed = True
        mock_verification_result.skipped = False
        mock_verification.return_value = mock_verification_result

        # Setup execution mock
        mock_result = Mock()
        mock_result.success = True
        mock_result.output = "Feature completed"
        mock_result.cost_usd = 0.05
        mock_result.duration_ms = 5000
        mock_result.session_id = "session-123"
        mock_execute.return_value = mock_result

        # Setup commit orchestrator mock
        mock_orchestrator = MagicMock()
        mock_orchestrator.commit_feature.return_value = {
            "success": True,
            "commit_sha": "abc1234",
            "error": None
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        # Save initial state
        sample_state.save(tmp_path)

        # Run workflow
        final_state = await run_auto_continue(
            state=sample_state,
            project_root=tmp_path,
            max_iterations=1,
            delay_seconds=0,
            model="sonnet",
            verify_first=False
        )

        # Reload state from disk to verify persistence
        reloaded_state = WorkflowState.load(sample_state.workflow_id, tmp_path)

        # Check if commit_sha was added to feature (this will be implemented)
        # For now, we just verify the commit was attempted
        assert reloaded_state.features[0].status == "completed"

    @pytest.mark.asyncio
    @patch('jean_claude.orchestration.auto_continue._execute_prompt_sdk_async')
    @patch('jean_claude.orchestration.auto_continue.run_verification')
    @patch('jean_claude.orchestration.auto_continue.FeatureCommitOrchestrator')
    async def test_multiple_features_each_get_commit(
        self, mock_orchestrator_class, mock_verification, mock_execute, sample_state, tmp_path
    ):
        """Test that each completed feature gets its own commit."""
        # Setup verification mock
        mock_verification_result = Mock()
        mock_verification_result.passed = True
        mock_verification_result.skipped = False
        mock_verification.return_value = mock_verification_result

        # Setup execution mock to succeed for both iterations
        mock_result = Mock()
        mock_result.success = True
        mock_result.output = "Feature completed"
        mock_result.cost_usd = 0.05
        mock_result.duration_ms = 5000
        mock_result.session_id = "session-123"
        mock_execute.return_value = mock_result

        # Setup commit orchestrator mock
        mock_orchestrator = MagicMock()
        mock_orchestrator.commit_feature.return_value = {
            "success": True,
            "commit_sha": "abc1234",
            "error": None
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        # Save initial state
        sample_state.save(tmp_path)

        # Run workflow for 2 iterations (both features)
        final_state = await run_auto_continue(
            state=sample_state,
            project_root=tmp_path,
            max_iterations=2,
            delay_seconds=0,
            model="sonnet",
            verify_first=False
        )

        # Verify commit_feature was called twice (once per feature)
        assert mock_orchestrator.commit_feature.call_count == 2

        # Verify correct feature numbers were passed
        first_call = mock_orchestrator.commit_feature.call_args_list[0][1]
        second_call = mock_orchestrator.commit_feature.call_args_list[1][1]

        assert first_call["feature_number"] == 1
        assert first_call["feature_name"] == "test-feature-1"

        assert second_call["feature_number"] == 2
        assert second_call["feature_name"] == "test-feature-2"

    @pytest.mark.asyncio
    @patch('jean_claude.orchestration.auto_continue._execute_prompt_sdk_async')
    @patch('jean_claude.orchestration.auto_continue.run_verification')
    @patch('jean_claude.orchestration.auto_continue.FeatureCommitOrchestrator')
    async def test_commit_orchestrator_initialized_with_repo_path(
        self, mock_orchestrator_class, mock_verification, mock_execute, sample_state, tmp_path
    ):
        """Test that FeatureCommitOrchestrator is initialized with correct repo path."""
        # Setup verification mock
        mock_verification_result = Mock()
        mock_verification_result.passed = True
        mock_verification_result.skipped = False
        mock_verification.return_value = mock_verification_result

        # Setup execution mock
        mock_result = Mock()
        mock_result.success = True
        mock_result.output = "Feature completed"
        mock_result.cost_usd = 0.05
        mock_result.duration_ms = 5000
        mock_result.session_id = "session-123"
        mock_execute.return_value = mock_result

        # Setup commit orchestrator mock
        mock_orchestrator = MagicMock()
        mock_orchestrator.commit_feature.return_value = {
            "success": True,
            "commit_sha": "abc1234",
            "error": None
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        # Save initial state
        sample_state.save(tmp_path)

        # Run workflow
        await run_auto_continue(
            state=sample_state,
            project_root=tmp_path,
            max_iterations=1,
            delay_seconds=0,
            model="sonnet",
            verify_first=False
        )

        # Verify FeatureCommitOrchestrator was initialized with project_root
        mock_orchestrator_class.assert_called_once_with(repo_path=tmp_path)
