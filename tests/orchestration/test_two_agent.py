# ABOUTME: Tests for two-agent orchestration pattern
# ABOUTME: Validates initializer agent, coder agent handoff, and state management

"""Tests for two-agent orchestration pattern."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jean_claude.core.state import WorkflowState, Feature
from jean_claude.core.agent import ExecutionResult
from jean_claude.orchestration.two_agent import (
    run_initializer,
    run_two_agent_workflow,
    INITIALIZER_PROMPT,
)


# project_root fixture is provided by tests/orchestration/conftest.py


@pytest.fixture
def mock_execution_result() -> ExecutionResult:
    """Create a mock execution result with feature JSON output.

    Note: This fixture has test-specific output content (JSON features)
    which differs from the generic fixture in conftest.py.
    """
    return ExecutionResult(
        success=True,
        output='{"features": [{"name": "test-feature", "description": "Test feature", "test_file": "tests/test_feature.py"}]}',
        session_id="test-session",
        cost_usd=0.01,
        duration_ms=1000,
    )


@pytest.mark.asyncio
async def test_run_initializer_success(
    project_root: Path, mock_execution_result: ExecutionResult
) -> None:
    """Test successful initializer execution."""
    with patch(
        "jean_claude.orchestration.two_agent._execute_prompt_sdk_async",
        new_callable=AsyncMock,
    ) as mock_execute:
        mock_execute.return_value = mock_execution_result

        state = await run_initializer(
            description="Build a simple API",
            project_root=project_root,
            workflow_id="test-workflow",
            model="opus",
        )

        # Verify state
        assert state.workflow_id == "test-workflow"
        assert state.workflow_type == "two-agent"
        assert len(state.features) == 1
        assert state.features[0].name == "test-feature"
        assert state.features[0].description == "Test feature"
        assert state.features[0].test_file == "tests/test_feature.py"

        # Verify state was saved
        state_file = project_root / "agents" / "test-workflow" / "state.json"
        assert state_file.exists()

        # Verify state file content
        with open(state_file) as f:
            saved_data = json.load(f)
        assert saved_data["workflow_id"] == "test-workflow"
        assert len(saved_data["features"]) == 1


@pytest.mark.asyncio
async def test_run_initializer_with_markdown_code_block(
    project_root: Path,
) -> None:
    """Test initializer handles JSON in markdown code blocks."""
    result = ExecutionResult(
        success=True,
        output='```json\n{"features": [{"name": "test", "description": "Test", "test_file": "tests/test.py"}]}\n```',
        session_id="test",
        cost_usd=0.01,
        duration_ms=1000,
    )

    with patch(
        "jean_claude.orchestration.two_agent._execute_prompt_sdk_async",
        new_callable=AsyncMock,
    ) as mock_execute:
        mock_execute.return_value = result

        state = await run_initializer(
            description="Test",
            project_root=project_root,
            workflow_id="test",
        )

        assert len(state.features) == 1
        assert state.features[0].name == "test"


@pytest.mark.asyncio
async def test_run_initializer_invalid_json(project_root: Path) -> None:
    """Test initializer handles invalid JSON gracefully."""
    result = ExecutionResult(
        success=True,
        output="This is not JSON",
        session_id="test",
        cost_usd=0.01,
        duration_ms=1000,
    )

    with patch(
        "jean_claude.orchestration.two_agent._execute_prompt_sdk_async",
        new_callable=AsyncMock,
    ) as mock_execute:
        mock_execute.return_value = result

        with pytest.raises(ValueError, match="not valid JSON"):
            await run_initializer(
                description="Test",
                project_root=project_root,
            )


@pytest.mark.asyncio
async def test_run_initializer_missing_features_key(project_root: Path) -> None:
    """Test initializer validates features key exists."""
    result = ExecutionResult(
        success=True,
        output='{"wrong_key": []}',
        session_id="test",
        cost_usd=0.01,
        duration_ms=1000,
    )

    with patch(
        "jean_claude.orchestration.two_agent._execute_prompt_sdk_async",
        new_callable=AsyncMock,
    ) as mock_execute:
        mock_execute.return_value = result

        with pytest.raises(ValueError, match="missing 'features'"):
            await run_initializer(
                description="Test",
                project_root=project_root,
            )


@pytest.mark.asyncio
async def test_run_initializer_empty_features(project_root: Path) -> None:
    """Test initializer validates features list is not empty."""
    result = ExecutionResult(
        success=True,
        output='{"features": []}',
        session_id="test",
        cost_usd=0.01,
        duration_ms=1000,
    )

    with patch(
        "jean_claude.orchestration.two_agent._execute_prompt_sdk_async",
        new_callable=AsyncMock,
    ) as mock_execute:
        mock_execute.return_value = result

        with pytest.raises(ValueError, match="Feature list is empty"):
            await run_initializer(
                description="Test",
                project_root=project_root,
            )


@pytest.mark.asyncio
async def test_run_initializer_auto_generates_workflow_id(project_root: Path) -> None:
    """Test initializer auto-generates workflow ID if not provided."""
    result = ExecutionResult(
        success=True,
        output='{"features": [{"name": "test", "description": "Test", "test_file": "tests/test.py"}]}',
        session_id="test",
        cost_usd=0.01,
        duration_ms=1000,
    )

    with patch(
        "jean_claude.orchestration.two_agent._execute_prompt_sdk_async",
        new_callable=AsyncMock,
    ) as mock_execute:
        mock_execute.return_value = result

        state = await run_initializer(
            description="Test",
            project_root=project_root,
            workflow_id=None,  # No workflow ID
        )

        # Should generate a workflow ID like "two-agent-abc12345"
        assert state.workflow_id.startswith("two-agent-")
        assert len(state.workflow_id) > len("two-agent-")


@pytest.mark.asyncio
async def test_run_two_agent_workflow_with_auto_confirm(
    project_root: Path, mock_execution_result: ExecutionResult
) -> None:
    """Test full two-agent workflow with auto-confirmation."""
    # Mock initializer execution
    with patch(
        "jean_claude.orchestration.two_agent._execute_prompt_sdk_async",
        new_callable=AsyncMock,
    ) as mock_execute:
        mock_execute.return_value = mock_execution_result

        # Mock auto_continue
        with patch(
            "jean_claude.orchestration.two_agent.run_auto_continue",
            new_callable=AsyncMock,
        ) as mock_auto_continue:
            # Create a completed state
            completed_state = WorkflowState(
                workflow_id="test-workflow",
                workflow_name="Test",
                workflow_type="two-agent",
            )
            completed_state.add_feature("test-feature", "Test", "tests/test.py")
            completed_state.mark_feature_complete()

            mock_auto_continue.return_value = completed_state

            # Run workflow
            final_state = await run_two_agent_workflow(
                description="Build a simple API",
                project_root=project_root,
                workflow_id="test-workflow",
                auto_confirm=True,  # Skip user confirmation
            )

            # Verify both agents were called
            assert mock_execute.called
            assert mock_auto_continue.called

            # Verify final state
            assert final_state.is_complete()
            assert final_state.workflow_id == "test-workflow"


@pytest.mark.asyncio
async def test_run_two_agent_workflow_user_cancellation(
    project_root: Path, mock_execution_result: ExecutionResult
) -> None:
    """Test workflow handles user cancellation."""
    with patch(
        "jean_claude.orchestration.two_agent._execute_prompt_sdk_async",
        new_callable=AsyncMock,
    ) as mock_execute:
        mock_execute.return_value = mock_execution_result

        # Mock user declining confirmation
        with patch("jean_claude.orchestration.two_agent.Confirm.ask", return_value=False):
            with pytest.raises(KeyboardInterrupt):
                await run_two_agent_workflow(
                    description="Test",
                    project_root=project_root,
                    auto_confirm=False,  # Require confirmation
                )


@pytest.mark.asyncio
async def test_initializer_uses_correct_model(project_root: Path) -> None:
    """Test initializer passes correct model to executor."""
    result = ExecutionResult(
        success=True,
        output='{"features": [{"name": "test", "description": "Test", "test_file": "tests/test.py"}]}',
        session_id="test",
        cost_usd=0.01,
        duration_ms=1000,
    )

    with patch(
        "jean_claude.orchestration.two_agent._execute_prompt_sdk_async",
        new_callable=AsyncMock,
    ) as mock_execute:
        mock_execute.return_value = result

        await run_initializer(
            description="Test",
            project_root=project_root,
            model="opus",
        )

        # Verify model was passed correctly
        call_args = mock_execute.call_args
        request = call_args[0][0]
        assert request.model == "opus"


@pytest.mark.asyncio
async def test_two_agent_workflow_uses_different_models(
    project_root: Path, mock_execution_result: ExecutionResult
) -> None:
    """Test workflow uses different models for initializer and coder."""
    with patch(
        "jean_claude.orchestration.two_agent._execute_prompt_sdk_async",
        new_callable=AsyncMock,
    ) as mock_execute:
        mock_execute.return_value = mock_execution_result

        with patch(
            "jean_claude.orchestration.two_agent.run_auto_continue",
            new_callable=AsyncMock,
        ) as mock_auto_continue:
            completed_state = WorkflowState(
                workflow_id="test",
                workflow_name="Test",
                workflow_type="two-agent",
            )
            mock_auto_continue.return_value = completed_state

            await run_two_agent_workflow(
                description="Test",
                project_root=project_root,
                initializer_model="opus",
                coder_model="sonnet",
                auto_confirm=True,
            )

            # Verify initializer used opus
            init_call_args = mock_execute.call_args
            init_request = init_call_args[0][0]
            assert init_request.model == "opus"

            # Verify coder used sonnet
            auto_continue_call_args = mock_auto_continue.call_args
            assert auto_continue_call_args[1]["model"] == "sonnet"


def test_initializer_prompt_contains_critical_requirements() -> None:
    """Test initializer prompt has all critical requirements."""
    assert "JSON" in INITIALIZER_PROMPT
    assert "features" in INITIALIZER_PROMPT
    assert "test_file" in INITIALIZER_PROMPT
    assert "description" in INITIALIZER_PROMPT
    assert "CRITICAL" in INITIALIZER_PROMPT or "REQUIREMENTS" in INITIALIZER_PROMPT
