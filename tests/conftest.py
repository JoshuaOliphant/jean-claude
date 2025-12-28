# ABOUTME: Shared pytest fixtures for Jean Claude test suite
# ABOUTME: Provides common fixtures for CliRunner, mocks, and test data

"""Shared pytest fixtures for Jean Claude tests.

MOCKING ASYNC FUNCTIONS:
- Use `Mock` for sync functions (e.g., fetch_beads_task, update_beads_status)
- Use `Mock` for mocking the result of async functions called via anyio.run()
- Use `AsyncMock` only when directly testing async code with pytest.mark.asyncio
- The anyio.run() wrapper handles the async context, so we mock its return value
"""

from pathlib import Path
from typing import Callable, Generator
from unittest.mock import AsyncMock, Mock, patch

import pytest
from click.testing import CliRunner

from jean_claude.core.beads import BeadsTask, BeadsTaskStatus, BeadsTaskPriority, BeadsTaskType
from jean_claude.core.message import Message, MessagePriority
from jean_claude.core.state import WorkflowState


# =============================================================================
# CLI Testing Fixtures
# =============================================================================


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a reusable CliRunner instance."""
    return CliRunner()


@pytest.fixture
def isolated_cli_runner(cli_runner: CliRunner, tmp_path: Path) -> Generator[CliRunner, None, None]:
    """Provide a CliRunner with isolated filesystem using pytest's tmp_path.

    Using tmp_path instead of isolated_filesystem() is faster because:
    - tmp_path is managed by pytest and can be reused
    - No need to change working directory
    """
    with cli_runner.isolated_filesystem(temp_dir=tmp_path):
        yield cli_runner


# =============================================================================
# Beads Task Fixtures
# =============================================================================


@pytest.fixture
def mock_beads_task() -> BeadsTask:
    """Provide a standard mock BeadsTask for testing."""
    return BeadsTask(
        id="test-task.1",
        title="Test Task",
        description="A test task for unit testing",
        acceptance_criteria=["Criterion 1", "Criterion 2"],
        status=BeadsTaskStatus.OPEN
    )


@pytest.fixture
def mock_beads_task_factory():
    """Factory fixture for creating BeadsTask with custom values."""
    def _create_task(
        id: str = "test-task.1",
        title: str = "Test Task",
        description: str = "A test task",
        acceptance_criteria: list[str] | None = None,
        status: str | BeadsTaskStatus = BeadsTaskStatus.OPEN,
        priority: str | BeadsTaskPriority | None = None,
        task_type: str | BeadsTaskType | None = None,
    ) -> BeadsTask:
        # Convert string to enum if needed
        if isinstance(status, str):
            status = BeadsTaskStatus(status)
        return BeadsTask(
            id=id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria or [],
            status=status,
            priority=priority,
            task_type=task_type,
        )
    return _create_task


# =============================================================================
# WorkflowState Fixtures
# =============================================================================


@pytest.fixture
def mock_workflow_state() -> WorkflowState:
    """Provide a standard mock WorkflowState for testing."""
    return WorkflowState(
        workflow_id="test-workflow-123",
        workflow_name="Test Workflow",
        workflow_type="two-agent",
    )


@pytest.fixture
def mock_workflow_state_instance() -> Mock:
    """Provide a basic mock WorkflowState instance.

    Use this when you need to mock a WorkflowState that's being patched
    in the work command. This fixture provides a clean mock with default
    behavior for common methods.
    """
    mock_state = Mock(spec=WorkflowState)
    mock_state.workflow_id = "test-workflow-123"
    mock_state.phase = "planning"
    return mock_state


@pytest.fixture
def completed_workflow_state() -> Mock:
    """Provide a mock WorkflowState that reports as complete.

    Includes phase and save attributes required by work.py phase transitions.
    """
    state = Mock(spec=WorkflowState)
    state.is_complete.return_value = True
    state.is_failed.return_value = False
    state.workflow_id = "test-workflow-123"
    state.phase = "implementing"
    state.save = Mock()
    return state


@pytest.fixture
def failed_workflow_state() -> Mock:
    """Provide a mock WorkflowState that reports as failed.

    Includes phase and save attributes required by work.py phase transitions.
    """
    state = Mock(spec=WorkflowState)
    state.is_complete.return_value = False
    state.is_failed.return_value = True
    state.workflow_id = "test-workflow-123"
    state.phase = "implementing"
    state.save = Mock()
    return state


# =============================================================================
# Work Command Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_fetch_beads_task(mock_beads_task: BeadsTask):
    """Mock fetch_beads_task to return the mock task."""
    with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task) as mock:
        yield mock


@pytest.fixture
def mock_generate_spec():
    """Mock generate_spec_from_beads to return simple spec content."""
    with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test Spec\n\nTest content") as mock:
        yield mock


@pytest.fixture
def mock_update_beads_status():
    """Mock update_beads_status to do nothing."""
    with patch('jean_claude.cli.commands.work.update_beads_status') as mock:
        yield mock


@pytest.fixture
def mock_close_beads_task():
    """Mock close_beads_task to do nothing."""
    with patch('jean_claude.cli.commands.work.close_beads_task') as mock:
        yield mock


@pytest.fixture
def mock_anyio_run_success(completed_workflow_state: Mock):
    """Mock anyio.run to return a successful workflow state."""
    with patch('jean_claude.cli.commands.work.anyio.run', return_value=completed_workflow_state) as mock:
        yield mock


@pytest.fixture
def mock_anyio_run_failure(failed_workflow_state: Mock):
    """Mock anyio.run to return a failed workflow state."""
    with patch('jean_claude.cli.commands.work.anyio.run', return_value=failed_workflow_state) as mock:
        yield mock


@pytest.fixture
def mock_event_logger():
    """Mock EventLogger and return both the class and instance mocks."""
    with patch('jean_claude.cli.commands.work.EventLogger') as mock_class:
        mock_instance = Mock()
        mock_class.return_value = mock_instance
        yield {"class": mock_class, "instance": mock_instance}


@pytest.fixture
def mock_workflow_state_class(mock_workflow_state_instance: Mock):
    """Mock the WorkflowState class in the work command module.

    Returns a dict with:
    - 'class': The mocked WorkflowState class
    - 'instance': The instance that will be returned when the class is instantiated
    """
    with patch('jean_claude.cli.commands.work.WorkflowState') as mock_class:
        mock_class.return_value = mock_workflow_state_instance
        yield {"class": mock_class, "instance": mock_workflow_state_instance}


@pytest.fixture
def mock_task_validator():
    """Mock TaskValidator to return clean validation result."""
    from jean_claude.core.task_validator import ValidationResult
    mock_result = ValidationResult(is_valid=True, warnings=[], errors=[])
    with patch('jean_claude.cli.commands.work.TaskValidator') as mock_class:
        mock_instance = Mock()
        mock_instance.validate.return_value = mock_result
        mock_class.return_value = mock_instance
        yield {"class": mock_class, "instance": mock_instance, "result": mock_result}


# =============================================================================
# Combined Work Command Fixtures
# =============================================================================


@pytest.fixture
def work_command_mocks(
    mock_fetch_beads_task,
    mock_generate_spec,
    mock_update_beads_status,
    mock_close_beads_task,
    mock_anyio_run_success,
    mock_event_logger,
    mock_workflow_state_class,
    mock_task_validator,
):
    """Combine all work command mocks for integration tests.

    Usage:
        def test_work_does_something(isolated_cli_runner, work_command_mocks):
            result = isolated_cli_runner.invoke(work, ["task-123"])
            assert result.exit_code == 0

            # Access individual mocks
            work_command_mocks["event_logger"]["instance"].emit.assert_called()
            work_command_mocks["workflow_state"]["class"].assert_called()
    """
    return {
        "fetch_beads_task": mock_fetch_beads_task,
        "generate_spec": mock_generate_spec,
        "update_status": mock_update_beads_status,
        "close_task": mock_close_beads_task,
        "anyio_run": mock_anyio_run_success,
        "event_logger": mock_event_logger,
        "workflow_state": mock_workflow_state_class,
        "task_validator": mock_task_validator,
    }


# =============================================================================
# Subprocess Mock Fixtures (for beads.py tests)
# =============================================================================


@pytest.fixture
def mock_subprocess_success():
    """Mock subprocess.run to return success."""
    with patch('jean_claude.core.beads.subprocess.run') as mock:
        mock.return_value = Mock(
            returncode=0,
            stdout='{"id": "test.1", "title": "Test", "description": "Desc", "acceptance_criteria": [], "status": "open"}',
            stderr=""
        )
        yield mock


@pytest.fixture
def mock_subprocess_failure():
    """Mock subprocess.run to return failure."""
    with patch('jean_claude.core.beads.subprocess.run') as mock:
        mock.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error: Task not found"
        )
        yield mock


# =============================================================================
# Message Fixtures
# =============================================================================


@pytest.fixture
def sample_message() -> Message:
    """Provide a standard Message for testing."""
    return Message(
        from_agent="agent-1",
        to_agent="agent-2",
        type="test",
        subject="Test Message",
        body="This is a test message body."
    )


@pytest.fixture
def urgent_message() -> Message:
    """Provide an urgent priority Message for testing."""
    return Message(
        from_agent="agent-1",
        to_agent="coordinator",
        type="help_request",
        subject="Urgent Help Needed",
        body="I need immediate assistance.",
        priority=MessagePriority.URGENT,
        awaiting_response=True
    )


@pytest.fixture
def message_factory() -> Callable[..., Message]:
    """Factory fixture for creating Message with custom values.

    Usage:
        def test_something(message_factory):
            msg = message_factory(priority=MessagePriority.URGENT)
    """
    def _create_message(
        from_agent: str = "agent-1",
        to_agent: str = "agent-2",
        type: str = "test",
        subject: str = "Test Subject",
        body: str = "Test body content",
        priority: MessagePriority = MessagePriority.NORMAL,
        awaiting_response: bool = False,
    ) -> Message:
        return Message(
            from_agent=from_agent,
            to_agent=to_agent,
            type=type,
            subject=subject,
            body=body,
            priority=priority,
            awaiting_response=awaiting_response,
        )
    return _create_message
