# ABOUTME: Tests for auto-continue orchestrator
# ABOUTME: Verifies workflow loops, state persistence, and feature completion

"""Tests for auto-continue orchestrator."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jean_claude.core.state import WorkflowState, Feature
from jean_claude.core.agent import ExecutionResult
from jean_claude.orchestration.auto_continue import (
    run_auto_continue,
    initialize_workflow,
    resume_workflow,
    build_feature_prompt,
    AutoContinueError,
)


# Fixtures moved to tests/orchestration/conftest.py:
# - mock_project_root: Creates temp project with agents/ directory
# - sample_workflow_state: Pre-configured state with 3 features


class TestBuildFeaturePrompt:
    """Test prompt generation for features."""

    def test_build_feature_prompt_basic(self, sample_workflow_state, mock_project_root):
        """Test basic prompt generation."""
        feature = sample_workflow_state.features[0]
        prompt = build_feature_prompt(feature, sample_workflow_state, mock_project_root)

        # Verify prompt contains critical elements
        assert "Feature 1" in prompt
        assert "Implement authentication" in prompt
        assert "tests/test_auth.py" in prompt
        assert "GET YOUR BEARINGS" in prompt
        assert "IMPLEMENT FEATURE" in prompt
        assert "UPDATE STATE" in prompt
        assert str(mock_project_root / "agents" / "test-abc123" / "state.json") in prompt

    def test_build_feature_prompt_includes_warnings(
        self, sample_workflow_state, mock_project_root
    ):
        """Test that prompt includes critical warnings."""
        feature = sample_workflow_state.features[0]
        prompt = build_feature_prompt(feature, sample_workflow_state, mock_project_root)

        assert "⚠️" in prompt
        assert "NEVER skip" in prompt
        assert "NEVER modify the feature list" in prompt
        assert "ALWAYS save state" in prompt

    def test_build_feature_prompt_without_test_file(
        self, sample_workflow_state, mock_project_root
    ):
        """Test prompt when feature has no test file."""
        feature = Feature(name="No Test Feature", description="A feature without tests")
        prompt = build_feature_prompt(feature, sample_workflow_state, mock_project_root)

        # Should not mention specific test file
        assert "tests/" not in prompt or "should be in:" not in prompt


class TestInitializeWorkflow:
    """Test workflow initialization."""

    @pytest.mark.asyncio
    async def test_initialize_workflow_basic(self, mock_project_root):
        """Test basic workflow initialization."""
        features = [
            ("Auth", "Implement auth", "tests/test_auth.py"),
            ("Profile", "User profile", "tests/test_profile.py"),
            ("Logout", "Logout feature", None),
        ]

        state = await initialize_workflow(
            workflow_id="test-init",
            workflow_name="Test Init",
            workflow_type="feature",
            features=features,
            project_root=mock_project_root,
            max_iterations=20,
        )

        assert state.workflow_id == "test-init"
        assert state.workflow_name == "Test Init"
        assert state.workflow_type == "feature"
        assert len(state.features) == 3
        assert state.max_iterations == 20
        assert state.current_feature_index == 0
        assert state.iteration_count == 0

        # Verify features
        assert state.features[0].name == "Auth"
        assert state.features[0].test_file == "tests/test_auth.py"
        assert state.features[2].test_file is None

    @pytest.mark.asyncio
    async def test_initialize_workflow_saves_state(self, mock_project_root):
        """Test that initialization saves state to disk."""
        features = [("Test", "Test feature", None)]

        state = await initialize_workflow(
            workflow_id="test-save",
            workflow_name="Test Save",
            workflow_type="chore",
            features=features,
            project_root=mock_project_root,
        )

        # Verify state file exists
        state_file = mock_project_root / "agents" / "test-save" / "state.json"
        assert state_file.exists()

        # Verify can reload
        loaded_state = WorkflowState.load("test-save", mock_project_root)
        assert loaded_state.workflow_id == state.workflow_id
        assert len(loaded_state.features) == 1


class TestResumeWorkflow:
    """Test workflow resumption."""

    def test_resume_workflow_basic(self, sample_workflow_state, mock_project_root):
        """Test basic workflow resumption."""
        # Mark first feature as complete
        sample_workflow_state.mark_feature_complete()
        sample_workflow_state.save(mock_project_root)

        # Resume
        resumed_state = resume_workflow("test-abc123", mock_project_root)

        assert resumed_state.workflow_id == "test-abc123"
        assert resumed_state.current_feature_index == 1
        assert resumed_state.features[0].status == "completed"

    def test_resume_workflow_not_found(self, mock_project_root):
        """Test resuming non-existent workflow."""
        with pytest.raises(AutoContinueError, match="not found"):
            resume_workflow("nonexistent-workflow", mock_project_root)


class TestRunAutoContinue:
    """Test auto-continue orchestration."""

    @pytest.mark.asyncio
    async def test_run_auto_continue_single_feature(
        self, sample_workflow_state, mock_project_root
    ):
        """Test auto-continue with single feature."""
        # Only one feature
        state = WorkflowState(
            workflow_id="single-feature",
            workflow_name="Single",
            workflow_type="chore",
            max_iterations=5,
        )
        state.add_feature("Test Feature", "A test feature", None)
        state.save(mock_project_root)

        # Mock successful execution
        mock_result = ExecutionResult(
            output="Feature completed",
            success=True,
            session_id="session-123",
            cost_usd=0.05,
            duration_ms=1000,
        )

        with patch(
            "jean_claude.orchestration.auto_continue._execute_prompt_sdk_async",
            new=AsyncMock(return_value=mock_result),
        ):
            final_state = await run_auto_continue(
                state=state,
                project_root=mock_project_root,
                max_iterations=5,
                delay_seconds=0.1,
                model="haiku",
            )

        # Verify completion
        assert final_state.is_complete()
        assert final_state.current_feature_index == 1
        assert final_state.iteration_count == 1
        assert final_state.features[0].status == "completed"
        assert final_state.total_cost_usd == 0.05

    @pytest.mark.asyncio
    async def test_run_auto_continue_multiple_features(
        self, sample_workflow_state, mock_project_root
    ):
        """Test auto-continue with multiple features."""
        # Mock successful execution
        mock_result = ExecutionResult(
            output="Feature completed",
            success=True,
            session_id="session-123",
            cost_usd=0.05,
            duration_ms=1000,
        )

        with patch(
            "jean_claude.orchestration.auto_continue._execute_prompt_sdk_async",
            new=AsyncMock(return_value=mock_result),
        ):
            final_state = await run_auto_continue(
                state=sample_workflow_state,
                project_root=mock_project_root,
                max_iterations=10,
                delay_seconds=0.1,
                model="sonnet",
            )

        # Verify all features completed
        assert final_state.is_complete()
        assert final_state.current_feature_index == 3
        assert final_state.iteration_count == 3
        assert all(f.status == "completed" for f in final_state.features)
        assert abs(final_state.total_cost_usd - 0.15) < 0.001  # 3 features * $0.05 (with float tolerance)

    @pytest.mark.asyncio
    async def test_run_auto_continue_feature_failure(
        self, sample_workflow_state, mock_project_root
    ):
        """Test auto-continue when a feature fails."""
        # Mock failure on second feature
        call_count = 0

        async def mock_execute(request, max_retries):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ExecutionResult(output="Success", success=True, cost_usd=0.05)
            else:
                return ExecutionResult(
                    output="Feature failed", success=False, cost_usd=0.03
                )

        with patch(
            "jean_claude.orchestration.auto_continue._execute_prompt_sdk_async",
            new=mock_execute,
        ):
            final_state = await run_auto_continue(
                state=sample_workflow_state,
                project_root=mock_project_root,
                max_iterations=10,
                delay_seconds=0.1,
                model="sonnet",
            )

        # Verify stopped at failure
        assert not final_state.is_complete()
        assert final_state.is_failed()
        # iteration_count is 1 because: iteration 0 completes feature 0,
        # then iteration 1 tries feature 1 and fails
        assert final_state.iteration_count == 1
        assert final_state.features[0].status == "completed"
        assert final_state.features[1].status == "failed"

    @pytest.mark.asyncio
    async def test_run_auto_continue_max_iterations(
        self, sample_workflow_state, mock_project_root
    ):
        """Test auto-continue respects max iterations."""
        # Mock slow/stuck execution
        mock_result = ExecutionResult(
            output="Still working...",
            success=True,  # Success but never completes
            cost_usd=0.01,
        )

        with patch(
            "jean_claude.orchestration.auto_continue._execute_prompt_sdk_async",
            new=AsyncMock(return_value=mock_result),
        ):
            final_state = await run_auto_continue(
                state=sample_workflow_state,
                project_root=mock_project_root,
                max_iterations=2,  # Very low limit
                delay_seconds=0.1,
                model="haiku",
            )

        # Verify stopped at max iterations
        assert not final_state.is_complete()
        assert final_state.iteration_count == 2

    @pytest.mark.asyncio
    async def test_run_auto_continue_state_persistence(
        self, sample_workflow_state, mock_project_root
    ):
        """Test that state is saved after each iteration."""
        mock_result = ExecutionResult(output="Success", success=True, cost_usd=0.05)

        with patch(
            "jean_claude.orchestration.auto_continue._execute_prompt_sdk_async",
            new=AsyncMock(return_value=mock_result),
        ):
            final_state = await run_auto_continue(
                state=sample_workflow_state,
                project_root=mock_project_root,
                max_iterations=10,
                delay_seconds=0.1,
                model="sonnet",
            )

        # Reload state from disk
        loaded_state = WorkflowState.load(
            sample_workflow_state.workflow_id, mock_project_root
        )

        # Verify persisted state matches final state
        assert loaded_state.is_complete() == final_state.is_complete()
        assert loaded_state.iteration_count == final_state.iteration_count
        assert loaded_state.current_feature_index == final_state.current_feature_index

    @pytest.mark.asyncio
    async def test_run_auto_continue_progress_tracking(
        self, sample_workflow_state, mock_project_root
    ):
        """Test progress tracking during execution."""
        mock_result = ExecutionResult(
            output="Success", success=True, session_id="session-123", cost_usd=0.05
        )

        with patch(
            "jean_claude.orchestration.auto_continue._execute_prompt_sdk_async",
            new=AsyncMock(return_value=mock_result),
        ):
            final_state = await run_auto_continue(
                state=sample_workflow_state,
                project_root=mock_project_root,
                max_iterations=10,
                delay_seconds=0.1,
                model="sonnet",
            )

        # Verify progress metadata
        summary = final_state.get_summary()
        assert summary["total_features"] == 3
        assert summary["completed_features"] == 3
        assert summary["failed_features"] == 0
        assert summary["progress_percentage"] == 100.0
        assert summary["is_complete"] is True
        assert summary["iteration_count"] == 3

    @pytest.mark.asyncio
    async def test_run_auto_continue_session_tracking(
        self, sample_workflow_state, mock_project_root
    ):
        """Test that session IDs are tracked."""
        # Mock with different session IDs
        call_count = 0

        async def mock_execute(request, max_retries):
            nonlocal call_count
            call_count += 1
            return ExecutionResult(
                output="Success",
                success=True,
                session_id=f"session-{call_count}",
                cost_usd=0.05,
            )

        with patch(
            "jean_claude.orchestration.auto_continue._execute_prompt_sdk_async",
            new=mock_execute,
        ):
            final_state = await run_auto_continue(
                state=sample_workflow_state,
                project_root=mock_project_root,
                max_iterations=10,
                delay_seconds=0.1,
                model="sonnet",
            )

        # Verify session tracking
        assert len(final_state.session_ids) == 3
        assert final_state.session_ids == ["session-1", "session-2", "session-3"]

    @pytest.mark.asyncio
    async def test_run_auto_continue_output_directory_structure(
        self, sample_workflow_state, mock_project_root
    ):
        """Test that output directories are created correctly."""
        mock_result = ExecutionResult(output="Success", success=True)

        with patch(
            "jean_claude.orchestration.auto_continue._execute_prompt_sdk_async",
            new=AsyncMock(return_value=mock_result),
        ):
            await run_auto_continue(
                state=sample_workflow_state,
                project_root=mock_project_root,
                max_iterations=10,
                delay_seconds=0.1,
                model="sonnet",
            )

        # Verify output directory structure
        output_dir = (
            mock_project_root / "agents" / sample_workflow_state.workflow_id / "auto_continue"
        )
        assert output_dir.exists()

        # Check iteration directories
        iteration_dirs = list(output_dir.glob("iteration_*"))
        assert len(iteration_dirs) == 3  # Three features completed
