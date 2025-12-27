# ABOUTME: Shared pytest fixtures for tests/orchestration/ test suite
# ABOUTME: Provides common fixtures for workflow state, project root, and execution mocks

"""Shared pytest fixtures for orchestration module tests.

These fixtures are automatically available to all tests in tests/orchestration/.
Import from the root conftest.py for fixtures that should be shared across
all test directories.

USAGE:
    def test_something(mock_project_root, sample_workflow_state):
        # Fixtures are automatically injected
        pass

GUIDELINES:
    1. Use mock_project_root for temporary project directories
    2. Use sample_workflow_state for pre-configured workflow state
    3. Use mock_execution_result for agent execution responses
    4. Add new fixtures here when a pattern is used 3+ times
"""

from pathlib import Path
from typing import Callable
from unittest.mock import Mock

import pytest

from jean_claude.core.agent import ExecutionResult
from jean_claude.core.state import WorkflowState, Feature


# =============================================================================
# Project Root Fixtures
# =============================================================================


@pytest.fixture
def mock_project_root(tmp_path: Path) -> Path:
    """Create a temporary project root directory with agents folder.

    This is the standard fixture for creating a temporary project root.
    Includes the agents/ directory that workflows expect.
    """
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path


# Alias for tests that use project_root instead of mock_project_root
@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Alias for mock_project_root without agents/ directory.

    Simple fixture that just returns tmp_path for basic tests.
    """
    return tmp_path


# =============================================================================
# Workflow State Fixtures
# =============================================================================


@pytest.fixture
def sample_workflow_state(mock_project_root: Path) -> WorkflowState:
    """Create a sample workflow state with three features.

    The state is saved to the mock_project_root so it can be loaded
    by tests that use initialize_workflow or resume_workflow.
    """
    state = WorkflowState(
        workflow_id="test-abc123",
        workflow_name="Test Workflow",
        workflow_type="feature",
        max_iterations=10,
    )

    # Add three features
    state.add_feature(
        name="Feature 1",
        description="Implement authentication",
        test_file="tests/test_auth.py",
    )
    state.add_feature(
        name="Feature 2",
        description="Add user profile",
        test_file="tests/test_profile.py",
    )
    state.add_feature(
        name="Feature 3",
        description="Implement logout",
        test_file="tests/test_logout.py",
    )

    state.save(mock_project_root)
    return state


@pytest.fixture
def minimal_workflow_state(mock_project_root: Path) -> WorkflowState:
    """Create a minimal workflow state without features.

    Use this when you need a clean workflow state for testing.
    """
    state = WorkflowState(
        workflow_id="minimal-123",
        workflow_name="Minimal Workflow",
        workflow_type="feature",
    )
    state.save(mock_project_root)
    return state


@pytest.fixture
def workflow_state_factory(mock_project_root: Path) -> Callable[..., WorkflowState]:
    """Factory fixture for creating WorkflowState with custom values.

    Usage:
        def test_something(workflow_state_factory):
            state = workflow_state_factory(workflow_id="custom-id", max_iterations=5)
    """
    def _create_state(
        workflow_id: str = "factory-workflow-1",
        workflow_name: str = "Factory Workflow",
        workflow_type: str = "feature",
        max_iterations: int = 10,
        save: bool = True,
    ) -> WorkflowState:
        state = WorkflowState(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            workflow_type=workflow_type,
            max_iterations=max_iterations,
        )
        if save:
            state.save(mock_project_root)
        return state
    return _create_state


# =============================================================================
# Execution Result Fixtures
# =============================================================================


@pytest.fixture
def mock_execution_result() -> ExecutionResult:
    """Create a mock execution result for successful agent execution."""
    return ExecutionResult(
        success=True,
        output="Test output from agent",
        session_id="test-session",
        cost_usd=0.01,
        duration_ms=1000,
    )


@pytest.fixture
def failed_execution_result() -> ExecutionResult:
    """Create a mock execution result for failed agent execution."""
    return ExecutionResult(
        success=False,
        output="Error occurred",
        session_id="test-session",
        cost_usd=0.005,
        duration_ms=500,
    )


@pytest.fixture
def execution_result_factory() -> Callable[..., ExecutionResult]:
    """Factory fixture for creating ExecutionResult with custom values.

    Usage:
        def test_something(execution_result_factory):
            result = execution_result_factory(success=False, output="Error")
    """
    def _create_result(
        success: bool = True,
        output: str = "Test output",
        session_id: str | None = "test-session",
        cost_usd: float | None = 0.01,
        duration_ms: int | None = 1000,
    ) -> ExecutionResult:
        return ExecutionResult(
            success=success,
            output=output,
            session_id=session_id,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
        )
    return _create_result
