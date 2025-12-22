# ABOUTME: Integration tests for auto-continue with mock workflows
# ABOUTME: End-to-end verification of the auto-continue pattern

"""Integration tests for auto-continue orchestrator."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jean_claude.core.state import WorkflowState
from jean_claude.core.agent import ExecutionResult
from jean_claude.orchestration.auto_continue import (
    run_auto_continue,
    initialize_workflow,
)


@pytest.fixture
def mock_project_root(tmp_path: Path) -> Path:
    """Create a temporary project root directory with basic structure."""
    # Create directories
    (tmp_path / "agents").mkdir(exist_ok=True)
    (tmp_path / "specs").mkdir(exist_ok=True)
    (tmp_path / "tests").mkdir(exist_ok=True)
    (tmp_path / "src").mkdir(exist_ok=True)

    # Create a simple test file
    test_file = tmp_path / "tests" / "test_example.py"
    test_file.write_text(
        """
def test_always_passes():
    assert True
"""
    )

    return tmp_path


@pytest.mark.asyncio
async def test_full_workflow_lifecycle(mock_project_root):
    """Test complete workflow lifecycle from initialization to completion."""
    # 1. Initialize workflow
    features = [
        ("Add logging", "Implement logging middleware", "tests/test_logging.py"),
        ("Add error handling", "Add error handlers", "tests/test_errors.py"),
        ("Add monitoring", "Add health checks", None),
    ]

    state = await initialize_workflow(
        workflow_id="integration-test",
        workflow_name="Integration Test Workflow",
        workflow_type="feature",
        features=features,
        project_root=mock_project_root,
        max_iterations=10,
    )

    # Verify initialization
    assert len(state.features) == 3
    assert state.current_feature_index == 0
    assert state.iteration_count == 0

    # 2. Mock successful execution for all features
    mock_results = [
        ExecutionResult(
            output=f"Completed feature {i}",
            success=True,
            session_id=f"session-{i}",
            cost_usd=0.05,
            duration_ms=1000,
        )
        for i in range(3)
    ]

    current_result_index = 0

    async def mock_execute(request, max_retries):
        nonlocal current_result_index
        result = mock_results[current_result_index]
        current_result_index += 1
        return result

    # 3. Run auto-continue loop
    with patch(
        "jean_claude.orchestration.auto_continue._execute_prompt_sdk_async",
        new=mock_execute,
    ), patch(
        "jean_claude.orchestration.auto_continue.run_verification",
        return_value=MagicMock(passed=True, skipped=True, skip_reason="No tests yet"),
    ):
        final_state = await run_auto_continue(
            state=state,
            project_root=mock_project_root,
            max_iterations=10,
            delay_seconds=0.1,
            model="sonnet",
        )

    # 4. Verify final state
    assert final_state.is_complete()
    assert final_state.current_feature_index == 3
    assert final_state.iteration_count == 3
    assert abs(final_state.total_cost_usd - 0.15) < 0.001  # Float tolerance

    # 5. Verify all features completed
    for feature in final_state.features:
        assert feature.status == "completed"

    # 6. Verify state persisted
    loaded_state = WorkflowState.load("integration-test", mock_project_root)
    assert loaded_state.is_complete()

    # 7. Verify summary
    summary = loaded_state.get_summary()
    assert summary["completed_features"] == 3
    assert summary["failed_features"] == 0
    assert summary["progress_percentage"] == 100.0


@pytest.mark.asyncio
async def test_workflow_with_failure_recovery(mock_project_root):
    """Test workflow that fails, gets fixed, and resumes."""
    # Initialize workflow
    features = [
        ("Feature 1", "First feature", None),
        ("Feature 2", "Second feature - will fail", None),
        ("Feature 3", "Third feature", None),
    ]

    state = await initialize_workflow(
        workflow_id="failure-recovery",
        workflow_name="Failure Recovery Test",
        workflow_type="chore",
        features=features,
        project_root=mock_project_root,
        max_iterations=5,
    )

    # First run - fails on feature 2
    call_count = 0

    async def mock_execute_with_failure(request, max_retries):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return ExecutionResult(output="Success", success=True, cost_usd=0.05)
        elif call_count == 2:
            return ExecutionResult(output="Failed!", success=False, cost_usd=0.03)
        else:
            return ExecutionResult(output="Success", success=True, cost_usd=0.05)

    with patch(
        "jean_claude.orchestration.auto_continue._execute_prompt_sdk_async",
        new=mock_execute_with_failure,
    ), patch(
        "jean_claude.orchestration.auto_continue.run_verification",
        return_value=MagicMock(passed=True, skipped=True),
    ):
        first_run_state = await run_auto_continue(
            state=state,
            project_root=mock_project_root,
            max_iterations=5,
            delay_seconds=0.1,
            model="sonnet",
        )

    # Verify it stopped at failure
    assert not first_run_state.is_complete()
    assert first_run_state.is_failed()
    assert first_run_state.features[0].status == "completed"
    assert first_run_state.features[1].status == "failed"

    # Simulate fixing the issue manually
    first_run_state.features[1].status = "not_started"
    first_run_state.save(mock_project_root)

    # Resume workflow
    resumed_state = WorkflowState.load("failure-recovery", mock_project_root)
    resumed_state.current_feature_index = 1  # Go back to failed feature

    # Second run - succeeds
    call_count = 0

    async def mock_execute_success(request, max_retries):
        return ExecutionResult(output="Success", success=True, cost_usd=0.05)

    with patch(
        "jean_claude.orchestration.auto_continue._execute_prompt_sdk_async",
        new=mock_execute_success,
    ), patch(
        "jean_claude.orchestration.auto_continue.run_verification",
        return_value=MagicMock(passed=True, skipped=True),
    ):
        final_state = await run_auto_continue(
            state=resumed_state,
            project_root=mock_project_root,
            max_iterations=5,
            delay_seconds=0.1,
            model="sonnet",
        )

    # Verify completion
    assert final_state.is_complete()
    assert all(f.status == "completed" for f in final_state.features)


@pytest.mark.asyncio
async def test_workflow_interrupt_and_resume(mock_project_root):
    """Test workflow can be interrupted and resumed."""
    features = [
        ("Feature A", "Feature A", None),
        ("Feature B", "Feature B", None),
        ("Feature C", "Feature C", None),
    ]

    state = await initialize_workflow(
        workflow_id="interrupt-test",
        workflow_name="Interrupt Test",
        workflow_type="feature",
        features=features,
        project_root=mock_project_root,
        max_iterations=10,
    )

    # First run - only complete 1 feature (simulate interrupt)
    call_count = 0

    async def mock_execute_limited(request, max_retries):
        nonlocal call_count
        call_count += 1
        return ExecutionResult(output="Success", success=True, cost_usd=0.05)

    with patch(
        "jean_claude.orchestration.auto_continue._execute_prompt_sdk_async",
        new=mock_execute_limited,
    ), patch(
        "jean_claude.orchestration.auto_continue.run_verification",
        return_value=MagicMock(passed=True, skipped=True),
    ):
        partial_state = await run_auto_continue(
            state=state,
            project_root=mock_project_root,
            max_iterations=1,  # Only one iteration
            delay_seconds=0.1,
            model="sonnet",
        )

    # Verify partial completion
    assert not partial_state.is_complete()
    assert partial_state.features[0].status == "completed"
    assert partial_state.current_feature_index == 1

    # Resume from disk
    resumed_state = WorkflowState.load("interrupt-test", mock_project_root)
    assert resumed_state.current_feature_index == 1

    # Continue execution
    call_count = 0
    with patch(
        "jean_claude.orchestration.auto_continue._execute_prompt_sdk_async",
        new=mock_execute_limited,
    ), patch(
        "jean_claude.orchestration.auto_continue.run_verification",
        return_value=MagicMock(passed=True, skipped=True),
    ):
        final_state = await run_auto_continue(
            state=resumed_state,
            project_root=mock_project_root,
            max_iterations=10,
            delay_seconds=0.1,
            model="sonnet",
        )

    # Verify completion
    assert final_state.is_complete()
    assert all(f.status == "completed" for f in final_state.features)


@pytest.mark.asyncio
async def test_empty_workflow_completes_immediately(mock_project_root):
    """Test workflow with no features completes immediately."""
    state = await initialize_workflow(
        workflow_id="empty-workflow",
        workflow_name="Empty Workflow",
        workflow_type="chore",
        features=[],
        project_root=mock_project_root,
    )

    # Run should complete immediately with no features
    with patch(
        "jean_claude.orchestration.auto_continue._execute_prompt_sdk_async"
    ) as mock_exec, patch(
        "jean_claude.orchestration.auto_continue.run_verification"
    ):
        final_state = await run_auto_continue(
            state=state,
            project_root=mock_project_root,
            delay_seconds=0.1,
        )

        # Should not execute any prompts
        mock_exec.assert_not_called()

    # Verify state
    assert final_state.iteration_count == 0
    assert final_state.current_feature_index == 0


@pytest.mark.asyncio
async def test_workflow_cost_and_duration_tracking(mock_project_root):
    """Test that costs and durations are properly tracked."""
    features = [
        ("Task 1", "First task", None),
        ("Task 2", "Second task", None),
    ]

    state = await initialize_workflow(
        workflow_id="cost-tracking",
        workflow_name="Cost Tracking Test",
        workflow_type="chore",
        features=features,
        project_root=mock_project_root,
    )

    # Mock with varying costs and durations
    mock_results = [
        ExecutionResult(
            output="Done",
            success=True,
            session_id="s1",
            cost_usd=0.10,
            duration_ms=2000,
        ),
        ExecutionResult(
            output="Done",
            success=True,
            session_id="s2",
            cost_usd=0.15,
            duration_ms=3000,
        ),
    ]

    current_index = 0

    async def mock_execute(request, max_retries):
        nonlocal current_index
        result = mock_results[current_index]
        current_index += 1
        return result

    with patch(
        "jean_claude.orchestration.auto_continue._execute_prompt_sdk_async",
        new=mock_execute,
    ), patch(
        "jean_claude.orchestration.auto_continue.run_verification",
        return_value=MagicMock(passed=True, skipped=True),
    ):
        final_state = await run_auto_continue(
            state=state,
            project_root=mock_project_root,
            delay_seconds=0.1,
        )

    # Verify tracking
    assert final_state.total_cost_usd == 0.25
    assert final_state.total_duration_ms == 5000
    assert len(final_state.session_ids) == 2
    assert final_state.session_ids == ["s1", "s2"]
